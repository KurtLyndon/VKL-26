from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ScanImportBatch, ScanResult, ScanResultFinding, Target, TargetAttributeDefinition, TargetAttributeValue


CORE_GROUP_ORDER = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "Khác"]
CORE_GROUP_SET = set(CORE_GROUP_ORDER[:-1])
QUARTER_LABELS = {1: "Quý I", 2: "Quý II", 3: "Quý III", 4: "Quý IV"}


@dataclass
class DashboardFilters:
    year: int | None = None
    quarter: int | None = None
    month: int | None = None
    week: int | None = None


@dataclass
class BatchPeriod:
    batch: ScanImportBatch
    year: int
    quarter: int
    month: int | None
    week: int
    effective_date: datetime


def _effective_datetime(batch: ScanImportBatch) -> datetime:
    return batch.scan_started_at or batch.scan_finished_at or batch.created_at


def _build_batch_period(batch: ScanImportBatch) -> BatchPeriod:
    effective_date = _effective_datetime(batch)
    return BatchPeriod(
        batch=batch,
        year=batch.scan_year,
        quarter=batch.scan_quarter,
        month=effective_date.month if effective_date else None,
        week=batch.scan_week,
        effective_date=effective_date,
    )


def _match_filters(period: BatchPeriod, filters: DashboardFilters, *, skip_key: str | None = None) -> bool:
    if skip_key != "year" and filters.year is not None and period.year != filters.year:
        return False
    if skip_key != "quarter" and filters.quarter is not None and period.quarter != filters.quarter:
        return False
    if skip_key != "month" and filters.month is not None and period.month != filters.month:
        return False
    if skip_key != "week" and filters.week is not None and period.week != filters.week:
        return False
    return True


def _load_batches(db: Session) -> list[BatchPeriod]:
    batches = db.scalars(select(ScanImportBatch).order_by(ScanImportBatch.id.asc())).all()
    return [_build_batch_period(batch) for batch in batches]


def _extract_ip(scan_result: ScanResult) -> str | None:
    normalized = scan_result.normalized_output_json or {}
    if isinstance(normalized, dict) and normalized.get("ip"):
        return str(normalized["ip"]).strip()
    if scan_result.raw_output:
        try:
            payload = json.loads(scan_result.raw_output)
        except (TypeError, ValueError, json.JSONDecodeError):
            return None
        if isinstance(payload, dict) and payload.get("ip"):
            return str(payload["ip"]).strip()
    return None


def _extract_port(scan_result: ScanResult) -> int | None:
    normalized = scan_result.normalized_output_json or {}
    if isinstance(normalized, dict) and normalized.get("port") not in (None, ""):
        try:
            return int(normalized["port"])
        except (TypeError, ValueError):
            return None
    return None


def _load_scan_results_for_batches(db: Session, periods: list[BatchPeriod]) -> list[ScanResult]:
    execution_ids = [item.batch.operation_execution_id for item in periods]
    if not execution_ids:
        return []
    return db.scalars(
        select(ScanResult).where(ScanResult.operation_execution_id.in_(execution_ids)).order_by(ScanResult.id.asc())
    ).all()


def _load_findings_for_scan_results(db: Session, scan_results: list[ScanResult]) -> list[ScanResultFinding]:
    scan_result_ids = [item.id for item in scan_results]
    if not scan_result_ids:
        return []
    return db.scalars(
        select(ScanResultFinding).where(ScanResultFinding.scan_result_id.in_(scan_result_ids)).order_by(ScanResultFinding.id.asc())
    ).all()


def _group_target_ids_by_core_group(db: Session) -> dict[str, set[int]]:
    definition = db.scalar(
        select(TargetAttributeDefinition).where(
            (TargetAttributeDefinition.attribute_code == "dv_cap_1")
            | (TargetAttributeDefinition.attribute_name == "ĐV Cấp 1")
        )
    )
    target_ids_by_group: dict[str, set[int]] = {key: set() for key in CORE_GROUP_ORDER}
    targets = db.scalars(select(Target).order_by(Target.id.asc())).all()
    if definition is None:
        target_ids_by_group["Khác"] = {target.id for target in targets}
        return target_ids_by_group

    values = db.scalars(
        select(TargetAttributeValue).where(TargetAttributeValue.attribute_definition_id == definition.id)
    ).all()
    value_map = {item.target_id: (item.value_text or "").strip().upper() for item in values}
    for target in targets:
        raw_value = value_map.get(target.id, "")
        key = raw_value if raw_value in CORE_GROUP_SET else "Khác"
        target_ids_by_group.setdefault(key, set()).add(target.id)
    return target_ids_by_group


def get_dashboard_filter_options(db: Session, filters: DashboardFilters) -> dict:
    periods = _load_batches(db)
    return {
        "years": sorted({item.year for item in periods if _match_filters(item, filters, skip_key="year")}),
        "quarters": sorted({item.quarter for item in periods if _match_filters(item, filters, skip_key="quarter")}),
        "months": sorted({item.month for item in periods if item.month and _match_filters(item, filters, skip_key="month")}),
        "weeks": sorted({item.week for item in periods if _match_filters(item, filters, skip_key="week")}),
    }


def _overview_from_periods(db: Session, periods: list[BatchPeriod]) -> dict:
    scan_results = _load_scan_results_for_batches(db, periods)
    findings = _load_findings_for_scan_results(db, scan_results)
    findings_by_scan_result_id = defaultdict(list)
    for finding in findings:
        findings_by_scan_result_id[finding.scan_result_id].append(finding)

    scanned_target_ids = {item.target_id for item in scan_results if item.target_id}
    detected_ips = {ip for item in scan_results if (ip := _extract_ip(item))}
    open_port_pairs = {
        (ip, port)
        for item in scan_results
        if (ip := _extract_ip(item)) and (port := _extract_port(item)) is not None
    }
    target_ids_with_vuln = {
        item.target_id
        for item in scan_results
        if findings_by_scan_result_id.get(item.id)
    }
    risky_ips = {
        _extract_ip(item)
        for item in scan_results
        if findings_by_scan_result_id.get(item.id) and _extract_ip(item)
    }

    return {
        "scanned_targets": len(scanned_target_ids),
        "detected_ips": len(detected_ips),
        "open_ports": len(open_port_pairs),
        "detected_vulns": len(findings),
        "targets_at_risk": len(target_ids_with_vuln),
        "ips_at_risk": len(risky_ips),
    }


def get_dashboard_overview(db: Session, filters: DashboardFilters) -> dict:
    periods = [item for item in _load_batches(db) if _match_filters(item, filters)]
    return _overview_from_periods(db, periods)


def get_dashboard_total_summary(db: Session) -> dict:
    return _overview_from_periods(db, _load_batches(db))


def get_top_vulnerabilities(db: Session, filters: DashboardFilters, limit: int = 5) -> list[dict]:
    periods = [item for item in _load_batches(db) if _match_filters(item, filters)]
    scan_results = _load_scan_results_for_batches(db, periods)
    findings = _load_findings_for_scan_results(db, scan_results)
    counts: dict[tuple[str, str], int] = defaultdict(int)
    for finding in findings:
        code = finding.finding_code or finding.title or "UNKNOWN"
        counts[(code, finding.title or code)] += 1
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0][0]))
    return [
        {"code": code, "title": title, "count": count}
        for (code, title), count in ranked[:limit]
    ]


def get_target_quarterly_comparison(db: Session, *, year: int, target_ids: list[int]) -> dict:
    selected_target_ids = [int(item) for item in target_ids[:5]]
    periods = [item for item in _load_batches(db) if item.year == year]
    scan_results = _load_scan_results_for_batches(db, periods)
    findings = _load_findings_for_scan_results(db, scan_results)
    scan_result_map = {item.id: item for item in scan_results}
    execution_to_quarter = {item.batch.operation_execution_id: item.quarter for item in periods}
    target_map = {
        target.id: target
        for target in db.scalars(select(Target).where(Target.id.in_(selected_target_ids))).all()
    }

    series_map = {
        target_id: {"target_id": target_id, "target_name": target_map.get(target_id).name if target_map.get(target_id) else f"Target {target_id}", "quarters": {quarter: 0 for quarter in range(1, 5)}}
        for target_id in selected_target_ids
    }
    for finding in findings:
        scan_result = scan_result_map.get(finding.scan_result_id)
        if scan_result is None or scan_result.target_id not in series_map:
            continue
        quarter = execution_to_quarter.get(scan_result.operation_execution_id)
        if quarter in {1, 2, 3, 4}:
            series_map[scan_result.target_id]["quarters"][quarter] += 1

    return {
        "year": year,
        "quarters": [{"value": quarter, "label": QUARTER_LABELS[quarter]} for quarter in range(1, 5)],
        "series": list(series_map.values()),
    }


def get_core_group_options() -> list[str]:
    return CORE_GROUP_ORDER


def get_core_group_quarterly_chart(db: Session, *, year: int, groups: list[str], metric: str) -> dict:
    normalized_groups = []
    for item in groups[:5]:
        value = (item or "").strip()
        if value in CORE_GROUP_ORDER and value not in normalized_groups:
            normalized_groups.append(value)

    target_ids_by_group = _group_target_ids_by_core_group(db)
    periods = [item for item in _load_batches(db) if item.year == year]
    scan_results = _load_scan_results_for_batches(db, periods)
    findings = _load_findings_for_scan_results(db, scan_results)
    scan_result_map = {item.id: item for item in scan_results}
    execution_to_quarter = {item.batch.operation_execution_id: item.quarter for item in periods}

    findings_by_group_quarter: dict[tuple[str, int], int] = defaultdict(int)
    risky_targets_by_group_quarter: dict[tuple[str, int], set[int]] = defaultdict(set)
    target_group_lookup: dict[int, str] = {}
    for group_name, target_ids in target_ids_by_group.items():
        for target_id in target_ids:
            target_group_lookup[target_id] = group_name

    for finding in findings:
        scan_result = scan_result_map.get(finding.scan_result_id)
        if scan_result is None:
            continue
        group_name = target_group_lookup.get(scan_result.target_id, "Khác")
        quarter = execution_to_quarter.get(scan_result.operation_execution_id)
        if quarter not in {1, 2, 3, 4}:
            continue
        findings_by_group_quarter[(group_name, quarter)] += 1
        risky_targets_by_group_quarter[(group_name, quarter)].add(scan_result.target_id)

    series = []
    for group_name in normalized_groups:
        quarter_values = {}
        total_targets = len(target_ids_by_group.get(group_name, set()))
        for quarter in range(1, 5):
            if metric == "risk_rate":
                risky_count = len(risky_targets_by_group_quarter.get((group_name, quarter), set()))
                value = round((risky_count / total_targets) * 100, 2) if total_targets else 0
            else:
                value = findings_by_group_quarter.get((group_name, quarter), 0)
            quarter_values[quarter] = value
        series.append(
            {
                "group": group_name,
                "quarters": quarter_values,
                "total_targets": total_targets,
            }
        )

    return {
        "year": year,
        "metric": metric,
        "quarters": [{"value": quarter, "label": QUARTER_LABELS[quarter]} for quarter in range(1, 5)],
        "series": series,
    }


def get_vulnerability_trend_by_quarter(db: Session) -> dict:
    periods = _load_batches(db)
    scan_results = _load_scan_results_for_batches(db, periods)
    findings = _load_findings_for_scan_results(db, scan_results)
    scan_result_map = {item.id: item for item in scan_results}
    execution_lookup = {
        item.batch.operation_execution_id: (item.year, item.quarter)
        for item in periods
    }
    counts: dict[tuple[int, int], int] = defaultdict(int)
    for finding in findings:
        scan_result = scan_result_map.get(finding.scan_result_id)
        if scan_result is None:
            continue
        year_quarter = execution_lookup.get(scan_result.operation_execution_id)
        if year_quarter:
            counts[year_quarter] += 1

    labels = sorted(counts.keys())
    return {
        "points": [
            {
                "label": f"{year} - {QUARTER_LABELS[quarter]}",
                "year": year,
                "quarter": quarter,
                "count": counts[(year, quarter)],
            }
            for year, quarter in labels
        ]
    }

from __future__ import annotations

from typing import Any


TABLE_PURPOSES = {
    "account_group": "Stores user account groups or roles used for access control.",
    "account_group_permission": "Links account groups to application permissions and records whether each permission is enabled.",
    "agent": "Stores scan or processing agents, including connection details and the latest runtime status.",
    "agent_capability": "Stores capabilities supported by each agent so the system can choose suitable agents for tasks.",
    "agent_update_history": "Stores the update history for agent packages and versions.",
    "agent_update_package": "Stores metadata for agent software update packages.",
    "app_permission": "Stores application permissions grouped by module for role-based authorization.",
    "finding_asset": "Stores assets related to a finding, such as IPs, domains, URLs, or additional metadata.",
    "generated_report": "Stores generated report files and the execution or template context used to create them.",
    "operation": "Stores scan operations or workflows, including schedule configuration and activation status.",
    "operation_execution": "Stores each concrete run of an operation, including status, timing, scan period, and summary.",
    "operation_result_import_export": "Stores import/export history for operation results.",
    "operation_task": "Assigns tasks to operations, including execution order and input override configuration.",
    "report_snapshot": "Stores report data snapshots captured when a report is generated.",
    "report_template": "Stores report templates and their filter/layout configuration.",
    "scan_import_batch": "Stores metadata for a historical scan data import batch.",
    "scan_result": "Stores parsed scan results at the target and task-execution level.",
    "scan_result_finding": "Stores individual vulnerabilities or findings detected from scan results.",
    "target": "Stores scan targets such as networks, IP ranges, domains, or URLs.",
    "target_attribute_definition": "Defines dynamic attributes that can be assigned to targets.",
    "target_attribute_value": "Stores dynamic attribute values for each target.",
    "target_group": "Stores target groups used for classification, filtering, scans, and reporting.",
    "target_group_mapping": "Links targets to target groups.",
    "task": "Stores task or script definitions that agents can execute.",
    "task_execution": "Stores each task run inside an operation execution.",
    "user_account": "Stores login accounts and their assigned permission group.",
    "vulnerability": "Stores normalized vulnerability definitions used to map and enrich findings.",
    "vulnerability_reference": "Stores external references for a vulnerability.",
    "vulnerability_script": "Stores scripts used to test or verify vulnerabilities.",
}


COLUMN_PURPOSES = {
    "id": "Auto-increment primary key for the row.",
    "code": "Business identifier, usually unique and human-readable.",
    "name": "Display name for the row.",
    "description": "Business description or explanatory note.",
    "created_at": "Timestamp when the row was created.",
    "updated_at": "Timestamp when the row was last updated.",
    "is_active": "Boolean flag indicating whether the row is active.",
    "status": "Current processing or runtime status.",
    "note": "Additional note for the row or processing run.",
    "summary_json": "JSON summary used for display, reporting, or processing.",
    "metadata_json": "Extended metadata stored as JSON.",
    "input_schema_json": "JSON schema describing the input expected by a task or script.",
    "output_schema_json": "JSON schema describing the output returned by a task or script.",
    "input_override_json": "JSON input override applied when a task is assigned to an operation.",
    "input_data_json": "Actual task input payload for a task execution.",
    "output_data_json": "Actual task output payload for a task execution.",
    "normalized_output_json": "Normalized scan output stored as JSON.",
    "raw_output": "Raw output from the tool or agent before normalization.",
    "raw_log": "Raw execution log for a task run.",
    "file_path": "Filesystem path of the related file.",
    "file_name": "Name of the related file.",
    "file_format": "File format, such as csv, xlsx, or json.",
    "version": "Version of a task, script, agent, or package.",
    "old_version": "Version before an update.",
    "new_version": "Version after an update.",
    "package_name": "Agent update package name.",
    "package_version": "Agent update package version.",
    "checksum": "Checksum used to validate file or package integrity.",
    "username": "User login name.",
    "full_name": "User full name.",
    "email": "User email address.",
    "password_hash": "Hashed password; never use it for display.",
    "last_login_at": "Timestamp of the user's latest login.",
    "is_enabled": "Boolean flag indicating whether a permission link is enabled.",
    "module_name": "Application module that owns the permission.",
    "permission_id": "Foreign key to the application permission.",
    "group_id": "Foreign key to the account group.",
    "agent_id": "Foreign key to the agent that owns or executed the data.",
    "agent_type": "Agent or tool type, such as nmap, nuclei, or acunetix.",
    "host": "Agent host name or address.",
    "ip_address": "IP address of the agent or host.",
    "port": "Service port related to an agent, target, or finding.",
    "duration": "Measured duration or runtime counter, usually in seconds.",
    "old_time": "Previous timestamp used for status-change tracking.",
    "old_status": "Previous status value.",
    "status_note": "Detailed note about agent status.",
    "last_seen_at": "Timestamp when the agent was last seen or sent a heartbeat.",
    "capability_code": "Agent capability code.",
    "capability_name": "Agent capability display name.",
    "update_package_id": "Foreign key to the agent update package.",
    "executed_at": "Timestamp when an import, export, or update action was executed.",
    "script_name": "Task or vulnerability script name.",
    "script_path": "Filesystem path of the script.",
    "script_content": "Script content stored in the database.",
    "script_type": "Script type, such as py or another supported type.",
    "max_concurrency_per_agent": "Maximum concurrent tasks of this type per agent; 0 usually means no specific limit.",
    "schedule_type": "Operation schedule type, such as none, cron, or interval.",
    "schedule_config_json": "Operation schedule configuration stored as JSON.",
    "operation_id": "Foreign key to the operation.",
    "task_id": "Foreign key to the task.",
    "order_index": "Task order inside an operation.",
    "continue_on_error": "Boolean flag allowing the operation to continue if this task fails.",
    "execution_code": "Unique code for an operation execution.",
    "trigger_type": "Execution trigger source, such as manual, cron, or interval.",
    "started_at": "Timestamp when processing started.",
    "finished_at": "Timestamp when processing finished.",
    "year": "Year of the scan or import period.",
    "quarter": "Quarter of the scan or import period.",
    "week": "Week of the scan or import period.",
    "source_root_path": "Source directory used during data import.",
    "selected_target_ids_json": "JSON list of target IDs selected for a run or import.",
    "operation_execution_id": "Foreign key to the operation execution.",
    "operation_task_id": "Foreign key to the task assignment inside an operation.",
    "target_id": "Foreign key to the target.",
    "target_type": "Target type, such as network, domain, or url.",
    "ip_range": "Target IP range or single IP address.",
    "domain": "Target domain or URL.",
    "attribute_code": "Code of a dynamic target attribute.",
    "attribute_name": "Display name of a dynamic target attribute.",
    "data_type": "Expected data type of a dynamic target attribute.",
    "is_required": "Boolean flag indicating whether the attribute is required.",
    "default_value": "Default value for the attribute.",
    "attribute_definition_id": "Foreign key to the target attribute definition.",
    "value_text": "Actual value of a dynamic target attribute.",
    "target_group_id": "Foreign key to the target group.",
    "title": "Vulnerability or finding title.",
    "level": "Numeric severity level of a vulnerability.",
    "threat": "Risk or impact description of a vulnerability.",
    "proposal": "Recommended remediation for a vulnerability.",
    "poc_file_name": "Name of the proof-of-concept or evidence file.",
    "poc_file_path": "Filesystem path of the PoC file.",
    "poc_file_mime_type": "MIME type of the PoC file.",
    "poc_file_size": "PoC file size in bytes.",
    "poc_text": "Proof-of-concept content stored as text.",
    "vulnerability_id": "Foreign key to the normalized vulnerability.",
    "ref_type": "Reference type, such as CVE, CWE, URL, or vendor advisory.",
    "ref_value": "External vulnerability reference value.",
    "url": "Reference URL.",
    "task_execution_id": "Foreign key to the task execution.",
    "source_tool": "Tool or agent that produced the scan result.",
    "detected_at": "Timestamp when the result or finding was detected.",
    "parse_status": "Status of scan-result parsing.",
    "scan_result_id": "Foreign key to the scan result.",
    "scan_result_finding_id": "Foreign key to the finding.",
    "finding_code": "Finding identifier.",
    "severity": "Text severity of the finding.",
    "protocol": "Service protocol, such as tcp, udp, or http.",
    "service_name": "Detected service name on the port.",
    "evidence": "Technical evidence for the finding.",
    "confidence": "Confidence score for the finding.",
    "first_seen_at": "Timestamp when the finding was first observed.",
    "last_seen_at": "Timestamp when the finding was most recently observed.",
    "asset_type": "Type of asset related to the finding.",
    "asset_value": "Asset value, such as an IP, domain, or URL.",
    "action_type": "Import or export action type.",
    "batch_code": "Code of the scan import batch.",
    "scan_year": "Historical scan year.",
    "scan_quarter": "Historical scan quarter.",
    "scan_week": "Historical scan week.",
    "scan_started_at": "Timestamp when the imported scan started.",
    "scan_finished_at": "Timestamp when the imported scan finished.",
    "source_file_name": "Source file name used for import.",
    "report_type": "Report type.",
    "filter_config_json": "Report-template filter configuration stored as JSON.",
    "layout_config_json": "Report-template layout configuration stored as JSON.",
    "report_template_id": "Foreign key to the report template.",
    "generated_at": "Timestamp when the report was generated.",
    "generated_by": "User or process that generated the report.",
    "generated_report_id": "Foreign key to the generated report.",
    "snapshot_date": "Timestamp of the report data snapshot.",
    "data_json": "Report snapshot data stored as JSON.",
}


def table_kind(table: dict[str, Any]) -> str:
    return "link" if len(table.get("foreign_keys") or []) >= 2 else "main"


def table_kind_label(table: dict[str, Any]) -> str:
    return "link / assignment" if table_kind(table) == "link" else "main table"


def humanize_name(value: str) -> str:
    return value.replace("_", " ")


def foreign_key_for_column(table: dict[str, Any], column_name: str) -> dict[str, Any] | None:
    for fk in table.get("foreign_keys") or []:
        if fk.get("column") == column_name:
            return fk
    return None


def table_purpose(table: dict[str, Any]) -> str:
    name = table["name"]
    if name in TABLE_PURPOSES:
        return TABLE_PURPOSES[name]
    foreign_keys = table.get("foreign_keys") or []
    if len(foreign_keys) >= 2:
        references = ", ".join(fk["references_table"] for fk in foreign_keys)
        return f"Links or assigns data between the main tables: {references}."
    if name.endswith("_history"):
        return "Stores change history or processing history for the related entity."
    if name.endswith("_mapping"):
        return "Maps many-to-many relationships between main entities."
    if name.endswith("_reference"):
        return "Stores external references for the related main entity."
    return f"Stores business data for the {humanize_name(name)} entity."


def column_purpose(table: dict[str, Any], column: dict[str, Any]) -> str:
    fk = foreign_key_for_column(table, column["name"])
    if fk:
        return (
            f"Foreign key to {fk['references_table']}.{fk['references_column']}; "
            f"use it to join {table['name']} with {fk['references_table']}."
        )
    name = column["name"]
    if name in COLUMN_PURPOSES:
        return COLUMN_PURPOSES[name]
    if name.endswith("_json"):
        return "Stores configuration or extended payload data as JSON."
    if name.endswith("_at"):
        return "Timestamp related to the row status or lifecycle."
    if name.endswith("_id"):
        return "Identifier column that may link to another entity; check foreign keys when present."
    if name.startswith("is_"):
        return "Boolean flag representing a true/false state for the row."
    return f"Stores the {humanize_name(name)} value for the {table['name']} table."


def format_column_constraints(table: dict[str, Any], column: dict[str, Any]) -> str:
    constraints = []
    if column.get("key"):
        constraints.append(f"key={column['key']}")
    constraints.append("nullable=YES" if column.get("nullable") else "nullable=NO")
    if column.get("default") is not None:
        constraints.append(f"default={column['default']}")
    if column.get("extra"):
        constraints.append(f"extra={column['extra']}")
    fk = foreign_key_for_column(table, column["name"])
    if fk:
        constraints.append(
            f"FK {fk['constraint']}: {table['name']}.{fk['column']} -> "
            f"{fk['references_table']}.{fk['references_column']}"
        )
    return "; ".join(constraints)


def build_schema_text_for_ai(schema_document: dict[str, Any]) -> str:
    lines = [
        f"DATABASE SCHEMA: {schema_document.get('schema') or '(current database)'}",
        "",
        "TABLES",
    ]

    tables = schema_document.get("tables") or []
    for table in tables:
        lines.extend(
            [
                "",
                f"## {table['name']}",
                f"Table purpose: {table_purpose(table)}",
                f"Table type: {table_kind_label(table)}",
                "Columns:",
            ]
        )
        for column in table.get("columns") or []:
            lines.extend(
                [
                    f"- {column['name']}",
                    f"  - Data type: {column['type']}",
                    f"  - Constraints: {format_column_constraints(table, column) or 'no special constraint'}",
                    f"  - Column purpose: {column_purpose(table, column)}",
                ]
            )
        if table.get("foreign_keys"):
            lines.append("Foreign keys:")
            for fk in table["foreign_keys"]:
                lines.append(
                    f"- {fk['constraint']}: {table['name']}.{fk['column']} -> "
                    f"{fk['references_table']}.{fk['references_column']}"
                )

    lines.extend(["", "ALL FOREIGN KEY RELATIONSHIPS"])
    relationships = [
        f"{fk['constraint']}: {table['name']}.{fk['column']} -> {fk['references_table']}.{fk['references_column']}"
        for table in tables
        for fk in table.get("foreign_keys") or []
    ]
    if relationships:
        lines.extend(f"- {relationship}" for relationship in relationships)
    else:
        lines.append("- No foreign keys are present in the current schema response.")

    return "\n".join(lines)

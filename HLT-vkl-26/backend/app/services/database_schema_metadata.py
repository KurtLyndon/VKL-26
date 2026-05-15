from __future__ import annotations

from typing import Any


TABLE_PURPOSES = {
    "account_group": "Luu nhom tai khoan/role dung de phan quyen nguoi dung trong he thong.",
    "account_group_permission": "Bang lien ket giua nhom tai khoan va quyen, cho biet quyen nao duoc bat cho tung nhom.",
    "agent": "Luu thong tin agent/worker thuc thi tac vu scan hoac xu ly du lieu, kem trang thai runtime gan nhat.",
    "agent_capability": "Luu nang luc/chuc nang ma tung agent ho tro de he thong chon agent phu hop khi chay task.",
    "agent_update_history": "Luu lich su cap nhat phien ban/package cho agent.",
    "agent_update_package": "Luu metadata cac goi cap nhat phan mem agent.",
    "app_permission": "Danh muc quyen thao tac theo module de gan cho nhom tai khoan.",
    "finding_asset": "Luu asset lien quan toi mot finding nhu IP, domain, URL hoac metadata phu.",
    "generated_report": "Luu file bao cao da sinh ra tu template va du lieu execution.",
    "operation": "Danh muc operation/quy trinh scan gom cau hinh lich chay va trang thai kich hoat.",
    "operation_execution": "Luu tung lan chay cu the cua mot operation, gom trang thai, thoi gian, ky scan va summary.",
    "operation_result_import_export": "Luu lich su import/export ket qua cua mot operation.",
    "operation_task": "Bang phan cong cac task nam trong mot operation, gom thu tu chay va cau hinh override.",
    "report_snapshot": "Luu snapshot du lieu bao cao tai thoi diem sinh bao cao.",
    "report_template": "Danh muc mau bao cao va cau hinh layout/filter.",
    "scan_import_batch": "Luu metadata cua mot dot import du lieu scan lich su.",
    "scan_result": "Luu ket qua scan da parse o cap target/task execution.",
    "scan_result_finding": "Luu tung lo hong/finding phat hien tu scan_result.",
    "target": "Danh muc muc tieu scan nhu network, IP range, domain hoac URL.",
    "target_attribute_definition": "Dinh nghia thuoc tinh dong co the gan cho target.",
    "target_attribute_value": "Luu gia tri thuoc tinh dong cua tung target.",
    "target_group": "Danh muc nhom target de phan loai hoac loc khi scan/bao cao.",
    "target_group_mapping": "Bang lien ket target voi target_group.",
    "task": "Danh muc task/script ma agent co the thuc thi.",
    "task_execution": "Luu tung lan thuc thi task trong mot operation_execution.",
    "user_account": "Luu tai khoan dang nhap va lien ket nhom quyen.",
    "vulnerability": "Danh muc lo hong chuan hoa dung de map voi finding.",
    "vulnerability_reference": "Luu tai lieu/tham chieu ben ngoai cua vulnerability.",
    "vulnerability_script": "Luu script kiem tra/xac minh vulnerability.",
}


COLUMN_PURPOSES = {
    "id": "Khoa chinh tu tang cua ban ghi.",
    "code": "Ma dinh danh nghiep vu, thuong unique de tham chieu de doc.",
    "name": "Ten hien thi cua ban ghi.",
    "description": "Mo ta nghiep vu hoac ghi chu giai thich ban ghi.",
    "created_at": "Thoi diem tao ban ghi.",
    "updated_at": "Thoi diem cap nhat ban ghi gan nhat.",
    "is_active": "Co cho biet ban ghi dang duoc su dung hay da tat.",
    "status": "Trang thai xu ly/runtime hien tai cua ban ghi.",
    "note": "Ghi chu bo sung cho ban ghi hoac lan xu ly.",
    "summary_json": "Du lieu tong hop dang JSON phuc vu hien thi hoac bao cao.",
    "metadata_json": "Metadata mo rong dang JSON.",
    "input_schema_json": "Schema JSON mo ta input ma task/script can nhan.",
    "output_schema_json": "Schema JSON mo ta output ma task/script tra ve.",
    "input_override_json": "JSON override input mac dinh khi task duoc gan vao operation.",
    "input_data_json": "Payload input thuc te cua mot lan chay task.",
    "output_data_json": "Payload output thuc te cua mot lan chay task.",
    "normalized_output_json": "Ket qua scan da chuan hoa dang JSON.",
    "raw_output": "Output goc tu tool/agent truoc khi chuan hoa.",
    "raw_log": "Log tho cua qua trinh thuc thi task.",
    "file_path": "Duong dan file trong he thong.",
    "file_name": "Ten file lien quan toi ban ghi.",
    "file_format": "Dinh dang file nhu csv, xlsx hoac json.",
    "version": "Phien ban cua task, script, agent hoac package.",
    "old_version": "Phien ban cu truoc khi cap nhat.",
    "new_version": "Phien ban moi sau khi cap nhat.",
    "package_name": "Ten goi cap nhat agent.",
    "package_version": "Phien ban goi cap nhat agent.",
    "checksum": "Checksum dung de kiem tra tinh toan ven file/package.",
    "username": "Ten dang nhap cua user.",
    "full_name": "Ten day du cua user.",
    "email": "Email lien he hoac dang nhap cua user.",
    "password_hash": "Mat khau da hash, khong dung de hien thi truc tiep.",
    "last_login_at": "Thoi diem dang nhap gan nhat.",
    "is_enabled": "Co bat/tat quyen hoac lien ket quyen.",
    "module_name": "Ten module chuc nang chua quyen.",
    "permission_id": "Khoa ngoai toi quyen ung dung.",
    "group_id": "Khoa ngoai toi nhom tai khoan.",
    "agent_id": "Khoa ngoai toi agent thuc thi hoac so huu du lieu.",
    "agent_type": "Loai agent/tool xu ly nhu nmap, nuclei, acunetix.",
    "host": "Hostname hoac dia chi host cua agent.",
    "ip_address": "Dia chi IP cua agent hoac host.",
    "port": "Cong dich vu lien quan toi agent, target hoac finding.",
    "duration": "Thoi luong hoac so giay do duoc cho trang thai/runtime.",
    "old_time": "Moc thoi gian truoc do dung de theo doi thay doi trang thai.",
    "old_status": "Trang thai truoc do cua agent/ban ghi.",
    "status_note": "Ghi chu chi tiet ve trang thai agent.",
    "last_seen_at": "Thoi diem agent heartbeat hoac xuat hien gan nhat.",
    "capability_code": "Ma nang luc agent.",
    "capability_name": "Ten nang luc agent.",
    "update_package_id": "Khoa ngoai toi goi cap nhat agent.",
    "executed_at": "Thoi diem thao tac import/export/cap nhat duoc thuc thi.",
    "script_name": "Ten file hoac ten script task/vulnerability.",
    "script_path": "Duong dan script tren he thong.",
    "script_content": "Noi dung script duoc luu trong database.",
    "script_type": "Loai script nhu py hoac template tuong ung.",
    "max_concurrency_per_agent": "So task cung loai toi da cho moi agent; 0 thuong nghia la khong gioi han rieng.",
    "schedule_type": "Kieu lich chay operation nhu none, cron hoac interval.",
    "schedule_config_json": "Cau hinh lich chay operation dang JSON.",
    "operation_id": "Khoa ngoai toi operation.",
    "task_id": "Khoa ngoai toi task.",
    "order_index": "Thu tu task trong operation.",
    "continue_on_error": "Cho phep operation tiep tuc khi task nay loi.",
    "execution_code": "Ma dinh danh duy nhat cua mot lan chay operation.",
    "trigger_type": "Nguon kich hoat execution nhu manual, cron hoac interval.",
    "started_at": "Thoi diem bat dau chay.",
    "finished_at": "Thoi diem ket thuc chay.",
    "year": "Nam cua ky du lieu scan/import.",
    "quarter": "Quy cua ky du lieu scan/import.",
    "week": "Tuan cua ky du lieu scan/import.",
    "source_root_path": "Thu muc nguon chua du lieu import.",
    "selected_target_ids_json": "Danh sach target duoc chon trong lan chay/import dang JSON.",
    "operation_execution_id": "Khoa ngoai toi lan chay operation.",
    "operation_task_id": "Khoa ngoai toi task duoc cau hinh trong operation.",
    "target_id": "Khoa ngoai toi target.",
    "target_type": "Loai target nhu network, domain hoac url.",
    "ip_range": "Dai IP hoac IP don cua target.",
    "domain": "Domain hoac URL cua target.",
    "attribute_code": "Ma thuoc tinh dong cua target.",
    "attribute_name": "Ten hien thi cua thuoc tinh dong.",
    "data_type": "Kieu du lieu ky vong cua thuoc tinh dong.",
    "is_required": "Co cho biet thuoc tinh co bat buoc nhap hay khong.",
    "default_value": "Gia tri mac dinh cua thuoc tinh.",
    "attribute_definition_id": "Khoa ngoai toi dinh nghia thuoc tinh target.",
    "value_text": "Gia tri thuc te cua thuoc tinh target.",
    "target_group_id": "Khoa ngoai toi nhom target.",
    "title": "Tieu de vulnerability/finding.",
    "level": "Muc do nghiem trong dang so cua vulnerability.",
    "threat": "Mo ta nguy co/tac dong cua vulnerability.",
    "proposal": "Khuyen nghi xu ly vulnerability.",
    "poc_file_name": "Ten file bang chung khai thac hoac PoC.",
    "poc_file_path": "Duong dan file PoC.",
    "poc_file_mime_type": "MIME type cua file PoC.",
    "poc_file_size": "Kich thuoc file PoC tinh theo byte.",
    "poc_text": "Noi dung PoC dang text.",
    "vulnerability_id": "Khoa ngoai toi vulnerability chuan hoa.",
    "ref_type": "Loai tham chieu nhu CVE, CWE, URL hoac vendor advisory.",
    "ref_value": "Gia tri ma tham chieu vulnerability.",
    "url": "Duong dan URL tham chieu.",
    "task_execution_id": "Khoa ngoai toi lan chay task.",
    "source_tool": "Ten tool/agent sinh ra ket qua scan.",
    "detected_at": "Thoi diem phat hien ket qua/finding.",
    "parse_status": "Trang thai parse du lieu scan.",
    "scan_result_id": "Khoa ngoai toi scan_result.",
    "scan_result_finding_id": "Khoa ngoai toi finding.",
    "finding_code": "Ma dinh danh finding.",
    "severity": "Muc do nghiem trong dang text cua finding.",
    "protocol": "Giao thuc dich vu nhu tcp/udp/http.",
    "service_name": "Ten dich vu phat hien tren port.",
    "evidence": "Bang chung ky thuat cua finding.",
    "confidence": "Do tin cay cua finding.",
    "first_seen_at": "Thoi diem finding xuat hien lan dau.",
    "last_seen_at": "Thoi diem finding xuat hien gan nhat.",
    "asset_type": "Loai asset lien quan toi finding.",
    "asset_value": "Gia tri asset nhu IP, domain hoac URL.",
    "action_type": "Loai thao tac import hoac export.",
    "batch_code": "Ma dot import du lieu scan.",
    "scan_year": "Nam du lieu scan lich su.",
    "scan_quarter": "Quy du lieu scan lich su.",
    "scan_week": "Tuan du lieu scan lich su.",
    "scan_started_at": "Thoi diem bat dau scan trong du lieu import.",
    "scan_finished_at": "Thoi diem ket thuc scan trong du lieu import.",
    "source_file_name": "Ten file nguon dung de import.",
    "report_type": "Loai bao cao.",
    "filter_config_json": "Cau hinh loc du lieu cho report template.",
    "layout_config_json": "Cau hinh bo cuc report template.",
    "report_template_id": "Khoa ngoai toi report_template.",
    "generated_at": "Thoi diem sinh bao cao.",
    "generated_by": "Nguoi hoac tien trinh sinh bao cao.",
    "generated_report_id": "Khoa ngoai toi generated_report.",
    "snapshot_date": "Thoi diem snapshot du lieu bao cao.",
    "data_json": "Du lieu snapshot/report dang JSON.",
}


def table_kind(table: dict[str, Any]) -> str:
    return "link" if len(table.get("foreign_keys") or []) >= 2 else "main"


def table_kind_label(table: dict[str, Any]) -> str:
    return "lien ket / phan cong" if table_kind(table) == "link" else "bang chinh"


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
        return f"Bang lien ket/phan cong du lieu giua cac bang chinh: {references}."
    if name.endswith("_history"):
        return "Luu lich su thay doi hoac lich su xu ly cua thuc the lien quan."
    if name.endswith("_mapping"):
        return "Bang mapping/lien ket nhieu-nhieu giua cac thuc the chinh."
    if name.endswith("_reference"):
        return "Luu thong tin tham chieu ngoai cua thuc the chinh."
    return f"Luu du lieu nghiep vu cho thuc the {humanize_name(name)}."


def column_purpose(table: dict[str, Any], column: dict[str, Any]) -> str:
    fk = foreign_key_for_column(table, column["name"])
    if fk:
        return (
            f"Khoa ngoai lien ket toi {fk['references_table']}.{fk['references_column']}, "
            f"dung de join bang {table['name']} voi {fk['references_table']}."
        )
    name = column["name"]
    if name in COLUMN_PURPOSES:
        return COLUMN_PURPOSES[name]
    if name.endswith("_json"):
        return "Du lieu cau hinh hoac payload mo rong dang JSON."
    if name.endswith("_at"):
        return "Moc thoi gian lien quan toi trang thai hoac vong doi ban ghi."
    if name.endswith("_id"):
        return "Cot dinh danh lien ket toi thuc the khac; kiem tra foreign key neu co."
    if name.startswith("is_"):
        return "Co boolean bieu thi trang thai dung/sai cua ban ghi."
    return f"Luu gia tri {humanize_name(name)} cua bang {table['name']}."


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
        "Muc dich: Dung tai lieu nay de hoi AI viet cau SELECT an toan, dung bang, dung cot va dung quan he join.",
        "Quy uoc: Chi nen dung SELECT de doc du lieu. Cac quan he FK ben duoi la goi y join chinh xac.",
        "",
        "TABLES",
    ]

    tables = schema_document.get("tables") or []
    for table in tables:
        lines.extend(
            [
                "",
                f"## {table['name']}",
                f"Muc dich bang: {table_purpose(table)}",
                f"Loai bang: {table_kind_label(table)}",
                "Cot:",
            ]
        )
        for column in table.get("columns") or []:
            lines.extend(
                [
                    f"- {column['name']}",
                    f"  - Kieu du lieu: {column['type']}",
                    f"  - Constraints: {format_column_constraints(table, column) or 'khong co constraint dac biet'}",
                    f"  - Muc dich cot: {column_purpose(table, column)}",
                ]
            )
        if table.get("foreign_keys"):
            lines.append("Khoa ngoai cua bang:")
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
        lines.append("- Khong co foreign key trong schema response hien tai.")

    return "\n".join(lines)

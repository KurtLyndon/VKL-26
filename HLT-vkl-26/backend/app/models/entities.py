from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Agent(Base, TimestampMixin):
    __tablename__ = "agent"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    agent_type: Mapped[str] = mapped_column(String(100), index=True)
    host: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="offline")
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class AccountGroup(Base, TimestampMixin):
    __tablename__ = "account_group"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class AppPermission(Base):
    __tablename__ = "app_permission"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    module_name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AccountGroupPermission(Base, TimestampMixin):
    __tablename__ = "account_group_permission"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("account_group.id"), index=True)
    permission_id: Mapped[int] = mapped_column(ForeignKey("app_permission.id"), index=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    group: Mapped["AccountGroup"] = relationship()
    permission: Mapped["AppPermission"] = relationship()


class UserAccount(Base, TimestampMixin):
    __tablename__ = "user_account"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    group_id: Mapped[int | None] = mapped_column(ForeignKey("account_group.id"), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    group: Mapped["AccountGroup | None"] = relationship()


class AgentCapability(Base):
    __tablename__ = "agent_capability"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agent.id"), index=True)
    capability_code: Mapped[str] = mapped_column(String(100))
    capability_name: Mapped[str] = mapped_column(String(255))
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    agent: Mapped[Agent] = relationship()


class AgentUpdatePackage(Base):
    __tablename__ = "agent_update_package"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    agent_type: Mapped[str] = mapped_column(String(100), index=True)
    package_name: Mapped[str] = mapped_column(String(255))
    package_version: Mapped[str] = mapped_column(String(50))
    file_path: Mapped[str] = mapped_column(String(500))
    checksum: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AgentUpdateHistory(Base):
    __tablename__ = "agent_update_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agent.id"), index=True)
    update_package_id: Mapped[int] = mapped_column(ForeignKey("agent_update_package.id"), index=True)
    old_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    new_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    executed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class Task(Base, TimestampMixin):
    __tablename__ = "task"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    agent_type: Mapped[str] = mapped_column(String(100), index=True)
    script_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    script_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    script_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    input_schema_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    output_schema_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Operation(Base, TimestampMixin):
    __tablename__ = "operation"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    schedule_type: Mapped[str] = mapped_column(String(30), default="none")
    schedule_config_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class OperationTask(Base):
    __tablename__ = "operation_task"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    operation_id: Mapped[int] = mapped_column(ForeignKey("operation.id"), index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("task.id"), index=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    input_override_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    continue_on_error: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    task: Mapped["Task"] = relationship()


class OperationExecution(Base):
    __tablename__ = "operation_execution"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    operation_id: Mapped[int] = mapped_column(ForeignKey("operation.id"), index=True)
    execution_code: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    trigger_type: Mapped[str] = mapped_column(String(30), default="manual")
    status: Mapped[str] = mapped_column(String(30), default="pending")
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quarter: Mapped[int | None] = mapped_column(Integer, nullable=True)
    week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_root_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    selected_target_ids_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    summary_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    operation: Mapped["Operation"] = relationship()


class TaskExecution(Base):
    __tablename__ = "task_execution"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    operation_execution_id: Mapped[int] = mapped_column(ForeignKey("operation_execution.id"), index=True)
    operation_task_id: Mapped[int] = mapped_column(ForeignKey("operation_task.id"), index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("task.id"), index=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agent.id"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    input_data_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    output_data_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    raw_log: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    agent: Mapped["Agent"] = relationship()
    task: Mapped["Task"] = relationship()


class Target(Base, TimestampMixin):
    __tablename__ = "target"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    target_type: Mapped[str] = mapped_column(String(50), default="network")
    ip_range: Mapped[str | None] = mapped_column(String(255), nullable=True)
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class TargetAttributeDefinition(Base):
    __tablename__ = "target_attribute_definition"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    attribute_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    attribute_name: Mapped[str] = mapped_column(String(255))
    data_type: Mapped[str] = mapped_column(String(30), default="text")
    is_required: Mapped[bool] = mapped_column(Boolean, default=False)
    default_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class TargetAttributeValue(Base, TimestampMixin):
    __tablename__ = "target_attribute_value"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    target_id: Mapped[int] = mapped_column(ForeignKey("target.id"), index=True)
    attribute_definition_id: Mapped[int] = mapped_column(ForeignKey("target_attribute_definition.id"), index=True)
    value_text: Mapped[str | None] = mapped_column(Text, nullable=True)


class TargetGroup(Base):
    __tablename__ = "target_group"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class TargetGroupMapping(Base):
    __tablename__ = "target_group_mapping"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    target_id: Mapped[int] = mapped_column(ForeignKey("target.id"), index=True)
    target_group_id: Mapped[int] = mapped_column(ForeignKey("target_group.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Vulnerability(Base, TimestampMixin):
    __tablename__ = "vulnerability"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    level: Mapped[int] = mapped_column(Integer, default=0)
    threat: Mapped[str | None] = mapped_column(Text, nullable=True)
    proposal: Mapped[str | None] = mapped_column(Text, nullable=True)
    poc_file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    poc_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class VulnerabilityReference(Base):
    __tablename__ = "vulnerability_reference"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    vulnerability_id: Mapped[int] = mapped_column(ForeignKey("vulnerability.id"), index=True)
    ref_type: Mapped[str] = mapped_column(String(50))
    ref_value: Mapped[str] = mapped_column(String(255))
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class VulnerabilityScript(Base, TimestampMixin):
    __tablename__ = "vulnerability_script"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    vulnerability_id: Mapped[int] = mapped_column(ForeignKey("vulnerability.id"), index=True)
    script_name: Mapped[str] = mapped_column(String(255))
    script_type: Mapped[str] = mapped_column(String(30), default="py")
    script_content: Mapped[str] = mapped_column(Text)
    version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class ScanResult(Base):
    __tablename__ = "scan_result"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    operation_execution_id: Mapped[int] = mapped_column(ForeignKey("operation_execution.id"), index=True)
    task_execution_id: Mapped[int] = mapped_column(ForeignKey("task_execution.id"), index=True)
    target_id: Mapped[int] = mapped_column(ForeignKey("target.id"), index=True)
    agent_type: Mapped[str] = mapped_column(String(100))
    source_tool: Mapped[str | None] = mapped_column(String(100), nullable=True)
    raw_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    normalized_output_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    detected_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    parse_status: Mapped[str] = mapped_column(String(30), default="success")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ScanResultFinding(Base, TimestampMixin):
    __tablename__ = "scan_result_finding"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    scan_result_id: Mapped[int] = mapped_column(ForeignKey("scan_result.id"), index=True)
    vulnerability_id: Mapped[int | None] = mapped_column(ForeignKey("vulnerability.id"), nullable=True, index=True)
    finding_code: Mapped[str] = mapped_column(String(100))
    severity: Mapped[str | None] = mapped_column(String(30), nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    protocol: Mapped[str | None] = mapped_column(String(20), nullable=True)
    service_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    poc_file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    poc_file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    poc_file_mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    poc_file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    first_seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="open")


class FindingAsset(Base):
    __tablename__ = "finding_asset"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    scan_result_finding_id: Mapped[int] = mapped_column(ForeignKey("scan_result_finding.id"), index=True)
    target_id: Mapped[int | None] = mapped_column(ForeignKey("target.id"), nullable=True, index=True)
    asset_type: Mapped[str] = mapped_column(String(50))
    asset_value: Mapped[str] = mapped_column(String(255))
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class OperationResultImportExport(Base):
    __tablename__ = "operation_result_import_export"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    operation_id: Mapped[int] = mapped_column(ForeignKey("operation.id"), index=True)
    action_type: Mapped[str] = mapped_column(String(30))
    file_name: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_format: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(30), default="pending")
    executed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class ScanImportBatch(Base, TimestampMixin):
    __tablename__ = "scan_import_batch"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    operation_execution_id: Mapped[int] = mapped_column(ForeignKey("operation_execution.id"), index=True)
    task_execution_id: Mapped[int] = mapped_column(ForeignKey("task_execution.id"), index=True)
    batch_code: Mapped[str] = mapped_column(String(100), index=True)
    scan_year: Mapped[int] = mapped_column(Integer)
    scan_quarter: Mapped[int] = mapped_column(Integer)
    scan_week: Mapped[int] = mapped_column(Integer)
    scan_started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    scan_finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_root_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_file_name: Mapped[str] = mapped_column(String(255))
    selected_target_ids_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    summary_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class ReportTemplate(Base, TimestampMixin):
    __tablename__ = "report_template"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    report_type: Mapped[str] = mapped_column(String(50))
    filter_config_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    layout_config_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class GeneratedReport(Base):
    __tablename__ = "generated_report"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    report_template_id: Mapped[int] = mapped_column(ForeignKey("report_template.id"), index=True)
    operation_execution_id: Mapped[int | None] = mapped_column(ForeignKey("operation_execution.id"), nullable=True, index=True)
    file_name: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    generated_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    summary_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class ReportSnapshot(Base):
    __tablename__ = "report_snapshot"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    generated_report_id: Mapped[int] = mapped_column(ForeignKey("generated_report.id"), index=True)
    snapshot_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    data_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

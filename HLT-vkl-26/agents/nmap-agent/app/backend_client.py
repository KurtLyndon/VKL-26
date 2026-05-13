from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import urljoin

import httpx

from app.config import Settings
from app.schemas import (
    AgentHeartbeatPayload,
    NormalizePayload,
    TaskHeartbeatPayload,
    TaskStatusPayload,
)


class BackendClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _absolute_url(self, path: str) -> str:
        return urljoin(f"{self.settings.normalized_backend_base_url}/", path.lstrip("/"))

    async def _post(self, path: str, payload: dict) -> None:
        async with httpx.AsyncClient(timeout=self.settings.backend_timeout_seconds) as client:
            response = await client.post(self._absolute_url(path), json=payload)
            response.raise_for_status()

    async def send_agent_heartbeat(self, metadata_json: dict | None = None) -> None:
        payload = AgentHeartbeatPayload(
            agent_id=self.settings.agent_id,
            agent_code=self.settings.agent_code,
            status="online",
            host=self.settings.agent_public_host,
            ip_address=self.settings.agent_public_ip,
            port=self.settings.agent_port,
            version=self.settings.agent_version,
            seen_at=datetime.now(timezone.utc),
            metadata_json=metadata_json,
        )
        await self._post("/api/v1/agents/heartbeat", payload.model_dump(mode="json"))

    async def send_task_heartbeat(
        self,
        path: str,
        *,
        raw_log: str | None = None,
        progress_percent: int | None = None,
        output_data_json: dict | None = None,
    ) -> None:
        payload = TaskHeartbeatPayload(
            agent_id=self.settings.agent_id,
            agent_code=self.settings.agent_code,
            status="running",
            raw_log=raw_log,
            progress_percent=progress_percent,
            output_data_json=output_data_json,
            seen_at=datetime.now(timezone.utc),
        )
        await self._post(path, payload.model_dump(mode="json"))

    async def send_task_status(
        self,
        path: str,
        *,
        status: str,
        output_data_json: dict | None = None,
        raw_log: str | None = None,
        raw_output: str | None = None,
    ) -> None:
        payload = TaskStatusPayload(
            status=status,
            output_data_json=output_data_json,
            raw_log=raw_log,
            raw_output=raw_output,
        )
        await self._post(path, payload.model_dump(mode="json"))

    async def send_normalized_result(
        self,
        path: str,
        *,
        raw_output: str,
        operation_execution_id: int,
        task_execution_id: int,
        target_id: int,
    ) -> None:
        payload = NormalizePayload(
            agent_type="nmap",
            source_tool="nmap",
            raw_output=raw_output,
            operation_execution_id=operation_execution_id,
            task_execution_id=task_execution_id,
            target_id=target_id,
            detected_at=datetime.now(timezone.utc),
        )
        await self._post(path, payload.model_dump(mode="json"))

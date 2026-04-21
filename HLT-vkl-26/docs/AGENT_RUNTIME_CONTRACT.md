# Agent Runtime Contract

This document describes the minimal runtime contract now supported by the backend for external agents.

## Execute dispatch

- Backend dispatches `POST /execute` on the external agent.
- Request body matches `AgentExecuteRequest`.
- Response body matches `AgentExecuteResponse`.

### Request fields

- `contract_version`: current contract version string.
- `dispatched_at`: UTC timestamp when backend sent the request.
- `task_execution_id`: backend task execution id.
- `operation_execution_id`: backend operation execution id.
- `agent`: backend metadata for the selected agent record.
- `task`: task metadata including `code`, `script_name`, `script_path`, and version.
- `target`: resolved target metadata plus a normalized `value`.
- `input_data`: merged shared input and operation-task overrides.
- `callback_paths`: backend callback paths for heartbeat, completion, and optional scan normalization.

### Response modes

- Synchronous completion:
  - Return `status="completed"` and include `raw_output`.
  - Backend will mark the task complete and normalize findings immediately.
- Asynchronous acceptance:
  - Return `status="accepted"` or `status="running"`.
  - Backend keeps the task in `running` state and expects follow-up callbacks.

## Heartbeat callbacks

### `POST /api/v1/agents/heartbeat`

Use this to refresh agent liveness.

- Required: `agent_id` or `agent_code`
- Typical payload:
  - `status="online"`
  - `version`, `host`, `ip_address`, `port`
  - `seen_at`

This updates `agent.status` and `agent.last_seen_at`.

### `POST /api/v1/task-executions/{task_execution_id}/heartbeat`

Use this while a dispatched task is still in progress.

- Optional agent guard: `agent_id` or `agent_code`
- Supported status values: `queued`, `running`
- Optional progress fields:
  - `progress_percent`
  - `raw_log`
  - `output_data_json`

This refreshes both the agent heartbeat and the task execution runtime state.

## Completion callback

### `POST /api/v1/task-executions/{task_execution_id}/status`

Use the existing task status API to finish the task.

- `status`: `running`, `completed`, `failed`, or `canceled`
- `output_data_json`: optional final structured output
- `raw_log`: optional final log/error text

If the task completes successfully and the external agent did not already return inline `raw_output`, the agent can optionally call scan normalization next.

## Optional normalization callback

### `POST /api/v1/scan-results/normalize`

Use this when the agent wants the backend parser to normalize raw scan output after asynchronous completion.

Required fields:

- `agent_type`
- `raw_output`
- `operation_execution_id`
- `task_execution_id`
- `target_id`

## Discovery endpoint

Backend exposes `GET /api/v1/agents/runtime/execute-contract` to return the current contract version plus example request and response payloads.

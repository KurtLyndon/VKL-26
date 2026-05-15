import axios from "axios";
import { useAuthStore } from "../stores/auth";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1",
});

api.interceptors.request.use((config) => {
  const auth = useAuthStore();
  if (auth.state.token) {
    config.headers.Authorization = `Bearer ${auth.state.token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      const auth = useAuthStore();
      auth.clearSession();
    }
    return Promise.reject(error);
  }
);

export async function login(payload) {
  const { data } = await api.post("/auth/login", payload);
  return data;
}

export async function getCurrentUser() {
  const { data } = await api.get("/auth/me");
  return data;
}

export async function getList(resource) {
  const { data } = await api.get(`/${resource}`);
  return data;
}

export async function getAgentMonitorOverview() {
  const { data } = await api.get("/agents/monitor/overview");
  return data;
}

export async function runAgentMonitorNow() {
  const { data } = await api.post("/agents/monitor/run");
  return data;
}

export async function createManagedAgent(payload) {
  const { data } = await api.post("/agents/manage", payload);
  return data;
}

export async function updateManagedAgent(agentId, payload) {
  const { data } = await api.put(`/agents/manage/${agentId}`, payload);
  return data;
}

export async function getTaskAgentTypeOptions() {
  const { data } = await api.get("/tasks/agent-types");
  return data;
}

export async function createItem(resource, payload) {
  const { data } = await api.post(`/${resource}`, payload);
  return data;
}

export async function updateItem(resource, id, payload) {
  const { data } = await api.put(`/${resource}/${id}`, payload);
  return data;
}

export async function deleteItem(resource, id) {
  await api.delete(`/${resource}/${id}`);
}

export async function getDashboardSummary() {
  const { data } = await api.get("/dashboard/summary");
  return data;
}

export async function getHistoricalDashboardFilterOptions(filters = {}) {
  const { data } = await api.get("/dashboard/historical/filter-options", { params: filters });
  return data;
}

export async function getHistoricalDashboardOverview(filters = {}) {
  const { data } = await api.get("/dashboard/historical/overview", { params: filters });
  return data;
}

export async function getHistoricalDashboardTotalSummary() {
  const { data } = await api.get("/dashboard/historical/total-summary");
  return data;
}

export async function getHistoricalDashboardTargetOptions() {
  const { data } = await api.get("/dashboard/historical/target-options");
  return data;
}

export async function getHistoricalTargetQuarterlyChart(year, targetIds) {
  const { data } = await api.get("/dashboard/historical/target-quarterly", {
    params: {
      year,
      target_ids: JSON.stringify(targetIds),
    },
  });
  return data;
}

export async function getHistoricalTopVulnerabilities(filters = {}) {
  const { data } = await api.get("/dashboard/historical/top-vulnerabilities", { params: filters });
  return data;
}

export async function getHistoricalCoreGroupOptions() {
  const { data } = await api.get("/dashboard/historical/core-group-options");
  return data;
}

export async function getHistoricalCoreGroupQuarterlyChart(year, groups, metric) {
  const { data } = await api.get("/dashboard/historical/core-group-quarterly", {
    params: {
      year,
      groups: JSON.stringify(groups),
      metric,
    },
  });
  return data;
}

export async function getHistoricalVulnerabilityTrend() {
  const { data } = await api.get("/dashboard/historical/trend");
  return data;
}

export async function getOperationsRuntimeOverview() {
  const { data } = await api.get("/operations/runtime/overview");
  return data;
}

export async function launchOperation(operationId, payload) {
  const { data } = await api.post(`/operations/${operationId}/launch`, payload);
  return data;
}

export async function runMockDemoFlow(payload) {
  const { data } = await api.post("/demo/mock-flow", payload);
  return data;
}

export async function getExecutionTasks(executionId) {
  const { data } = await api.get(`/operation-executions/${executionId}/tasks`);
  return data;
}

export async function getOperationTasks(operationId) {
  const { data } = await api.get(`/operations/${operationId}/tasks`);
  return data;
}

export async function getTargetsEnriched() {
  const { data } = await api.get("/targets-enriched");
  return data;
}

export async function createManagedTarget(payload) {
  const { data } = await api.post("/targets/manage", payload);
  return data;
}

export async function updateManagedTarget(targetId, payload) {
  const { data } = await api.put(`/targets/manage/${targetId}`, payload);
  return data;
}

export async function deleteManagedTarget(targetId) {
  await api.delete(`/targets/manage/${targetId}`);
}

export async function updateTargetAttributeValues(targetId, items) {
  const { data } = await api.put(`/targets/${targetId}/attribute-values`, { items });
  return data;
}

export async function updateTargetGroups(targetId, targetGroupIds) {
  const { data } = await api.put(`/targets/${targetId}/groups`, { target_group_ids: targetGroupIds });
  return data;
}

export async function importTargetsFile(file) {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post("/targets/import", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function createTargetAttributeDefinitionManaged(payload) {
  const { data } = await api.post("/target-attribute-definitions/manage", payload);
  return data;
}

export async function deleteTargetAttributeDefinitionManaged(definitionId) {
  await api.delete(`/target-attribute-definitions/manage/${definitionId}`);
}

export async function createTargetGroupManaged(payload) {
  const { data } = await api.post("/target-groups/manage", payload);
  return data;
}

export async function deleteTargetGroupManaged(groupId) {
  await api.delete(`/target-groups/manage/${groupId}`);
}

export async function updateTargetGroupMembers(groupId, targetIds) {
  const { data } = await api.put(`/target-groups/${groupId}/targets`, { target_ids: targetIds });
  return data;
}

export async function uploadFindingPocFile(findingId, file) {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post(`/scan-findings/${findingId}/poc-file`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function downloadFindingPocFile(findingId) {
  const response = await api.get(`/scan-findings/${findingId}/poc-file`, {
    responseType: "blob",
  });
  return response;
}

export async function deleteFindingPocFile(findingId) {
  const { data } = await api.delete(`/scan-findings/${findingId}/poc-file`);
  return data;
}

export async function getFindingFilterOptions(operationExecutionId = null) {
  const { data } = await api.get("/scan-findings/filter-options", {
    params: operationExecutionId ? { operation_execution_id: operationExecutionId } : {},
  });
  return data;
}

export async function getManagedFindings(filters = {}) {
  const params = {};
  if (filters.operation_execution_id) params.operation_execution_id = filters.operation_execution_id;
  if (filters.target_id) params.target_id = filters.target_id;
  if (filters.status_value) params.status_value = filters.status_value;
  const { data } = await api.get("/scan-findings", { params });
  return data;
}

export async function getManagedFinding(findingId) {
  const { data } = await api.get(`/scan-findings/${findingId}`);
  return data;
}

export async function updateManagedFinding(findingId, payload) {
  const { data } = await api.put(`/scan-findings/${findingId}`, payload);
  return data;
}

export async function updateManagedFindingStatus(findingId, statusValue) {
  const { data } = await api.post(`/scan-findings/${findingId}/status`, { status: statusValue });
  return data;
}

export async function updateTaskExecutionStatus(taskExecutionId, payload) {
  const { data } = await api.post(`/task-executions/${taskExecutionId}/status`, payload);
  return data;
}

export async function getDatabaseExplorerSchema() {
  const { data } = await api.get("/database-explorer/schema");
  return data;
}

export async function runDatabaseExplorerQuery(payload) {
  const { data } = await api.post("/database-explorer/query", payload);
  return data;
}

export async function runSchedulerNow() {
  const { data } = await api.post("/scheduler/run");
  return data;
}

export async function runWorkerNow() {
  const { data } = await api.post("/worker/run");
  return data;
}

export async function exportOperationResults(operationId, fileFormat) {
  const { data } = await api.post(`/operations/${operationId}/results/export`, {
    file_format: fileFormat,
  });
  return data;
}

export async function importOperationResults(operationId, payloadJson) {
  const { data } = await api.post(`/operations/${operationId}/results/import`, {
    payload_json: payloadJson,
  });
  return data;
}

export async function previewHistoricalServicesVulnsImport(payload) {
  const formData = new FormData();
  formData.append("batch_code", payload.batch_code);
  formData.append("selected_target_ids_json", JSON.stringify(payload.selected_target_ids));
  if (payload.manual_target_mapping) {
    formData.append("manual_target_mapping_json", JSON.stringify(payload.manual_target_mapping));
  }
  formData.append("file", payload.file);
  const { data } = await api.post("/historical-scan-imports/services-vulns/preview", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function commitHistoricalServicesVulnsImport(payload) {
  const formData = new FormData();
  formData.append("batch_code", payload.batch_code);
  formData.append("year", String(payload.year));
  formData.append("quarter", String(payload.quarter));
  formData.append("week", String(payload.week));
  if (payload.scan_started_at) formData.append("scan_started_at", payload.scan_started_at);
  if (payload.scan_finished_at) formData.append("scan_finished_at", payload.scan_finished_at);
  if (payload.note) formData.append("note", payload.note);
  if (payload.source_root_path) formData.append("source_root_path", payload.source_root_path);
  formData.append("selected_target_ids_json", JSON.stringify(payload.selected_target_ids));
  formData.append("manual_target_mapping_json", JSON.stringify(payload.manual_target_mapping || {}));
  formData.append("file", payload.file);
  const { data } = await api.post("/historical-scan-imports/services-vulns/commit", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function getGroupPermissions(groupId) {
  const { data } = await api.get(`/account-groups/${groupId}/permissions`);
  return data;
}

export async function updateGroupPermissions(groupId, items) {
  const { data } = await api.put(`/account-groups/${groupId}/permissions`, { items });
  return data;
}

export default api;

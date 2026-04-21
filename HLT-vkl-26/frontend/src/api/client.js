import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1",
});

export async function getList(resource) {
  const { data } = await api.get(`/${resource}`);
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

export async function getOperationsRuntimeOverview() {
  const { data } = await api.get("/operations/runtime/overview");
  return data;
}

export async function launchOperation(operationId, payload) {
  const { data } = await api.post(`/operations/${operationId}/launch`, payload);
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

export async function updateTaskExecutionStatus(taskExecutionId, payload) {
  const { data } = await api.post(`/task-executions/${taskExecutionId}/status`, payload);
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

export default api;

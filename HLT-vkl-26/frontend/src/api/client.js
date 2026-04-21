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

export default api;

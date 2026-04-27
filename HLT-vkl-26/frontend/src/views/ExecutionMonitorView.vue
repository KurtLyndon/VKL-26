<template>
  <section class="page-header">
    <div>
      <p class="eyebrow">Runtime filter</p>
      <h2>Execution Monitor</h2>
      <p class="page-copy">Lọc execution theo operation, trigger type và trạng thái để theo dõi luồng chạy.</p>
    </div>
    <button class="ghost-button" @click="loadData">Refresh</button>
  </section>

  <section class="stat-grid compact-grid">
    <article class="mini-stat">
      <span>Tổng execution</span>
      <strong>{{ executions.length }}</strong>
    </article>
    <article class="mini-stat">
      <span>Queued</span>
      <strong>{{ statusCount("queued") }}</strong>
    </article>
    <article class="mini-stat">
      <span>Running</span>
      <strong>{{ statusCount("running") }}</strong>
    </article>
    <article class="mini-stat">
      <span>Completed</span>
      <strong>{{ statusCount("completed") }}</strong>
    </article>
    <article class="mini-stat">
      <span>Failed</span>
      <strong>{{ statusCount("failed") }}</strong>
    </article>
  </section>

  <section class="panel-grid">
    <article class="panel">
      <div class="panel-head">
        <h3>Bộ lọc</h3>
        <span class="badge">{{ sortedExecutions.length }} kết quả</span>
      </div>

      <div class="filter-grid">
        <label class="field-block">
          <span>operation_id</span>
          <select v-model="filters.operationId">
            <option value="">Tất cả</option>
            <option v-for="operation in operations" :key="operation.id" :value="String(operation.id)">
              {{ operation.code }}
            </option>
          </select>
        </label>

        <label class="field-block">
          <span>status</span>
          <select v-model="filters.status">
            <option value="">Tất cả</option>
            <option value="queued">queued</option>
            <option value="running">running</option>
            <option value="completed">completed</option>
            <option value="failed">failed</option>
          </select>
        </label>

        <label class="field-block">
          <span>trigger_type</span>
          <select v-model="filters.triggerType">
            <option value="">Tất cả</option>
            <option value="manual">manual</option>
            <option value="cron">cron</option>
            <option value="interval">interval</option>
          </select>
        </label>
      </div>
    </article>
  </section>

  <section class="panel-grid">
    <article class="panel">
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th class="sortable-header" @click="toggleSort('id')">ID{{ sortLabel('id') }}</th>
              <th class="sortable-header" @click="toggleSort('operation_id')">Operation{{ sortLabel('operation_id') }}</th>
              <th class="sortable-header" @click="toggleSort('execution_code')">Mã execution{{ sortLabel('execution_code') }}</th>
              <th class="sortable-header" @click="toggleSort('trigger_type')">Trigger{{ sortLabel('trigger_type') }}</th>
              <th class="sortable-header" @click="toggleSort('status')">Trạng thái{{ sortLabel('status') }}</th>
              <th class="sortable-header" @click="toggleSort('summary_json')">Tóm tắt{{ sortLabel('summary_json') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in sortedExecutions" :key="item.id">
              <td>{{ item.id }}</td>
              <td>{{ operationCode(item.operation_id) }}</td>
              <td>{{ item.execution_code }}</td>
              <td><StatusPill :value="item.trigger_type" /></td>
              <td><StatusPill :value="item.status" /></td>
              <td>{{ summaryText(item.summary_json) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </article>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { getList } from "../api/client";
import StatusPill from "../components/StatusPill.vue";
import { nextSortState, sortIndicator, sortRows } from "../utils/tableSort";

const executions = ref([]);
const operations = ref([]);
const sortState = ref({ key: "id", direction: "desc" });
const filters = reactive({
  operationId: "",
  status: "",
  triggerType: "",
});

const filteredExecutions = computed(() =>
  executions.value.filter((item) => {
    if (filters.operationId && item.operation_id !== Number(filters.operationId)) return false;
    if (filters.status && item.status !== filters.status) return false;
    if (filters.triggerType && item.trigger_type !== filters.triggerType) return false;
    return true;
  })
);

const sortedExecutions = computed(() => sortRows(filteredExecutions.value, sortState.value));

function operationCode(operationId) {
  return operations.value.find((item) => item.id === operationId)?.code || operationId;
}

function statusCount(status) {
  return executions.value.filter((item) => item.status === status).length;
}

function summaryText(summaryJson) {
  const summary = summaryJson || {};
  const parts = [];
  if (typeof summary.total_tasks === "number") parts.push(`${summary.total_tasks} task`);
  if (typeof summary.completed_tasks === "number") parts.push(`${summary.completed_tasks} hoàn tất`);
  if (typeof summary.failed_tasks === "number" && summary.failed_tasks > 0) parts.push(`${summary.failed_tasks} lỗi`);
  return parts.length ? parts.join(" | ") : "-";
}

function toggleSort(key) {
  sortState.value = nextSortState(sortState.value, key);
}

function sortLabel(key) {
  return sortIndicator(sortState.value, key);
}

async function loadData() {
  const [executionList, operationList] = await Promise.all([
    getList("operation-executions"),
    getList("operations"),
  ]);
  executions.value = executionList;
  operations.value = operationList;
}

onMounted(loadData);
</script>

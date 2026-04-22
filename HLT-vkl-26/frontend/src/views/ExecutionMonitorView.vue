<template>
  <section class="page-header">
    <div>
      <p class="eyebrow">Runtime filter</p>
      <h2>Execution Monitor</h2>
      <p class="page-copy">Lọc nhanh execution theo operation, trigger type và status để theo dõi luồng chạy.</p>
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
        <span class="badge">{{ filteredExecutions.length }} kết quả</span>
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
              <th>ID</th>
              <th>Operation</th>
              <th>Mã execution</th>
              <th>Trigger</th>
              <th>Trạng thái</th>
              <th>Tóm tắt</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in filteredExecutions" :key="item.id">
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

const executions = ref([]);
const operations = ref([]);
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

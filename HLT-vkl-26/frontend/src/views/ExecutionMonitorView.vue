<template>
  <section class="page-header">
    <div>
      <p class="eyebrow">Runtime filter</p>
      <h2>Execution Monitor</h2>
      <p class="page-copy">Loc nhanh execution theo operation, trigger type va status de theo doi luong chay.</p>
    </div>
    <button class="ghost-button" @click="loadData">Refresh</button>
  </section>

  <section class="panel-grid">
    <article class="panel">
      <div class="panel-head">
        <h3>Filters</h3>
        <span class="badge">{{ filteredExecutions.length }} matches</span>
      </div>

      <div class="filter-grid">
        <label class="field-block">
          <span>operation_id</span>
          <select v-model="filters.operationId">
            <option value="">All</option>
            <option v-for="operation in operations" :key="operation.id" :value="String(operation.id)">
              {{ operation.code }}
            </option>
          </select>
        </label>

        <label class="field-block">
          <span>status</span>
          <select v-model="filters.status">
            <option value="">All</option>
            <option value="queued">queued</option>
            <option value="running">running</option>
            <option value="completed">completed</option>
            <option value="failed">failed</option>
          </select>
        </label>

        <label class="field-block">
          <span>trigger_type</span>
          <select v-model="filters.triggerType">
            <option value="">All</option>
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
              <th>operation</th>
              <th>execution_code</th>
              <th>trigger_type</th>
              <th>status</th>
              <th>summary_json</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in filteredExecutions" :key="item.id">
              <td>{{ item.id }}</td>
              <td>{{ operationCode(item.operation_id) }}</td>
              <td>{{ item.execution_code }}</td>
              <td>{{ item.trigger_type }}</td>
              <td>{{ item.status }}</td>
              <td>{{ JSON.stringify(item.summary_json || {}) }}</td>
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

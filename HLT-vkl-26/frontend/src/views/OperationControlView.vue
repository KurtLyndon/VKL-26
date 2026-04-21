<template>
  <section class="page-header">
    <div>
      <p class="eyebrow">Execution runtime</p>
      <h2>Operation Control</h2>
      <p class="page-copy">
        Launch operation, xem execution gan nhat va cap nhat trang thai task execution trong luc dev scheduler.
      </p>
    </div>
    <button class="ghost-button" @click="loadRuntime">Refresh</button>
  </section>

  <section class="panel-grid">
    <article class="panel">
      <div class="panel-head">
        <h3>Scheduler Runner</h3>
        <span class="badge">cron + interval</span>
      </div>

      <p class="page-copy">
        Chay mot vong scheduler de tu dong launch cac operation den han. Background loop co the bat qua file env.
      </p>

      <div class="form-actions">
        <button class="primary-button" type="button" @click="runScheduler">Run Scheduler Now</button>
      </div>

      <p v-if="schedulerSummary" class="inline-note">{{ schedulerSummary }}</p>
    </article>

    <article class="panel">
      <div class="panel-head">
        <h3>Runtime Overview</h3>
        <span class="badge">{{ runtimeItems.length }} operations</span>
      </div>

      <div class="runtime-list">
        <button
          v-for="item in runtimeItems"
          :key="item.operation_id"
          class="runtime-card"
          :class="{ active: selectedOperationId === item.operation_id }"
          @click="selectOperation(item)"
        >
          <strong>{{ item.operation_name }}</strong>
          <span>{{ item.operation_code }}</span>
          <small>
            {{ item.total_executions }} executions | latest:
            {{ item.latest_execution_status || "no-run" }}
          </small>
        </button>
      </div>
    </article>

    <article class="panel">
      <div class="panel-head">
        <h3>Launch Operation</h3>
        <span class="badge">{{ selectedOperation?.operation_code || "pick one" }}</span>
      </div>

      <form class="resource-form" @submit.prevent="submitLaunch">
        <label class="field-block">
          <span>trigger_type</span>
          <select v-model="launchForm.trigger_type">
            <option value="manual">manual</option>
            <option value="cron">cron</option>
            <option value="interval">interval</option>
          </select>
        </label>

        <label class="field-block">
          <span>shared_input</span>
          <textarea v-model="launchForm.shared_input" rows="5" placeholder='{"target_id": 1}' />
        </label>

        <div class="form-actions">
          <button class="primary-button" type="submit" :disabled="!selectedOperationId">Launch</button>
        </div>
      </form>

      <p v-if="message" class="inline-note">{{ message }}</p>
    </article>
  </section>

  <section class="panel-grid">
    <article class="panel">
      <div class="panel-head">
        <h3>Recent Executions</h3>
        <span class="badge">{{ filteredExecutions.length }} records</span>
      </div>

      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>execution_code</th>
              <th>trigger_type</th>
              <th>status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="execution in filteredExecutions" :key="execution.id">
              <td>{{ execution.id }}</td>
              <td>{{ execution.execution_code }}</td>
              <td>{{ execution.trigger_type }}</td>
              <td>{{ execution.status }}</td>
              <td class="action-cell">
                <button class="table-button" @click="selectExecution(execution)">View Tasks</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </article>

    <article class="panel">
      <div class="panel-head">
        <h3>Execution Tasks</h3>
        <span class="badge">{{ selectedExecution ? `execution ${selectedExecution.id}` : "pick one" }}</span>
      </div>

      <div v-if="selectedExecution" class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>task_id</th>
              <th>agent_id</th>
              <th>status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="taskExecution in executionTasks" :key="taskExecution.id">
              <td>{{ taskExecution.id }}</td>
              <td>{{ taskExecution.task_id }}</td>
              <td>{{ taskExecution.agent_id }}</td>
              <td>{{ taskExecution.status }}</td>
              <td class="action-cell">
                <button class="table-button" @click="setStatus(taskExecution.id, 'running')">Running</button>
                <button class="table-button" @click="setStatus(taskExecution.id, 'completed')">Complete</button>
                <button class="table-button danger" @click="setStatus(taskExecution.id, 'failed')">Fail</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <p v-else class="inline-note">Chon mot execution de xem va cap nhat task runtime.</p>
    </article>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import {
  getExecutionTasks,
  getList,
  getOperationsRuntimeOverview,
  launchOperation,
  runSchedulerNow,
  updateTaskExecutionStatus,
} from "../api/client";

const runtimeItems = ref([]);
const executions = ref([]);
const executionTasks = ref([]);
const selectedOperationId = ref(null);
const selectedExecution = ref(null);
const message = ref("");
const schedulerSummary = ref("");

const launchForm = reactive({
  trigger_type: "manual",
  shared_input: "{}",
});

const selectedOperation = computed(() =>
  runtimeItems.value.find((item) => item.operation_id === selectedOperationId.value) || null
);

const filteredExecutions = computed(() =>
  executions.value
    .filter((item) => !selectedOperationId.value || item.operation_id === selectedOperationId.value)
    .sort((left, right) => right.id - left.id)
);

function parseSharedInput() {
  try {
    return JSON.parse(launchForm.shared_input || "{}");
  } catch {
    throw new Error("shared_input must be valid JSON.");
  }
}

async function loadRuntime() {
  const [overview, executionList] = await Promise.all([
    getOperationsRuntimeOverview(),
    getList("operation-executions"),
  ]);
  runtimeItems.value = overview;
  executions.value = executionList;

  if (!selectedOperationId.value && overview.length > 0) {
    selectedOperationId.value = overview[0].operation_id;
  }
}

function selectOperation(item) {
  selectedOperationId.value = item.operation_id;
  selectedExecution.value = null;
  executionTasks.value = [];
}

async function selectExecution(execution) {
  selectedExecution.value = execution;
  executionTasks.value = await getExecutionTasks(execution.id);
}

async function submitLaunch() {
  if (!selectedOperationId.value) return;
  try {
    const response = await launchOperation(selectedOperationId.value, {
      trigger_type: launchForm.trigger_type,
      shared_input: parseSharedInput(),
    });
    message.value = `Launched execution ${response.execution.execution_code} with ${response.task_executions.length} task(s).`;
    await loadRuntime();
    await selectExecution(response.execution);
  } catch (error) {
    message.value = error?.message || "Unable to launch operation.";
  }
}

async function runScheduler() {
  try {
    const result = await runSchedulerNow();
    schedulerSummary.value = `Scheduler checked ${result.checked_operations} operation(s) and launched ${result.launched_operations} execution(s).`;
    await loadRuntime();
  } catch (error) {
    schedulerSummary.value = error?.message || "Unable to run scheduler.";
  }
}

async function setStatus(taskExecutionId, status) {
  try {
    await updateTaskExecutionStatus(taskExecutionId, {
      status,
      raw_log: `Status updated to ${status} from UI control panel.`,
    });
    if (selectedExecution.value) {
      await selectExecution(selectedExecution.value);
    }
    await loadRuntime();
  } catch (error) {
    message.value = error?.message || "Unable to update task execution status.";
  }
}

onMounted(loadRuntime);
</script>

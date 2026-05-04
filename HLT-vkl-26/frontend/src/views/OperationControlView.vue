<template>
  <section class="page-header">
    <div>
      <p class="eyebrow">Execution runtime</p>
      <h2>Operation Control</h2>
      <p class="page-copy">Launch operation, chạy scheduler hoặc worker, và theo dõi task execution trong lúc dev.</p>
    </div>
    <button class="ghost-button" @click="loadRuntime">Refresh</button>
  </section>

  <section class="panel-grid">
    <article class="panel">
      <div class="panel-head">
        <h3>Scheduler Runner</h3>
        <span class="badge">cron + interval</span>
      </div>
      <p class="page-copy">Chạy một vòng scheduler để tự động launch các operation đến hạn.</p>
      <div class="form-actions">
        <button class="primary-button" type="button" @click="runScheduler">Run Scheduler Now</button>
      </div>
      <p v-if="schedulerSummary" class="inline-note">{{ schedulerSummary }}</p>
    </article>

    <article class="panel">
      <div class="panel-head">
        <h3>Worker Runner</h3>
        <span class="badge">sequential mock-run</span>
      </div>
      <p class="page-copy">Xử lý task execution đang queued theo đúng thứ tự và tự cập nhật execution summary.</p>
      <div class="form-actions">
        <button class="primary-button" type="button" @click="runWorker">Run Worker Now</button>
      </div>
      <p v-if="workerSummary" class="inline-note">{{ workerSummary }}</p>
    </article>

    <article class="panel">
      <div class="panel-head">
        <h3>Mock Demo Flow</h3>
        <span class="badge">launch + worker</span>
      </div>
      <p class="page-copy">Chạy nhanh toàn bộ luồng mock: tạo execution, xử lý worker và sinh finding để demo.</p>
      <div class="form-actions">
        <button class="primary-button" type="button" :disabled="!selectedOperationId" @click="runMockFlow">
          Run Mock Demo
        </button>
      </div>
      <p v-if="mockSummary" class="inline-note">{{ mockSummary }}</p>
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
          <small>{{ item.total_executions }} executions | latest: {{ item.latest_execution_status || "no-run" }}</small>
        </button>
      </div>
    </article>

    <article class="panel panel-span-full">
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

        <div class="filter-grid">
          <label class="field-block">
            <span>Năm</span>
            <input v-model.number="launchForm.year" type="number" min="2000" max="2100" />
          </label>

          <label class="field-block">
            <span>Quý</span>
            <select v-model.number="launchForm.quarter">
              <option :value="null">-</option>
              <option :value="1">1</option>
              <option :value="2">2</option>
              <option :value="3">3</option>
              <option :value="4">4</option>
            </select>
          </label>

          <label class="field-block">
            <span>Tuần</span>
            <input v-model.number="launchForm.week" type="number" min="1" max="53" />
          </label>
        </div>

        <div class="selection-toolbar">
          <MultiSelectDialog
            v-model="selectedTargetIds"
            title="Chọn mục tiêu cho execution"
            :options="targetPickerOptions"
            button-label="Chọn target"
            search-placeholder="Tìm theo tên target hoặc ID..."
          />

          <div class="selected-chip-list">
            <span v-for="item in selectedTargetChips" :key="item.id" class="selected-chip">
              {{ item.name }}
            </span>
          </div>
        </div>

        <label class="field-block">
          <span>source_root_path</span>
          <input v-model="launchForm.source_root_path" placeholder="Đường dẫn nguồn nếu có" />
        </label>

        <label class="field-block">
          <span>note</span>
          <textarea v-model="launchForm.note" rows="3" placeholder="Ghi chú execution" />
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
        <span class="badge">{{ totalExecutionItems }} bản ghi</span>
      </div>

      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th class="sortable-header" @click="toggleExecutionSort('id')">ID{{ executionSortLabel("id") }}</th>
              <th class="sortable-header" @click="toggleExecutionSort('execution_code')">
                execution_code{{ executionSortLabel("execution_code") }}
              </th>
              <th class="sortable-header" @click="toggleExecutionSort('trigger_type')">
                trigger_type{{ executionSortLabel("trigger_type") }}
              </th>
              <th class="sortable-header" @click="toggleExecutionSort('status')">
                status{{ executionSortLabel("status") }}
              </th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="execution in paginatedExecutions" :key="execution.id">
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

      <PaginationBar
        :current-page="executionCurrentPage"
        :page-size="executionPageSize"
        :total-items="totalExecutionItems"
        :total-pages="executionTotalPages"
        @update:page-size="executionPageSize = $event"
        @previous="goToPreviousExecutionPage"
        @next="goToNextExecutionPage"
      />
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
              <th class="sortable-header" @click="toggleTaskSort('id')">ID{{ taskSortLabel("id") }}</th>
              <th class="sortable-header" @click="toggleTaskSort('task_id')">task_id{{ taskSortLabel("task_id") }}</th>
              <th class="sortable-header" @click="toggleTaskSort('agent_id')">
                agent_id{{ taskSortLabel("agent_id") }}
              </th>
              <th class="sortable-header" @click="toggleTaskSort('status')">status{{ taskSortLabel("status") }}</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="taskExecution in paginatedExecutionTasks" :key="taskExecution.id">
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

      <PaginationBar
        v-if="selectedExecution"
        :current-page="taskCurrentPage"
        :page-size="taskPageSize"
        :total-items="totalTaskItems"
        :total-pages="taskTotalPages"
        @update:page-size="taskPageSize = $event"
        @previous="goToPreviousTaskPage"
        @next="goToNextTaskPage"
      />

      <p v-else class="inline-note">Chọn một execution để xem và cập nhật task runtime.</p>
    </article>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import {
  getExecutionTasks,
  getList,
  getOperationsRuntimeOverview,
  getTargetsEnriched,
  launchOperation,
  runMockDemoFlow,
  runSchedulerNow,
  runWorkerNow,
  updateTaskExecutionStatus,
} from "../api/client";
import MultiSelectDialog from "../components/MultiSelectDialog.vue";
import PaginationBar from "../components/PaginationBar.vue";
import { usePagination } from "../composables/usePagination";
import { nextSortState, sortIndicator, sortRows } from "../utils/tableSort";

const runtimeItems = ref([]);
const executions = ref([]);
const executionTasks = ref([]);
const targets = ref([]);
const selectedOperationId = ref(null);
const selectedExecution = ref(null);
const selectedTargetIds = ref([]);
const message = ref("");
const schedulerSummary = ref("");
const workerSummary = ref("");
const mockSummary = ref("");
const executionSortState = ref({ key: "id", direction: "desc" });
const taskSortState = ref({ key: "id", direction: "desc" });

const launchForm = reactive({
  trigger_type: "manual",
  year: new Date().getFullYear(),
  quarter: null,
  week: null,
  note: "",
  source_root_path: "",
  shared_input: "{}",
});

const selectedOperation = computed(
  () => runtimeItems.value.find((item) => item.operation_id === selectedOperationId.value) || null
);

const filteredExecutions = computed(() =>
  executions.value.filter((item) => !selectedOperationId.value || item.operation_id === selectedOperationId.value)
);

const sortedExecutions = computed(() => sortRows(filteredExecutions.value, executionSortState.value));
const sortedExecutionTasks = computed(() => sortRows(executionTasks.value, taskSortState.value));
const targetPickerOptions = computed(() =>
  [...targets.value]
    .sort((left, right) => left.id - right.id)
    .map((target) => ({
      value: target.id,
      label: target.name,
      description: `ID ${target.id}${target.ip_range ? ` • ${target.ip_range}` : ""}`,
    }))
);
const selectedTargetChips = computed(() => {
  const targetMap = new Map(targets.value.map((item) => [item.id, item]));
  return selectedTargetIds.value.map((id) => targetMap.get(id)).filter(Boolean);
});

const {
  currentPage: executionCurrentPage,
  pageSize: executionPageSize,
  paginatedItems: paginatedExecutions,
  totalItems: totalExecutionItems,
  totalPages: executionTotalPages,
  goToPreviousPage: goToPreviousExecutionPage,
  goToNextPage: goToNextExecutionPage,
} = usePagination(sortedExecutions);

const {
  currentPage: taskCurrentPage,
  pageSize: taskPageSize,
  paginatedItems: paginatedExecutionTasks,
  totalItems: totalTaskItems,
  totalPages: taskTotalPages,
  goToPreviousPage: goToPreviousTaskPage,
  goToNextPage: goToNextTaskPage,
} = usePagination(sortedExecutionTasks);

function executionSortLabel(key) {
  return sortIndicator(executionSortState.value, key);
}

function taskSortLabel(key) {
  return sortIndicator(taskSortState.value, key);
}

function toggleExecutionSort(key) {
  executionSortState.value = nextSortState(executionSortState.value, key);
}

function toggleTaskSort(key) {
  taskSortState.value = nextSortState(taskSortState.value, key);
}

function parseSharedInput() {
  try {
    return JSON.parse(launchForm.shared_input || "{}");
  } catch {
    throw new Error("shared_input phải là JSON hợp lệ.");
  }
}

async function loadRuntime() {
  const [overview, executionList, targetList] = await Promise.all([
    getOperationsRuntimeOverview(),
    getList("operation-executions"),
    getTargetsEnriched(),
  ]);
  runtimeItems.value = overview;
  executions.value = executionList;
  targets.value = targetList;

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
      target_ids: selectedTargetIds.value,
      year: launchForm.year || null,
      quarter: launchForm.quarter || null,
      week: launchForm.week || null,
      note: launchForm.note || null,
      source_root_path: launchForm.source_root_path || null,
      shared_input: parseSharedInput(),
    });
    message.value = `Đã launch execution ${response.execution.execution_code} với ${response.task_executions.length} task.`;
    await loadRuntime();
    await selectExecution(response.execution);
  } catch (error) {
    message.value = error?.message || "Không thể launch operation.";
  }
}

async function runScheduler() {
  try {
    const result = await runSchedulerNow();
    schedulerSummary.value = `Scheduler đã kiểm tra ${result.checked_operations} operation và launch ${result.launched_operations} execution.`;
    await loadRuntime();
  } catch (error) {
    schedulerSummary.value = error?.message || "Không thể chạy scheduler.";
  }
}

async function runWorker() {
  try {
    const result = await runWorkerNow();
    workerSummary.value = `Worker đã kiểm tra ${result.checked_executions} execution, xử lý ${result.processed_tasks} task, hoàn tất ${result.completed_tasks}, thất bại ${result.failed_tasks}.`;
    await loadRuntime();
    if (selectedExecution.value) {
      await selectExecution(selectedExecution.value);
    }
  } catch (error) {
    workerSummary.value = error?.message || "Không thể chạy worker.";
  }
}

async function runMockFlow() {
  try {
    const result = await runMockDemoFlow({
      operation_id: selectedOperationId.value,
      target_id: selectedTargetIds.value[0] || null,
    });
    mockSummary.value = `Mock flow đã tạo execution #${result.operation_execution_id}, sinh ${result.findings_created} finding và trạng thái cuối là ${result.execution_status}.`;
    await loadRuntime();
    const execution = executions.value.find((item) => item.id === result.operation_execution_id);
    if (execution) {
      await selectExecution(execution);
    }
  } catch (error) {
    mockSummary.value = error?.response?.data?.detail || error?.message || "Không thể chạy mock flow.";
  }
}

async function setStatus(taskExecutionId, status) {
  try {
    await updateTaskExecutionStatus(taskExecutionId, {
      status,
      raw_log: `Status được cập nhật thành ${status} từ UI control panel.`,
    });
    if (selectedExecution.value) {
      await selectExecution(selectedExecution.value);
    }
    await loadRuntime();
  } catch (error) {
    message.value = error?.message || "Không thể cập nhật trạng thái task execution.";
  }
}

onMounted(loadRuntime);
</script>

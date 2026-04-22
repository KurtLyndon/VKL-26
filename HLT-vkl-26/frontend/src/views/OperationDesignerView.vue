<template>
  <section class="page-header">
    <div>
      <p class="eyebrow">Workflow builder</p>
      <h2>Operation Task Designer</h2>
      <p class="page-copy">
        Sắp xếp task trong operation, thêm task mới, chỉnh `continue_on_error` và `input_override_json`.
      </p>
    </div>
    <button class="ghost-button" @click="loadData">Refresh</button>
  </section>

  <section class="panel-grid">
    <article class="panel">
      <div class="panel-head">
        <h3>Operations</h3>
        <span class="badge">{{ operations.length }} records</span>
      </div>

      <div class="runtime-list">
        <button
          v-for="operation in operations"
          :key="operation.id"
          class="runtime-card"
          :class="{ active: selectedOperationId === operation.id }"
          @click="selectOperation(operation.id)"
        >
          <strong>{{ operation.name }}</strong>
          <span>{{ operation.code }}</span>
          <small>{{ operation.schedule_type }} | {{ operation.is_active ? "active" : "inactive" }}</small>
        </button>
      </div>
    </article>

    <article class="panel">
      <div class="panel-head">
        <h3>Add Task To Operation</h3>
        <span class="badge">{{ selectedOperation?.code || "pick one" }}</span>
      </div>

      <form class="resource-form" @submit.prevent="submitOperationTask">
        <label class="field-block">
          <span>task_id</span>
          <select v-model="operationTaskForm.task_id">
            <option value="">Chọn task</option>
            <option v-for="task in tasks" :key="task.id" :value="String(task.id)">
              {{ task.code }} - {{ task.name }}
            </option>
          </select>
        </label>

        <label class="field-block">
          <span>continue_on_error</span>
          <select v-model="operationTaskForm.continue_on_error">
            <option value="false">false</option>
            <option value="true">true</option>
          </select>
        </label>

        <label class="field-block">
          <span>input_override_json</span>
          <textarea v-model="operationTaskForm.input_override_json" rows="5" placeholder="{}" />
        </label>

        <div class="form-actions">
          <button class="primary-button" type="submit" :disabled="!selectedOperationId">Add Task</button>
        </div>
      </form>

      <p v-if="message" class="inline-note">{{ message }}</p>
    </article>
  </section>

  <section class="panel-grid">
    <article class="panel">
      <div class="panel-head">
        <h3>Ordered Tasks</h3>
        <span class="badge">{{ operationTasks.length }} task(s)</span>
      </div>

      <div class="task-stack" v-if="selectedOperationId">
        <article v-for="(item, index) in operationTasks" :key="item.id" class="task-card">
          <div class="task-card-head">
            <div>
              <strong>#{{ item.order_index }} - {{ taskName(item.task_id) }}</strong>
              <p class="inline-note">task_id: {{ item.task_id }} | continue_on_error: {{ item.continue_on_error }}</p>
            </div>
            <div class="action-cell">
              <button class="table-button" :disabled="index === 0" @click="moveTask(item, -1)">Up</button>
              <button class="table-button" :disabled="index === operationTasks.length - 1" @click="moveTask(item, 1)">Down</button>
              <button class="table-button danger" @click="removeOperationTask(item.id)">Delete</button>
            </div>
          </div>

          <label class="field-block">
            <span>input_override_json</span>
            <textarea v-model="item.overrideText" rows="4" />
          </label>

          <div class="form-actions">
            <button class="ghost-button" type="button" @click="saveOperationTask(item)">Save Override</button>
          </div>
        </article>
      </div>

      <p v-else class="inline-note">Chọn một operation để quản lý thứ tự task.</p>
    </article>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { createItem, deleteItem, getList, getOperationTasks, updateItem } from "../api/client";

const operations = ref([]);
const tasks = ref([]);
const operationTasks = ref([]);
const selectedOperationId = ref(null);
const message = ref("");

const operationTaskForm = reactive({
  task_id: "",
  continue_on_error: "false",
  input_override_json: "{}",
});

const selectedOperation = computed(() =>
  operations.value.find((item) => item.id === selectedOperationId.value) || null
);

function parseJsonSafe(text) {
  return JSON.parse(text || "{}");
}

function taskName(taskId) {
  const task = tasks.value.find((item) => item.id === taskId);
  return task ? `${task.code} - ${task.name}` : `Task ${taskId}`;
}

async function loadData() {
  const [operationList, taskList] = await Promise.all([getList("operations"), getList("tasks")]);
  operations.value = operationList;
  tasks.value = taskList;
  if (!selectedOperationId.value && operationList.length > 0) {
    await selectOperation(operationList[0].id);
  } else if (selectedOperationId.value) {
    await loadOperationTasks();
  }
}

async function loadOperationTasks() {
  if (!selectedOperationId.value) return;
  const items = await getOperationTasks(selectedOperationId.value);
  operationTasks.value = items.map((item) => ({
    ...item,
    overrideText: JSON.stringify(item.input_override_json || {}, null, 2),
  }));
}

async function selectOperation(operationId) {
  selectedOperationId.value = operationId;
  await loadOperationTasks();
}

async function submitOperationTask() {
  await createItem("operation-tasks", {
    operation_id: selectedOperationId.value,
    task_id: Number(operationTaskForm.task_id),
    order_index: operationTasks.value.length + 1,
    continue_on_error: operationTaskForm.continue_on_error === "true",
    input_override_json: parseJsonSafe(operationTaskForm.input_override_json),
  });
  message.value = "Đã thêm task vào operation.";
  operationTaskForm.task_id = "";
  operationTaskForm.continue_on_error = "false";
  operationTaskForm.input_override_json = "{}";
  await loadOperationTasks();
}

async function moveTask(item, direction) {
  const currentIndex = operationTasks.value.findIndex((entry) => entry.id === item.id);
  const targetIndex = currentIndex + direction;
  if (targetIndex < 0 || targetIndex >= operationTasks.value.length) return;

  const current = operationTasks.value[currentIndex];
  const target = operationTasks.value[targetIndex];

  await Promise.all([
    updateItem("operation-tasks", current.id, { order_index: target.order_index }),
    updateItem("operation-tasks", target.id, { order_index: current.order_index }),
  ]);
  await loadOperationTasks();
}

async function saveOperationTask(item) {
  await updateItem("operation-tasks", item.id, {
    input_override_json: parseJsonSafe(item.overrideText),
    continue_on_error: item.continue_on_error,
    order_index: item.order_index,
  });
  message.value = `Đã lưu task order #${item.order_index}.`;
  await loadOperationTasks();
}

async function removeOperationTask(id) {
  await deleteItem("operation-tasks", id);
  const reordered = operationTasks.value.filter((item) => item.id !== id);
  await Promise.all(
    reordered.map((item, index) =>
      updateItem("operation-tasks", item.id, {
        order_index: index + 1,
        continue_on_error: item.continue_on_error,
        input_override_json: parseJsonSafe(item.overrideText),
      })
    )
  );
  await loadOperationTasks();
}

onMounted(loadData);
</script>

<template>
  <section class="page-header">
    <div>
      <p class="eyebrow">Task manager</p>
      <h2>Quản lý Task</h2>
      <p class="page-copy">Task gắn với loại agent thực thi. Một task có thể được nhiều agent cùng loại thực thi ở các máy khác nhau.</p>
    </div>
    <button class="ghost-button" @click="loadAll">Refresh</button>
  </section>

  <section class="panel-grid">
    <article class="panel panel-table">
      <div class="panel-head">
        <h3>Danh sách Task</h3>
        <span class="badge">{{ totalItems }} bản ghi</span>
      </div>

      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th class="sortable-header" @click="toggleSort('id')">ID{{ sortLabel("id") }}</th>
              <th class="sortable-header" @click="toggleSort('code')">code{{ sortLabel("code") }}</th>
              <th class="sortable-header" @click="toggleSort('name')">name{{ sortLabel("name") }}</th>
              <th class="sortable-header" @click="toggleSort('agent_type')">agent_type{{ sortLabel("agent_type") }}</th>
              <th class="sortable-header" @click="toggleSort('script_name')">script_name{{ sortLabel("script_name") }}</th>
              <th class="sortable-header" @click="toggleSort('script_path')">script_path{{ sortLabel("script_path") }}</th>
              <th class="sortable-header" @click="toggleSort('version')">version{{ sortLabel("version") }}</th>
              <th class="sortable-header" @click="toggleSort('max_concurrency_per_agent')">max_concurrency{{ sortLabel("max_concurrency_per_agent") }}</th>
              <th class="sortable-header" @click="toggleSort('is_active')">is_active{{ sortLabel("is_active") }}</th>
              <th>Tác vụ</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in paginatedItems"
              :key="item.id"
              class="row-selectable"
              :class="{ 'row-selected': form.id === item.id }"
              @click="editItem(item)"
            >
              <td>{{ item.id }}</td>
              <td>{{ item.code }}</td>
              <td>{{ item.name }}</td>
              <td>{{ item.agent_type || "-" }}</td>
              <td>{{ item.script_name || "-" }}</td>
              <td>{{ item.script_path || "-" }}</td>
              <td>{{ item.version || "-" }}</td>
              <td>{{ item.max_concurrency_per_agent ?? 0 }}</td>
              <td>{{ item.is_active ? "true" : "false" }}</td>
              <td class="action-cell">
                <button class="table-button danger" @click.stop="removeItem(item.id)">Delete</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <PaginationBar
        :current-page="currentPage"
        :page-size="pageSize"
        :total-items="totalItems"
        :total-pages="totalPages"
        @update:page-size="pageSize = $event"
        @previous="goToPreviousPage"
        @next="goToNextPage"
      />
    </article>

    <article class="panel panel-form">
      <div class="panel-head">
        <h3>{{ form.id ? "Cập nhật Task" : "Tạo mới Task" }}</h3>
      </div>

      <form class="resource-form" @submit.prevent="submitForm">
        <label class="field-block">
          <span>code</span>
          <input v-model="form.code" type="text" />
        </label>

        <label class="field-block">
          <span>name</span>
          <input v-model="form.name" type="text" />
        </label>

        <label class="field-block">
          <span>agent_type</span>
          <select v-model="form.agent_type">
            <option value="">Chọn agent type</option>
            <option v-for="option in agentTypeOptions" :key="option.agent_type" :value="option.agent_type">
              {{ option.agent_type }} ({{ option.agent_count }} agent)
            </option>
          </select>
          <small class="field-help">Danh sách này lấy từ các agent type hiện có trong hệ thống.</small>
        </label>

        <label class="field-block">
          <span>script_name</span>
          <input v-model="form.script_name" type="text" />
        </label>

        <label class="field-block">
          <span>script_path</span>
          <input v-model="form.script_path" type="text" />
        </label>

        <label class="field-block">
          <span>version</span>
          <input v-model="form.version" type="text" />
        </label>

        <label class="field-block">
          <span>max_concurrency_per_agent</span>
          <input v-model="form.max_concurrency_per_agent" type="number" min="0" />
          <small class="field-help">`0` nghĩa là không giới hạn theo agent.</small>
        </label>

        <label class="field-block">
          <span>is_active</span>
          <select v-model="form.is_active">
            <option value="true">true</option>
            <option value="false">false</option>
          </select>
        </label>

        <label class="field-block">
          <span>description</span>
          <textarea v-model="form.description" rows="4" />
        </label>

        <label class="field-block">
          <span>input_schema_json</span>
          <textarea v-model="form.input_schema_json" rows="4" placeholder="{}" />
        </label>

        <label class="field-block">
          <span>output_schema_json</span>
          <textarea v-model="form.output_schema_json" rows="4" placeholder="{}" />
        </label>

        <label class="field-block">
          <span>script_content</span>
          <textarea v-model="form.script_content" rows="6" />
        </label>

        <div class="form-actions">
          <button class="primary-button" type="submit">{{ form.id ? "Lưu thay đổi" : "Tạo mới" }}</button>
          <button v-if="form.id" class="ghost-button" type="button" @click="resetForm">Bỏ chọn</button>
        </div>
      </form>
    </article>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { createItem, deleteItem, getList, getTaskAgentTypeOptions, updateItem } from "../api/client";
import PaginationBar from "../components/PaginationBar.vue";
import { usePagination } from "../composables/usePagination";
import { nextSortState, sortIndicator, sortRows } from "../utils/tableSort";

const items = ref([]);
const agentTypeOptions = ref([]);
const sortState = ref({ key: "id", direction: "desc" });
const form = reactive({});

const sortedItems = computed(() => sortRows(items.value, sortState.value));
const { currentPage, pageSize, paginatedItems, totalItems, totalPages, goToPreviousPage, goToNextPage } =
  usePagination(sortedItems);

function resetForm() {
  Object.keys(form).forEach((key) => delete form[key]);
  form.id = null;
  form.code = "";
  form.name = "";
  form.agent_type = "";
  form.script_name = "";
  form.script_path = "";
  form.script_content = "";
  form.input_schema_json = "{}";
  form.output_schema_json = "{}";
  form.description = "";
  form.version = "";
  form.max_concurrency_per_agent = "0";
  form.is_active = "true";
}

function displayJson(value) {
  return JSON.stringify(value || {}, null, 2);
}

function editItem(item) {
  resetForm();
  form.id = item.id;
  form.code = item.code ?? "";
  form.name = item.name ?? "";
  form.agent_type = item.agent_type ?? "";
  form.script_name = item.script_name ?? "";
  form.script_path = item.script_path ?? "";
  form.script_content = item.script_content ?? "";
  form.input_schema_json = displayJson(item.input_schema_json);
  form.output_schema_json = displayJson(item.output_schema_json);
  form.description = item.description ?? "";
  form.version = item.version ?? "";
  form.max_concurrency_per_agent = String(item.max_concurrency_per_agent ?? 0);
  form.is_active = item.is_active ? "true" : "false";
}

function toggleSort(key) {
  sortState.value = nextSortState(sortState.value, key);
}

function sortLabel(key) {
  return sortIndicator(sortState.value, key);
}

function buildPayload() {
  return {
    code: form.code,
    name: form.name,
    agent_type: form.agent_type,
    script_name: form.script_name || null,
    script_path: form.script_path || null,
    script_content: form.script_content || null,
    input_schema_json: JSON.parse(form.input_schema_json || "{}"),
    output_schema_json: JSON.parse(form.output_schema_json || "{}"),
    description: form.description || null,
    version: form.version || null,
    max_concurrency_per_agent: Number(form.max_concurrency_per_agent || 0),
    is_active: form.is_active === "true",
  };
}

async function loadAll() {
  const [taskRows, typeRows] = await Promise.all([getList("tasks"), getTaskAgentTypeOptions()]);
  items.value = taskRows;
  agentTypeOptions.value = typeRows;
}

async function submitForm() {
  const payload = buildPayload();
  if (form.id) {
    await updateItem("tasks", form.id, payload);
  } else {
    await createItem("tasks", payload);
  }
  resetForm();
  await loadAll();
}

async function removeItem(id) {
  await deleteItem("tasks", id);
  if (form.id === id) resetForm();
  await loadAll();
}

onMounted(async () => {
  resetForm();
  await loadAll();
});
</script>

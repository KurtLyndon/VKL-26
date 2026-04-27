<template>
  <section class="page-header">
    <div>
      <p class="eyebrow">Mục tiêu</p>
      <h2>Quản lý Target</h2>
      <p class="page-copy">Quản lý mục tiêu, dải IP, thuộc tính động và import danh sách từ Excel hoặc CSV.</p>
    </div>
    <button class="ghost-button" @click="loadData">Làm mới</button>
  </section>

  <section class="panel-grid">
    <article class="panel">
      <div class="panel-head">
        <h3>{{ form.id ? "Cập nhật target" : "Thêm target" }}</h3>
        <span class="badge">{{ sortedTargets.length }} target</span>
      </div>

      <form class="resource-form" @submit.prevent="submitTarget">
        <label class="field-block">
          <span>Tên</span>
          <input v-model="form.name" required />
        </label>

        <label class="field-block">
          <span>Dải IP</span>
          <input
            v-model="form.ip_range"
            placeholder="192.168.[1-3].0/24, 10.0.0.10, 10.0.0.20-10.0.0.30"
          />
        </label>

        <label class="field-block">
          <span>Loại target</span>
          <select v-model="form.target_type">
            <option value="network">network</option>
            <option value="host">host</option>
            <option value="domain">domain</option>
            <option value="application">application</option>
          </select>
        </label>

        <label class="field-block">
          <span>Domain</span>
          <input v-model="form.domain" />
        </label>

        <label class="field-block">
          <span>Mô tả</span>
          <textarea v-model="form.description" rows="4" />
        </label>

        <div class="form-actions">
          <button class="primary-button" type="submit">{{ form.id ? "Lưu target" : "Tạo target" }}</button>
          <button v-if="form.id" class="ghost-button" type="button" @click="resetForm">Bỏ chọn</button>
        </div>
      </form>

      <p v-if="message" class="inline-note">{{ message }}</p>
    </article>

    <article class="panel">
      <div class="panel-head">
        <h3>Import danh sách</h3>
        <span class="badge">Excel / CSV</span>
      </div>

      <div class="resource-form">
        <label class="field-block">
          <span>Chọn file</span>
          <input type="file" accept=".xlsx,.xlsm,.csv" @change="handleFileChange" />
        </label>

        <div class="form-actions">
          <button class="primary-button" type="button" :disabled="!importFile" @click="submitImport">
            Import target
          </button>
        </div>
      </div>

      <p class="inline-note">
        Cột chuẩn: `Tên`, `Dải IP`, `Mô tả`, `Domain`, `Loại target`. Cột mới sẽ tự tạo thành thuộc tính động.
      </p>
      <p class="inline-note">
        Có thể nhập nhiều dải/IP cách nhau bằng dấu phẩy. Hệ thống sẽ tự chuẩn hóa các dạng như
        `192.168.[1 - 3].0/24` hoặc `192.168.[1_3].0/24` về `192.168.[1-3].0/24`.
      </p>
      <p v-if="importMessage" class="inline-note">{{ importMessage }}</p>
    </article>
  </section>

  <section class="panel-grid">
    <article class="panel">
      <div class="panel-head">
        <h3>Danh sách target</h3>
        <span class="badge">{{ sortedTargets.length }} bản ghi</span>
      </div>

      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th class="sortable-header" @click="toggleSort('id')">ID{{ sortLabel('id') }}</th>
              <th class="sortable-header" @click="toggleSort('name')">Tên{{ sortLabel('name') }}</th>
              <th class="sortable-header" @click="toggleSort('ip_range')">Dải IP{{ sortLabel('ip_range') }}</th>
              <th class="sortable-header" @click="toggleSort('ip_entry_type')">Kiểu IP{{ sortLabel('ip_entry_type') }}</th>
              <th class="sortable-header" @click="toggleSort('groups')">Nhóm{{ sortLabel('groups') }}</th>
              <th>Tác vụ</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="target in sortedTargets" :key="target.id">
              <td>{{ target.id }}</td>
              <td>{{ target.name }}</td>
              <td>{{ target.ip_range || "-" }}</td>
              <td>{{ target.ip_entry_type }}</td>
              <td>{{ target.groups.map((group) => group.name).join(", ") || "-" }}</td>
              <td class="action-cell">
                <button class="table-button" @click="selectTarget(target)">Chọn</button>
                <button class="table-button danger" @click="removeTarget(target.id)">Xóa</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </article>

    <article class="panel">
      <div class="panel-head">
        <h3>Thuộc tính và nhóm</h3>
        <span class="badge">{{ selectedTarget ? selectedTarget.name : "chưa chọn" }}</span>
      </div>

      <div v-if="selectedTarget" class="resource-form">
        <p class="inline-note">
          Dải IP đã chuẩn hóa: {{ selectedTarget.ip_range || "-" }}
        </p>
        <p class="inline-note">
          Phân giải để khớp scan: {{ selectedTarget.resolved_ip_entries.join(", ") || "-" }}
        </p>

        <label v-for="definition in attributeDefinitions" :key="definition.id" class="field-block">
          <span>{{ definition.attribute_name }}</span>
          <textarea v-if="definition.data_type === 'textarea'" v-model="attributeDrafts[definition.id]" rows="3" />
          <input v-else v-model="attributeDrafts[definition.id]" />
        </label>

        <div class="form-actions">
          <button class="primary-button" type="button" @click="saveAttributes">Lưu thuộc tính</button>
        </div>

        <div class="group-check-grid">
          <label v-for="group in targetGroups" :key="group.id" class="switch-line">
            <input v-model="selectedGroupIds" :value="group.id" type="checkbox" />
            <span>{{ group.name }}</span>
          </label>
        </div>

        <div class="form-actions">
          <button class="ghost-button" type="button" @click="saveGroups">Lưu nhóm target</button>
        </div>
      </div>

      <p v-else class="inline-note">Chọn một target để chỉnh sửa thuộc tính và nhóm.</p>
    </article>
  </section>
</template>

<script setup>
import { computed, reactive, ref } from "vue";
import {
  createManagedTarget,
  deleteManagedTarget,
  getList,
  getTargetsEnriched,
  importTargetsFile,
  updateManagedTarget,
  updateTargetAttributeValues,
  updateTargetGroups,
} from "../api/client";
import { nextSortState, sortIndicator, sortRows } from "../utils/tableSort";

const targets = ref([]);
const attributeDefinitions = ref([]);
const targetGroups = ref([]);
const selectedTarget = ref(null);
const selectedGroupIds = ref([]);
const attributeDrafts = reactive({});
const importFile = ref(null);
const message = ref("");
const importMessage = ref("");
const sortState = ref({ key: "id", direction: "desc" });

const form = reactive({
  id: null,
  name: "",
  ip_range: "",
  target_type: "network",
  domain: "",
  description: "",
});

const sortedTargets = computed(() =>
  sortRows(targets.value, sortState.value, (row, key) => {
    if (key === "groups") {
      return row.groups.map((group) => group.name).join(", ");
    }
    return row?.[key];
  })
);

function resetForm() {
  form.id = null;
  form.name = "";
  form.ip_range = "";
  form.target_type = "network";
  form.domain = "";
  form.description = "";
  selectedTarget.value = null;
  selectedGroupIds.value = [];
  Object.keys(attributeDrafts).forEach((key) => {
    attributeDrafts[key] = "";
  });
}

function toggleSort(key) {
  sortState.value = nextSortState(sortState.value, key);
}

function sortLabel(key) {
  return sortIndicator(sortState.value, key);
}

function applyTargetSelection(target) {
  selectedTarget.value = target;
  form.id = target.id;
  form.name = target.name;
  form.ip_range = target.ip_range || "";
  form.target_type = target.target_type || "network";
  form.domain = target.domain || "";
  form.description = target.description || "";
  selectedGroupIds.value = [...target.group_ids];

  attributeDefinitions.value.forEach((definition) => {
    const valueItem = target.attribute_values.find(
      (item) => item.attribute_definition_id === definition.id
    );
    attributeDrafts[definition.id] = valueItem?.value_text || "";
  });
}

async function loadData() {
  const [targetList, definitionList, groupList] = await Promise.all([
    getTargetsEnriched(),
    getList("target-attribute-definitions"),
    getList("target-groups"),
  ]);
  targets.value = targetList;
  attributeDefinitions.value = definitionList.sort((left, right) =>
    left.attribute_name.localeCompare(right.attribute_name)
  );
  targetGroups.value = groupList.sort((left, right) => left.name.localeCompare(right.name));

  attributeDefinitions.value.forEach((definition) => {
    if (!(definition.id in attributeDrafts)) {
      attributeDrafts[definition.id] = "";
    }
  });

  if (selectedTarget.value) {
    const refreshed = targets.value.find((item) => item.id === selectedTarget.value.id);
    if (refreshed) {
      applyTargetSelection(refreshed);
    } else {
      resetForm();
    }
  }
}

function selectTarget(target) {
  applyTargetSelection(target);
}

async function submitTarget() {
  const payload = {
    name: form.name,
    ip_range: form.ip_range || null,
    target_type: form.target_type,
    domain: form.domain || null,
    description: form.description || null,
  };
  const saved = form.id
    ? await updateManagedTarget(form.id, payload)
    : await createManagedTarget(payload);
  message.value = form.id ? "Đã cập nhật target." : "Đã tạo target mới.";
  await loadData();
  const refreshed = targets.value.find((item) => item.id === saved.id);
  if (refreshed) {
    applyTargetSelection(refreshed);
  }
}

async function saveAttributes() {
  if (!selectedTarget.value) return;
  await updateTargetAttributeValues(
    selectedTarget.value.id,
    attributeDefinitions.value.map((definition) => ({
      attribute_definition_id: definition.id,
      value_text: attributeDrafts[definition.id] || null,
    }))
  );
  message.value = "Đã lưu thuộc tính target.";
  await loadData();
}

async function saveGroups() {
  if (!selectedTarget.value) return;
  await updateTargetGroups(selectedTarget.value.id, selectedGroupIds.value);
  message.value = "Đã cập nhật nhóm target.";
  await loadData();
}

async function removeTarget(targetId) {
  await deleteManagedTarget(targetId);
  message.value = "Đã xóa target.";
  if (selectedTarget.value?.id === targetId) {
    resetForm();
  }
  await loadData();
}

function handleFileChange(event) {
  importFile.value = event.target.files?.[0] || null;
}

async function submitImport() {
  if (!importFile.value) return;
  const result = await importTargetsFile(importFile.value);
  importMessage.value =
    `Đã import ${result.imported_targets} target, tạo mới ${result.created_targets}, ` +
    `cập nhật ${result.updated_targets}, sinh ${result.created_attribute_definitions} thuộc tính mới.`;
  importFile.value = null;
  await loadData();
}

loadData();
</script>

<template>
  <section class="page-header">
    <div>
      <p class="eyebrow">Resource manager</p>
      <h2>{{ title }}</h2>
      <p class="page-copy">
        CRUD co ban cho giai doan khoi tao du an. Nhap cac truong dang JSON bang object hop le.
      </p>
    </div>
    <button class="ghost-button" @click="loadItems">Refresh</button>
  </section>

  <section class="panel-grid">
    <article class="panel panel-form">
      <div class="panel-head">
        <h3>{{ form.id ? "Cap nhat ban ghi" : "Tao moi ban ghi" }}</h3>
      </div>

      <form class="resource-form" @submit.prevent="submitForm">
        <label v-for="field in allFormFields" :key="field" class="field-block">
          <span>{{ field }}</span>
          <select v-if="isBooleanField(field)" v-model="form[field]">
            <option value="">Chon gia tri</option>
            <option value="true">true</option>
            <option value="false">false</option>
          </select>
          <textarea
            v-else-if="isLongTextField(field) || isJsonField(field)"
            v-model="form[field]"
            :placeholder="isJsonField(field) ? '{}' : ''"
            rows="4"
          />
          <input v-else v-model="form[field]" :type="inputType(field)" />
        </label>

        <div class="form-actions">
          <button class="primary-button" type="submit">{{ form.id ? "Luu thay doi" : "Tao moi" }}</button>
          <button v-if="form.id" class="ghost-button" type="button" @click="resetForm">Bo chon</button>
        </div>
      </form>
    </article>

    <article class="panel panel-table">
      <div class="panel-head">
        <h3>Danh sach</h3>
        <span class="badge">{{ items.length }} records</span>
      </div>

      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th v-for="field in fields" :key="field">{{ field }}</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in items" :key="item.id">
              <td>{{ item.id }}</td>
              <td v-for="field in fields" :key="field">{{ displayValue(item[field]) }}</td>
              <td class="action-cell">
                <button class="table-button" @click="editItem(item)">Edit</button>
                <button class="table-button danger" @click="removeItem(item.id)">Delete</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </article>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { createItem, deleteItem, getList, updateItem } from "../api/client";

const props = defineProps({
  title: { type: String, required: true },
  resource: { type: String, required: true },
  fields: { type: Array, required: true },
  jsonFields: { type: Array, default: () => [] },
  longTextFields: { type: Array, default: () => [] },
});

const items = ref([]);
const form = reactive({});

const allFormFields = computed(() => {
  const merged = [...props.fields, ...props.jsonFields, ...props.longTextFields];
  return [...new Set(merged)];
});

function resetForm() {
  Object.keys(form).forEach((key) => delete form[key]);
  allFormFields.value.forEach((field) => {
    form[field] = props.jsonFields.includes(field) ? "{}" : "";
  });
  form.id = null;
}

function isJsonField(field) {
  return props.jsonFields.includes(field);
}

function isLongTextField(field) {
  return props.longTextFields.includes(field);
}

function isBooleanField(field) {
  return field.startsWith("is_") || field === "continue_on_error";
}

function inputType(field) {
  if (field.includes("level") || field.includes("port") || field.includes("_id")) return "number";
  return "text";
}

function displayValue(value) {
  if (value === null || value === undefined || value === "") return "-";
  if (typeof value === "object") return JSON.stringify(value);
  if (typeof value === "boolean") return value ? "true" : "false";
  return value;
}

function toPayload() {
  const payload = {};
  allFormFields.value.forEach((field) => {
    const rawValue = form[field];
    if (rawValue === "" || rawValue === null || rawValue === undefined) return;
    if (isJsonField(field)) {
      payload[field] = typeof rawValue === "string" ? JSON.parse(rawValue || "{}") : rawValue;
      return;
    }
    if (isBooleanField(field)) {
      payload[field] = rawValue === true || rawValue === "true";
      return;
    }
    if (field.includes("level") || field.includes("port") || field.endsWith("_id")) {
      payload[field] = Number(rawValue);
      return;
    }
    payload[field] = rawValue;
  });
  return payload;
}

async function loadItems() {
  items.value = await getList(props.resource);
}

function editItem(item) {
  resetForm();
  Object.entries(item).forEach(([key, value]) => {
    form[key] = isJsonField(key) ? JSON.stringify(value || {}, null, 2) : value;
  });
}

async function submitForm() {
  const payload = toPayload();
  if (form.id) {
    await updateItem(props.resource, form.id, payload);
  } else {
    await createItem(props.resource, payload);
  }
  resetForm();
  await loadItems();
}

async function removeItem(id) {
  await deleteItem(props.resource, id);
  if (form.id === id) resetForm();
  await loadItems();
}

onMounted(async () => {
  resetForm();
  await loadItems();
});
</script>

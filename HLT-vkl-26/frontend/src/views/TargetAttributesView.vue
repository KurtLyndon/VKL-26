<template>
  <section class="page-header">
    <div>
      <p class="eyebrow">Mục tiêu</p>
      <h2>Quản lý Target Attribute</h2>
      <p class="page-copy">
        Khai báo các thuộc tính động để dùng cho lọc, thống kê và gán giá trị cho từng target.
      </p>
    </div>
    <button class="ghost-button" @click="loadData">Làm mới</button>
  </section>

  <section class="panel-grid">
    <article class="panel">
      <div class="panel-head">
        <h3>{{ form.id ? "Cập nhật thuộc tính" : "Thêm thuộc tính" }}</h3>
        <span class="badge">{{ definitions.length }} thuộc tính</span>
      </div>

      <form class="resource-form" @submit.prevent="submitDefinition">
        <label class="field-block">
          <span>Tên thuộc tính</span>
          <input v-model="form.attribute_name" required />
        </label>

        <label class="field-block">
          <span>Mã thuộc tính</span>
          <input v-model="form.attribute_code" placeholder="Tự sinh nếu bỏ trống" />
        </label>

        <label class="field-block">
          <span>Kiểu dữ liệu</span>
          <select v-model="form.data_type">
            <option value="text">text</option>
            <option value="textarea">textarea</option>
            <option value="number">number</option>
            <option value="date">date</option>
          </select>
        </label>

        <label class="field-block">
          <span>Giá trị mặc định</span>
          <input v-model="form.default_value" />
        </label>

        <label class="field-block">
          <span>Mô tả</span>
          <textarea v-model="form.description" rows="3" />
        </label>

        <label class="switch-line">
          <input v-model="form.is_required" type="checkbox" />
          <span>Bắt buộc</span>
        </label>

        <div class="form-actions">
          <button class="primary-button" type="submit">{{ form.id ? "Lưu thuộc tính" : "Tạo thuộc tính" }}</button>
          <button v-if="form.id" class="ghost-button" type="button" @click="resetForm">Bỏ chọn</button>
        </div>
      </form>

      <p v-if="message" class="inline-note">{{ message }}</p>
    </article>

    <article class="panel">
      <div class="panel-head">
        <h3>Danh sách thuộc tính</h3>
        <span class="badge">{{ definitions.length }} bản ghi</span>
      </div>

      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Tên</th>
              <th>Mã</th>
              <th>Kiểu</th>
              <th>Bắt buộc</th>
              <th>Tác vụ</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="definition in definitions" :key="definition.id">
              <td>{{ definition.id }}</td>
              <td>{{ definition.attribute_name }}</td>
              <td>{{ definition.attribute_code }}</td>
              <td>{{ definition.data_type }}</td>
              <td>{{ definition.is_required ? "Có" : "Không" }}</td>
              <td class="action-cell">
                <button class="table-button" @click="editDefinition(definition)">Sửa</button>
                <button class="table-button danger" @click="removeDefinition(definition.id)">Xóa</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </article>
  </section>
</template>

<script setup>
import { reactive, ref } from "vue";
import {
  createTargetAttributeDefinitionManaged,
  deleteTargetAttributeDefinitionManaged,
  getList,
  updateItem,
} from "../api/client";

const definitions = ref([]);
const message = ref("");

const form = reactive({
  id: null,
  attribute_name: "",
  attribute_code: "",
  data_type: "text",
  default_value: "",
  description: "",
  is_required: false,
});

function resetForm() {
  form.id = null;
  form.attribute_name = "";
  form.attribute_code = "";
  form.data_type = "text";
  form.default_value = "";
  form.description = "";
  form.is_required = false;
}

async function loadData() {
  definitions.value = await getList("target-attribute-definitions");
}

function editDefinition(definition) {
  form.id = definition.id;
  form.attribute_name = definition.attribute_name;
  form.attribute_code = definition.attribute_code || "";
  form.data_type = definition.data_type || "text";
  form.default_value = definition.default_value || "";
  form.description = definition.description || "";
  form.is_required = definition.is_required;
}

async function submitDefinition() {
  const payload = {
    attribute_name: form.attribute_name,
    attribute_code: form.attribute_code || null,
    data_type: form.data_type,
    default_value: form.default_value || null,
    description: form.description || null,
    is_required: form.is_required,
  };
  if (form.id) {
    await updateItem("target-attribute-definitions", form.id, payload);
    message.value = "Đã cập nhật thuộc tính.";
  } else {
    await createTargetAttributeDefinitionManaged(payload);
    message.value = "Đã tạo thuộc tính mới.";
  }
  resetForm();
  await loadData();
}

async function removeDefinition(definitionId) {
  await deleteTargetAttributeDefinitionManaged(definitionId);
  message.value = "Đã xóa thuộc tính.";
  if (form.id === definitionId) {
    resetForm();
  }
  await loadData();
}

loadData();
</script>

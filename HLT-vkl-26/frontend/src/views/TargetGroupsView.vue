<template>
  <section class="page-header">
    <div>
      <p class="eyebrow">Mục tiêu</p>
      <h2>Quản lý Target Group</h2>
      <p class="page-copy">
        Quản lý nhóm target và thêm hoặc gỡ target khỏi từng nhóm ngay trên giao diện.
      </p>
    </div>
    <button class="ghost-button" @click="loadData">Làm mới</button>
  </section>

  <section class="panel-grid">
    <article class="panel">
      <div class="panel-head">
        <h3>{{ form.id ? "Cập nhật nhóm" : "Thêm nhóm" }}</h3>
        <span class="badge">{{ groups.length }} nhóm</span>
      </div>

      <form class="resource-form" @submit.prevent="submitGroup">
        <label class="field-block">
          <span>Tên nhóm</span>
          <input v-model="form.name" required />
        </label>

        <label class="field-block">
          <span>Mã nhóm</span>
          <input v-model="form.code" placeholder="Tự sinh nếu bỏ trống" />
        </label>

        <label class="field-block">
          <span>Mô tả</span>
          <textarea v-model="form.description" rows="4" />
        </label>

        <div class="form-actions">
          <button class="primary-button" type="submit">{{ form.id ? "Lưu nhóm" : "Tạo nhóm" }}</button>
          <button v-if="form.id" class="ghost-button" type="button" @click="resetForm">Bỏ chọn</button>
        </div>
      </form>

      <p v-if="message" class="inline-note">{{ message }}</p>
    </article>

    <article class="panel">
      <div class="panel-head">
        <h3>Danh sách nhóm</h3>
        <span class="badge">{{ groups.length }} bản ghi</span>
      </div>

      <div class="runtime-list">
        <button
          v-for="group in groups"
          :key="group.id"
          class="runtime-card"
          :class="{ active: selectedGroup?.id === group.id }"
          @click="selectGroup(group)"
        >
          <strong>{{ group.name }}</strong>
          <span>{{ group.code }}</span>
          <small>{{ group.description || "Chưa có mô tả" }}</small>
        </button>
      </div>
    </article>
  </section>

  <section class="panel-grid">
    <article class="panel">
      <div class="panel-head">
        <h3>Thành viên nhóm</h3>
        <span class="badge">{{ selectedGroup ? selectedGroup.name : "chưa chọn" }}</span>
      </div>

      <div v-if="selectedGroup" class="group-check-grid">
        <label v-for="target in targets" :key="target.id" class="switch-line">
          <input v-model="selectedTargetIds" :value="target.id" type="checkbox" />
          <span>{{ target.name }} <small>({{ target.ip_range || "no-ip" }})</small></span>
        </label>
      </div>

      <div v-if="selectedGroup" class="form-actions">
        <button class="primary-button" type="button" @click="saveMembers">Lưu thành viên</button>
        <button class="table-button danger" type="button" @click="removeGroup(selectedGroup.id)">Xóa nhóm</button>
      </div>

      <p v-else class="inline-note">Chọn một nhóm để thêm hoặc gỡ target.</p>
    </article>
  </section>
</template>

<script setup>
import { reactive, ref } from "vue";
import {
  createTargetGroupManaged,
  deleteTargetGroupManaged,
  getList,
  getTargetsEnriched,
  updateItem,
  updateTargetGroupMembers,
} from "../api/client";

const groups = ref([]);
const targets = ref([]);
const selectedGroup = ref(null);
const selectedTargetIds = ref([]);
const message = ref("");

const form = reactive({
  id: null,
  name: "",
  code: "",
  description: "",
});

function resetForm() {
  form.id = null;
  form.name = "";
  form.code = "";
  form.description = "";
  selectedGroup.value = null;
  selectedTargetIds.value = [];
}

async function loadData() {
  const [groupList, targetList] = await Promise.all([getList("target-groups"), getTargetsEnriched()]);
  groups.value = groupList.sort((left, right) => left.name.localeCompare(right.name));
  targets.value = targetList.sort((left, right) => left.name.localeCompare(right.name));

  if (selectedGroup.value) {
    const refreshed = groups.value.find((item) => item.id === selectedGroup.value.id);
    if (refreshed) {
      selectGroup(refreshed);
    } else {
      resetForm();
    }
  }
}

function selectGroup(group) {
  selectedGroup.value = group;
  form.id = group.id;
  form.name = group.name;
  form.code = group.code || "";
  form.description = group.description || "";
  selectedTargetIds.value = targets.value
    .filter((target) => target.group_ids.includes(group.id))
    .map((target) => target.id);
}

async function submitGroup() {
  const payload = {
    name: form.name,
    code: form.code || null,
    description: form.description || null,
  };
  const saved = form.id ? await updateItem("target-groups", form.id, payload) : await createTargetGroupManaged(payload);
  message.value = form.id ? "Đã cập nhật nhóm target." : "Đã tạo nhóm target.";
  await loadData();
  const refreshed = groups.value.find((item) => item.id === saved.id);
  if (refreshed) {
    selectGroup(refreshed);
  }
}

async function saveMembers() {
  if (!selectedGroup.value) return;
  await updateTargetGroupMembers(selectedGroup.value.id, selectedTargetIds.value);
  message.value = "Đã cập nhật thành viên nhóm.";
  await loadData();
}

async function removeGroup(groupId) {
  await deleteTargetGroupManaged(groupId);
  message.value = "Đã xóa nhóm target.";
  if (selectedGroup.value?.id === groupId) {
    resetForm();
  }
  await loadData();
}

loadData();
</script>

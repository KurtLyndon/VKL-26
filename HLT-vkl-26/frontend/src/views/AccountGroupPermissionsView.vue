<template>
  <section class="page-header">
    <div>
      <p class="eyebrow">RBAC management</p>
      <h2>Quyền theo nhóm</h2>
      <p class="page-copy">Chọn nhóm tài khoản, sau đó bật hoặc tắt quyền cho từng phân hệ.</p>
    </div>
    <button class="ghost-button" @click="loadData">Refresh</button>
  </section>

  <section class="panel-grid">
    <article class="panel">
      <div class="panel-head">
        <h3>Nhóm tài khoản</h3>
        <span class="badge">{{ groups.length }} nhóm</span>
      </div>

      <div class="runtime-list">
        <button
          v-for="group in groups"
          :key="group.id"
          class="runtime-card"
          :class="{ active: selectedGroupId === group.id }"
          @click="selectGroup(group.id)"
        >
          <strong>{{ group.name }}</strong>
          <span>{{ group.code }}</span>
          <small>{{ group.is_active ? "active" : "inactive" }}</small>
        </button>
      </div>
    </article>

    <article class="panel">
      <div class="panel-head">
        <h3>Quyền</h3>
        <span class="badge">{{ permissionItems.length }} quyền</span>
      </div>

      <div v-if="selectedGroupId" class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>Module</th>
              <th>Mã quyền</th>
              <th>Tên quyền</th>
              <th>Bật / tắt</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in permissionItems" :key="item.permission_id">
              <td>{{ item.module_name }}</td>
              <td>{{ item.permission_code }}</td>
              <td>{{ item.permission_name }}</td>
              <td>
                <label class="switch-line">
                  <input v-model="item.is_enabled" type="checkbox" />
                  <span>{{ item.is_enabled ? "enabled" : "disabled" }}</span>
                </label>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <p v-else class="inline-note">Chọn một nhóm tài khoản để quản lý quyền.</p>

      <div class="form-actions" v-if="selectedGroupId">
        <button class="primary-button" type="button" @click="savePermissions">Lưu quyền</button>
      </div>

      <p class="inline-note" v-if="message">{{ message }}</p>
    </article>
  </section>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { getGroupPermissions, getList, updateGroupPermissions } from "../api/client";

const groups = ref([]);
const permissionItems = ref([]);
const selectedGroupId = ref(null);
const message = ref("");

async function loadData() {
  groups.value = await getList("account-groups");
  if (!selectedGroupId.value && groups.value.length > 0) {
    await selectGroup(groups.value[0].id);
  } else if (selectedGroupId.value) {
    permissionItems.value = await getGroupPermissions(selectedGroupId.value);
  }
}

async function selectGroup(groupId) {
  selectedGroupId.value = groupId;
  permissionItems.value = await getGroupPermissions(groupId);
}

async function savePermissions() {
  await updateGroupPermissions(
    selectedGroupId.value,
    permissionItems.value.map((item) => ({
      permission_id: item.permission_id,
      is_enabled: item.is_enabled,
    }))
  );
  message.value = "Đã cập nhật quyền cho nhóm tài khoản.";
}

onMounted(loadData);
</script>

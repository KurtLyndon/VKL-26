<template>
  <section class="page-header">
    <div>
      <p class="eyebrow">RBAC management</p>
      <h2>Quyền theo Nhóm</h2>
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
        <span class="badge">{{ totalItems }} quyền</span>
      </div>

      <div v-if="selectedGroupId" class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th class="sortable-header" @click="toggleSort('module_name')">Module{{ sortLabel("module_name") }}</th>
              <th class="sortable-header" @click="toggleSort('permission_code')">
                Mã quyền{{ sortLabel("permission_code") }}
              </th>
              <th class="sortable-header" @click="toggleSort('permission_name')">
                Tên quyền{{ sortLabel("permission_name") }}
              </th>
              <th class="sortable-header" @click="toggleSort('is_enabled')">Bật / tắt{{ sortLabel("is_enabled") }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in paginatedItems" :key="item.permission_id">
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

      <PaginationBar
        v-if="selectedGroupId"
        :current-page="currentPage"
        :page-size="pageSize"
        :total-items="totalItems"
        :total-pages="totalPages"
        @update:page-size="pageSize = $event"
        @previous="goToPreviousPage"
        @next="goToNextPage"
      />

      <div v-if="selectedGroupId" class="form-actions">
        <button class="primary-button" type="button" @click="savePermissions">Lưu quyền</button>
      </div>

      <p v-if="message" class="inline-note">{{ message }}</p>
    </article>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { getGroupPermissions, getList, updateGroupPermissions } from "../api/client";
import PaginationBar from "../components/PaginationBar.vue";
import { usePagination } from "../composables/usePagination";
import { nextSortState, sortIndicator, sortRows } from "../utils/tableSort";

const groups = ref([]);
const permissionItems = ref([]);
const selectedGroupId = ref(null);
const message = ref("");
const sortState = ref({ key: "module_name", direction: "desc" });

const sortedPermissionItems = computed(() => sortRows(permissionItems.value, sortState.value));
const { currentPage, pageSize, paginatedItems, totalItems, totalPages, goToPreviousPage, goToNextPage } =
  usePagination(sortedPermissionItems);

function toggleSort(key) {
  sortState.value = nextSortState(sortState.value, key);
}

function sortLabel(key) {
  return sortIndicator(sortState.value, key);
}

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

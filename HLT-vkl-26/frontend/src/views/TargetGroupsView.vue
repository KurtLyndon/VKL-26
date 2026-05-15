<template>
  <section class="page-header">
    <div>
      <p class="eyebrow">Mục tiêu</p>
      <h2>Quản lý Nhóm Target</h2>
      <p class="page-copy">Quản lý nhóm target và thao tác thành viên theo dạng bảng để dễ lọc, rà soát và cập nhật.</p>
    </div>
    <button class="ghost-button" @click="loadData">Làm mới</button>
  </section>

  <section class="panel-grid">
    <article class="panel">
      <div class="panel-head">
        <h3>Danh sách Nhóm Target</h3>
        <span class="badge">{{ totalGroupItems }} bản ghi</span>
      </div>

      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th class="sortable-header" @click="toggleGroupSort('id')">ID{{ groupSortLabel("id") }}</th>
              <th class="sortable-header" @click="toggleGroupSort('name')">Tên nhóm{{ groupSortLabel("name") }}</th>
              <th class="sortable-header" @click="toggleGroupSort('code')">Mã nhóm{{ groupSortLabel("code") }}</th>
              <th class="sortable-header" @click="toggleGroupSort('description')">Mô tả{{ groupSortLabel("description") }}</th>
              <th>Tác vụ</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="group in paginatedGroups"
              :key="group.id"
              class="row-selectable"
              :class="{ 'row-selected': selectedGroup?.id === group.id }"
              @click="selectGroup(group)"
            >
              <td>{{ group.id }}</td>
              <td>{{ group.name }}</td>
              <td>{{ group.code || "-" }}</td>
              <td>{{ group.description || "-" }}</td>
              <td class="action-cell">
                <button class="table-button danger" @click.stop="removeGroup(group.id)">Xóa</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <PaginationBar
        :current-page="groupCurrentPage"
        :page-size="groupPageSize"
        :total-items="totalGroupItems"
        :total-pages="groupTotalPages"
        @update:page-size="groupPageSize = $event"
        @previous="goToPreviousGroupPage"
        @next="goToNextGroupPage"
      />
    </article>

    <article class="panel">
      <div class="panel-head">
        <h3>{{ form.id ? "Chỉnh sửa Nhóm Target" : "Thêm Nhóm Target" }}</h3>
        <span class="badge">{{ form.id ? `ID ${form.id}` : "tạo mới" }}</span>
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
  </section>

  <section class="panel-grid">
    <article class="panel">
      <div class="panel-head">
        <h3>Thành viên Nhóm Target</h3>
        <span class="badge">{{ selectedGroup ? selectedGroup.name : "chưa chọn" }}</span>
      </div>

      <div v-if="selectedGroup" class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th class="sortable-header" @click="toggleMemberSort('id')">ID target{{ memberSortLabel("id") }}</th>
              <th class="sortable-header" @click="toggleMemberSort('name')">Tên target{{ memberSortLabel("name") }}</th>
              <th class="sortable-header" @click="toggleMemberSort('target_type')">Loại{{ memberSortLabel("target_type") }}</th>
              <th class="sortable-header" @click="toggleMemberSort('ip_range')">Dải IP{{ memberSortLabel("ip_range") }}</th>
              <th class="sortable-header" @click="toggleMemberSort('domain')">Domain{{ memberSortLabel("domain") }}</th>
              <th>Chọn</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="target in paginatedTargets" :key="target.id">
              <td>{{ target.id }}</td>
              <td>{{ target.name }}</td>
              <td>{{ target.target_type || "-" }}</td>
              <td>{{ target.ip_range || "-" }}</td>
              <td>{{ target.domain || "-" }}</td>
              <td>
                <input v-model="selectedTargetIds" :value="target.id" type="checkbox" />
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <PaginationBar
        v-if="selectedGroup"
        :current-page="targetCurrentPage"
        :page-size="targetPageSize"
        :total-items="totalTargetItems"
        :total-pages="targetTotalPages"
        @update:page-size="targetPageSize = $event"
        @previous="goToPreviousTargetPage"
        @next="goToNextTargetPage"
      />

      <div v-if="selectedGroup" class="form-actions">
        <button class="primary-button" type="button" @click="saveMembers">Lưu thành viên</button>
      </div>

      <p v-else class="inline-note">Chọn một nhóm để quản lý thành viên.</p>
    </article>
  </section>
</template>

<script setup>
import { computed, reactive, ref } from "vue";
import {
  createTargetGroupManaged,
  deleteTargetGroupManaged,
  getList,
  getTargetsEnriched,
  updateItem,
  updateTargetGroupMembers,
} from "../api/client";
import PaginationBar from "../components/PaginationBar.vue";
import { usePagination } from "../composables/usePagination";
import { nextSortState, sortIndicator, sortRows } from "../utils/tableSort";

const groups = ref([]);
const targets = ref([]);
const selectedGroup = ref(null);
const selectedTargetIds = ref([]);
const message = ref("");
const groupSortState = ref({ key: "id", direction: "desc" });
const memberSortState = ref({ key: "id", direction: "desc" });

const form = reactive({
  id: null,
  name: "",
  code: "",
  description: "",
});

const sortedGroups = computed(() => sortRows(groups.value, groupSortState.value));
const sortedTargets = computed(() => sortRows(targets.value, memberSortState.value));

const {
  currentPage: groupCurrentPage,
  pageSize: groupPageSize,
  paginatedItems: paginatedGroups,
  totalItems: totalGroupItems,
  totalPages: groupTotalPages,
  goToPreviousPage: goToPreviousGroupPage,
  goToNextPage: goToNextGroupPage,
} = usePagination(sortedGroups);

const {
  currentPage: targetCurrentPage,
  pageSize: targetPageSize,
  paginatedItems: paginatedTargets,
  totalItems: totalTargetItems,
  totalPages: targetTotalPages,
  goToPreviousPage: goToPreviousTargetPage,
  goToNextPage: goToNextTargetPage,
} = usePagination(sortedTargets);

function resetForm() {
  form.id = null;
  form.name = "";
  form.code = "";
  form.description = "";
  selectedGroup.value = null;
  selectedTargetIds.value = [];
}

function toggleGroupSort(key) {
  groupSortState.value = nextSortState(groupSortState.value, key);
}

function toggleMemberSort(key) {
  memberSortState.value = nextSortState(memberSortState.value, key);
}

function groupSortLabel(key) {
  return sortIndicator(groupSortState.value, key);
}

function memberSortLabel(key) {
  return sortIndicator(memberSortState.value, key);
}

async function loadData() {
  const [groupList, targetList] = await Promise.all([getList("target-groups"), getTargetsEnriched()]);
  groups.value = groupList;
  targets.value = targetList;

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

<template>
  <section class="page-header">
    <div>
      <p class="eyebrow">Result exchange</p>
      <h2>Import / Export Results</h2>
      <p class="page-copy">Export kết quả operation ra JSON, CSV, XLSX và import lại dữ liệu scan từ JSON.</p>
    </div>
    <button class="ghost-button" @click="loadData">Refresh</button>
  </section>

  <section class="panel-grid">
    <article class="panel">
      <div class="panel-head">
        <h3>Export</h3>
        <span class="badge">{{ operations.length }} operations</span>
      </div>

      <form class="resource-form" @submit.prevent="submitExport">
        <label class="field-block">
          <span>operation_id</span>
          <select v-model="selectedOperationId">
            <option value="">Chọn operation</option>
            <option v-for="operation in operations" :key="operation.id" :value="String(operation.id)">
              {{ operation.code }} - {{ operation.name }}
            </option>
          </select>
        </label>

        <label class="field-block">
          <span>file_format</span>
          <select v-model="exportFormat">
            <option value="json">json</option>
            <option value="csv">csv</option>
            <option value="xlsx">xlsx</option>
          </select>
        </label>

        <div class="form-actions">
          <button class="primary-button" type="submit" :disabled="!selectedOperationId">Export</button>
        </div>
      </form>

      <p v-if="exportMessage" class="inline-note">{{ exportMessage }}</p>
    </article>

    <article class="panel">
      <div class="panel-head">
        <h3>Import JSON</h3>
        <span class="badge">scan_results + findings</span>
      </div>

      <form class="resource-form" @submit.prevent="submitImport">
        <label class="field-block">
          <span>operation_id</span>
          <select v-model="selectedOperationId">
            <option value="">Chọn operation</option>
            <option v-for="operation in operations" :key="operation.id" :value="String(operation.id)">
              {{ operation.code }} - {{ operation.name }}
            </option>
          </select>
        </label>

        <label class="field-block">
          <span>payload_json</span>
          <textarea v-model="importPayload" rows="10" placeholder='{"scan_results":[],"findings":[]}' />
        </label>

        <div class="form-actions">
          <button class="primary-button" type="submit" :disabled="!selectedOperationId">Import</button>
        </div>
      </form>

      <p v-if="importMessage" class="inline-note">{{ importMessage }}</p>
    </article>
  </section>

  <section class="panel-grid">
    <article class="panel">
      <div class="panel-head">
        <h3>History</h3>
        <span class="badge">{{ totalItems }} bản ghi</span>
      </div>

      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th class="sortable-header" @click="toggleSort('id')">ID{{ sortLabel("id") }}</th>
              <th class="sortable-header" @click="toggleSort('operation_id')">
                operation_id{{ sortLabel("operation_id") }}
              </th>
              <th class="sortable-header" @click="toggleSort('action_type')">
                action_type{{ sortLabel("action_type") }}
              </th>
              <th class="sortable-header" @click="toggleSort('file_name')">file_name{{ sortLabel("file_name") }}</th>
              <th class="sortable-header" @click="toggleSort('file_format')">
                file_format{{ sortLabel("file_format") }}
              </th>
              <th class="sortable-header" @click="toggleSort('status')">status{{ sortLabel("status") }}</th>
              <th class="sortable-header" @click="toggleSort('note')">note{{ sortLabel("note") }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in paginatedItems" :key="item.id">
              <td>{{ item.id }}</td>
              <td>{{ item.operation_id }}</td>
              <td>{{ item.action_type }}</td>
              <td>{{ item.file_name }}</td>
              <td>{{ item.file_format }}</td>
              <td>{{ item.status }}</td>
              <td>{{ item.note || "-" }}</td>
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
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { exportOperationResults, getList, importOperationResults } from "../api/client";
import PaginationBar from "../components/PaginationBar.vue";
import { usePagination } from "../composables/usePagination";
import { nextSortState, sortIndicator, sortRows } from "../utils/tableSort";

const operations = ref([]);
const historyItems = ref([]);
const selectedOperationId = ref("");
const exportFormat = ref("json");
const importPayload = ref('{"scan_results":[],"findings":[]}');
const exportMessage = ref("");
const importMessage = ref("");
const sortState = ref({ key: "id", direction: "desc" });

const filteredHistory = computed(() =>
  historyItems.value.filter((item) => !selectedOperationId.value || item.operation_id === Number(selectedOperationId.value))
);

const sortedHistory = computed(() => sortRows(filteredHistory.value, sortState.value));
const { currentPage, pageSize, paginatedItems, totalItems, totalPages, goToPreviousPage, goToNextPage } =
  usePagination(sortedHistory);

function toggleSort(key) {
  sortState.value = nextSortState(sortState.value, key);
}

function sortLabel(key) {
  return sortIndicator(sortState.value, key);
}

async function loadData() {
  const [operationList, historyList] = await Promise.all([getList("operations"), getList("operation-result-history")]);
  operations.value = operationList;
  historyItems.value = historyList;
  if (!selectedOperationId.value && operationList.length > 0) {
    selectedOperationId.value = String(operationList[0].id);
  }
}

async function submitExport() {
  const result = await exportOperationResults(Number(selectedOperationId.value), exportFormat.value);
  exportMessage.value = `Đã export ${result.exported_records} record sang ${result.history.file_name}.`;
  await loadData();
}

async function submitImport() {
  const payload = JSON.parse(importPayload.value || "{}");
  const result = await importOperationResults(Number(selectedOperationId.value), payload);
  importMessage.value = `Đã import ${result.imported_scan_results} scan result và ${result.imported_findings} finding.`;
  await loadData();
}

onMounted(loadData);
</script>

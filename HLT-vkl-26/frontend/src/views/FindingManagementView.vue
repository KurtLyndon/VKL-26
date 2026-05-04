<template>
  <section class="page-header">
    <div>
      <p class="eyebrow">Kết quả lỗ hổng</p>
      <h2>Quản lý Finding</h2>
      <p class="page-copy">
        Mô tả và mức độ của finding được đồng bộ từ CVE đã map. Analyst chỉ chỉnh trạng thái, ghi chú, thông tin kỹ thuật bổ sung và tệp PoC.
      </p>
    </div>
    <button class="ghost-button" @click="refreshAll">Làm mới</button>
  </section>

  <section class="panel panel-accent finding-filter-panel">
    <div class="panel-head">
      <h3>Bộ lọc Finding</h3>
      <span class="badge">{{ totalItems }} finding sau lọc</span>
    </div>

    <div class="filter-grid">
      <label class="field-block">
        <span>Operation</span>
        <select v-model="filters.operationExecutionId">
          <option value="">Tất cả</option>
          <option v-for="option in filterOptions.operations" :key="option.id" :value="String(option.id)">
            {{ option.label }}
          </option>
        </select>
      </label>

      <label class="field-block">
        <span>Target</span>
        <select v-model="filters.targetId">
          <option value="">Tất cả</option>
          <option v-for="option in filterOptions.targets" :key="option.id" :value="String(option.id)">
            {{ option.label }}
          </option>
        </select>
      </label>

      <label class="field-block">
        <span>Trạng thái</span>
        <select v-model="filters.statusValue">
          <option value="">Tất cả</option>
          <option v-for="option in filterOptions.statuses" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
      </label>
    </div>

    <div class="finding-status-help-grid">
      <article v-for="option in filterOptions.statuses" :key="option.value" class="finding-status-help-card">
        <div class="finding-status-help-head">
          <StatusPill :value="option.value" />
        </div>
        <p>{{ option.help_text }}</p>
      </article>
    </div>
  </section>

  <section class="finding-layout">
    <article class="panel finding-list-panel">
      <div class="panel-head">
        <h3>Danh sách Finding</h3>
        <span class="badge">{{ totalItems }} bản ghi</span>
      </div>

      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th class="sortable-header" @click="toggleSort('id')">ID{{ sortLabel("id") }}</th>
              <th class="sortable-header" @click="toggleSort('ip_address')">IP{{ sortLabel("ip_address") }}</th>
              <th class="sortable-header" @click="toggleSort('finding_code')">Mã finding{{ sortLabel("finding_code") }}</th>
              <th class="sortable-header" @click="toggleSort('severity')">Mức độ{{ sortLabel("severity") }}</th>
              <th class="sortable-header" @click="toggleSort('status')">Trạng thái{{ sortLabel("status") }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in paginatedItems"
              :key="item.id"
              class="row-selectable"
              :class="{ 'row-selected': selectedFindingId === item.id }"
              @click="selectItem(item)"
            >
              <td>{{ item.id }}</td>
              <td>{{ item.ip_address || "-" }}</td>
              <td>{{ item.finding_code }}</td>
              <td><StatusPill :value="item.severity || 'info'" /></td>
              <td>
                <div class="finding-status-cell" @click.stop>
                  <select
                    class="compact-select"
                    :value="item.status"
                    @change="updateListStatus(item, $event.target.value)"
                  >
                    <option
                      v-for="statusOption in allowedStatusOptions(item)"
                      :key="statusOption.value"
                      :value="statusOption.value"
                    >
                      {{ statusOption.label }}
                    </option>
                  </select>
                  <small>{{ statusHelpText(item.status) }}</small>
                </div>
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

    <article class="panel finding-poc-panel">
      <div class="panel-head">
        <h3>PoC của Finding</h3>
        <span class="badge">{{ selectedFileLabel }}</span>
      </div>

      <div v-if="selectedFindingId" class="resource-form">
        <label class="field-block">
          <span>Upload / thay thế PoC</span>
          <input type="file" accept=".txt,.log,.json,.csv,.md,.png,.jpg,.jpeg,.gif,.webp,.bmp,.rar,.zip,.7z" @change="handleFileChange" />
          <small class="field-help">Khi upload hoặc thay thế PoC, trạng thái finding sẽ tự chuyển sang <code>confirmed</code>.</small>
        </label>

        <div class="form-actions">
          <button class="primary-button" type="button" :disabled="!uploadFile" @click="uploadPoc">Upload PoC</button>
          <button class="ghost-button" type="button" :disabled="!form.poc_file_path" @click="downloadPoc">Tải file</button>
          <button class="ghost-button" type="button" :disabled="!form.poc_file_path" @click="previewPoc">Preview</button>
          <button class="table-button danger" type="button" :disabled="!form.poc_file_path" @click="removePoc">Xóa PoC</button>
        </div>

        <div class="insight-grid">
          <article class="insight-card">
            <span>Tên file</span>
            <strong>{{ form.poc_file_name || "-" }}</strong>
          </article>
          <article class="insight-card">
            <span>MIME</span>
            <strong>{{ form.poc_file_mime_type || "-" }}</strong>
          </article>
          <article class="insight-card">
            <span>Kích thước</span>
            <strong>{{ formatFileSize(form.poc_file_size) }}</strong>
          </article>
        </div>

        <p class="inline-note">
          Khi xóa PoC, trạng thái finding sẽ tự chuyển lại <code>open</code>. Tệp PoC được lưu ở server để phục vụ báo cáo và xác minh.
        </p>
      </div>

      <p v-else class="inline-note">Chọn một finding từ danh sách để quản lý PoC.</p>
      <p v-if="fileMessage" class="inline-note">{{ fileMessage }}</p>
      <p v-if="fileError" class="inline-note text-danger">{{ fileError }}</p>
    </article>

    <article class="panel finding-preview-panel">
      <div class="panel-head">
        <h3>Preview PoC</h3>
        <span class="badge">{{ previewState.kindLabel }}</span>
      </div>

      <div v-if="previewState.loading" class="inline-note">Đang tải preview...</div>
      <pre v-else-if="previewState.type === 'text'" class="preview-text">{{ previewState.text }}</pre>
      <div v-else-if="previewState.type === 'image'" class="preview-image-wrap">
        <img :src="previewState.imageUrl" alt="POC preview" class="preview-image" />
      </div>
      <p v-else class="inline-note">{{ previewState.message }}</p>
    </article>

    <article class="panel finding-edit-panel">
      <div class="panel-head">
        <h3>Thông tin Finding</h3>
        <span class="badge">{{ selectedFindingId ? `ID ${selectedFindingId}` : "chưa chọn" }}</span>
      </div>

      <div v-if="selectedFindingId" class="resource-form">
        <div class="filter-grid">
          <label class="field-block">
            <span>Operation</span>
            <input :value="form.operation_label || '-'" disabled />
          </label>
          <label class="field-block">
            <span>Target</span>
            <input :value="form.target_label || '-'" disabled />
          </label>
          <label class="field-block">
            <span>IP</span>
            <input :value="form.ip_address || '-'" disabled />
          </label>
        </div>

        <div class="filter-grid">
          <label class="field-block">
            <span>Mã finding</span>
            <input :value="form.finding_code || '-'" disabled />
          </label>
          <label class="field-block">
            <span>Mức độ</span>
            <input :value="form.severity || '-'" disabled />
          </label>
          <label class="field-block">
            <span>Trạng thái</span>
            <select v-model="form.status">
              <option v-for="statusOption in editableStatusOptions" :key="statusOption.value" :value="statusOption.value">
                {{ statusOption.label }}
              </option>
            </select>
            <small class="field-help">{{ currentStatusHelpText }}</small>
          </label>
        </div>

        <label class="field-block">
          <span>Mô tả từ CVE</span>
          <textarea :value="form.description || ''" rows="4" disabled />
        </label>

        <div class="filter-grid">
          <label class="field-block">
            <span>Port</span>
            <input v-model.number="form.port" type="number" min="0" />
          </label>
          <label class="field-block">
            <span>Protocol</span>
            <input v-model="form.protocol" />
          </label>
          <label class="field-block">
            <span>Service</span>
            <input v-model="form.service_name" />
          </label>
        </div>

        <div class="filter-grid">
          <label class="field-block">
            <span>Confidence</span>
            <input v-model.number="form.confidence" type="number" min="0" max="100" />
          </label>
          <label class="field-block">
            <span>First seen</span>
            <input :value="formatDateTime(form.first_seen_at)" disabled />
          </label>
          <label class="field-block">
            <span>Last seen</span>
            <input :value="formatDateTime(form.last_seen_at)" disabled />
          </label>
        </div>

        <label class="field-block">
          <span>Note</span>
          <textarea v-model="form.note" rows="4" />
        </label>

        <label class="field-block">
          <span>Evidence</span>
          <textarea :value="form.evidence || ''" rows="3" disabled />
          <small class="field-help">Evidence hiện để trống để dành cho output runtime hoặc đường dẫn tệp về sau.</small>
        </label>

        <div class="form-actions">
          <button class="primary-button" type="button" @click="saveFinding">Lưu thay đổi</button>
          <button class="ghost-button" type="button" @click="reloadSelectedFinding">Nạp lại</button>
        </div>
      </div>

      <p v-else class="inline-note">Chọn một finding từ danh sách để xem chi tiết và cập nhật trạng thái hoặc ghi chú.</p>
      <p v-if="message" class="inline-note">{{ message }}</p>
    </article>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import {
  deleteFindingPocFile,
  downloadFindingPocFile,
  getFindingFilterOptions,
  getManagedFinding,
  getManagedFindings,
  updateManagedFinding,
  updateManagedFindingStatus,
  uploadFindingPocFile,
} from "../api/client";
import PaginationBar from "../components/PaginationBar.vue";
import StatusPill from "../components/StatusPill.vue";
import { usePagination } from "../composables/usePagination";
import { nextSortState, sortIndicator, sortRows } from "../utils/tableSort";

const items = ref([]);
const message = ref("");
const fileMessage = ref("");
const fileError = ref("");
const uploadFile = ref(null);
const selectedFindingId = ref(null);
const sortState = ref({ key: "id", direction: "desc" });
const filterOptions = reactive({
  operations: [],
  targets: [],
  statuses: [],
});
const filters = reactive({
  operationExecutionId: "",
  targetId: "",
  statusValue: "",
});
const previewState = reactive({
  type: "none",
  text: "",
  imageUrl: "",
  message: "Chưa có preview.",
  loading: false,
  kindLabel: "chưa có",
});
const form = reactive({
  id: null,
  operation_label: "",
  target_label: "",
  ip_address: "",
  finding_code: "",
  severity: "",
  description: "",
  port: null,
  protocol: "",
  service_name: "",
  note: "",
  evidence: "",
  confidence: null,
  status: "open",
  first_seen_at: null,
  last_seen_at: null,
  poc_file_name: "",
  poc_file_path: "",
  poc_file_mime_type: "",
  poc_file_size: null,
});

const sortedItems = computed(() => sortRows(items.value, sortState.value));
const { currentPage, pageSize, paginatedItems, totalItems, totalPages, goToPreviousPage, goToNextPage } =
  usePagination(sortedItems);

const selectedFileLabel = computed(() => form.poc_file_name || "chưa có file");
const statusOptionMap = computed(() =>
  Object.fromEntries(filterOptions.statuses.map((option) => [option.value, option]))
);
const editableStatusOptions = computed(() => {
  const current = form.status || "open";
  const currentOption = statusOptionMap.value[current];
  const allowed = new Set([current, ...(currentOption?.allowed_next_statuses || [])]);
  return filterOptions.statuses.filter((option) => allowed.has(option.value));
});
const currentStatusHelpText = computed(() => statusHelpText(form.status));

function resetPreview() {
  if (previewState.imageUrl) {
    URL.revokeObjectURL(previewState.imageUrl);
  }
  previewState.type = "none";
  previewState.text = "";
  previewState.imageUrl = "";
  previewState.message = "Chưa có preview.";
  previewState.loading = false;
  previewState.kindLabel = "chưa có";
}

function resetForm() {
  form.id = null;
  form.operation_label = "";
  form.target_label = "";
  form.ip_address = "";
  form.finding_code = "";
  form.severity = "";
  form.description = "";
  form.port = null;
  form.protocol = "";
  form.service_name = "";
  form.note = "";
  form.evidence = "";
  form.confidence = null;
  form.status = "open";
  form.first_seen_at = null;
  form.last_seen_at = null;
  form.poc_file_name = "";
  form.poc_file_path = "";
  form.poc_file_mime_type = "";
  form.poc_file_size = null;
  uploadFile.value = null;
  selectedFindingId.value = null;
  resetPreview();
}

function applyFindingData(item) {
  selectedFindingId.value = item.id;
  form.id = item.id;
  form.operation_label = item.operation_label || "";
  form.target_label = item.target_label || "";
  form.ip_address = item.ip_address || "";
  form.finding_code = item.finding_code || "";
  form.severity = item.severity || "";
  form.description = item.description || "";
  form.port = item.port;
  form.protocol = item.protocol || "";
  form.service_name = item.service_name || "";
  form.note = item.note || "";
  form.evidence = item.evidence || "";
  form.confidence = item.confidence;
  form.status = item.status || "open";
  form.first_seen_at = item.first_seen_at || null;
  form.last_seen_at = item.last_seen_at || null;
  form.poc_file_name = item.poc_file_name || "";
  form.poc_file_path = item.poc_file_path || "";
  form.poc_file_mime_type = item.poc_file_mime_type || "";
  form.poc_file_size = item.poc_file_size;
  uploadFile.value = null;
  fileMessage.value = "";
  fileError.value = "";
  resetPreview();
}

function updateLocalItem(updatedItem) {
  items.value = items.value.map((item) => (item.id === updatedItem.id ? updatedItem : item));
  if (selectedFindingId.value === updatedItem.id) {
    applyFindingData(updatedItem);
  }
}

function toggleSort(key) {
  sortState.value = nextSortState(sortState.value, key);
}

function sortLabel(key) {
  return sortIndicator(sortState.value, key);
}

function statusHelpText(statusValue) {
  return statusOptionMap.value[statusValue]?.help_text || "Trạng thái hiện tại của finding.";
}

function allowedStatusOptions(item) {
  const current = item.status || "open";
  const currentOption = statusOptionMap.value[current];
  const allowed = new Set([current, ...(currentOption?.allowed_next_statuses || [])]);
  return filterOptions.statuses.filter((option) => allowed.has(option.value));
}

function selectItem(item) {
  applyFindingData(item);
}

async function loadFilterOptions() {
  const data = await getFindingFilterOptions(filters.operationExecutionId ? Number(filters.operationExecutionId) : null);
  filterOptions.operations = data.operations || [];
  filterOptions.targets = data.targets || [];
  filterOptions.statuses = data.statuses || [];

  if (filters.targetId && !filterOptions.targets.some((option) => String(option.id) === filters.targetId)) {
    filters.targetId = "";
  }
  if (filters.statusValue && !filterOptions.statuses.some((option) => option.value === filters.statusValue)) {
    filters.statusValue = "";
  }
}

async function loadItems() {
  items.value = await getManagedFindings({
    operation_execution_id: filters.operationExecutionId ? Number(filters.operationExecutionId) : null,
    target_id: filters.targetId ? Number(filters.targetId) : null,
    status_value: filters.statusValue || null,
  });

  if (selectedFindingId.value) {
    const selectedItem = items.value.find((item) => item.id === selectedFindingId.value);
    if (selectedItem) {
      applyFindingData(selectedItem);
    } else {
      resetForm();
    }
  }
}

async function refreshAll() {
  await loadFilterOptions();
  await loadItems();
}

async function reloadSelectedFinding() {
  if (!selectedFindingId.value) return;
  const finding = await getManagedFinding(selectedFindingId.value);
  updateLocalItem(finding);
}

async function saveFinding() {
  if (!selectedFindingId.value) return;
  const updated = await updateManagedFinding(selectedFindingId.value, {
    port: form.port === null || form.port === "" ? null : Number(form.port),
    protocol: form.protocol || null,
    service_name: form.service_name || null,
    note: form.note || null,
    confidence: form.confidence === null || form.confidence === "" ? null : Number(form.confidence),
    status: form.status || null,
  });
  message.value = "Đã cập nhật finding.";
  updateLocalItem(updated);
  await loadItems();
}

async function updateListStatus(item, nextStatus) {
  if (!nextStatus || nextStatus === item.status) return;
  const updated = await updateManagedFindingStatus(item.id, nextStatus);
  message.value = `Đã chuyển trạng thái finding #${item.id} sang ${updated.status}.`;
  updateLocalItem(updated);
  await loadItems();
}

function handleFileChange(event) {
  uploadFile.value = event.target.files?.[0] || null;
}

async function uploadPoc() {
  if (!selectedFindingId.value || !uploadFile.value) return;
  fileError.value = "";
  const updated = await uploadFindingPocFile(selectedFindingId.value, uploadFile.value);
  updateLocalItem(updated);
  fileMessage.value = "Đã upload / thay thế file PoC. Trạng thái finding được chuyển sang confirmed.";
  uploadFile.value = null;
  await loadItems();
}

function parseDownloadFileName(response, fallbackName) {
  const disposition = response.headers["content-disposition"] || "";
  const matched = disposition.match(/filename="?([^"]+)"?/i);
  return matched?.[1] || fallbackName || "poc-file";
}

function detectPreviewType(fileName, mimeType) {
  const lowerName = (fileName || "").toLowerCase();
  const lowerMime = (mimeType || "").toLowerCase();
  if (lowerMime.startsWith("image/")) return "image";
  if (lowerMime.startsWith("text/")) return "text";
  if ([".txt", ".log", ".json", ".csv", ".md", ".xml", ".html"].some((ext) => lowerName.endsWith(ext))) return "text";
  return "none";
}

async function previewPoc() {
  if (!selectedFindingId.value || !form.poc_file_path) return;
  fileError.value = "";
  fileMessage.value = "";
  resetPreview();
  previewState.loading = true;
  try {
    const response = await downloadFindingPocFile(selectedFindingId.value);
    const blob = response.data;
    const previewType = detectPreviewType(form.poc_file_name, form.poc_file_mime_type || blob.type);
    if (previewType === "image") {
      previewState.type = "image";
      previewState.imageUrl = URL.createObjectURL(blob);
      previewState.kindLabel = "ảnh";
      previewState.message = "";
    } else if (previewType === "text") {
      previewState.type = "text";
      previewState.text = await blob.text();
      previewState.kindLabel = "text";
      previewState.message = "";
    } else {
      previewState.type = "none";
      previewState.kindLabel = "không preview";
      previewState.message = "File nén hoặc định dạng này hiện chưa có preview.";
    }
  } catch (error) {
    previewState.type = "none";
    previewState.kindLabel = "lỗi";
    previewState.message = error?.response?.data?.detail || error?.message || "Không thể tải preview file PoC.";
  } finally {
    previewState.loading = false;
  }
}

async function downloadPoc() {
  if (!selectedFindingId.value || !form.poc_file_path) return;
  fileError.value = "";
  try {
    const response = await downloadFindingPocFile(selectedFindingId.value);
    const blobUrl = URL.createObjectURL(response.data);
    const anchor = document.createElement("a");
    anchor.href = blobUrl;
    anchor.download = parseDownloadFileName(response, form.poc_file_name);
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(blobUrl);
    fileMessage.value = "Đã tải file PoC về máy.";
  } catch (error) {
    fileError.value = error?.response?.data?.detail || error?.message || "Không thể tải file PoC.";
  }
}

async function removePoc() {
  if (!selectedFindingId.value || !form.poc_file_path) return;
  fileError.value = "";
  const updated = await deleteFindingPocFile(selectedFindingId.value);
  updateLocalItem(updated);
  fileMessage.value = "Đã xóa file PoC. Trạng thái finding được chuyển lại open.";
  resetPreview();
  await loadItems();
}

function formatFileSize(size) {
  if (!size) return "-";
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDateTime(value) {
  if (!value) return "-";
  return new Date(value).toLocaleString("vi-VN");
}

watch(
  () => filters.operationExecutionId,
  async () => {
    filters.targetId = "";
    await loadFilterOptions();
    await loadItems();
  }
);

watch(
  () => [filters.targetId, filters.statusValue],
  async () => {
    await loadItems();
  }
);

onMounted(async () => {
  await refreshAll();
});

onBeforeUnmount(() => {
  resetPreview();
});
</script>

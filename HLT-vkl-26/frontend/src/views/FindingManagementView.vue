<template>
  <section class="page-header">
    <div>
      <p class="eyebrow">Kết quả lỗ hổng</p>
      <h2>Quản lý Finding</h2>
      <p class="page-copy">Title của finding được lấy theo mã finding. Ghi chú vận hành dùng cột note, còn evidence để trống cho output hoặc đường dẫn PoC trong tương lai.</p>
    </div>
    <button class="ghost-button" @click="loadItems">Làm mới</button>
  </section>

  <section class="panel-grid">
    <article class="panel panel-table">
      <div class="panel-head">
        <h3>Danh sách Finding</h3>
        <span class="badge">{{ totalItems }} bản ghi</span>
      </div>

      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th class="sortable-header" @click="toggleSort('id')">ID{{ sortLabel("id") }}</th>
              <th class="sortable-header" @click="toggleSort('finding_code')">Mã finding{{ sortLabel("finding_code") }}</th>
              <th class="sortable-header" @click="toggleSort('title')">Title{{ sortLabel("title") }}</th>
              <th class="sortable-header" @click="toggleSort('severity')">Mức độ{{ sortLabel("severity") }}</th>
              <th class="sortable-header" @click="toggleSort('port')">Port{{ sortLabel("port") }}</th>
              <th class="sortable-header" @click="toggleSort('service_name')">Service{{ sortLabel("service_name") }}</th>
              <th class="sortable-header" @click="toggleSort('status')">Trạng thái{{ sortLabel("status") }}</th>
              <th>Tác vụ</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in paginatedItems"
              :key="item.id"
              class="row-selectable"
              :class="{ 'row-selected': form.id === item.id }"
              @click="selectItem(item)"
            >
              <td>{{ item.id }}</td>
              <td>{{ item.finding_code }}</td>
              <td>{{ item.finding_code }}</td>
              <td>{{ item.severity || "-" }}</td>
              <td>{{ item.port ?? "-" }}</td>
              <td>{{ item.service_name || "-" }}</td>
              <td>{{ item.status }}</td>
              <td class="action-cell">
                <button class="table-button danger" @click.stop="removeItem(item.id)">Xóa</button>
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
        <h3>{{ form.id ? "Cập nhật Finding" : "Thêm Finding" }}</h3>
        <span class="badge">{{ form.id ? `ID ${form.id}` : "tạo mới" }}</span>
      </div>

      <form class="resource-form" @submit.prevent="submitForm">
        <div class="filter-grid">
          <label class="field-block">
            <span>Scan result ID</span>
            <input v-model.number="form.scan_result_id" type="number" min="1" required />
          </label>

          <label class="field-block">
            <span>Vulnerability ID</span>
            <input v-model.number="form.vulnerability_id" type="number" min="1" />
          </label>
        </div>

        <div class="filter-grid">
          <label class="field-block">
            <span>Mã finding</span>
            <input v-model="form.finding_code" required />
          </label>

          <label class="field-block">
            <span>Title</span>
            <input :value="form.finding_code" disabled />
            <small class="field-help">Title tự đồng bộ theo mã finding.</small>
          </label>
        </div>

        <div class="filter-grid">
          <label class="field-block">
            <span>Mức độ</span>
            <select v-model="form.severity">
              <option value="">-</option>
              <option value="info">info</option>
              <option value="low">low</option>
              <option value="medium">medium</option>
              <option value="high">high</option>
              <option value="critical">critical</option>
            </select>
          </label>

          <label class="field-block">
            <span>Trạng thái</span>
            <select v-model="form.status">
              <option value="open">open</option>
              <option value="accepted">accepted</option>
              <option value="mitigated">mitigated</option>
              <option value="closed">closed</option>
            </select>
          </label>
        </div>

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

        <label class="field-block">
          <span>Mô tả</span>
          <textarea v-model="form.description" rows="4" />
        </label>

        <label class="field-block">
          <span>Note</span>
          <textarea v-model="form.note" rows="4" />
        </label>

        <label class="field-block">
          <span>Evidence</span>
          <textarea :value="form.evidence || ''" rows="3" disabled />
          <small class="field-help">Cột này đang để trống để dành cho output hoặc đường dẫn file PoC về sau.</small>
        </label>

        <label class="field-block">
          <span>Confidence</span>
          <input v-model.number="form.confidence" type="number" min="0" max="100" />
        </label>

        <div class="form-actions">
          <button class="primary-button" type="submit">{{ form.id ? "Lưu thay đổi" : "Tạo mới" }}</button>
          <button v-if="form.id" class="ghost-button" type="button" @click="resetForm">Bỏ chọn</button>
        </div>
      </form>

      <p v-if="message" class="inline-note">{{ message }}</p>
    </article>
  </section>

  <section class="panel-grid">
    <article class="panel">
      <div class="panel-head">
        <h3>File PoC của Finding</h3>
        <span class="badge">{{ selectedFileLabel }}</span>
      </div>

      <div v-if="form.id" class="resource-form">
        <label class="field-block">
          <span>Upload file PoC</span>
          <input type="file" accept=".txt,.log,.json,.csv,.md,.png,.jpg,.jpeg,.gif,.webp,.bmp,.rar,.zip,.7z" @change="handleFileChange" />
        </label>

        <div class="form-actions">
          <button class="primary-button" type="button" :disabled="!uploadFile" @click="uploadPoc">Upload / thay thế file</button>
          <button class="ghost-button" type="button" :disabled="!form.poc_file_path" @click="downloadPoc">Tải file về</button>
          <button class="ghost-button" type="button" :disabled="!form.poc_file_path" @click="previewPoc">Preview</button>
          <button class="table-button danger" type="button" :disabled="!form.poc_file_path" @click="removePoc">Xóa file</button>
        </div>

        <div class="insight-grid">
          <article class="insight-card">
            <span>Tên file người dùng upload</span>
            <strong>{{ form.poc_file_name || "-" }}</strong>
          </article>
          <article class="insight-card">
            <span>Kiểu MIME</span>
            <strong>{{ form.poc_file_mime_type || "-" }}</strong>
          </article>
          <article class="insight-card">
            <span>Kích thước</span>
            <strong>{{ formatFileSize(form.poc_file_size) }}</strong>
          </article>
        </div>

        <p class="inline-note">File PoC kết quả/đính kèm sẽ được lưu ở server trong thư mục dữ liệu riêng cho finding, không lưu ở frontend.</p>
      </div>

      <p v-else class="inline-note">Chọn một finding để upload, tải hoặc preview file PoC.</p>
      <p v-if="fileMessage" class="inline-note">{{ fileMessage }}</p>
      <p v-if="fileError" class="inline-note text-danger">{{ fileError }}</p>
    </article>

    <article class="panel">
      <div class="panel-head">
        <h3>Preview file PoC</h3>
        <span class="badge">{{ previewState.kindLabel }}</span>
      </div>

      <div v-if="previewState.loading" class="inline-note">Đang tải preview...</div>
      <pre v-else-if="previewState.type === 'text'" class="preview-text">{{ previewState.text }}</pre>
      <div v-else-if="previewState.type === 'image'" class="preview-image-wrap">
        <img :src="previewState.imageUrl" alt="POC preview" class="preview-image" />
      </div>
      <p v-else class="inline-note">{{ previewState.message }}</p>
    </article>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import {
  createItem,
  deleteFindingPocFile,
  deleteItem,
  downloadFindingPocFile,
  getList,
  updateItem,
  uploadFindingPocFile,
} from "../api/client";
import PaginationBar from "../components/PaginationBar.vue";
import { usePagination } from "../composables/usePagination";
import { nextSortState, sortIndicator, sortRows } from "../utils/tableSort";

const items = ref([]);
const message = ref("");
const fileMessage = ref("");
const fileError = ref("");
const uploadFile = ref(null);
const sortState = ref({ key: "id", direction: "desc" });
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
  scan_result_id: null,
  vulnerability_id: null,
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
  poc_file_name: "",
  poc_file_path: "",
  poc_file_mime_type: "",
  poc_file_size: null,
});

const sortedItems = computed(() => sortRows(items.value, sortState.value));
const { currentPage, pageSize, paginatedItems, totalItems, totalPages, goToPreviousPage, goToNextPage } =
  usePagination(sortedItems);

const selectedFileLabel = computed(() => form.poc_file_name || "chưa có file");

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
  form.scan_result_id = null;
  form.vulnerability_id = null;
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
  form.poc_file_name = "";
  form.poc_file_path = "";
  form.poc_file_mime_type = "";
  form.poc_file_size = null;
  uploadFile.value = null;
  resetPreview();
}

function toggleSort(key) {
  sortState.value = nextSortState(sortState.value, key);
}

function sortLabel(key) {
  return sortIndicator(sortState.value, key);
}

function selectItem(item) {
  form.id = item.id;
  form.scan_result_id = item.scan_result_id;
  form.vulnerability_id = item.vulnerability_id;
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
  form.poc_file_name = item.poc_file_name || "";
  form.poc_file_path = item.poc_file_path || "";
  form.poc_file_mime_type = item.poc_file_mime_type || "";
  form.poc_file_size = item.poc_file_size;
  uploadFile.value = null;
  fileError.value = "";
  fileMessage.value = "";
  resetPreview();
}

function updateLocalItem(updatedItem) {
  items.value = items.value.map((item) => (item.id === updatedItem.id ? updatedItem : item));
  if (form.id === updatedItem.id) {
    selectItem(updatedItem);
  }
}

async function loadItems() {
  items.value = await getList("scan-findings");
}

async function submitForm() {
  const payload = {
    scan_result_id: Number(form.scan_result_id),
    vulnerability_id: form.vulnerability_id ? Number(form.vulnerability_id) : null,
    finding_code: form.finding_code.trim(),
    title: form.finding_code.trim(),
    severity: form.severity || null,
    description: form.description || null,
    port: form.port === null || form.port === "" ? null : Number(form.port),
    protocol: form.protocol || null,
    service_name: form.service_name || null,
    note: form.note || null,
    evidence: null,
    confidence: form.confidence === null || form.confidence === "" ? null : Number(form.confidence),
    status: form.status || "open",
  };
  if (form.id) {
    const updated = await updateItem("scan-findings", form.id, payload);
    message.value = "Đã cập nhật finding.";
    updateLocalItem(updated);
  } else {
    await createItem("scan-findings", payload);
    message.value = "Đã tạo finding mới.";
    resetForm();
    await loadItems();
  }
}

async function removeItem(id) {
  await deleteItem("scan-findings", id);
  if (form.id === id) {
    resetForm();
  }
  message.value = "Đã xóa finding.";
  await loadItems();
}

function handleFileChange(event) {
  uploadFile.value = event.target.files?.[0] || null;
}

async function uploadPoc() {
  if (!form.id || !uploadFile.value) return;
  fileError.value = "";
  const updated = await uploadFindingPocFile(form.id, uploadFile.value);
  updateLocalItem(updated);
  uploadFile.value = null;
  fileMessage.value = "Đã upload file PoC cho finding.";
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
  if (!form.id || !form.poc_file_path) return;
  fileError.value = "";
  fileMessage.value = "";
  resetPreview();
  previewState.loading = true;
  try {
    const response = await downloadFindingPocFile(form.id);
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
      previewState.message = "File nén hoặc định dạng này hiện không có preview.";
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
  if (!form.id || !form.poc_file_path) return;
  fileError.value = "";
  try {
    const response = await downloadFindingPocFile(form.id);
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
  if (!form.id || !form.poc_file_path) return;
  fileError.value = "";
  const updated = await deleteFindingPocFile(form.id);
  updateLocalItem(updated);
  resetPreview();
  fileMessage.value = "Đã xóa file PoC khỏi server.";
}

function formatFileSize(size) {
  if (!size) return "-";
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

onMounted(async () => {
  resetForm();
  await loadItems();
});

onBeforeUnmount(() => {
  resetPreview();
});
</script>

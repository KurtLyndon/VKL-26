<template>
  <section class="page-header">
    <div>
      <p class="eyebrow">Danh mục</p>
      <h2>Result Explorer</h2>
      <p class="page-copy">Tra cứu mục tiêu, IP, dịch vụ, finding, vulnerability và evidence từ dữ liệu scan đã chuẩn hóa.</p>
    </div>
    <button class="ghost-button" type="button" @click="refreshAll">Làm mới</button>
  </section>

  <section class="panel result-explorer-filter-panel">
    <div class="panel-head">
      <h3>Bộ lọc</h3>
      <span class="badge">{{ totalItems }} dòng</span>
    </div>

    <div class="filter-grid result-explorer-filter-grid">
      <label class="field-block">
        <span>Operation</span>
        <select v-model="filters.operationId">
          <option value="">Tất cả</option>
          <option v-for="option in filterOptions.operations" :key="option.id" :value="String(option.id)">
            {{ option.label }}
          </option>
        </select>
      </label>

      <label class="field-block">
        <span>Năm</span>
        <select v-model="filters.year">
          <option value="">Tất cả</option>
          <option v-for="year in filterOptions.years" :key="year" :value="String(year)">{{ year }}</option>
        </select>
      </label>

      <label class="field-block">
        <span>Quý</span>
        <select v-model="filters.quarter">
          <option value="">Tất cả</option>
          <option v-for="quarter in filterOptions.quarters" :key="quarter" :value="String(quarter)">Q{{ quarter }}</option>
        </select>
      </label>

      <label class="field-block">
        <span>Tháng</span>
        <select v-model="filters.month">
          <option value="">Tất cả</option>
          <option v-for="month in filterOptions.months" :key="month" :value="String(month)">Tháng {{ month }}</option>
        </select>
      </label>

      <label class="field-block">
        <span>Tuần</span>
        <select v-model="filters.week">
          <option value="">Tất cả</option>
          <option v-for="week in filterOptions.weeks" :key="week" :value="String(week)">W{{ week }}</option>
        </select>
      </label>

      <label class="field-block result-explorer-search">
        <span>Search target / IP</span>
        <input v-model="filters.q" placeholder="Tên target, dải IP, IP scan result" @keyup.enter="loadItems" />
      </label>
    </div>

    <div class="form-actions result-explorer-toolbar">
      <div class="segmented-control" aria-label="Chế độ xem Result Explorer">
        <button type="button" :class="{ active: filters.mode === 'full' }" @click="setMode('full')">Full</button>
        <button type="button" :class="{ active: filters.mode === 'threat' }" @click="setMode('threat')">Threat</button>
      </div>
      <button class="primary-button" type="button" @click="loadItems">Tra cứu</button>
      <button class="ghost-button" type="button" @click="resetFilters">Xóa lọc</button>
    </div>

    <p v-if="errorMessage" class="inline-note text-danger">{{ errorMessage }}</p>
  </section>

  <section class="result-explorer-layout">
    <article class="panel result-explorer-table-panel">
      <div class="panel-head">
        <h3>Kết quả</h3>
        <span class="badge">{{ responseModeLabel }}</span>
      </div>

      <div v-if="loading" class="inline-note">Đang tải dữ liệu...</div>
      <div v-else class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>STT</th>
              <th class="sortable-header" @click="toggleSort('target_name')">Tên mục tiêu{{ sortLabel("target_name") }}</th>
              <th class="sortable-header" @click="toggleSort('ip_address')">IP scan{{ sortLabel("ip_address") }}</th>
              <th class="sortable-header" @click="toggleSort('finding_code')">Mã lỗ hổng{{ sortLabel("finding_code") }}</th>
              <th class="sortable-header" @click="toggleSort('severity')">Mức độ{{ sortLabel("severity") }}</th>
              <th class="sortable-header" @click="toggleSort('finding_status')">Trạng thái{{ sortLabel("finding_status") }}</th>
              <th class="sortable-header" @click="toggleSort('port')">Port{{ sortLabel("port") }}</th>
              <th class="sortable-header" @click="toggleSort('service')">Service{{ sortLabel("service") }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(item, index) in paginatedItems"
              :key="item.row_id"
              class="row-selectable"
              :class="{ 'row-selected': selectedRowId === item.row_id }"
              @click="selectItem(item)"
            >
              <td>{{ rowNumber(index) }}</td>
              <td>{{ item.target_name }}</td>
              <td>{{ item.ip_address || "-" }}</td>
              <td>{{ item.finding_code || "-" }}</td>
              <td>
                <StatusPill v-if="item.severity" :value="item.severity" />
                <span v-else>-</span>
              </td>
              <td>
                <StatusPill v-if="item.finding_status" :value="item.finding_status" />
                <span v-else>-</span>
              </td>
              <td>{{ item.port ?? "-" }}</td>
              <td>{{ item.service || "-" }}</td>
            </tr>
            <tr v-if="!paginatedItems.length">
              <td colspan="8">Không có dữ liệu phù hợp.</td>
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

    <article class="panel result-explorer-detail-panel">
      <div class="panel-head">
        <h3>Chi tiết</h3>
        <span class="badge">{{ selectedItem ? selectedItem.row_id : "chưa chọn" }}</span>
      </div>

      <template v-if="selectedItem">
        <div class="detail-section">
          <h4>Operation / Scan</h4>
          <div class="detail-grid">
            <InfoItem label="Operation" :value="operationTitle" />
            <InfoItem label="Operation Execution" :value="selectedItem.operation.execution_code" />
            <InfoItem label="Năm" :value="selectedItem.operation.year" />
            <InfoItem label="Quý" :value="selectedItem.operation.quarter ? `Q${selectedItem.operation.quarter}` : null" />
            <InfoItem label="Tháng" :value="selectedItem.operation.month" />
            <InfoItem label="Tuần" :value="selectedItem.operation.week ? `W${selectedItem.operation.week}` : null" />
            <InfoItem label="Batch/source" :value="selectedItem.operation.batch_code || selectedItem.operation.source_file_name" />
            <InfoItem label="source_root_path" :value="selectedItem.operation.source_root_path" wide />
          </div>
        </div>

        <div class="detail-section">
          <h4>Target</h4>
          <div class="detail-grid">
            <InfoItem label="target_id" :value="selectedItem.target.target_id" />
            <InfoItem label="code" :value="selectedItem.target.code" />
            <InfoItem label="Tên mục tiêu" :value="selectedItem.target.name" />
            <InfoItem label="target_type" :value="selectedItem.target.target_type" />
            <InfoItem label="Dải IP" :value="selectedItem.target.ip_range" />
            <InfoItem label="Domain" :value="selectedItem.target.domain" />
            <InfoItem label="Description" :value="selectedItem.target.description" wide />
          </div>
          <div class="tag-list">
            <span v-for="attribute in selectedItem.target.attributes" :key="attribute.attribute_code" class="detail-tag">
              {{ attribute.attribute_name }}: {{ attribute.value_text || "-" }}
            </span>
            <span v-for="group in selectedItem.target.groups" :key="group.id" class="detail-tag detail-tag-strong">
              {{ group.name }}
            </span>
            <span v-if="!selectedItem.target.attributes.length && !selectedItem.target.groups.length" class="inline-note">
              Target chưa có attribute động hoặc group.
            </span>
          </div>
        </div>

        <div class="detail-section">
          <h4>Scan Result</h4>
          <div class="detail-grid">
            <InfoItem label="scan_result_id" :value="selectedItem.scan_result.scan_result_id" />
            <InfoItem label="IP cụ thể" :value="selectedItem.scan_result.ip_address" />
            <InfoItem label="Port" :value="selectedItem.scan_result.port" />
            <InfoItem label="Protocol" :value="selectedItem.scan_result.protocol" />
            <InfoItem label="Service" :value="selectedItem.scan_result.service" />
            <InfoItem label="Version" :value="selectedItem.scan_result.version" />
            <InfoItem label="source_tool" :value="selectedItem.scan_result.source_tool" />
            <InfoItem label="detected_at" :value="formatDateTime(selectedItem.scan_result.detected_at)" />
            <InfoItem label="parse_status" :value="selectedItem.scan_result.parse_status" />
            <InfoItem label="note" :value="selectedItem.scan_result.note" wide />
          </div>
          <details class="result-details">
            <summary>Raw / normalized summary</summary>
            <pre class="preview-text">{{ selectedItem.scan_result.normalized_summary || "-" }}</pre>
            <pre class="preview-text">{{ selectedItem.scan_result.raw_summary || "-" }}</pre>
          </details>
        </div>

        <div class="detail-section">
          <h4>Finding</h4>
          <div v-if="selectedItem.finding" class="detail-grid">
            <InfoItem label="finding_id" :value="selectedItem.finding.finding_id" />
            <InfoItem label="finding_code" :value="selectedItem.finding.finding_code" />
            <InfoItem label="severity" :value="selectedItem.finding.severity" />
            <InfoItem label="status" :value="selectedItem.finding.status" />
            <InfoItem label="port" :value="selectedItem.finding.port" />
            <InfoItem label="protocol" :value="selectedItem.finding.protocol" />
            <InfoItem label="service_name" :value="selectedItem.finding.service_name" />
            <InfoItem label="confidence" :value="selectedItem.finding.confidence" />
            <InfoItem label="first_seen_at" :value="formatDateTime(selectedItem.finding.first_seen_at)" />
            <InfoItem label="last_seen_at" :value="formatDateTime(selectedItem.finding.last_seen_at)" />
            <InfoItem label="note" :value="selectedItem.finding.note" wide />
            <InfoItem label="output runtime" :value="selectedItem.finding.runtime_output" wide />
          </div>
          <p v-else class="inline-note">Record này chưa có finding.</p>
        </div>

        <div class="detail-section">
          <h4>Vulnerability</h4>
          <div v-if="selectedItem.vulnerability" class="detail-grid">
            <InfoItem label="vulnerability_id" :value="selectedItem.vulnerability.vulnerability_id" />
            <InfoItem label="code" :value="selectedItem.vulnerability.code" />
            <InfoItem label="title/name" :value="selectedItem.vulnerability.title" />
            <InfoItem label="level/severity" :value="vulnerabilitySeverityLabel" />
            <InfoItem label="nguy cơ mất ATTT" :value="selectedItem.vulnerability.threat" wide />
            <InfoItem label="kiến nghị đề xuất" :value="selectedItem.vulnerability.proposal" wide />
            <InfoItem label="description" :value="selectedItem.vulnerability.description" wide />
            <InfoItem label="Ghi chú kiểm chứng" :value="selectedItem.vulnerability.evidence_text" wide />
            <InfoItem label="PoC script" :value="vulnerabilityScriptLabel" wide />
          </div>
          <p v-else class="inline-note">Record này chưa map vulnerability.</p>
        </div>

        <div class="detail-section result-evidence-section">
          <div class="panel-head panel-head-compact">
            <h4>Evidence file</h4>
            <span class="badge">{{ selectedEvidenceLabel }}</span>
          </div>
          <template v-if="selectedItem.finding">
            <label class="field-block">
              <span>Upload / thay thế Evidence</span>
              <input type="file" accept=".txt,.log,.json,.csv,.md,.png,.jpg,.jpeg,.gif,.webp,.bmp,.rar,.zip,.7z" @change="handleFileChange" />
            </label>
            <div class="form-actions">
              <button class="primary-button" type="button" :disabled="!uploadFile" @click="uploadEvidence">Upload Evidence</button>
              <button class="ghost-button" type="button" :disabled="!selectedItem.finding.evidence_file_path" @click="downloadEvidence">Tải file</button>
              <button class="ghost-button" type="button" :disabled="!selectedItem.finding.evidence_file_path" @click="previewEvidence">Preview</button>
              <button class="table-button danger" type="button" :disabled="!selectedItem.finding.evidence_file_path" @click="removeEvidence">Xóa Evidence</button>
            </div>
            <div class="insight-grid">
              <article class="insight-card">
                <span>Tên file</span>
                <strong>{{ selectedItem.finding.evidence_file_name || "-" }}</strong>
              </article>
              <article class="insight-card">
                <span>MIME</span>
                <strong>{{ selectedItem.finding.evidence_file_mime_type || "-" }}</strong>
              </article>
              <article class="insight-card">
                <span>Kích thước</span>
                <strong>{{ formatFileSize(selectedItem.finding.evidence_file_size) }}</strong>
              </article>
            </div>
            <p v-if="fileMessage" class="inline-note">{{ fileMessage }}</p>
            <p v-if="fileError" class="inline-note text-danger">{{ fileError }}</p>
            <div class="result-preview-box">
              <div v-if="previewState.loading" class="inline-note">Đang tải preview...</div>
              <pre v-else-if="previewState.type === 'text'" class="preview-text">{{ previewState.text }}</pre>
              <div v-else-if="previewState.type === 'image'" class="preview-image-wrap">
                <img :src="previewState.imageUrl" alt="Evidence preview" class="preview-image" />
              </div>
              <p v-else class="inline-note">{{ previewState.message }}</p>
            </div>
          </template>
          <p v-else class="inline-note">Record này chưa có finding nên chưa có evidence.</p>
        </div>
      </template>

      <p v-else class="inline-note">Chọn một dòng trong bảng để xem chi tiết target, scan result, finding, vulnerability và evidence.</p>
    </article>
  </section>
</template>

<script setup>
import { computed, defineComponent, h, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import {
  deleteFindingEvidenceFile,
  downloadFindingEvidenceFile,
  getResultExplorerFilterOptions,
  getResultExplorerItems,
  uploadFindingEvidenceFile,
} from "../api/client";
import PaginationBar from "../components/PaginationBar.vue";
import StatusPill from "../components/StatusPill.vue";
import { usePagination } from "../composables/usePagination";
import { nextSortState, sortIndicator, sortRows } from "../utils/tableSort";

const InfoItem = defineComponent({
  props: {
    label: { type: String, required: true },
    value: { type: [String, Number, Boolean], default: null },
    wide: { type: Boolean, default: false },
  },
  setup(props) {
    return () =>
      h("article", { class: ["info-item", props.wide ? "info-item-wide" : ""] }, [
        h("span", props.label),
        h("strong", props.value === null || props.value === undefined || props.value === "" ? "-" : String(props.value)),
      ]);
  },
});

const items = ref([]);
const loading = ref(false);
const errorMessage = ref("");
const selectedRowId = ref("");
const sortState = ref({ key: "scan_result_id", direction: "desc" });
const uploadFile = ref(null);
const fileMessage = ref("");
const fileError = ref("");
const responseMode = ref("full");
const filterOptions = reactive({
  operations: [],
  years: [],
  quarters: [],
  months: [],
  weeks: [],
});
const filters = reactive({
  operationId: "",
  year: "",
  quarter: "",
  month: "",
  week: "",
  q: "",
  mode: "full",
});
const previewState = reactive({
  type: "none",
  text: "",
  imageUrl: "",
  message: "Chưa có preview.",
  loading: false,
});

const sortedItems = computed(() => sortRows(items.value, sortState.value));
const { currentPage, pageSize, paginatedItems, totalItems, totalPages, goToPreviousPage, goToNextPage } =
  usePagination(sortedItems);
const selectedItem = computed(() => items.value.find((item) => item.row_id === selectedRowId.value) || null);
const responseModeLabel = computed(() => (responseMode.value === "threat" ? "Threat mode" : "Full mode"));
const operationTitle = computed(() => {
  if (!selectedItem.value) return "-";
  const operation = selectedItem.value.operation;
  return [operation.operation_code, operation.operation_name].filter(Boolean).join(" - ") || "-";
});
const vulnerabilitySeverityLabel = computed(() => {
  const vulnerability = selectedItem.value?.vulnerability;
  if (!vulnerability) return "-";
  return `${vulnerability.level ?? "-"} / ${vulnerability.severity || "-"}`;
});
const vulnerabilityScriptLabel = computed(() => {
  const vulnerability = selectedItem.value?.vulnerability;
  if (!vulnerability) return "-";
  return vulnerability.active_script_name || vulnerability.poc_file_name || "Chưa có script PoC";
});
const selectedEvidenceLabel = computed(() => selectedItem.value?.finding?.evidence_file_name || "chưa có file");

function requestPayload() {
  return {
    operation_id: filters.operationId ? Number(filters.operationId) : null,
    year: filters.year ? Number(filters.year) : null,
    quarter: filters.quarter ? Number(filters.quarter) : null,
    month: filters.month ? Number(filters.month) : null,
    week: filters.week ? Number(filters.week) : null,
    q: filters.q.trim() || null,
    mode: filters.mode,
  };
}

function resetPreview() {
  if (previewState.imageUrl) URL.revokeObjectURL(previewState.imageUrl);
  previewState.type = "none";
  previewState.text = "";
  previewState.imageUrl = "";
  previewState.message = "Chưa có preview.";
  previewState.loading = false;
}

function setMode(mode) {
  filters.mode = mode;
  loadItems();
}

function resetFilters() {
  filters.operationId = "";
  filters.year = "";
  filters.quarter = "";
  filters.month = "";
  filters.week = "";
  filters.q = "";
  filters.mode = "full";
  loadItems();
}

async function loadFilterOptions() {
  const data = await getResultExplorerFilterOptions();
  filterOptions.operations = data.operations || [];
  filterOptions.years = data.years || [];
  filterOptions.quarters = data.quarters || [];
  filterOptions.months = data.months || [];
  filterOptions.weeks = data.weeks || [];
}

async function loadItems({ keepSelection = true } = {}) {
  loading.value = true;
  errorMessage.value = "";
  const previousRowId = selectedRowId.value;
  try {
    const data = await getResultExplorerItems(requestPayload());
    items.value = data.items || [];
    responseMode.value = data.mode || filters.mode;
    if (keepSelection && previousRowId && items.value.some((item) => item.row_id === previousRowId)) {
      selectedRowId.value = previousRowId;
    } else {
      selectedRowId.value = items.value[0]?.row_id || "";
    }
    resetPreview();
  } catch (error) {
    errorMessage.value = error?.response?.data?.detail || error?.message || "Không thể tải Result Explorer.";
  } finally {
    loading.value = false;
  }
}

async function refreshAll() {
  await loadFilterOptions();
  await loadItems();
}

function selectItem(item) {
  selectedRowId.value = item.row_id;
  uploadFile.value = null;
  fileMessage.value = "";
  fileError.value = "";
  resetPreview();
}

function rowNumber(index) {
  return (currentPage.value - 1) * pageSize.value + index + 1;
}

function toggleSort(key) {
  sortState.value = nextSortState(sortState.value, key);
}

function sortLabel(key) {
  return sortIndicator(sortState.value, key);
}

function handleFileChange(event) {
  uploadFile.value = event.target.files?.[0] || null;
}

function updateFindingEvidenceFields(updatedFinding) {
  if (!updatedFinding?.id) return;
  items.value = items.value.map((item) => {
    if (item.finding_id !== updatedFinding.id || !item.finding) return item;
    return {
      ...item,
      finding_status: updatedFinding.status,
      finding: {
        ...item.finding,
        status: updatedFinding.status,
        evidence_file_name: updatedFinding.evidence_file_name,
        evidence_file_path: updatedFinding.evidence_file_path,
        evidence_file_mime_type: updatedFinding.evidence_file_mime_type,
        evidence_file_size: updatedFinding.evidence_file_size,
      },
    };
  });
}

async function uploadEvidence() {
  const findingId = selectedItem.value?.finding?.finding_id;
  if (!findingId || !uploadFile.value) return;
  fileError.value = "";
  const updated = await uploadFindingEvidenceFile(findingId, uploadFile.value);
  updateFindingEvidenceFields(updated);
  uploadFile.value = null;
  fileMessage.value = "Đã upload / thay thế file Evidence.";
}

async function downloadEvidence() {
  const finding = selectedItem.value?.finding;
  if (!finding?.finding_id || !finding.evidence_file_path) return;
  fileError.value = "";
  try {
    const response = await downloadFindingEvidenceFile(finding.finding_id);
    const blobUrl = URL.createObjectURL(response.data);
    const anchor = document.createElement("a");
    anchor.href = blobUrl;
    anchor.download = parseDownloadFileName(response, finding.evidence_file_name);
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(blobUrl);
    fileMessage.value = "Đã tải file Evidence.";
  } catch (error) {
    fileError.value = error?.response?.data?.detail || error?.message || "Không thể tải file Evidence.";
  }
}

async function previewEvidence() {
  const finding = selectedItem.value?.finding;
  if (!finding?.finding_id || !finding.evidence_file_path) return;
  resetPreview();
  previewState.loading = true;
  try {
    const response = await downloadFindingEvidenceFile(finding.finding_id);
    const blob = response.data;
    const previewType = detectPreviewType(finding.evidence_file_name, finding.evidence_file_mime_type || blob.type);
    if (previewType === "image") {
      previewState.type = "image";
      previewState.imageUrl = URL.createObjectURL(blob);
      previewState.message = "";
    } else if (previewType === "text") {
      previewState.type = "text";
      previewState.text = await blob.text();
      previewState.message = "";
    } else {
      previewState.message = "Định dạng này hiện chưa có preview.";
    }
  } catch (error) {
    previewState.message = error?.response?.data?.detail || error?.message || "Không thể preview file Evidence.";
  } finally {
    previewState.loading = false;
  }
}

async function removeEvidence() {
  const finding = selectedItem.value?.finding;
  if (!finding?.finding_id || !finding.evidence_file_path) return;
  fileError.value = "";
  const updated = await deleteFindingEvidenceFile(finding.finding_id);
  updateFindingEvidenceFields(updated);
  fileMessage.value = "Đã xóa file Evidence.";
  resetPreview();
}

function parseDownloadFileName(response, fallbackName) {
  const disposition = response.headers["content-disposition"] || "";
  const matched = disposition.match(/filename="?([^"]+)"?/i);
  return matched?.[1] || fallbackName || "evidence-file";
}

function detectPreviewType(fileName, mimeType) {
  const lowerName = (fileName || "").toLowerCase();
  const lowerMime = (mimeType || "").toLowerCase();
  if (lowerMime.startsWith("image/")) return "image";
  if (lowerMime.startsWith("text/")) return "text";
  if ([".txt", ".log", ".json", ".csv", ".md", ".xml", ".html"].some((ext) => lowerName.endsWith(ext))) return "text";
  return "none";
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
  () => [filters.operationId, filters.year, filters.quarter, filters.month, filters.week],
  () => loadItems()
);

onMounted(async () => {
  await refreshAll();
});

onBeforeUnmount(() => {
  resetPreview();
});
</script>

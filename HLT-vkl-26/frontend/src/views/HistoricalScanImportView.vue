<template>
  <section class="page-header">
    <div>
      <p class="eyebrow">Báo cáo</p>
      <h2>Import Scan Cũ</h2>
      <p class="page-copy">
        Import file <code>services_vulns.csv</code> vào HLT để lưu lịch sử scan, phục vụ dashboard, báo cáo và so sánh theo kỳ.
      </p>
    </div>
    <button class="ghost-button" @click="loadTargets">Làm mới danh sách Target</button>
  </section>

  <section class="panel-grid">
    <article class="panel">
      <div class="panel-head">
        <h3>Metadata đợt import</h3>
        <span class="badge">{{ form.batch_code || "chưa nhập mã đợt" }}</span>
      </div>

      <form class="resource-form" @submit.prevent="runPreview">
        <label class="field-block">
          <span>Tên đợt quét / mã đợt quét</span>
          <input v-model="form.batch_code" required />
        </label>

        <div class="filter-grid">
          <label class="field-block">
            <span>Năm</span>
            <input v-model.number="form.year" type="number" min="2000" max="2100" required />
          </label>

          <label class="field-block">
            <span>Quý</span>
            <select v-model.number="form.quarter">
              <option :value="1">1</option>
              <option :value="2">2</option>
              <option :value="3">3</option>
              <option :value="4">4</option>
            </select>
          </label>

          <label class="field-block">
            <span>Tuần</span>
            <input v-model.number="form.week" type="number" min="1" max="53" required />
          </label>
        </div>

        <div class="filter-grid">
          <label class="field-block">
            <span>Ngày bắt đầu quét</span>
            <input v-model="form.scan_started_at" type="date" />
          </label>

          <label class="field-block">
            <span>Ngày kết thúc quét</span>
            <input v-model="form.scan_finished_at" type="date" />
          </label>
        </div>

        <label class="field-block">
          <span>Đường dẫn / thư mục gốc lưu kết quả scan</span>
          <input v-model="form.source_root_path" placeholder="D:\Pentest\2026\week18 hoặc /home/kali/26week18" />
        </label>

        <label class="field-block">
          <span>Ghi chú</span>
          <textarea v-model="form.note" rows="3" />
        </label>

        <label class="field-block">
          <span>File services_vulns.csv</span>
          <input type="file" accept=".csv" @change="handleFileChange" />
        </label>

        <div class="form-actions">
          <button class="primary-button" type="submit" :disabled="!canPreview">Preview trước khi import</button>
        </div>
      </form>

      <p v-if="message" class="inline-note">{{ message }}</p>
      <p v-if="errorMessage" class="inline-note text-danger">{{ errorMessage }}</p>
    </article>

    <article class="panel">
      <div class="panel-head">
        <h3>Chọn phạm vi Target</h3>
        <span class="badge">{{ selectedTargetIds.length }} đã chọn</span>
      </div>

      <div class="filter-grid">
        <label class="field-block">
          <span>Tìm Target</span>
          <input v-model="targetSearch" placeholder="Tên target, code hoặc IP..." />
        </label>
      </div>

      <div class="form-actions">
        <button class="table-button" type="button" @click="selectVisibleTargets">Chọn danh sách đang lọc</button>
        <button class="table-button" type="button" @click="clearTargetSelection">Bỏ chọn hết</button>
      </div>

      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>Chọn</th>
              <th class="sortable-header" @click="toggleTargetSort('id')">ID{{ targetSortLabel("id") }}</th>
              <th class="sortable-header" @click="toggleTargetSort('name')">Tên target{{ targetSortLabel("name") }}</th>
              <th class="sortable-header" @click="toggleTargetSort('ip_range')">Dải IP{{ targetSortLabel("ip_range") }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="target in paginatedTargets"
              :key="target.id"
              class="row-selectable"
              :class="{ 'row-selected': selectedTargetIds.includes(target.id) }"
              @click="toggleTargetSelection(target.id)"
            >
              <td><input :checked="selectedTargetIds.includes(target.id)" type="checkbox" @click.stop="toggleTargetSelection(target.id)" /></td>
              <td>{{ target.id }}</td>
              <td>{{ target.name }}</td>
              <td>{{ target.ip_range || "-" }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <PaginationBar
        :current-page="targetCurrentPage"
        :page-size="targetPageSize"
        :total-items="targetTotalItems"
        :total-pages="targetTotalPages"
        @update:page-size="targetPageSize = $event"
        @previous="goToPreviousTargetPage"
        @next="goToNextTargetPage"
      />
    </article>
  </section>

  <section v-if="preview" class="stat-grid compact-grid">
    <article class="mini-stat">
      <span>Tổng dòng</span>
      <strong>{{ preview.total_rows }}</strong>
    </article>
    <article class="mini-stat">
      <span>Số IP</span>
      <strong>{{ preview.detected_ips }}</strong>
    </article>
    <article class="mini-stat">
      <span>Port / Service</span>
      <strong>{{ preview.service_rows }}</strong>
    </article>
    <article class="mini-stat">
      <span>Finding / Vuln</span>
      <strong>{{ preview.finding_count }}</strong>
    </article>
    <article class="mini-stat">
      <span>Vuln match</span>
      <strong>{{ preview.matched_vulnerability_count }}</strong>
    </article>
    <article class="mini-stat">
      <span>Vuln chưa match</span>
      <strong>{{ preview.unmatched_vulnerability_count }}</strong>
    </article>
    <article class="mini-stat">
      <span>IP map được</span>
      <strong>{{ preview.mapped_ip_count }}</strong>
    </article>
    <article class="mini-stat">
      <span>IP chưa map</span>
      <strong>{{ preview.unmapped_ip_count }}</strong>
    </article>
  </section>

  <section v-if="preview" class="panel-grid">
    <article class="panel">
      <div class="panel-head">
        <h3>Preview mapping IP</h3>
        <span class="badge">{{ preview.mapping_items.length }} IP</span>
      </div>

      <p v-if="preview.unmatched_vulnerability_codes.length" class="inline-note text-danger">
        Vuln code chưa có trong hệ thống: {{ preview.unmatched_vulnerability_codes.join(", ") }}
      </p>
      <p v-for="warning in preview.warning_messages" :key="warning" class="inline-note text-danger">{{ warning }}</p>

      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>IP</th>
              <th>Trạng thái</th>
              <th>Target khớp</th>
              <th>Chọn target khi commit</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in paginatedMappings" :key="item.ip">
              <td>{{ item.ip }}</td>
              <td>{{ item.status }}</td>
              <td>{{ candidateLabel(item) }}</td>
              <td>
                <select v-model="manualTargetMappings[item.ip]">
                  <option value="">{{ item.status === "auto" ? "Giữ tự động" : "Cần chọn thủ công" }}</option>
                  <option value="__UNMAPPED__">Đánh dấu unmapped</option>
                  <option v-for="target in mappingOptions(item)" :key="target.id" :value="String(target.id)">
                    {{ target.name }} (ID {{ target.id }})
                  </option>
                </select>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <PaginationBar
        :current-page="mappingCurrentPage"
        :page-size="mappingPageSize"
        :total-items="mappingTotalItems"
        :total-pages="mappingTotalPages"
        @update:page-size="mappingPageSize = $event"
        @previous="goToPreviousMappingPage"
        @next="goToNextMappingPage"
      />

      <div class="form-actions">
        <button class="primary-button" type="button" :disabled="!canCommit" @click="commitImport">
          Xác nhận import vào database
        </button>
      </div>

      <p v-if="commitMessage" class="inline-note">{{ commitMessage }}</p>
    </article>
  </section>
</template>

<script setup>
import { computed, reactive, ref } from "vue";
import { commitHistoricalServicesVulnsImport, getTargetsEnriched, previewHistoricalServicesVulnsImport } from "../api/client";
import PaginationBar from "../components/PaginationBar.vue";
import { usePagination } from "../composables/usePagination";
import { nextSortState, sortIndicator, sortRows } from "../utils/tableSort";

const targets = ref([]);
const importFile = ref(null);
const preview = ref(null);
const message = ref("");
const errorMessage = ref("");
const commitMessage = ref("");
const targetSearch = ref("");
const selectedTargetIds = ref([]);
const manualTargetMappings = reactive({});
const targetSortState = ref({ key: "id", direction: "desc" });

const form = reactive({
  batch_code: "",
  year: new Date().getFullYear(),
  quarter: 1,
  week: 1,
  scan_started_at: "",
  scan_finished_at: "",
  note: "",
  source_root_path: "",
});

const filteredTargets = computed(() => {
  const keyword = targetSearch.value.trim().toLowerCase();
  const baseList = !keyword
    ? targets.value
    : targets.value.filter((target) => {
        const haystack = `${target.code || ""} ${target.name || ""} ${target.ip_range || ""}`.toLowerCase();
        return haystack.includes(keyword);
      });
  return sortRows(baseList, targetSortState.value);
});

const {
  currentPage: targetCurrentPage,
  pageSize: targetPageSize,
  paginatedItems: paginatedTargets,
  totalItems: targetTotalItems,
  totalPages: targetTotalPages,
  goToPreviousPage: goToPreviousTargetPage,
  goToNextPage: goToNextTargetPage,
} = usePagination(filteredTargets);

const previewMappings = computed(() => preview.value?.mapping_items || []);
const {
  currentPage: mappingCurrentPage,
  pageSize: mappingPageSize,
  paginatedItems: paginatedMappings,
  totalItems: mappingTotalItems,
  totalPages: mappingTotalPages,
  goToPreviousPage: goToPreviousMappingPage,
  goToNextPage: goToNextMappingPage,
} = usePagination(previewMappings);

const canPreview = computed(() => Boolean(importFile.value && form.batch_code.trim() && selectedTargetIds.value.length));
const canCommit = computed(() => Boolean(preview.value) && preview.value.unmatched_vulnerability_count === 0);

function toggleTargetSort(key) {
  targetSortState.value = nextSortState(targetSortState.value, key);
}

function targetSortLabel(key) {
  return sortIndicator(targetSortState.value, key);
}

function toggleTargetSelection(targetId) {
  if (selectedTargetIds.value.includes(targetId)) {
    selectedTargetIds.value = selectedTargetIds.value.filter((item) => item !== targetId);
  } else {
    selectedTargetIds.value = [...selectedTargetIds.value, targetId];
  }
}

function buildManualMappingPayload() {
  const payload = {};
  for (const item of previewMappings.value) {
    const selectedValue = manualTargetMappings[item.ip];
    if (selectedValue === undefined || selectedValue === null || selectedValue === "") continue;
    payload[item.ip] = selectedValue;
  }
  return payload;
}

function candidateLabel(item) {
  if (!item.matched_targets.length) return "-";
  return [...item.matched_targets]
    .sort((left, right) => left.id - right.id)
    .map((target) => `${target.name} (ID ${target.id})`)
    .join(", ");
}

function mappingOptions(item) {
  return [...item.matched_targets].sort((left, right) => left.id - right.id);
}

function handleFileChange(event) {
  importFile.value = event.target.files?.[0] || null;
}

function selectVisibleTargets() {
  selectedTargetIds.value = [...new Set([...selectedTargetIds.value, ...filteredTargets.value.map((item) => item.id)])];
}

function clearTargetSelection() {
  selectedTargetIds.value = [];
}

function seedManualMappingsFromPreview() {
  Object.keys(manualTargetMappings).forEach((key) => delete manualTargetMappings[key]);
  for (const item of previewMappings.value) {
    if (item.status === "unmapped") {
      manualTargetMappings[item.ip] = "__UNMAPPED__";
    } else {
      manualTargetMappings[item.ip] = "";
    }
  }
}

async function loadTargets() {
  targets.value = await getTargetsEnriched();
}

async function runPreview() {
  errorMessage.value = "";
  commitMessage.value = "";
  message.value = "";
  try {
    preview.value = await previewHistoricalServicesVulnsImport({
      file: importFile.value,
      batch_code: form.batch_code,
      selected_target_ids: selectedTargetIds.value,
      manual_target_mapping: buildManualMappingPayload(),
    });
    seedManualMappingsFromPreview();
    message.value = "Đã tạo preview. Rà lại mapping IP và tình trạng match Vulnerability trước khi commit.";
  } catch (error) {
    preview.value = null;
    errorMessage.value = error?.response?.data?.detail || error?.message || "Không thể preview file import.";
  }
}

async function commitImport() {
  errorMessage.value = "";
  commitMessage.value = "";
  try {
    const result = await commitHistoricalServicesVulnsImport({
      file: importFile.value,
      batch_code: form.batch_code,
      year: form.year,
      quarter: form.quarter,
      week: form.week,
      scan_started_at: form.scan_started_at || null,
      scan_finished_at: form.scan_finished_at || null,
      note: form.note || null,
      source_root_path: form.source_root_path || null,
      selected_target_ids: selectedTargetIds.value,
      manual_target_mapping: buildManualMappingPayload(),
    });
    commitMessage.value = `Đã import batch #${result.batch.id}: ${result.created_scan_results} scan result, ${result.created_findings} finding.`;
  } catch (error) {
    errorMessage.value = error?.response?.data?.detail || error?.message || "Không thể commit import.";
  }
}

loadTargets();
</script>

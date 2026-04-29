<template>
  <section class="page-header">
    <div>
      <p class="eyebrow">Dashboard phân tích</p>
      <h2>Dashboard lịch sử scan</h2>
      <p class="page-copy">
        Theo dõi số liệu scan đã import theo tuần, tháng, quý, năm; so sánh mục tiêu, nhóm trọng điểm và xu hướng vuln theo quý.
      </p>
    </div>
    <button class="ghost-button" @click="loadDashboard">Làm mới dashboard</button>
  </section>

  <section class="filter-strip">
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
        <option v-for="quarter in filterOptions.quarters" :key="quarter" :value="String(quarter)">Quý {{ quarter }}</option>
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
        <option v-for="week in filterOptions.weeks" :key="week" :value="String(week)">Tuần {{ week }}</option>
      </select>
    </label>
  </section>

  <section class="panel-grid panel-grid-loose">
    <article class="panel panel-span-full">
      <div class="panel-head">
        <h3>Tổng quan theo thời gian và Top 5 vuln/CVE</h3>
        <span class="badge">lọc linh hoạt</span>
      </div>

      <div class="panel-grid panel-grid-nested">
        <article class="panel panel-inner">
          <div class="panel-head">
            <h3>Thống kê tổng quan theo thời gian</h3>
            <span class="badge">overview</span>
          </div>

          <div class="stat-grid compact-grid">
            <StatCard label="Target được dò quét" :value="overview.scanned_targets" />
            <StatCard label="IP phát hiện" :value="overview.detected_ips" />
            <StatCard label="Cổng mở" :value="overview.open_ports" />
            <StatCard label="Vuln phát hiện" :value="overview.detected_vulns" />
            <StatCard label="Target có nguy cơ" :value="overview.targets_at_risk" />
            <StatCard label="IP có nguy cơ" :value="overview.ips_at_risk" />
          </div>
        </article>

        <article class="panel panel-inner">
          <div class="panel-head">
            <h3>Top 5 vuln/CVE xuất hiện nhiều nhất</h3>
            <span class="badge">theo bộ lọc thời gian</span>
          </div>

          <TopListChart :items="topVulnerabilities" />
        </article>
      </div>
    </article>

    <article class="panel">
      <div class="panel-head">
        <h3>Thống kê tổng</h3>
        <span class="badge">toàn thời gian</span>
      </div>

      <div class="stat-grid compact-grid">
        <StatCard label="Target được dò quét" :value="totalSummary.scanned_targets" />
        <StatCard label="IP phát hiện" :value="totalSummary.detected_ips" />
        <StatCard label="Cổng mở" :value="totalSummary.open_ports" />
        <StatCard label="Vuln phát hiện" :value="totalSummary.detected_vulns" />
        <StatCard label="Target có nguy cơ" :value="totalSummary.targets_at_risk" />
        <StatCard label="IP có nguy cơ" :value="totalSummary.ips_at_risk" />
      </div>
    </article>
  </section>

  <section class="panel-grid panel-grid-loose">
    <article class="panel">
      <div class="panel-head">
        <h3>So sánh vuln của các mục tiêu theo quý</h3>
        <span class="badge">chọn tối đa 5 target</span>
      </div>

      <div class="filter-grid">
        <label class="field-block">
          <span>Năm</span>
          <select v-model="targetChartYear">
            <option value="">Chọn năm</option>
            <option v-for="year in filterOptions.years" :key="year" :value="String(year)">{{ year }}</option>
          </select>
        </label>
      </div>

      <div class="selection-toolbar">
        <MultiSelectDialog
          v-model="selectedTargetIds"
          title="Chọn mục tiêu để so sánh"
          :options="targetPickerOptions"
          button-label="Chọn target"
          search-placeholder="Tìm theo tên target hoặc ID..."
        />

        <div class="selected-chip-list">
          <span v-for="item in selectedTargetChips" :key="item.id" class="selected-chip">
            {{ item.name }}
          </span>
        </div>
      </div>

      <GroupedBarChart
        :quarters="targetQuarterly.quarters"
        :series="targetQuarterlySeries"
      />
    </article>

  </section>

  <section class="panel-grid panel-grid-loose">
    <article class="panel panel-span-full">
      <div class="panel-head">
        <h3>Nhóm mục tiêu trọng điểm theo quý</h3>
        <span class="badge">A đến I và Khác</span>
      </div>

      <div class="filter-grid">
        <label class="field-block">
          <span>Năm</span>
          <select v-model="groupChartYear">
            <option value="">Chọn năm</option>
            <option v-for="year in filterOptions.years" :key="year" :value="String(year)">{{ year }}</option>
          </select>
        </label>
      </div>

      <div class="selection-toolbar">
        <MultiSelectDialog
          v-model="selectedCoreGroups"
          title="Chọn nhóm ĐV Cấp 1"
          :options="coreGroupPickerOptions"
          button-label="Chọn nhóm trọng điểm"
          search-placeholder="Tìm theo mã nhóm..."
        />

        <div class="selected-chip-list">
          <span v-for="group in selectedCoreGroups" :key="group" class="selected-chip">
            {{ group }}
          </span>
        </div>
      </div>

      <div class="panel-grid panel-grid-nested-single">
        <article class="panel panel-inner panel-inner-wide">
          <div class="panel-head">
            <h3>So sánh số lượng vuln</h3>
            <span class="badge">count</span>
          </div>

          <GroupedBarChart
            :quarters="coreGroupCountChart.quarters"
            :series="coreGroupCountSeries"
          />
        </article>

        <article class="panel panel-inner panel-inner-wide">
          <div class="panel-head">
            <h3>Tỉ lệ tồn tại nguy cơ</h3>
            <span class="badge">%</span>
          </div>

          <GroupedBarChart
            :quarters="coreGroupRiskChart.quarters"
            :series="coreGroupRiskSeries"
            :formatter="percentFormatter"
          />
        </article>
      </div>
    </article>
  </section>

  <section class="panel-grid panel-grid-loose">
    <article class="panel">
      <div class="panel-head">
        <h3>Xu hướng vuln theo quý</h3>
        <span class="badge">toàn bộ lịch sử</span>
      </div>

      <TrendLineChart :points="trend.points" />
    </article>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from "vue";
import {
  getHistoricalCoreGroupOptions,
  getHistoricalCoreGroupQuarterlyChart,
  getHistoricalDashboardFilterOptions,
  getHistoricalDashboardOverview,
  getHistoricalDashboardTargetOptions,
  getHistoricalDashboardTotalSummary,
  getHistoricalTargetQuarterlyChart,
  getHistoricalTopVulnerabilities,
  getHistoricalVulnerabilityTrend,
} from "../api/client";
import GroupedBarChart from "../components/GroupedBarChart.vue";
import MultiSelectDialog from "../components/MultiSelectDialog.vue";
import StatCard from "../components/StatCard.vue";
import TopListChart from "../components/TopListChart.vue";
import TrendLineChart from "../components/TrendLineChart.vue";

const filters = reactive({
  year: "",
  quarter: "",
  month: "",
  week: "",
});

const overview = reactive({
  scanned_targets: 0,
  detected_ips: 0,
  open_ports: 0,
  detected_vulns: 0,
  targets_at_risk: 0,
  ips_at_risk: 0,
});

const totalSummary = reactive({
  scanned_targets: 0,
  detected_ips: 0,
  open_ports: 0,
  detected_vulns: 0,
  targets_at_risk: 0,
  ips_at_risk: 0,
});

const filterOptions = reactive({
  years: [],
  quarters: [],
  months: [],
  weeks: [],
});

const targetOptions = ref([]);
const coreGroupOptions = ref([]);
const selectedTargetIds = ref([]);
const selectedCoreGroups = ref([]);
const targetChartYear = ref("");
const groupChartYear = ref("");
const targetQuarterly = reactive({ quarters: [], series: [] });
const topVulnerabilities = ref([]);
const coreGroupCountChart = reactive({ quarters: [], series: [] });
const coreGroupRiskChart = reactive({ quarters: [], series: [] });
const trend = reactive({ points: [] });

const targetPalette = ["#b32020", "#0f7a2d", "#1666b0", "#8a4fff", "#c57f0a"];
const coreGroupPalette = {
  A: "#b32020",
  B: "#0f7a2d",
  C: "#1666b0",
  D: "#8a4fff",
  E: "#c57f0a",
  F: "#7b2cbf",
  G: "#14532d",
  H: "#0f766e",
  I: "#9f1239",
  "Khác": "#6b7280",
};

const targetQuarterlySeries = computed(() =>
  (targetQuarterly.series || []).map((item, index) => ({
    key: item.target_id,
    label: item.target_name,
    quarters: item.quarters,
    color: targetPalette[index % targetPalette.length],
  }))
);

const targetPickerOptions = computed(() =>
  [...targetOptions.value].sort((left, right) => left.id - right.id).map((target) => ({
    value: target.id,
    label: target.name,
    description: `ID ${target.id}${target.ip_range ? ` • ${target.ip_range}` : ""}`,
  }))
);

const selectedTargetChips = computed(() => {
  const targetMap = new Map(targetOptions.value.map((item) => [item.id, item]));
  return selectedTargetIds.value
    .map((id) => targetMap.get(id))
    .filter(Boolean);
});

const coreGroupPickerOptions = computed(() =>
  [...coreGroupOptions.value].map((group) => ({
    value: group,
    label: group,
    description: group === "Khác" ? "Các giá trị ngoài A đến I" : `Nhóm ĐV Cấp 1 ${group}`,
  }))
);

const coreGroupCountSeries = computed(() =>
  (coreGroupCountChart.series || []).map((item) => ({
    key: item.group,
    label: item.group,
    quarters: item.quarters,
    color: coreGroupPalette[item.group] || "#6b7280",
  }))
);

const coreGroupRiskSeries = computed(() =>
  (coreGroupRiskChart.series || []).map((item) => ({
    key: item.group,
    label: item.group,
    quarters: item.quarters,
    color: coreGroupPalette[item.group] || "#6b7280",
  }))
);

function currentFilterParams() {
  return {
    year: filters.year ? Number(filters.year) : undefined,
    quarter: filters.quarter ? Number(filters.quarter) : undefined,
    month: filters.month ? Number(filters.month) : undefined,
    week: filters.week ? Number(filters.week) : undefined,
  };
}

function percentFormatter(value) {
  return `${Number(value || 0).toFixed(1)}%`;
}

async function loadFilterOptions() {
  const data = await getHistoricalDashboardFilterOptions(currentFilterParams());
  filterOptions.years = data.years || [];
  filterOptions.quarters = data.quarters || [];
  filterOptions.months = data.months || [];
  filterOptions.weeks = data.weeks || [];
}

async function loadOverviewCards() {
  Object.assign(overview, await getHistoricalDashboardOverview(currentFilterParams()));
  Object.assign(totalSummary, await getHistoricalDashboardTotalSummary());
}

async function loadTopVulnerabilities() {
  topVulnerabilities.value = await getHistoricalTopVulnerabilities(currentFilterParams());
}

async function loadTargetQuarterlyChart() {
  if (!targetChartYear.value || !selectedTargetIds.value.length) {
    targetQuarterly.quarters = [];
    targetQuarterly.series = [];
    return;
  }
  const data = await getHistoricalTargetQuarterlyChart(Number(targetChartYear.value), [...selectedTargetIds.value]);
  targetQuarterly.quarters = data.quarters || [];
  targetQuarterly.series = data.series || [];
}

async function loadCoreGroupCharts() {
  if (!groupChartYear.value || !selectedCoreGroups.value.length) {
    coreGroupCountChart.quarters = [];
    coreGroupCountChart.series = [];
    coreGroupRiskChart.quarters = [];
    coreGroupRiskChart.series = [];
    return;
  }

  const [countData, riskData] = await Promise.all([
    getHistoricalCoreGroupQuarterlyChart(Number(groupChartYear.value), [...selectedCoreGroups.value], "count"),
    getHistoricalCoreGroupQuarterlyChart(Number(groupChartYear.value), [...selectedCoreGroups.value], "risk_rate"),
  ]);

  coreGroupCountChart.quarters = countData.quarters || [];
  coreGroupCountChart.series = countData.series || [];
  coreGroupRiskChart.quarters = riskData.quarters || [];
  coreGroupRiskChart.series = riskData.series || [];
}

async function loadTrend() {
  Object.assign(trend, await getHistoricalVulnerabilityTrend());
}

async function loadStaticOptions() {
  const [targets, groups] = await Promise.all([
    getHistoricalDashboardTargetOptions(),
    getHistoricalCoreGroupOptions(),
  ]);
  targetOptions.value = targets || [];
  coreGroupOptions.value = groups || [];
  if (!selectedCoreGroups.value.length && coreGroupOptions.value.length) {
    selectedCoreGroups.value = [coreGroupOptions.value[0]];
  }
}

async function loadDashboard() {
  await Promise.all([loadFilterOptions(), loadOverviewCards(), loadTopVulnerabilities(), loadTrend()]);

  if (!targetChartYear.value && filterOptions.years.length) {
    targetChartYear.value = String(filterOptions.years[filterOptions.years.length - 1]);
  }
  if (!groupChartYear.value && filterOptions.years.length) {
    groupChartYear.value = String(filterOptions.years[filterOptions.years.length - 1]);
  }

  await Promise.all([loadTargetQuarterlyChart(), loadCoreGroupCharts()]);
}

watch(
  () => [filters.year, filters.quarter, filters.month, filters.week],
  async () => {
    await loadFilterOptions();
    await Promise.all([loadOverviewCards(), loadTopVulnerabilities()]);
  }
);

watch(
  () => [targetChartYear.value, JSON.stringify(selectedTargetIds.value)],
  async () => {
    await loadTargetQuarterlyChart();
  }
);

watch(
  () => [groupChartYear.value, JSON.stringify(selectedCoreGroups.value)],
  async () => {
    await loadCoreGroupCharts();
  }
);

onMounted(async () => {
  await loadStaticOptions();
  await loadDashboard();
});
</script>

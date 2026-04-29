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

  <section class="panel-grid">
    <article class="panel">
      <div class="panel-head">
        <h3>Thống kê tổng quan theo thời gian</h3>
        <span class="badge">lọc linh hoạt</span>
      </div>

      <div class="filter-grid">
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

  <section class="panel-grid">
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

      <div class="option-chip-grid">
        <button
          v-for="target in targetOptions"
          :key="target.id"
          type="button"
          class="option-chip"
          :class="{ active: selectedTargetIds.includes(target.id) }"
          @click="toggleTargetSelection(target.id)"
        >
          <strong>{{ target.name }}</strong>
          <small>ID {{ target.id }}</small>
        </button>
      </div>

      <GroupedBarChart
        :quarters="targetQuarterly.quarters"
        :series="targetQuarterlySeries"
      />
    </article>

    <article class="panel">
      <div class="panel-head">
        <h3>Top 5 vuln/CVE xuất hiện nhiều nhất</h3>
        <span class="badge">theo bộ lọc thời gian</span>
      </div>

      <TopListChart :items="topVulnerabilities" />
    </article>
  </section>

  <section class="panel-grid">
    <article class="panel">
      <div class="panel-head">
        <h3>So sánh số lượng vuln của nhóm mục tiêu trọng điểm</h3>
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

      <div class="option-chip-grid">
        <button
          v-for="group in coreGroupOptions"
          :key="group"
          type="button"
          class="option-chip"
          :class="{ active: selectedCoreGroups.includes(group) }"
          @click="toggleCoreGroup(group)"
        >
          <strong>{{ group }}</strong>
        </button>
      </div>

      <GroupedBarChart
        :quarters="coreGroupCountChart.quarters"
        :series="coreGroupCountSeries"
      />
    </article>

    <article class="panel">
      <div class="panel-head">
        <h3>Tỉ lệ tồn tại nguy cơ của nhóm mục tiêu trọng điểm</h3>
        <span class="badge">%</span>
      </div>

      <GroupedBarChart
        :quarters="coreGroupRiskChart.quarters"
        :series="coreGroupRiskSeries"
        :formatter="percentFormatter"
      />
    </article>
  </section>

  <section class="panel-grid">
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

const targetOptions = reactive([]);
const coreGroupOptions = reactive([]);
const selectedTargetIds = reactive([]);
const selectedCoreGroups = reactive([]);
const targetChartYear = ref("");
const groupChartYear = ref("");
const targetQuarterly = reactive({ quarters: [], series: [] });
const topVulnerabilities = reactive([]);
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
  const data = await getHistoricalTopVulnerabilities(currentFilterParams());
  topVulnerabilities.splice(0, topVulnerabilities.length, ...(data || []));
}

async function loadTargetQuarterlyChart() {
  if (!targetChartYear.value || !selectedTargetIds.length) {
    targetQuarterly.quarters = [];
    targetQuarterly.series = [];
    return;
  }
  const data = await getHistoricalTargetQuarterlyChart(Number(targetChartYear.value), [...selectedTargetIds]);
  targetQuarterly.quarters = data.quarters || [];
  targetQuarterly.series = data.series || [];
}

async function loadCoreGroupCharts() {
  if (!groupChartYear.value || !selectedCoreGroups.length) {
    coreGroupCountChart.quarters = [];
    coreGroupCountChart.series = [];
    coreGroupRiskChart.quarters = [];
    coreGroupRiskChart.series = [];
    return;
  }
  const [countData, riskData] = await Promise.all([
    getHistoricalCoreGroupQuarterlyChart(Number(groupChartYear.value), [...selectedCoreGroups], "count"),
    getHistoricalCoreGroupQuarterlyChart(Number(groupChartYear.value), [...selectedCoreGroups], "risk_rate"),
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
  targetOptions.splice(0, targetOptions.length, ...(targets || []));
  coreGroupOptions.splice(0, coreGroupOptions.length, ...(groups || []));
  if (!selectedCoreGroups.length && coreGroupOptions.length) {
    selectedCoreGroups.push(coreGroupOptions[0]);
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

function toggleTargetSelection(targetId) {
  const index = selectedTargetIds.indexOf(targetId);
  if (index >= 0) {
    selectedTargetIds.splice(index, 1);
    return;
  }
  if (selectedTargetIds.length >= 5) return;
  selectedTargetIds.push(targetId);
}

function toggleCoreGroup(group) {
  const index = selectedCoreGroups.indexOf(group);
  if (index >= 0) {
    selectedCoreGroups.splice(index, 1);
    return;
  }
  if (selectedCoreGroups.length >= 5) return;
  selectedCoreGroups.push(group);
}

watch(
  () => [filters.year, filters.quarter, filters.month, filters.week],
  async () => {
    await loadFilterOptions();
    await Promise.all([loadOverviewCards(), loadTopVulnerabilities()]);
  }
);

watch(
  () => [targetChartYear.value, [...selectedTargetIds]],
  async () => {
    await loadTargetQuarterlyChart();
  },
  { deep: true }
);

watch(
  () => [groupChartYear.value, [...selectedCoreGroups]],
  async () => {
    await loadCoreGroupCharts();
  },
  { deep: true }
);

onMounted(async () => {
  await loadStaticOptions();
  await loadDashboard();
});
</script>

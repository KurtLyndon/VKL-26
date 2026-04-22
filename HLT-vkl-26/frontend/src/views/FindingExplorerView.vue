<template>
  <section class="page-header">
    <div>
      <p class="eyebrow">Finding explorer</p>
      <h2>Finding Filters</h2>
      <p class="page-copy">Lọc finding theo severity, status, service và từ khóa để xem kết quả nhanh hơn.</p>
    </div>
    <button class="ghost-button" @click="loadData">Refresh</button>
  </section>

  <section class="stat-grid compact-grid">
    <article class="mini-stat">
      <span>Tổng finding</span>
      <strong>{{ findings.length }}</strong>
    </article>
    <article class="mini-stat">
      <span>Critical / High</span>
      <strong>{{ highRiskCount }}</strong>
    </article>
    <article class="mini-stat">
      <span>Open</span>
      <strong>{{ openCount }}</strong>
    </article>
    <article class="mini-stat">
      <span>Dịch vụ phổ biến</span>
      <strong>{{ topService }}</strong>
    </article>
  </section>

  <section class="panel-grid">
    <article class="panel">
      <div class="panel-head">
        <h3>Bộ lọc</h3>
        <span class="badge">{{ filteredFindings.length }} kết quả</span>
      </div>

      <div class="filter-grid">
        <label class="field-block">
          <span>severity</span>
          <select v-model="filters.severity">
            <option value="">Tất cả</option>
            <option value="critical">critical</option>
            <option value="high">high</option>
            <option value="medium">medium</option>
            <option value="low">low</option>
            <option value="info">info</option>
          </select>
        </label>

        <label class="field-block">
          <span>status</span>
          <select v-model="filters.status">
            <option value="">Tất cả</option>
            <option value="open">open</option>
            <option value="closed">closed</option>
          </select>
        </label>

        <label class="field-block">
          <span>service_name</span>
          <input v-model="filters.serviceName" type="text" placeholder="http, ssh..." />
        </label>

        <label class="field-block">
          <span>search</span>
          <input v-model="filters.search" type="text" placeholder="finding code hoặc title" />
        </label>
      </div>
    </article>
  </section>

  <section class="panel-grid">
    <article class="panel">
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Mã finding</th>
              <th>Tiêu đề</th>
              <th>Severity</th>
              <th>Service</th>
              <th>Port</th>
              <th>Trạng thái</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in filteredFindings" :key="item.id">
              <td>{{ item.id }}</td>
              <td>{{ item.finding_code }}</td>
              <td>{{ item.title }}</td>
              <td><StatusPill :value="item.severity" /></td>
              <td>{{ item.service_name || "-" }}</td>
              <td>{{ item.port || "-" }}</td>
              <td><StatusPill :value="item.status" /></td>
            </tr>
          </tbody>
        </table>
      </div>
    </article>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { getList } from "../api/client";
import StatusPill from "../components/StatusPill.vue";

const findings = ref([]);
const filters = reactive({
  severity: "",
  status: "",
  serviceName: "",
  search: "",
});

const filteredFindings = computed(() =>
  findings.value.filter((item) => {
    if (filters.severity && item.severity !== filters.severity) return false;
    if (filters.status && item.status !== filters.status) return false;
    if (filters.serviceName && !(item.service_name || "").toLowerCase().includes(filters.serviceName.toLowerCase())) {
      return false;
    }
    if (filters.search) {
      const haystack = `${item.finding_code} ${item.title}`.toLowerCase();
      if (!haystack.includes(filters.search.toLowerCase())) return false;
    }
    return true;
  })
);

const highRiskCount = computed(
  () => findings.value.filter((item) => ["critical", "high"].includes((item.severity || "").toLowerCase())).length
);

const openCount = computed(() => findings.value.filter((item) => item.status === "open").length);

const topService = computed(() => {
  const counts = new Map();
  for (const item of findings.value) {
    const key = item.service_name || "-";
    counts.set(key, (counts.get(key) || 0) + 1);
  }
  const top = [...counts.entries()].sort((left, right) => right[1] - left[1])[0];
  return top ? top[0] : "-";
});

async function loadData() {
  findings.value = await getList("scan-findings");
}

onMounted(loadData);
</script>

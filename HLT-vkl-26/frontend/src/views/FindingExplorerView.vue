<template>
  <section class="page-header">
    <div>
      <p class="eyebrow">Finding explorer</p>
      <h2>Finding Filters</h2>
      <p class="page-copy">Lọc finding theo severity, status, service và text tìm kiếm để xem kết quả nhanh hơn.</p>
    </div>
    <button class="ghost-button" @click="loadData">Refresh</button>
  </section>

  <section class="panel-grid">
    <article class="panel">
      <div class="panel-head">
        <h3>Filters</h3>
        <span class="badge">{{ filteredFindings.length }} matches</span>
      </div>

      <div class="filter-grid">
        <label class="field-block">
          <span>severity</span>
          <select v-model="filters.severity">
            <option value="">All</option>
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
            <option value="">All</option>
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
          <input v-model="filters.search" type="text" placeholder="finding code or title" />
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
              <th>finding_code</th>
              <th>title</th>
              <th>severity</th>
              <th>service</th>
              <th>port</th>
              <th>status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in filteredFindings" :key="item.id">
              <td>{{ item.id }}</td>
              <td>{{ item.finding_code }}</td>
              <td>{{ item.title }}</td>
              <td>{{ item.severity }}</td>
              <td>{{ item.service_name || "-" }}</td>
              <td>{{ item.port || "-" }}</td>
              <td>{{ item.status }}</td>
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

async function loadData() {
  findings.value = await getList("scan-findings");
}

onMounted(loadData);
</script>

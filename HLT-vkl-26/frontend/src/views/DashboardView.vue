<template>
  <section class="page-header">
    <div>
      <p class="eyebrow">System overview</p>
      <h2>Dashboard</h2>
      <p class="page-copy">
        Theo doi nhanh so luong thanh phan trong he thong dieu phoi scan, ket qua va bao cao.
      </p>
    </div>
  </section>

  <section class="stat-grid">
    <StatCard label="Agents" :value="summary.agents" />
    <StatCard label="Tasks" :value="summary.tasks" />
    <StatCard label="Operations" :value="summary.operations" />
    <StatCard label="Targets" :value="summary.targets" />
    <StatCard label="Vulnerabilities" :value="summary.vulnerabilities" />
    <StatCard label="Scan Results" :value="summary.scan_results" />
    <StatCard label="Open Findings" :value="summary.open_findings" />
    <StatCard label="Report Templates" :value="summary.report_templates" />
  </section>

  <section class="panel-grid">
    <article class="panel">
      <h3>Phan he da co</h3>
      <ul class="feature-list">
        <li>Quan ly agent, task, operation va lich chay</li>
        <li>Quan ly target, thuoc tinh dong va grouping</li>
        <li>Quan ly CVE, script PoC va ket qua scan chuan hoa</li>
        <li>Template bao cao va dashboard summary</li>
      </ul>
    </article>

    <article class="panel">
      <h3>Huong phat trien tiep</h3>
      <ul class="feature-list">
        <li>Parser rieng cho nmap, nuclei, acunetix</li>
        <li>Realtime heartbeat agent va theo doi execution</li>
        <li>Import/export Excel, CSV, PDF, JSON</li>
        <li>Drag and drop operation task + scheduler runner</li>
      </ul>
    </article>
  </section>
</template>

<script setup>
import { onMounted, reactive } from "vue";
import { getDashboardSummary } from "../api/client";
import StatCard from "../components/StatCard.vue";

const summary = reactive({
  agents: 0,
  tasks: 0,
  operations: 0,
  targets: 0,
  vulnerabilities: 0,
  scan_results: 0,
  open_findings: 0,
  report_templates: 0,
});

onMounted(async () => {
  Object.assign(summary, await getDashboardSummary());
});
</script>

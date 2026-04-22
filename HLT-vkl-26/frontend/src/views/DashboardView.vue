<template>
  <section class="page-header">
    <div>
      <p class="eyebrow">System overview</p>
      <h2>Dashboard</h2>
      <p class="page-copy">
        Theo dõi nhanh sức khỏe hệ thống mock runtime, số lượng tài nguyên và kết quả scan để demo nội bộ mượt hơn.
      </p>
    </div>
  </section>

  <section class="stat-grid">
    <StatCard label="Agents" :value="summary.agents" />
    <StatCard label="Tasks" :value="summary.tasks" />
    <StatCard label="Operations" :value="summary.operations" />
    <StatCard label="Operation Executions" :value="summary.operation_executions" />
    <StatCard label="Task Executions" :value="summary.task_executions" />
    <StatCard label="Targets" :value="summary.targets" />
    <StatCard label="Vulnerabilities" :value="summary.vulnerabilities" />
    <StatCard label="Scan Results" :value="summary.scan_results" />
    <StatCard label="Open Findings" :value="summary.open_findings" />
    <StatCard label="Report Templates" :value="summary.report_templates" />
    <StatCard label="Generated Reports" :value="summary.generated_reports" />
  </section>

  <section class="panel-grid">
    <article class="panel panel-accent">
      <div class="panel-head">
        <h3>Tóm tắt runtime</h3>
        <span class="badge">mock mode ready</span>
      </div>

      <div class="insight-grid">
        <div class="insight-card">
          <span>Execution hoạt động</span>
          <strong>{{ executionHealthLabel }}</strong>
          <small>{{ summary.operation_executions }} execution, {{ summary.task_executions }} task execution</small>
        </div>
        <div class="insight-card">
          <span>Finding đang mở</span>
          <strong>{{ summary.open_findings }}</strong>
          <small>{{ summary.scan_results }} scan result đã được chuẩn hóa</small>
        </div>
        <div class="insight-card">
          <span>Mức sẵn sàng demo</span>
          <strong>{{ demoReadiness }}</strong>
          <small>Scheduler, worker, parser và UI đều đã có luồng mock</small>
        </div>
      </div>
    </article>

    <article class="panel">
      <div class="panel-head">
        <h3>Checklist demo</h3>
        <span class="badge">nội bộ</span>
      </div>
      <ul class="feature-list">
        <li>Chạy backend với `SCHEDULER_ENABLED=true` và `WORKER_ENABLED=true`</li>
        <li>Giữ `AGENT_DISPATCH_MODE=auto` để fallback mock nếu agent thật chưa sẵn sàng</li>
        <li>Dùng `Operation Control` để launch operation và xem task execution</li>
        <li>Dùng `Finding Explorer` để lọc finding theo severity, status và service</li>
      </ul>
    </article>
  </section>

  <section class="panel-grid">
    <article class="panel">
      <h3>Phân hệ đã có</h3>
      <ul class="feature-list">
        <li>Quản lý agent, task, operation và lịch chạy</li>
        <li>Quản lý target, thuộc tính động và grouping</li>
        <li>Quản lý CVE, script PoC và kết quả scan chuẩn hóa</li>
        <li>Execution flow, parser registry và template báo cáo</li>
      </ul>
    </article>

    <article class="panel">
      <h3>Hướng phát triển tiếp</h3>
      <ul class="feature-list">
        <li>Parser riêng cho nmap, nuclei, acunetix</li>
        <li>Realtime heartbeat agent, dispatch và theo dõi execution</li>
        <li>Import/export Excel, CSV, PDF, JSON</li>
        <li>Drag and drop operation task + scheduler runner</li>
      </ul>
    </article>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive } from "vue";
import { getDashboardSummary } from "../api/client";
import StatCard from "../components/StatCard.vue";

const summary = reactive({
  agents: 0,
  tasks: 0,
  operations: 0,
  operation_executions: 0,
  task_executions: 0,
  targets: 0,
  vulnerabilities: 0,
  scan_results: 0,
  open_findings: 0,
  report_templates: 0,
  generated_reports: 0,
});

const executionHealthLabel = computed(() => {
  if (summary.operation_executions === 0) return "Chưa có execution";
  if (summary.open_findings > 0) return "Có dữ liệu để demo";
  return "Đang sẵn sàng";
});

const demoReadiness = computed(() => {
  if (summary.tasks === 0 || summary.operations === 0) return "Cần seed dữ liệu";
  if (summary.scan_results === 0) return "Sẵn sàng chạy mock";
  return "Sẵn sàng demo";
});

onMounted(async () => {
  Object.assign(summary, await getDashboardSummary());
});
</script>

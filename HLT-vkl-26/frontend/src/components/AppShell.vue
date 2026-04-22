<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div>
        <p class="eyebrow">HLT internal security</p>
        <h1>Control Center</h1>
        <p class="sidebar-copy">
          Nền tảng khởi tạo cho điều phối task agent, lưu trữ kết quả scan, quản trị CVE và báo cáo.
        </p>
      </div>

      <nav class="nav-list">
        <RouterLink v-for="item in navigation" :key="item.to" :to="item.to" class="nav-link">
          <span>{{ item.label }}</span>
          <small>{{ item.caption }}</small>
        </RouterLink>
      </nav>
    </aside>

    <main class="main-panel">
      <slot />
    </main>
  </div>
</template>

<script setup>
const navigation = [
  { to: "/", label: "Dashboard", caption: "Tổng quan hệ thống" },
  { to: "/control", label: "Control", caption: "Launch và runtime execution" },
  { to: "/operation-designer", label: "Designer", caption: "Sắp xếp workflow task" },
  { to: "/execution-monitor", label: "Monitor", caption: "Bộ lọc execution" },
  { to: "/finding-explorer", label: "Explorer", caption: "Bộ lọc finding" },
  { to: "/result-exchange", label: "Exchange", caption: "Import export kết quả" },
  { to: "/agents", label: "Agents", caption: "Trạng thái và version" },
  { to: "/tasks", label: "Tasks", caption: "Script va schema" },
  { to: "/operations", label: "Operations", caption: "Workflow và lịch chạy" },
  { to: "/operation-executions", label: "Executions", caption: "Tiến trình operation và task" },
  { to: "/targets", label: "Targets", caption: "Tài sản và nhóm đối tượng" },
  { to: "/vulnerabilities", label: "CVE", caption: "Threat, proposal, PoC" },
  { to: "/scan-results", label: "Scan Results", caption: "Dữ liệu chuẩn hóa" },
  { to: "/scan-findings", label: "Findings", caption: "Lỗ hổng và bằng chứng" },
  { to: "/report-templates", label: "Reports", caption: "Mẫu và thống kê" },
  { to: "/generated-reports", label: "Generated", caption: "Báo cáo đã sinh ra" },
  { to: "/operation-result-history", label: "History", caption: "Lịch sử kết quả" },
];
</script>

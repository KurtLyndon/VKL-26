<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div>
        <p class="eyebrow">HLT internal security</p>
        <h1>Control Center</h1>
        <p class="sidebar-copy">
          Nen tang khoi tao cho dieu phoi task agent, luu tru ket qua scan, quan tri CVE va bao cao.
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
  { to: "/", label: "Dashboard", caption: "Tong quan he thong" },
  { to: "/control", label: "Control", caption: "Launch va runtime execution" },
  { to: "/operation-designer", label: "Designer", caption: "Sap xep workflow task" },
  { to: "/execution-monitor", label: "Monitor", caption: "Bo loc execution" },
  { to: "/finding-explorer", label: "Explorer", caption: "Bo loc finding" },
  { to: "/result-exchange", label: "Exchange", caption: "Import export ket qua" },
  { to: "/agents", label: "Agents", caption: "Trang thai va version" },
  { to: "/tasks", label: "Tasks", caption: "Script va schema" },
  { to: "/operations", label: "Operations", caption: "Workflow va lich chay" },
  { to: "/operation-executions", label: "Executions", caption: "Tien trinh operation va task" },
  { to: "/targets", label: "Targets", caption: "Tai san va nhom doi tuong" },
  { to: "/vulnerabilities", label: "CVE", caption: "Threat, proposal, PoC" },
  { to: "/scan-results", label: "Scan Results", caption: "Du lieu chuan hoa" },
  { to: "/scan-findings", label: "Findings", caption: "Loi hong va bang chung" },
  { to: "/report-templates", label: "Reports", caption: "Mau va thong ke" },
  { to: "/generated-reports", label: "Generated", caption: "Bao cao da sinh ra" },
  { to: "/operation-result-history", label: "History", caption: "Lich su ket qua" },
];
</script>

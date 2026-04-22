<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div>
        <p class="eyebrow">HLT internal security</p>
        <h1>Control Center</h1>
        <p class="sidebar-copy">
          Nền tảng khởi tạo cho điều phối task agent, lưu trữ kết quả scan, quản trị CVE, báo cáo và phân quyền nhóm tài khoản.
        </p>
      </div>

      <nav class="nav-section-list">
        <section v-for="section in visibleSections" :key="section.label" class="nav-section">
          <button class="nav-section-toggle" type="button" @click="toggleSection(section.label)">
            <span>{{ section.label }}</span>
            <small>{{ expandedSection === section.label ? "−" : "+" }}</small>
          </button>

          <div v-if="expandedSection === section.label" class="nav-list">
            <RouterLink
              v-for="item in section.items"
              :key="item.to"
              :to="item.to"
              class="nav-link"
              @click="emitNavigate"
            >
              <span>{{ item.label }}</span>
              <small>{{ item.caption }}</small>
            </RouterLink>
          </div>
        </section>
      </nav>

      <div class="user-card">
        <strong>{{ auth.state.user?.full_name || auth.state.user?.username }}</strong>
        <small>{{ auth.state.user?.username }}</small>
        <button class="ghost-button" type="button" @click="logout">Đăng xuất</button>
      </div>
    </aside>

    <main class="main-panel">
      <slot />
    </main>
  </div>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";

const emit = defineEmits(["navigate"]);
const router = useRouter();
const auth = useAuthStore();
const expandedSection = ref("Điều phối");

const sections = [
  {
    label: "Điều phối",
    items: [
      { to: "/", label: "Dashboard", caption: "Tổng quan hệ thống", permission: "dashboard.view" },
      { to: "/control", label: "Control", caption: "Launch và runtime execution", permission: "runtime.control" },
      { to: "/operation-designer", label: "Designer", caption: "Sắp xếp workflow task", permission: "operations.manage" },
      { to: "/execution-monitor", label: "Monitor", caption: "Theo dõi execution", permission: "runtime.control" },
      { to: "/finding-explorer", label: "Explorer", caption: "Khám phá finding", permission: "scan_results.view" },
      { to: "/result-exchange", label: "Exchange", caption: "Import export kết quả", permission: "reports.manage" },
    ],
  },
  {
    label: "Danh mục",
    items: [
      { to: "/agents", label: "Agents", caption: "Trạng thái và version", permission: "agents.manage" },
      { to: "/tasks", label: "Tasks", caption: "Script và schema", permission: "tasks.manage" },
      { to: "/operations", label: "Operations", caption: "Workflow và lịch chạy", permission: "operations.manage" },
      { to: "/operation-executions", label: "Executions", caption: "Tiến trình operation", permission: "runtime.control" },
      { to: "/task-executions", label: "Task Executions", caption: "Tiến trình task", permission: "runtime.control" },
      { to: "/targets", label: "Targets", caption: "Tài sản và nhóm đối tượng", permission: "targets.manage" },
      { to: "/vulnerabilities", label: "CVE", caption: "Threat, proposal, PoC", permission: "vulnerabilities.manage" },
      { to: "/scan-results", label: "Scan Results", caption: "Dữ liệu chuẩn hóa", permission: "scan_results.view" },
      { to: "/scan-findings", label: "Findings", caption: "Lỗ hổng và bằng chứng", permission: "scan_results.view" },
    ],
  },
  {
    label: "Báo cáo",
    items: [
      { to: "/report-templates", label: "Reports", caption: "Mẫu và thống kê", permission: "reports.manage" },
      { to: "/generated-reports", label: "Generated", caption: "Báo cáo đã sinh ra", permission: "reports.manage" },
      { to: "/report-snapshots", label: "Snapshots", caption: "Dữ liệu snapshot", permission: "reports.manage" },
      { to: "/operation-result-history", label: "History", caption: "Lịch sử kết quả", permission: "reports.manage" },
    ],
  },
  {
    label: "Phân quyền",
    items: [
      { to: "/account-groups", label: "Nhóm tài khoản", caption: "Quản lý nhóm", permission: "auth.manage" },
      { to: "/user-accounts", label: "Tài khoản", caption: "Quản lý người dùng", permission: "auth.manage" },
      { to: "/group-permissions", label: "Quyền theo nhóm", caption: "Bật tắt quyền", permission: "auth.manage" },
    ],
  },
];

const visibleSections = computed(() =>
  sections
    .map((section) => ({
      ...section,
      items: section.items.filter((item) => auth.hasPermission(item.permission)),
    }))
    .filter((section) => section.items.length > 0)
);

watch(
  visibleSections,
  (items) => {
    if (!items.length) return;
    if (!items.some((section) => section.label === expandedSection.value)) {
      expandedSection.value = items[0].label;
    }
  },
  { immediate: true }
);

function toggleSection(label) {
  expandedSection.value = expandedSection.value === label ? "" : label;
}

function emitNavigate() {
  emit("navigate");
}

function logout() {
  auth.clearSession();
  router.push("/login");
}
</script>

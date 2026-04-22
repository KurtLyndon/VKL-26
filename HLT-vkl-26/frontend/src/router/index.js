import { createRouter, createWebHistory } from "vue-router";
import { getCurrentUser } from "../api/client";
import { useAuthStore } from "../stores/auth";
import DashboardView from "../views/DashboardView.vue";
import ExecutionMonitorView from "../views/ExecutionMonitorView.vue";
import FindingExplorerView from "../views/FindingExplorerView.vue";
import LoginView from "../views/LoginView.vue";
import OperationDesignerView from "../views/OperationDesignerView.vue";
import OperationControlView from "../views/OperationControlView.vue";
import ResultExchangeView from "../views/ResultExchangeView.vue";
import ResourceView from "../views/ResourceView.vue";
import AccountGroupPermissionsView from "../views/AccountGroupPermissionsView.vue";

const routes = [
  { path: "/login", name: "login", component: LoginView, meta: { title: "Login", public: true } },
  { path: "/", name: "dashboard", component: DashboardView, meta: { title: "Dashboard", permission: "dashboard.view" } },
  {
    path: "/control",
    component: OperationControlView,
    meta: { title: "Operation Control", permission: "runtime.control" },
  },
  {
    path: "/operation-designer",
    component: OperationDesignerView,
    meta: { title: "Operation Designer", permission: "operations.manage" },
  },
  {
    path: "/execution-monitor",
    component: ExecutionMonitorView,
    meta: { title: "Execution Monitor", permission: "runtime.control" },
  },
  {
    path: "/finding-explorer",
    component: FindingExplorerView,
    meta: { title: "Finding Explorer", permission: "scan_results.view" },
  },
  {
    path: "/result-exchange",
    component: ResultExchangeView,
    meta: { title: "Result Exchange", permission: "reports.manage" },
  },
  {
    path: "/agents",
    component: ResourceView,
    meta: { title: "Agents", permission: "agents.manage" },
    props: {
      title: "Quản lý Agent",
      resource: "agents",
      fields: ["code", "name", "agent_type", "ip_address", "port", "version", "status"],
      jsonFields: [],
    },
  },
  {
    path: "/tasks",
    component: ResourceView,
    meta: { title: "Tasks", permission: "tasks.manage" },
    props: {
      title: "Quản lý Task",
      resource: "tasks",
      fields: ["code", "name", "agent_type", "script_name", "script_path", "version", "is_active"],
      jsonFields: ["input_schema_json", "output_schema_json"],
      longTextFields: ["description", "script_content"],
    },
  },
  {
    path: "/operations",
    component: ResourceView,
    meta: { title: "Operations", permission: "operations.manage" },
    props: {
      title: "Quản lý Operation",
      resource: "operations",
      fields: ["code", "name", "schedule_type", "is_active"],
      jsonFields: ["schedule_config_json"],
      longTextFields: ["description"],
    },
  },
  {
    path: "/operation-executions",
    component: ResourceView,
    meta: { title: "Executions", permission: "runtime.control" },
    props: {
      title: "Quản lý Operation Execution",
      resource: "operation-executions",
      fields: ["operation_id", "execution_code", "trigger_type", "status"],
      jsonFields: ["summary_json"],
      longTextFields: [],
    },
  },
  {
    path: "/task-executions",
    component: ResourceView,
    meta: { title: "Task Executions", permission: "runtime.control" },
    props: {
      title: "Quản lý Task Execution",
      resource: "task-executions",
      fields: ["operation_execution_id", "operation_task_id", "task_id", "agent_id", "status"],
      jsonFields: ["input_data_json", "output_data_json"],
      longTextFields: ["raw_log"],
    },
  },
  {
    path: "/targets",
    component: ResourceView,
    meta: { title: "Targets", permission: "targets.manage" },
    props: {
      title: "Quản lý Target",
      resource: "targets",
      fields: ["code", "name", "target_type", "ip_range", "domain"],
      jsonFields: [],
      longTextFields: ["description"],
    },
  },
  {
    path: "/vulnerabilities",
    component: ResourceView,
    meta: { title: "CVE", permission: "vulnerabilities.manage" },
    props: {
      title: "Quản lý CVE",
      resource: "vulnerabilities",
      fields: ["code", "title", "level", "poc_file_name"],
      jsonFields: [],
      longTextFields: ["threat", "proposal", "description"],
    },
  },
  {
    path: "/scan-results",
    component: ResourceView,
    meta: { title: "Scan Results", permission: "scan_results.view" },
    props: {
      title: "Kết quả chuẩn hóa",
      resource: "scan-results",
      fields: ["operation_execution_id", "task_execution_id", "target_id", "agent_type", "source_tool", "parse_status"],
      jsonFields: ["normalized_output_json"],
      longTextFields: ["raw_output"],
    },
  },
  {
    path: "/scan-findings",
    component: ResourceView,
    meta: { title: "Findings", permission: "scan_results.view" },
    props: {
      title: "Quản lý Finding",
      resource: "scan-findings",
      fields: ["scan_result_id", "finding_code", "title", "severity", "port", "service_name", "status"],
      jsonFields: [],
      longTextFields: ["description", "evidence"],
    },
  },
  {
    path: "/report-templates",
    component: ResourceView,
    meta: { title: "Reports", permission: "reports.manage" },
    props: {
      title: "Mẫu báo cáo",
      resource: "report-templates",
      fields: ["code", "name", "report_type"],
      jsonFields: ["filter_config_json", "layout_config_json"],
      longTextFields: [],
    },
  },
  {
    path: "/generated-reports",
    component: ResourceView,
    meta: { title: "Generated Reports", permission: "reports.manage" },
    props: {
      title: "Báo cáo đã sinh",
      resource: "generated-reports",
      fields: ["report_template_id", "operation_execution_id", "file_name", "file_path", "generated_by"],
      jsonFields: ["summary_json"],
      longTextFields: [],
    },
  },
  {
    path: "/report-snapshots",
    component: ResourceView,
    meta: { title: "Report Snapshots", permission: "reports.manage" },
    props: {
      title: "Snapshot báo cáo",
      resource: "report-snapshots",
      fields: ["generated_report_id"],
      jsonFields: ["data_json"],
      longTextFields: [],
    },
  },
  {
    path: "/operation-result-history",
    component: ResourceView,
    meta: { title: "Result History", permission: "reports.manage" },
    props: {
      title: "Lịch sử import export",
      resource: "operation-result-history",
      fields: ["operation_id", "action_type", "file_name", "file_format", "status"],
      jsonFields: [],
      longTextFields: ["note", "file_path"],
    },
  },
  {
    path: "/account-groups",
    component: ResourceView,
    meta: { title: "Account Groups", permission: "auth.manage" },
    props: {
      title: "Quản lý nhóm tài khoản",
      resource: "account-groups",
      fields: ["code", "name", "is_active"],
      jsonFields: [],
      longTextFields: ["description"],
    },
  },
  {
    path: "/user-accounts",
    component: ResourceView,
    meta: { title: "User Accounts", permission: "auth.manage" },
    props: {
      title: "Quản lý tài khoản",
      resource: "user-accounts",
      fields: ["username", "full_name", "email", "group_id", "is_active", "password"],
      jsonFields: [],
      longTextFields: [],
    },
  },
  {
    path: "/group-permissions",
    component: AccountGroupPermissionsView,
    meta: { title: "Group Permissions", permission: "auth.manage" },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

let authHydrated = false;

router.beforeEach(async (to) => {
  const auth = useAuthStore();

  if (!authHydrated && auth.state.token) {
    try {
      const session = await getCurrentUser();
      auth.hydrateSession(session);
    } catch {
      auth.clearSession();
    } finally {
      authHydrated = true;
    }
  } else if (!authHydrated) {
    auth.state.ready = true;
    authHydrated = true;
  }

  if (to.meta.public) {
    if (to.path === "/login" && auth.isAuthenticated.value) {
      return "/";
    }
    return true;
  }

  if (!auth.isAuthenticated.value) {
    return "/login";
  }

  if (to.meta.permission && !auth.hasPermission(to.meta.permission)) {
    return "/";
  }

  return true;
});

router.afterEach((to) => {
  document.title = `HLT VKL 26 | ${to.meta.title || "Admin"}`;
});

export default router;

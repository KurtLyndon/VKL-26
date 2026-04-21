import { createRouter, createWebHistory } from "vue-router";
import DashboardView from "../views/DashboardView.vue";
import ResourceView from "../views/ResourceView.vue";

const routes = [
  { path: "/", name: "dashboard", component: DashboardView, meta: { title: "Dashboard" } },
  {
    path: "/agents",
    component: ResourceView,
    meta: { title: "Agents" },
    props: {
      title: "Quan ly Agent",
      resource: "agents",
      fields: ["code", "name", "agent_type", "ip_address", "port", "version", "status"],
      jsonFields: [],
    },
  },
  {
    path: "/tasks",
    component: ResourceView,
    meta: { title: "Tasks" },
    props: {
      title: "Quan ly Task",
      resource: "tasks",
      fields: ["code", "name", "agent_type", "script_name", "script_path", "version", "is_active"],
      jsonFields: ["input_schema_json", "output_schema_json"],
      longTextFields: ["description", "script_content"],
    },
  },
  {
    path: "/operations",
    component: ResourceView,
    meta: { title: "Operations" },
    props: {
      title: "Quan ly Operation",
      resource: "operations",
      fields: ["code", "name", "schedule_type", "is_active"],
      jsonFields: ["schedule_config_json"],
      longTextFields: ["description"],
    },
  },
  {
    path: "/operation-executions",
    component: ResourceView,
    meta: { title: "Executions" },
    props: {
      title: "Quan ly Operation Execution",
      resource: "operation-executions",
      fields: ["operation_id", "execution_code", "trigger_type", "status"],
      jsonFields: ["summary_json"],
      longTextFields: [],
    },
  },
  {
    path: "/task-executions",
    component: ResourceView,
    meta: { title: "Task Executions" },
    props: {
      title: "Quan ly Task Execution",
      resource: "task-executions",
      fields: ["operation_execution_id", "operation_task_id", "task_id", "agent_id", "status"],
      jsonFields: ["input_data_json", "output_data_json"],
      longTextFields: ["raw_log"],
    },
  },
  {
    path: "/targets",
    component: ResourceView,
    meta: { title: "Targets" },
    props: {
      title: "Quan ly Target",
      resource: "targets",
      fields: ["code", "name", "target_type", "ip_range", "domain"],
      jsonFields: [],
      longTextFields: ["description"],
    },
  },
  {
    path: "/vulnerabilities",
    component: ResourceView,
    meta: { title: "CVE" },
    props: {
      title: "Quan ly CVE",
      resource: "vulnerabilities",
      fields: ["code", "title", "level", "poc_file_name"],
      jsonFields: [],
      longTextFields: ["threat", "proposal", "description"],
    },
  },
  {
    path: "/scan-results",
    component: ResourceView,
    meta: { title: "Scan Results" },
    props: {
      title: "Ket qua chuan hoa",
      resource: "scan-results",
      fields: ["operation_execution_id", "task_execution_id", "target_id", "agent_type", "source_tool", "parse_status"],
      jsonFields: ["normalized_output_json"],
      longTextFields: ["raw_output"],
    },
  },
  {
    path: "/scan-findings",
    component: ResourceView,
    meta: { title: "Findings" },
    props: {
      title: "Quan ly Finding",
      resource: "scan-findings",
      fields: ["scan_result_id", "finding_code", "title", "severity", "port", "service_name", "status"],
      jsonFields: [],
      longTextFields: ["description", "evidence"],
    },
  },
  {
    path: "/report-templates",
    component: ResourceView,
    meta: { title: "Reports" },
    props: {
      title: "Mau bao cao",
      resource: "report-templates",
      fields: ["code", "name", "report_type"],
      jsonFields: ["filter_config_json", "layout_config_json"],
      longTextFields: [],
    },
  },
  {
    path: "/generated-reports",
    component: ResourceView,
    meta: { title: "Generated Reports" },
    props: {
      title: "Bao cao da sinh",
      resource: "generated-reports",
      fields: ["report_template_id", "operation_execution_id", "file_name", "file_path", "generated_by"],
      jsonFields: ["summary_json"],
      longTextFields: [],
    },
  },
  {
    path: "/report-snapshots",
    component: ResourceView,
    meta: { title: "Report Snapshots" },
    props: {
      title: "Snapshot bao cao",
      resource: "report-snapshots",
      fields: ["generated_report_id"],
      jsonFields: ["data_json"],
      longTextFields: [],
    },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.afterEach((to) => {
  document.title = `HLT VKL 26 | ${to.meta.title || "Admin"}`;
});

export default router;

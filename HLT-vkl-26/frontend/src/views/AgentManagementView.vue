<template>
  <section class="page-header">
    <div>
      <p class="eyebrow">Giám sát agent</p>
      <h2>Quản lý Agent</h2>
      <p class="page-copy">Quản lý và giám sát tình trạng agent.</p>
    </div>
    <div class="agent-header-actions">
      <div class="form-actions">
        <button class="ghost-button" type="button" @click="refreshAll">Làm mới</button>
        <button class="primary-button" type="button" @click="runMonitor">Kiểm tra trạng thái ngay</button>
      </div>
      <small class="agent-countdown-note">
        Đợt kiểm tra trạng thái tiếp theo sau: <strong>{{ countdownLabel }}</strong>
      </small>
    </div>
  </section>

  <section class="stat-grid agent-overview-grid">
    <article class="stat-card">
      <span class="stat-label">Tổng số agent</span>
      <strong class="stat-value">{{ overview.total_agents || 0 }}</strong>
      <small class="inline-note">Chu kỳ kiểm tra: {{ overview.poll_seconds || 60 }} giây</small>
    </article>
    <article v-for="item in overview.type_summaries" :key="item.agent_type" class="stat-card">
      <span class="stat-label">Loại Agent: {{ item.agent_type }}</span>
      <strong class="stat-value">{{ item.count }}</strong>
      <small class="inline-note">Online: {{ item.online_count || 0 }}</small>
    </article>
  </section>

  <section class="panel panel-span-full">
    <div class="panel-head">
      <h3>Agents</h3>
      <span class="badge">{{ overview.agents.length }} bản ghi</span>
    </div>

    <div class="agent-card-grid">
      <button
        v-for="agent in overview.agents"
        :key="agent.id"
        type="button"
        class="agent-monitor-card"
        :class="{ 'agent-monitor-card--selected': form.id === agent.id }"
        :style="agentTypeCardStyle(agent.agent_type)"
        @click="selectAgent(agent)"
      >
        <div class="agent-monitor-card-head">
          <div>
            <strong>{{ agent.name }}</strong>
            <small>{{ agent.code }}</small>
          </div>
          <span class="agent-type-tag">{{ agent.agent_type }}</span>
        </div>

        <div class="agent-monitor-card-grid">
          <div>
            <span>Version</span>
            <strong>{{ agent.version || "-" }}</strong>
          </div>
          <div>
            <span>Trạng thái</span>
            <strong class="agent-status-text" :class="`agent-status-text--${agent.status}`">{{ statusLabel(agent.status) }}</strong>
          </div>
          <div>
            <span>Thời gian</span>
            <strong>{{ agent.duration_label }}</strong>
          </div>
          <div>
            <span>Đã thực thi</span>
            <strong>{{ agent.task_execution_count }} task | {{ agent.operation_execution_count }} operation</strong>
          </div>
        </div>

        <p class="agent-status-note">{{ agent.status_note || "-" }}</p>
      </button>
    </div>

    <p v-if="runtimeMessage" class="inline-note">{{ runtimeMessage }}</p>
  </section>

  <section class="panel-grid panel-grid-loose">
    <article class="panel agent-table-panel">
      <div class="panel-head">
        <h3>Danh sách Agent</h3>
        <span class="badge">{{ totalItems }} bản ghi</span>
      </div>

      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th class="sortable-header" @click="toggleSort('code')">Mã{{ sortLabel("code") }}</th>
              <th class="sortable-header" @click="toggleSort('name')">Tên{{ sortLabel("name") }}</th>
              <th class="sortable-header" @click="toggleSort('agent_type')">Loại{{ sortLabel("agent_type") }}</th>
              <th>Tác vụ</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="agent in paginatedItems"
              :key="agent.id"
              class="row-selectable"
              :class="{ 'row-selected': form.id === agent.id }"
              @click="selectAgent(agent)"
            >
              <td>{{ agent.code }}</td>
              <td>{{ agent.name }}</td>
              <td>{{ agent.agent_type }}</td>
              <td class="action-cell">
                <button class="table-button danger" type="button" @click.stop="removeAgent(agent.id)">Xóa</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <PaginationBar
        :current-page="currentPage"
        :page-size="pageSize"
        :total-items="totalItems"
        :total-pages="totalPages"
        @update:page-size="pageSize = $event"
        @previous="goToPreviousPage"
        @next="goToNextPage"
      />
    </article>

    <article class="panel agent-form-panel">
      <div class="panel-head">
        <h3>Thông tin Agent</h3>
        <span class="badge">{{ form.id ? `ID ${form.id}` : "tạo mới" }}</span>
      </div>

      <form class="resource-form" @submit.prevent="saveAgent">
        <div class="filter-grid">
          <label class="field-block">
            <span>Mã agent</span>
            <input v-model="form.code" required />
          </label>
          <label class="field-block">
            <span>Tên agent</span>
            <input v-model="form.name" required />
          </label>
          <label class="field-block">
            <span>Loại agent</span>
            <input v-model="form.agent_type" required />
          </label>
        </div>

        <div class="filter-grid">
          <label class="field-block">
            <span>Host</span>
            <input v-model="form.host" />
          </label>
          <label class="field-block">
            <span>IP</span>
            <input v-model="form.ip_address" />
          </label>
          <label class="field-block">
            <span>Port</span>
            <input v-model.number="form.port" type="number" min="0" />
          </label>
        </div>

        <div class="filter-grid">
          <label class="field-block">
            <span>Version</span>
            <input v-model="form.version" />
          </label>
          <label class="field-block">
            <span>Trạng thái</span>
            <input :value="statusLabel(form.status)" disabled />
          </label>
          <label class="field-block">
            <span>Duration</span>
            <input :value="form.duration_label || '-'" disabled />
          </label>
        </div>

        <div class="filter-grid">
          <label class="field-block">
            <span>Old status</span>
            <input :value="statusLabel(form.old_status)" disabled />
          </label>
          <label class="field-block">
            <span>Old time</span>
            <input :value="formatDateTime(form.old_time)" disabled />
          </label>
          <label class="field-block">
            <span>Last seen</span>
            <input :value="formatDateTime(form.last_seen_at)" disabled />
          </label>
        </div>

        <label class="field-block">
          <span>Status note</span>
          <textarea :value="form.status_note || ''" rows="3" disabled />
        </label>

        <div class="form-actions">
          <button class="primary-button" type="submit">{{ form.id ? "Lưu thay đổi" : "Tạo mới" }}</button>
          <button v-if="form.id" class="ghost-button" type="button" @click="resetForm">Bỏ chọn</button>
        </div>
      </form>

      <p v-if="message" class="inline-note">{{ message }}</p>
    </article>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import {
  createManagedAgent,
  deleteItem,
  getAgentMonitorOverview,
  runAgentMonitorNow,
  updateManagedAgent,
} from "../api/client";
import PaginationBar from "../components/PaginationBar.vue";
import { usePagination } from "../composables/usePagination";
import { nextSortState, sortIndicator, sortRows } from "../utils/tableSort";

const AGENT_OVERVIEW_CACHE_KEY = "hlt-agent-monitor-overview";

const overview = reactive({
  total_agents: 0,
  type_summaries: [],
  agents: [],
  last_run_at: null,
  next_run_at: null,
  poll_seconds: 60,
});
const message = ref("");
const runtimeMessage = ref("");
const sortState = ref({ key: "code", direction: "asc" });
const refreshTimer = ref(null);
const countdownTimer = ref(null);
const countdownSeconds = ref(60);
const form = reactive({
  id: null,
  code: "",
  name: "",
  agent_type: "",
  host: "",
  ip_address: "",
  port: null,
  version: "",
  status: "offline",
  duration: 0,
  duration_label: "",
  old_time: null,
  old_status: "",
  status_note: "",
  last_seen_at: null,
});

const sortedAgents = computed(() => sortRows(overview.agents, sortState.value));
const { currentPage, pageSize, paginatedItems, totalItems, totalPages, goToPreviousPage, goToNextPage } =
  usePagination(sortedAgents);
const countdownLabel = computed(() => `${Math.max(countdownSeconds.value, 0)}s`);

function applyOverview(data) {
  overview.total_agents = data.total_agents || 0;
  overview.type_summaries = data.type_summaries || [];
  overview.agents = data.agents || [];
  overview.last_run_at = data.last_run_at || null;
  overview.next_run_at = data.next_run_at || null;
  overview.poll_seconds = data.poll_seconds || 60;
}

function hydrateOverviewFromCache() {
  if (typeof window === "undefined") {
    return;
  }
  try {
    const raw = window.localStorage.getItem(AGENT_OVERVIEW_CACHE_KEY);
    if (!raw) {
      return;
    }
    const cached = JSON.parse(raw);
    applyOverview(cached);
  } catch (_error) {
    window.localStorage.removeItem(AGENT_OVERVIEW_CACHE_KEY);
  }
}

function persistOverviewToCache() {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(
    AGENT_OVERVIEW_CACHE_KEY,
    JSON.stringify({
      total_agents: overview.total_agents,
      type_summaries: overview.type_summaries,
      agents: overview.agents,
      last_run_at: overview.last_run_at,
      next_run_at: overview.next_run_at,
      poll_seconds: overview.poll_seconds,
    }),
  );
}

function resetForm() {
  form.id = null;
  form.code = "";
  form.name = "";
  form.agent_type = "";
  form.host = "";
  form.ip_address = "";
  form.port = null;
  form.version = "";
  form.status = "offline";
  form.duration = 0;
  form.duration_label = "";
  form.old_time = null;
  form.old_status = "";
  form.status_note = "";
  form.last_seen_at = null;
}

function statusLabel(value) {
  const normalized = (value || "offline").toLowerCase();
  if (normalized === "ready") return "Ready";
  if (normalized === "working") return "Working";
  if (normalized === "error") return "Error";
  return "Offline";
}

function formatDateTime(value) {
  return value ? new Date(value).toLocaleString("vi-VN") : "-";
}

function toggleSort(key) {
  sortState.value = nextSortState(sortState.value, key);
}

function sortLabel(key) {
  return sortIndicator(sortState.value, key);
}

function agentTypeCardStyle(agentType) {
  const value = (agentType || "agent").toLowerCase();
  let hash = 0;
  for (const char of value) {
    hash = (hash * 31 + char.charCodeAt(0)) % 360;
  }
  const hue = value === "system" ? 42 : hash;
  return {
    "--agent-type-accent": `hsl(${hue} 58% 34%)`,
    "--agent-type-fill": `hsla(${hue} 62% 74% / 0.22)`,
  };
}

function selectAgent(agent) {
  form.id = agent.id;
  form.code = agent.code || "";
  form.name = agent.name || "";
  form.agent_type = agent.agent_type || "";
  form.host = agent.host || "";
  form.ip_address = agent.ip_address || "";
  form.port = agent.port ?? null;
  form.version = agent.version || "";
  form.status = agent.status || "offline";
  form.duration = agent.duration || 0;
  form.duration_label = agent.duration_label || "";
  form.old_time = agent.old_time || null;
  form.old_status = agent.old_status || "";
  form.status_note = agent.status_note || "";
  form.last_seen_at = agent.last_seen_at || null;
}

async function loadOverview() {
  const data = await getAgentMonitorOverview();
  applyOverview(data);
  persistOverviewToCache();

  if (form.id) {
    const current = overview.agents.find((item) => item.id === form.id);
    if (current) {
      selectAgent(current);
    }
  }
  syncCountdown();
}

async function refreshAll() {
  await loadOverview();
}

async function runMonitor() {
  const data = await runAgentMonitorNow();
  runtimeMessage.value = `Đã kiểm tra ${data.checked_agents} agent | Ready ${data.ready_agents} | Working ${data.working_agents} | Error ${data.error_agents} | Offline ${data.offline_agents}.`;
  overview.next_run_at = data.next_run_at || null;
  syncCountdown();
  await loadOverview();
}

async function saveAgent() {
  const payload = {
    code: form.code.trim(),
    name: form.name.trim(),
    agent_type: form.agent_type.trim(),
    host: form.host || null,
    ip_address: form.ip_address || null,
    port: form.port === null || form.port === "" ? null : Number(form.port),
    version: form.version || null,
  };

  if (form.id) {
    const data = await updateManagedAgent(form.id, payload);
    message.value = `Đã cập nhật agent ${data.code}.`;
    selectAgent(data);
  } else {
    const data = await createManagedAgent(payload);
    message.value = `Đã tạo agent ${data.code}.`;
    selectAgent(data);
  }
  await loadOverview();
}

async function removeAgent(agentId) {
  await deleteItem("agents", agentId);
  if (form.id === agentId) {
    resetForm();
  }
  message.value = "Đã xóa agent.";
  await loadOverview();
}

function startAutoRefresh() {
  stopAutoRefresh();
  refreshTimer.value = window.setInterval(() => {
    loadOverview();
  }, 30000);
}

function stopAutoRefresh() {
  if (refreshTimer.value) {
    window.clearInterval(refreshTimer.value);
    refreshTimer.value = null;
  }
}

function syncCountdown() {
  if (!overview.next_run_at) {
    countdownSeconds.value = overview.poll_seconds || 60;
    return;
  }
  const remaining = Math.ceil((new Date(overview.next_run_at).getTime() - Date.now()) / 1000);
  countdownSeconds.value = remaining > 0 ? remaining : 0;
}

function startCountdown() {
  stopCountdown();
  countdownTimer.value = window.setInterval(() => {
    if (countdownSeconds.value > 0) {
      countdownSeconds.value -= 1;
    } else {
      countdownSeconds.value = overview.poll_seconds || 60;
    }
  }, 1000);
}

function stopCountdown() {
  if (countdownTimer.value) {
    window.clearInterval(countdownTimer.value);
    countdownTimer.value = null;
  }
}

onMounted(async () => {
  resetForm();
  hydrateOverviewFromCache();
  syncCountdown();
  await loadOverview();
  startAutoRefresh();
  startCountdown();
});

onBeforeUnmount(() => {
  stopAutoRefresh();
  stopCountdown();
});
</script>

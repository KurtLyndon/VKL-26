<template>
  <section class="page-header">
    <div>
      <p class="eyebrow">Danh mục</p>
      <h2>Database Explorer</h2>
      <p class="page-copy">Tra cứu cấu trúc và chạy câu SELECT an toàn để đọc dữ liệu hệ thống.</p>
    </div>
    <button class="ghost-button" type="button" @click="loadSchema">Refresh schema</button>
  </section>

  <section class="panel database-schema-panel">
    <div class="panel-head">
      <h3>Cấu trúc database</h3>
      <span class="badge">{{ schema.tables.length }} tables</span>
    </div>

    <div class="schema-grid">
      <article v-for="table in schema.tables" :key="table.name" :id="tableAnchor(table.name)" class="schema-table">
        <div class="schema-table-head">
          <strong>{{ table.name }}</strong>
          <small>{{ table.columns.length }} columns</small>
        </div>
        <ul class="schema-column-list">
          <li v-for="column in table.columns" :key="`${table.name}.${column.name}`">
            <code>{{ column.name }}</code>
            <span>{{ column.type }}</span>
            <small>{{ column.key || (column.nullable ? "NULL" : "NOT NULL") }}</small>
          </li>
        </ul>
        <div v-if="table.foreign_keys.length" class="schema-fk-list">
          <a
            v-for="fk in table.foreign_keys"
            :key="`${table.name}.${fk.constraint}.${fk.column}`"
            :href="`#${tableAnchor(fk.references_table)}`"
          >
            {{ fk.column }} -> {{ fk.references_table }}.{{ fk.references_column }}
          </a>
        </div>
      </article>
    </div>
  </section>

  <section class="panel">
    <div class="panel-head">
      <h3>SELECT query</h3>
      <span class="badge">read only</span>
    </div>

    <form class="resource-form" @submit.prevent="submitQuery">
      <label class="field-block">
        <span>SQL</span>
        <textarea v-model="queryText" rows="7" placeholder="SELECT * FROM target LIMIT 20" />
      </label>
      <div class="filter-grid">
        <label class="field-block">
          <span>Max rows</span>
          <input v-model.number="maxRows" type="number" min="1" max="2000" />
        </label>
      </div>
      <div class="form-actions">
        <button class="primary-button" type="submit">Run SELECT</button>
        <button class="ghost-button" type="button" :disabled="!result.rows.length" @click="exportExcel">
          Export Excel
        </button>
      </div>
    </form>

    <p v-if="message" class="inline-note">{{ message }}</p>
  </section>

  <section class="panel">
    <div class="panel-head">
      <h3>Kết quả</h3>
      <span class="badge">{{ sortedRows.length }} rows</span>
    </div>

    <div v-if="result.truncated" class="inline-note">
      Kết quả đã được giới hạn ở {{ result.max_rows }} dòng.
    </div>

    <div class="table-wrap">
      <table class="data-table database-result-table">
        <thead>
          <tr>
            <th
              v-for="column in visibleColumns"
              :key="column"
              draggable="true"
              class="sortable-header draggable-column"
              @click="toggleSort(column)"
              @dragstart="startColumnDrag(column)"
              @dragover.prevent
              @drop="dropColumn(column)"
            >
              {{ column }}{{ sortLabel(column) }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, rowIndex) in sortedRows" :key="rowIndex">
            <td v-for="column in visibleColumns" :key="`${rowIndex}.${column}`">{{ formatCell(row[column]) }}</td>
          </tr>
          <tr v-if="!sortedRows.length">
            <td :colspan="visibleColumns.length || 1">Chưa có dữ liệu.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { getDatabaseExplorerSchema, runDatabaseExplorerQuery } from "../api/client";
import { nextSortState, sortIndicator, sortRows } from "../utils/tableSort";

const schema = reactive({ schema: "", tables: [] });
const queryText = ref("SELECT * FROM target LIMIT 20");
const maxRows = ref(500);
const message = ref("");
const result = reactive({ columns: [], rows: [], row_count: 0, truncated: false, max_rows: 500 });
const columnOrder = ref([]);
const sortState = ref({ key: "", direction: "" });
const draggedColumn = ref("");

const visibleColumns = computed(() => columnOrder.value.filter((column) => result.columns.includes(column)));
const sortedRows = computed(() => {
  if (!sortState.value.key || !sortState.value.direction) return result.rows;
  return sortRows(result.rows, sortState.value);
});

function tableAnchor(name) {
  return `db-table-${String(name).replace(/[^A-Za-z0-9_-]+/g, "-")}`;
}

function formatCell(value) {
  if (value === null || value === undefined) return "";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function sortLabel(column) {
  return sortIndicator(sortState.value, column);
}

function toggleSort(column) {
  sortState.value = nextSortState(sortState.value, column);
}

function startColumnDrag(column) {
  draggedColumn.value = column;
}

function dropColumn(targetColumn) {
  const sourceColumn = draggedColumn.value;
  if (!sourceColumn || sourceColumn === targetColumn) return;
  const nextOrder = [...columnOrder.value];
  const sourceIndex = nextOrder.indexOf(sourceColumn);
  const targetIndex = nextOrder.indexOf(targetColumn);
  if (sourceIndex < 0 || targetIndex < 0) return;
  nextOrder.splice(sourceIndex, 1);
  nextOrder.splice(targetIndex, 0, sourceColumn);
  columnOrder.value = nextOrder;
  draggedColumn.value = "";
}

async function loadSchema() {
  const data = await getDatabaseExplorerSchema();
  schema.schema = data.schema;
  schema.tables = data.tables || [];
}

async function submitQuery() {
  try {
    const data = await runDatabaseExplorerQuery({ sql: queryText.value, max_rows: maxRows.value || 500 });
    result.columns = data.columns || [];
    result.rows = data.rows || [];
    result.row_count = data.row_count || 0;
    result.truncated = Boolean(data.truncated);
    result.max_rows = data.max_rows || maxRows.value;
    columnOrder.value = [...result.columns];
    sortState.value = { key: "", direction: "" };
    message.value = `Đã trả về ${result.row_count} dòng.`;
  } catch (error) {
    message.value = error?.response?.data?.detail || error?.message || "Không thể chạy query.";
  }
}

function escapeHtml(value) {
  return formatCell(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function exportExcel() {
  const header = visibleColumns.value.map((column) => `<th>${escapeHtml(column)}</th>`).join("");
  const body = sortedRows.value
    .map((row) => `<tr>${visibleColumns.value.map((column) => `<td>${escapeHtml(row[column])}</td>`).join("")}</tr>`)
    .join("");
  const html = `<table><thead><tr>${header}</tr></thead><tbody>${body}</tbody></table>`;
  const blob = new Blob([html], { type: "application/vnd.ms-excel;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `database-explorer-${new Date().toISOString().slice(0, 19).replaceAll(":", "")}.xls`;
  link.click();
  URL.revokeObjectURL(url);
}

onMounted(async () => {
  await loadSchema();
});
</script>

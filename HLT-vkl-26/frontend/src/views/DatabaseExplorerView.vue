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
      <div class="panel-actions">
        <button class="ghost-button compact-button" type="button" @click="copySchemaForAi">
          {{ schemaCopyMessage || "Copy schema cho AI" }}
        </button>
        <span class="badge">{{ schema.tables.length }} tables</span>
      </div>
    </div>

    <div class="schema-layout">
      <div class="schema-diagram-wrap">
        <div class="schema-legend" aria-label="Chú giải sơ đồ database">
          <span><i class="legend-shape legend-oval"></i>Bảng chính</span>
          <span><i class="legend-shape legend-rect"></i>Bảng liên kết / phân công</span>
          <span><i class="legend-line"></i>Khóa ngoại</span>
        </div>

        <div class="schema-diagram" :style="diagramStyle">
          <svg
            class="schema-link-layer"
            :viewBox="`0 0 ${diagramSize.width} ${diagramSize.height}`"
            preserveAspectRatio="none"
            aria-hidden="true"
          >
            <defs>
              <marker
                id="schema-arrow"
                markerWidth="10"
                markerHeight="10"
                refX="8"
                refY="3"
                orient="auto"
                markerUnits="strokeWidth"
              >
                <path d="M0,0 L0,6 L9,3 z" />
              </marker>
            </defs>
            <path
              v-for="edge in graphEdges"
              :key="edge.key"
              class="schema-link"
              :class="{ 'schema-link-active': edgeTouchesSelected(edge) }"
              :d="edge.path"
              marker-end="url(#schema-arrow)"
            />
          </svg>

          <button
            v-for="node in graphNodes"
            :key="node.name"
            class="schema-node"
            :class="[
              node.kind === 'link' ? 'schema-node-link' : 'schema-node-main',
              { 'schema-node-selected': selectedTable?.name === node.name },
            ]"
            type="button"
            :style="nodeStyle(node)"
            @click="selectTable(node.table)"
          >
            <strong>{{ node.name }}</strong>
            <small>{{ node.table.columns.length }} cột · {{ node.table.foreign_keys.length }} FK</small>
          </button>
        </div>
      </div>

      <aside class="schema-detail-panel">
        <template v-if="selectedTable">
          <div class="schema-detail-head">
            <div>
              <p class="eyebrow">Thông tin bảng</p>
              <h4>{{ selectedTable.name }}</h4>
            </div>
            <span class="badge">{{ tableKindLabel(selectedTable) }}</span>
          </div>

          <div class="schema-summary-grid">
            <span>{{ selectedTable.columns.length }} cột</span>
            <span>{{ selectedTable.foreign_keys.length }} khóa ngoại</span>
            <span>{{ incomingForeignKeys(selectedTable.name).length }} bảng tham chiếu tới</span>
          </div>

          <div class="schema-detail-section">
            <h5>Cột và constraints</h5>
            <div class="schema-column-detail-list">
              <article
                v-for="column in selectedTable.columns"
                :key="`${selectedTable.name}.${column.name}`"
                class="schema-column-detail"
              >
                <div>
                  <strong>{{ column.name }}</strong>
                  <span>{{ column.type }}</span>
                </div>
                <div class="schema-constraint-tags">
                  <small v-if="column.key">{{ column.key }}</small>
                  <small>{{ column.nullable ? "NULL" : "NOT NULL" }}</small>
                  <small v-if="column.default !== null && column.default !== undefined">
                    DEFAULT {{ column.default }}
                  </small>
                  <small v-if="column.extra">{{ column.extra }}</small>
                  <small v-if="foreignKeyForColumn(selectedTable, column.name)">
                    FK {{ foreignKeyForColumn(selectedTable, column.name).references_table }}.{{
                      foreignKeyForColumn(selectedTable, column.name).references_column
                    }}
                  </small>
                </div>
              </article>
            </div>
          </div>

          <div v-if="selectedTable.foreign_keys.length" class="schema-detail-section">
            <h5>Khóa ngoại đi</h5>
            <button
              v-for="fk in selectedTable.foreign_keys"
              :key="`${selectedTable.name}.${fk.constraint}.${fk.column}`"
              class="schema-relation-button"
              type="button"
              @click="selectTableByName(fk.references_table)"
            >
              <strong>{{ fk.column }}</strong>
              <span>{{ fk.constraint }} -> {{ fk.references_table }}.{{ fk.references_column }}</span>
            </button>
          </div>

          <div v-if="incomingForeignKeys(selectedTable.name).length" class="schema-detail-section">
            <h5>Bảng đang tham chiếu tới</h5>
            <button
              v-for="fk in incomingForeignKeys(selectedTable.name)"
              :key="`${fk.table}.${fk.constraint}.${fk.column}`"
              class="schema-relation-button"
              type="button"
              @click="selectTableByName(fk.table)"
            >
              <strong>{{ fk.table }}.{{ fk.column }}</strong>
              <span>{{ fk.constraint }}</span>
            </button>
          </div>
        </template>
        <p v-else class="inline-note">Click một khối trong sơ đồ để xem columns, data type và constraints.</p>
      </aside>
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
import { getDatabaseExplorerSchema, getDatabaseExplorerSchemaText, runDatabaseExplorerQuery } from "../api/client";
import { nextSortState, sortIndicator, sortRows } from "../utils/tableSort";

const NODE_WIDTH = 170;
const NODE_HEIGHT = 82;
const NODE_GAP_X = 74;
const NODE_GAP_Y = 72;
const DIAGRAM_PADDING = 42;

const schema = reactive({ schema: "", tables: [] });
const queryText = ref("SELECT * FROM target LIMIT 20");
const maxRows = ref(500);
const message = ref("");
const result = reactive({ columns: [], rows: [], row_count: 0, truncated: false, max_rows: 500 });
const columnOrder = ref([]);
const sortState = ref({ key: "", direction: "" });
const draggedColumn = ref("");
const selectedTableName = ref("");
const schemaCopyMessage = ref("");

const tableByName = computed(() => new Map(schema.tables.map((table) => [table.name, table])));

const selectedTable = computed(() => {
  if (!selectedTableName.value) return schema.tables[0] || null;
  return tableByName.value.get(selectedTableName.value) || schema.tables[0] || null;
});

const graphNodes = computed(() => {
  const mainTables = schema.tables.filter((table) => tableKind(table) === "main");
  const linkTables = schema.tables.filter((table) => tableKind(table) === "link");
  const columns = Math.max(3, Math.ceil(Math.sqrt(Math.max(schema.tables.length, 1))));
  const layoutRows = [
    ...mainTables.map((table) => ({ table, rowOffset: 0 })),
    ...linkTables.map((table) => ({ table, rowOffset: Math.ceil(mainTables.length / columns) || 1 })),
  ];

  return layoutRows.map(({ table, rowOffset }, index) => {
    const localIndex = tableKind(table) === "main" ? mainTables.indexOf(table) : linkTables.indexOf(table);
    const x = DIAGRAM_PADDING + (localIndex % columns) * (NODE_WIDTH + NODE_GAP_X);
    const y = DIAGRAM_PADDING + (rowOffset + Math.floor(localIndex / columns)) * (NODE_HEIGHT + NODE_GAP_Y);
    return {
      name: table.name,
      table,
      kind: tableKind(table),
      x,
      y,
      width: NODE_WIDTH,
      height: NODE_HEIGHT,
      centerX: x + NODE_WIDTH / 2,
      centerY: y + NODE_HEIGHT / 2,
      index,
    };
  });
});

const graphNodeByName = computed(() => new Map(graphNodes.value.map((node) => [node.name, node])));

const diagramSize = computed(() => {
  const maxX = Math.max(...graphNodes.value.map((node) => node.x + node.width), 640);
  const maxY = Math.max(...graphNodes.value.map((node) => node.y + node.height), 360);
  return { width: maxX + DIAGRAM_PADDING, height: maxY + DIAGRAM_PADDING };
});

const diagramStyle = computed(() => ({
  width: `${diagramSize.value.width}px`,
  height: `${diagramSize.value.height}px`,
}));

const graphEdges = computed(() =>
  schema.tables.flatMap((table) => {
    const source = graphNodeByName.value.get(table.name);
    if (!source) return [];
    return table.foreign_keys
      .map((fk) => {
        const target = graphNodeByName.value.get(fk.references_table);
        if (!target) return null;
        const midY = source.centerY + (target.centerY - source.centerY) / 2;
        return {
          key: `${table.name}.${fk.constraint}.${fk.column}`,
          source: table.name,
          target: fk.references_table,
          path: `M ${source.centerX} ${source.centerY} C ${source.centerX} ${midY}, ${target.centerX} ${midY}, ${target.centerX} ${target.centerY}`,
        };
      })
      .filter(Boolean);
  })
);

const visibleColumns = computed(() => columnOrder.value.filter((column) => result.columns.includes(column)));
const sortedRows = computed(() => {
  if (!sortState.value.key || !sortState.value.direction) return result.rows;
  return sortRows(result.rows, sortState.value);
});

function tableKind(table) {
  return table.foreign_keys.length >= 2 ? "link" : "main";
}

function tableKindLabel(table) {
  return tableKind(table) === "link" ? "liên kết / phân công" : "bảng chính";
}

function nodeStyle(node) {
  return {
    left: `${node.x}px`,
    top: `${node.y}px`,
    width: `${node.width}px`,
    height: `${node.height}px`,
  };
}

function edgeTouchesSelected(edge) {
  const name = selectedTable.value?.name;
  return Boolean(name && (edge.source === name || edge.target === name));
}

function selectTable(table) {
  selectedTableName.value = table.name;
}

function selectTableByName(name) {
  if (tableByName.value.has(name)) selectedTableName.value = name;
}

function incomingForeignKeys(tableName) {
  return schema.tables.flatMap((table) =>
    table.foreign_keys
      .filter((fk) => fk.references_table === tableName)
      .map((fk) => ({
        ...fk,
        table: table.name,
      }))
  );
}

function foreignKeyForColumn(table, columnName) {
  return table.foreign_keys.find((fk) => fk.column === columnName);
}

async function copySchemaForAi() {
  try {
    const data = await getDatabaseExplorerSchemaText();
    const text = data.text || "";
    await navigator.clipboard.writeText(text);
    schemaCopyMessage.value = "Đã copy";
  } catch {
    try {
      const data = await getDatabaseExplorerSchemaText();
      const text = data.text || "";
      const textarea = document.createElement("textarea");
      textarea.value = text;
      textarea.setAttribute("readonly", "");
      textarea.style.position = "fixed";
      textarea.style.opacity = "0";
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
      schemaCopyMessage.value = "Đã copy";
    } catch (error) {
      schemaCopyMessage.value = "Copy lỗi";
      message.value = error?.response?.data?.detail || error?.message || "Không thể copy schema.";
    }
  }
  window.setTimeout(() => {
    schemaCopyMessage.value = "";
  }, 1800);
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
  if (!selectedTableName.value && schema.tables.length) {
    selectedTableName.value = schema.tables[0].name;
  }
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

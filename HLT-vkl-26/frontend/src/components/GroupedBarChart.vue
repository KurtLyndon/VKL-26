<template>
  <div class="chart-card">
    <div v-if="!series.length" class="inline-note">Chưa có dữ liệu để hiển thị biểu đồ.</div>
    <div v-else class="grouped-chart">
      <div class="grouped-chart-legend">
        <div v-for="item in legendItems" :key="item.label" class="legend-item">
          <span class="legend-swatch" :style="{ backgroundColor: item.color }"></span>
          <span>{{ item.label }}</span>
        </div>
      </div>

      <div class="grouped-chart-body">
        <div
          v-for="quarter in normalizedQuarters"
          :key="quarter.value"
          class="grouped-chart-group"
        >
          <div class="grouped-chart-bars">
            <div
              v-for="item in series"
              :key="`${quarter.value}-${item.key}`"
              class="grouped-chart-bar-wrap"
            >
              <span class="grouped-chart-value">{{ formatValue(item.quarters[quarter.value] ?? 0) }}</span>
              <div class="grouped-chart-plot">
                <div
                  class="grouped-chart-bar"
                  :style="{
                    height: `${barHeight(item.quarters[quarter.value] ?? 0)}%`,
                    backgroundColor: item.color,
                  }"
                ></div>
              </div>
            </div>
          </div>
          <strong class="grouped-chart-label">{{ quarter.label }}</strong>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  quarters: { type: Array, default: () => [] },
  series: { type: Array, default: () => [] },
  formatter: { type: Function, default: (value) => value },
});

const normalizedQuarters = computed(() => props.quarters || []);
const legendItems = computed(() => props.series.map((item) => ({ label: item.label, color: item.color })));
const maxValue = computed(() => {
  const values = props.series.flatMap((item) => normalizedQuarters.value.map((quarter) => Number(item.quarters?.[quarter.value] || 0)));
  return Math.max(...values, 1);
});

function barHeight(value) {
  return Math.max((Number(value || 0) / maxValue.value) * 100, value > 0 ? 4 : 0);
}

function formatValue(value) {
  return props.formatter(value);
}
</script>

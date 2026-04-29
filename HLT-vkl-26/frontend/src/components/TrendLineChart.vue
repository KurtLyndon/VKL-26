<template>
  <div class="chart-card">
    <div v-if="!points.length" class="inline-note">Chưa có dữ liệu xu hướng.</div>
    <div v-else class="trend-chart">
      <div class="trend-chart-grid">
        <div
          v-for="point in normalizedPoints"
          :key="point.label"
          class="trend-chart-point"
        >
          <span class="trend-chart-value">{{ point.count }}</span>
          <div class="trend-chart-dot-wrap">
            <div class="trend-chart-stem" :style="{ height: `${point.height}%` }"></div>
            <div class="trend-chart-dot"></div>
          </div>
          <strong class="trend-chart-label">{{ point.label }}</strong>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  points: { type: Array, default: () => [] },
});

const normalizedPoints = computed(() => {
  const maxCount = Math.max(...props.points.map((item) => item.count || 0), 1);
  return props.points.map((item) => ({
    ...item,
    height: ((item.count || 0) / maxCount) * 100,
  }));
});
</script>

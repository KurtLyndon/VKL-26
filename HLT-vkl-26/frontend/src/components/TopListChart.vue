<template>
  <div class="chart-card">
    <div v-if="!items.length" class="inline-note">Chưa có dữ liệu top vulnerability trong phạm vi lọc.</div>
    <div v-else class="top-list-chart">
      <div v-for="item in normalizedItems" :key="item.code" class="top-list-row">
        <div class="top-list-meta">
          <strong>{{ item.code }}</strong>
          <small>{{ item.title }}</small>
        </div>
        <div class="top-list-bar-wrap">
          <div class="top-list-bar" :style="{ width: `${item.width}%` }"></div>
        </div>
        <strong class="top-list-count">{{ item.count }}</strong>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  items: { type: Array, default: () => [] },
});

const normalizedItems = computed(() => {
  const maxCount = Math.max(...props.items.map((item) => item.count || 0), 1);
  return props.items.map((item) => ({
    ...item,
    width: ((item.count || 0) / maxCount) * 100,
  }));
});
</script>

<template>
  <article class="stat-card">
    <span class="stat-label">{{ label }}</span>
    <strong class="stat-value">{{ value }}</strong>
  </article>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], required: true },
});
</script>

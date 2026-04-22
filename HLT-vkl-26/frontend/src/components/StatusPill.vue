<template>
  <span class="status-pill" :class="`status-pill--${tone}`">{{ label }}</span>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  value: { type: String, default: "" },
});

const tone = computed(() => {
  const value = (props.value || "").toLowerCase();
  if (["completed", "online", "open", "success", "active"].includes(value)) return "success";
  if (["running", "queued", "manual", "cron", "interval", "info"].includes(value)) return "info";
  if (["failed", "offline", "critical", "high"].includes(value)) return "danger";
  if (["medium", "warning", "paused"].includes(value)) return "warning";
  return "neutral";
});

const label = computed(() => props.value || "-");
</script>

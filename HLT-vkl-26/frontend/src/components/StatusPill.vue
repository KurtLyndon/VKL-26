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
  if (["completed", "online", "success", "active", "resolved"].includes(value)) return "success";
  if (["running", "queued", "manual", "cron", "interval", "info"].includes(value)) return "info";
  if (["failed", "offline", "critical", "high", "confirmed", "reopened"].includes(value)) return "danger";
  if (["medium", "warning", "paused", "risk_accepted", "open"].includes(value)) return "warning";
  if (["in_progress"].includes(value)) return "info";
  if (["false_positive", "low", "info"].includes(value)) return "neutral";
  return "neutral";
});

const label = computed(() => props.value || "-");
</script>

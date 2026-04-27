<template>
  <router-view v-if="route.meta.public" :key="route.fullPath" />
  <AppShell v-else @navigate="scrollMainToTop">
    <router-view :key="route.fullPath" />
  </AppShell>
</template>

<script setup>
import { nextTick, watch } from "vue";
import { useRoute } from "vue-router";
import AppShell from "./components/AppShell.vue";

const route = useRoute();

async function scrollMainToTop() {
  await nextTick();
  const panel = document.querySelector(".main-panel");
  if (panel) {
    panel.scrollTo({ top: 0, behavior: "smooth" });
  } else {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
}

watch(
  () => route.fullPath,
  async () => {
    await scrollMainToTop();
  }
);
</script>

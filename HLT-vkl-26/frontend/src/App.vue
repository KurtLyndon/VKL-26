<template>
  <router-view v-if="route.meta.public" />
  <AppShell v-else>
    <router-view />
  </AppShell>
</template>

<script setup>
import { useRoute } from "vue-router";
import AppShell from "./components/AppShell.vue";

const route = useRoute();
</script>

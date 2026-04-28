<template>
  <div class="pagination-bar" v-if="totalItems > 0">
    <div class="pagination-meta">
      <span>{{ totalItems }} bản ghi</span>
    </div>

    <div class="pagination-controls">
      <label class="pagination-size">
        <span>Hiển thị</span>
        <select :value="pageSize" @change="$emit('update:pageSize', $event.target.value)">
          <option value="10">10</option>
          <option value="20">20</option>
          <option value="50">50</option>
          <option value="all">Toàn bộ</option>
        </select>
      </label>

      <div class="pagination-nav" v-if="pageSize !== 'all'">
        <button class="table-button" type="button" :disabled="currentPage <= 1" @click="$emit('previous')">
          Trước
        </button>
        <span>Trang {{ currentPage }}/{{ totalPages }}</span>
        <button class="table-button" type="button" :disabled="currentPage >= totalPages" @click="$emit('next')">
          Sau
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  currentPage: { type: Number, required: true },
  pageSize: { type: String, required: true },
  totalItems: { type: Number, required: true },
  totalPages: { type: Number, required: true },
});

defineEmits(["update:pageSize", "previous", "next"]);
</script>

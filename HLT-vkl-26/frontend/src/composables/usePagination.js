import { computed, ref, watch } from "vue";

export function usePagination(itemsRef) {
  const pageSize = ref("10");
  const currentPage = ref(1);

  const pageSizeNumber = computed(() => {
    if (pageSize.value === "all") {
      return Math.max(itemsRef.value.length, 1);
    }
    return Number(pageSize.value);
  });

  const totalItems = computed(() => itemsRef.value.length);
  const totalPages = computed(() => Math.max(1, Math.ceil(totalItems.value / pageSizeNumber.value)));

  const paginatedItems = computed(() => {
    if (pageSize.value === "all") {
      return itemsRef.value;
    }
    const start = (currentPage.value - 1) * pageSizeNumber.value;
    return itemsRef.value.slice(start, start + pageSizeNumber.value);
  });

  watch(pageSize, () => {
    currentPage.value = 1;
  });

  watch(totalPages, (value) => {
    if (currentPage.value > value) {
      currentPage.value = value;
    }
  });

  function goToPreviousPage() {
    if (currentPage.value > 1) {
      currentPage.value -= 1;
    }
  }

  function goToNextPage() {
    if (currentPage.value < totalPages.value) {
      currentPage.value += 1;
    }
  }

  return {
    currentPage,
    pageSize,
    paginatedItems,
    totalItems,
    totalPages,
    goToPreviousPage,
    goToNextPage,
  };
}

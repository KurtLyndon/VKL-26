<template>
  <div class="selection-dialog-trigger">
    <button class="ghost-button" type="button" @click="openDialog">
      {{ buttonLabel }}
    </button>
    <small class="selection-dialog-help">{{ selectedSummary }}</small>
  </div>

  <div v-if="isOpen" class="selection-drawer-overlay" @click.self="closeDialog">
    <aside class="selection-drawer">
      <div class="selection-dialog-header">
        <div class="panel-head">
          <h3>{{ title }}</h3>
          <span class="badge">{{ draftSelection.length }}/{{ maxSelected }}</span>
        </div>

        <div class="form-actions selection-dialog-actions selection-dialog-actions-top">
          <button class="ghost-button" type="button" @click="clearSelection">Bỏ chọn hết</button>
          <button class="ghost-button" type="button" @click="closeDialog">Đóng</button>
          <button class="primary-button" type="button" @click="applySelection">Áp dụng</button>
        </div>

        <label class="field-block">
          <span>Tìm kiếm</span>
          <input v-model="keyword" :placeholder="searchPlaceholder" />
        </label>
      </div>

      <div class="selection-dialog-list">
        <button
          v-for="option in filteredOptions"
          :key="optionKey(option)"
          type="button"
          class="selection-dialog-item"
          :class="{ active: isSelected(option) }"
          @click="toggleOption(option)"
        >
          <div>
            <strong>{{ optionLabel(option) }}</strong>
            <small v-if="optionDescription(option)">{{ optionDescription(option) }}</small>
          </div>
          <span>{{ isSelected(option) ? "Đã chọn" : "Chưa chọn" }}</span>
        </button>
      </div>
    </aside>
  </div>
</template>

<script setup>
import { computed, ref, watch } from "vue";

const props = defineProps({
  title: { type: String, required: true },
  options: { type: Array, default: () => [] },
  modelValue: { type: Array, default: () => [] },
  maxSelected: { type: Number, default: 5 },
  labelKey: { type: String, default: "label" },
  descriptionKey: { type: String, default: "description" },
  valueKey: { type: String, default: "value" },
  buttonLabel: { type: String, required: true },
  searchPlaceholder: { type: String, default: "Nhập từ khóa..." },
});

const emit = defineEmits(["update:modelValue"]);

const isOpen = ref(false);
const keyword = ref("");
const draftSelection = ref([]);

watch(
  () => props.modelValue,
  (value) => {
    draftSelection.value = [...value];
  },
  { immediate: true }
);

const selectedSummary = computed(() => {
  if (!props.modelValue.length) return "Chưa chọn mục nào";
  return `Đã chọn ${props.modelValue.length} mục`;
});

const filteredOptions = computed(() => {
  const normalizedKeyword = keyword.value.trim().toLowerCase();
  if (!normalizedKeyword) return props.options;
  return props.options.filter((option) => {
    const haystack = `${optionLabel(option)} ${optionDescription(option)}`.toLowerCase();
    return haystack.includes(normalizedKeyword);
  });
});

function optionLabel(option) {
  return option?.[props.labelKey] ?? option?.label ?? String(option);
}

function optionDescription(option) {
  return option?.[props.descriptionKey] ?? option?.description ?? "";
}

function optionValue(option) {
  return option?.[props.valueKey] ?? option?.value ?? option;
}

function optionKey(option) {
  return String(optionValue(option));
}

function isSelected(option) {
  return draftSelection.value.includes(optionValue(option));
}

function toggleOption(option) {
  const value = optionValue(option);
  const currentIndex = draftSelection.value.indexOf(value);
  if (currentIndex >= 0) {
    draftSelection.value.splice(currentIndex, 1);
    return;
  }
  if (draftSelection.value.length >= props.maxSelected) return;
  draftSelection.value.push(value);
}

function openDialog() {
  draftSelection.value = [...props.modelValue];
  keyword.value = "";
  isOpen.value = true;
}

function closeDialog() {
  isOpen.value = false;
}

function clearSelection() {
  draftSelection.value = [];
}

function applySelection() {
  emit("update:modelValue", [...draftSelection.value]);
  closeDialog();
}
</script>

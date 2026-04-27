export function compareTableValues(leftValue, rightValue) {
  const left = normalizeValue(leftValue);
  const right = normalizeValue(rightValue);

  if (left === right) return 0;
  if (left === null) return 1;
  if (right === null) return -1;

  if (typeof left === "number" && typeof right === "number") {
    return left - right;
  }

  return String(left).localeCompare(String(right), undefined, {
    numeric: true,
    sensitivity: "base",
  });
}

export function sortRows(rows, sortState, valueGetter = (row, key) => row?.[key]) {
  return [...rows].sort((left, right) => {
    const comparison = compareTableValues(
      valueGetter(left, sortState.key),
      valueGetter(right, sortState.key)
    );
    return sortState.direction === "asc" ? comparison : -comparison;
  });
}

export function nextSortState(currentState, key) {
  if (currentState.key === key) {
    return {
      key,
      direction: currentState.direction === "desc" ? "asc" : "desc",
    };
  }

  return { key, direction: "desc" };
}

export function sortIndicator(sortState, key) {
  if (sortState.key !== key) return "";
  return sortState.direction === "desc" ? " ↓" : " ↑";
}

function normalizeValue(value) {
  if (value === undefined || value === null || value === "") return null;
  if (typeof value === "boolean") return value ? 1 : 0;
  if (typeof value === "object") return JSON.stringify(value);
  return value;
}

import { computed, reactive } from "vue";

const TOKEN_KEY = "hlt_access_token";

const state = reactive({
  token: localStorage.getItem(TOKEN_KEY) || "",
  user: null,
  permissions: [],
  ready: false,
});

export function useAuthStore() {
  const isAuthenticated = computed(() => Boolean(state.token));

  function setSession(payload) {
    state.token = payload.access_token;
    state.user = payload.user;
    state.permissions = payload.permissions || [];
    state.ready = true;
    localStorage.setItem(TOKEN_KEY, state.token);
  }

  function hydrateSession(payload) {
    state.user = payload.user;
    state.permissions = payload.permissions || [];
    state.ready = true;
  }

  function clearSession() {
    state.token = "";
    state.user = null;
    state.permissions = [];
    state.ready = true;
    localStorage.removeItem(TOKEN_KEY);
  }

  function hasPermission(permission) {
    return state.permissions.includes(permission);
  }

  return {
    state,
    isAuthenticated,
    setSession,
    hydrateSession,
    clearSession,
    hasPermission,
  };
}

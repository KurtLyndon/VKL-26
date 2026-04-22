<template>
  <div class="login-shell">
    <section class="login-card">
      <p class="eyebrow">RBAC login</p>
      <h1>HLT VKL 26</h1>
      <p class="page-copy">
        Đăng nhập để truy cập dashboard, runtime control và màn hình quản lý quyền theo nhóm tài khoản.
      </p>

      <form class="resource-form" @submit.prevent="submitLogin">
        <label class="field-block">
          <span>username</span>
          <input v-model="form.username" type="text" autocomplete="username" />
        </label>

        <label class="field-block">
          <span>password</span>
          <input v-model="form.password" type="password" autocomplete="current-password" />
        </label>

        <div class="form-actions">
          <button class="primary-button" type="submit">Đăng nhập</button>
        </div>
      </form>

      <p class="inline-note" v-if="message">{{ message }}</p>
      <p class="inline-note">Tài khoản mặc định: `admin` / `Admin@123`</p>
    </section>
  </div>
</template>

<script setup>
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { login } from "../api/client";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const auth = useAuthStore();
const message = ref("");
const form = reactive({
  username: "admin",
  password: "Admin@123",
});

async function submitLogin() {
  try {
    const session = await login(form);
    auth.setSession(session);
    router.push("/");
  } catch (error) {
    message.value = error?.response?.data?.detail || "Đăng nhập thất bại.";
  }
}
</script>

import { ref, computed } from "vue";
import { defineStore } from "pinia";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export const useAuthStore = defineStore("auth", () => {
  const token = ref(localStorage.getItem("token") || null);
  const user = ref(JSON.parse(localStorage.getItem("user") || null));
  const userRoles = ref(JSON.parse(localStorage.getItem("userRoles") || null));

  function isTokenExpired() {
    if (!token.value) return true;
    try {
      const payload = JSON.parse(atob(token.value.split(".")[1]));
      return Date.now() >= payload.exp * 1000;
    } catch {
      return true;
    }
  }

  const isAuthenticated = computed(() => !!token.value && !isTokenExpired());
  const name = computed(() => user.value?.full_name || user.value?.email || "");

  function setAuth(tokenValue, userData) {
    token.value = tokenValue;
    user.value = userData;
    userRoles.value = Array.isArray(userData.role) ? userData.role : [userData.role];
    localStorage.setItem("token", tokenValue);
    localStorage.setItem("user", JSON.stringify(userData));
    localStorage.setItem("userRoles", JSON.stringify(userRoles.value));
  }

  function logout() {
    token.value = null;
    user.value = null;
    userRoles.value = null;
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    localStorage.removeItem("userRoles");
  }

  async function login(email, password) {
    const formData = new URLSearchParams();
    formData.append("username", email);
    formData.append("password", password);

    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Login failed");
    }

    const data = await res.json();
    setAuth(data.access_token, data.user);
    return data;
  }

  async function register(payload) {
    const res = await fetch(`${API_BASE}/users/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Registration failed");
    }

    return await res.json();
  }

  return {
    token,
    user,
    userRoles,
    isAuthenticated,
    isTokenExpired,
    name,
    login,
    register,
    logout,
    setAuth,
  };
});

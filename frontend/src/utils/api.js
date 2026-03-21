import axios from "axios";
import router from "@/router";
import { useAuthStore } from "@/stores/auth";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE,
});

/* -------------------------
   REQUEST INTERCEPTOR
   Attach JWT automatically
--------------------------*/
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

/* -------------------------
   RESPONSE INTERCEPTOR
   Handle 401 globally
--------------------------*/
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      const authStore = useAuthStore();

      authStore.logout();

      // Redirect to login (if not already there)
      if (router.currentRoute.value.path !== "/login") {
        router.push("/login");
      }
    }

    return Promise.reject(error);
  },
);

export default api;

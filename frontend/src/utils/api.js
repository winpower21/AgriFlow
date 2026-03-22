import axios from "axios";
import router from "@/router";
import { useAuthStore } from "@/stores/auth";
import { useNotificationStore } from '@/stores/notification'

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
  (response) => {
    // Only unwrap if response is an ApiResponse envelope (has 'data' key)
    if (response.data?.data !== undefined) {
      const notificationStore = useNotificationStore()
      if (response.data.message) {
        notificationStore.addNotification(response.data.message, response.data.type || 'success')
      }
      response.data = response.data.data  // unwrap envelope
    }
    return response
  },
  (error) => {
    const notificationStore = useNotificationStore()

    if (error.response?.status === 401) {
      const authStore = useAuthStore();

      authStore.logout();

      // Redirect to login (if not already there)
      if (router.currentRoute.value.path !== "/login") {
        router.push("/login");
      }
      return Promise.reject(error)
    }

    if (error.response) {
      const msg = error.response.data?.detail || 'Something went wrong'
      notificationStore.addNotification(msg, 'error')
    } else {
      notificationStore.addNotification('Network error', 'error')
    }

    return Promise.reject(error)
  },
);

export default api;

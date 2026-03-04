import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "../stores/auth";

const routes = [
    {
        path: "/",
        name: "home",
        component: () => import("@/views/HomeView.vue"),
        meta: { layout: "public" },
    },
    {
        path: "/login",
        name: "login",
        component: () => import("@/views/Login.vue"),
        meta: { layout: "public" },
    },
    {
        path: "/register",
        name: "register",
        component: () => import("@/views/Register.vue"),
        meta: { layout: "public" },
    },
    {
        path: "/dashboard",
        name: "dashboard",
        component: () => import("@/views/DashboardView.vue"),
        meta: { layout: "app", requiresAuth: true },
    },
    {
        path: "/manage-users",
        name: "manage-users",
        component: () => import("@/views/UserManagement.vue"),
        meta: { layout: "app", requiresAuth: true, requiresRole: "admin" },
    },
    {
        path: "/personnel",
        name: "personnel",
        component: () => import("@/views/Personnel.vue"),
        meta: { layout: "app", requiresAuth: true },
    },
    {
        path: "/plantations",
        name: "plantations",
        component: () => import("@/views/Plantations.vue"),
        meta: { layout: "app", requiresAuth: true },
    },
    {
        path: "/weather",
        name: "weather",
        component: () => import("@/views/WeatherView.vue"),
        meta: { layout: "app", requiresAuth: true },
    },
    {
        path: "/settings",
        name: "settings",
        component: () => import("@/views/Settings.vue"),
        meta: { layout: "app", requiresAuth: true },
    },
];

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes,
});

router.beforeEach((to) => {
    const token = localStorage.getItem("token");

    if (to.meta.requiresAuth && !token) {
        return { name: "login" };
    }

    if (to.meta.requiresRole) {
        const auth = useAuthStore();
        if (!auth.userRoles?.includes(to.meta.requiresRole)) {
            return { name: "dashboard" };
        }
    }
});

export default router;

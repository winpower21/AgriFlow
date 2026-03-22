import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { useNotificationStore } from '@/stores/notification'

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
    {
        path: "/vehicles",
        name: "vehicles",
        component: () => import("@/views/Vehicles.vue"),
        meta: { layout: "app", requiresAuth: true },
    },
    {
        path: "/consumables",
        name: "consumables",
        component: () => import("@/views/Consumables.vue"),
        meta: { layout: "app", requiresAuth: true },
    },
    {
        path: "/expenses",
        name: "expenses",
        component: () => import("@/views/Expenses.vue"),
        meta: { layout: "app", requiresAuth: true },
    },
    {
        path: "/batches",
        name: "batches",
        component: () => import("@/views/Batches.vue"),
        meta: { layout: "app", requiresAuth: true },
    },
    {
        path: "/batches/:id",
        name: "batch-detail",
        component: () => import("@/views/BatchDetail.vue"),
        meta: { layout: "app", requiresAuth: true },
    },
    {
        path: "/transformations",
        name: "transformations",
        component: () => import("@/views/Transformations.vue"),
        meta: { layout: "app", requiresAuth: true },
    },
    {
        path: "/transformations/:id",
        name: "transformation-detail",
        component: () => import("@/views/TransformationDetail.vue"),
        meta: { layout: "app", requiresAuth: true },
    },
    {
        path: "/sales",
        name: "sales",
        component: () => import("@/views/Sales.vue"),
        meta: { layout: "app", requiresAuth: true },
    },
    {
        path: "/reports",
        name: "reports",
        component: () => import("@/views/ReportsView.vue"),
        meta: { layout: "app", requiresAuth: true },
    },
];

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes,
});

router.beforeEach((to) => {
    const auth = useAuthStore();

    if (to.meta.requiresAuth) {
        if (!auth.isAuthenticated) {
            auth.logout(); // clear stale/expired token from localStorage
            return { name: "login" };
        }
    }

    if (to.meta.requiresRole) {
        if (!auth.userRoles?.includes(to.meta.requiresRole)) {
            return { name: "dashboard" };
        }
    }
});

router.beforeEach(() => {
  const notificationStore = useNotificationStore()
  notificationStore.clear()
})

export default router;

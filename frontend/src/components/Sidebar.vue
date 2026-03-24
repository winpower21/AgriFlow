<script setup>
import { computed } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const props = defineProps({
    expanded: { type: Boolean, default: false },
    mobileMenuExpanded: { type: Boolean, default: false },
});

const emit = defineEmits(["update:expanded", "update:mobileMenuExpanded"]);
const router = useRouter();
const auth = useAuthStore();

function toggle() {
    emit("update:expanded", !props.expanded);
}

function toggleMobileMenu() {
    // Implement toggleMobileMenu logic here
    emit("update:mobileMenuExpanded", !props.mobileMenuExpanded);
}

function handleLogout() {
    auth.logout();
    router.push({ name: "login" });
}

const allNavItems = [
    { icon: "bi-grid-1x2",       label: "Dashboard",   route: "dashboard" },
    { icon: "bi-tree",            label: "Plantations",  route: "plantations" },
    { icon: "bi-layers",          label: "Batches",         route: "batches" },
    { icon: "bi-arrow-repeat",    label: "Transformations", route: "transformations" },
    { icon: "bi-people",          label: "Personnel",    route: "personnel" },
    { icon: "bi-truck",           label: "Vehicles",     route: "vehicles" },
    { icon: "bi-box-seam",        label: "Consumables",  route: "consumables" },
    { icon: "bi-receipt",         label: "Expenses",     route: "expenses" },
    { icon: "bi-clipboard-check", label: "Approvals",    route: "approvals" },
    { icon: "bi-cart3",           label: "Sales",        route: "sales" },
    { icon: "bi-graph-up",        label: "Reports",      route: "reports" },
    { icon: "bi-cloud-sun",       label: "Weather",      route: "weather" },
    { icon: "bi-person-gear",     label: "Users",        route: "manage-users" },
];

const navItems = computed(() =>
    allNavItems.filter(item => item.label !== "Users" || auth.userRoles?.includes("admin"))
);

// Items shown in the mobile bottom bar (limited to 5 slots including more)
const mobileNavItems = computed(() => navItems.value.slice(0, 4));
const mobileSidebarItems = computed(() => navItems.value.slice(4));
</script>

<template>
    <!-- Desktop Sidebar -->
    <aside class="agri-sidebar d-none d-md-flex" :class="{ expanded }">
        <!-- Toggle -->
        <div class="sidebar-header">
            <button
                class="toggle-btn"
                @click="toggle"
                :title="expanded ? 'Collapse' : 'Expand'"
            >
                <i
                    class="bi"
                    :class="
                        expanded ? 'bi-arrow-bar-left' : 'bi-arrow-bar-right'
                    "
                ></i>
            </button>
            <Transition name="brand-fade">
                <span v-if="expanded" class="sidebar-brand">AgriFlow</span>
            </Transition>
        </div>

        <!-- Navigation -->
        <nav class="sidebar-nav">
            <RouterLink
                v-for="item in navItems"
                :key="item.label"
                :to="{ name: item.route }"
                class="sidebar-link"
                :title="!expanded ? item.label : undefined"
            >
                <span class="sidebar-icon">
                    <i class="bi" :class="item.icon"></i>
                </span>
                <Transition name="label-slide">
                    <span v-if="expanded" class="sidebar-label">{{
                        item.label
                    }}</span>
                </Transition>
            </RouterLink>
        </nav>

        <!-- Footer -->
        <div class="sidebar-footer">
            <RouterLink to="/settings" class="sidebar-link" title="Settings">
                <span class="sidebar-icon"><i class="bi bi-gear"></i></span>
                <Transition name="label-slide">
                    <span v-if="expanded" class="sidebar-label">Settings</span>
                </Transition>
            </RouterLink>
            <button
                class="sidebar-link logout-btn"
                @click="handleLogout"
                title="Log out"
            >
                <span class="sidebar-icon"
                    ><i class="bi bi-box-arrow-left"></i
                ></span>
                <Transition name="label-slide">
                    <span v-if="expanded" class="sidebar-label">Log out</span>
                </Transition>
            </button>
        </div>
    </aside>

    <!-- Mobile Bottom Bar -->
    <nav class="mobile-bottom-bar d-md-none">
        <RouterLink
            v-for="item in mobileNavItems"
            :key="item.label"
            :to="{ name: item.route }"
            class="bottom-bar-item"
        >
            <i class="bi" :class="item.icon"></i>
            <span class="bottom-bar-label">{{ item.label }}</span>
        </RouterLink>
        <button class="bottom-bar-item" @click="toggleMobileMenu">
            <i class="bi bi-box-arrow-left"></i>
            <span class="bottom-bar-label">Menu</span>
        </button>
    </nav>
    <!-- Overlay -->
    <div
        v-if="mobileMenuExpanded"
        class="overlay"
        @click="toggleMobileMenu"
    ></div>

    <!-- Sidebar -->
    <aside :class="['mobile-sidebar', { open: mobileMenuExpanded }]">
        <nav class="sidebar-nav">
            <RouterLink
                v-for="item in mobileSidebarItems"
                :key="item.label"
                :to="{ name: item.route }"
                class="sidebar-link"
                :title="item.label"
                @click="toggleMobileMenu"
            >
                <span class="sidebar-icon">
                    <i class="bi" :class="item.icon"></i>
                </span>
                <Transition name="label-slide">
                    <span class="sidebar-label">{{ item.label }}</span>
                </Transition>
            </RouterLink>
        </nav>
        <div class="mobile-sidebar-footer">
            <RouterLink to="/settings" class="sidebar-link" title="Settings">
                <span class="sidebar-icon"><i class="bi bi-gear"></i></span>
                <span class="sidebar-label">Settings</span>
            </RouterLink>
            <button
                class="sidebar-link logout-btn"
                @click="handleLogout"
                title="Log out"
            >
                <span class="sidebar-icon"
                    ><i class="bi bi-box-arrow-left"></i
                ></span>
                <Transition name="label-slide">
                    <span class="sidebar-label">Log out</span>
                </Transition>
            </button>
        </div>
        <div>
            <span
                class="circle close-btn"
                v-if="mobileMenuExpanded"
                @click="toggleMobileMenu"
                ><i class="bi bi-x-lg"></i
            ></span>
        </div>
    </aside>
</template>

<style scoped>
/* ---- Desktop Sidebar ---- */
.agri-sidebar {
    position: fixed;
    top: 12px;
    left: 12px;
    bottom: 12px;
    width: var(--sidebar-collapsed);
    background: var(--loam);
    border-radius: 16px;
    z-index: 1000;
    flex-direction: column;
    box-shadow: var(--shadow-float);
    transition: width var(--transition-smooth);
    overflow: hidden;
}

.agri-sidebar.expanded {
    width: var(--sidebar-expanded);
}

/* Header */
.sidebar-header {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 16px;
    min-height: 60px;
}

.toggle-btn {
    width: 38px;
    height: 38px;
    border: none;
    background: rgba(255, 255, 255, 0.08);
    color: var(--sage-light);
    border-radius: 10px;
    font-size: 1.1rem;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    transition: all var(--transition-fast);
}

.toggle-btn:hover {
    background: rgba(255, 255, 255, 0.14);
    color: var(--white);
}

.sidebar-brand {
    font-family: var(--font-display);
    font-size: 1.2rem;
    color: var(--parchment);
    white-space: nowrap;
    letter-spacing: -0.01em;
}

/* Navigation */
.sidebar-nav {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 2px;
    padding: 8px 10px;
    overflow-y: auto;
    overflow-x: hidden;
}

.sidebar-link {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 12px;
    border-radius: 10px;
    text-decoration: none;
    color: rgba(242, 237, 228, 0.6);
    font-size: 0.88rem;
    font-weight: 500;
    white-space: nowrap;
    transition: all var(--transition-fast);
    border: none;
    background: transparent;
    cursor: pointer;
    width: 100%;
    text-align: left;
}

.sidebar-link:hover {
    color: var(--parchment);
    background: rgba(255, 255, 255, 0.08);
}

.sidebar-link.router-link-active {
    color: var(--white);
    background: rgba(138, 154, 123, 0.25);
}

.sidebar-icon {
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.15rem;
    flex-shrink: 0;
}

.sidebar-label {
    overflow: hidden;
}

/* Footer */
.sidebar-footer {
    padding: 8px 10px 14px;
    display: flex;
    flex-direction: column;
    gap: 2px;
    border-top: 1px solid rgba(255, 255, 255, 0.07);
}

.logout-btn:hover {
    color: var(--sienna-light) !important;
    background: rgba(181, 105, 77, 0.12) !important;
}

/* Transitions */
.brand-fade-enter-active,
.brand-fade-leave-active {
    transition:
        opacity 0.25s var(--ease-out),
        transform 0.25s var(--ease-out);
}

.brand-fade-enter-from,
.brand-fade-leave-to {
    opacity: 0;
    transform: translateX(-6px);
}

.label-slide-enter-active,
.label-slide-leave-active {
    transition:
        opacity 0.2s var(--ease-out),
        transform 0.2s var(--ease-out);
}

.label-slide-enter-from,
.label-slide-leave-to {
    opacity: 0;
    transform: translateX(-4px);
}

/* ---- Mobile Bottom Bar ---- */
.mobile-bottom-bar {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    margin: 10px;
    border-radius: 20px;
    height: var(--sidebar-bottom-height, 64px);
    background: var(--loam);
    z-index: 1000;
    display: flex;
    align-items: center;
    justify-content: space-around;
    padding: 0 4px;
    box-shadow: 0 -4px 20px rgba(43, 45, 43, 0.15);
}

.bottom-bar-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 3px;
    flex: 1;
    padding: 8px 4px;
    color: rgba(242, 237, 228, 0.5);
    text-decoration: none;
    font-size: 1.15rem;
    border: none;
    background: transparent;
    cursor: pointer;
    transition: color var(--transition-fast);
    -webkit-tap-highlight-color: transparent;
}

.bottom-bar-item:hover,
.bottom-bar-item:active {
    color: var(--parchment);
}

.bottom-bar-item.router-link-active {
    color: var(--sage-light);
}

.bottom-bar-label {
    font-size: 0.65rem;
    font-weight: 500;
    letter-spacing: 0.02em;
    line-height: 1;
}

.mobile-sidebar {
    position: fixed;
    top: 10px;
    right: 0;
    width: 70vw;
    height: calc(100vh - 20px);
    background: var(--loam);
    transform: translateX(100%);
    transition: transform 0.3s ease;
    z-index: 1200;
    padding: 20px;
    margin: 0px;
    border-radius: 30px 0px 0px 30px;
    box-shadow:
        0 4px 8px 0 rgba(0, 0, 0, 0.2),
        0 6px 20px 0 rgba(0, 0, 0, 0.19);
}

.mobile-sidebar.open {
    transform: translateX(0);
}

.mobile-sidebar-footer {
    width: 100%;
    padding: 8px 0px 14px;
    display: flex;
    flex-direction: column;
    position: fixed;
    bottom: 0px;
    gap: 2px;
    border-top: 1px solid rgba(255, 255, 255, 0.07);
}

/* Overlay */
.overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.1);
    backdrop-filter: blur(4px);
    z-index: 1100;
}

.close-btn {
    position: absolute;
    bottom: 6px;
    left: calc(100% - 60px);
    width: 50px;
    height: 50px;
    border-radius: 50%;
    background: yellowgreen;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
}

.close-btn:hover {
    background: var(--sage-light);
}

@media (min-width: 768px) {
    .mobile-sidebar,
    .overlay,
    .close-btn,
    .mobile-sidebar-footer {
        display: none;
    }
}
</style>

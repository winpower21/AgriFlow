<script setup>
import { ref, onMounted, onUnmounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const scrolled = ref(false);
const mobileMenuOpen = ref(false);

function onScroll() {
    scrolled.value = window.scrollY > 8;
}

function handleHomeClick(e) {
    e.preventDefault();
    mobileMenuOpen.value = false;
    if (route.name === "home") {
        window.scrollTo({ top: 0, behavior: "smooth" });
    } else {
        router.push("/").then(() => {
            window.scrollTo({ top: 0, behavior: "smooth" });
        });
    }
}

function scrollToFeatures() {
    mobileMenuOpen.value = false;
    const el = document.getElementById("features");
    if (el) el.scrollIntoView({ behavior: "smooth" });
}

watch(route, () => {
    mobileMenuOpen.value = false;
});

onMounted(() => window.addEventListener("scroll", onScroll, { passive: true }));
onUnmounted(() => window.removeEventListener("scroll", onScroll));
</script>

<template>
    <nav class="agri-navbar" :class="{ scrolled, 'menu-open': mobileMenuOpen }">
        <div
            class="container-fluid px-3 px-sm-4 d-flex align-items-center justify-content-between h-100"
        >
            <!-- Brand -->
            <a
                href="/"
                class="brand d-flex align-items-center gap-2 text-decoration-none"
                @click="handleHomeClick"
            >
                <span
                    class="brand-icon d-flex align-items-center justify-content-center"
                >
                    <i class="bi bi-tree"></i>
                </span>
                <span class="brand-text">AgriFlow</span>
            </a>

            <!-- Desktop Navigation Links -->
            <div class="nav-links d-none d-md-flex align-items-center gap-1">
                <a
                    href="/"
                    class="nav-pill"
                    :class="{ active: route.name === 'home' }"
                    @click="handleHomeClick"
                >
                    Home
                </a>
                <a
                    v-if="route.name === 'home'"
                    href="#features"
                    class="nav-pill"
                    @click.prevent="scrollToFeatures"
                    >Features</a
                >
            </div>

            <!-- Desktop Actions -->
            <div class="d-none d-md-flex align-items-center gap-2">
                <template v-if="auth.isAuthenticated">
                    <RouterLink
                        to="/dashboard"
                        class="btn btn-sm btn-moss px-3 rounded-pill"
                    >
                        <i class="bi bi-grid-1x2 me-1"></i>Dashboard
                    </RouterLink>
                </template>
                <template v-else>
                    <RouterLink
                        v-if="route.name !== 'login'"
                        to="/login"
                        class="btn btn-sm btn-outline-moss px-3 rounded-pill"
                    >
                        Log in
                    </RouterLink>
                    <RouterLink
                        v-if="route.name !== 'register'"
                        to="/register"
                        class="btn btn-sm btn-moss px-3 rounded-pill"
                    >
                        Get started
                    </RouterLink>
                </template>
            </div>

            <!-- Mobile Hamburger -->
            <button
                class="hamburger d-md-none"
                @click="mobileMenuOpen = !mobileMenuOpen"
                :aria-expanded="mobileMenuOpen"
                aria-label="Toggle menu"
            >
                <i class="bi" :class="mobileMenuOpen ? 'bi-x-lg' : 'bi-list'"></i>
            </button>
        </div>

        <!-- Mobile Dropdown -->
        <Transition name="mobile-menu">
            <div v-if="mobileMenuOpen" class="mobile-menu d-md-none">
                <div class="mobile-menu-inner">
                    <a
                        href="/"
                        class="mobile-link"
                        :class="{ active: route.name === 'home' }"
                        @click="handleHomeClick"
                    >
                        <i class="bi bi-house me-2"></i>Home
                    </a>
                    <a
                        v-if="route.name === 'home'"
                        href="#features"
                        class="mobile-link"
                        @click.prevent="scrollToFeatures"
                    >
                        <i class="bi bi-stars me-2"></i>Features
                    </a>

                    <div class="mobile-divider"></div>

                    <template v-if="auth.isAuthenticated">
                        <RouterLink to="/dashboard" class="mobile-link" @click="mobileMenuOpen = false">
                            <i class="bi bi-grid-1x2 me-2"></i>Dashboard
                        </RouterLink>
                    </template>
                    <template v-else>
                        <RouterLink
                            v-if="route.name !== 'login'"
                            to="/login"
                            class="mobile-link"
                            @click="mobileMenuOpen = false"
                        >
                            <i class="bi bi-box-arrow-in-right me-2"></i>Log in
                        </RouterLink>
                        <RouterLink
                            v-if="route.name !== 'register'"
                            to="/register"
                            class="mobile-link highlight"
                            @click="mobileMenuOpen = false"
                        >
                            <i class="bi bi-person-plus me-2"></i>Get started
                        </RouterLink>
                    </template>
                </div>
            </div>
        </Transition>
    </nav>

    <!-- Mobile menu backdrop -->
    <Transition name="backdrop-fade">
        <div
            v-if="mobileMenuOpen"
            class="mobile-backdrop d-md-none"
            @click="mobileMenuOpen = false"
        ></div>
    </Transition>
</template>

<style scoped>
.agri-navbar {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: var(--navbar-height);
    z-index: 1000;
    background: rgba(242, 237, 228, 0.6);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border-bottom: 1px solid transparent;
    transition: all var(--transition-smooth);
}

.agri-navbar.scrolled,
.agri-navbar.menu-open {
    background: rgba(242, 237, 228, 0.85);
    border-bottom-color: var(--border-light);
    box-shadow: 0 1px 12px rgba(43, 45, 43, 0.05);
}

.brand {
    color: var(--loam);
}

.brand:hover {
    color: var(--moss);
}

.brand-icon {
    width: 34px;
    height: 34px;
    background: var(--moss);
    color: white;
    border-radius: 9px;
    font-size: 1.05rem;
}

.brand-text {
    font-family: var(--font-display);
    font-size: 1.3rem;
    letter-spacing: -0.01em;
}

.nav-pill {
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 0.88rem;
    font-weight: 500;
    color: var(--text-secondary);
    text-decoration: none;
    transition: all var(--transition-fast);
}

.nav-pill:hover {
    color: var(--text-primary);
    background: rgba(43, 45, 43, 0.05);
}

.nav-pill.active {
    color: var(--moss);
    background: var(--moss-faded);
}

/* Hamburger */
.hamburger {
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: none;
    background: transparent;
    color: var(--loam);
    font-size: 1.3rem;
    cursor: pointer;
    border-radius: 8px;
    transition: background var(--transition-fast);
}

.hamburger:hover {
    background: rgba(43, 45, 43, 0.06);
}

/* Mobile Menu */
.mobile-menu {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: rgba(242, 237, 228, 0.95);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-bottom: 1px solid var(--border-light);
    box-shadow: 0 8px 24px rgba(43, 45, 43, 0.08);
}

.mobile-menu-inner {
    padding: 8px 16px 16px;
    display: flex;
    flex-direction: column;
    gap: 2px;
}

.mobile-link {
    display: flex;
    align-items: center;
    padding: 12px 14px;
    border-radius: 10px;
    font-size: 0.92rem;
    font-weight: 500;
    color: var(--text-secondary);
    text-decoration: none;
    transition: all var(--transition-fast);
}

.mobile-link:hover,
.mobile-link.active {
    color: var(--text-primary);
    background: rgba(43, 45, 43, 0.05);
}

.mobile-link.active {
    color: var(--moss);
}

.mobile-link.highlight {
    color: var(--moss);
    font-weight: 600;
}

.mobile-divider {
    height: 1px;
    background: var(--border-light);
    margin: 6px 14px;
}

.mobile-backdrop {
    position: fixed;
    inset: 0;
    z-index: 999;
    background: rgba(43, 45, 43, 0.15);
}

/* Transitions */
.mobile-menu-enter-active,
.mobile-menu-leave-active {
    transition: opacity 0.25s var(--ease-out), transform 0.25s var(--ease-out);
}

.mobile-menu-enter-from,
.mobile-menu-leave-to {
    opacity: 0;
    transform: translateY(-8px);
}

.backdrop-fade-enter-active,
.backdrop-fade-leave-active {
    transition: opacity 0.25s var(--ease-out);
}

.backdrop-fade-enter-from,
.backdrop-fade-leave-to {
    opacity: 0;
}

@media (max-width: 767.98px) {
    .brand-icon {
        width: 30px;
        height: 30px;
        font-size: 0.95rem;
        border-radius: 8px;
    }

    .brand-text {
        font-size: 1.15rem;
    }
}
</style>

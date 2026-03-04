<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)
const showPassword = ref(false)

async function handleLogin() {
    error.value = ''
    loading.value = true
    try {
        await auth.login(email.value, password.value)
        router.push({ name: 'dashboard' })
    } catch (e) {
        error.value = e.message
    } finally {
        loading.value = false
    }
}
</script>

<template>
    <div class="auth-page">
        <div class="auth-bg"></div>
        <div class="container position-relative">
            <div class="row auth-row align-items-center justify-content-center">
                <div class="col-sm-10 col-md-7 col-lg-5 col-xl-4">
                    <div class="auth-card animate-fade-in-up">
                        <!-- Header -->
                        <div class="auth-header text-center">
                            <RouterLink to="/"
                                class="auth-brand d-inline-flex align-items-center gap-2 mb-4 text-decoration-none">
                                <span class="brand-icon">
                                    <i class="bi bi-tree"></i>
                                </span>
                                <span class="brand-text">AgriFlow</span>
                            </RouterLink>
                            <h2 class="auth-title">Welcome back</h2>
                            <p class="auth-subtitle">Sign in to your account to continue</p>
                        </div>

                        <!-- Error -->
                        <div v-if="error"
                            class="alert alert-danger d-flex align-items-center gap-2 py-2 animate-fade-in"
                            role="alert">
                            <i class="bi bi-exclamation-circle"></i>
                            <span class="small">{{ error }}</span>
                        </div>

                        <!-- Form -->
                        <form @submit.prevent="handleLogin" class="auth-form">
                            <div class="mb-3">
                                <label for="email" class="form-label">Email address</label>
                                <div class="input-group">
                                    <span class="input-group-text input-icon">
                                        <i class="bi bi-envelope"></i>
                                    </span>
                                    <input id="email" v-model="email" type="email" class="form-control"
                                        placeholder="you@example.com" required autocomplete="email" />
                                </div>
                            </div>

                            <div class="mb-4">
                                <div class="d-flex justify-content-between align-items-center">
                                    <label for="password" class="form-label mb-0">Password</label>
                                    <a href="#" class="forgot-link">Forgot?</a>
                                </div>
                                <div class="input-group mt-1">
                                    <span class="input-group-text input-icon">
                                        <i class="bi bi-lock"></i>
                                    </span>
                                    <input id="password" v-model="password" :type="showPassword ? 'text' : 'password'"
                                        class="form-control" placeholder="Enter your password" required
                                        autocomplete="current-password" />
                                    <button type="button" class="input-group-text input-icon toggle-pw"
                                        @click="showPassword = !showPassword" tabindex="-1">
                                        <i class="bi" :class="showPassword ? 'bi-eye-slash' : 'bi-eye'"></i>
                                    </button>
                                </div>
                            </div>

                            <button type="submit" class="btn btn-moss w-100 py-2 rounded-pill" :disabled="loading">
                                <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
                                {{ loading ? 'Signing in...' : 'Sign in' }}
                            </button>
                        </form>

                        <!-- Footer -->
                        <div class="auth-footer text-center">
                            <span class="text-secondary small">Don't have an account?</span>
                            <RouterLink to="/register" class="ms-1 small fw-semibold">Create one</RouterLink>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
.auth-page {
    position: relative;
    min-height: calc(100vh - var(--navbar-height));
    min-height: calc(100dvh - var(--navbar-height));
}

.auth-row {
    min-height: calc(100vh - var(--navbar-height));
    min-height: calc(100dvh - var(--navbar-height));
}

.auth-bg {
    position: fixed;
    inset: 0;
    background:
        radial-gradient(ellipse 60% 50% at 20% 80%, rgba(74, 103, 65, 0.06) 0%, transparent 50%),
        radial-gradient(ellipse 50% 40% at 80% 20%, rgba(181, 105, 77, 0.04) 0%, transparent 50%);
    pointer-events: none;
}

.auth-card {
    background: var(--bg-card);
    border: 1px solid var(--border-light);
    border-radius: 18px;
    padding: 40px 36px;
    box-shadow: var(--shadow-md);
}

.auth-header {
    margin-bottom: 28px;
}

.brand-icon {
    width: 36px;
    height: 36px;
    background: var(--moss);
    color: white;
    border-radius: 9px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.05rem;
}

.brand-text {
    font-family: var(--font-display);
    font-size: 1.25rem;
    color: var(--loam);
}

.auth-title {
    font-family: var(--font-display);
    font-size: 1.6rem;
    margin-bottom: 6px;
}

.auth-subtitle {
    color: var(--text-secondary);
    font-size: 0.9rem;
    margin-bottom: 0;
}

.auth-form {
    margin-bottom: 20px;
}

.input-icon {
    background: var(--white);
    border: 1.5px solid var(--border);
    border-right: none;
    color: var(--sage);
    font-size: 0.95rem;
}

.input-icon:last-child,
.toggle-pw {
    border-right: 1.5px solid var(--border);
    border-left: none;
    cursor: pointer;
}

.input-group .form-control {
    border-left: none;
    border-right: none;
}

.input-group .form-control:focus {
    box-shadow: none;
}

.input-group:focus-within .input-icon,
.input-group:focus-within .form-control {
    border-color: var(--sage);
}

.input-group:focus-within .input-icon {
    color: var(--moss);
}

.forgot-link {
    font-size: 0.8rem;
    color: var(--sienna);
    font-weight: 500;
}

.forgot-link:hover {
    color: var(--sienna-light);
}

.auth-footer {
    padding-top: 16px;
    border-top: 1px solid var(--border-light);
}

.auth-footer a {
    color: var(--moss);
}

.auth-footer a:hover {
    color: var(--moss-light);
}

.alert-danger {
    background: var(--sienna-faded);
    border: 1px solid rgba(181, 105, 77, 0.2);
    color: var(--sienna);
    border-radius: 10px;
}

@media (max-width: 575.98px) {
    .auth-card {
        padding: 28px 20px;
        border-radius: 14px;
    }

    .auth-title {
        font-size: 1.35rem;
    }

    .auth-header {
        margin-bottom: 20px;
    }
}
</style>

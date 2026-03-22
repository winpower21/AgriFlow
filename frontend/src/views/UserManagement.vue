<template>
    <div class="user-management">
        <!-- Page Header -->
        <div class="page-header">
            <div>
                <h2 class="page-title">User Management</h2>
                <p class="page-subtitle">
                    {{ allUsers.length }} registered
                    {{ allUsers.length === 1 ? "user" : "users" }}
                </p>
            </div>
        </div>

        <!-- User Table (desktop) -->
        <div class="table-wrapper d-none d-md-block animate-fade-in-up">
            <div class="table-scroll">
                <table class="user-table">
                    <thead>
                        <tr>
                            <th>User</th>
                            <th>Email</th>
                            <th>Role</th>
                            <th>Status</th>
                            <th>Verification</th>
                            <th class="th-actions">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr
                            v-for="(user, i) in allUsers"
                            :key="user.id"
                            class="user-row"
                            :style="{ animationDelay: `${i * 0.04}s` }"
                        >
                            <td>
                                <div class="user-identity">
                                    <span class="user-avatar">{{
                                        getInitials(user.full_name)
                                    }}</span>
                                    <span class="user-name">{{
                                        user.full_name || "Unnamed"
                                    }}</span>
                                </div>
                            </td>
                            <td class="user-email">{{ user.email }}</td>
                            <td>
                                <div class="role-chips">
                                    <span
                                        v-for="role in user.roles"
                                        :key="role.id"
                                        class="role-chip"
                                        :class="`role-${role.name}`"
                                    >
                                        {{ capitalize(role.name) }}
                                    </span>
                                    <span
                                        v-if="!user.roles?.length"
                                        class="role-chip role-none"
                                    >
                                        No role
                                    </span>
                                </div>
                            </td>
                            <td>
                                <span
                                    class="status-chip"
                                    :class="
                                        user.is_active
                                            ? 'status-active'
                                            : 'status-inactive'
                                    "
                                >
                                    <i
                                        class="bi"
                                        :class="
                                            user.is_active
                                                ? 'bi-check-circle-fill'
                                                : 'bi-pause-circle-fill'
                                        "
                                    ></i>
                                    {{ user.is_active ? "Active" : "Inactive" }}
                                </span>
                            </td>
                            <td>
                                <span
                                    class="status-chip"
                                    :class="
                                        user.is_verified
                                            ? 'status-verified'
                                            : 'status-unverified'
                                    "
                                >
                                    <i
                                        class="bi"
                                        :class="
                                            user.is_verified
                                                ? 'bi-patch-check-fill'
                                                : 'bi-shield-exclamation'
                                        "
                                    ></i>
                                    {{
                                        user.is_verified
                                            ? "Verified"
                                            : "Unverified"
                                    }}
                                </span>
                            </td>
                            <td>
                                <div class="action-group">
                                    <button
                                        class="btn-action btn-role"
                                        :disabled="
                                            user.roles[0].name === 'admin'
                                        "
                                        @click="openModal('role', user)"
                                        title="Change role"
                                    >
                                        <i class="bi bi-person-gear"></i>
                                    </button>
                                    <button
                                        class="btn-action btn-verify"
                                        :disabled="user.is_verified"
                                        @click="openModal('verify', user)"
                                        title="Verify user"
                                    >
                                        <i
                                            class="bi"
                                            :class="
                                                user.is_verified
                                                    ? 'bi-check-circle-fill'
                                                    : 'bi-x-circle-fill'
                                            "
                                        ></i>
                                    </button>
                                    <button
                                        class="btn-action btn-status"
                                        @click="openModal('status', user)"
                                        :title="
                                            user.is_active
                                                ? 'Deactivate user'
                                                : 'Activate user'
                                        "
                                        :disabled="
                                            user.roles[0].name === 'admin'
                                        "
                                    >
                                        <i
                                            class="bi"
                                            :class="
                                                user.is_active
                                                    ? 'bi-person-slash'
                                                    : 'bi-person-check'
                                            "
                                        ></i>
                                    </button>
                                </div>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
            <div v-if="loading" class="empty-state">
                <i class="bi bi-hourglass-split"></i>
                <p>Loading users...</p>
            </div>
            <div v-else-if="allUsers.length === 0" class="empty-state">
                <i class="bi bi-people"></i>
                <p>No users found</p>
            </div>
        </div>

        <!-- User Cards (mobile) -->
        <div class="d-md-none">
            <div
                v-for="(user, i) in allUsers"
                :key="user.id"
                class="user-card animate-fade-in-up"
                :style="{ animationDelay: `${i * 0.06}s` }"
            >
                <div class="user-card-header">
                    <div class="user-identity">
                        <span class="user-avatar">{{
                            getInitials(user.full_name)
                        }}</span>
                        <div>
                            <div class="user-name">
                                {{ user.full_name || "Unnamed" }}
                            </div>
                            <div class="user-email">{{ user.email }}</div>
                        </div>
                    </div>
                </div>
                <div class="user-card-body">
                    <div class="chip-row">
                        <span
                            v-for="role in user.roles"
                            :key="role.id"
                            class="role-chip"
                            :class="`role-${role.name}`"
                        >
                            {{ capitalize(role.name) }}
                        </span>
                        <span
                            v-if="!user.roles?.length"
                            class="role-chip role-none"
                        >
                            No role
                        </span>
                        <span
                            class="status-chip"
                            :class="
                                user.is_active
                                    ? 'status-active'
                                    : 'status-inactive'
                            "
                        >
                            <i
                                class="bi"
                                :class="
                                    user.is_active
                                        ? 'bi-check-circle-fill'
                                        : 'bi-pause-circle-fill'
                                "
                            ></i>
                            {{ user.is_active ? "Active" : "Inactive" }}
                        </span>
                        <span
                            class="status-chip"
                            :class="
                                user.is_verified
                                    ? 'status-verified'
                                    : 'status-unverified'
                            "
                        >
                            <i
                                class="bi"
                                :class="
                                    user.is_verified
                                        ? 'bi-patch-check-fill'
                                        : 'bi-shield-exclamation'
                                "
                            ></i>
                            {{ user.is_verified ? "Verified" : "Unverified" }}
                        </span>
                    </div>
                    <div class="action-group">
                        <button
                            class="btn-action btn-role"
                            :disabled="user.roles[0].name === 'admin'"
                            @click="openModal('role', user)"
                        >
                            <i class="bi bi-person-gear"></i>
                            Role
                        </button>
                        <button
                            class="btn-action btn-verify"
                            :disabled="user.is_verified"
                            @click="openModal('verify', user)"
                        >
                            <i class="bi bi-patch-check"></i>
                            Verify
                        </button>
                        <button
                            class="btn-action btn-status"
                            @click="openModal('status', user)"
                        >
                            <i
                                class="bi"
                                :class="
                                    user.is_active
                                        ? 'bi-person-slash'
                                        : 'bi-person-check'
                                "
                            ></i>
                            {{ user.is_active ? "Deactivate" : "Activate" }}
                        </button>
                    </div>
                </div>
            </div>
            <div v-if="loading" class="empty-state">
                <i class="bi bi-hourglass-split"></i>
                <p>Loading users...</p>
            </div>
            <div v-else-if="allUsers.length === 0" class="empty-state">
                <i class="bi bi-people"></i>
                <p>No users found</p>
            </div>
        </div>

        <!-- Confirmation Modal -->
        <div
            class="modal fade"
            id="confirmModal"
            tabindex="-1"
            aria-hidden="true"
            ref="modalRef"
        >
            <div class="modal-dialog modal-dialog-centered modal-sm">
                <div class="modal-content confirm-modal">
                    <div class="modal-body">
                        <div class="modal-icon" :class="modalIconClass">
                            <i class="bi" :class="modalIconName"></i>
                        </div>
                        <h5 class="modal-title">{{ modalTitle }}</h5>

                        <!-- Role change: radio options -->
                        <template v-if="modalAction === 'role'">
                            <p class="modal-desc">
                                Select a new role for
                                <strong>{{
                                    modalUser?.full_name || modalUser?.email
                                }}</strong>
                            </p>
                            <div class="role-options">
                                <label
                                    v-for="role in availableRoles"
                                    :key="role"
                                    class="role-option"
                                    :class="{
                                        selected: selectedRole === role,
                                        current: isCurrentRole(modalUser, role),
                                    }"
                                >
                                    <input
                                        type="radio"
                                        v-model="selectedRole"
                                        :value="role"
                                        :disabled="
                                            isCurrentRole(modalUser, role)
                                        "
                                    />
                                    <span class="role-option-dot"></span>
                                    <span class="role-option-label">
                                        <span class="role-option-name">{{
                                            capitalize(role)
                                        }}</span>
                                        <span
                                            v-if="
                                                isCurrentRole(modalUser, role)
                                            "
                                            class="role-option-current"
                                            >Current</span
                                        >
                                    </span>
                                </label>
                            </div>
                        </template>

                        <!-- Verify / Status descriptions -->
                        <template v-else>
                            <p class="modal-desc">
                                <template v-if="modalAction === 'verify'">
                                    Verify
                                    <strong>{{
                                        modalUser?.full_name || modalUser?.email
                                    }}</strong
                                    >? This will grant them full access.
                                </template>
                                <template v-else-if="modalUser?.is_active">
                                    Deactivate
                                    <strong>{{
                                        modalUser?.full_name || modalUser?.email
                                    }}</strong
                                    >? They will lose access until reactivated.
                                </template>
                                <template v-else>
                                    Activate
                                    <strong>{{
                                        modalUser?.full_name || modalUser?.email
                                    }}</strong
                                    >? They will regain access.
                                </template>
                            </p>
                        </template>
                    </div>
                    <div class="modal-footer">
                        <button
                            type="button"
                            class="btn-modal btn-modal-cancel"
                            data-bs-dismiss="modal"
                        >
                            Cancel
                        </button>
                        <button
                            type="button"
                            class="btn-modal btn-modal-confirm"
                            :class="modalConfirmClass"
                            :disabled="
                                modalAction === 'role' &&
                                (!selectedRole ||
                                    isCurrentRole(modalUser, selectedRole))
                            "
                            @click="confirmAction"
                        >
                            {{ modalConfirmLabel }}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from "vue";
import { Modal } from "bootstrap";
import api from "../utils/api";

const allUsers = ref([]);
const loading = ref(true);
const modalRef = ref(null);
const modalAction = ref("");
const modalUser = ref(null);
const selectedRole = ref("");
let bsModal = null;

const availableRoles = ["admin", "manager", "user"];

function capitalize(str) {
    if (!str) return "";
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function getInitials(name) {
    if (!name) return "?";
    return name
        .split(" ")
        .map((w) => w[0])
        .join("")
        .toUpperCase()
        .slice(0, 2);
}

function isCurrentRole(user, role) {
    return user?.roles?.some((r) => r.name === role) ?? false;
}

function getUserCurrentRole(user) {
    return user?.roles?.[0]?.name || "";
}

// --- Modal computed helpers ---
const modalTitle = computed(() => {
    if (modalAction.value === "role") return "Change Role";
    if (modalAction.value === "verify") return "Verify User";
    return modalUser.value?.is_active ? "Deactivate User" : "Activate User";
});

const modalIconClass = computed(() => {
    if (modalAction.value === "role") return "icon-role";
    if (modalAction.value === "verify") return "icon-verify";
    return "icon-status";
});

const modalIconName = computed(() => {
    if (modalAction.value === "role") return "bi-person-gear";
    if (modalAction.value === "verify") return "bi-patch-check";
    return modalUser.value?.is_active ? "bi-person-slash" : "bi-person-check";
});

const modalConfirmLabel = computed(() => {
    if (modalAction.value === "role") return "Change Role";
    if (modalAction.value === "verify") return "Verify";
    return modalUser.value?.is_active ? "Deactivate" : "Activate";
});

const modalConfirmClass = computed(() => {
    if (modalAction.value === "status" && modalUser.value?.is_active)
        return "btn-modal-danger";
    return "";
});

function openModal(action, user) {
    modalAction.value = action;
    modalUser.value = user;
    if (action === "role") {
        // Pre-select the first role that isn't the user's current role
        const current = getUserCurrentRole(user);
        const other = availableRoles.find((r) => r !== current);
        selectedRole.value = other || "";
    }
    if (!bsModal) {
        bsModal = new Modal(modalRef.value);
    }
    bsModal.show();
}

function confirmAction() {
    if (modalAction.value === "verify") {
        verifyUser(modalUser.value.id);
    } else if (modalAction.value === "status") {
        changeUserStatus(modalUser.value.id, !modalUser.value.is_active);
    } else if (modalAction.value === "role") {
        changeUserRole(modalUser.value.id, selectedRole.value);
    }
    bsModal.hide();
}

const getUsers = async () => {
    try {
        const response = await api.get("/users/all");
        // const response = await request("/users/all");
        allUsers.value = response.data;
        return;
    } catch (error) {
        console.error(error);
        return;
    } finally {
        loading.value = false;
    }
};

const verifyUser = async (userId) => {
    try {
        const response = await api.put(`/users/update/${userId}`, {
            is_verified: true,
        });
        // const response = await request(
        //     `/users/user/${userId}`,
        //     (data = { body: { is_verified: true } }),
        // );
        const updatedUser = response.data;
        const index = allUsers.value.findIndex((user) => user.id === userId);
        if (index !== -1) {
            allUsers.value[index] = updatedUser;
        }
    } catch (error) {
        console.error(error);
    }
};

const changeUserStatus = async (userId, status) => {
    try {
        const response = await api.put(`/users/update/${userId}`, {
            is_active: status,
        });
        // const response = await request(`/users/update/${userId}`);
        const updatedUser = response.data;
        const index = allUsers.value.findIndex((user) => user.id === userId);
        if (index !== -1) {
            allUsers.value[index] = updatedUser;
        }
    } catch (error) {
        console.error(error);
    }
};

const changeUserRole = async (userId, roleName) => {
    try {
        const response = await api.put(`/users/change-role/${userId}`, {
            role: roleName,
        });
        const index = allUsers.value.findIndex((user) => user.id === userId);
        if (index !== -1) {
            allUsers.value[index] = response.data;
        }
    } catch (error) {
        console.error(error);
    }
};

onMounted(async () => {
    await getUsers();
});

onBeforeUnmount(() => {
    bsModal?.dispose();
});
</script>

<style scoped>
/* ---- Page Layout ---- */
.user-management {
    max-width: 100vw;
}

.page-header {
    margin-bottom: 28px;
}

.page-title {
    font-family: var(--font-display);
    font-size: 1.6rem;
    color: var(--text-primary);
    margin: 0 0 4px;
}

.page-subtitle {
    font-size: 0.85rem;
    color: var(--text-secondary);
    margin: 0;
    letter-spacing: 0.01em;
}

/* ---- Table ---- */
.table-wrapper {
    background: var(--bg-card);
    border: 1px solid var(--border-light);
    border-radius: 14px;
    overflow: hidden;
    box-shadow: var(--shadow-sm);
}

.table-scroll {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
}

.user-table {
    width: 100%;
    min-width: 720px;
    border-collapse: collapse;
}

.user-table thead th {
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--text-secondary);
    padding: 14px 18px;
    border-bottom: 1px solid var(--border-light);
    background: var(--parchment-deep);
    text-align: left;
    white-space: nowrap;
}

.th-actions {
    text-align: right !important;
    padding-right: 22px !important;
}

.user-table tbody tr {
    transition: background var(--transition-fast);
}

.user-table tbody tr:hover {
    background: rgba(138, 154, 123, 0.06);
}

.user-table tbody td {
    padding: 12px 18px;
    border-bottom: 1px solid var(--border-light);
    vertical-align: middle;
    font-size: 0.88rem;
}

.user-table tbody tr:last-child td {
    border-bottom: none;
}

/* ---- User Identity ---- */
.user-identity {
    display: flex;
    align-items: center;
    gap: 12px;
}

.user-avatar {
    width: 36px;
    height: 36px;
    border-radius: 10px;
    background: var(--moss-faded);
    color: var(--moss);
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.02em;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.user-name {
    font-weight: 600;
    font-size: 0.9rem;
    color: var(--text-primary);
    white-space: nowrap;
}

.user-email {
    font-size: 0.82rem;
    color: var(--text-secondary);
}

/* ---- Role Chips ---- */
.role-chips {
    display: flex;
    gap: 5px;
    flex-wrap: wrap;
}

.role-chip {
    display: inline-flex;
    align-items: center;
    font-size: 0.72rem;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 20px;
    letter-spacing: 0.02em;
    text-transform: capitalize;
}

.role-admin {
    background: rgba(181, 105, 77, 0.12);
    color: var(--sienna);
}

.role-manager {
    background: rgba(196, 163, 90, 0.14);
    color: #8a6f2a;
}

.role-user {
    background: rgba(138, 154, 123, 0.14);
    color: var(--sage);
}

.role-none {
    background: rgba(107, 109, 107, 0.1);
    color: var(--text-secondary);
}

/* ---- Status Chips ---- */
.status-chip {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 20px;
    letter-spacing: 0.01em;
    white-space: nowrap;
}

.status-chip i {
    font-size: 0.7rem;
}

.status-active {
    background: rgba(74, 103, 65, 0.1);
    color: var(--moss);
}

.status-inactive {
    background: rgba(181, 105, 77, 0.1);
    color: var(--sienna);
}

.status-verified {
    background: rgba(74, 103, 65, 0.1);
    color: var(--moss);
}

.status-unverified {
    background: rgba(196, 163, 90, 0.12);
    color: #9a7d2e;
}

/* ---- Action Buttons ---- */
.action-group {
    display: flex;
    align-items: center;
    gap: 6px;
    justify-content: flex-end;
}

.btn-action {
    width: 34px;
    height: 34px;
    border-radius: 9px;
    border: 1.5px solid var(--border);
    background: transparent;
    color: var(--text-secondary);
    font-size: 1rem;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    transition: all var(--transition-fast);
}

.btn-action:hover:not(:disabled) {
    border-color: var(--moss);
    color: var(--moss);
    background: rgba(74, 103, 65, 0.06);
}

.btn-role:hover:not(:disabled) {
    border-color: var(--harvest);
    color: #8a6f2a;
    background: rgba(196, 163, 90, 0.08);
}

.btn-status:hover:not(:disabled) {
    border-color: var(--sienna);
    color: var(--sienna);
    background: rgba(181, 105, 77, 0.06);
}

.btn-action:disabled {
    opacity: 0.3;
    cursor: not-allowed;
}

/* ---- Mobile Cards ---- */
.user-card {
    background: var(--bg-card);
    border: 1px solid var(--border-light);
    border-radius: 14px;
    margin-bottom: 12px;
    box-shadow: var(--shadow-sm);
    overflow: hidden;
}

.user-card-header {
    padding: 16px 16px 0;
}

.user-card-body {
    padding: 12px 16px 16px;
}

.chip-row {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-bottom: 14px;
}

.user-card .action-group {
    justify-content: flex-start;
}

.user-card .btn-action {
    width: auto;
    height: auto;
    padding: 7px 14px;
    font-size: 0.8rem;
    gap: 6px;
    font-weight: 500;
}

/* ---- Empty State ---- */
.empty-state {
    text-align: center;
    padding: 48px 20px;
    color: var(--text-secondary);
}

.empty-state i {
    font-size: 2.4rem;
    opacity: 0.3;
    margin-bottom: 10px;
    display: block;
}

.empty-state p {
    font-size: 0.9rem;
    margin: 0;
}

/* ---- Confirmation Modal ---- */
.confirm-modal {
    border: none;
    border-radius: 16px;
    box-shadow: var(--shadow-lg);
    overflow: hidden;
    background: var(--bg-card);
}

.confirm-modal .modal-body {
    padding: 28px 24px 16px;
    text-align: center;
}

.modal-icon {
    width: 48px;
    height: 48px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.3rem;
    margin: 0 auto 16px;
}

.icon-verify {
    background: rgba(74, 103, 65, 0.1);
    color: var(--moss);
}

.icon-status {
    background: rgba(181, 105, 77, 0.1);
    color: var(--sienna);
}

.icon-role {
    background: rgba(196, 163, 90, 0.12);
    color: #8a6f2a;
}

.modal-title {
    font-family: var(--font-display);
    font-size: 1.15rem;
    margin: 0 0 8px;
    color: var(--text-primary);
}

.modal-desc {
    font-size: 0.85rem;
    color: var(--text-secondary);
    margin: 0;
    line-height: 1.5;
}

/* ---- Role Selection (inside modal) ---- */
.role-options {
    display: flex;
    flex-direction: column;
    gap: 6px;
    margin-top: 16px;
    text-align: left;
}

.role-option {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 14px;
    border-radius: 10px;
    border: 1.5px solid var(--border-light);
    cursor: pointer;
    transition: all var(--transition-fast);
    background: transparent;
}

.role-option:hover:not(.current) {
    border-color: var(--sage);
    background: rgba(138, 154, 123, 0.04);
}

.role-option.selected:not(.current) {
    border-color: var(--moss);
    background: rgba(74, 103, 65, 0.06);
}

.role-option.current {
    opacity: 0.45;
    cursor: not-allowed;
}

.role-option input[type="radio"] {
    display: none;
}

.role-option-dot {
    width: 16px;
    height: 16px;
    border-radius: 50%;
    border: 2px solid var(--border);
    flex-shrink: 0;
    transition: all var(--transition-fast);
    position: relative;
}

.role-option.selected:not(.current) .role-option-dot {
    border-color: var(--moss);
}

.role-option.selected:not(.current) .role-option-dot::after {
    content: "";
    position: absolute;
    top: 3px;
    left: 3px;
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--moss);
}

.role-option-label {
    display: flex;
    align-items: center;
    gap: 8px;
    flex: 1;
}

.role-option-name {
    font-size: 0.88rem;
    font-weight: 600;
    color: var(--text-primary);
}

.role-option-current {
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--text-secondary);
    background: rgba(107, 109, 107, 0.1);
    padding: 2px 7px;
    border-radius: 4px;
}

/* ---- Modal Footer ---- */
.confirm-modal .modal-footer {
    border-top: 1px solid var(--border-light);
    padding: 12px 24px;
    display: flex;
    gap: 8px;
    justify-content: flex-end;
}

.btn-modal {
    border: none;
    border-radius: 9px;
    padding: 8px 18px;
    font-size: 0.85rem;
    font-weight: 600;
    font-family: var(--font-body);
    cursor: pointer;
    transition: all var(--transition-fast);
}

.btn-modal:disabled {
    opacity: 0.4;
    cursor: not-allowed;
}

.btn-modal-cancel {
    background: transparent;
    color: var(--text-secondary);
}

.btn-modal-cancel:hover {
    background: var(--parchment-deep);
    color: var(--text-primary);
}

.btn-modal-confirm {
    background: var(--moss);
    color: var(--white);
}

.btn-modal-confirm:hover:not(:disabled) {
    background: var(--moss-light);
}

.btn-modal-danger {
    background: var(--sienna);
}

.btn-modal-danger:hover:not(:disabled) {
    background: var(--sienna-light);
}

/* ---- Responsive ---- */
@media (max-width: 767.98px) {
    .user-management {
        max-width: 100%;
    }

    .page-title {
        font-size: 1.35rem;
    }

    .page-header {
        margin-bottom: 20px;
    }
}
</style>

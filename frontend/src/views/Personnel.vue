<template>
    <div class="personnel-management">
        <!-- Page Header -->
        <div class="page-header">
            <div>
                <h2 class="page-title">Personnel</h2>
                <p class="page-subtitle">
                    {{ personnel.length }} registered
                    {{ personnel.length === 1 ? "worker" : "workers" }}
                </p>
            </div>
            <button v-if="isAdmin" class="btn-add" @click="openAddModal">
                <i class="bi bi-plus-lg"></i>
                <span>Add Personnel</span>
            </button>
        </div>

        <!-- Desktop Table -->
        <div class="table-wrapper d-none d-md-block animate-fade-in-up">
            <div class="table-scroll">
                <table class="personnel-table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Wage Type</th>
                            <th>Rate</th>
                            <th>Phone</th>
                            <th>Status</th>
                            <th v-if="isAdmin" class="th-actions">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr
                            v-for="(p, i) in personnel"
                            :key="p.id"
                            class="personnel-row"
                            :style="{ animationDelay: `${i * 0.04}s` }"
                        >
                            <td>
                                <div class="person-identity">
                                    <span class="person-avatar">
                                        <img
                                            v-if="p.photo"
                                            :src="photoUrl(p.photo)"
                                            class="avatar-img"
                                            :alt="p.name"
                                        />
                                        <template v-else>{{
                                            getInitials(p.name)
                                        }}</template>
                                    </span>
                                    <div>
                                        <span class="person-name">{{
                                            p.name
                                        }}</span>
                                        <span v-if="isPendingSalary(p.id)" class="salary-due-dot" title="Salary due">
                                            <i class="bi bi-circle-fill" style="color: #e74c3c; font-size: 8px;"></i>
                                        </span>
                                        <span
                                            v-if="p.address"
                                            class="person-address"
                                            >{{ p.address }}</span
                                        >
                                    </div>
                                </div>
                            </td>
                            <td>
                                <span
                                    class="wage-chip"
                                    :class="wageClass(p.wage_type?.name)"
                                >
                                    {{ p.wage_type?.name || "—" }}
                                </span>
                            </td>
                            <td class="rate-cell">
                                {{ formatRate(p.current_rate) }}
                            </td>
                            <td class="phone-cell">
                                {{ p.phone || "—" }}
                            </td>
                            <td>
                                <span
                                    class="status-chip"
                                    :class="
                                        p.is_active
                                            ? 'status-active'
                                            : 'status-inactive'
                                    "
                                >
                                    <i
                                        class="bi"
                                        :class="
                                            p.is_active
                                                ? 'bi-check-circle-fill'
                                                : 'bi-pause-circle-fill'
                                        "
                                    ></i>
                                    {{ p.is_active ? "Active" : "Inactive" }}
                                </span>
                            </td>
                            <td v-if="isAdmin">
                                <div class="action-group">
                                    <button
                                        v-if="isPendingSalary(p.id)"
                                        class="btn-action btn-pay-salary"
                                        title="Pay Salary"
                                        @click="paySalary(p)"
                                    >
                                        <i class="bi bi-cash-coin"></i>
                                    </button>
                                    <button
                                        class="btn-action btn-edit"
                                        title="Edit"
                                        @click="openEditModal(p)"
                                    >
                                        <i class="bi bi-pencil"></i>
                                    </button>
                                    <button
                                        class="btn-action btn-delete"
                                        title="Delete"
                                        @click="openDeleteModal(p)"
                                    >
                                        <i class="bi bi-trash3"></i>
                                    </button>
                                </div>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
            <div v-if="loading" class="empty-state">
                <i class="bi bi-hourglass-split"></i>
                <p>Loading personnel...</p>
            </div>
            <div v-else-if="personnel.length === 0" class="empty-state">
                <i class="bi bi-people"></i>
                <p>No personnel found</p>
            </div>
        </div>

        <!-- Mobile Cards -->
        <div class="d-md-none">
            <div
                v-for="(p, i) in personnel"
                :key="p.id"
                class="person-card animate-fade-in-up"
                :style="{ animationDelay: `${i * 0.06}s` }"
            >
                <div class="person-card-header">
                    <div class="person-identity">
                        <span class="person-avatar">
                            <img
                                v-if="p.photo"
                                :src="photoUrl(p.photo)"
                                class="avatar-img"
                                :alt="p.name"
                            />
                            <template v-else>{{
                                getInitials(p.name)
                            }}</template>
                        </span>
                        <div>
                            <div class="person-name">
                                {{ p.name }}
                                <span v-if="isPendingSalary(p.id)" class="salary-due-dot" title="Salary due">
                                    <i class="bi bi-circle-fill" style="color: #e74c3c; font-size: 8px;"></i>
                                </span>
                            </div>
                            <div class="person-address" v-if="p.address">
                                {{ p.address }}
                            </div>
                        </div>
                    </div>
                </div>
                <div class="person-card-body">
                    <div class="chip-row">
                        <span
                            class="wage-chip"
                            :class="wageClass(p.wage_type?.name)"
                        >
                            {{ p.wage_type?.name || "—" }}
                        </span>
                        <span class="rate-chip">
                            {{ formatRate(p.current_rate) }}
                        </span>
                        <span
                            class="status-chip"
                            :class="
                                p.is_active
                                    ? 'status-active'
                                    : 'status-inactive'
                            "
                        >
                            <i
                                class="bi"
                                :class="
                                    p.is_active
                                        ? 'bi-check-circle-fill'
                                        : 'bi-pause-circle-fill'
                                "
                            ></i>
                            {{ p.is_active ? "Active" : "Inactive" }}
                        </span>
                    </div>
                    <div v-if="p.phone" class="phone-row">
                        <i class="bi bi-telephone"></i>
                        {{ p.phone }}
                    </div>
                    <div v-if="isAdmin" class="action-group">
                        <button
                            v-if="isPendingSalary(p.id)"
                            class="btn-action btn-pay-salary"
                            title="Pay Salary"
                            @click="paySalary(p)"
                        >
                            <i class="bi bi-cash-coin"></i>
                            Pay Salary
                        </button>
                        <button
                            class="btn-action btn-edit"
                            @click="openEditModal(p)"
                        >
                            <i class="bi bi-pencil"></i>
                            Edit
                        </button>
                        <button
                            class="btn-action btn-delete"
                            @click="openDeleteModal(p)"
                        >
                            <i class="bi bi-trash3"></i>
                            Delete
                        </button>
                    </div>
                </div>
            </div>
            <div v-if="loading" class="empty-state">
                <i class="bi bi-hourglass-split"></i>
                <p>Loading personnel...</p>
            </div>
            <div v-else-if="personnel.length === 0" class="empty-state">
                <i class="bi bi-people"></i>
                <p>No personnel found</p>
            </div>
        </div>

        <!-- Add / Edit Modal -->
        <div
            class="modal fade"
            id="formModal"
            tabindex="-1"
            aria-hidden="true"
            ref="formModalRef"
        >
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content form-modal">
                    <div class="modal-body">
                        <!-- Photo picker -->
                        <div class="photo-picker-wrapper">
                            <div
                                class="photo-picker"
                                @click="photoInputRef.click()"
                            >
                                <img
                                    v-if="form.photoPreview"
                                    :src="form.photoPreview"
                                    class="photo-preview"
                                    alt="Preview"
                                />
                                <span v-else class="photo-placeholder">
                                    <i class="bi bi-camera"></i>
                                </span>
                                <button
                                    v-if="form.photoPreview"
                                    type="button"
                                    class="photo-clear"
                                    @click.stop="clearPhoto"
                                >
                                    <i class="bi bi-x"></i>
                                </button>
                            </div>
                            <input
                                ref="photoInputRef"
                                type="file"
                                accept="image/jpeg,image/png,image/webp"
                                class="d-none"
                                @change="onPhotoSelected"
                            />
                        </div>
                        <h5 class="modal-title">
                            {{ isEditing ? "Edit Personnel" : "Add Personnel" }}
                        </h5>

                        <form
                            class="personnel-form"
                            @submit.prevent="handleFormSubmit"
                        >
                            <!-- Name -->
                            <div class="form-group">
                                <label class="form-label" for="pName"
                                    >Full Name</label
                                >
                                <input
                                    id="pName"
                                    v-model="form.name"
                                    type="text"
                                    class="form-control"
                                    placeholder="e.g. Rajesh Kumar"
                                    required
                                />
                            </div>

                            <!-- Wage Type & Rate (side by side) -->
                            <div class="form-row">
                                <div class="form-group flex-1">
                                    <label class="form-label" for="pWageType"
                                        >Wage Type</label
                                    >
                                    <select
                                        id="pWageType"
                                        v-model="form.wage_type_id"
                                        class="form-select"
                                        required
                                    >
                                        <option disabled :value="null">
                                            Select type
                                        </option>
                                        <option
                                            v-for="wt in wageTypes"
                                            :key="wt.id"
                                            :value="wt.id"
                                        >
                                            {{ wt.name }}
                                        </option>
                                    </select>
                                </div>
                                <div class="form-group flex-1">
                                    <label class="form-label" for="pRate"
                                        >Current Rate</label
                                    >
                                    <input
                                        id="pRate"
                                        v-model.number="form.current_rate"
                                        type="number"
                                        step="0.01"
                                        min="0"
                                        class="form-control"
                                        placeholder="0.00"
                                        required
                                    />
                                </div>
                            </div>

                            <!-- Phone -->
                            <div class="form-group">
                                <label class="form-label" for="pPhone"
                                    >Phone</label
                                >
                                <input
                                    id="pPhone"
                                    v-model="form.phone"
                                    type="tel"
                                    class="form-control"
                                    :class="{ 'is-invalid': phoneError }"
                                    placeholder="e.g. 9876543210"
                                    maxlength="10"
                                    inputmode="numeric"
                                    pattern="[1-9][0-9]{9}"
                                    @input="validatePhone"
                                />
                                <div v-if="phoneError" class="invalid-feedback">{{ phoneError }}</div>
                            </div>

                            <!-- Address -->
                            <div class="form-group">
                                <label class="form-label" for="pAddress"
                                    >Address</label
                                >
                                <textarea
                                    id="pAddress"
                                    v-model="form.address"
                                    class="form-control"
                                    rows="2"
                                    placeholder="Village, district..."
                                ></textarea>
                            </div>

                            <!-- Salary Payment Date (MONTHLY only) -->
                            <div v-if="selectedWageType?.calculation_method === 'MONTHLY'" class="form-group">
                                <label class="form-label" for="pPayDate">Salary Payment Date (Day of Month) *</label>
                                <input
                                    id="pPayDate"
                                    v-model.number="form.salary_payment_date"
                                    type="number"
                                    class="form-control"
                                    min="1"
                                    max="28"
                                    placeholder="e.g. 1 (1st of month)"
                                />
                                <small class="form-text text-muted">Day 1-28 when monthly salary is due</small>
                            </div>

                            <!-- Active toggle (edit only) -->
                            <div v-if="isEditing" class="form-group">
                                <label class="toggle-row">
                                    <span class="toggle-label">Active</span>
                                    <span
                                        class="toggle-switch"
                                        :class="{ on: form.is_active }"
                                        @click="
                                            form.is_active = !form.is_active
                                        "
                                    >
                                        <span class="toggle-knob"></span>
                                    </span>
                                </label>
                            </div>
                        </form>
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
                            @click="handleFormSubmit"
                            :disabled="!isFormValid"
                        >
                            {{ isEditing ? "Save Changes" : "Add Personnel" }}
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Delete Confirmation Modal -->
        <div
            class="modal fade"
            id="deleteModal"
            tabindex="-1"
            aria-hidden="true"
            ref="deleteModalRef"
        >
            <div class="modal-dialog modal-dialog-centered modal-sm">
                <div class="modal-content confirm-modal">
                    <div class="modal-body">
                        <div class="modal-icon icon-delete">
                            <i class="bi bi-trash3"></i>
                        </div>
                        <h5 class="modal-title">Delete Personnel</h5>
                        <p class="modal-desc">
                            Remove
                            <strong>{{ deleteTarget?.name }}</strong
                            >? This action cannot be undone.
                        </p>
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
                            class="btn-modal btn-modal-confirm btn-modal-danger"
                            @click="confirmDelete"
                        >
                            Delete
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
import { useReportsStore } from "@/stores/reports";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
const isAdmin = computed(() => auth.userRoles?.includes("admin"));

const reportsStore = useReportsStore();

// ── Reactive State ──────────────────────────────────

const loading = ref(true);
const personnel = ref([]);
const wageTypes = ref([]);

const formModalRef = ref(null);
const deleteModalRef = ref(null);
let bsFormModal = null;
let bsDeleteModal = null;

const isEditing = ref(false);
const editingId = ref(null);
const deleteTarget = ref(null);

const form = ref(getEmptyForm());

function getEmptyForm() {
    return {
        name: "",
        wage_type_id: null,
        current_rate: null,
        phone: "",
        address: "",
        is_active: true,
        salary_payment_date: null,
        photoFile: null, // File object from picker
        photoPreview: null, // object URL for local preview
    };
}

const photoInputRef = ref(null);

const isFormValid = computed(() => {
    return (
        form.value.name.trim() !== "" &&
        form.value.wage_type_id !== null &&
        form.value.current_rate !== null &&
        form.value.current_rate >= 0
    );
});

const phoneError = ref('')

function validatePhone() {
    const p = form.value.phone
    if (!p) {
        phoneError.value = ''
        return true
    }
    if (!/^\d+$/.test(p)) {
        phoneError.value = 'Phone must contain only digits'
        return false
    }
    if (p.startsWith('0')) {
        phoneError.value = 'Phone must not start with 0'
        return false
    }
    if (p.length !== 10) {
        phoneError.value = 'Phone must be exactly 10 digits'
        return false
    }
    phoneError.value = ''
    return true
}

const selectedWageType = computed(() => {
    return wageTypes.value.find(w => w.id === form.value.wage_type_id) || null
})

const pendingSalaries = ref([])

async function fetchPendingSalaries() {
    try {
        const res = await api.get('/personnel/pending-salaries')
        pendingSalaries.value = res.data
    } catch (e) {
        console.error('Failed to fetch pending salaries:', e)
    }
}

function isPendingSalary(personnelId) {
    return pendingSalaries.value.some(ps => ps.personnel_id === personnelId)
}

function getPendingSalaryInfo(personnelId) {
    return pendingSalaries.value.find(ps => ps.personnel_id === personnelId)
}

async function paySalary(p) {
    if (!confirm(`Pay monthly salary of ₹${p.current_rate} to ${p.name}?`)) return
    try {
        await api.post(`/personnel/${p.id}/pay-salary`)
        await fetchPendingSalaries()
    } catch (e) {
        alert(e.response?.data?.detail || 'Failed to pay salary')
    }
}

// ── Helpers ─────────────────────────────────────────

function getInitials(name) {
    if (!name) return "?";
    return name
        .split(" ")
        .map((w) => w[0])
        .join("")
        .toUpperCase()
        .slice(0, 2);
}

function formatRate(rate) {
    if (rate == null) return "—";
    return `₹${Number(rate).toLocaleString("en-IN", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    })}`;
}

function wageClass(typeName) {
    if (!typeName) return "wage-none";
    const lower = typeName.toLowerCase();
    if (lower.includes("daily") || lower === "daily") return "wage-daily";
    if (lower.includes("kg") || lower === "per_kg") return "wage-perkg";
    return "wage-other";
}

// ── Photo Helpers ────────────────────────────────────

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

function photoUrl(path) {
    return path ? `${API_BASE}/uploads/${path}` : null;
}

function onPhotoSelected(event) {
    const file = event.target.files[0];
    if (!file) return;
    // Revoke previous object URL to avoid memory leaks
    if (form.value.photoPreview) URL.revokeObjectURL(form.value.photoPreview);
    form.value.photoFile = file;
    form.value.photoPreview = URL.createObjectURL(file);
}

function clearPhoto() {
    if (form.value.photoPreview) URL.revokeObjectURL(form.value.photoPreview);
    form.value.photoFile = null;
    form.value.photoPreview = null;
    if (photoInputRef.value) photoInputRef.value.value = "";
}

// ── Modal Handlers ──────────────────────────────────

function openAddModal() {
    isEditing.value = false;
    editingId.value = null;
    form.value = getEmptyForm();
    if (!bsFormModal) bsFormModal = new Modal(formModalRef.value);
    bsFormModal.show();
}

function openEditModal(p) {
    isEditing.value = true;
    editingId.value = p.id;
    form.value = {
        name: p.name,
        wage_type_id: p.wage_type?.id ?? p.wage_type_id,
        current_rate: Number(p.current_rate),
        phone: p.phone || "",
        address: p.address || "",
        is_active: p.is_active,
        salary_payment_date: p.salary_payment_date || null,
        photoFile: null,
        photoPreview: p.photo ? photoUrl(p.photo) : null,
    };
    if (!bsFormModal) bsFormModal = new Modal(formModalRef.value);
    bsFormModal.show();
}

function openDeleteModal(p) {
    deleteTarget.value = p;
    if (!bsDeleteModal) bsDeleteModal = new Modal(deleteModalRef.value);
    bsDeleteModal.show();
}

// ── API Functions ───────────────────────────────────

async function fetchPersonnel() {
    try {
        const response = await api.get("/personnel/");
        personnel.value = response.data;
    } catch (error) {
        console.error("Failed to fetch personnel:", error);
    }
}

async function fetchWageTypes() {
    try {
        const response = await api.get("/personnel/wage-types");
        wageTypes.value = response.data;
    } catch (error) {
        console.error("Failed to fetch wage types:", error);
    }
}

async function handleFormSubmit() {
    if (!isFormValid.value) return;
    if (form.value.phone && !validatePhone()) return;

    if (isEditing.value) {
        await updatePersonnel(editingId.value, { ...form.value });
    } else {
        await addPersonnel({ ...form.value });
    }
    bsFormModal.hide();
}

async function addPersonnel(data) {
    try {
        const fd = new FormData();
        fd.append("name", data.name);
        fd.append("wage_type_id", data.wage_type_id);
        fd.append("current_rate", data.current_rate);
        if (data.phone) fd.append("phone", data.phone);
        if (data.address) fd.append("address", data.address);
        if (data.salary_payment_date != null) fd.append("salary_payment_date", data.salary_payment_date);
        if (data.photoFile) fd.append("photo", data.photoFile);

        const response = await api.post("/personnel/", fd);
        reportsStore.invalidate("personnel");
        personnel.value.push(response.data);
    } catch (error) {
        console.error("Failed to add personnel:", error);
    }
}

async function updatePersonnel(id, data) {
    try {
        const fd = new FormData();
        if (data.name !== undefined) fd.append("name", data.name);
        if (data.wage_type_id !== undefined)
            fd.append("wage_type_id", data.wage_type_id);
        if (data.current_rate !== undefined)
            fd.append("current_rate", data.current_rate);
        if (data.phone !== undefined) fd.append("phone", data.phone);
        if (data.address !== undefined) fd.append("address", data.address);
        if (data.is_active !== undefined)
            fd.append("is_active", data.is_active);
        if (data.salary_payment_date != null) fd.append("salary_payment_date", data.salary_payment_date);
        if (data.photoFile) fd.append("photo", data.photoFile);

        const response = await api.put(`/personnel/${id}`, fd);
        reportsStore.invalidate("personnel");
        const idx = personnel.value.findIndex((p) => p.id === id);
        if (idx !== -1) personnel.value[idx] = response.data;
    } catch (error) {
        console.error("Failed to update personnel:", error);
    }
}

async function confirmDelete() {
    if (!deleteTarget.value) return;
    await deletePersonnel(deleteTarget.value.id);
    bsDeleteModal.hide();
}

async function deletePersonnel(id) {
    try {
        await api.delete(`/personnel/${id}`);
        reportsStore.invalidate("personnel");
        personnel.value = personnel.value.filter((p) => p.id !== id);
    } catch (error) {
        console.error("Failed to delete personnel:", error);
    }
}

// ── Lifecycle ───────────────────────────────────────

onMounted(async () => {
    await Promise.all([fetchPersonnel(), fetchWageTypes(), fetchPendingSalaries()]);
    loading.value = false;
});

onBeforeUnmount(() => {
    if (form.value.photoPreview && form.value.photoFile) {
        URL.revokeObjectURL(form.value.photoPreview);
    }
    bsFormModal?.dispose();
    bsDeleteModal?.dispose();
});
</script>

<style scoped>
/* ── Page Layout ────────────────────────────── */
.personnel-management {
    max-width: 100vw;
}

.page-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 28px;
    gap: 16px;
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

.btn-add {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    padding: 9px 18px;
    border: none;
    border-radius: 10px;
    background: var(--moss);
    color: var(--white);
    font-family: var(--font-body);
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    transition: all var(--transition-fast);
    white-space: nowrap;
}

.btn-add:hover {
    background: var(--moss-light);
    box-shadow: 0 4px 12px var(--moss-faded);
}

.btn-add i {
    font-size: 1rem;
}

/* ── Table ──────────────────────────────────── */
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

.personnel-table {
    width: 100%;
    min-width: 700px;
    border-collapse: collapse;
}

.personnel-table thead th {
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

.personnel-table tbody tr {
    transition: background var(--transition-fast);
}

.personnel-table tbody tr:hover {
    background: rgba(138, 154, 123, 0.06);
}

.personnel-table tbody td {
    padding: 12px 18px;
    border-bottom: 1px solid var(--border-light);
    vertical-align: middle;
    font-size: 0.88rem;
}

.personnel-table tbody tr:last-child td {
    border-bottom: none;
}

/* ── Person Identity ────────────────────────── */
.person-identity {
    display: flex;
    align-items: center;
    gap: 12px;
}

.person-avatar {
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

.avatar-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    border-radius: 10px;
}

.person-name {
    font-weight: 600;
    font-size: 0.9rem;
    color: var(--text-primary);
    white-space: nowrap;
    display: block;
}

.person-address {
    font-size: 0.78rem;
    color: var(--text-secondary);
    display: block;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 220px;
}

/* ── Wage Chips ─────────────────────────────── */
.wage-chip {
    display: inline-flex;
    align-items: center;
    font-size: 0.72rem;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 20px;
    letter-spacing: 0.02em;
}

.wage-daily {
    background: rgba(74, 103, 65, 0.1);
    color: var(--moss);
}

.wage-perkg {
    background: rgba(196, 163, 90, 0.14);
    color: #8a6f2a;
}

.wage-other {
    background: rgba(138, 154, 123, 0.14);
    color: var(--sage);
}

.wage-none {
    background: rgba(107, 109, 107, 0.1);
    color: var(--text-secondary);
}

/* ── Rate ────────────────────────────────────── */
.rate-cell {
    font-weight: 600;
    font-variant-numeric: tabular-nums;
    color: var(--text-primary);
}

.rate-chip {
    display: inline-flex;
    align-items: center;
    font-size: 0.78rem;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 20px;
    background: rgba(181, 105, 77, 0.1);
    color: var(--sienna);
    font-variant-numeric: tabular-nums;
}

.phone-cell {
    font-size: 0.84rem;
    color: var(--text-secondary);
    font-variant-numeric: tabular-nums;
}

/* ── Status Chips ───────────────────────────── */
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

/* ── Action Buttons ─────────────────────────── */
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

.btn-edit:hover:not(:disabled) {
    border-color: var(--harvest);
    color: #8a6f2a;
    background: rgba(196, 163, 90, 0.08);
}

.btn-delete:hover:not(:disabled) {
    border-color: var(--sienna);
    color: var(--sienna);
    background: rgba(181, 105, 77, 0.06);
}

.btn-pay-salary {
    border-color: #e74c3c;
    color: #e74c3c;
    background: rgba(231, 76, 60, 0.06);
}

.btn-pay-salary:hover:not(:disabled) {
    border-color: #c0392b;
    color: #c0392b;
    background: rgba(231, 76, 60, 0.12);
}

.salary-due-dot {
    display: inline-flex;
    align-items: center;
    margin-left: 4px;
    animation: pulse 1.5s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}

.btn-action:disabled {
    opacity: 0.3;
    cursor: not-allowed;
}

/* ── Mobile Cards ───────────────────────────── */
.person-card {
    background: var(--bg-card);
    border: 1px solid var(--border-light);
    border-radius: 14px;
    margin-bottom: 12px;
    box-shadow: var(--shadow-sm);
    overflow: hidden;
}

.person-card-header {
    padding: 16px 16px 0;
}

.person-card-body {
    padding: 12px 16px 16px;
}

.chip-row {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-bottom: 10px;
}

.phone-row {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.82rem;
    color: var(--text-secondary);
    margin-bottom: 14px;
}

.phone-row i {
    font-size: 0.78rem;
}

.person-card .action-group {
    justify-content: flex-start;
}

.person-card .btn-action {
    width: auto;
    height: auto;
    padding: 7px 14px;
    font-size: 0.8rem;
    gap: 6px;
    font-weight: 500;
}

/* ── Empty State ────────────────────────────── */
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

/* ── Form Modal ─────────────────────────────── */
.form-modal {
    border: none;
    border-radius: 16px;
    box-shadow: var(--shadow-lg);
    overflow: hidden;
    background: var(--bg-card);
}

.form-modal .modal-body {
    padding: 28px 24px 8px;
    text-align: center;
}

.personnel-form {
    text-align: left;
    margin-top: 20px;
}

.form-group {
    margin-bottom: 16px;
}

.form-row {
    display: flex;
    gap: 12px;
}

.flex-1 {
    flex: 1;
}

/* ── Toggle Switch ──────────────────────────── */
.toggle-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    cursor: pointer;
}

.toggle-label {
    font-weight: 500;
    font-size: 0.85rem;
    color: var(--text-secondary);
    letter-spacing: 0.02em;
}

.toggle-switch {
    width: 44px;
    height: 24px;
    border-radius: 12px;
    background: var(--border);
    position: relative;
    transition: background var(--transition-fast);
    cursor: pointer;
}

.toggle-switch.on {
    background: var(--moss);
}

.toggle-knob {
    position: absolute;
    top: 3px;
    left: 3px;
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: var(--white);
    box-shadow: var(--shadow-sm);
    transition: transform var(--transition-fast);
}

.toggle-switch.on .toggle-knob {
    transform: translateX(20px);
}

/* ── Confirm / Delete Modal ─────────────────── */
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

.icon-add {
    background: rgba(74, 103, 65, 0.1);
    color: var(--moss);
}

.icon-edit {
    background: rgba(196, 163, 90, 0.12);
    color: #8a6f2a;
}

.icon-delete {
    background: rgba(181, 105, 77, 0.1);
    color: var(--sienna);
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

/* ── Modal Footer ───────────────────────────── */
.form-modal .modal-footer,
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

/* ── Photo Picker ───────────────────────────── */
.photo-picker-wrapper {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-bottom: 4px;
}

.photo-picker {
    position: relative;
    width: 72px;
    height: 72px;
    border-radius: 50%;
    background: var(--parchment-deep);
    border: 2px dashed var(--border);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    transition: border-color var(--transition-fast);
    margin: 0 auto 12px;
}

.photo-picker:hover {
    border-color: var(--sage);
}

.photo-preview {
    width: 100%;
    height: 100%;
    object-fit: cover;
    border-radius: 50%;
}

.photo-placeholder i {
    font-size: 1.6rem;
    color: var(--text-secondary);
}

.photo-clear {
    position: absolute;
    top: 2px;
    right: 2px;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: var(--sienna);
    color: var(--white);
    border: none;
    font-size: 0.7rem;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    padding: 0;
    line-height: 1;
}

/* ── Responsive ─────────────────────────────── */
@media (max-width: 767.98px) {
    .personnel-management {
        max-width: 100%;
    }

    .page-title {
        font-size: 1.35rem;
    }

    .page-header {
        margin-bottom: 20px;
    }

    .btn-add {
        padding: 8px 14px;
        font-size: 0.8rem;
    }

    .btn-add span {
        display: none;
    }

    .btn-add i {
        font-size: 1.15rem;
    }

    .form-row {
        flex-direction: column;
        gap: 0;
    }
}
</style>

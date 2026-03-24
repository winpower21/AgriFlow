<template>
    <div class="expenses-page">
        <!-- ══════════════════════════════════════════════ -->
        <!-- PAGE HEADER                                    -->
        <!-- ══════════════════════════════════════════════ -->
        <div class="page-header animate-fade-in-up">
            <div>
                <h2 class="page-title">Expenses</h2>
                <p class="page-subtitle">
                    Track and manage farm expenditures across categories
                </p>
            </div>
            <div class="header-actions">
                <template v-if="isAdmin">
                    <button class="btn-add" @click="openExpenseModal(null)">
                        <i class="bi bi-plus-lg"></i>
                        <span>Add Expense</span>
                    </button>
                </template>
                <template v-else>
                    <button
                        class="btn-add btn-add-secondary"
                        @click="openRequestModal"
                    >
                        <i class="bi bi-send"></i>
                        <span>Submit Request</span>
                    </button>
                </template>
            </div>
        </div>

        <!-- ══════════════════════════════════════════════ -->
        <!-- ADMIN: PENDING APPROVALS BANNER               -->
        <!-- ══════════════════════════════════════════════ -->
        <div v-if="isAdmin && pendingApprovalCount > 0" class="approval-banner">
            <i class="bi bi-exclamation-triangle"></i>
            {{ pendingApprovalCount }} pending expense approval{{ pendingApprovalCount !== 1 ? 's' : '' }}
            <router-link :to="{ name: 'approvals', query: { type: 'EXPENSE' } }" class="banner-link">
                View in Approvals <i class="bi bi-arrow-right"></i>
            </router-link>
        </div>

        <!-- ══════════════════════════════════════════════ -->
        <!-- TOOLBAR (search + filters button)             -->
        <!-- ══════════════════════════════════════════════ -->
        <div class="toolbar animate-fade-in-up animate-delay-2">
            <div class="search-wrap">
                <i class="bi bi-search search-icon"></i>
                <input
                    v-model="filters.search"
                    type="text"
                    class="form-control search-input"
                    placeholder="Search by description..."
                    @input="fetchExpenses"
                />
            </div>

            <!-- Filters button + floating popover -->
            <div class="filter-btn-wrap" ref="filterBtnWrap">
                <button
                    class="btn-filters"
                    :class="{ active: filterPanelOpen }"
                    @click="filterPanelOpen = !filterPanelOpen"
                >
                    <i class="bi bi-sliders"></i>
                    Filters
                    <span v-if="activeFilterCount > 0" class="filter-badge">{{
                        activeFilterCount
                    }}</span>
                </button>

                <div v-if="filterPanelOpen" class="filter-popover">
                    <div class="fp-header">
                        <span class="fp-title">Filters</span>
                        <button
                            v-if="hasActiveFilters"
                            class="fp-clear"
                            @click="clearFilters"
                        >
                            Clear all
                        </button>
                    </div>

                    <div class="fp-field">
                        <label class="fp-label">Category</label>
                        <select
                            v-model="filters.category_id"
                            class="form-select form-select-sm"
                            @change="fetchExpenses"
                        >
                            <option :value="null">All Categories</option>
                            <option
                                v-for="cat in categories"
                                :key="cat.id"
                                :value="cat.id"
                            >
                                {{ cat.name }}
                            </option>
                        </select>
                    </div>

                    <div class="fp-field">
                        <label class="fp-label">Plantation</label>
                        <select
                            v-model="filters.plantation_id"
                            class="form-select form-select-sm"
                            @change="fetchExpenses"
                        >
                            <option :value="null">All Plantations</option>
                            <option
                                v-for="pl in plantations"
                                :key="pl.id"
                                :value="pl.id"
                            >
                                {{ pl.name }}
                            </option>
                        </select>
                    </div>

                    <div class="fp-field">
                        <label class="fp-label">Vehicle</label>
                        <select
                            v-model="filters.vehicle_id"
                            class="form-select form-select-sm"
                            @change="fetchExpenses"
                        >
                            <option :value="null">All Vehicles</option>
                            <option
                                v-for="veh in vehicles"
                                :key="veh.id"
                                :value="veh.id"
                            >
                                {{ veh.number }}
                            </option>
                        </select>
                    </div>

                    <div class="fp-field">
                        <label class="fp-label">From date</label>
                        <input
                            v-model="filters.from_date"
                            type="date"
                            class="form-control form-control-sm"
                            @change="fetchExpenses"
                        />
                    </div>

                    <div class="fp-field">
                        <label class="fp-label">To date</label>
                        <input
                            v-model="filters.to_date"
                            type="date"
                            class="form-control form-control-sm"
                            @change="fetchExpenses"
                        />
                    </div>
                </div>
            </div>
        </div>

        <!-- ══════════════════════════════════════════════ -->
        <!-- EXPENSE LIST                                   -->
        <!-- ══════════════════════════════════════════════ -->
        <div class="content-panel animate-fade-in-up animate-delay-3">
            <div v-if="loading" class="empty-state">
                <i class="bi bi-hourglass-split"></i>
                <p>Loading expenses...</p>
            </div>
            <div v-else-if="expenses.length === 0" class="empty-state">
                <i class="bi bi-receipt"></i>
                <p>
                    {{
                        hasActiveFilters
                            ? "No expenses match your filters"
                            : "No expenses recorded yet"
                    }}
                </p>
            </div>

            <TransitionGroup v-else name="list" tag="div" class="expenses-list">
                <div v-for="exp in expenses" :key="exp.id" class="expense-row">
                    <div class="expense-date">{{ formatDate(exp.date) }}</div>
                    <div class="expense-main">
                        <span class="badge-category">{{
                            categoryName(exp.category_id)
                        }}</span>
                        <span class="expense-amount"
                            >₹{{ formatMoney(exp.amount) }}</span
                        >
                        <span
                            v-if="exp.description"
                            class="expense-description"
                        >
                            {{ exp.description }}
                        </span>
                    </div>
                    <div class="expense-tags">
                        <span
                            v-if="exp.plantation_id"
                            class="expense-tag tag-plantation"
                            :title="plantationName(exp.plantation_id)"
                        >
                            <i class="bi bi-geo-alt"></i>
                            {{ plantationName(exp.plantation_id) }}
                        </span>
                        <span
                            v-if="exp.vehicle_id"
                            class="expense-tag tag-vehicle"
                            :title="vehicleNumber(exp.vehicle_id)"
                        >
                            <i class="bi bi-truck"></i>
                            {{ vehicleNumber(exp.vehicle_id) }}
                        </span>
                    </div>
                    <div v-if="isAdmin" class="expense-actions">
                        <button
                            class="btn-action btn-edit"
                            title="Edit"
                            @click="openExpenseModal(exp)"
                        >
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button
                            class="btn-action btn-delete"
                            title="Delete"
                            @click="promptDelete(exp)"
                        >
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </div>
            </TransitionGroup>
        </div>

        <!-- ══════════════════════════════════════════════ -->
        <!-- NON-ADMIN: MY REQUESTS SECTION                 -->
        <!-- ══════════════════════════════════════════════ -->
        <div
            v-if="!isAdmin && myRequests.length > 0"
            class="my-requests-panel animate-fade-in-up animate-delay-3"
        >
            <div class="my-requests-header">
                <i class="bi bi-clock-history"></i>
                <span>My Expense Requests</span>
            </div>

            <div
                v-for="req in myRequests"
                :key="req.id"
                class="my-request-card"
            >
                <div class="my-request-top">
                    <div class="my-request-meta">
                        <span class="my-request-date">
                            <i class="bi bi-calendar3"></i>
                            {{ formatDate(req.created_at) }}
                        </span>
                        <span class="my-request-count">
                            {{ req.payload?.length || 0 }} item{{
                                (req.payload?.length || 0) !== 1 ? "s" : ""
                            }}
                        </span>
                    </div>
                    <span
                        class="status-chip"
                        :class="statusChipClass(req.status)"
                    >
                        {{ req.status }}
                    </span>
                </div>

                <div class="my-request-items">
                    <div
                        v-for="(item, idx) in req.payload"
                        :key="idx"
                        class="my-request-item"
                    >
                        <span class="mri-date">{{
                            formatDate(item.data?.date)
                        }}</span>
                        <span class="mri-amount"
                            >₹{{ formatMoney(item.data?.amount) }}</span
                        >
                        <span class="mri-category">{{
                            categoryName(item.data?.category_id)
                        }}</span>
                        <span v-if="item.data?.description" class="mri-desc">
                            {{ item.data.description }}
                        </span>
                        <span v-if="item.data?.plantation_id" class="mri-tag">
                            <i class="bi bi-geo-alt"></i>
                            {{ plantationName(item.data.plantation_id) }}
                        </span>
                        <span v-if="item.data?.vehicle_id" class="mri-tag">
                            <i class="bi bi-truck"></i>
                            {{ vehicleNumber(item.data.vehicle_id) }}
                        </span>
                        <span
                            class="status-chip status-chip-sm"
                            :class="statusChipClass(item.status || 'PENDING')"
                        >
                            {{ item.status || "PENDING" }}
                        </span>
                        <span v-if="item.rejection_note" class="mri-note">
                            <i class="bi bi-chat-text"></i>
                            {{ item.rejection_note }}
                        </span>
                    </div>
                </div>

                <div v-if="req.notes" class="my-request-notes">
                    <i class="bi bi-sticky"></i>
                    {{ req.notes }}
                </div>
            </div>
        </div>

        <!-- ══════════════════════════════════════════════ -->
        <!-- MODALS                                         -->
        <!-- ══════════════════════════════════════════════ -->

        <!-- Admin: Add/Edit Expense Modal -->
        <div
            class="modal fade"
            id="expenseModal"
            tabindex="-1"
            aria-hidden="true"
            ref="expenseModalRef"
        >
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content form-modal">
                    <div class="modal-body">
                        <div
                            class="modal-icon"
                            :class="editingExpense ? 'icon-edit' : 'icon-add'"
                        >
                            <i
                                class="bi"
                                :class="
                                    editingExpense ? 'bi-pencil' : 'bi-plus-lg'
                                "
                            ></i>
                        </div>
                        <h5 class="modal-title">
                            {{
                                editingExpense ? "Edit Expense" : "Add Expense"
                            }}
                        </h5>
                        <p v-if="expenseFormError" class="form-error">
                            {{ expenseFormError }}
                        </p>

                        <form
                            class="expense-form"
                            @submit.prevent="saveExpense"
                        >
                            <div class="form-row">
                                <div class="form-group flex-1">
                                    <label class="form-label" for="eDate"
                                        >Date *</label
                                    >
                                    <input
                                        id="eDate"
                                        v-model="expenseForm.date"
                                        type="date"
                                        class="form-control"
                                        required
                                    />
                                </div>
                                <div class="form-group flex-1">
                                    <label class="form-label" for="eAmount"
                                        >Amount (₹) *</label
                                    >
                                    <input
                                        id="eAmount"
                                        v-model="expenseForm.amount"
                                        type="number"
                                        step="0.01"
                                        min="0.01"
                                        class="form-control"
                                        placeholder="0.00"
                                        required
                                    />
                                </div>
                            </div>
                            <div class="form-group">
                                <label class="form-label" for="eCategory"
                                    >Category *</label
                                >
                                <select
                                    id="eCategory"
                                    v-model="expenseForm.category_id"
                                    class="form-select"
                                    required
                                >
                                    <option :value="null" disabled>
                                        Select category
                                    </option>
                                    <option
                                        v-for="cat in categories"
                                        :key="cat.id"
                                        :value="cat.id"
                                    >
                                        {{ cat.name }}
                                    </option>
                                </select>
                            </div>
                            <div class="form-row">
                                <div class="form-group flex-1">
                                    <label class="form-label" for="ePlantation"
                                        >Plantation</label
                                    >
                                    <select
                                        id="ePlantation"
                                        v-model="expenseForm.plantation_id"
                                        class="form-select"
                                    >
                                        <option :value="null">None</option>
                                        <option
                                            v-for="pl in plantations"
                                            :key="pl.id"
                                            :value="pl.id"
                                        >
                                            {{ pl.name }}
                                        </option>
                                    </select>
                                </div>
                                <div class="form-group flex-1">
                                    <label class="form-label" for="eVehicle"
                                        >Vehicle</label
                                    >
                                    <select
                                        id="eVehicle"
                                        v-model="expenseForm.vehicle_id"
                                        class="form-select"
                                    >
                                        <option :value="null">None</option>
                                        <option
                                            v-for="veh in vehicles"
                                            :key="veh.id"
                                            :value="veh.id"
                                        >
                                            {{ veh.number }}
                                        </option>
                                    </select>
                                </div>
                            </div>
                            <div class="form-group">
                                <label class="form-label" for="eDescription"
                                    >Description</label
                                >
                                <textarea
                                    id="eDescription"
                                    v-model="expenseForm.description"
                                    class="form-control"
                                    rows="2"
                                    placeholder="Optional description"
                                ></textarea>
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
                            :disabled="!isExpenseFormValid || saving"
                            @click="saveExpense"
                        >
                            <span v-if="saving"
                                ><i class="bi bi-hourglass-split"></i
                            ></span>
                            <span v-else>{{
                                editingExpense ? "Save Changes" : "Add Expense"
                            }}</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Admin: Delete Confirmation Modal -->
        <div
            class="modal fade"
            id="deleteExpenseModal"
            tabindex="-1"
            aria-hidden="true"
            ref="deleteModalRef"
        >
            <div class="modal-dialog modal-dialog-centered modal-sm">
                <div class="modal-content confirm-modal">
                    <div class="modal-body">
                        <div class="modal-icon icon-delete">
                            <i class="bi bi-trash"></i>
                        </div>
                        <h5 class="modal-title">Delete Expense</h5>
                        <p v-if="deleteError" class="form-error">
                            {{ deleteError }}
                        </p>
                        <p v-else class="modal-desc">
                            This will permanently remove the expense of
                            <strong
                                >₹{{
                                    deletingExpense
                                        ? formatMoney(deletingExpense.amount)
                                        : ""
                                }}</strong
                            >. This action cannot be undone.
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
                            v-if="!deleteError"
                            type="button"
                            class="btn-modal btn-modal-confirm btn-modal-danger"
                            @click="deleteExpense"
                        >
                            Delete
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Non-admin: Submit Expense Request Modal -->
        <div
            class="modal fade"
            id="expenseRequestModal"
            tabindex="-1"
            aria-hidden="true"
            ref="requestModalRef"
        >
            <div class="modal-dialog modal-dialog-centered modal-lg">
                <div class="modal-content form-modal">
                    <div class="modal-body">
                        <div class="modal-icon icon-add">
                            <i class="bi bi-send"></i>
                        </div>
                        <h5 class="modal-title">Submit Expense Request</h5>

                        <div class="request-rows-container">
                            <div
                                v-for="(row, idx) in requestRows"
                                :key="idx"
                                class="request-row-item"
                            >
                                <div class="request-row-header">
                                    <span class="request-row-num"
                                        >Expense {{ idx + 1 }}</span
                                    >
                                    <button
                                        v-if="requestRows.length > 1"
                                        type="button"
                                        class="btn-remove-row"
                                        @click="removeRequestRow(idx)"
                                    >
                                        <i class="bi bi-x-lg"></i>
                                    </button>
                                </div>
                                <div class="request-row-fields">
                                    <div class="form-row-sm">
                                        <div class="form-group flex-1">
                                            <label class="form-label"
                                                >Date *</label
                                            >
                                            <input
                                                v-model="row.date"
                                                type="date"
                                                class="form-control form-control-sm"
                                            />
                                        </div>
                                        <div class="form-group flex-1">
                                            <label class="form-label"
                                                >Amount (₹) *</label
                                            >
                                            <input
                                                v-model="row.amount"
                                                type="number"
                                                step="0.01"
                                                min="0.01"
                                                class="form-control form-control-sm"
                                                placeholder="0.00"
                                            />
                                        </div>
                                        <div class="form-group flex-1">
                                            <label class="form-label"
                                                >Category *</label
                                            >
                                            <select
                                                v-model="row.category_id"
                                                class="form-select form-select-sm"
                                            >
                                                <option :value="null" disabled>
                                                    Select
                                                </option>
                                                <option
                                                    v-for="cat in categories"
                                                    :key="cat.id"
                                                    :value="cat.id"
                                                >
                                                    {{ cat.name }}
                                                </option>
                                            </select>
                                        </div>
                                    </div>
                                    <div class="form-row-sm">
                                        <div class="form-group flex-1">
                                            <label class="form-label"
                                                >Plantation</label
                                            >
                                            <select
                                                v-model="row.plantation_id"
                                                class="form-select form-select-sm"
                                            >
                                                <option :value="null">
                                                    None
                                                </option>
                                                <option
                                                    v-for="pl in plantations"
                                                    :key="pl.id"
                                                    :value="pl.id"
                                                >
                                                    {{ pl.name }}
                                                </option>
                                            </select>
                                        </div>
                                        <div class="form-group flex-1">
                                            <label class="form-label"
                                                >Vehicle</label
                                            >
                                            <select
                                                v-model="row.vehicle_id"
                                                class="form-select form-select-sm"
                                            >
                                                <option :value="null">
                                                    None
                                                </option>
                                                <option
                                                    v-for="veh in vehicles"
                                                    :key="veh.id"
                                                    :value="veh.id"
                                                >
                                                    {{ veh.number }}
                                                </option>
                                            </select>
                                        </div>
                                        <div class="form-group flex-1-wide">
                                            <label class="form-label"
                                                >Description</label
                                            >
                                            <input
                                                v-model="row.description"
                                                type="text"
                                                class="form-control form-control-sm"
                                                placeholder="Optional"
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <button
                            type="button"
                            class="btn-add-row"
                            @click="addRequestRow"
                        >
                            <i class="bi bi-plus-lg"></i>
                            Add Another Expense
                        </button>

                        <div class="form-group mt-3">
                            <label class="form-label" for="reqNotes"
                                >Request Notes</label
                            >
                            <textarea
                                id="reqNotes"
                                v-model="requestNotes"
                                class="form-control"
                                rows="2"
                                placeholder="Optional notes for this request"
                            ></textarea>
                        </div>
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
                            :disabled="!isRequestFormValid"
                            @click="submitRequest"
                        >
                            <i class="bi bi-send"></i>
                            Submit Request
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
import { useAuthStore } from "../stores/auth";
import { useReportsStore } from "@/stores/reports";

const reportsStore = useReportsStore();

// ── v-click-outside for filter popover ───────────────

// ── Filter popover state ──────────────────────────────
const filterPanelOpen = ref(false);
const filterBtnWrap = ref(null);

function onDocumentClick(e) {
    if (filterBtnWrap.value && !filterBtnWrap.value.contains(e.target)) {
        filterPanelOpen.value = false;
    }
}

// ── Auth ─────────────────────────────────────────────
const auth = useAuthStore();
const isAdmin = computed(() => {
    const roles = auth.userRoles;
    if (!roles) return false;
    if (Array.isArray(roles)) return roles.includes("admin");
    if (typeof roles === "string") return roles === "admin";
    if (roles && typeof roles === "object") return roles.name === "admin";
    return false;
});

// ── Data ─────────────────────────────────────────────
const loading = ref(true);
const expenses = ref([]);
const categories = ref([]);
const plantations = ref([]);
const vehicles = ref([]);
const approvals = ref([]);

// ── Filters ──────────────────────────────────────────
const filters = ref({
    search: "",
    category_id: null,
    plantation_id: null,
    vehicle_id: null,
    from_date: "",
    to_date: "",
});

// ── Admin expense modal ───────────────────────────────
const expenseModalRef = ref(null);
const deleteModalRef = ref(null);
let bsExpenseModal = null;
let bsDeleteModal = null;
const editingExpense = ref(null);
const deletingExpense = ref(null);
const expenseForm = ref({
    date: "",
    amount: "",
    category_id: null,
    plantation_id: null,
    vehicle_id: null,
    description: "",
});
const expenseFormError = ref("");
const saving = ref(false);

const isExpenseFormValid = computed(() => {
    const f = expenseForm.value;
    return (
        f.date !== "" &&
        String(f.amount).trim() !== "" &&
        Number(f.amount) > 0 &&
        f.category_id !== null
    );
});

// ── Non-admin request modal ───────────────────────────
const requestModalRef = ref(null);
let bsRequestModal = null;
const requestNotes = ref("");
const requestRows = ref([
    {
        date: "",
        amount: "",
        category_id: null,
        plantation_id: null,
        vehicle_id: null,
        description: "",
    },
]);

const isRequestFormValid = computed(() => {
    return requestRows.value.every(
        (r) =>
            r.date !== "" &&
            String(r.amount).trim() !== "" &&
            Number(r.amount) > 0 &&
            r.category_id !== null,
    );
});

// ── Computed ─────────────────────────────────────────
const pendingApprovalCount = computed(() =>
    approvals.value.filter(
        (a) => a.type === 'EXPENSE' && (a.status === 'PENDING' || a.status === 'PARTIAL'),
    ).length
);

const myRequests = computed(() => approvals.value);

const hasActiveFilters = computed(
    () =>
        filters.value.search ||
        filters.value.category_id ||
        filters.value.plantation_id ||
        filters.value.vehicle_id ||
        filters.value.from_date ||
        filters.value.to_date,
);

const activeFilterCount = computed(() => {
    let count = 0;
    if (filters.value.category_id) count++;
    if (filters.value.plantation_id) count++;
    if (filters.value.vehicle_id) count++;
    if (filters.value.from_date) count++;
    if (filters.value.to_date) count++;
    return count;
});

// ── Delete state ──────────────────────────────────────
const deleteError = ref("");

// ── Helpers ──────────────────────────────────────────
function formatDate(d) {
    return d
        ? new Date(d).toLocaleDateString("en-IN", {
              day: "2-digit",
              month: "short",
              year: "numeric",
          })
        : "—";
}

function formatMoney(v) {
    if (v == null || v === "") return "—";
    const n = Number(v);
    return isNaN(n)
        ? v
        : n.toLocaleString("en-IN", {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
          });
}

function categoryName(id) {
    return (
        categories.value.find((c) => c.id === id)?.name || (id ? `#${id}` : "—")
    );
}

function plantationName(id) {
    return id
        ? plantations.value.find((p) => p.id === id)?.name || `#${id}`
        : null;
}

function vehicleNumber(id) {
    return id
        ? vehicles.value.find((v) => v.id === id)?.number || `#${id}`
        : null;
}

function statusChipClass(status) {
    if (!status) return "";
    const s = status.toUpperCase();
    if (s === "PENDING") return "status-pending";
    if (s === "PARTIAL") return "status-partial";
    if (s === "APPROVED") return "status-active";
    if (s === "REJECTED") return "status-inactive";
    return "";
}

// ── Fetch ────────────────────────────────────────────
async function fetchExpenses() {
    try {
        const params = {};
        if (filters.value.search) params.search = filters.value.search;
        if (filters.value.category_id)
            params.category_id = filters.value.category_id;
        if (filters.value.plantation_id)
            params.plantation_id = filters.value.plantation_id;
        if (filters.value.vehicle_id)
            params.vehicle_id = filters.value.vehicle_id;
        if (filters.value.from_date) params.from_date = filters.value.from_date;
        if (filters.value.to_date) params.to_date = filters.value.to_date;
        const res = await api.get("/expenses/", { params });
        expenses.value = res.data;
    } catch (err) {
        console.error("Failed to fetch expenses:", err);
    }
}

async function fetchLookups() {
    try {
        const [catRes, plantRes, vehRes] = await Promise.all([
            api.get("/settings/expense-categories"),
            api.get("/plantations/"),
            api.get("/vehicles/", { params: { active_only: true } }),
        ]);
        categories.value = catRes.data;
        plantations.value = plantRes.data;
        vehicles.value = vehRes.data;
    } catch (err) {
        console.error("Failed to fetch lookups:", err);
    }
}

async function fetchApprovals() {
    try {
        const res = await api.get("/approvals/");
        approvals.value = res.data.filter((a) => a.type === "EXPENSE");
    } catch (err) {
        console.error("Failed to fetch approvals:", err);
    }
}

function clearFilters() {
    filters.value = {
        search: "",
        category_id: null,
        plantation_id: null,
        vehicle_id: null,
        from_date: "",
        to_date: "",
    };
    fetchExpenses();
}

// ── Admin: Add/Edit Expense Modal ────────────────────
function openExpenseModal(expense) {
    editingExpense.value = expense;
    expenseFormError.value = "";
    if (expense) {
        expenseForm.value = {
            date: expense.date ? expense.date.slice(0, 10) : "",
            amount: expense.amount ?? "",
            category_id: expense.category_id ?? null,
            plantation_id: expense.plantation_id ?? null,
            vehicle_id: expense.vehicle_id ?? null,
            description: expense.description || "",
        };
    } else {
        expenseForm.value = {
            date: "",
            amount: "",
            category_id: null,
            plantation_id: null,
            vehicle_id: null,
            description: "",
        };
    }
    if (!bsExpenseModal) bsExpenseModal = new Modal(expenseModalRef.value);
    bsExpenseModal.show();
}

async function saveExpense() {
    if (!isExpenseFormValid.value) return;
    saving.value = true;
    expenseFormError.value = "";
    const payload = {
        date: expenseForm.value.date,
        amount: String(expenseForm.value.amount),
        category_id: expenseForm.value.category_id,
        plantation_id: expenseForm.value.plantation_id || null,
        vehicle_id: expenseForm.value.vehicle_id || null,
        description: expenseForm.value.description.trim() || null,
    };
    try {
        if (editingExpense.value) {
            const res = await api.put(
                `/expenses/${editingExpense.value.id}`,
                payload,
            );
            const idx = expenses.value.findIndex(
                (e) => e.id === editingExpense.value.id,
            );
            if (idx !== -1) expenses.value[idx] = res.data;
        } else {
            const res = await api.post("/expenses/", payload);
            expenses.value.unshift(res.data);
        }
        reportsStore.invalidate('expenses');
        bsExpenseModal.hide();
    } catch (err) {
        expenseFormError.value =
            err.response?.data?.detail ||
            "Failed to save expense. Please try again.";
    } finally {
        saving.value = false;
    }
}

// ── Admin: Delete Expense ────────────────────────────
function promptDelete(expense) {
    deletingExpense.value = expense;
    deleteError.value = "";
    if (!bsDeleteModal) bsDeleteModal = new Modal(deleteModalRef.value);
    bsDeleteModal.show();
}

async function deleteExpense() {
    if (!deletingExpense.value) return;
    try {
        await api.delete(`/expenses/${deletingExpense.value.id}`);
        reportsStore.invalidate('expenses');
        expenses.value = expenses.value.filter(
            (e) => e.id !== deletingExpense.value.id,
        );
        bsDeleteModal.hide();
    } catch (err) {
        if (err.response?.status === 409) {
            deleteError.value =
                err.response.data?.detail || "Cannot delete this expense.";
        } else {
            console.error("Failed to delete expense:", err);
        }
    }
}

// ── Non-admin: Request Modal ─────────────────────────
function openRequestModal() {
    requestNotes.value = "";
    requestRows.value = [
        {
            date: "",
            amount: "",
            category_id: null,
            plantation_id: null,
            vehicle_id: null,
            description: "",
        },
    ];
    if (!bsRequestModal) bsRequestModal = new Modal(requestModalRef.value);
    bsRequestModal.show();
}

function addRequestRow() {
    requestRows.value.push({
        date: "",
        amount: "",
        category_id: null,
        plantation_id: null,
        vehicle_id: null,
        description: "",
    });
}

function removeRequestRow(idx) {
    requestRows.value.splice(idx, 1);
}

async function submitRequest() {
    if (!isRequestFormValid.value) return;
    try {
        const requestItems = requestRows.value.map((row, idx) => ({
            index: idx,
            status: "pending",
            data: {
                date: row.date ? new Date(row.date).toISOString() : null,
                amount: String(row.amount),
                category_id: row.category_id,
                plantation_id: row.plantation_id || null,
                vehicle_id: row.vehicle_id || null,
                description: row.description.trim() || null,
            },
        }));
        await api.post("/approvals/", {
            type: "EXPENSE",
            items: requestItems,
            notes: requestNotes.value.trim() || "",
        });
        bsRequestModal.hide();
        await fetchApprovals();
    } catch (err) {
        console.error("Failed to submit request:", err);
    }
}

// ── Lifecycle ────────────────────────────────────────
onMounted(async () => {
    document.addEventListener("click", onDocumentClick, true);
    await Promise.all([fetchExpenses(), fetchLookups(), fetchApprovals()]);
    loading.value = false;
});

onBeforeUnmount(() => {
    document.removeEventListener("click", onDocumentClick, true);
    bsExpenseModal?.dispose();
    bsDeleteModal?.dispose();
    bsRequestModal?.dispose();
});
</script>

<style scoped>
/* ── Page Layout ──────────────────────────────────── */
.expenses-page {
    max-width: 100vw;
}

.page-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 24px;
    gap: 16px;
    flex-wrap: wrap;
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

.header-actions {
    display: flex;
    gap: 8px;
    align-items: center;
    flex-shrink: 0;
}

/* ── Buttons ──────────────────────────────────────── */
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

.btn-add-secondary {
    background: var(--sienna);
}

.btn-add-secondary:hover {
    background: var(--sienna-light);
    box-shadow: 0 4px 12px rgba(181, 105, 77, 0.25);
}

/* ── Toolbar ──────────────────────────────────────── */
.toolbar {
    display: flex;
    gap: 10px;
    margin-bottom: 16px;
    align-items: center;
    position: relative;
    z-index: 10;
}

.search-wrap {
    position: relative;
    flex: 1;
    min-width: 200px;
}

.search-icon {
    position: absolute;
    left: 12px;
    top: 50%;
    transform: translateY(-50%);
    color: var(--text-secondary);
    font-size: 0.85rem;
    pointer-events: none;
}

.search-input {
    padding-left: 34px;
    font-size: 0.85rem;
}

/* Filters button */
.filter-btn-wrap {
    position: relative;
    flex-shrink: 0;
}

.btn-filters {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 14px;
    border: 1.5px solid var(--border-light);
    border-radius: 10px;
    background: var(--bg-card);
    color: var(--text-primary);
    font-family: var(--font-body);
    font-size: 0.83rem;
    font-weight: 500;
    cursor: pointer;
    transition: all var(--transition-fast);
}

.btn-filters:hover,
.btn-filters.active {
    border-color: var(--moss);
    color: var(--moss);
    background: rgba(138, 154, 123, 0.06);
}

.filter-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 18px;
    height: 18px;
    padding: 0 5px;
    border-radius: 20px;
    background: var(--moss);
    color: var(--white);
    font-size: 0.68rem;
    font-weight: 700;
    line-height: 1;
}

/* Floating filter popover */
.filter-popover {
    position: absolute;
    top: calc(100% + 6px);
    right: 0;
    width: 260px;
    background: var(--bg-card);
    border: 1px solid var(--border-light);
    border-radius: 12px;
    box-shadow: var(--shadow-md);
    padding: 14px;
    z-index: 200;
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.fp-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 2px;
}

.fp-title {
    font-size: 0.8rem;
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

.fp-clear {
    border: none;
    background: transparent;
    color: var(--sienna);
    font-size: 0.78rem;
    cursor: pointer;
    padding: 0;
}

.fp-clear:hover {
    text-decoration: underline;
}

.fp-field {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.fp-label {
    font-size: 0.75rem;
    color: var(--text-secondary);
    font-weight: 500;
}

/* ── Content Panel ────────────────────────────────── */
.content-panel {
    background: var(--bg-card);
    border: 1px solid var(--border-light);
    border-radius: 14px;
    box-shadow: var(--shadow-sm);
    overflow: hidden;
}

/* ── Expenses List ────────────────────────────────── */
.expenses-list {
    position: relative;
}

.expense-row {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 14px 18px;
    border-bottom: 1px solid var(--border-light);
    transition: background var(--transition-fast);
    min-width: 0;
}

.expense-row:last-child {
    border-bottom: none;
}

.expense-row:hover {
    background: rgba(138, 154, 123, 0.04);
}

.expense-date {
    font-size: 0.78rem;
    color: var(--text-secondary);
    white-space: nowrap;
    font-variant-numeric: tabular-nums;
    flex-shrink: 0;
    min-width: 88px;
}

.expense-main {
    display: flex;
    align-items: center;
    gap: 10px;
    flex: 1;
    min-width: 0;
    flex-wrap: wrap;
}

.badge-category {
    display: inline-flex;
    align-items: center;
    font-size: 0.7rem;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 20px;
    background: rgba(196, 163, 90, 0.14);
    color: #8a6f2a;
    letter-spacing: 0.03em;
    white-space: nowrap;
    flex-shrink: 0;
}

.expense-amount {
    font-weight: 700;
    font-size: 0.95rem;
    color: var(--text-primary);
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
    flex-shrink: 0;
}

.expense-description {
    font-size: 0.82rem;
    color: var(--text-secondary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    min-width: 0;
    flex: 1;
}

.expense-tags {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-shrink: 0;
    flex-wrap: wrap;
}

.expense-tag {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 0.72rem;
    font-weight: 600;
    padding: 3px 9px;
    border-radius: 20px;
    white-space: nowrap;
    max-width: 120px;
    overflow: hidden;
    text-overflow: ellipsis;
}

.tag-plantation {
    background: rgba(74, 103, 65, 0.1);
    color: var(--moss);
}

.tag-vehicle {
    background: rgba(138, 154, 123, 0.12);
    color: var(--sage);
}

.expense-actions {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-shrink: 0;
}

/* ── Action Buttons ───────────────────────────────── */
.btn-action {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    border: 1.5px solid var(--border);
    background: transparent;
    color: var(--text-secondary);
    font-size: 0.9rem;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    transition: all var(--transition-fast);
}

.btn-edit:hover {
    border-color: var(--harvest);
    color: #8a6f2a;
    background: rgba(196, 163, 90, 0.08);
}

.btn-delete:hover {
    border-color: var(--sienna);
    color: var(--sienna);
    background: rgba(181, 105, 77, 0.06);
}

/* ── Status Chips ─────────────────────────────────── */
.status-chip {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 0.72rem;
    font-weight: 600;
    padding: 3px 9px;
    border-radius: 20px;
    letter-spacing: 0.01em;
    white-space: nowrap;
    flex-shrink: 0;
}

.status-chip i {
    font-size: 0.68rem;
}

.status-chip-sm {
    font-size: 0.66rem;
    padding: 2px 7px;
}

.status-active {
    background: rgba(74, 103, 65, 0.1);
    color: var(--moss);
}

.status-inactive {
    background: rgba(181, 105, 77, 0.1);
    color: var(--sienna);
}

.status-pending {
    background: rgba(196, 163, 90, 0.14);
    color: #8a6f2a;
}

.status-partial {
    background: rgba(138, 154, 123, 0.14);
    color: var(--sage);
}

/* ── Empty State ──────────────────────────────────── */
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

/* ── Approval Banner ──────────────────────────────── */
.approval-banner {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 16px;
    background: var(--amber-light, #fff8e1);
    border: 1px solid var(--amber, #ffc107);
    border-radius: 8px;
    font-size: 0.9rem;
    color: var(--text-primary);
    margin-bottom: 16px;
}
.approval-banner i { color: var(--amber, #ffc107); }
.banner-link {
    margin-left: auto;
    color: var(--moss);
    font-weight: 600;
    text-decoration: none;
}
.banner-link:hover { text-decoration: underline; }

/* ── My Requests Panel ────────────────────────────── */
.my-requests-panel {
    margin-top: 24px;
    background: var(--bg-card);
    border: 1.5px solid var(--border-light);
    border-radius: 14px;
    overflow: hidden;
    box-shadow: var(--shadow-sm);
}

.my-requests-header {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 14px 18px;
    border-bottom: 1px solid var(--border-light);
    font-size: 0.85rem;
    font-weight: 700;
    color: var(--text-primary);
    background: var(--parchment-deep);
}

.my-request-card {
    padding: 14px 18px;
    border-bottom: 1px solid var(--border-light);
}

.my-request-card:last-child {
    border-bottom: none;
}

.my-request-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}

.my-request-meta {
    display: flex;
    align-items: center;
    gap: 14px;
}

.my-request-date {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 0.8rem;
    color: var(--text-secondary);
}

.my-request-count {
    font-size: 0.78rem;
    color: var(--text-secondary);
}

.my-request-items {
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.my-request-item {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    padding: 8px 12px;
    background: var(--parchment-deep);
    border-radius: 8px;
    font-size: 0.82rem;
}

.mri-date {
    font-size: 0.76rem;
    color: var(--text-secondary);
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
}

.mri-amount {
    font-weight: 700;
    color: var(--text-primary);
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
}

.mri-category {
    display: inline-flex;
    align-items: center;
    font-size: 0.68rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 20px;
    background: rgba(196, 163, 90, 0.14);
    color: #8a6f2a;
    white-space: nowrap;
}

.mri-desc {
    font-size: 0.78rem;
    color: var(--text-secondary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    min-width: 0;
    flex: 1;
}

.mri-tag {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 0.7rem;
    font-weight: 600;
    color: var(--text-secondary);
}

.mri-note {
    font-size: 0.76rem;
    color: var(--sienna);
    font-style: italic;
    display: inline-flex;
    align-items: center;
    gap: 4px;
    width: 100%;
}

.my-request-notes {
    margin-top: 8px;
    font-size: 0.78rem;
    color: var(--text-secondary);
    font-style: italic;
    display: flex;
    align-items: flex-start;
    gap: 6px;
}

/* ── Form Modal ───────────────────────────────────── */
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

.expense-form {
    text-align: left;
    margin-top: 20px;
}

.form-group {
    margin-bottom: 16px;
}

.form-label {
    font-size: 0.83rem;
    font-weight: 600;
    color: var(--text-primary);
    display: block;
    margin-bottom: 6px;
}

.form-row {
    display: flex;
    gap: 12px;
}

.form-row-sm {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}

.flex-1 {
    flex: 1;
    min-width: 0;
}

.flex-1-wide {
    flex: 2;
    min-width: 0;
}

.form-error {
    margin-top: 8px;
    padding: 8px 12px;
    border-radius: 8px;
    background: rgba(181, 105, 77, 0.08);
    border: 1px solid rgba(181, 105, 77, 0.2);
    color: var(--sienna);
    font-size: 0.82rem;
    text-align: left;
}

/* ── Confirm Modal ────────────────────────────────── */
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

/* ── Modal Footers ────────────────────────────────── */
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
    display: inline-flex;
    align-items: center;
    gap: 6px;
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

/* ── Request Form ─────────────────────────────────── */
.request-rows-container {
    text-align: left;
    margin-top: 20px;
    display: flex;
    flex-direction: column;
    gap: 14px;
    max-height: 55vh;
    overflow-y: auto;
}

.request-row-item {
    background: var(--parchment-deep);
    border: 1px solid var(--border-light);
    border-radius: 10px;
    padding: 14px;
}

.request-row-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}

.request-row-num {
    font-size: 0.78rem;
    font-weight: 700;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

.btn-remove-row {
    width: 24px;
    height: 24px;
    border-radius: 6px;
    border: 1.5px solid var(--border);
    background: transparent;
    color: var(--text-secondary);
    font-size: 0.7rem;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    transition: all var(--transition-fast);
}

.btn-remove-row:hover {
    border-color: var(--sienna);
    color: var(--sienna);
    background: rgba(181, 105, 77, 0.06);
}

.request-row-fields {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.btn-add-row {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    margin-top: 12px;
    padding: 7px 14px;
    border: 1.5px dashed var(--border);
    border-radius: 9px;
    background: transparent;
    color: var(--text-secondary);
    font-family: var(--font-body);
    font-size: 0.82rem;
    font-weight: 600;
    cursor: pointer;
    transition: all var(--transition-fast);
    width: 100%;
    justify-content: center;
}

.btn-add-row:hover {
    border-color: var(--moss);
    color: var(--moss);
    background: rgba(74, 103, 65, 0.04);
}

.mt-2 {
    margin-top: 0.5rem;
}

.mt-3 {
    margin-top: 1rem;
}

/* ── List Transitions ─────────────────────────────── */
.list-enter-active {
    transition: all 0.3s var(--ease-out);
}

.list-leave-active {
    transition: all 0.2s var(--ease-out);
}

.list-enter-from {
    opacity: 0;
    transform: translateY(-8px);
}

.list-leave-to {
    opacity: 0;
    transform: translateX(20px);
}

/* ── Responsive ───────────────────────────────────── */
@media (max-width: 767.98px) {
    .page-title {
        font-size: 1.35rem;
    }

    .page-header {
        margin-bottom: 18px;
    }

    .header-actions .btn-add span {
        display: none;
    }

    .header-actions .btn-add i {
        font-size: 1.15rem;
    }

    .filter-bar {
        gap: 8px;
    }

    .filter-select,
    .filter-date {
        min-width: 0;
        flex: 1;
    }

    .expense-row {
        flex-wrap: wrap;
        padding: 12px 14px;
        gap: 8px;
    }

    .expense-date {
        min-width: 0;
        width: 100%;
    }

    .expense-main {
        gap: 8px;
    }

    .expense-tags {
        gap: 4px;
    }

    .expense-actions {
        margin-left: auto;
    }

    .form-row {
        flex-direction: column;
        gap: 0;
    }

    .form-row-sm {
        flex-direction: column;
        gap: 0;
    }
}

@media (max-width: 575.98px) {
    .expense-description {
        display: none;
    }
}
</style>

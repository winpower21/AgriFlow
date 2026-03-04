<template>
    <div class="plantations-page">
        <!-- Page Header -->
        <div class="page-header animate-fade-in-up">
            <div>
                <h2 class="page-title">Plantations</h2>
                <p class="page-subtitle">
                    {{ plantations.length }} registered &mdash;
                    {{ activePlantations.length }} active,
                    {{ expiredPlantations.length }} expired
                </p>
            </div>
            <button v-if="isAdmin" class="btn-add" @click="openAddModal">
                <i class="bi bi-plus-lg"></i>
                <span>Add Plantation</span>
            </button>
        </div>

        <!-- Tab Navigation -->
        <div class="tab-bar animate-fade-in-up animate-delay-1">
            <button
                class="tab-btn"
                :class="{ active: activeTab === 'active' }"
                @click="activeTab = 'active'"
            >
                <i class="bi bi-check-circle-fill"></i>
                <span class="tab-label">Active Leases</span>
                <span class="tab-count">{{ activePlantations.length }}</span>
            </button>
            <button
                class="tab-btn"
                :class="{ active: activeTab === 'expired' }"
                @click="activeTab = 'expired'"
            >
                <i class="bi bi-x-circle-fill"></i>
                <span class="tab-label">Expired Leases</span>
                <span class="tab-count">{{ expiredPlantations.length }}</span>
            </button>
        </div>

        <!-- Desktop Table -->
        <div
            v-if="currentPlantations.length > 0"
            class="table-wrapper d-none d-md-block animate-fade-in-up animate-delay-2"
            :class="{ 'table-expired': activeTab === 'expired' }"
        >
            <div class="table-scroll">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Plantation</th>
                            <th>Location</th>
                            <th>Lease Start</th>
                            <th>Lease End</th>
                            <th>Lease Cost</th>
                            <th>Status</th>
                            <th class="th-actions">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr
                            v-for="(p, i) in currentPlantations"
                            :key="p.id"
                            class="data-row"
                            :style="{ animationDelay: `${i * 0.04}s` }"
                        >
                            <td>
                                <div class="plantation-identity">
                                    <span
                                        class="plantation-icon"
                                        :class="{
                                            'plantation-icon-expired':
                                                activeTab === 'expired',
                                        }"
                                    >
                                        <i class="bi bi-tree"></i>
                                    </span>
                                    <span class="plantation-name">{{
                                        p.name
                                    }}</span>
                                </div>
                            </td>
                            <td class="location-cell">
                                <span v-if="p.location" class="location-text">
                                    <i class="bi bi-geo-alt"></i>
                                    {{ p.location.city
                                    }}<template v-if="p.location.state"
                                        >, {{ p.location.state }}</template
                                    >
                                </span>
                                <span v-else class="text-muted">&mdash;</span>
                            </td>
                            <td class="date-cell">
                                {{ formatDate(p.lease_start) }}
                            </td>
                            <td class="date-cell">
                                {{ formatDate(p.lease_end) }}
                            </td>
                            <td>
                                <span
                                    v-if="getLeaseExpense(p.id)"
                                    class="cost-chip"
                                    :class="{
                                        'cost-chip-muted':
                                            activeTab === 'expired',
                                    }"
                                >
                                    {{
                                        formatCurrency(
                                            getLeaseExpense(p.id).amount,
                                        )
                                    }}
                                </span>
                                <button
                                    v-else-if="
                                        isAdmin && activeTab === 'active'
                                    "
                                    class="btn-lease-cost"
                                    @click="openLeaseCostModal(p)"
                                    title="Add lease cost"
                                >
                                    <i class="bi bi-plus-circle"></i>
                                    Add
                                </button>
                                <span v-else class="text-muted">&mdash;</span>
                            </td>
                            <td>
                                <span
                                    class="status-chip"
                                    :class="leaseStatusClass(p)"
                                >
                                    <i
                                        class="bi"
                                        :class="leaseStatusIcon(p)"
                                    ></i>
                                    {{ leaseStatusLabel(p) }}
                                </span>
                            </td>
                            <td>
                                <div class="action-group">
                                    <button
                                        class="btn-action btn-details"
                                        title="Details"
                                        @click="openDetailsModal(p)"
                                    >
                                        <i class="bi bi-clock-history"></i>
                                    </button>
                                    <template v-if="isAdmin">
                                        <button
                                            class="btn-action btn-edit"
                                            :title="
                                                activeTab === 'expired'
                                                    ? 'Renew / Edit'
                                                    : 'Edit'
                                            "
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
                                    </template>
                                </div>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Mobile Cards -->
        <div v-if="currentPlantations.length > 0" class="d-md-none">
            <div
                v-for="(p, i) in currentPlantations"
                :key="p.id"
                class="plantation-card animate-fade-in-up"
                :class="{ 'plantation-card-expired': activeTab === 'expired' }"
                :style="{ animationDelay: `${i * 0.06}s` }"
            >
                <div class="plantation-card-header">
                    <div class="plantation-identity">
                        <span
                            class="plantation-icon"
                            :class="{
                                'plantation-icon-expired':
                                    activeTab === 'expired',
                            }"
                        >
                            <i class="bi bi-tree"></i>
                        </span>
                        <span class="plantation-name">{{ p.name }}</span>
                    </div>
                    <span class="status-chip" :class="leaseStatusClass(p)">
                        <i class="bi" :class="leaseStatusIcon(p)"></i>
                        {{ leaseStatusLabel(p) }}
                    </span>
                </div>
                <div class="plantation-card-body">
                    <div v-if="p.location" class="card-location">
                        <i class="bi bi-geo-alt"></i>
                        {{ p.location.city
                        }}<template v-if="p.location.state"
                            >, {{ p.location.state }}</template
                        >
                    </div>
                    <div class="lease-dates">
                        <div class="lease-date-item">
                            <span class="lease-label">Lease Start</span>
                            <span class="lease-value">{{
                                formatDate(p.lease_start)
                            }}</span>
                        </div>
                        <div class="lease-date-item">
                            <span class="lease-label">Lease End</span>
                            <span class="lease-value">{{
                                formatDate(p.lease_end)
                            }}</span>
                        </div>
                        <div
                            v-if="activeTab === 'active'"
                            class="lease-date-item"
                        >
                            <span class="lease-label">Lease Cost</span>
                            <span
                                v-if="getLeaseExpense(p.id)"
                                class="lease-value"
                            >
                                {{
                                    formatCurrency(getLeaseExpense(p.id).amount)
                                }}
                            </span>
                            <button
                                v-else-if="isAdmin"
                                class="btn-lease-cost btn-lease-cost-sm"
                                @click="openLeaseCostModal(p)"
                            >
                                <i class="bi bi-plus-circle"></i>
                                Add
                            </button>
                            <span v-else class="lease-value">&mdash;</span>
                        </div>
                    </div>
                    <div class="action-group action-group-mobile">
                        <button
                            class="btn-action btn-details"
                            @click="openDetailsModal(p)"
                        >
                            <i class="bi bi-clock-history"></i>
                            History
                        </button>
                        <template v-if="isAdmin">
                            <button
                                class="btn-action btn-edit"
                                @click="openEditModal(p)"
                            >
                                <i class="bi bi-pencil"></i>
                                {{ activeTab === "expired" ? "Renew" : "Edit" }}
                            </button>
                            <button
                                class="btn-action btn-delete"
                                @click="openDeleteModal(p)"
                            >
                                <i class="bi bi-trash3"></i>
                                Delete
                            </button>
                        </template>
                    </div>
                </div>
            </div>
        </div>

        <!-- Empty State -->
        <div
            v-if="currentPlantations.length === 0"
            class="empty-state animate-fade-in-up animate-delay-2"
        >
            <i
                class="bi"
                :class="activeTab === 'active' ? 'bi-tree' : 'bi-check-circle'"
            ></i>
            <p>
                {{
                    activeTab === "active"
                        ? "No active leases"
                        : "No expired leases"
                }}
            </p>
        </div>

        <!-- ══════════ MODALS ══════════ -->

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
                        <div
                            class="modal-icon"
                            :class="isEditing ? 'icon-edit' : 'icon-add'"
                        >
                            <i
                                class="bi"
                                :class="
                                    isEditing ? 'bi-pencil-square' : 'bi-tree'
                                "
                            ></i>
                        </div>
                        <h5 class="modal-title">
                            {{
                                isEditing ? "Edit Plantation" : "Add Plantation"
                            }}
                        </h5>
                        <p
                            v-if="isEditing && isExpired(editingPlantation)"
                            class="modal-hint"
                        >
                            <i class="bi bi-info-circle"></i>
                            Changing lease dates will archive the current lease
                            to history.
                        </p>

                        <form
                            class="plantation-form"
                            @submit.prevent="handleFormSubmit"
                        >
                            <div class="form-group">
                                <label class="form-label" for="pName"
                                    >Plantation Name</label
                                >
                                <input
                                    id="pName"
                                    v-model="form.name"
                                    type="text"
                                    class="form-control"
                                    placeholder="e.g. Green Valley Estate"
                                    required
                                />
                            </div>

                            <!-- Location Search -->
                            <div class="form-group">
                                <label class="form-label">Location</label>
                                <div v-if="form.location" class="location-chip">
                                    <i class="bi bi-geo-alt-fill"></i>
                                    <span
                                        >{{ form.location.city
                                        }}<template v-if="form.location.state"
                                            >,
                                            {{ form.location.state }}</template
                                        ></span
                                    >
                                    <button
                                        type="button"
                                        class="location-chip-clear"
                                        @click="clearLocation"
                                    >
                                        <i class="bi bi-x-lg"></i>
                                    </button>
                                </div>
                                <div v-else class="location-search-wrapper">
                                    <div class="location-search-input-wrap">
                                        <i
                                            class="bi bi-search location-search-icon"
                                        ></i>
                                        <input
                                            v-model="locationQuery"
                                            type="text"
                                            class="form-control location-search-input"
                                            placeholder="Search for a city or region..."
                                            @input="onLocationSearch"
                                            @focus="
                                                showPredictions =
                                                    locationPredictions.length >
                                                    0
                                            "
                                            @blur="hidePredictionsDelayed"
                                        />
                                        <span
                                            v-if="locationSearching"
                                            class="location-spinner"
                                        >
                                            <i
                                                class="bi bi-arrow-repeat spin"
                                            ></i>
                                        </span>
                                    </div>
                                    <div
                                        v-if="
                                            showPredictions &&
                                            locationPredictions.length > 0
                                        "
                                        class="location-dropdown"
                                    >
                                        <button
                                            v-for="pred in locationPredictions"
                                            :key="pred.place_id"
                                            type="button"
                                            class="location-dropdown-item"
                                            @mousedown.prevent="
                                                selectPrediction(pred)
                                            "
                                        >
                                            <i class="bi bi-geo-alt"></i>
                                            <div>
                                                <div class="loc-main">
                                                    {{ pred.main_text }}
                                                </div>
                                                <div class="loc-secondary">
                                                    {{ pred.secondary_text }}
                                                </div>
                                            </div>
                                        </button>
                                    </div>
                                </div>
                            </div>

                            <div class="form-row">
                                <div class="form-group flex-1">
                                    <label class="form-label" for="pLeaseStart"
                                        >Lease Start</label
                                    >
                                    <input
                                        id="pLeaseStart"
                                        v-model="form.lease_start"
                                        type="date"
                                        class="form-control"
                                        required
                                    />
                                </div>
                                <div class="form-group flex-1">
                                    <label class="form-label" for="pLeaseEnd"
                                        >Lease End</label
                                    >
                                    <input
                                        id="pLeaseEnd"
                                        v-model="form.lease_end"
                                        type="date"
                                        class="form-control"
                                        required
                                    />
                                </div>
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
                            {{ isEditing ? "Save Changes" : "Add Plantation" }}
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Lease Cost Modal -->
        <div
            class="modal fade"
            id="leaseCostModal"
            tabindex="-1"
            aria-hidden="true"
            ref="leaseCostModalRef"
        >
            <div class="modal-dialog modal-dialog-centered modal-sm">
                <div class="modal-content form-modal">
                    <div class="modal-body">
                        <div class="modal-icon icon-lease">
                            <i class="bi bi-cash-coin"></i>
                        </div>
                        <h5 class="modal-title">Add Lease Cost</h5>
                        <p
                            v-if="leaseCostTarget"
                            class="modal-desc"
                            style="margin-bottom: 16px"
                        >
                            for
                            <strong>{{ leaseCostTarget.name }}</strong>
                        </p>

                        <div
                            v-if="!leaseCostCategoryId"
                            class="alert-missing-category"
                        >
                            <i class="bi bi-exclamation-triangle-fill"></i>
                            <div>
                                <strong>"Lease Cost"</strong> expense category
                                not found. Please create it in
                                <RouterLink to="/settings">Settings</RouterLink>
                                first.
                            </div>
                        </div>

                        <div v-else class="plantation-form">
                            <div class="form-group">
                                <label class="form-label" for="leaseCostAmount"
                                    >Amount</label
                                >
                                <input
                                    id="leaseCostAmount"
                                    v-model.number="leaseCostAmount"
                                    type="number"
                                    step="0.01"
                                    min="0"
                                    class="form-control"
                                    placeholder="0.00"
                                />
                            </div>
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
                            v-if="leaseCostCategoryId"
                            type="button"
                            class="btn-modal btn-modal-confirm"
                            @click="submitLeaseCost"
                            :disabled="!leaseCostAmount || leaseCostAmount <= 0"
                        >
                            Add Expense
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Details / Lease History Modal -->
        <div
            class="modal fade"
            id="detailsModal"
            tabindex="-1"
            aria-hidden="true"
            ref="detailsModalRef"
        >
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content form-modal">
                    <div class="modal-body" v-if="detailsTarget">
                        <div class="modal-icon icon-history">
                            <i class="bi bi-clock-history"></i>
                        </div>
                        <h5 class="modal-title">{{ detailsTarget.name }}</h5>
                        <p
                            v-if="detailsTarget.location"
                            class="modal-desc"
                            style="margin-bottom: 8px"
                        >
                            <i class="bi bi-geo-alt"></i>
                            {{ detailsTarget.location.city
                            }}<template v-if="detailsTarget.location.state"
                                >, {{ detailsTarget.location.state }}</template
                            ><template v-if="detailsTarget.location.country"
                                >,
                                {{ detailsTarget.location.country }}</template
                            >
                        </p>
                        <p class="modal-desc" style="margin-bottom: 20px">
                            Lease history &mdash;
                            {{ leaseHistory.length }}
                            {{
                                leaseHistory.length === 1 ? "record" : "records"
                            }}
                        </p>

                        <!-- Current Lease -->
                        <div class="history-current">
                            <div class="history-badge history-badge-current">
                                Current Lease
                            </div>
                            <div class="history-row">
                                <div class="history-dates">
                                    <span>{{
                                        formatDate(detailsTarget.lease_start)
                                    }}</span>
                                    <i class="bi bi-arrow-right"></i>
                                    <span>{{
                                        formatDate(detailsTarget.lease_end)
                                    }}</span>
                                </div>
                                <span
                                    class="status-chip"
                                    :class="leaseStatusClass(detailsTarget)"
                                    style="font-size: 0.7rem"
                                >
                                    <i
                                        class="bi"
                                        :class="leaseStatusIcon(detailsTarget)"
                                    ></i>
                                    {{ leaseStatusLabel(detailsTarget) }}
                                </span>
                            </div>
                        </div>

                        <!-- History Timeline -->
                        <div
                            v-if="leaseHistory.length > 0"
                            class="history-timeline"
                        >
                            <div
                                v-for="(h, i) in leaseHistory"
                                :key="h.id"
                                class="history-item"
                            >
                                <div class="history-connector">
                                    <div class="history-dot"></div>
                                    <div
                                        v-if="i < leaseHistory.length - 1"
                                        class="history-line"
                                    ></div>
                                </div>
                                <div class="history-content">
                                    <div class="history-dates">
                                        <span>{{
                                            formatDate(h.start_date)
                                        }}</span>
                                        <i class="bi bi-arrow-right"></i>
                                        <span>{{
                                            formatDate(h.end_date)
                                        }}</span>
                                    </div>
                                    <span
                                        v-if="h.cost"
                                        class="cost-chip cost-chip-muted"
                                        style="font-size: 0.75rem"
                                    >
                                        {{ formatCurrency(h.cost) }}
                                    </span>
                                </div>
                            </div>
                        </div>

                        <div
                            v-else
                            class="empty-state-inline"
                            style="margin-top: 12px"
                        >
                            <i class="bi bi-journal-text"></i>
                            <span>No previous lease records</span>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button
                            type="button"
                            class="btn-modal btn-modal-cancel"
                            data-bs-dismiss="modal"
                        >
                            Close
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
                        <h5 class="modal-title">Delete Plantation</h5>
                        <p class="modal-desc">
                            Remove
                            <strong>{{ deleteTarget?.name }}</strong
                            >?
                        </p>
                        <div
                            v-if="deleteHasHistory"
                            class="alert-missing-category"
                            style="margin-top: 14px"
                        >
                            <i class="bi bi-exclamation-triangle-fill"></i>
                            <div>
                                This plantation has
                                <strong>{{ deleteHistoryCount }}</strong>
                                lease history
                                {{
                                    deleteHistoryCount === 1
                                        ? "record"
                                        : "records"
                                }}. Deleting will permanently remove all
                                history.
                            </div>
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
                            class="btn-modal btn-modal-confirm btn-modal-danger"
                            @click="confirmDelete"
                        >
                            {{
                                deleteHasHistory
                                    ? "Delete With History"
                                    : "Delete"
                            }}
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
import { useAuthStore } from "@/stores/auth";
import api from "../utils/api";

// ── Auth ────────────────────────────────────────────
const auth = useAuthStore();
const isAdmin = computed(() => auth.userRoles?.includes("admin"));

// ── Reactive State ──────────────────────────────────
const plantations = ref([]);
const expenseCategories = ref([]);
const plantationExpenses = ref([]);

const formModalRef = ref(null);
const deleteModalRef = ref(null);
const leaseCostModalRef = ref(null);
const detailsModalRef = ref(null);
let bsFormModal = null;
let bsDeleteModal = null;
let bsLeaseCostModal = null;
let bsDetailsModal = null;

// Lease cost modal state
const leaseCostTarget = ref(null);
const leaseCostAmount = ref(null);

const leaseCostCategoryId = computed(() => {
    const cat = expenseCategories.value.find(
        (c) => c.name.toLowerCase() === "lease cost",
    );
    return cat?.id || null;
});

// Form state
const isEditing = ref(false);
const editingId = ref(null);
const editingPlantation = ref(null);
const deleteTarget = ref(null);
const deleteHasHistory = ref(false);
const deleteHistoryCount = ref(0);

// Details modal state
const detailsTarget = ref(null);
const leaseHistory = ref([]);

const form = ref(getEmptyForm());

// Location search state
const locationQuery = ref("");
const locationPredictions = ref([]);
const locationSearching = ref(false);
const showPredictions = ref(false);
let locationSearchTimer = null;

function getEmptyForm() {
    return {
        name: "",
        lease_start: "",
        lease_end: "",
        location: null,
    };
}

const isFormValid = computed(() => {
    return (
        form.value.name.trim() !== "" &&
        form.value.lease_start !== "" &&
        form.value.lease_end !== ""
    );
});

// ── Tab State ───────────────────────────────────────
const activeTab = ref("active");

// ── Computed: Split Active / Expired ────────────────

const activePlantations = computed(() => {
    const now = new Date();
    return plantations.value.filter((p) => new Date(p.lease_end) >= now);
});

const expiredPlantations = computed(() => {
    const now = new Date();
    return plantations.value.filter((p) => new Date(p.lease_end) < now);
});

const currentPlantations = computed(() => {
    return activeTab.value === "active"
        ? activePlantations.value
        : expiredPlantations.value;
});

// ── Helpers ─────────────────────────────────────────

function formatCurrency(amount) {
    if (amount == null) return "—";
    return `₹${Number(amount).toLocaleString("en-IN", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    })}`;
}

function getLeaseExpense(plantationId) {
    return plantationExpenses.value.find(
        (e) =>
            e.plantation_id === plantationId &&
            e.category?.name?.toLowerCase() === "lease cost",
    );
}

function formatDate(dateStr) {
    if (!dateStr) return "—";
    const d = new Date(dateStr);
    return d.toLocaleDateString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric",
    });
}

function toISODate(dateStr) {
    if (!dateStr) return "";
    const d = new Date(dateStr);
    return d.toISOString().split("T")[0];
}

function isExpired(p) {
    if (!p) return false;
    return new Date(p.lease_end) < new Date();
}

function leaseStatusClass(p) {
    const now = new Date();
    const end = new Date(p.lease_end);
    const start = new Date(p.lease_start);
    if (now < start) return "status-upcoming";
    if (now > end) return "status-expired";
    const daysLeft = (end - now) / (1000 * 60 * 60 * 24);
    if (daysLeft <= 90) return "status-expiring";
    return "status-active";
}

function leaseStatusIcon(p) {
    const cls = leaseStatusClass(p);
    if (cls === "status-active") return "bi-check-circle-fill";
    if (cls === "status-expiring") return "bi-exclamation-triangle-fill";
    if (cls === "status-expired") return "bi-x-circle-fill";
    return "bi-clock-fill";
}

function leaseStatusLabel(p) {
    const cls = leaseStatusClass(p);
    if (cls === "status-active") return "Active";
    if (cls === "status-expiring") return "Expiring Soon";
    if (cls === "status-expired") return "Expired";
    return "Upcoming";
}

// ── Location Search ─────────────────────────────────

function onLocationSearch() {
    const q = locationQuery.value.trim();
    if (q.length < 2) {
        locationPredictions.value = [];
        showPredictions.value = false;
        return;
    }
    clearTimeout(locationSearchTimer);
    locationSearchTimer = setTimeout(() => fetchLocationPredictions(q), 300);
}

async function fetchLocationPredictions(query) {
    locationSearching.value = true;
    try {
        const res = await api.get("/api/weather/search-locations", {
            params: { query },
        });
        locationPredictions.value = res.data.predictions || [];
        showPredictions.value = locationPredictions.value.length > 0;
    } catch (e) {
        console.error("Location search failed:", e);
        locationPredictions.value = [];
    } finally {
        locationSearching.value = false;
    }
}

async function selectPrediction(pred) {
    showPredictions.value = false;
    locationQuery.value = "";
    locationPredictions.value = [];
    locationSearching.value = true;

    try {
        const res = await api.get("/api/weather/place-details", {
            params: { place_id: pred.place_id },
        });
        const details = res.data;
        const components = details.address_components || [];

        let city = details.name || pred.main_text;
        let state = null;
        let country = null;

        for (const c of components) {
            if (c.types.includes("administrative_area_level_1"))
                state = c.long_name;
            if (c.types.includes("country")) country = c.long_name;
        }

        form.value.location = {
            city,
            state,
            country,
            latitude: details.latitude,
            longitude: details.longitude,
        };
    } catch (e) {
        console.error("Place details fetch failed:", e);
    } finally {
        locationSearching.value = false;
    }
}

function clearLocation() {
    form.value.location = null;
    locationQuery.value = "";
    locationPredictions.value = [];
}

function hidePredictionsDelayed() {
    setTimeout(() => {
        showPredictions.value = false;
    }, 200);
}

// ── Modal Handlers ──────────────────────────────────

function openAddModal() {
    isEditing.value = false;
    editingId.value = null;
    editingPlantation.value = null;
    form.value = getEmptyForm();
    locationQuery.value = "";
    locationPredictions.value = [];
    if (!bsFormModal) bsFormModal = new Modal(formModalRef.value);
    bsFormModal.show();
}

function openEditModal(p) {
    isEditing.value = true;
    editingId.value = p.id;
    editingPlantation.value = p;
    form.value = {
        name: p.name,
        lease_start: toISODate(p.lease_start),
        lease_end: toISODate(p.lease_end),
        location: p.location ? { ...p.location } : null,
    };
    locationQuery.value = "";
    locationPredictions.value = [];
    if (!bsFormModal) bsFormModal = new Modal(formModalRef.value);
    bsFormModal.show();
}

async function openDeleteModal(p) {
    deleteTarget.value = p;
    deleteHasHistory.value = false;
    deleteHistoryCount.value = 0;

    // Check for lease history
    try {
        const res = await api.get(`/plantations/${p.id}/delete-check`);
        deleteHasHistory.value = res.data.has_history;
        deleteHistoryCount.value = res.data.history_count;
    } catch (error) {
        console.error("Failed to check delete:", error);
    }

    if (!bsDeleteModal) bsDeleteModal = new Modal(deleteModalRef.value);
    bsDeleteModal.show();
}

async function openDetailsModal(p) {
    detailsTarget.value = p;
    leaseHistory.value = [];
    if (!bsDetailsModal) bsDetailsModal = new Modal(detailsModalRef.value);
    bsDetailsModal.show();

    try {
        const res = await api.get(`/plantations/${p.id}/lease-history`);
        leaseHistory.value = res.data;
    } catch (error) {
        console.error("Failed to fetch lease history:", error);
    }
}

// ── Lease Cost Modal ────────────────────────────────

function openLeaseCostModal(p) {
    leaseCostTarget.value = p;
    leaseCostAmount.value = null;
    if (!bsLeaseCostModal)
        bsLeaseCostModal = new Modal(leaseCostModalRef.value);
    bsLeaseCostModal.show();
}

async function submitLeaseCost() {
    if (
        !leaseCostTarget.value ||
        !leaseCostAmount.value ||
        !leaseCostCategoryId.value
    )
        return;

    const payload = {
        date: new Date(leaseCostTarget.value.lease_start).toISOString(),
        amount: leaseCostAmount.value,
        category_id: leaseCostCategoryId.value,
        plantation_id: leaseCostTarget.value.id,
        description: `Lease cost for ${leaseCostTarget.value.name}`,
    };

    try {
        const response = await api.post("/expenses/", payload);
        plantationExpenses.value.push(response.data);
        bsLeaseCostModal.hide();
    } catch (error) {
        console.error("Failed to add lease cost:", error);
    }
}

// ── API Functions ───────────────────────────────────

async function fetchExpenseCategories() {
    try {
        const response = await api.get("/settings/expense-categories");
        expenseCategories.value = response.data;
    } catch (error) {
        console.error("Failed to fetch expense categories:", error);
    }
}

async function fetchAllExpenses() {
    try {
        const response = await api.get("/expenses/");
        plantationExpenses.value = response.data;
    } catch (error) {
        console.error("Failed to fetch expenses:", error);
    }
}

async function fetchPlantations() {
    try {
        const response = await api.get("/plantations/");
        plantations.value = response.data;
        console.log(plantations.value);
    } catch (error) {
        console.error("Failed to fetch plantations:", error);
    }
}

async function handleFormSubmit() {
    if (!isFormValid.value) return;

    const payload = {
        name: form.value.name,
        lease_start: new Date(form.value.lease_start).toISOString(),
        lease_end: new Date(form.value.lease_end).toISOString(),
    };

    if (form.value.location) {
        payload.location = {
            city: form.value.location.city,
            state: form.value.location.state || null,
            country: form.value.location.country || null,
            latitude: form.value.location.latitude,
            longitude: form.value.location.longitude,
        };
    }

    if (isEditing.value) {
        await updatePlantation(editingId.value, payload);
    } else {
        await addPlantation(payload);
    }
    bsFormModal.hide();
}

async function addPlantation(data) {
    try {
        const response = await api.post("/plantations/", data);
        plantations.value.push(response.data);
    } catch (error) {
        console.error("Failed to add plantation:", error);
    }
}

async function updatePlantation(id, data) {
    try {
        const response = await api.put(`/plantations/${id}`, data);
        const idx = plantations.value.findIndex((p) => p.id === id);
        if (idx !== -1) plantations.value[idx] = response.data;
    } catch (error) {
        console.error("Failed to update plantation:", error);
    }
}

async function confirmDelete() {
    if (!deleteTarget.value) return;
    await deletePlantation(deleteTarget.value.id, deleteHasHistory.value);
    bsDeleteModal.hide();
}

async function deletePlantation(id, force = false) {
    try {
        const url = force
            ? `/plantations/${id}?force=true`
            : `/plantations/${id}`;
        await api.delete(url);
        plantations.value = plantations.value.filter((p) => p.id !== id);
    } catch (error) {
        console.error("Failed to delete plantation:", error);
    }
}

// ── Lifecycle ───────────────────────────────────────

onMounted(async () => {
    await Promise.all([
        fetchPlantations(),
        fetchExpenseCategories(),
        fetchAllExpenses(),
    ]);
});

onBeforeUnmount(() => {
    bsFormModal?.dispose();
    bsDeleteModal?.dispose();
    bsLeaseCostModal?.dispose();
    bsDetailsModal?.dispose();
});
</script>

<style scoped>
/* ── Page Layout ────────────────────────────── */
.plantations-page {
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

/* ── Tab Bar ────────────────────────────────── */
.tab-bar {
    display: flex;
    gap: 6px;
    margin-bottom: 20px;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    padding-bottom: 2px;
}

.tab-btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 10px 18px;
    border: 1.5px solid var(--border);
    border-radius: 10px;
    background: transparent;
    color: var(--text-secondary);
    font-family: var(--font-body);
    font-size: 0.84rem;
    font-weight: 500;
    cursor: pointer;
    transition: all var(--transition-fast);
    white-space: nowrap;
    flex-shrink: 0;
}

.tab-btn:hover {
    border-color: var(--sage);
    color: var(--text-primary);
    background: rgba(138, 154, 123, 0.06);
}

.tab-btn.active {
    border-color: var(--moss);
    color: var(--moss);
    background: rgba(74, 103, 65, 0.08);
    font-weight: 600;
}

.tab-btn i {
    font-size: 1rem;
}

.tab-label {
    display: inline;
}

.tab-count {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 22px;
    height: 22px;
    padding: 0 6px;
    border-radius: 11px;
    background: var(--border-light);
    font-size: 0.72rem;
    font-weight: 700;
    color: var(--text-secondary);
    transition: all var(--transition-fast);
}

.tab-btn.active .tab-count {
    background: var(--moss-faded);
    color: var(--moss);
}

/* ── Table ──────────────────────────────────── */
.table-wrapper {
    background: var(--bg-card);
    border: 1px solid var(--border-light);
    border-radius: 14px;
    overflow: hidden;
    box-shadow: var(--shadow-sm);
}

.table-expired {
    opacity: 0.85;
}

.table-scroll {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
}

.data-table {
    width: 100%;
    min-width: 750px;
    border-collapse: collapse;
}

.data-table thead th {
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

.data-table tbody tr {
    transition: background var(--transition-fast);
}

.data-table tbody tr:hover {
    background: rgba(138, 154, 123, 0.06);
}

.data-table tbody td {
    padding: 12px 18px;
    border-bottom: 1px solid var(--border-light);
    vertical-align: middle;
    font-size: 0.88rem;
}

.data-table tbody tr:last-child td {
    border-bottom: none;
}

/* ── Plantation Identity ─────────────────────── */
.plantation-identity {
    display: flex;
    align-items: center;
    gap: 12px;
}

.plantation-icon {
    width: 36px;
    height: 36px;
    border-radius: 10px;
    background: var(--moss-faded);
    color: var(--moss);
    font-size: 1rem;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.plantation-icon-expired {
    background: rgba(181, 105, 77, 0.1);
    color: var(--sienna);
}

.plantation-name {
    font-weight: 600;
    font-size: 0.9rem;
    color: var(--text-primary);
    white-space: nowrap;
}

/* ── Date Cells ──────────────────────────────── */
.date-cell {
    font-variant-numeric: tabular-nums;
    color: var(--text-secondary);
    font-size: 0.85rem;
}

/* ── Status Chips ────────────────────────────── */
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

.status-expiring {
    background: rgba(196, 163, 90, 0.14);
    color: #8a6f2a;
}

.status-expired {
    background: rgba(181, 105, 77, 0.1);
    color: var(--sienna);
}

.status-upcoming {
    background: rgba(138, 154, 123, 0.14);
    color: var(--sage);
}

/* ── Lease Cost ──────────────────────────────── */
.cost-chip {
    display: inline-flex;
    align-items: center;
    font-size: 0.82rem;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 20px;
    background: rgba(74, 103, 65, 0.1);
    color: var(--moss);
    font-variant-numeric: tabular-nums;
}

.cost-chip-muted {
    background: rgba(107, 109, 107, 0.1);
    color: var(--text-secondary);
}

.btn-lease-cost {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 10px;
    border: 1.5px dashed var(--border);
    border-radius: 20px;
    background: transparent;
    color: var(--text-secondary);
    font-size: 0.78rem;
    font-weight: 500;
    cursor: pointer;
    transition: all var(--transition-fast);
    font-family: var(--font-body);
}

.btn-lease-cost:hover {
    border-color: var(--moss);
    color: var(--moss);
    background: rgba(74, 103, 65, 0.04);
}

.btn-lease-cost i {
    font-size: 0.8rem;
}

.btn-lease-cost-sm {
    padding: 2px 8px;
    font-size: 0.72rem;
    margin-top: 2px;
}

.icon-lease {
    background: rgba(196, 163, 90, 0.12);
    color: #8a6f2a;
}

.icon-history {
    background: rgba(138, 154, 123, 0.14);
    color: var(--sage);
}

.alert-missing-category {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 14px 16px;
    border-radius: 10px;
    background: rgba(181, 105, 77, 0.08);
    border: 1px solid rgba(181, 105, 77, 0.2);
    font-size: 0.84rem;
    color: var(--text-primary);
    line-height: 1.5;
    text-align: left;
}

.alert-missing-category i {
    color: var(--sienna);
    font-size: 1.1rem;
    flex-shrink: 0;
    margin-top: 1px;
}

.alert-missing-category a {
    color: var(--moss);
    font-weight: 600;
    text-decoration: underline;
}

/* ── Action Buttons ──────────────────────────── */
.action-group {
    display: flex;
    align-items: center;
    gap: 6px;
    justify-content: flex-end;
}

.action-group-mobile {
    justify-content: flex-start;
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

.btn-details:hover:not(:disabled) {
    border-color: var(--sage);
    color: var(--sage);
    background: rgba(138, 154, 123, 0.08);
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

/* ── Mobile Cards ────────────────────────────── */
.plantation-card {
    background: var(--bg-card);
    border: 1px solid var(--border-light);
    border-radius: 14px;
    margin-bottom: 12px;
    box-shadow: var(--shadow-sm);
    overflow: hidden;
}

.plantation-card-expired {
    opacity: 0.85;
}

.plantation-card-header {
    padding: 16px 16px 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
}

.plantation-card-body {
    padding: 12px 16px 16px;
}

.lease-dates {
    display: flex;
    gap: 20px;
    margin-bottom: 14px;
    flex-wrap: wrap;
}

.lease-date-item {
    display: flex;
    flex-direction: column;
    gap: 2px;
}

.lease-label {
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--text-secondary);
}

.lease-value {
    font-size: 0.85rem;
    font-weight: 500;
    color: var(--text-primary);
    font-variant-numeric: tabular-nums;
}

.plantation-card .btn-action {
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

/* ── History Timeline ────────────────────────── */
.history-current {
    background: rgba(74, 103, 65, 0.06);
    border: 1px solid rgba(74, 103, 65, 0.15);
    border-radius: 10px;
    padding: 12px 16px;
    text-align: left;
}

.history-badge {
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 6px;
}

.history-badge-current {
    color: var(--moss);
}

.history-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
}

.history-dates {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.84rem;
    font-weight: 500;
    color: var(--text-primary);
    font-variant-numeric: tabular-nums;
}

.history-dates i {
    font-size: 0.7rem;
    color: var(--text-secondary);
}

.history-timeline {
    margin-top: 16px;
    text-align: left;
}

.history-item {
    display: flex;
    gap: 14px;
    min-height: 48px;
}

.history-connector {
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 16px;
    flex-shrink: 0;
}

.history-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: var(--border);
    flex-shrink: 0;
    margin-top: 6px;
}

.history-line {
    width: 2px;
    flex: 1;
    background: var(--border-light);
    margin: 4px 0;
}

.history-content {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    flex: 1;
    padding-bottom: 14px;
    border-bottom: 1px solid var(--border-light);
}

.history-item:last-child .history-content {
    border-bottom: none;
    padding-bottom: 0;
}

/* ── Form Modal ──────────────────────────────── */
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

.plantation-form {
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

.modal-hint {
    font-size: 0.8rem;
    color: var(--sage);
    margin: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
}

.modal-hint i {
    font-size: 0.85rem;
}

/* ── Confirm / Delete Modal ──────────────────── */
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

/* ── Modal Footer ────────────────────────────── */
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

/* ── Location ────────────────────────────────── */
.location-cell {
    font-size: 0.84rem;
    color: var(--text-secondary);
}

.location-text {
    display: inline-flex;
    align-items: center;
    gap: 4px;
}

.location-text i {
    font-size: 0.8rem;
    color: var(--sage);
}

.card-location {
    font-size: 0.78rem;
    color: var(--text-secondary);
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 4px;
}

.card-location i {
    font-size: 0.8rem;
    color: var(--sage);
}

/* Location search in form */
.location-search-wrapper {
    position: relative;
}

.location-search-input-wrap {
    position: relative;
}

.location-search-icon {
    position: absolute;
    left: 12px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 0.85rem;
    color: var(--text-secondary);
    pointer-events: none;
}

.location-search-input {
    padding-left: 34px !important;
    padding-right: 34px !important;
}

.location-spinner {
    position: absolute;
    right: 12px;
    top: 50%;
    transform: translateY(-50%);
    color: var(--sage);
    font-size: 0.9rem;
}

.spin {
    display: inline-block;
    animation: spin 0.8s linear infinite;
}

@keyframes spin {
    from {
        transform: rotate(0deg);
    }
    to {
        transform: rotate(360deg);
    }
}

.location-dropdown {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    z-index: 50;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    margin-top: 4px;
    box-shadow: var(--shadow-md);
    max-height: 220px;
    overflow-y: auto;
}

.location-dropdown-item {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    width: 100%;
    padding: 10px 14px;
    border: none;
    background: transparent;
    text-align: left;
    cursor: pointer;
    transition: background var(--transition-fast);
    font-family: var(--font-body);
}

.location-dropdown-item:hover {
    background: rgba(138, 154, 123, 0.08);
}

.location-dropdown-item:not(:last-child) {
    border-bottom: 1px solid var(--border-light);
}

.location-dropdown-item i {
    color: var(--sage);
    font-size: 0.95rem;
    margin-top: 2px;
    flex-shrink: 0;
}

.loc-main {
    font-size: 0.85rem;
    font-weight: 500;
    color: var(--text-primary);
}

.loc-secondary {
    font-size: 0.75rem;
    color: var(--text-secondary);
    margin-top: 1px;
}

.location-chip {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    border-radius: 10px;
    background: rgba(138, 154, 123, 0.1);
    border: 1px solid rgba(138, 154, 123, 0.2);
    font-size: 0.85rem;
    color: var(--text-primary);
}

.location-chip i {
    color: var(--sage);
    font-size: 0.9rem;
}

.location-chip-clear {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 20px;
    height: 20px;
    border: none;
    border-radius: 50%;
    background: rgba(0, 0, 0, 0.08);
    color: var(--text-secondary);
    font-size: 0.65rem;
    cursor: pointer;
    padding: 0;
    margin-left: 2px;
    transition: all var(--transition-fast);
}

.location-chip-clear:hover {
    background: rgba(181, 105, 77, 0.15);
    color: var(--sienna);
}

/* ── Responsive ──────────────────────────────── */
@media (max-width: 767.98px) {
    .plantations-page {
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

    .tab-bar {
        gap: 4px;
        margin-bottom: 16px;
    }

    .tab-btn {
        padding: 8px 12px;
        font-size: 0.78rem;
        gap: 6px;
    }

    .tab-label {
        display: none;
    }

    .tab-btn.active .tab-label {
        display: inline;
    }

    .history-dates {
        font-size: 0.78rem;
    }
}
</style>

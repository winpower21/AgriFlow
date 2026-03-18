<template>
    <div class="settings-page">
        <!-- Page Header -->
        <div class="page-header animate-fade-in-up">
            <div>
                <h2 class="page-title">Settings</h2>
                <p class="page-subtitle">
                    Manage transformation types, wage types, batch stages &
                    expense categories
                </p>
            </div>
        </div>

        <!-- Tab Navigation -->
        <div class="tab-bar animate-fade-in-up animate-delay-1">
            <button
                v-for="tab in tabs"
                :key="tab.key"
                class="tab-btn"
                :class="{ active: activeTab === tab.key }"
                @click="activeTab = tab.key"
            >
                <i class="bi" :class="tab.icon"></i>
                <span class="tab-label">{{ tab.label }}</span>
                <span class="tab-count">{{ getItems(tab.key).length }}</span>
            </button>
        </div>

        <!-- Content Panel -->
        <div class="content-panel animate-fade-in-up animate-delay-2">
            <!-- Unit Conversion Panel — shown only when this tab is active -->
            <div v-if="activeTab === 'unitConversion'" class="conversion-panel">
                <div class="conversion-field">
                    <label class="conversion-label">
                        <i class="bi bi-rulers"></i>
                        Hectares to Acres conversion rate
                    </label>
                    <p class="conversion-hint">
                        1 hectare = <strong>X</strong> acres. Standard value is 2.47105.
                        Regional values in India may vary between 2.47 and 2.50.
                    </p>
                    <div class="conversion-input-row">
                        <input
                            v-model="hectaresToAcresRate"
                            type="number"
                            step="0.00001"
                            min="0.1"
                            class="form-control conversion-input"
                            placeholder="e.g. 2.47105"
                        />
                        <button
                            class="btn-add"
                            :disabled="rateLoading || !hectaresToAcresRate"
                            @click="saveConversionRate"
                        >
                            <i v-if="rateSaved" class="bi bi-check-lg"></i>
                            <i v-else-if="rateLoading" class="bi bi-hourglass-split"></i>
                            <i v-else class="bi bi-floppy"></i>
                            <span>{{ rateSaved ? "Saved!" : "Save" }}</span>
                        </button>
                    </div>
                </div>
            </div>

            <!-- Add Row -->
            <div v-if="activeTab !== 'unitConversion'" class="add-row">
                <div class="add-inputs">
                    <input
                        v-model="newItem.name"
                        type="text"
                        class="form-control"
                        :placeholder="addPlaceholder"
                        @keydown.enter="handleAdd"
                    />
                    <input
                        v-if="hasDescription"
                        v-model="newItem.description"
                        type="text"
                        class="form-control"
                        placeholder="Description (optional)"
                        @keydown.enter="handleAdd"
                    />
                    <label v-if="isBatchStages" class="salable-toggle">
                        <input type="checkbox" v-model="newItem.is_salable" />
                        <span class="salable-label">Salable</span>
                    </label>
                </div>
                <button
                    class="btn-add"
                    :disabled="!newItem.name.trim()"
                    @click="handleAdd"
                >
                    <i class="bi bi-plus-lg"></i>
                    <span>Add</span>
                </button>
            </div>

            <!-- Items List -->
            <TransitionGroup v-if="activeTab !== 'unitConversion'" name="list" tag="div" class="items-list">
                <div
                    v-for="item in getItems(activeTab)"
                    :key="item.id"
                    class="item-row"
                    :class="{ editing: editingId === item.id }"
                >
                    <!-- View Mode -->
                    <template v-if="editingId !== item.id">
                        <div class="item-info">
                            <span class="item-id">#{{ item.id }}</span>
                            <span class="item-name">{{ item.name }}</span>
                            <span
                                v-if="item.description"
                                class="item-desc"
                            >
                                {{ item.description }}
                            </span>
                            <span v-if="isBatchStages && item.is_salable" class="salable-badge">Salable</span>
                        </div>
                        <div class="item-actions">
                            <button
                                class="btn-action btn-edit"
                                title="Edit"
                                @click="startEdit(item)"
                            >
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button
                                class="btn-action btn-delete"
                                title="Delete"
                                @click="openDeleteModal(item)"
                            >
                                <i class="bi bi-trash3"></i>
                            </button>
                        </div>
                    </template>

                    <!-- Edit Mode -->
                    <template v-else>
                        <div class="edit-inputs">
                            <input
                                v-model="editForm.name"
                                type="text"
                                class="form-control form-control-sm"
                                placeholder="Name"
                                @keydown.enter="saveEdit"
                                @keydown.escape="cancelEdit"
                                ref="editNameInput"
                            />
                            <input
                                v-if="hasDescription"
                                v-model="editForm.description"
                                type="text"
                                class="form-control form-control-sm"
                                placeholder="Description"
                                @keydown.enter="saveEdit"
                                @keydown.escape="cancelEdit"
                            />
                            <label v-if="isBatchStages" class="salable-toggle">
                                <input type="checkbox" v-model="editForm.is_salable" />
                                <span class="salable-label">Salable</span>
                            </label>
                        </div>
                        <div class="item-actions">
                            <button
                                class="btn-action btn-save"
                                title="Save"
                                :disabled="!editForm.name.trim()"
                                @click="saveEdit"
                            >
                                <i class="bi bi-check-lg"></i>
                            </button>
                            <button
                                class="btn-action btn-cancel"
                                title="Cancel"
                                @click="cancelEdit"
                            >
                                <i class="bi bi-x-lg"></i>
                            </button>
                        </div>
                    </template>
                </div>
            </TransitionGroup>

            <!-- Empty State -->
            <div
                v-if="activeTab !== 'unitConversion' && getItems(activeTab).length === 0"
                class="empty-state"
            >
                <i class="bi" :class="currentTab.icon"></i>
                <p>No {{ currentTab.label.toLowerCase() }} yet</p>
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
                        <h5 class="modal-title">Delete Item</h5>
                        <p class="modal-desc">
                            Remove
                            <strong>{{ deleteTarget?.name }}</strong
                            >? This may affect related records.
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
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from "vue";
import { Modal } from "bootstrap";
import api from "../utils/api";

// ── Tab Config ──────────────────────────────────────

const tabs = [
    {
        key: "transformationTypes",
        label: "Transformation Types",
        icon: "bi-arrow-repeat",
        endpoint: "/settings/transformation-types",
    },
    {
        key: "wageTypes",
        label: "Wage Types",
        icon: "bi-cash-coin",
        endpoint: "/settings/wage-types",
    },
    {
        key: "batchStages",
        label: "Batch Stages",
        icon: "bi-layers",
        endpoint: "/settings/batch-stages",
    },
    {
        key: "expenseCategories",
        label: "Expense Categories",
        icon: "bi-receipt",
        endpoint: "/settings/expense-categories",
    },
    {
        key: "unitConversion",
        label: "Unit Conversion",
        icon: "bi-rulers",
        endpoint: null,
    },
];

const activeTab = ref("transformationTypes");

const currentTab = computed(() => tabs.find((t) => t.key === activeTab.value));

const addPlaceholder = computed(() => {
    const map = {
        transformationTypes: "e.g. HARVEST, CLEAN, DRY...",
        wageTypes: "e.g. Daily, Per KG...",
        batchStages: "e.g. HARVESTED, CLEANED...",
        expenseCategories: "e.g. Fuel, Lease Cost, Maintenance...",
    };
    return map[activeTab.value];
});

const hasDescription = computed(() => {
    return (
        activeTab.value === "transformationTypes" ||
        activeTab.value === "expenseCategories"
    );
});

const isBatchStages = computed(() => activeTab.value === "batchStages");

// ── Data ────────────────────────────────────────────

const transformationTypes = ref([]);
const wageTypes = ref([]);
const batchStages = ref([]);
const expenseCategories = ref([]);

// ── Unit Conversion ──────────────────────────────────────
const hectaresToAcresRate = ref("");
const rateLoading = ref(false);
const rateSaved = ref(false);

async function fetchConversionRate() {
    try {
        const res = await api.get("/settings/app-config/hectares_to_acres_rate");
        hectaresToAcresRate.value = res.data.value;
    } catch {
        // Key not yet set in DB — use default
        hectaresToAcresRate.value = "2.47105";
    }
}

async function saveConversionRate() {
    if (!hectaresToAcresRate.value) return;
    rateLoading.value = true;
    try {
        await api.put("/settings/app-config/hectares_to_acres_rate", {
            value: String(hectaresToAcresRate.value),
        });
        rateSaved.value = true;
        setTimeout(() => (rateSaved.value = false), 2000);
    } catch (error) {
        console.error("Failed to save conversion rate:", error);
    } finally {
        rateLoading.value = false;
    }
}

function getItems(key) {
    if (key === "unitConversion") return [];
    const map = {
        transformationTypes: transformationTypes,
        wageTypes: wageTypes,
        batchStages: batchStages,
        expenseCategories: expenseCategories,
    };
    return map[key]?.value || [];
}

function getEndpoint(key) {
    return tabs.find((t) => t.key === (key || activeTab.value))?.endpoint;
}

function getRef(key) {
    const map = {
        transformationTypes: transformationTypes,
        wageTypes: wageTypes,
        batchStages: batchStages,
        expenseCategories: expenseCategories,
    };
    return map[key || activeTab.value];
}

// ── Add ─────────────────────────────────────────────

const newItem = ref({ name: "", description: "", is_salable: false });

async function handleAdd() {
    if (!newItem.value.name.trim()) return;

    const payload = { name: newItem.value.name.trim() };
    if (hasDescription.value && newItem.value.description.trim()) {
        payload.description = newItem.value.description.trim();
    }
    if (isBatchStages.value) {
        payload.is_salable = newItem.value.is_salable;
    }

    try {
        const response = await api.post(getEndpoint(), payload);
        getRef().value.push(response.data);
        newItem.value = { name: "", description: "", is_salable: false };
    } catch (error) {
        console.error("Failed to add item:", error);
    }
}

// ── Inline Edit ─────────────────────────────────────

const editingId = ref(null);
const editForm = ref({ name: "", description: "", is_salable: false });
const editNameInput = ref(null);

function startEdit(item) {
    editingId.value = item.id;
    editForm.value = {
        name: item.name,
        description: item.description || "",
        is_salable: item.is_salable || false,
    };
    nextTick(() => {
        const inputs = document.querySelectorAll(
            ".item-row.editing .form-control-sm",
        );
        if (inputs.length) inputs[0].focus();
    });
}

function cancelEdit() {
    editingId.value = null;
    editForm.value = { name: "", description: "", is_salable: false };
}

async function saveEdit() {
    if (!editForm.value.name.trim()) return;

    const payload = { name: editForm.value.name.trim() };
    if (hasDescription.value) {
        payload.description = editForm.value.description.trim() || null;
    }
    if (isBatchStages.value) {
        payload.is_salable = editForm.value.is_salable;
    }

    try {
        const response = await api.put(
            `${getEndpoint()}/${editingId.value}`,
            payload,
        );
        const items = getRef().value;
        const idx = items.findIndex((i) => i.id === editingId.value);
        if (idx !== -1) items[idx] = response.data;
        cancelEdit();
    } catch (error) {
        console.error("Failed to update item:", error);
    }
}

// ── Delete ──────────────────────────────────────────

const deleteModalRef = ref(null);
let bsDeleteModal = null;
const deleteTarget = ref(null);

function openDeleteModal(item) {
    deleteTarget.value = item;
    if (!bsDeleteModal) bsDeleteModal = new Modal(deleteModalRef.value);
    bsDeleteModal.show();
}

async function confirmDelete() {
    if (!deleteTarget.value) return;
    try {
        await api.delete(`${getEndpoint()}/${deleteTarget.value.id}`);
        const items = getRef();
        items.value = items.value.filter((i) => i.id !== deleteTarget.value.id);
    } catch (error) {
        console.error("Failed to delete item:", error);
    }
    bsDeleteModal.hide();
}

// ── Fetch ───────────────────────────────────────────

async function fetchAll() {
    try {
        const [ttRes, wtRes, bsRes, ecRes] = await Promise.all([
            api.get("/settings/transformation-types"),
            api.get("/settings/wage-types"),
            api.get("/settings/batch-stages"),
            api.get("/settings/expense-categories"),
        ]);
        transformationTypes.value = ttRes.data;
        wageTypes.value = wtRes.data;
        batchStages.value = bsRes.data;
        expenseCategories.value = ecRes.data;
    } catch (error) {
        console.error("Failed to fetch settings:", error);
    }
    await fetchConversionRate();
}

// ── Lifecycle ───────────────────────────────────────

onMounted(fetchAll);

onBeforeUnmount(() => {
    bsDeleteModal?.dispose();
});
</script>

<style scoped>
/* ── Page Layout ────────────────────────────── */
.settings-page {
    max-width: 100vw;
}

.page-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 24px;
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

/* ── Content Panel ──────────────────────────── */
.content-panel {
    background: var(--bg-card);
    border: 1px solid var(--border-light);
    border-radius: 14px;
    box-shadow: var(--shadow-sm);
    overflow: hidden;
}

/* ── Add Row ────────────────────────────────── */
.add-row {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 16px 18px;
    border-bottom: 1px solid var(--border-light);
    background: var(--parchment-deep);
}

.add-inputs {
    display: flex;
    gap: 8px;
    flex: 1;
    min-width: 0;
}

.add-inputs .form-control {
    font-size: 0.85rem;
    padding: 8px 12px;
}

.btn-add {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 16px;
    border: none;
    border-radius: 9px;
    background: var(--moss);
    color: var(--white);
    font-family: var(--font-body);
    font-size: 0.84rem;
    font-weight: 600;
    cursor: pointer;
    transition: all var(--transition-fast);
    white-space: nowrap;
    flex-shrink: 0;
}

.btn-add:hover:not(:disabled) {
    background: var(--moss-light);
    box-shadow: 0 4px 12px var(--moss-faded);
}

.btn-add:disabled {
    opacity: 0.4;
    cursor: not-allowed;
}

.btn-add i {
    font-size: 0.95rem;
}

/* ── Items List ─────────────────────────────── */
.items-list {
    position: relative;
}

.item-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 12px 18px;
    border-bottom: 1px solid var(--border-light);
    transition: background var(--transition-fast);
}

.item-row:last-child {
    border-bottom: none;
}

.item-row:hover {
    background: rgba(138, 154, 123, 0.04);
}

.item-row.editing {
    background: rgba(196, 163, 90, 0.06);
}

.item-info {
    display: flex;
    align-items: center;
    gap: 10px;
    flex: 1;
    min-width: 0;
}

.item-id {
    font-size: 0.72rem;
    font-weight: 600;
    color: var(--text-secondary);
    opacity: 0.6;
    font-variant-numeric: tabular-nums;
    flex-shrink: 0;
}

.item-name {
    font-weight: 600;
    font-size: 0.9rem;
    color: var(--text-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.item-desc {
    font-size: 0.8rem;
    color: var(--text-secondary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    flex-shrink: 1;
    min-width: 0;
}

.item-desc::before {
    content: "—";
    margin-right: 8px;
    opacity: 0.4;
}

/* ── Edit Inputs ────────────────────────────── */
.edit-inputs {
    display: flex;
    gap: 8px;
    flex: 1;
    min-width: 0;
}

.edit-inputs .form-control-sm {
    font-size: 0.85rem;
    padding: 6px 10px;
    border-radius: 7px;
}

/* ── Action Buttons ─────────────────────────── */
.item-actions {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-shrink: 0;
}

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

.btn-save {
    border-color: var(--moss);
    color: var(--moss);
}

.btn-save:hover:not(:disabled) {
    background: rgba(74, 103, 65, 0.1);
}

.btn-save:disabled {
    opacity: 0.3;
    cursor: not-allowed;
}

.btn-cancel {
    border-color: var(--border);
    color: var(--text-secondary);
}

.btn-cancel:hover {
    border-color: var(--sienna);
    color: var(--sienna);
    background: rgba(181, 105, 77, 0.06);
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

/* ── Delete Modal ───────────────────────────── */
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

.btn-modal-danger {
    background: var(--sienna);
}

.btn-modal-danger:hover {
    background: var(--sienna-light);
}

/* ── List Transitions ───────────────────────── */
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

/* ── Responsive ─────────────────────────────── */
@media (max-width: 767.98px) {
    .page-title {
        font-size: 1.35rem;
    }

    .page-header {
        margin-bottom: 18px;
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

    .add-row {
        flex-direction: column;
        gap: 8px;
        padding: 14px;
    }

    .add-inputs {
        flex-direction: column;
        width: 100%;
    }

    .btn-add {
        width: 100%;
        justify-content: center;
    }

    .item-row {
        padding: 10px 14px;
    }

    .item-info {
        flex-wrap: wrap;
        gap: 4px 10px;
    }

    .item-desc {
        width: 100%;
        padding-left: 0;
    }

    .item-desc::before {
        display: none;
    }

    .edit-inputs {
        flex-direction: column;
    }
}

@media (max-width: 575.98px) {
    .tab-btn {
        padding: 8px 10px;
        font-size: 0.75rem;
    }
}

/* ── Unit Conversion Panel ──────────────────────────── */
.conversion-panel {
    padding: 24px 18px;
}

.conversion-field {
    max-width: 420px;
}

.conversion-label {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
    font-size: 0.9rem;
    color: var(--text-primary);
    margin-bottom: 6px;
}

.conversion-label i {
    color: var(--sage);
    font-size: 1rem;
}

.conversion-hint {
    font-size: 0.82rem;
    color: var(--text-secondary);
    margin-bottom: 14px;
    line-height: 1.5;
}

.conversion-input-row {
    display: flex;
    gap: 10px;
    align-items: center;
}

.conversion-input {
    max-width: 180px;
    font-size: 0.9rem;
    padding: 8px 12px;
}

/* ── Salable Toggle & Badge ───────────────────── */
.salable-toggle {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    cursor: pointer;
    flex-shrink: 0;
    white-space: nowrap;
}

.salable-toggle input[type="checkbox"] {
    accent-color: var(--moss);
    width: 16px;
    height: 16px;
    cursor: pointer;
}

.salable-label {
    font-size: 0.82rem;
    font-weight: 500;
    color: var(--text-secondary);
}

.salable-badge {
    font-size: 0.7rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 6px;
    background: rgba(74, 103, 65, 0.1);
    color: var(--moss);
    flex-shrink: 0;
}
</style>

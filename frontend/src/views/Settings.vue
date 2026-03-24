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
                    <label v-if="isBatchStages" class="salable-toggle">
                        <input type="checkbox" v-model="newItem.is_waste" />
                        <span class="salable-label">Waste type</span>
                    </label>
                    <label v-if="isTransformationTypes" class="salable-toggle">
                        <input type="checkbox" v-model="newItem.measures_personnel_efficiency" />
                        <span class="salable-label">Measures Efficiency</span>
                    </label>
                    <label v-if="isTransformationTypes" class="salable-toggle">
                        <input type="checkbox" v-model="newItem.is_root" />
                        <span class="salable-label">Root (Harvest)</span>
                    </label>
                    <select v-if="isWageTypes" v-model="newItem.calculation_method" class="form-control form-select" style="max-width: 180px;">
                        <option value="DAILY">Wage (Daily)</option>
                        <option value="OUTPUT">Output (Per KG)</option>
                        <option value="MONTHLY">Salary (Monthly)</option>
                    </select>
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

            <!-- Batch Stages Tree View -->
            <div v-if="activeTab === 'batchStages'" class="stage-tree">
                <StageTreeLevel
                    :nodes="stageTree"
                    :depth="0"
                    :editing-id="editingId"
                    :edit-form="editForm"
                    :drag-state="dragState"
                    @start-edit="startEdit"
                    @save-edit="saveEdit"
                    @cancel-edit="cancelEdit"
                    @open-delete="openDeleteModal"
                    @open-icon-picker="openIconPicker"
                    @open-color-picker="openColorPicker"
                    @drag-start="onDragStart"
                    @drag-over="onDragOver"
                    @drag-leave="onDragLeave"
                    @drop="onDrop"
                    @drag-end="onDragEnd"
                />
            </div>

            <!-- Items List (non-batchStages tabs) -->
            <TransitionGroup v-if="activeTab !== 'unitConversion' && activeTab !== 'batchStages'" name="list" tag="div" class="items-list">
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
                            <span v-if="isTransformationTypes && item.measures_personnel_efficiency" class="salable-badge efficiency-badge">Efficiency</span>
                            <span v-if="isTransformationTypes && item.is_root" class="salable-badge">Root</span>
                            <span v-if="isWageTypes && item.calculation_method" class="salable-badge">{{ item.calculation_method }}</span>
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
                            <label v-if="isTransformationTypes" class="salable-toggle">
                                <input type="checkbox" v-model="editForm.measures_personnel_efficiency" />
                                <span class="salable-label">Measures Efficiency</span>
                            </label>
                            <label v-if="isTransformationTypes" class="salable-toggle">
                                <input type="checkbox" v-model="editForm.is_root" />
                                <span class="salable-label">Root (Harvest)</span>
                            </label>
                            <select v-if="isWageTypes" v-model="editForm.calculation_method" class="form-control form-control-sm form-select" style="max-width: 180px;">
                                <option value="DAILY">Wage (Daily)</option>
                                <option value="OUTPUT">Output (Per KG)</option>
                                <option value="MONTHLY">Salary (Monthly)</option>
                            </select>
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

            <!-- Loading State -->
            <div v-if="loading && activeTab !== 'unitConversion'" class="empty-state">
                <i class="bi bi-hourglass-split"></i>
                <p>Loading settings...</p>
            </div>
            <!-- Empty State -->
            <div
                v-else-if="activeTab !== 'unitConversion' && getItems(activeTab).length === 0"
                class="empty-state"
            >
                <i class="bi" :class="currentTab.icon"></i>
                <p>No {{ currentTab.label.toLowerCase() }} yet</p>
            </div>
        </div>

        <!-- Icon Picker Popover (outside content-panel to avoid overflow:hidden clipping) -->
        <div v-if="iconPickerStageId" class="picker-overlay" @click.self="closeIconPicker">
            <div class="picker-popover icon-picker" :style="pickerPosition">
                <div class="picker-header">
                    <span class="picker-title">Choose Icon</span>
                    <button class="picker-close" @click="closeIconPicker">
                        <i class="bi bi-x-lg"></i>
                    </button>
                </div>
                <div class="icon-grid">
                    <button
                        v-for="icon in STAGE_ICONS"
                        :key="icon.class"
                        class="icon-option"
                        :class="{ selected: getStageById(iconPickerStageId)?.icon === icon.class }"
                        :title="icon.label"
                        @click="selectIcon(icon.class)"
                    >
                        <i class="bi" :class="icon.class"></i>
                    </button>
                </div>
            </div>
        </div>

        <!-- Color Picker Popover (outside content-panel to avoid overflow:hidden clipping) -->
        <div v-if="colorPickerStageId" class="picker-overlay" @click.self="closeColorPicker">
            <div class="picker-popover color-picker" :style="pickerPosition">
                <div class="picker-header">
                    <span class="picker-title">Choose Color</span>
                    <button class="picker-close" @click="closeColorPicker">
                        <i class="bi bi-x-lg"></i>
                    </button>
                </div>
                <div class="color-grid">
                    <button
                        v-for="color in STAGE_COLORS"
                        :key="color"
                        class="color-option"
                        :class="{ selected: getStageById(colorPickerStageId)?.color === color }"
                        :style="{ background: color }"
                        @click="selectColor(color)"
                    >
                        <i v-if="getStageById(colorPickerStageId)?.color === color" class="bi bi-check-lg"></i>
                    </button>
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
import { ref, computed, onMounted, onBeforeUnmount, nextTick, defineComponent, h } from "vue";
import { Modal } from "bootstrap";
import api from "../utils/api";
import { STAGE_COLORS, STAGE_ICONS, DEFAULT_STAGE_COLOR, DEFAULT_STAGE_ICON } from "@/utils/colorPalette";

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
const isTransformationTypes = computed(() => activeTab.value === "transformationTypes");
const isWageTypes = computed(() => activeTab.value === "wageTypes");

// ── Data ────────────────────────────────────────────

const loading = ref(true);
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

const newItem = ref({ name: "", description: "", is_salable: false, is_waste: false, measures_personnel_efficiency: true, is_root: false, calculation_method: "DAILY" });

async function handleAdd() {
    if (!newItem.value.name.trim()) return;

    const payload = { name: newItem.value.name.trim() };
    if (hasDescription.value && newItem.value.description.trim()) {
        payload.description = newItem.value.description.trim();
    }
    if (isBatchStages.value) {
        payload.is_salable = newItem.value.is_salable;
        payload.is_waste = newItem.value.is_waste;
    }
    if (isTransformationTypes.value) {
        payload.measures_personnel_efficiency = newItem.value.measures_personnel_efficiency;
        payload.is_root = newItem.value.is_root;
    }
    if (isWageTypes.value) {
        payload.calculation_method = newItem.value.calculation_method;
    }

    try {
        const response = await api.post(getEndpoint(), payload);
        getRef().value.push(response.data);
        newItem.value = { name: "", description: "", is_salable: false, is_waste: false, measures_personnel_efficiency: true, is_root: false, calculation_method: "DAILY" };
    } catch (error) {
        console.error("Failed to add item:", error);
    }
}

// ── Inline Edit ─────────────────────────────────────

const editingId = ref(null);
const editForm = ref({ name: "", description: "", is_salable: false, is_waste: false, measures_personnel_efficiency: true, is_root: false, calculation_method: "DAILY" });
const editNameInput = ref(null);

function startEdit(item) {
    editingId.value = item.id;
    editForm.value = {
        name: item.name,
        description: item.description || "",
        is_salable: item.is_salable || false,
        is_waste: item.is_waste || false,
        measures_personnel_efficiency: item.measures_personnel_efficiency ?? true,
        is_root: item.is_root || false,
        calculation_method: item.calculation_method || "DAILY",
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
    editForm.value = { name: "", description: "", is_salable: false, is_waste: false, measures_personnel_efficiency: true, is_root: false, calculation_method: "DAILY" };
}

async function saveEdit() {
    if (!editForm.value.name.trim()) return;

    const payload = { name: editForm.value.name.trim() };
    if (hasDescription.value) {
        payload.description = editForm.value.description.trim() || null;
    }
    if (isBatchStages.value) {
        payload.is_salable = editForm.value.is_salable;
        payload.is_waste = editForm.value.is_waste;
    }
    if (isTransformationTypes.value) {
        payload.measures_personnel_efficiency = editForm.value.measures_personnel_efficiency;
        payload.is_root = editForm.value.is_root;
    }
    if (isWageTypes.value) {
        payload.calculation_method = editForm.value.calculation_method;
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
    } finally {
        loading.value = false;
    }
    await fetchConversionRate();
}

// ── Batch Stage Tree ────────────────────────────────

const stageTree = computed(() => {
    const stages = batchStages.value;
    if (!stages.length) return [];
    return buildTree(stages, null);
});

function buildTree(stages, parentId) {
    return stages
        .filter((s) => (s.parent_id ?? null) === parentId)
        .sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0))
        .map((s) => ({
            ...s,
            children: buildTree(stages, s.id),
        }));
}

function getStageById(id) {
    return batchStages.value.find((s) => s.id === id) || null;
}

// ── Drag and Drop ──────────────────────────────────

const dragState = ref({
    draggedId: null,
    targetId: null,
    dropZone: null, // 'before' | 'after' | 'child'
});

function onDragStart(stageId) {
    dragState.value.draggedId = stageId;
}

function onDragOver(event, stageId, depth) {
    event.preventDefault();
    if (stageId === dragState.value.draggedId) return;

    const rect = event.currentTarget.getBoundingClientRect();
    const y = event.clientY - rect.top;
    const height = rect.height;
    const x = event.clientX - rect.left;
    const indentThreshold = (depth + 1) * 24 + 60;

    let zone;
    if (y < height * 0.3) {
        zone = "before";
    } else if (x > indentThreshold && y > height * 0.5) {
        zone = "child";
    } else {
        zone = "after";
    }

    dragState.value.targetId = stageId;
    dragState.value.dropZone = zone;
}

function onDragLeave(event) {
    // Only clear if leaving the actual element (not entering a child)
    if (!event.currentTarget.contains(event.relatedTarget)) {
        dragState.value.targetId = null;
        dragState.value.dropZone = null;
    }
}

function onDragEnd() {
    dragState.value = { draggedId: null, targetId: null, dropZone: null };
}

function isDescendant(stages, parentId, childId) {
    const children = stages.filter((s) => s.parent_id === parentId);
    for (const c of children) {
        if (c.id === childId) return true;
        if (isDescendant(stages, c.id, childId)) return true;
    }
    return false;
}

async function onDrop(event) {
    event.preventDefault();
    const { draggedId, targetId, dropZone } = dragState.value;
    if (!draggedId || !targetId || draggedId === targetId) {
        onDragEnd();
        return;
    }

    // Prevent dropping a parent onto its own descendant
    if (dropZone === "child" && isDescendant(batchStages.value, draggedId, targetId)) {
        onDragEnd();
        return;
    }

    const target = getStageById(targetId);
    if (!target) { onDragEnd(); return; }

    let newParentId;
    let siblings;

    if (dropZone === "child") {
        newParentId = targetId;
        siblings = batchStages.value.filter(
            (s) => s.parent_id === targetId && s.id !== draggedId,
        );
    } else {
        newParentId = target.parent_id ?? null;
        siblings = batchStages.value.filter(
            (s) =>
                (s.parent_id ?? null) === (target.parent_id ?? null) &&
                s.id !== draggedId,
        );
    }

    // Build new order
    siblings.sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0));

    const targetIdx = siblings.findIndex((s) => s.id === targetId);
    const insertAt =
        dropZone === "before"
            ? targetIdx
            : dropZone === "child"
              ? siblings.length
              : targetIdx + 1;

    const dragged = getStageById(draggedId);
    siblings.splice(insertAt < 0 ? 0 : insertAt, 0, dragged);

    // Build reorder payload for ALL stages (update moved item + affected siblings)
    const reorderPayload = [];
    siblings.forEach((s, i) => {
        reorderPayload.push({
            id: s.id,
            parent_id: newParentId,
            sort_order: i,
        });
    });

    // Also include all other stages that aren't in this sibling set
    const siblingIds = new Set(reorderPayload.map((r) => r.id));
    batchStages.value.forEach((s) => {
        if (!siblingIds.has(s.id)) {
            reorderPayload.push({
                id: s.id,
                parent_id: s.parent_id ?? null,
                sort_order: s.sort_order ?? 0,
            });
        }
    });

    onDragEnd();

    try {
        const response = await api.put(
            "/settings/batch-stages/reorder",
            reorderPayload,
        );
        batchStages.value = response.data;
    } catch (error) {
        console.error("Failed to reorder stages:", error);
    }
}

// ── Icon Picker ─────────────────────────────────────

const iconPickerStageId = ref(null);
const colorPickerStageId = ref(null);
const pickerPosition = ref({});

function openIconPicker(stageId, event) {
    closeColorPicker();
    iconPickerStageId.value = stageId;
    positionPicker(event);
}

function closeIconPicker() {
    iconPickerStageId.value = null;
}

async function selectIcon(iconClass) {
    const stageId = iconPickerStageId.value;
    if (!stageId) return;
    try {
        const response = await api.put(`/settings/batch-stages/${stageId}`, {
            icon: iconClass,
        });
        const idx = batchStages.value.findIndex((s) => s.id === stageId);
        if (idx !== -1) batchStages.value[idx] = response.data;
    } catch (error) {
        console.error("Failed to update icon:", error);
    }
    closeIconPicker();
}

// ── Color Picker ────────────────────────────────────

function openColorPicker(stageId, event) {
    closeIconPicker();
    colorPickerStageId.value = stageId;
    positionPicker(event);
}

function closeColorPicker() {
    colorPickerStageId.value = null;
}

async function selectColor(color) {
    const stageId = colorPickerStageId.value;
    if (!stageId) return;
    try {
        const response = await api.put(`/settings/batch-stages/${stageId}`, {
            color: color,
        });
        const idx = batchStages.value.findIndex((s) => s.id === stageId);
        if (idx !== -1) batchStages.value[idx] = response.data;
    } catch (error) {
        console.error("Failed to update color:", error);
    }
    closeColorPicker();
}

function positionPicker(event) {
    const btn = event.currentTarget || event.target;
    const rect = btn.getBoundingClientRect();
    const viewportW = window.innerWidth;
    const viewportH = window.innerHeight;

    let top = rect.bottom + 8;
    let left = rect.left;

    // Keep popover within viewport
    if (left + 300 > viewportW) left = viewportW - 320;
    if (left < 10) left = 10;
    if (top + 300 > viewportH) top = rect.top - 310;

    pickerPosition.value = {
        position: "fixed",
        top: `${top}px`,
        left: `${left}px`,
        zIndex: 2000,
    };
}

// ── StageTreeLevel Component (inline) ───────────────

const StageTreeLevel = defineComponent({
    name: "StageTreeLevel",
    props: {
        nodes: Array,
        depth: Number,
        editingId: Number,
        editForm: Object,
        dragState: Object,
    },
    emits: [
        "startEdit",
        "saveEdit",
        "cancelEdit",
        "openDelete",
        "openIconPicker",
        "openColorPicker",
        "dragStart",
        "dragOver",
        "dragLeave",
        "drop",
        "dragEnd",
    ],
    setup(props, { emit }) {
        return () => {
            if (!props.nodes || !props.nodes.length) return null;

            const items = props.nodes.map((node) => {
                const isEditing = props.editingId === node.id;
                const ds = props.dragState;
                const isDragTarget = ds.targetId === node.id && ds.draggedId !== node.id;
                const isDragging = ds.draggedId === node.id;

                const dropIndicatorClass =
                    isDragTarget && ds.dropZone
                        ? `drop-indicator-${ds.dropZone}`
                        : "";

                // Build children recursively
                const childrenVnode =
                    node.children && node.children.length
                        ? h(StageTreeLevel, {
                              nodes: node.children,
                              depth: props.depth + 1,
                              editingId: props.editingId,
                              editForm: props.editForm,
                              dragState: props.dragState,
                              onStartEdit: (item) => emit("startEdit", item),
                              onSaveEdit: () => emit("saveEdit"),
                              onCancelEdit: () => emit("cancelEdit"),
                              onOpenDelete: (item) => emit("openDelete", item),
                              onOpenIconPicker: (id, ev) =>
                                  emit("openIconPicker", id, ev),
                              onOpenColorPicker: (id, ev) =>
                                  emit("openColorPicker", id, ev),
                              onDragStart: (id) => emit("dragStart", id),
                              onDragOver: (ev, id, d) =>
                                  emit("dragOver", ev, id, d),
                              onDragLeave: (ev) => emit("dragLeave", ev),
                              onDrop: (ev) => emit("drop", ev),
                              onDragEnd: () => emit("dragEnd"),
                          })
                        : null;

                const nodeColor = node.color || DEFAULT_STAGE_COLOR;
                const nodeIcon = node.icon || DEFAULT_STAGE_ICON;

                // View mode content
                const viewContent = !isEditing
                    ? h("div", { class: "stage-node-content" }, [
                          // Drag handle
                          h(
                              "span",
                              { class: "drag-handle", title: "Drag to reorder" },
                              [h("i", { class: "bi bi-grip-vertical" })],
                          ),
                          // Color swatch
                          h("button", {
                              class: "color-swatch",
                              style: { background: nodeColor },
                              title: "Change color",
                              onClick: (ev) => {
                                  ev.stopPropagation();
                                  emit("openColorPicker", node.id, ev);
                              },
                          }),
                          // Icon button
                          h(
                              "button",
                              {
                                  class: "icon-btn",
                                  title: "Change icon",
                                  onClick: (ev) => {
                                      ev.stopPropagation();
                                      emit("openIconPicker", node.id, ev);
                                  },
                              },
                              [h("i", { class: `bi ${nodeIcon}` })],
                          ),
                          // Name
                          h("span", { class: "stage-name" }, node.name),
                          // Salable badge
                          node.is_salable
                              ? h("span", { class: "salable-badge" }, "Salable")
                              : null,
                          // Waste badge
                          node.is_waste
                              ? h("span", { class: "salable-badge waste-badge" }, "Waste")
                              : null,
                          // Spacer
                          h("span", { style: "flex:1" }),
                          // Actions
                          h("div", { class: "item-actions" }, [
                              h(
                                  "button",
                                  {
                                      class: "btn-action btn-edit",
                                      title: "Edit",
                                      onClick: (ev) => {
                                          ev.stopPropagation();
                                          emit("startEdit", node);
                                      },
                                  },
                                  [h("i", { class: "bi bi-pencil" })],
                              ),
                              h(
                                  "button",
                                  {
                                      class: "btn-action btn-delete",
                                      title: "Delete",
                                      onClick: (ev) => {
                                          ev.stopPropagation();
                                          emit("openDelete", node);
                                      },
                                  },
                                  [h("i", { class: "bi bi-trash3" })],
                              ),
                          ]),
                      ])
                    : null;

                // Edit mode content
                const editContent = isEditing
                    ? h("div", { class: "stage-node-content stage-edit-mode" }, [
                          h("input", {
                              class: "form-control form-control-sm",
                              value: props.editForm.name,
                              placeholder: "Name",
                              onInput: (ev) => {
                                  props.editForm.name = ev.target.value;
                              },
                              onKeydown: (ev) => {
                                  if (ev.key === "Enter") emit("saveEdit");
                                  if (ev.key === "Escape") emit("cancelEdit");
                              },
                          }),
                          h("label", { class: "salable-toggle" }, [
                              h("input", {
                                  type: "checkbox",
                                  checked: props.editForm.is_salable,
                                  onChange: (ev) => {
                                      props.editForm.is_salable =
                                          ev.target.checked;
                                  },
                              }),
                              h("span", { class: "salable-label" }, "Salable"),
                          ]),
                          h("label", { class: "salable-toggle" }, [
                              h("input", {
                                  type: "checkbox",
                                  checked: props.editForm.is_waste,
                                  onChange: (ev) => {
                                      props.editForm.is_waste =
                                          ev.target.checked;
                                  },
                              }),
                              h("span", { class: "salable-label" }, "Waste type"),
                          ]),
                          h("span", { style: "flex:1" }),
                          h("div", { class: "item-actions" }, [
                              h(
                                  "button",
                                  {
                                      class: "btn-action btn-save",
                                      title: "Save",
                                      disabled: !(
                                          props.editForm.name &&
                                          props.editForm.name.trim()
                                      ),
                                      onClick: () => emit("saveEdit"),
                                  },
                                  [h("i", { class: "bi bi-check-lg" })],
                              ),
                              h(
                                  "button",
                                  {
                                      class: "btn-action btn-cancel",
                                      title: "Cancel",
                                      onClick: () => emit("cancelEdit"),
                                  },
                                  [h("i", { class: "bi bi-x-lg" })],
                              ),
                          ]),
                      ])
                    : null;

                return h("div", { key: node.id, class: "stage-tree-branch" }, [
                    h(
                        "div",
                        {
                            class: [
                                "stage-node",
                                dropIndicatorClass,
                                isDragging ? "is-dragging" : "",
                            ]
                                .filter(Boolean)
                                .join(" "),
                            style: {
                                paddingLeft: `${props.depth * 24 + 12}px`,
                            },
                            draggable: !isEditing,
                            onDragstart: (ev) => {
                                ev.dataTransfer.effectAllowed = "move";
                                emit("dragStart", node.id);
                            },
                            onDragover: (ev) =>
                                emit("dragOver", ev, node.id, props.depth),
                            onDragleave: (ev) => emit("dragLeave", ev),
                            onDrop: (ev) => emit("drop", ev),
                            onDragend: () => emit("dragEnd"),
                        },
                        [viewContent, editContent],
                    ),
                    childrenVnode,
                ]);
            });

            return h("div", { class: "stage-tree-level" }, items);
        };
    },
});

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

    .picker-popover {
        min-width: 200px;
        max-width: calc(100vw - 32px);
    }

    .icon-grid {
        grid-template-columns: repeat(5, 1fr);
    }

    .color-grid {
        grid-template-columns: repeat(6, 1fr);
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

.efficiency-badge {
    background: rgba(91, 155, 213, 0.1);
    color: #5B9BD5;
}

.waste-badge {
    background: rgba(181, 105, 77, 0.12);
    color: var(--terracotta);
}

/* ── Picker Overlay & Popover ──────────────── */
.picker-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 1999;
}

.picker-popover {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    box-shadow: var(--shadow-lg);
    padding: 12px;
    min-width: 240px;
    max-width: 320px;
}

.picker-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 10px;
}

.picker-title {
    font-weight: 600;
    font-size: 0.82rem;
    color: var(--text-primary);
}

.picker-close {
    background: none;
    border: none;
    cursor: pointer;
    color: var(--text-secondary);
    font-size: 0.85rem;
    padding: 2px 4px;
    border-radius: 4px;
}

.picker-close:hover {
    background: var(--parchment-deep);
    color: var(--text-primary);
}

/* Icon Grid */
.icon-grid {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 4px;
}

.icon-option {
    width: 38px;
    height: 38px;
    border: 1.5px solid var(--border-light);
    border-radius: 8px;
    background: transparent;
    color: var(--text-secondary);
    font-size: 1.1rem;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    transition: all 0.15s;
    padding: 0;
}

.icon-option:hover {
    border-color: var(--sage);
    color: var(--moss);
    background: rgba(74, 103, 65, 0.06);
}

.icon-option.selected {
    border-color: var(--moss);
    color: var(--moss);
    background: rgba(74, 103, 65, 0.12);
    box-shadow: 0 0 0 2px var(--moss-faded);
}

/* Color Grid */
.color-grid {
    display: grid;
    grid-template-columns: repeat(8, 1fr);
    gap: 6px;
}

.color-option {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    border: 2px solid rgba(0, 0, 0, 0.08);
    cursor: pointer;
    position: relative;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    transition: transform 0.15s, box-shadow 0.15s;
    padding: 0;
    color: rgba(0, 0, 0, 0.5);
    font-size: 0.75rem;
}

.color-option:hover {
    transform: scale(1.2);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.color-option.selected {
    border-color: rgba(0, 0, 0, 0.3);
    box-shadow: 0 0 0 3px var(--bg-card), 0 0 0 5px var(--moss);
}

/* ── Stage Tree ────────────────────────────── */
.stage-tree {
    position: relative;
}
</style>

<!-- Unscoped styles for StageTreeLevel (inline defineComponent with h() render functions).
     Vue scoped CSS doesn't reach elements rendered by child components via h(). -->
<style>
.stage-tree .stage-tree-level {
    /* no extra styling needed; just a container */
}

.stage-tree .stage-node {
    display: flex;
    align-items: center;
    padding-right: 12px;
    padding-top: 2px;
    padding-bottom: 2px;
    border-bottom: 1px solid var(--border-light);
    transition: background 0.15s ease;
    position: relative;
    cursor: default;
}

.stage-tree .stage-node:hover {
    background: rgba(138, 154, 123, 0.04);
}

.stage-tree .stage-node.is-dragging {
    opacity: 0.4;
}

.stage-tree .stage-node-content {
    display: flex;
    align-items: center;
    gap: 10px;
    flex: 1;
    min-width: 0;
    padding: 8px 0;
}

.stage-tree .stage-edit-mode {
    gap: 8px;
}

.stage-tree .stage-edit-mode .form-control-sm {
    font-size: 0.85rem;
    padding: 6px 10px;
    border-radius: 7px;
    max-width: 220px;
}

/* Drag handle */
.stage-tree .drag-handle {
    cursor: grab;
    color: var(--text-secondary);
    opacity: 0.4;
    font-size: 1.1rem;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    transition: opacity 0.15s;
}

.stage-tree .drag-handle:hover {
    opacity: 0.8;
}

.stage-tree .stage-node[draggable="true"] .drag-handle {
    cursor: grab;
}

/* Color swatch button */
.stage-tree .color-swatch {
    width: 22px;
    height: 22px;
    border-radius: 50%;
    border: 2px solid rgba(0, 0, 0, 0.1);
    cursor: pointer;
    flex-shrink: 0;
    transition: transform 0.15s, box-shadow 0.15s;
    padding: 0;
}

.stage-tree .color-swatch:hover {
    transform: scale(1.15);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

/* Icon button */
.stage-tree .icon-btn {
    background: none;
    border: 1.5px solid var(--border);
    border-radius: 7px;
    width: 30px;
    height: 30px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    color: var(--text-secondary);
    font-size: 1rem;
    flex-shrink: 0;
    transition: all 0.15s;
    padding: 0;
}

.stage-tree .icon-btn:hover {
    border-color: var(--sage);
    color: var(--moss);
    background: rgba(74, 103, 65, 0.06);
}

/* Stage name in tree */
.stage-tree .stage-name {
    font-weight: 600;
    font-size: 0.9rem;
    color: var(--text-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* ── Drop Zone Indicators ──────────────────── */
.stage-tree .drop-indicator-before::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: var(--moss);
    border-radius: 2px;
    z-index: 10;
}

.stage-tree .drop-indicator-after::after {
    content: "";
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: var(--moss);
    border-radius: 2px;
    z-index: 10;
}

.stage-tree .drop-indicator-child {
    background: rgba(74, 103, 65, 0.08) !important;
    outline: 2px dashed var(--moss);
    outline-offset: -2px;
    border-radius: 6px;
}


/* ── Action Buttons (inside h() child component) ── */
.stage-tree .item-actions {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-shrink: 0;
}

.stage-tree .btn-action {
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
    transition: all 0.15s;
}

.stage-tree .btn-edit:hover {
    border-color: var(--harvest);
    color: #8a6f2a;
    background: rgba(196, 163, 90, 0.08);
}

.stage-tree .btn-delete:hover {
    border-color: var(--sienna);
    color: var(--sienna);
    background: rgba(181, 105, 77, 0.06);
}

.stage-tree .btn-save {
    border-color: var(--moss);
    color: var(--moss);
}

.stage-tree .btn-save:hover:not(:disabled) {
    background: rgba(74, 103, 65, 0.1);
}

.stage-tree .btn-save:disabled {
    opacity: 0.3;
    cursor: not-allowed;
}

.stage-tree .btn-cancel {
    border-color: var(--border);
    color: var(--text-secondary);
}

.stage-tree .btn-cancel:hover {
    border-color: var(--sienna);
    color: var(--sienna);
    background: rgba(181, 105, 77, 0.06);
}

/* ── Salable Toggle & Badge (inside h() child component) ── */
.stage-tree .salable-toggle {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    cursor: pointer;
    flex-shrink: 0;
    white-space: nowrap;
}

.stage-tree .salable-toggle input[type="checkbox"] {
    accent-color: var(--moss);
    width: 16px;
    height: 16px;
    cursor: pointer;
}

.stage-tree .salable-label {
    font-size: 0.82rem;
    font-weight: 500;
    color: var(--text-secondary);
}

.stage-tree .salable-badge {
    font-size: 0.7rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 6px;
    background: rgba(74, 103, 65, 0.1);
    color: var(--moss);
    flex-shrink: 0;
}

/* ── Responsive Tree ───────────────────────── */
@media (max-width: 767.98px) {
    .stage-tree .stage-node {
        padding-right: 8px;
    }

    .stage-tree .stage-node-content {
        gap: 6px;
    }

    .stage-tree .stage-name {
        font-size: 0.82rem;
    }

    .stage-tree .icon-btn {
        width: 26px;
        height: 26px;
        font-size: 0.85rem;
    }

    .stage-tree .color-swatch {
        width: 18px;
        height: 18px;
    }

}
</style>

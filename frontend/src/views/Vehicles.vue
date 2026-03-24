<template>
    <div class="vehicles-page">
        <div class="page-header animate-fade-in-up">
            <div>
                <h2 class="page-title">Vehicles</h2>
                <p class="page-subtitle">Manage farm vehicles and equipment</p>
            </div>
            <button v-if="isAdmin" class="btn-primary" @click="openAddModal">
                <i class="bi bi-plus-lg"></i>
                <span>Add Vehicle</span>
            </button>
        </div>

        <div class="filter-bar animate-fade-in-up animate-delay-1">
            <div class="search-wrap">
                <i class="bi bi-search search-icon"></i>
                <input
                    v-model="searchQuery"
                    type="text"
                    class="form-control search-input"
                    placeholder="Search by number or type..."
                    @input="fetchVehicles"
                />
            </div>
            <label class="active-toggle">
                <input v-model="activeOnly" type="checkbox" @change="fetchVehicles" />
                <span>Active only</span>
            </label>
        </div>

        <div class="content-panel animate-fade-in-up animate-delay-2">
            <div v-if="loading" class="empty-state">
                <i class="bi bi-hourglass-split"></i>
                <p>Loading vehicles...</p>
            </div>
            <div v-else-if="vehicles.length === 0" class="empty-state">
                <i class="bi bi-truck"></i>
                <p>No vehicles found</p>
            </div>
            <TransitionGroup name="list" tag="div" class="items-list">
                <div v-for="v in vehicles" :key="v.id" class="vehicle-row">
                    <div class="vehicle-info">
                        <div class="vehicle-number">{{ v.number }}</div>
                        <div class="vehicle-type">{{ v.vehicle_type || '—' }}<span v-if="v.fuel_consumable_name" class="fuel-name"> · ⛽ {{ v.fuel_consumable_name }}</span></div>
                    </div>
                    <div class="vehicle-meta">
                        <span class="status-badge" :class="v.is_active ? 'badge-active' : 'badge-inactive'">
                            {{ v.is_active ? 'Active' : 'Inactive' }}
                        </span>
                        <template v-if="isAdmin">
                            <button class="btn-action btn-edit" title="Edit" @click="openEdit(v)">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button
                                class="btn-action"
                                :class="v.is_active ? 'btn-deactivate' : 'btn-activate'"
                                :title="v.is_active ? 'Deactivate' : 'Activate'"
                                @click="toggleActive(v)"
                            >
                                <i class="bi" :class="v.is_active ? 'bi-pause-circle' : 'bi-play-circle'"></i>
                            </button>
                        </template>
                    </div>
                </div>
            </TransitionGroup>
        </div>

        <!-- Add/Edit Modal -->
        <div class="modal fade" id="vehicleModal" tabindex="-1" ref="vehicleModalRef">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content agri-modal">
                    <div class="agri-modal-header">
                        <h5 class="modal-title">{{ editingVehicle ? 'Edit Vehicle' : 'Add Vehicle' }}</h5>
                        <button type="button" class="btn-close-modal" data-bs-dismiss="modal">
                            <i class="bi bi-x-lg"></i>
                        </button>
                    </div>
                    <div class="agri-modal-body">
                        <div class="form-group">
                            <label class="form-label">Vehicle Number *</label>
                            <input v-model="form.number" type="text" class="form-control" placeholder="e.g. KA-01-AB-1234" />
                        </div>
                        <div class="form-group">
                            <label class="form-label">Vehicle Type</label>
                            <input v-model="form.vehicle_type" type="text" class="form-control" placeholder="e.g. Tractor, Truck, Van" />
                        </div>
                        <div class="form-group">
                            <label class="form-label">Fuel Consumable *</label>
                            <select v-model="form.fuel_consumable_id" class="form-control form-select" required>
                                <option :value="null" disabled>Select fuel consumable...</option>
                                <option v-for="c in allConsumables" :key="c.id" :value="c.id">{{ c.name }} ({{ c.unit }})</option>
                            </select>
                        </div>
                        <p v-if="formError" class="form-error">{{ formError }}</p>
                    </div>
                    <div class="agri-modal-footer">
                        <button type="button" class="btn-modal-cancel" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn-modal-confirm" :disabled="!form.number.trim() || !form.fuel_consumable_id || saving" @click="saveVehicle">
                            <span v-if="saving"><i class="bi bi-hourglass-split"></i></span>
                            <span v-else>{{ editingVehicle ? 'Save Changes' : 'Add Vehicle' }}</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from "vue";
import { Modal } from "bootstrap";
import api from "../utils/api";
import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();
const isAdmin = auth.userRoles?.includes("admin");

const vehicles = ref([]);
const loading = ref(true);
const searchQuery = ref("");
const activeOnly = ref(false);
const saving = ref(false);
const formError = ref("");

const vehicleModalRef = ref(null);
let bsModal = null;
const editingVehicle = ref(null);
const form = ref({ number: "", vehicle_type: "", fuel_consumable_id: null });
const allConsumables = ref([]);

async function fetchVehicles() {
    const params = {};
    if (searchQuery.value) params.search = searchQuery.value;
    if (activeOnly.value) params.active_only = true;
    try {
        const res = await api.get("/vehicles/", { params });
        vehicles.value = res.data;
    } catch (err) {
        console.error("Failed to fetch vehicles:", err);
    } finally {
        loading.value = false;
    }
}

async function fetchConsumables() {
    if (allConsumables.value.length) return;
    try {
        const res = await api.get("/consumables/");
        allConsumables.value = res.data;
    } catch (err) {
        console.error("Failed to fetch consumables:", err);
    }
}

async function openAddModal() {
    editingVehicle.value = null;
    form.value = { number: "", vehicle_type: "", fuel_consumable_id: null };
    formError.value = "";
    await fetchConsumables();
    if (!bsModal) bsModal = new Modal(vehicleModalRef.value);
    bsModal.show();
}

async function openEdit(v) {
    editingVehicle.value = v;
    form.value = { number: v.number, vehicle_type: v.vehicle_type || "", fuel_consumable_id: v.fuel_consumable_id || null };
    formError.value = "";
    await fetchConsumables();
    if (!bsModal) bsModal = new Modal(vehicleModalRef.value);
    bsModal.show();
}

async function saveVehicle() {
    if (!form.value.number.trim()) return;
    saving.value = true;
    formError.value = "";
    const payload = {
        number: form.value.number.trim(),
        vehicle_type: form.value.vehicle_type.trim() || null,
        fuel_consumable_id: form.value.fuel_consumable_id || null,
    };
    try {
        if (editingVehicle.value) {
            const res = await api.put(`/vehicles/${editingVehicle.value.id}`, payload);
            const idx = vehicles.value.findIndex((v) => v.id === editingVehicle.value.id);
            if (idx !== -1) vehicles.value[idx] = res.data;
        } else {
            const res = await api.post("/vehicles/", payload);
            vehicles.value.unshift(res.data);
        }
        bsModal.hide();
    } catch (err) {
        formError.value = err.response?.data?.detail || "Failed to save vehicle.";
    } finally {
        saving.value = false;
    }
}

async function toggleActive(v) {
    try {
        const res = await api.put(`/vehicles/${v.id}`, { is_active: !v.is_active });
        const idx = vehicles.value.findIndex((x) => x.id === v.id);
        if (idx !== -1) vehicles.value[idx] = res.data;
    } catch (err) {
        console.error("Failed to toggle vehicle:", err);
    }
}

onMounted(fetchVehicles);
onBeforeUnmount(() => bsModal?.dispose());
</script>

<style scoped>
.vehicles-page { max-width: 100vw; }

.page-header {
    display: flex; align-items: flex-start; justify-content: space-between;
    margin-bottom: 24px; gap: 16px; flex-wrap: wrap;
}
.page-title { font-family: var(--font-display); font-size: 1.6rem; color: var(--text-primary); margin: 0 0 4px; }
.page-subtitle { font-size: 0.85rem; color: var(--text-secondary); margin: 0; }

.btn-primary {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 9px 18px; border: none; border-radius: 10px;
    background: var(--moss); color: var(--white);
    font-family: var(--font-body); font-size: 0.85rem; font-weight: 600;
    cursor: pointer; transition: all var(--transition-fast); white-space: nowrap; flex-shrink: 0;
}
.btn-primary:hover { background: var(--moss-light); box-shadow: 0 4px 12px var(--moss-faded); }

.filter-bar {
    display: flex; align-items: center; gap: 12px; margin-bottom: 20px; flex-wrap: wrap;
}
.search-wrap { position: relative; flex: 1; min-width: 200px; }
.search-icon { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: var(--text-secondary); font-size: 0.9rem; pointer-events: none; }
.search-input { padding-left: 36px; font-size: 0.88rem; }

.active-toggle { display: flex; align-items: center; gap: 8px; font-size: 0.85rem; color: var(--text-secondary); cursor: pointer; white-space: nowrap; user-select: none; }
.active-toggle input { accent-color: var(--moss); width: 16px; height: 16px; cursor: pointer; }

.content-panel {
    background: var(--bg-card); border: 1px solid var(--border-light);
    border-radius: 14px; box-shadow: var(--shadow-sm); overflow: hidden;
}

.items-list { position: relative; }

.vehicle-row {
    display: flex; align-items: center; justify-content: space-between;
    padding: 14px 18px; border-bottom: 1px solid var(--border-light);
    gap: 12px; transition: background var(--transition-fast);
}
.vehicle-row:last-child { border-bottom: none; }
.vehicle-row:hover { background: rgba(138, 154, 123, 0.04); }

.vehicle-info { flex: 1; min-width: 0; }
.vehicle-number { font-weight: 600; font-size: 0.95rem; color: var(--text-primary); }
.vehicle-type { font-size: 0.8rem; color: var(--text-secondary); margin-top: 2px; }
.fuel-name { font-size: 0.78rem; color: var(--text-secondary); }

.vehicle-meta { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }

.status-badge { display: inline-flex; align-items: center; padding: 3px 10px; border-radius: 20px; font-size: 0.72rem; font-weight: 600; }
.badge-active { background: rgba(74, 103, 65, 0.1); color: var(--moss); }
.badge-inactive { background: rgba(181, 105, 77, 0.08); color: var(--sienna); }

.btn-action {
    width: 32px; height: 32px; border-radius: 8px; border: 1.5px solid var(--border);
    background: transparent; color: var(--text-secondary); font-size: 0.9rem;
    cursor: pointer; display: inline-flex; align-items: center; justify-content: center;
    transition: all var(--transition-fast);
}
.btn-edit:hover { border-color: var(--harvest); color: #8a6f2a; background: rgba(196, 163, 90, 0.08); }
.btn-deactivate:hover { border-color: var(--sienna); color: var(--sienna); background: rgba(181, 105, 77, 0.06); }
.btn-activate:hover { border-color: var(--moss); color: var(--moss); background: rgba(74, 103, 65, 0.08); }

.empty-state { text-align: center; padding: 48px 20px; color: var(--text-secondary); }
.empty-state i { font-size: 2.4rem; opacity: 0.3; margin-bottom: 10px; display: block; }
.empty-state p { font-size: 0.9rem; margin: 0; }

/* Modal */
.agri-modal { border: none; border-radius: 16px; box-shadow: var(--shadow-lg); background: var(--bg-card); overflow: hidden; }
.agri-modal-header { padding: 20px 24px 12px; border-bottom: 1px solid var(--border-light); display: flex; align-items: center; justify-content: space-between; }
.agri-modal-header .modal-title { font-family: var(--font-display); font-size: 1.1rem; color: var(--text-primary); margin: 0; }
.btn-close-modal { background: transparent; border: none; color: var(--text-secondary); font-size: 1rem; cursor: pointer; padding: 4px 8px; border-radius: 6px; transition: all var(--transition-fast); }
.btn-close-modal:hover { color: var(--text-primary); background: var(--parchment-deep); }
.agri-modal-body { padding: 20px 24px; display: flex; flex-direction: column; gap: 16px; }
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-label { font-size: 0.83rem; font-weight: 600; color: var(--text-primary); }
.form-error { font-size: 0.82rem; color: var(--sienna); margin: 0; }
.agri-modal-footer { padding: 14px 24px; border-top: 1px solid var(--border-light); display: flex; gap: 8px; justify-content: flex-end; }
.btn-modal-cancel { background: transparent; border: 1.5px solid var(--border); border-radius: 9px; padding: 8px 18px; font-size: 0.85rem; font-weight: 600; cursor: pointer; color: var(--text-secondary); font-family: var(--font-body); transition: all var(--transition-fast); }
.btn-modal-cancel:hover { background: var(--parchment-deep); color: var(--text-primary); }
.btn-modal-confirm { background: var(--moss); color: var(--white); border: none; border-radius: 9px; padding: 8px 18px; font-size: 0.85rem; font-weight: 600; cursor: pointer; font-family: var(--font-body); transition: all var(--transition-fast); }
.btn-modal-confirm:hover:not(:disabled) { background: var(--moss-light); }
.btn-modal-confirm:disabled { opacity: 0.4; cursor: not-allowed; }

.list-enter-active { transition: all 0.3s var(--ease-out); }
.list-leave-active { transition: all 0.2s var(--ease-out); }
.list-enter-from { opacity: 0; transform: translateY(-8px); }
.list-leave-to { opacity: 0; transform: translateX(20px); }

@media (max-width: 767.98px) {
    .page-title { font-size: 1.35rem; }
    .page-header { margin-bottom: 16px; }
    .filter-bar { gap: 8px; }
    .vehicle-row { padding: 12px 14px; }
    .vehicle-meta { gap: 6px; }
}
</style>

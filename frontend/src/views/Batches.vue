<template>
    <div class="batches-page">
        <div class="page-header animate-fade-in-up">
            <div>
                <h2 class="page-title">Batches</h2>
                <p class="page-subtitle">Track material through the processing pipeline</p>
            </div>
        </div>

        <!-- Filters -->
        <div class="filter-bar animate-fade-in-up animate-delay-1">
            <div class="stage-chips">
                <button
                    class="chip"
                    :class="{ active: selectedStageId === null }"
                    @click="setStage(null)"
                >All</button>
                <button
                    v-for="stage in stages"
                    :key="stage.id"
                    class="chip"
                    :class="{ active: selectedStageId === stage.id }"
                    @click="setStage(stage.id)"
                >{{ stage.name }}</button>
            </div>
            <div class="filter-right">
                <div class="search-wrap">
                    <i class="bi bi-search search-icon"></i>
                    <input
                        v-model="searchQuery"
                        type="text"
                        class="form-control search-input"
                        placeholder="Search batch code..."
                        @input="fetchBatches"
                    />
                </div>
                <label class="active-toggle">
                    <input v-model="activeOnly" type="checkbox" @change="fetchBatches" />
                    <span>Active only</span>
                </label>
            </div>
        </div>

        <!-- Batch Cards -->
        <div v-if="loading" class="content-panel animate-fade-in-up animate-delay-2">
            <div class="empty-state">
                <i class="bi bi-hourglass-split"></i>
                <p>Loading batches...</p>
            </div>
        </div>
        <div v-else-if="batches.length === 0" class="content-panel animate-fade-in-up animate-delay-2">
            <div class="empty-state">
                <i class="bi bi-layers"></i>
                <p>No batches found</p>
            </div>
        </div>
        <div v-else class="batch-grid animate-fade-in-up animate-delay-2">
            <div
                v-for="b in batches"
                :key="b.id"
                class="batch-card"
                @click="goToBatch(b.id)"
            >
                <div class="card-top">
                    <div class="card-title-row">
                        <span class="batch-code">{{ b.batch_code }}</span>
                        <span class="stage-badge" :class="stageBadgeClass(b.stage_name)">
                            {{ b.stage_name || '—' }}
                        </span>
                    </div>
                    <div class="card-plantation">
                        <i class="bi bi-geo-alt"></i>
                        <span>{{ b.plantation_name || 'No plantation' }}</span>
                    </div>
                </div>

                <div class="card-weights">
                    <div class="weight-item">
                        <span class="weight-label">Initial</span>
                        <span class="weight-value">{{ formatKg(b.initial_weight_kg) }} kg</span>
                    </div>
                    <div class="weight-divider"></div>
                    <div class="weight-item">
                        <span class="weight-label">Remaining</span>
                        <span class="weight-value" :class="b.is_depleted ? 'depleted-value' : ''">{{ formatKg(b.remaining_weight_kg) }} kg</span>
                    </div>
                </div>

                <div class="card-footer">
                    <span class="status-dot" :class="b.is_depleted ? 'depleted' : 'active'">
                        <span class="dot"></span>
                        {{ b.is_depleted ? 'Depleted' : 'Active' }}
                    </span>
                    <div v-if="isAdmin" class="card-actions" @click.stop>
                        <button class="btn-action btn-edit" title="Edit" @click.stop="openEditModal(b)">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn-action btn-delete" title="Delete" @click.stop="confirmDelete(b)">
                            <i class="bi bi-trash3"></i>
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Edit Modal -->
        <div class="modal fade" id="batchModal" tabindex="-1" ref="batchModalRef">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content agri-modal">
                    <div class="agri-modal-header">
                        <h5 class="modal-title">Edit Batch</h5>
                        <button type="button" class="btn-close-modal" data-bs-dismiss="modal">
                            <i class="bi bi-x-lg"></i>
                        </button>
                    </div>
                    <div class="agri-modal-body">
                        <div class="form-group">
                            <label class="form-label">Plantation</label>
                            <select v-model="form.plantation_id" class="form-control form-select">
                                <option :value="null">— None —</option>
                                <option v-for="p in plantations" :key="p.id" :value="p.id">{{ p.name }}</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Notes</label>
                            <textarea v-model="form.notes" class="form-control" rows="2" placeholder="Optional notes..."></textarea>
                        </div>
                        <p v-if="formError" class="form-error">{{ formError }}</p>
                    </div>
                    <div class="agri-modal-footer">
                        <button type="button" class="btn-modal-cancel" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn-modal-confirm" :disabled="saving" @click="saveBatch">
                            <span v-if="saving"><i class="bi bi-hourglass-split"></i></span>
                            <span v-else>Save Changes</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Delete Confirm Modal -->
        <div class="modal fade" id="deleteModal" tabindex="-1" ref="deleteModalRef">
            <div class="modal-dialog modal-dialog-centered modal-sm">
                <div class="modal-content agri-modal">
                    <div class="agri-modal-header">
                        <h5 class="modal-title">Delete Batch</h5>
                        <button type="button" class="btn-close-modal" data-bs-dismiss="modal">
                            <i class="bi bi-x-lg"></i>
                        </button>
                    </div>
                    <div class="agri-modal-body">
                        <p class="confirm-text">Delete batch <strong>{{ deletingBatch?.batch_code }}</strong>? This cannot be undone.</p>
                        <p v-if="deleteError" class="form-error">{{ deleteError }}</p>
                    </div>
                    <div class="agri-modal-footer">
                        <button type="button" class="btn-modal-cancel" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn-modal-danger" :disabled="deleting" @click="deleteBatch">
                            <span v-if="deleting"><i class="bi bi-hourglass-split"></i></span>
                            <span v-else>Delete</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { Modal } from 'bootstrap'
import api from '../utils/api'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const isAdmin = auth.userRoles?.includes('admin')

const batches = ref([])
const stages = ref([])
const plantations = ref([])
const loading = ref(false)
const saving = ref(false)
const deleting = ref(false)

const searchQuery = ref('')
const selectedStageId = ref(null)
const activeOnly = ref(false)

const editingBatch = ref(null)
const deletingBatch = ref(null)
const form = ref({ plantation_id: null, notes: '' })
const formError = ref('')
const deleteError = ref('')

const batchModalRef = ref(null)
const deleteModalRef = ref(null)
let bsModal = null
let bsDeleteModal = null

function stageBadgeClass(name) {
    if (!name) return 'stage-default'
    const n = name.toUpperCase()
    if (n.includes('HARVEST')) return 'stage-harvest'
    if (n.includes('CLEAN')) return 'stage-clean'
    if (n.includes('DRY')) return 'stage-dry'
    if (n.includes('BAG')) return 'stage-bag'
    if (n.includes('GRADE')) return 'stage-grade'
    if (n.includes('PACK')) return 'stage-pack'
    if (n.includes('RETAIL')) return 'stage-retail'
    return 'stage-default'
}

function formatKg(val) {
    if (val == null) return '—'
    return Number(val).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function setStage(id) {
    selectedStageId.value = id
    fetchBatches()
}

async function fetchBatches() {
    loading.value = true
    try {
        const params = {}
        if (selectedStageId.value !== null) params.stage_id = selectedStageId.value
        if (activeOnly.value) params.is_depleted = false
        if (searchQuery.value) params.search = searchQuery.value
        const res = await api.get('/batches/', { params })
        batches.value = res.data
    } catch (err) {
        console.error('Failed to fetch batches:', err)
    } finally {
        loading.value = false
    }
}

async function fetchStages() {
    try {
        const res = await api.get('/batches/stages')
        stages.value = res.data
    } catch (err) {
        console.error('Failed to fetch stages:', err)
    }
}

async function fetchPlantations() {
    try {
        const res = await api.get('/plantations/')
        plantations.value = res.data
    } catch (err) {
        console.error('Failed to fetch plantations:', err)
    }
}

function openEditModal(b) {
    editingBatch.value = b
    form.value = {
        plantation_id: b.plantation_id,
        notes: b.notes || '',
    }
    formError.value = ''
    if (!bsModal) bsModal = new Modal(batchModalRef.value)
    bsModal.show()
}

async function saveBatch() {
    saving.value = true
    formError.value = ''
    try {
        const payload = {
            notes: form.value.notes || null,
            plantation_id: form.value.plantation_id || null,
        }
        await api.put(`/batches/${editingBatch.value.id}`, payload)
        bsModal.hide()
        fetchBatches()
    } catch (err) {
        formError.value = err.response?.data?.detail || 'Failed to save batch.'
    } finally {
        saving.value = false
    }
}

function confirmDelete(b) {
    deletingBatch.value = b
    deleteError.value = ''
    if (!bsDeleteModal) bsDeleteModal = new Modal(deleteModalRef.value)
    bsDeleteModal.show()
}

async function deleteBatch() {
    deleting.value = true
    deleteError.value = ''
    try {
        await api.delete(`/batches/${deletingBatch.value.id}`)
        bsDeleteModal.hide()
        fetchBatches()
    } catch (err) {
        if (err.response?.status === 409) {
            deleteError.value = 'Cannot delete: batch is referenced by a transformation.'
        } else {
            deleteError.value = err.response?.data?.detail || 'Failed to delete batch.'
        }
    } finally {
        deleting.value = false
    }
}

function goToBatch(id) {
    router.push({ name: 'batch-detail', params: { id } })
}

onMounted(() => {
    fetchBatches()
    fetchStages()
    fetchPlantations()
})

onBeforeUnmount(() => {
    bsModal?.dispose()
    bsDeleteModal?.dispose()
})
</script>

<style scoped>
.batches-page { max-width: 100vw; }

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
    display: flex; align-items: flex-start; gap: 12px; margin-bottom: 20px; flex-wrap: wrap;
}
.stage-chips { display: flex; gap: 6px; flex-wrap: wrap; flex: 1; }
.chip {
    padding: 5px 12px; border-radius: 20px; border: 1.5px solid var(--border);
    background: transparent; color: var(--text-secondary); font-size: 0.8rem; font-weight: 500;
    cursor: pointer; transition: all var(--transition-fast); font-family: var(--font-body);
}
.chip.active { background: var(--moss); border-color: var(--moss); color: var(--white); }
.chip:hover:not(.active) { border-color: var(--sage); color: var(--text-primary); }

.filter-right { display: flex; align-items: center; gap: 12px; flex-shrink: 0; }
.search-wrap { position: relative; }
.search-icon { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: var(--text-secondary); font-size: 0.9rem; pointer-events: none; }
.search-input { padding-left: 36px; font-size: 0.88rem; min-width: 200px; }

.active-toggle { display: flex; align-items: center; gap: 8px; font-size: 0.85rem; color: var(--text-secondary); cursor: pointer; white-space: nowrap; user-select: none; }
.active-toggle input { accent-color: var(--moss); width: 16px; height: 16px; cursor: pointer; }

.content-panel {
    background: var(--bg-card); border: 1px solid var(--border-light);
    border-radius: 14px; box-shadow: var(--shadow-sm); overflow: hidden;
}

.empty-state { text-align: center; padding: 48px 20px; color: var(--text-secondary); }
.empty-state i { font-size: 2.4rem; opacity: 0.3; margin-bottom: 10px; display: block; }
.empty-state p { font-size: 0.9rem; margin: 0; }

/* Batch card grid */
.batch-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
}

.batch-card {
    background: var(--bg-card);
    border: 1px solid var(--border-light);
    border-radius: 14px;
    box-shadow: var(--shadow-sm);
    padding: 18px 20px;
    cursor: pointer;
    display: flex;
    flex-direction: column;
    gap: 14px;
    transition: box-shadow var(--transition-fast), border-color var(--transition-fast), transform var(--transition-fast);
}
.batch-card:hover {
    box-shadow: var(--shadow-md);
    border-color: var(--sage);
    transform: translateY(-2px);
}

.card-top { display: flex; flex-direction: column; gap: 8px; }

.card-title-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    flex-wrap: wrap;
}

.batch-code { font-size: 1rem; font-weight: 700; color: var(--text-primary); letter-spacing: 0.01em; }

.card-plantation {
    display: flex;
    align-items: center;
    gap: 5px;
    font-size: 0.82rem;
    color: var(--text-secondary);
}
.card-plantation i { font-size: 0.78rem; opacity: 0.7; }

.card-weights {
    display: flex;
    align-items: center;
    gap: 0;
    background: var(--parchment);
    border-radius: 9px;
    padding: 10px 14px;
}
.weight-item { display: flex; flex-direction: column; gap: 2px; flex: 1; }
.weight-item:last-child { text-align: right; align-items: flex-end; }
.weight-label { font-size: 0.72rem; font-weight: 600; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.06em; }
.weight-value { font-size: 0.88rem; font-weight: 600; color: var(--text-primary); font-variant-numeric: tabular-nums; }
.weight-value.depleted-value { color: var(--text-secondary); }
.weight-divider { width: 1px; height: 32px; background: var(--border-light); margin: 0 14px; flex-shrink: 0; }

.card-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.card-actions { display: flex; gap: 4px; }

/* Stage badges */
.stage-badge {
    display: inline-flex; align-items: center; padding: 3px 10px; border-radius: 20px;
    font-size: 0.72rem; font-weight: 600; white-space: nowrap;
}
.stage-harvest { background: rgba(74, 103, 65, 0.12); color: #3a5233; }
.stage-clean { background: rgba(59, 130, 246, 0.1); color: #1d4ed8; }
.stage-dry { background: rgba(234, 88, 12, 0.1); color: #c2410c; }
.stage-bag { background: rgba(109, 40, 217, 0.1); color: #6d28d9; }
.stage-grade { background: rgba(79, 70, 229, 0.1); color: #4338ca; }
.stage-pack { background: rgba(13, 148, 136, 0.1); color: #0f766e; }
.stage-retail { background: rgba(196, 163, 90, 0.15); color: #8a6f2a; }
.stage-default { background: rgba(107, 109, 107, 0.1); color: var(--text-secondary); }

/* Status dot */
.status-dot { display: inline-flex; align-items: center; gap: 6px; font-size: 0.8rem; font-weight: 500; }
.dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.status-dot.active .dot { background: var(--moss); }
.status-dot.active { color: var(--moss); }
.status-dot.depleted .dot { background: var(--text-secondary); }
.status-dot.depleted { color: var(--text-secondary); }

.btn-action {
    width: 32px; height: 32px; border-radius: 8px; border: 1.5px solid var(--border);
    background: transparent; color: var(--text-secondary); font-size: 0.9rem;
    cursor: pointer; display: inline-flex; align-items: center; justify-content: center;
    transition: all var(--transition-fast); margin-left: 4px;
}
.btn-edit:hover { border-color: var(--harvest); color: #8a6f2a; background: rgba(196, 163, 90, 0.08); }
.btn-delete:hover { border-color: var(--sienna); color: var(--sienna); background: var(--sienna-faded); }

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
.confirm-text { font-size: 0.9rem; color: var(--text-primary); margin: 0; }
.agri-modal-footer { padding: 14px 24px; border-top: 1px solid var(--border-light); display: flex; gap: 8px; justify-content: flex-end; }
.btn-modal-cancel { background: transparent; border: 1.5px solid var(--border); border-radius: 9px; padding: 8px 18px; font-size: 0.85rem; font-weight: 600; cursor: pointer; color: var(--text-secondary); font-family: var(--font-body); transition: all var(--transition-fast); }
.btn-modal-cancel:hover { background: var(--parchment-deep); color: var(--text-primary); }
.btn-modal-confirm { background: var(--moss); color: var(--white); border: none; border-radius: 9px; padding: 8px 18px; font-size: 0.85rem; font-weight: 600; cursor: pointer; font-family: var(--font-body); transition: all var(--transition-fast); }
.btn-modal-confirm:hover:not(:disabled) { background: var(--moss-light); }
.btn-modal-confirm:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-modal-danger { background: var(--sienna); color: var(--white); border: none; border-radius: 9px; padding: 8px 18px; font-size: 0.85rem; font-weight: 600; cursor: pointer; font-family: var(--font-body); transition: all var(--transition-fast); }
.btn-modal-danger:hover:not(:disabled) { background: var(--sienna-light); }
.btn-modal-danger:disabled { opacity: 0.4; cursor: not-allowed; }

@media (max-width: 767.98px) {
    .page-title { font-size: 1.35rem; }
    .page-header { margin-bottom: 16px; }
    .filter-bar { flex-direction: column; gap: 10px; }
    .filter-right { width: 100%; }
    .search-input { width: 100%; min-width: unset; }
    .batch-grid { grid-template-columns: 1fr; }
    .batch-card { padding: 14px 16px; }
}
</style>

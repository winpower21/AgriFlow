<template>
    <div class="transformations-page">
        <div class="page-header animate-fade-in-up">
            <div>
                <h2 class="page-title">Transformations</h2>
                <p class="page-subtitle">Track processing operations from input to output</p>
            </div>
            <div style="display:flex;gap:8px;flex-shrink:0;">
                <button v-if="isAdmin" class="btn-secondary" @click="openTypesModal">
                    <i class="bi bi-tags"></i>
                    <span>Manage Types</span>
                </button>
                <button v-if="isAdmin" class="btn-primary" @click="openCreateModal">
                    <i class="bi bi-plus-lg"></i>
                    <span>New Transformation</span>
                </button>
            </div>
        </div>

        <!-- Status Filter -->
        <div class="filter-bar animate-fade-in-up animate-delay-1">
            <div class="status-chips">
                <button class="chip" :class="{ active: statusFilter === '' }" @click="setFilter('')">All</button>
                <button class="chip" :class="{ active: statusFilter === 'in_progress' }" @click="setFilter('in_progress')">
                    <span class="chip-dot in-progress"></span> In Progress
                </button>
                <button class="chip" :class="{ active: statusFilter === 'complete' }" @click="setFilter('complete')">
                    <span class="chip-dot complete"></span> Complete
                </button>
            </div>
        </div>

        <!-- Cards -->
        <div v-if="loading" class="content-panel animate-fade-in-up animate-delay-2">
            <div class="empty-state">
                <i class="bi bi-hourglass-split"></i><p>Loading...</p>
            </div>
        </div>
        <div v-else-if="transformations.length === 0" class="content-panel animate-fade-in-up animate-delay-2">
            <div class="empty-state">
                <i class="bi bi-arrow-repeat"></i>
                <p>No transformations found</p>
            </div>
        </div>
        <div v-else class="trans-grid animate-fade-in-up animate-delay-2">
            <div
                v-for="t in transformations"
                :key="t.id"
                class="trans-card"
                @click="goTo(t.id)"
            >
                <div class="trans-card-header">
                    <div class="trans-card-id">T-{{ t.id }}</div>
                    <span class="status-badge" :class="t.is_complete ? 'badge-complete' : 'badge-in-progress'">
                        {{ t.is_complete ? 'Complete' : 'In Progress' }}
                    </span>
                </div>

                <div class="trans-card-type">{{ t.type_name || '—' }}</div>

                <div class="trans-card-batches">
                    <span v-if="t.input_batch_codes.length === 0" class="text-secondary-cell">No input batches</span>
                    <template v-else>
                        <span class="batch-tag" v-for="code in t.input_batch_codes.slice(0, 3)" :key="code">{{ code }}</span>
                        <span v-if="t.input_batch_codes.length > 3" class="more-tag">+{{ t.input_batch_codes.length - 3 }}</span>
                    </template>
                    <span v-if="t.total_input_weight" class="weight-hint">{{ formatKg(t.total_input_weight) }} kg</span>
                </div>

                <div class="trans-card-footer">
                    <div class="trans-card-dates">
                        <span class="date-item">
                            <span class="date-label">Started</span>
                            <span class="date-value">{{ formatDate(t.from_date) }}</span>
                        </span>
                        <span class="date-sep">·</span>
                        <span class="date-item">
                            <span class="date-label">Completed</span>
                            <span class="date-value">{{ t.to_date ? formatDate(t.to_date) : '—' }}</span>
                        </span>
                    </div>
                    <div v-if="isAdmin" class="trans-card-actions" @click.stop>
                        <button class="btn-action btn-delete" title="Delete" @click.stop="confirmDelete(t)">
                            <i class="bi bi-trash3"></i>
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Create Modal -->
        <div class="modal fade" id="createTransModal" tabindex="-1" ref="createModalRef">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content agri-modal">
                    <div class="agri-modal-header">
                        <h5 class="modal-title">New Transformation</h5>
                        <button type="button" class="btn-close-modal" data-bs-dismiss="modal"><i class="bi bi-x-lg"></i></button>
                    </div>
                    <div class="agri-modal-body">
                        <div class="form-group">
                            <label class="form-label">Type *</label>
                            <select v-model="form.type_id" class="form-control form-select">
                                <option :value="null" disabled>Select type...</option>
                                <option v-for="type in types" :key="type.id" :value="type.id">{{ type.name }}</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Start Date *</label>
                            <input v-model="form.from_date" type="datetime-local" class="form-control" />
                        </div>
                        <div class="form-group">
                            <label class="form-label">Notes</label>
                            <textarea v-model="form.notes" class="form-control" rows="2" placeholder="Optional notes..."></textarea>
                        </div>
                        <p v-if="formError" class="form-error">{{ formError }}</p>
                    </div>
                    <div class="agri-modal-footer">
                        <button type="button" class="btn-modal-cancel" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn-modal-confirm" :disabled="!form.type_id || !form.from_date || saving" @click="createTransformation">
                            <span v-if="saving"><i class="bi bi-hourglass-split"></i></span>
                            <span v-else>Create &amp; Open</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Manage Types Modal -->
        <div class="modal fade" id="typesModal" tabindex="-1" ref="typesModalRef">
            <div class="modal-dialog modal-dialog-centered modal-lg">
                <div class="modal-content agri-modal">
                    <div class="agri-modal-header">
                        <h5 class="modal-title">Manage Transformation Types</h5>
                        <button type="button" class="btn-close-modal" data-bs-dismiss="modal"><i class="bi bi-x-lg"></i></button>
                    </div>
                    <div class="agri-modal-body">
                        <!-- Existing types list -->
                        <div v-if="types.length" class="types-list">
                            <div v-for="t in types" :key="t.id" class="type-row">
                                <div v-if="editingType?.id === t.id" class="type-edit-form">
                                    <div class="form-row">
                                        <div class="form-group">
                                            <label class="form-label">Name *</label>
                                            <input v-model="typeForm.name" type="text" class="form-control" />
                                        </div>
                                        <div class="form-group" style="display:flex;align-items:flex-end;gap:8px;">
                                            <label class="active-toggle" style="padding-bottom:6px;">
                                                <input v-model="typeForm.is_root" type="checkbox" />
                                                <span>Root (Harvest)</span>
                                            </label>
                                        </div>
                                    </div>
                                    <div class="form-group">
                                        <label class="form-label">Description</label>
                                        <input v-model="typeForm.description" type="text" class="form-control" placeholder="Optional description..." />
                                    </div>
                                    <div style="display:flex;gap:8px;margin-top:4px;">
                                        <button class="btn-modal-confirm" style="font-size:0.8rem;padding:6px 14px;" :disabled="!typeForm.name.trim() || typeSaving" @click="saveType(t.id)">
                                            <span v-if="typeSaving"><i class="bi bi-hourglass-split"></i></span>
                                            <span v-else>Save</span>
                                        </button>
                                        <button class="btn-modal-cancel" style="font-size:0.8rem;padding:6px 14px;" @click="editingType = null">Cancel</button>
                                    </div>
                                </div>
                                <template v-else>
                                    <div class="type-info">
                                        <span class="type-name">{{ t.name }}</span>
                                        <span v-if="t.is_root" class="stage-badge-sm stage-harvest">Root</span>
                                        <span v-if="t.description" class="type-desc">{{ t.description }}</span>
                                    </div>
                                    <div class="type-actions">
                                        <button class="btn-action btn-edit" title="Edit" @click="startEditType(t)"><i class="bi bi-pencil"></i></button>
                                        <button class="btn-action btn-delete" title="Delete" @click="deleteType(t.id)"><i class="bi bi-trash3"></i></button>
                                    </div>
                                </template>
                            </div>
                        </div>
                        <div v-else class="empty-state"><p>No types defined yet</p></div>

                        <hr style="border-color:var(--border-light);margin:16px 0;" />

                        <!-- Create new type form -->
                        <div>
                            <p class="form-label" style="font-size:0.9rem;margin-bottom:12px;">Add New Type</p>
                            <div class="form-row">
                                <div class="form-group">
                                    <label class="form-label">Name *</label>
                                    <input v-model="newTypeForm.name" type="text" class="form-control" placeholder="e.g. Grading" />
                                </div>
                                <div class="form-group" style="display:flex;align-items:flex-end;gap:8px;">
                                    <label class="active-toggle" style="padding-bottom:6px;">
                                        <input v-model="newTypeForm.is_root" type="checkbox" />
                                        <span>Root (Harvest)</span>
                                    </label>
                                </div>
                            </div>
                            <div class="form-group">
                                <label class="form-label">Description</label>
                                <input v-model="newTypeForm.description" type="text" class="form-control" placeholder="Optional description..." />
                            </div>
                            <p v-if="typeError" class="form-error">{{ typeError }}</p>
                        </div>
                    </div>
                    <div class="agri-modal-footer">
                        <button type="button" class="btn-modal-cancel" data-bs-dismiss="modal">Close</button>
                        <button type="button" class="btn-modal-confirm" :disabled="!newTypeForm.name.trim() || typeSaving" @click="createType">
                            <span v-if="typeSaving"><i class="bi bi-hourglass-split"></i></span>
                            <span v-else>Add Type</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Delete Modal -->
        <div class="modal fade" id="deleteTransModal" tabindex="-1" ref="deleteModalRef">
            <div class="modal-dialog modal-dialog-centered modal-sm">
                <div class="modal-content agri-modal">
                    <div class="agri-modal-header">
                        <h5 class="modal-title">Delete Transformation</h5>
                        <button type="button" class="btn-close-modal" data-bs-dismiss="modal"><i class="bi bi-x-lg"></i></button>
                    </div>
                    <div class="agri-modal-body">
                        <p class="confirm-text">Delete transformation <strong>T-{{ deletingItem?.id }}</strong>? This cannot be undone.</p>
                        <p v-if="deleteError" class="form-error">{{ deleteError }}</p>
                    </div>
                    <div class="agri-modal-footer">
                        <button type="button" class="btn-modal-cancel" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn-modal-danger" :disabled="deleting" @click="deleteTransformation">
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
import { useRouter, useRoute } from 'vue-router'
import { Modal } from 'bootstrap'
import api from '../utils/api'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const isAdmin = auth.userRoles?.includes('admin')

const transformations = ref([])
const types = ref([])
const loading = ref(false)
const saving = ref(false)
const deleting = ref(false)
const statusFilter = ref('')

const form = ref({ type_id: null, from_date: todayLocal(), notes: '' })
const formError = ref('')
const deletingItem = ref(null)
const deleteError = ref('')

const createModalRef = ref(null)
const deleteModalRef = ref(null)
const typesModalRef = ref(null)
let bsCreateModal = null
let bsDeleteModal = null
let bsTypesModal = null

// Type management
const editingType = ref(null)
const typeForm = ref({ name: '', description: '', is_root: false })
const newTypeForm = ref({ name: '', description: '', is_root: false })
const typeSaving = ref(false)
const typeError = ref('')

function todayLocal() {
    const now = new Date()
    now.setSeconds(0, 0)
    return now.toISOString().slice(0, 16)
}

function formatDate(val) {
    if (!val) return '—'
    return new Date(val).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
}

function formatKg(val) {
    if (val == null) return ''
    return Number(val).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function setFilter(val) {
    statusFilter.value = val
    fetchTransformations()
}

async function fetchTransformations() {
    loading.value = true
    try {
        const params = {}
        if (statusFilter.value) params.status = statusFilter.value
        const res = await api.get('/transformations/', { params })
        transformations.value = res.data
    } catch (err) {
        console.error(err)
    } finally {
        loading.value = false
    }
}

async function fetchTypes() {
    try {
        const res = await api.get('/transformation-types/')
        types.value = res.data
    } catch (err) {
        console.error(err)
    }
}

function openCreateModal() {
    form.value = { type_id: null, from_date: todayLocal(), notes: '' }
    formError.value = ''
    if (!bsCreateModal) bsCreateModal = new Modal(createModalRef.value)
    bsCreateModal.show()
}

async function createTransformation() {
    saving.value = true
    formError.value = ''
    try {
        const payload = {
            type_id: form.value.type_id,
            from_date: new Date(form.value.from_date).toISOString(),
            notes: form.value.notes || null,
        }
        const res = await api.post('/transformations/', payload)
        bsCreateModal.hide()
        router.push({ name: 'transformation-detail', params: { id: res.data.id } })
    } catch (err) {
        formError.value = err.response?.data?.detail || 'Failed to create transformation.'
    } finally {
        saving.value = false
    }
}

function confirmDelete(t) {
    deletingItem.value = t
    deleteError.value = ''
    if (!bsDeleteModal) bsDeleteModal = new Modal(deleteModalRef.value)
    bsDeleteModal.show()
}

async function deleteTransformation() {
    deleting.value = true
    deleteError.value = ''
    try {
        await api.delete(`/transformations/${deletingItem.value.id}`)
        bsDeleteModal.hide()
        fetchTransformations()
    } catch (err) {
        if (err.response?.status === 409) {
            deleteError.value = 'Cannot delete: transformation has output batches.'
        } else {
            deleteError.value = err.response?.data?.detail || 'Failed to delete.'
        }
    } finally {
        deleting.value = false
    }
}

function goTo(id) {
    router.push({ name: 'transformation-detail', params: { id } })
}

// ── Type Management ────────────────────────────────────────────────────────────
function openTypesModal() {
    editingType.value = null
    newTypeForm.value = { name: '', description: '', is_root: false }
    typeError.value = ''
    if (!bsTypesModal) bsTypesModal = new Modal(typesModalRef.value)
    bsTypesModal.show()
}

function startEditType(t) {
    editingType.value = t
    typeForm.value = { name: t.name, description: t.description || '', is_root: t.is_root || false }
}

async function createType() {
    if (!newTypeForm.value.name.trim()) return
    typeSaving.value = true
    typeError.value = ''
    try {
        const res = await api.post('/transformation-types/', {
            name: newTypeForm.value.name.trim(),
            description: newTypeForm.value.description || null,
            is_root: newTypeForm.value.is_root,
        })
        types.value.push(res.data)
        newTypeForm.value = { name: '', description: '', is_root: false }
    } catch (err) {
        typeError.value = err.response?.data?.detail || 'Failed to create type.'
    } finally {
        typeSaving.value = false
    }
}

async function saveType(typeId) {
    if (!typeForm.value.name.trim()) return
    typeSaving.value = true
    typeError.value = ''
    try {
        const res = await api.put(`/transformation-types/${typeId}`, {
            name: typeForm.value.name.trim(),
            description: typeForm.value.description || null,
            is_root: typeForm.value.is_root,
        })
        const idx = types.value.findIndex(t => t.id === typeId)
        if (idx !== -1) types.value[idx] = res.data
        editingType.value = null
    } catch (err) {
        typeError.value = err.response?.data?.detail || 'Failed to save type.'
    } finally {
        typeSaving.value = false
    }
}

async function deleteType(typeId) {
    if (!confirm('Delete this transformation type? This cannot be undone.')) return
    try {
        await api.delete(`/transformation-types/${typeId}`)
        types.value = types.value.filter(t => t.id !== typeId)
        if (editingType.value?.id === typeId) editingType.value = null
    } catch (err) {
        alert(err.response?.data?.detail || 'Failed to delete type.')
    }
}

onMounted(() => {
    fetchTransformations()
    fetchTypes()
    // Auto-open create modal if ?new=true
    if (route.query.new === 'true') {
        setTimeout(() => openCreateModal(), 300)
    }
})

onBeforeUnmount(() => {
    bsCreateModal?.dispose()
    bsDeleteModal?.dispose()
    bsTypesModal?.dispose()
})
</script>

<style scoped>
.transformations-page { max-width: 100vw; }

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

.filter-bar { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
.status-chips { display: flex; gap: 6px; }
.chip {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 5px 14px; border-radius: 20px; border: 1.5px solid var(--border);
    background: transparent; color: var(--text-secondary); font-size: 0.82rem; font-weight: 500;
    cursor: pointer; transition: all var(--transition-fast); font-family: var(--font-body);
}
.chip.active { background: var(--moss); border-color: var(--moss); color: var(--white); }
.chip:hover:not(.active) { border-color: var(--sage); color: var(--text-primary); }
.chip-dot { width: 7px; height: 7px; border-radius: 50%; }
.chip-dot.in-progress { background: #b45309; }
.chip-dot.complete { background: var(--moss); }

.content-panel { background: var(--bg-card); border: 1px solid var(--border-light); border-radius: 14px; box-shadow: var(--shadow-sm); overflow: hidden; }
.empty-state { text-align: center; padding: 48px 20px; color: var(--text-secondary); }
.empty-state i { font-size: 2.4rem; opacity: 0.3; margin-bottom: 10px; display: block; }
.empty-state p { font-size: 0.9rem; margin: 0; }

/* Card grid */
.trans-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
}

.trans-card {
    background: var(--bg-card);
    border: 1px solid var(--border-light);
    border-radius: 14px;
    box-shadow: var(--shadow-sm);
    padding: 18px 20px;
    cursor: pointer;
    transition: box-shadow var(--transition-fast), border-color var(--transition-fast), transform var(--transition-fast);
    display: flex;
    flex-direction: column;
    gap: 10px;
}
.trans-card:hover {
    border-color: var(--sage);
    box-shadow: var(--shadow-md);
    transform: translateY(-1px);
}

.trans-card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
}
.trans-card-id {
    font-weight: 700;
    font-size: 0.92rem;
    color: var(--text-primary);
    font-variant-numeric: tabular-nums;
}

.trans-card-type {
    font-size: 0.88rem;
    font-weight: 600;
    color: var(--moss);
}

.trans-card-batches {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
    min-height: 22px;
}

.trans-card-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    margin-top: 4px;
    padding-top: 10px;
    border-top: 1px solid var(--border-light);
}
.trans-card-dates {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
}
.date-item { display: flex; flex-direction: column; gap: 1px; }
.date-label { font-size: 0.72rem; font-weight: 600; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em; }
.date-value { font-size: 0.82rem; color: var(--text-primary); }
.date-sep { color: var(--border); font-size: 1rem; line-height: 1; align-self: center; }
.trans-card-actions { flex-shrink: 0; }

.text-secondary-cell { color: var(--text-secondary); font-size: 0.82rem; }

.batch-tag {
    display: inline-block; padding: 2px 8px; border-radius: 6px;
    background: rgba(74, 103, 65, 0.08); color: var(--moss);
    font-size: 0.75rem; font-weight: 600;
}
.more-tag { font-size: 0.75rem; color: var(--text-secondary); }
.weight-hint { font-size: 0.75rem; color: var(--text-secondary); margin-left: 4px; }

.status-badge { display: inline-flex; align-items: center; padding: 3px 10px; border-radius: 20px; font-size: 0.72rem; font-weight: 600; }
.badge-in-progress { background: rgba(180, 83, 9, 0.1); color: #b45309; }
.badge-complete { background: rgba(74, 103, 65, 0.1); color: var(--moss); }

.btn-action { width: 32px; height: 32px; border-radius: 8px; border: 1.5px solid var(--border); background: transparent; color: var(--text-secondary); font-size: 0.9rem; cursor: pointer; display: inline-flex; align-items: center; justify-content: center; transition: all var(--transition-fast); }
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
.btn-modal-cancel:hover { background: var(--parchment-deep); }
.btn-modal-confirm { background: var(--moss); color: var(--white); border: none; border-radius: 9px; padding: 8px 18px; font-size: 0.85rem; font-weight: 600; cursor: pointer; font-family: var(--font-body); transition: all var(--transition-fast); }
.btn-modal-confirm:hover:not(:disabled) { background: var(--moss-light); }
.btn-modal-confirm:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-modal-danger { background: var(--sienna); color: var(--white); border: none; border-radius: 9px; padding: 8px 18px; font-size: 0.85rem; font-weight: 600; cursor: pointer; font-family: var(--font-body); transition: all var(--transition-fast); }
.btn-modal-danger:hover:not(:disabled) { background: var(--sienna-light); }
.btn-modal-danger:disabled { opacity: 0.4; cursor: not-allowed; }

.btn-secondary {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 9px 18px; border: 1.5px solid var(--border); border-radius: 10px;
    background: transparent; color: var(--text-primary);
    font-family: var(--font-body); font-size: 0.85rem; font-weight: 600;
    cursor: pointer; transition: all var(--transition-fast); white-space: nowrap;
}
.btn-secondary:hover { border-color: var(--sage); background: var(--parchment-deep); }

.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }

.types-list { display: flex; flex-direction: column; gap: 0; }
.type-row {
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 0; border-bottom: 1px solid var(--border-light); gap: 12px;
}
.type-row:last-child { border-bottom: none; }
.type-info { display: flex; align-items: center; gap: 8px; flex: 1; flex-wrap: wrap; }
.type-name { font-weight: 600; font-size: 0.88rem; color: var(--text-primary); }
.type-desc { font-size: 0.78rem; color: var(--text-secondary); }
.type-actions { display: flex; gap: 6px; flex-shrink: 0; }
.type-edit-form { flex: 1; }

.active-toggle { display: flex; align-items: center; gap: 8px; font-size: 0.85rem; color: var(--text-secondary); cursor: pointer; user-select: none; }
.active-toggle input { accent-color: var(--moss); width: 16px; height: 16px; cursor: pointer; }

.stage-badge-sm { display: inline-flex; align-items: center; padding: 2px 8px; border-radius: 20px; font-size: 0.7rem; font-weight: 600; }
.stage-harvest { background: rgba(74, 103, 65, 0.12); color: #3a5233; }

@media (max-width: 767.98px) {
    .page-title { font-size: 1.35rem; }
    .page-header { margin-bottom: 16px; }
    .trans-grid { grid-template-columns: 1fr; gap: 12px; }
    .trans-card { padding: 14px 16px; }
}
</style>

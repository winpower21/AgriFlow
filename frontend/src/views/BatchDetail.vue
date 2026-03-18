<template>
    <div class="batch-detail-page" v-if="batch">
        <!-- Header -->
        <div class="page-header animate-fade-in-up">
            <div class="header-left">
                <button class="btn-back" @click="$router.push({ name: 'batches' })">
                    <i class="bi bi-arrow-left"></i>
                </button>
                <div>
                    <div class="header-title-row">
                        <h2 class="page-title">{{ batch.batch_code }}</h2>
                        <span class="stage-badge" :class="stageBadgeClass(batch.stage_name)">
                            {{ batch.stage_name || 'Unknown Stage' }}
                        </span>
                        <span class="status-dot" :class="batch.is_depleted ? 'depleted' : 'active'">
                            <span class="dot"></span>{{ batch.is_depleted ? 'Depleted' : 'Active' }}
                        </span>
                    </div>
                    <p class="page-subtitle">
                        {{ formatKg(batch.remaining_weight_kg) }} kg remaining
                        <span v-if="batch.plantation_name"> · {{ batch.plantation_name }}</span>
                    </p>
                </div>
            </div>
            <div class="header-actions" v-if="isAdmin">
                <button class="btn-secondary" @click="openEditModal">
                    <i class="bi bi-pencil"></i> Edit
                </button>
                <button class="btn-danger-outline" @click="confirmDelete">
                    <i class="bi bi-trash3"></i> Delete
                </button>
            </div>
        </div>

        <!-- Tabs -->
        <div class="tabs animate-fade-in-up animate-delay-1">
            <button v-for="tab in tabs" :key="tab.id" class="tab-btn" :class="{ active: activeTab === tab.id }" @click="activeTab = tab.id">
                <i class="bi" :class="tab.icon"></i> {{ tab.label }}
            </button>
        </div>

        <!-- Tree Tab -->
        <div v-if="activeTab === 'tree'" class="content-panel animate-fade-in-up animate-delay-2">
            <div class="panel-header"><span>Batch Genealogy</span></div>
            <div class="panel-body">
                <div v-if="genealogyLoading" class="empty-state"><i class="bi bi-hourglass-split"></i><p>Loading tree...</p></div>
                <div v-else-if="!genealogy" class="empty-state"><i class="bi bi-diagram-3"></i><p>No genealogy data available</p></div>
                <div v-else class="tree-container">
                    <!-- Parents (ancestors) -->
                    <div v-if="genealogy.parents && genealogy.parents.length" class="tree-section">
                        <div class="tree-section-label">Parents</div>
                        <div class="tree-parents">
                            <BatchTreeNode v-for="parent in genealogy.parents" :key="parent.batch_id" :node="parent" :currentId="batch.id" direction="up" @navigate="goToBatch" />
                        </div>
                        <div class="tree-connector"><i class="bi bi-arrow-down"></i></div>
                    </div>
                    <!-- Current batch -->
                    <div class="tree-current-node">
                        <div class="tree-node-content current">
                            <span class="tree-code">{{ genealogy.batch_code }}</span>
                            <span v-if="genealogy.stage_name" class="tree-stage">{{ genealogy.stage_name }}</span>
                            <span class="tree-weight">{{ Number(genealogy.remaining_weight_kg).toFixed(2) }} kg</span>
                            <span v-if="genealogy.is_depleted" class="tree-depleted">Depleted</span>
                        </div>
                    </div>
                    <!-- Children (descendants) -->
                    <div v-if="genealogy.children && genealogy.children.length" class="tree-section">
                        <div class="tree-connector"><i class="bi bi-arrow-down"></i></div>
                        <div class="tree-section-label">Children</div>
                        <div class="tree-children-section">
                            <BatchTreeNode v-for="child in genealogy.children" :key="child.batch_id" :node="child" :currentId="batch.id" direction="down" @navigate="goToBatch" />
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Timeline Tab -->
        <div v-if="activeTab === 'timeline'" class="content-panel animate-fade-in-up animate-delay-2">
            <div class="panel-header"><span>Processing History</span></div>
            <div class="panel-body">
                <div class="timeline">
                    <div v-if="relatedTransformations.length === 0" class="empty-state small">
                        <p>No transformations linked to this batch yet</p>
                    </div>
                    <div class="timeline-item" v-for="t in relatedTransformations" :key="t.id">
                        <div class="timeline-icon" :class="t.role === 'output' ? 'harvest' : 'process'">
                            <i class="bi" :class="t.role === 'output' ? 'bi-box-arrow-in-down' : 'bi-arrow-repeat'"></i>
                        </div>
                        <div class="timeline-content">
                            <div class="timeline-title">
                                {{ t.type_name }} — T-{{ t.id }}
                                <span class="role-tag" :class="t.role">{{ t.role === 'output' ? 'Created this batch' : 'Consumed this batch' }}</span>
                                <RouterLink :to="{ name: 'transformation-detail', params: { id: t.id } }" class="link-sm">View →</RouterLink>
                            </div>
                            <div class="timeline-meta">
                                Started {{ formatDate(t.from_date) }}
                                <span v-if="t.to_date"> · Completed {{ formatDate(t.to_date) }}</span>
                                <span v-else class="in-progress-tag"> · In Progress</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Details Tab -->
        <div v-if="activeTab === 'details'" class="content-panel animate-fade-in-up animate-delay-2">
            <div class="panel-header"><span>Batch Details</span></div>
            <div class="panel-body">
                <div class="details-grid">
                    <div class="form-group full-width">
                        <label class="form-label">Plantation</label>
                        <select v-model="editForm.plantation_id" class="form-control form-select" :disabled="!isAdmin">
                            <option :value="null">— None —</option>
                            <option v-for="p in plantations" :key="p.id" :value="p.id">{{ p.name }}</option>
                        </select>
                    </div>
                    <div class="form-group full-width">
                        <label class="form-label">Notes</label>
                        <textarea v-model="editForm.notes" class="form-control" rows="3" :disabled="!isAdmin"></textarea>
                    </div>
                    <div class="meta-info">
                        <span>Batch Code: {{ batch.batch_code }}</span>
                        <span>Created: {{ formatDate(batch.created_at) }}</span>
                        <span>Updated: {{ formatDate(batch.updated_at) }}</span>
                        <span>Initial weight: {{ formatKg(batch.initial_weight_kg) }} kg</span>
                        <span>Remaining weight: {{ formatKg(batch.remaining_weight_kg) }} kg</span>
                    </div>
                </div>
                <div v-if="isAdmin" class="save-row">
                    <p v-if="saveError" class="form-error">{{ saveError }}</p>
                    <button class="btn-primary" :disabled="saving" @click="saveDetails">
                        <span v-if="saving"><i class="bi bi-hourglass-split"></i></span>
                        <span v-else>Save Changes</span>
                    </button>
                </div>
            </div>
        </div>
    </div>

    <div v-else-if="loadError" class="empty-state page-empty">
        <i class="bi bi-exclamation-triangle"></i>
        <p>{{ loadError }}</p>
        <button class="btn-primary" @click="$router.push({ name: 'batches' })">Back to Batches</button>
    </div>

    <div v-else class="empty-state page-empty">
        <i class="bi bi-hourglass-split"></i>
        <p>Loading batch...</p>
    </div>

    <!-- Edit Modal -->
    <div class="modal fade" id="editBatchModal" tabindex="-1" ref="editModalRef">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content agri-modal">
                <div class="agri-modal-header">
                    <h5 class="modal-title">Edit Batch</h5>
                    <button type="button" class="btn-close-modal" data-bs-dismiss="modal"><i class="bi bi-x-lg"></i></button>
                </div>
                <div class="agri-modal-body">
                    <div class="form-group">
                        <label class="form-label">Plantation</label>
                        <select v-model="editForm.plantation_id" class="form-control form-select">
                            <option :value="null">— None —</option>
                            <option v-for="p in plantations" :key="p.id" :value="p.id">{{ p.name }}</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Notes</label>
                        <textarea v-model="editForm.notes" class="form-control" rows="2"></textarea>
                    </div>
                    <p v-if="saveError" class="form-error">{{ saveError }}</p>
                </div>
                <div class="agri-modal-footer">
                    <button type="button" class="btn-modal-cancel" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn-modal-confirm" :disabled="saving" @click="saveModal">
                        <span v-if="saving"><i class="bi bi-hourglass-split"></i></span>
                        <span v-else>Save Changes</span>
                    </button>
                </div>
            </div>
        </div>
    </div>

    <!-- Delete Modal -->
    <div class="modal fade" id="deleteBatchModal" tabindex="-1" ref="deleteModalRef">
        <div class="modal-dialog modal-dialog-centered modal-sm">
            <div class="modal-content agri-modal">
                <div class="agri-modal-header">
                    <h5 class="modal-title">Delete Batch</h5>
                    <button type="button" class="btn-close-modal" data-bs-dismiss="modal"><i class="bi bi-x-lg"></i></button>
                </div>
                <div class="agri-modal-body">
                    <p class="confirm-text">Delete batch <strong>{{ batch?.batch_code }}</strong>? This cannot be undone.</p>
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
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Modal } from 'bootstrap'
import api from '../utils/api'
import { useAuthStore } from '@/stores/auth'

// Recursive tree node component defined inline
const BatchTreeNode = {
    name: 'BatchTreeNode',
    props: { node: Object, currentId: Number, direction: { type: String, default: 'down' } },
    emits: ['navigate'],
    template: `
        <div class="tree-node">
            <!-- Recurse upward: render the parent's own ancestors first -->
            <div v-if="direction === 'up' && node.parents && node.parents.length" class="tree-ancestors">
                <BatchTreeNode v-for="ancestor in node.parents" :key="ancestor.batch_id" :node="ancestor" :currentId="currentId" direction="up" @navigate="$emit('navigate', $event)" />
                <div class="tree-connector-inner"><i class="bi bi-arrow-down"></i></div>
            </div>
            <div class="tree-node-content" :class="{ current: node.batch_id === currentId }" @click="$emit('navigate', node.batch_id)">
                <span class="tree-code">{{ node.batch_code }}</span>
                <span v-if="node.stage_name" class="tree-stage">{{ node.stage_name }}</span>
                <span class="tree-weight">{{ Number(node.remaining_weight_kg).toFixed(2) }} kg</span>
                <span v-if="node.is_depleted" class="tree-depleted">Depleted</span>
            </div>
            <!-- Recurse downward: render children below -->
            <div v-if="direction !== 'up' && node.children && node.children.length" class="tree-children">
                <BatchTreeNode v-for="child in node.children" :key="child.batch_id" :node="child" :currentId="currentId" direction="down" @navigate="$emit('navigate', $event)" />
            </div>
        </div>
    `,
}

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const isAdmin = auth.userRoles?.includes('admin')

const batch = ref(null)
const genealogy = ref(null)
const relatedTransformations = ref([])
const loadError = ref('')
const genealogyLoading = ref(false)
const saving = ref(false)
const deleting = ref(false)
const saveError = ref('')
const deleteError = ref('')

const activeTab = ref('tree')
const tabs = [
    { id: 'tree', label: 'Genealogy Tree', icon: 'bi-diagram-3' },
    { id: 'timeline', label: 'Timeline', icon: 'bi-clock-history' },
    { id: 'details', label: 'Details', icon: 'bi-info-circle' },
]

const editForm = ref({ plantation_id: null, notes: '' })
const plantations = ref([])

const editModalRef = ref(null)
const deleteModalRef = ref(null)
let bsEditModal = null
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

function formatDate(val) {
    if (!val) return '—'
    return new Date(val).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
}

async function fetchPlantations() {
    try {
        const res = await api.get('/plantations/')
        plantations.value = res.data
    } catch (err) {
        console.error('Failed to fetch plantations:', err)
    }
}

async function fetchBatch() {
    try {
        const res = await api.get(`/batches/${route.params.id}`)
        batch.value = res.data
        editForm.value = {
            plantation_id: res.data.plantation_id,
            notes: res.data.notes || '',
        }
    } catch (err) {
        loadError.value = err.response?.status === 404 ? 'Batch not found.' : 'Failed to load batch.'
    }
}

async function fetchGenealogy() {
    genealogyLoading.value = true
    try {
        const res = await api.get(`/batches/${route.params.id}/genealogy`)
        genealogy.value = res.data
    } catch (err) {
        console.error('Genealogy error:', err)
    } finally {
        genealogyLoading.value = false
    }
}

async function fetchRelatedTransformations() {
    try {
        const res = await api.get(`/batches/${route.params.id}/transformations`)
        relatedTransformations.value = res.data
    } catch (err) {
        console.error('Failed to load transformations:', err)
    }
}

function openEditModal() {
    saveError.value = ''
    if (!bsEditModal) bsEditModal = new Modal(editModalRef.value)
    bsEditModal.show()
}

function confirmDelete() {
    deleteError.value = ''
    if (!bsDeleteModal) bsDeleteModal = new Modal(deleteModalRef.value)
    bsDeleteModal.show()
}

async function saveModal() {
    saving.value = true
    saveError.value = ''
    try {
        const payload = {
            notes: editForm.value.notes || null,
            plantation_id: editForm.value.plantation_id || null,
        }
        const res = await api.put(`/batches/${route.params.id}`, payload)
        batch.value = res.data
        bsEditModal.hide()
    } catch (err) {
        saveError.value = err.response?.data?.detail || 'Failed to save.'
    } finally {
        saving.value = false
    }
}

async function saveDetails() {
    saving.value = true
    saveError.value = ''
    try {
        const payload = {
            notes: editForm.value.notes || null,
            plantation_id: editForm.value.plantation_id || null,
        }
        const res = await api.put(`/batches/${route.params.id}`, payload)
        batch.value = res.data
    } catch (err) {
        saveError.value = err.response?.data?.detail || 'Failed to save.'
    } finally {
        saving.value = false
    }
}

async function deleteBatch() {
    deleting.value = true
    deleteError.value = ''
    try {
        await api.delete(`/batches/${route.params.id}`)
        bsDeleteModal.hide()
        router.push({ name: 'batches' })
    } catch (err) {
        if (err.response?.status === 409) {
            deleteError.value = 'Cannot delete: batch is referenced by a transformation.'
        } else {
            deleteError.value = err.response?.data?.detail || 'Failed to delete.'
        }
    } finally {
        deleting.value = false
    }
}

function goToBatch(id) {
    if (id !== batch.value?.id) {
        router.push({ name: 'batch-detail', params: { id } })
    }
}

onMounted(async () => {
    await fetchBatch()
    fetchGenealogy()
    fetchPlantations()
})

onBeforeUnmount(() => {
    bsEditModal?.dispose()
    bsDeleteModal?.dispose()
})
</script>

<style scoped>
.batch-detail-page { max-width: 100vw; }
.page-empty { padding: 80px 20px; text-align: center; color: var(--text-secondary); }
.page-empty i { font-size: 2.5rem; opacity: 0.3; display: block; margin-bottom: 12px; }
.page-empty p { margin-bottom: 16px; }

.page-header {
    display: flex; align-items: flex-start; justify-content: space-between;
    margin-bottom: 20px; gap: 16px; flex-wrap: wrap;
}
.header-left { display: flex; align-items: flex-start; gap: 12px; }
.btn-back {
    width: 36px; height: 36px; border-radius: 10px; border: 1.5px solid var(--border);
    background: transparent; color: var(--text-secondary); cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem; transition: all var(--transition-fast); flex-shrink: 0; margin-top: 4px;
}
.btn-back:hover { border-color: var(--sage); color: var(--text-primary); }
.header-title-row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.page-title { font-family: var(--font-display); font-size: 1.6rem; color: var(--text-primary); margin: 0 0 6px; }
.page-subtitle { font-size: 0.85rem; color: var(--text-secondary); margin: 0; }
.header-actions { display: flex; gap: 8px; flex-shrink: 0; }

.btn-secondary {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 8px 16px; border: 1.5px solid var(--border); border-radius: 9px;
    background: transparent; color: var(--text-primary);
    font-family: var(--font-body); font-size: 0.85rem; font-weight: 600;
    cursor: pointer; transition: all var(--transition-fast);
}
.btn-secondary:hover { border-color: var(--sage); background: var(--parchment-deep); }

.btn-danger-outline {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 8px 16px; border: 1.5px solid var(--sienna); border-radius: 9px;
    background: transparent; color: var(--sienna);
    font-family: var(--font-body); font-size: 0.85rem; font-weight: 600;
    cursor: pointer; transition: all var(--transition-fast);
}
.btn-danger-outline:hover { background: var(--sienna-faded); }

/* Stage / Status badges */
.stage-badge {
    display: inline-flex; align-items: center; padding: 3px 10px; border-radius: 20px;
    font-size: 0.72rem; font-weight: 600;
}
.stage-harvest { background: rgba(74, 103, 65, 0.12); color: #3a5233; }
.stage-clean { background: rgba(59, 130, 246, 0.1); color: #1d4ed8; }
.stage-dry { background: rgba(234, 88, 12, 0.1); color: #c2410c; }
.stage-bag { background: rgba(109, 40, 217, 0.1); color: #6d28d9; }
.stage-grade { background: rgba(79, 70, 229, 0.1); color: #4338ca; }
.stage-pack { background: rgba(13, 148, 136, 0.1); color: #0f766e; }
.stage-retail { background: rgba(196, 163, 90, 0.15); color: #8a6f2a; }
.stage-default { background: rgba(107, 109, 107, 0.1); color: var(--text-secondary); }

.status-dot { display: inline-flex; align-items: center; gap: 5px; font-size: 0.78rem; font-weight: 500; }
.dot { width: 6px; height: 6px; border-radius: 50%; }
.status-dot.active .dot { background: var(--moss); }
.status-dot.active { color: var(--moss); }
.status-dot.depleted .dot { background: var(--text-secondary); }
.status-dot.depleted { color: var(--text-secondary); }

/* Tabs */
.tabs { display: flex; gap: 4px; margin-bottom: 16px; border-bottom: 1.5px solid var(--border-light); padding-bottom: 0; }
.tab-btn {
    padding: 10px 18px; border: none; border-bottom: 2.5px solid transparent; margin-bottom: -1.5px;
    background: transparent; color: var(--text-secondary); font-family: var(--font-body);
    font-size: 0.85rem; font-weight: 500; cursor: pointer; transition: all var(--transition-fast);
    display: flex; align-items: center; gap: 6px;
}
.tab-btn:hover { color: var(--text-primary); }
.tab-btn.active { color: var(--moss); border-bottom-color: var(--moss); font-weight: 600; }

/* Content panels */
.content-panel { background: var(--bg-card); border: 1px solid var(--border-light); border-radius: 14px; box-shadow: var(--shadow-sm); overflow: hidden; }
.panel-header { padding: 14px 20px; border-bottom: 1px solid var(--border-light); font-weight: 600; font-size: 0.9rem; color: var(--text-primary); }
.panel-body { padding: 20px; }

.empty-state { text-align: center; padding: 40px 20px; color: var(--text-secondary); }
.empty-state i { font-size: 2rem; opacity: 0.3; margin-bottom: 8px; display: block; }
.empty-state p { margin: 0; font-size: 0.88rem; }
.empty-state.small { padding: 24px 20px; }

/* Tree */
.tree-container { padding: 8px 0; }
.tree-node { padding-left: 20px; }
.tree-node:first-child { padding-left: 0; }
.tree-node-content {
    display: inline-flex; align-items: center; gap: 8px; padding: 8px 14px;
    border-radius: 10px; border: 1.5px solid var(--border-light);
    background: var(--bg-card); cursor: pointer; margin-bottom: 8px;
    transition: all var(--transition-fast);
}
.tree-node-content:hover { border-color: var(--sage); background: var(--parchment); }
.tree-node-content.current { border-color: var(--moss); background: rgba(74, 103, 65, 0.06); cursor: default; }
.tree-code { font-weight: 600; font-size: 0.88rem; color: var(--text-primary); }
.tree-stage { font-size: 0.75rem; color: var(--text-secondary); }
.tree-weight { font-size: 0.78rem; color: var(--moss); font-weight: 500; }
.tree-depleted { font-size: 0.72rem; color: var(--text-secondary); background: var(--parchment-deep); padding: 1px 7px; border-radius: 20px; }
.tree-children { border-left: 2px dashed var(--border-light); margin-left: 20px; padding-left: 16px; }
.tree-section { margin-bottom: 8px; }
.tree-section-label { font-size: 0.75rem; font-weight: 600; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px; }
.tree-connector { text-align: center; color: var(--text-secondary); font-size: 1.2rem; padding: 4px 0; }
.tree-connector-inner { text-align: left; color: var(--text-secondary); font-size: 1rem; padding: 2px 0 2px 2px; }
.tree-current-node { margin: 8px 0; }
.tree-parents { display: flex; flex-wrap: wrap; gap: 8px; }
.tree-children-section { padding-left: 20px; }

/* Timeline */
.timeline { display: flex; flex-direction: column; gap: 0; }
.timeline-item { display: flex; gap: 16px; padding: 16px 0; border-bottom: 1px solid var(--border-light); }
.timeline-item:last-child { border-bottom: none; }
.timeline-icon {
    width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center;
    justify-content: center; font-size: 0.9rem; flex-shrink: 0;
}
.timeline-icon.harvest { background: rgba(74, 103, 65, 0.12); color: var(--moss); }
.timeline-icon.process { background: rgba(196, 163, 90, 0.12); color: #8a6f2a; }
.timeline-content { flex: 1; }
.timeline-title { font-weight: 600; font-size: 0.9rem; color: var(--text-primary); display: flex; align-items: center; gap: 8px; }
.timeline-meta { font-size: 0.8rem; color: var(--text-secondary); margin-top: 2px; }
.link-sm { font-size: 0.78rem; color: var(--moss); font-weight: 500; }
.in-progress-tag { color: #b45309; }
.role-tag { font-size: 0.72rem; font-weight: 600; padding: 1px 8px; border-radius: 20px; }
.role-tag.output { background: rgba(74, 103, 65, 0.1); color: var(--moss); }
.role-tag.input { background: rgba(196, 163, 90, 0.12); color: #8a6f2a; }

/* Details tab */
.details-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-group.full-width { grid-column: 1 / -1; }
.form-label { font-size: 0.83rem; font-weight: 600; color: var(--text-primary); }
.meta-info { grid-column: 1 / -1; display: flex; flex-wrap: wrap; gap: 12px; font-size: 0.8rem; color: var(--text-secondary); }
.save-row { display: flex; align-items: center; justify-content: flex-end; gap: 12px; margin-top: 16px; padding-top: 16px; border-top: 1px solid var(--border-light); }
.form-error { font-size: 0.82rem; color: var(--sienna); margin: 0; }

.btn-primary {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 9px 18px; border: none; border-radius: 10px;
    background: var(--moss); color: var(--white);
    font-family: var(--font-body); font-size: 0.85rem; font-weight: 600;
    cursor: pointer; transition: all var(--transition-fast);
}
.btn-primary:hover:not(:disabled) { background: var(--moss-light); }
.btn-primary:disabled { opacity: 0.4; cursor: not-allowed; }

/* Modal */
.agri-modal { border: none; border-radius: 16px; box-shadow: var(--shadow-lg); background: var(--bg-card); overflow: hidden; }
.agri-modal-header { padding: 20px 24px 12px; border-bottom: 1px solid var(--border-light); display: flex; align-items: center; justify-content: space-between; }
.agri-modal-header .modal-title { font-family: var(--font-display); font-size: 1.1rem; color: var(--text-primary); margin: 0; }
.btn-close-modal { background: transparent; border: none; color: var(--text-secondary); font-size: 1rem; cursor: pointer; padding: 4px 8px; border-radius: 6px; transition: all var(--transition-fast); }
.btn-close-modal:hover { color: var(--text-primary); background: var(--parchment-deep); }
.agri-modal-body { padding: 20px 24px; display: flex; flex-direction: column; gap: 16px; }
.agri-modal-footer { padding: 14px 24px; border-top: 1px solid var(--border-light); display: flex; gap: 8px; justify-content: flex-end; }
.btn-modal-cancel { background: transparent; border: 1.5px solid var(--border); border-radius: 9px; padding: 8px 18px; font-size: 0.85rem; font-weight: 600; cursor: pointer; color: var(--text-secondary); font-family: var(--font-body); transition: all var(--transition-fast); }
.btn-modal-cancel:hover { background: var(--parchment-deep); }
.btn-modal-confirm { background: var(--moss); color: var(--white); border: none; border-radius: 9px; padding: 8px 18px; font-size: 0.85rem; font-weight: 600; cursor: pointer; font-family: var(--font-body); transition: all var(--transition-fast); }
.btn-modal-confirm:hover:not(:disabled) { background: var(--moss-light); }
.btn-modal-confirm:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-modal-danger { background: var(--sienna); color: var(--white); border: none; border-radius: 9px; padding: 8px 18px; font-size: 0.85rem; font-weight: 600; cursor: pointer; font-family: var(--font-body); transition: all var(--transition-fast); }
.btn-modal-danger:hover:not(:disabled) { background: var(--sienna-light); }
.btn-modal-danger:disabled { opacity: 0.4; cursor: not-allowed; }
.confirm-text { font-size: 0.9rem; color: var(--text-primary); margin: 0; }

@media (max-width: 767.98px) {
    .page-title { font-size: 1.3rem; }
    .header-left { gap: 8px; }
    .header-actions { gap: 6px; }
    .details-grid { grid-template-columns: 1fr; }
    .form-group.full-width { grid-column: unset; }
    .tabs { overflow-x: auto; }
    .tab-btn { white-space: nowrap; padding: 10px 14px; }
}
</style>

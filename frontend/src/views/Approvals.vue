<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/utils/api'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

// ── Auth ──────────────────────────────────────────────
const isAdmin = computed(() => {
  const roles = authStore.userRoles
  if (!roles) return false
  if (Array.isArray(roles)) return roles.includes('admin')
  if (typeof roles === 'string') return roles === 'admin'
  if (roles && typeof roles === 'object') return roles.name === 'admin'
  return false
})

// ── State ─────────────────────────────────────────────
const loading = ref(true)
const approvals = ref([])
const expandedRequests = ref(new Set())
const filterOpen = ref(false)

// ── Filters ───────────────────────────────────────────
const filters = ref({
  status: route.query.status || null,
  type: route.query.type || null,
  datePreset: 'all',
  dateFrom: '',
  dateTo: '',
  createdBy: null
})

// ── Lookup data ───────────────────────────────────────
const expenseCategories = ref([])
const plantations = ref([])
const vehicles = ref([])
const consumables = ref([])
const transformationCache = ref({})
const lookupsLoaded = ref({})

async function ensureLookups(type) {
  if (lookupsLoaded.value[type]) return
  if (['EXPENSE', 'TRANSFORMATION_EXPENSE'].includes(type)) {
    if (!expenseCategories.value.length) {
      const res = await api.get('/settings/expense-categories/')
      expenseCategories.value = res.data
    }
  }
  if (type === 'EXPENSE') {
    if (!plantations.value.length) {
      const res = await api.get('/plantations/')
      plantations.value = res.data
    }
    if (!vehicles.value.length) {
      const res = await api.get('/vehicles/')
      vehicles.value = res.data
    }
  }
  if (type === 'CONSUMABLE_PURCHASE') {
    if (!consumables.value.length) {
      const res = await api.get('/consumables/')
      consumables.value = res.data
    }
  }
  lookupsLoaded.value[type] = true
}

async function ensureTransformationCached(tId) {
  if (!tId || transformationCache.value[tId]) return
  try {
    const res = await api.get(`/transformations/${tId}`)
    transformationCache.value[tId] = res.data
  } catch (err) {
    console.error('Failed to fetch transformation:', tId, err)
  }
}

// ── Lookup helpers ────────────────────────────────────
function categoryName(id) {
  if (!id) return '—'
  const cat = expenseCategories.value.find(c => c.id === id)
  return cat ? cat.name : `#${id}`
}

function plantationName(id) {
  if (!id) return '—'
  const pl = plantations.value.find(p => p.id === id)
  return pl ? pl.name : `#${id}`
}

function vehicleLabel(id) {
  if (!id) return '—'
  const v = vehicles.value.find(vh => vh.id === id)
  return v ? v.number : `#${id}`
}

function consumableName(id) {
  if (!id) return '—'
  const c = consumables.value.find(co => co.id === id)
  return c ? c.name : `#${id}`
}

function getPersonnelName(transformationId, personnelAssignmentId) {
  const t = transformationCache.value[transformationId]
  if (!t || !t.personnel_assignments) return '—'
  const pa = t.personnel_assignments.find(p => p.id === personnelAssignmentId)
  return pa ? (pa.personnel_name || `#${personnelAssignmentId}`) : `#${personnelAssignmentId}`
}

function getCalculatedWage(transformationId, personnelAssignmentId) {
  const t = transformationCache.value[transformationId]
  if (!t || !t.personnel_assignments) return null
  const pa = t.personnel_assignments.find(p => p.id === personnelAssignmentId)
  return pa ? pa.total_wages_payable : null
}

// ── Formatting ────────────────────────────────────────
function formatDate(d) {
  if (!d) return '—'
  const dt = new Date(d)
  return dt.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
}

function formatMoney(v) {
  if (v == null) return '0.00'
  return Number(v).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

// ── Type display mapping ──────────────────────────────
const typeLabels = {
  EXPENSE: 'Expense',
  CONSUMABLE_PURCHASE: 'Consumable',
  TRANSFORMATION_COMPLETION: 'Completion',
  PERSONNEL_PAYMENT: 'Personnel Payment',
  TRANSFORMATION_EXPENSE: 'Transf. Expense'
}

const typeColors = {
  EXPENSE: 'type-expense',
  CONSUMABLE_PURCHASE: 'type-consumable',
  TRANSFORMATION_COMPLETION: 'type-completion',
  PERSONNEL_PAYMENT: 'type-personnel',
  TRANSFORMATION_EXPENSE: 'type-transf-expense'
}

// ── Date logic ────────────────────────────────────────
function computeDateRange(preset) {
  const now = new Date()
  const y = now.getFullYear()
  const m = now.getMonth()
  switch (preset) {
    case 'this_week': {
      const dayOfWeek = now.getDay()
      const start = new Date(y, m, now.getDate() - dayOfWeek)
      const end = new Date(y, m, now.getDate() + (6 - dayOfWeek))
      return { from: start, to: end }
    }
    case 'this_month':
      return { from: new Date(y, m, 1), to: new Date(y, m + 1, 0) }
    case 'last_month':
      return { from: new Date(y, m - 1, 1), to: new Date(y, m, 0) }
    default:
      return null
  }
}

function toDateString(dt) {
  const y = dt.getFullYear()
  const mo = String(dt.getMonth() + 1).padStart(2, '0')
  const day = String(dt.getDate()).padStart(2, '0')
  return `${y}-${mo}-${day}`
}

function onDatePresetChange() {
  if (filters.value.datePreset === 'all') {
    filters.value.dateFrom = ''
    filters.value.dateTo = ''
  } else if (filters.value.datePreset !== 'custom') {
    const range = computeDateRange(filters.value.datePreset)
    if (range) {
      filters.value.dateFrom = toDateString(range.from)
      filters.value.dateTo = toDateString(range.to)
    }
  }
}

// ── Unique submitters (admin only) ────────────────────
const uniqueSubmitters = computed(() => {
  const map = new Map()
  approvals.value.forEach(a => {
    if (a.requested_by?.email) {
      map.set(a.requested_by_id, a.requested_by.email)
    }
  })
  return Array.from(map.entries()).map(([id, email]) => ({ id, email }))
})

// ── Filtered list (reactive) ──────────────────────────
const filteredApprovals = computed(() => {
  let list = approvals.value

  if (filters.value.status) {
    list = list.filter(a => a.status === filters.value.status)
  }

  if (filters.value.type) {
    list = list.filter(a => a.type === filters.value.type)
  }

  if (filters.value.createdBy) {
    list = list.filter(a => a.requested_by_id === filters.value.createdBy)
  }

  if (filters.value.dateFrom) {
    const from = new Date(filters.value.dateFrom)
    list = list.filter(a => new Date(a.created_at) >= from)
  }
  if (filters.value.dateTo) {
    const to = new Date(filters.value.dateTo)
    to.setHours(23, 59, 59, 999)
    list = list.filter(a => new Date(a.created_at) <= to)
  }

  return list
})

const activeFilterCount = computed(() => {
  let count = 0
  if (filters.value.status) count++
  if (filters.value.type) count++
  if (filters.value.createdBy) count++
  if (filters.value.dateFrom || filters.value.dateTo) count++
  return count
})

// ── Helpers ───────────────────────────────────────────
const DATE_FIELDS = ['date', 'purchase_date', 'completion_date']
function toDateInput(val) {
  if (!val || typeof val !== 'string') return val
  return val.slice(0, 10) // "2026-03-23T00:00:00+00:00" → "2026-03-23"
}
function normalizeDates(obj) {
  for (const key of DATE_FIELDS) {
    if (key in obj) obj[key] = toDateInput(obj[key])
  }
  return obj
}

// ── Item status summary ───────────────────────────────
function itemSummary(req) {
  const items = req.payload || []
  const total = items.length
  const pending = items.filter(i => !i.status || i.status === 'pending').length
  const approved = items.filter(i => i.status === 'approved').length
  const rejected = items.filter(i => i.status === 'rejected').length
  const parts = []
  if (pending) parts.push(`${pending} pending`)
  if (approved) parts.push(`${approved} approved`)
  if (rejected) parts.push(`${rejected} rejected`)
  return `${total} item${total !== 1 ? 's' : ''} — ${parts.join(', ')}`
}

function hasPendingItems(req) {
  return (req.payload || []).some(i => !i.status || i.status === 'pending')
}

// ── Expand/collapse ───────────────────────────────────
const loadingRequests = ref(new Set())

function toggleExpand(req) {
  if (expandedRequests.value.has(req.id)) {
    expandedRequests.value.delete(req.id)
    expandedRequests.value = new Set(expandedRequests.value)
    return
  }

  // Expand immediately, fetch lookups in background
  expandedRequests.value.add(req.id)
  expandedRequests.value = new Set(expandedRequests.value)

  if (!lookupsLoaded.value[req.type] || ['TRANSFORMATION_COMPLETION', 'PERSONNEL_PAYMENT', 'TRANSFORMATION_EXPENSE'].includes(req.type)) {
    loadingRequests.value.add(req.id)
    loadingRequests.value = new Set(loadingRequests.value)

    const load = async () => {
      await ensureLookups(req.type)
      if (['TRANSFORMATION_COMPLETION', 'PERSONNEL_PAYMENT', 'TRANSFORMATION_EXPENSE'].includes(req.type)) {
        const tIds = new Set()
        for (const item of (req.payload || [])) {
          if (item.data?.transformation_id) tIds.add(item.data.transformation_id)
        }
        await Promise.all([...tIds].map(id => ensureTransformationCached(id)))
      }
      loadingRequests.value.delete(req.id)
      loadingRequests.value = new Set(loadingRequests.value)
    }
    load()
  }
}

// ── Admin per-item actions ────────────────────────────
const editingItem = ref(null) // { requestId, index, data }
const rejectingItem = ref(null) // { requestId, index, note }

function startEditApproval(requestId, index, itemData) {
  editingItem.value = {
    requestId,
    index,
    data: normalizeDates(JSON.parse(JSON.stringify(itemData)))
  }
  rejectingItem.value = null
}

function cancelEditApproval() {
  editingItem.value = null
}

async function submitApproveWithEdits(requestId, index) {
  try {
    await api.patch(`/approvals/${requestId}/items/${index}`, {
      action: 'approve_with_edits',
      modified_data: editingItem.value.data
    })
    editingItem.value = null
    await fetchApprovals()
  } catch (err) {
    console.error('Failed to approve with edits:', err)
  }
}

async function approveItem(requestId, index) {
  try {
    await api.patch(`/approvals/${requestId}/items/${index}`, {
      action: 'approve'
    })
    await fetchApprovals()
  } catch (err) {
    console.error('Failed to approve item:', err)
  }
}

function promptReject(requestId, index) {
  rejectingItem.value = { requestId, index, note: '' }
  editingItem.value = null
}

function cancelReject() {
  rejectingItem.value = null
}

async function submitReject(requestId, index) {
  try {
    await api.patch(`/approvals/${requestId}/items/${index}`, {
      action: 'reject',
      rejection_note: rejectingItem.value?.note || ''
    })
    rejectingItem.value = null
    await fetchApprovals()
  } catch (err) {
    console.error('Failed to reject item:', err)
  }
}

// ── Admin bulk actions ────────────────────────────────
const bulkRejectingId = ref(null)
const bulkRejectNote = ref('')

async function approveAll(requestId) {
  try {
    await api.post(`/approvals/${requestId}/approve-all`)
    await fetchApprovals()
  } catch (err) {
    console.error('Failed to approve all:', err)
  }
}

function promptBulkReject(requestId) {
  bulkRejectingId.value = requestId
  bulkRejectNote.value = ''
}

function cancelBulkReject() {
  bulkRejectingId.value = null
  bulkRejectNote.value = ''
}

async function submitBulkReject(requestId) {
  try {
    await api.post(`/approvals/${requestId}/reject-all`, {
      note: bulkRejectNote.value || ''
    })
    bulkRejectingId.value = null
    bulkRejectNote.value = ''
    await fetchApprovals()
  } catch (err) {
    console.error('Failed to reject all:', err)
  }
}

// ── Manager self-service ──────────────────────────────
const editingRequest = ref(null) // { id, items, notes }

function startEditRequest(req) {
  editingRequest.value = {
    id: req.id,
    items: req.payload.map(p => normalizeDates(JSON.parse(JSON.stringify(p.data)))),
    notes: req.notes || ''
  }
}

function cancelEditRequest() {
  editingRequest.value = null
}

async function submitEditRequest() {
  if (!editingRequest.value) return
  try {
    await api.put(`/approvals/${editingRequest.value.id}`, {
      items: editingRequest.value.items.map((item, i) => ({ index: i, data: item })),
      notes: editingRequest.value.notes
    })
    editingRequest.value = null
    await fetchApprovals()
  } catch (err) {
    console.error('Failed to update request:', err)
  }
}

async function deleteRequest(reqId) {
  if (!confirm('Delete this approval request? This cannot be undone.')) return
  try {
    await api.delete(`/approvals/${reqId}`)
    await fetchApprovals()
  } catch (err) {
    console.error('Failed to delete request:', err)
  }
}

// ── Fetch data ────────────────────────────────────────
async function fetchApprovals() {
  try {
    const res = await api.get('/approvals/')
    approvals.value = res.data || []
  } catch (err) {
    console.error('Failed to fetch approvals:', err)
    approvals.value = []
  }
}

// ── Filter helpers ────────────────────────────────────
function clearFilters() {
  filters.value.status = null
  filters.value.type = null
  filters.value.datePreset = 'all'
  filters.value.dateFrom = ''
  filters.value.dateTo = ''
  filters.value.createdBy = null
  filterOpen.value = false
}

function statusChipClass(status) {
  switch (status) {
    case 'PENDING': case 'pending': return 'status-pending'
    case 'PARTIAL': return 'status-partial'
    case 'RESOLVED': case 'approved': return 'status-active'
    case 'APPROVED': return 'status-active'
    case 'REJECTED': case 'rejected': return 'status-inactive'
    default: return ''
  }
}

function isEditing(requestId, index) {
  return editingItem.value?.requestId === requestId && editingItem.value?.index === index
}

function isRejecting(requestId, index) {
  return rejectingItem.value?.requestId === requestId && rejectingItem.value?.index === index
}

function isManagerEditingRequest(reqId) {
  return editingRequest.value?.id === reqId
}

function canManagerEdit(req) {
  return req.requested_by_id === authStore.user?.id && req.status === 'PENDING'
}

// ── Lifecycle ─────────────────────────────────────────
onMounted(async () => {
  await fetchApprovals()
  loading.value = false
})
</script>

<template>
  <div class="approvals-page">
    <!-- ══════════════════════════════════════════════ -->
    <!-- PAGE HEADER                                    -->
    <!-- ══════════════════════════════════════════════ -->
    <div class="page-header animate-fade-in-up">
      <div>
        <h2 class="page-title">Approvals</h2>
        <p class="page-subtitle">Review and manage approval requests across all modules</p>
      </div>
      <div class="header-actions">
        <button class="btn-filter" @click="filterOpen = true">
          <i class="bi bi-funnel"></i>
          Filters
          <span v-if="activeFilterCount > 0" class="filter-badge">{{ activeFilterCount }}</span>
        </button>
      </div>
    </div>

    <!-- ══════════════════════════════════════════════ -->
    <!-- CONTENT                                        -->
    <!-- ══════════════════════════════════════════════ -->
    <div class="content-panel animate-fade-in-up animate-delay-1">
      <!-- Loading -->
      <div v-if="loading" class="empty-state">
        <i class="bi bi-hourglass-split"></i>
        <p>Loading approvals...</p>
      </div>

      <!-- Empty -->
      <div v-else-if="filteredApprovals.length === 0" class="empty-state">
        <i class="bi bi-check2-square"></i>
        <p>{{ activeFilterCount > 0 ? 'No approvals match your filters' : 'No approval requests found' }}</p>
      </div>

      <!-- Approval Cards -->
      <div v-else class="approvals-list">
        <div
          v-for="req in filteredApprovals"
          :key="req.id"
          class="approval-card"
        >
          <!-- Card Header -->
          <div class="approval-card-header" @click="toggleExpand(req)">
            <div class="approval-meta">
              <span class="type-badge" :class="typeColors[req.type]">
                {{ typeLabels[req.type] || req.type }}
              </span>
              <span class="status-chip" :class="statusChipClass(req.status)">
                {{ req.status }}
              </span>
              <span class="approval-submitter">
                <i class="bi bi-person"></i>
                {{ req.requested_by?.email || 'Unknown' }}
              </span>
              <span class="approval-date">
                <i class="bi bi-calendar3"></i>
                {{ formatDate(req.created_at) }}
              </span>
              <span v-if="req.reviewed_at" class="approval-date">
                <i class="bi bi-check2-circle"></i>
                {{ formatDate(req.reviewed_at) }}
              </span>
              <span class="approval-items-count">
                {{ itemSummary(req) }}
              </span>
            </div>
            <div class="approval-card-right">
              <!-- Admin bulk actions -->
              <template v-if="isAdmin && hasPendingItems(req)">
                <button class="btn-approve-all" @click.stop="approveAll(req.id)">
                  <i class="bi bi-check-all"></i> Approve All
                </button>
                <button class="btn-action-sm btn-reject" @click.stop="promptBulkReject(req.id)">
                  <i class="bi bi-x-lg"></i> Reject All
                </button>
              </template>
              <!-- Manager self-service -->
              <template v-if="!isAdmin && canManagerEdit(req)">
                <button class="btn-action-sm btn-edit-approval" @click.stop="startEditRequest(req)">
                  <i class="bi bi-pencil"></i> Edit
                </button>
                <button class="btn-action-sm btn-reject" @click.stop="deleteRequest(req.id)">
                  <i class="bi bi-trash"></i> Delete
                </button>
              </template>
              <i
                class="bi expand-chevron"
                :class="expandedRequests.has(req.id) ? 'bi-chevron-up' : 'bi-chevron-down'"
              ></i>
            </div>
          </div>

          <!-- Bulk Reject Note Input -->
          <div v-if="bulkRejectingId === req.id" class="bulk-reject-bar">
            <input
              v-model="bulkRejectNote"
              type="text"
              class="form-control form-control-sm"
              placeholder="Rejection note (optional)..."
            />
            <button class="btn-action-sm btn-reject" @click="submitBulkReject(req.id)">
              <i class="bi bi-x-lg"></i> Confirm Reject All
            </button>
            <button class="btn-action-sm btn-cancel-edit" @click="cancelBulkReject">
              Cancel
            </button>
          </div>

          <!-- Manager Edit Request Form -->
          <div v-if="isManagerEditingRequest(req.id)" class="manager-edit-panel">
            <div class="manager-edit-header">
              <span>Edit Request Items</span>
            </div>
            <div
              v-for="(item, idx) in editingRequest.items"
              :key="idx"
              class="manager-edit-item"
            >
              <div class="manager-edit-item-label">Item {{ idx + 1 }}</div>
              <div class="approval-edit-fields">
                <!-- EXPENSE edit -->
                <template v-if="req.type === 'EXPENSE'">
                  <div class="ae-field">
                    <label class="ae-label">Date</label>
                    <input v-model="item.date" type="date" class="form-control form-control-sm" />
                  </div>
                  <div class="ae-field">
                    <label class="ae-label">Amount</label>
                    <input v-model="item.amount" type="number" step="0.01" min="0" class="form-control form-control-sm" />
                  </div>
                  <div class="ae-field">
                    <label class="ae-label">Category</label>
                    <select v-model="item.category_id" class="form-select form-select-sm">
                      <option :value="null" disabled>Select</option>
                      <option v-for="cat in expenseCategories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
                    </select>
                  </div>
                  <div class="ae-field">
                    <label class="ae-label">Plantation</label>
                    <select v-model="item.plantation_id" class="form-select form-select-sm">
                      <option :value="null">None</option>
                      <option v-for="pl in plantations" :key="pl.id" :value="pl.id">{{ pl.name }}</option>
                    </select>
                  </div>
                  <div class="ae-field">
                    <label class="ae-label">Vehicle</label>
                    <select v-model="item.vehicle_id" class="form-select form-select-sm">
                      <option :value="null">None</option>
                      <option v-for="veh in vehicles" :key="veh.id" :value="veh.id">{{ veh.number }}</option>
                    </select>
                  </div>
                  <div class="ae-field ae-field-wide">
                    <label class="ae-label">Description</label>
                    <input v-model="item.description" type="text" class="form-control form-control-sm" placeholder="Optional" />
                  </div>
                </template>

                <!-- CONSUMABLE_PURCHASE edit -->
                <template v-if="req.type === 'CONSUMABLE_PURCHASE'">
                  <div class="ae-field">
                    <label class="ae-label">Consumable</label>
                    <span class="ae-readonly">{{ consumableName(item.consumable_id) }}</span>
                  </div>
                  <div class="ae-field">
                    <label class="ae-label">Purchase Date</label>
                    <input v-model="item.purchase_date" type="date" class="form-control form-control-sm" />
                  </div>
                  <div class="ae-field">
                    <label class="ae-label">Quantity</label>
                    <input v-model="item.quantity" type="number" step="0.01" min="0" class="form-control form-control-sm" />
                  </div>
                  <div class="ae-field">
                    <label class="ae-label">Unit Cost</label>
                    <input v-model="item.unit_cost" type="number" step="0.01" min="0" class="form-control form-control-sm" />
                  </div>
                  <div class="ae-field">
                    <label class="ae-label">Supplier</label>
                    <input v-model="item.supplier" type="text" class="form-control form-control-sm" />
                  </div>
                  <div class="ae-field">
                    <label class="ae-label">Invoice #</label>
                    <input v-model="item.invoice_number" type="text" class="form-control form-control-sm" />
                  </div>
                  <div class="ae-field ae-field-wide">
                    <label class="ae-label">Notes</label>
                    <textarea v-model="item.notes" class="form-control form-control-sm" rows="2"></textarea>
                  </div>
                </template>

                <!-- TRANSFORMATION_COMPLETION edit -->
                <template v-if="req.type === 'TRANSFORMATION_COMPLETION'">
                  <div class="ae-field">
                    <label class="ae-label">Transformation</label>
                    <span class="ae-readonly">#{{ item.transformation_id }}</span>
                  </div>
                  <div class="ae-field">
                    <label class="ae-label">Completion Date</label>
                    <input v-model="item.completion_date" type="date" class="form-control form-control-sm" />
                  </div>
                </template>

                <!-- PERSONNEL_PAYMENT edit -->
                <template v-if="req.type === 'PERSONNEL_PAYMENT'">
                  <div class="ae-field">
                    <label class="ae-label">Transformation</label>
                    <span class="ae-readonly">#{{ item.transformation_id }}</span>
                  </div>
                  <div class="ae-field">
                    <label class="ae-label">Personnel</label>
                    <span class="ae-readonly">{{ getPersonnelName(item.transformation_id, item.personnel_assignment_id) }}</span>
                  </div>
                  <div class="ae-field">
                    <label class="ae-label">Calculated Wage</label>
                    <span class="ae-readonly">{{ formatMoney(getCalculatedWage(item.transformation_id, item.personnel_assignment_id)) }}</span>
                  </div>
                  <div class="ae-field">
                    <label class="ae-label">Additional Payments</label>
                    <input v-model="item.additional_payments" type="number" step="0.01" min="0" class="form-control form-control-sm" />
                  </div>
                  <div class="ae-field ae-field-wide">
                    <label class="ae-label">Additional Payments Description</label>
                    <input v-model="item.additional_payments_description" type="text" class="form-control form-control-sm" />
                  </div>
                  <div class="ae-field ae-field-wide">
                    <label class="ae-label">Notes</label>
                    <textarea v-model="item.notes" class="form-control form-control-sm" rows="2"></textarea>
                  </div>
                </template>

                <!-- TRANSFORMATION_EXPENSE edit -->
                <template v-if="req.type === 'TRANSFORMATION_EXPENSE'">
                  <div class="ae-field">
                    <label class="ae-label">Transformation</label>
                    <span class="ae-readonly">#{{ item.transformation_id }}</span>
                  </div>
                  <div class="ae-field">
                    <label class="ae-label">Amount</label>
                    <input v-model="item.amount" type="number" step="0.01" min="0" class="form-control form-control-sm" />
                  </div>
                  <div class="ae-field">
                    <label class="ae-label">Category</label>
                    <select v-model="item.category_id" class="form-select form-select-sm">
                      <option :value="null" disabled>Select</option>
                      <option v-for="cat in expenseCategories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
                    </select>
                  </div>
                  <div class="ae-field ae-field-wide">
                    <label class="ae-label">Description</label>
                    <input v-model="item.description" type="text" class="form-control form-control-sm" />
                  </div>
                  <div class="ae-field">
                    <label class="ae-label">Date</label>
                    <input v-model="item.date" type="date" class="form-control form-control-sm" />
                  </div>
                </template>
              </div>
            </div>
            <div class="ae-field ae-field-wide" style="padding: 0 18px;">
              <label class="ae-label">Notes</label>
              <textarea v-model="editingRequest.notes" class="form-control form-control-sm" rows="2" placeholder="Optional notes..."></textarea>
            </div>
            <div class="manager-edit-footer">
              <button class="btn-action-sm btn-approve" @click="submitEditRequest">
                <i class="bi bi-check-lg"></i> Save Changes
              </button>
              <button class="btn-action-sm btn-cancel-edit" @click="cancelEditRequest">
                <i class="bi bi-x-lg"></i> Cancel
              </button>
            </div>
          </div>

          <!-- Loading indicator -->
          <div v-if="expandedRequests.has(req.id) && loadingRequests.has(req.id)" class="approval-items-loading">
            <i class="bi bi-arrow-repeat spinning"></i> Loading details...
          </div>

          <!-- Expanded Items -->
          <div v-if="expandedRequests.has(req.id) && !loadingRequests.has(req.id) && !isManagerEditingRequest(req.id)" class="approval-items">
            <div
              v-for="(item, idx) in req.payload"
              :key="idx"
              class="approval-item-row"
              :class="`item-status-${(item.status || 'pending').toLowerCase()}`"
            >
              <!-- Normal display (not editing, not rejecting) -->
              <template v-if="!isEditing(req.id, idx) && !isRejecting(req.id, idx)">
                <div class="approval-item-info">
                  <!-- Item status badge -->
                  <span
                    v-if="item.status && item.status !== 'pending'"
                    class="status-chip status-chip-sm"
                    :class="statusChipClass(item.status)"
                  >
                    {{ item.status }}
                  </span>

                  <!-- EXPENSE display -->
                  <template v-if="req.type === 'EXPENSE'">
                    <span class="item-field dimmed">{{ formatDate(item.data?.date) }}</span>
                    <span class="item-amount">{{ formatMoney(item.data?.amount) }}</span>
                    <span class="approval-item-category">{{ categoryName(item.data?.category_id) }}</span>
                    <span v-if="item.data?.plantation_id" class="approval-item-tag tag-plantation">
                      <i class="bi bi-geo-alt"></i> {{ plantationName(item.data.plantation_id) }}
                    </span>
                    <span v-if="item.data?.vehicle_id" class="approval-item-tag tag-vehicle">
                      <i class="bi bi-truck"></i> {{ vehicleLabel(item.data.vehicle_id) }}
                    </span>
                    <span v-if="item.data?.description" class="item-field dimmed">{{ item.data.description }}</span>
                  </template>

                  <!-- CONSUMABLE_PURCHASE display -->
                  <template v-if="req.type === 'CONSUMABLE_PURCHASE'">
                    <span class="item-field">{{ consumableName(item.data?.consumable_id) }}</span>
                    <span class="item-field dimmed">{{ formatDate(item.data?.purchase_date) }}</span>
                    <span class="item-field">Qty: {{ Number(item.data?.quantity || 0) }}</span>
                    <span class="item-amount">{{ formatMoney(item.data?.unit_cost) }}</span>
                    <span v-if="item.data?.supplier" class="item-field dimmed">{{ item.data.supplier }}</span>
                    <span v-if="item.data?.invoice_number" class="item-field dimmed">Inv: {{ item.data.invoice_number }}</span>
                    <span v-if="item.data?.notes" class="item-field dimmed">{{ item.data.notes }}</span>
                  </template>

                  <!-- TRANSFORMATION_COMPLETION display -->
                  <template v-if="req.type === 'TRANSFORMATION_COMPLETION'">
                    <router-link
                      :to="{ name: 'transformation-detail', params: { id: item.data?.transformation_id } }"
                      class="item-link"
                      @click.stop
                    >
                      Transformation #{{ item.data?.transformation_id }}
                    </router-link>
                    <span class="item-field dimmed">{{ formatDate(item.data?.completion_date) }}</span>
                  </template>

                  <!-- PERSONNEL_PAYMENT display -->
                  <template v-if="req.type === 'PERSONNEL_PAYMENT'">
                    <router-link
                      :to="{ name: 'transformation-detail', params: { id: item.data?.transformation_id } }"
                      class="item-link"
                      @click.stop
                    >
                      Transformation #{{ item.data?.transformation_id }}
                    </router-link>
                    <span class="item-field">{{ getPersonnelName(item.data?.transformation_id, item.data?.personnel_assignment_id) }}</span>
                    <span class="item-field dimmed">
                      Calc. Wage: {{ formatMoney(getCalculatedWage(item.data?.transformation_id, item.data?.personnel_assignment_id)) }}
                    </span>
                    <span v-if="item.data?.additional_payments" class="item-amount">
                      +{{ formatMoney(item.data.additional_payments) }}
                    </span>
                    <span v-if="item.data?.additional_payments_description" class="item-field dimmed">
                      {{ item.data.additional_payments_description }}
                    </span>
                    <span v-if="item.data?.notes" class="item-field dimmed">{{ item.data.notes }}</span>
                  </template>

                  <!-- TRANSFORMATION_EXPENSE display -->
                  <template v-if="req.type === 'TRANSFORMATION_EXPENSE'">
                    <router-link
                      :to="{ name: 'transformation-detail', params: { id: item.data?.transformation_id } }"
                      class="item-link"
                      @click.stop
                    >
                      Transformation #{{ item.data?.transformation_id }}
                    </router-link>
                    <span class="item-amount">{{ formatMoney(item.data?.amount) }}</span>
                    <span class="approval-item-category">{{ categoryName(item.data?.category_id) }}</span>
                    <span v-if="item.data?.description" class="item-field dimmed">{{ item.data.description }}</span>
                    <span class="item-field dimmed">{{ formatDate(item.data?.date) }}</span>
                  </template>

                  <!-- Rejection note -->
                  <span v-if="item.rejection_note" class="rejection-note">
                    <i class="bi bi-chat-left-text"></i> {{ item.rejection_note }}
                  </span>
                </div>

                <!-- Admin per-item actions -->
                <div v-if="isAdmin && (!item.status || item.status === 'pending')" class="approval-item-actions">
                  <button class="btn-action-sm btn-approve" @click="approveItem(req.id, idx)">
                    <i class="bi bi-check-lg"></i> Approve
                  </button>
                  <button class="btn-action-sm btn-edit-approval" @click="startEditApproval(req.id, idx, item.data)">
                    <i class="bi bi-pencil"></i> Edit &amp; Approve
                  </button>
                  <button class="btn-action-sm btn-reject" @click="promptReject(req.id, idx)">
                    <i class="bi bi-x-lg"></i> Reject
                  </button>
                </div>
              </template>

              <!-- Inline Edit & Approve form -->
              <template v-else-if="isEditing(req.id, idx)">
                <div class="approval-edit-form">
                  <div class="approval-edit-fields">
                    <!-- EXPENSE edit -->
                    <template v-if="req.type === 'EXPENSE'">
                      <div class="ae-field">
                        <label class="ae-label">Date</label>
                        <input v-model="editingItem.data.date" type="date" class="form-control form-control-sm" />
                      </div>
                      <div class="ae-field">
                        <label class="ae-label">Amount</label>
                        <input v-model="editingItem.data.amount" type="number" step="0.01" min="0" class="form-control form-control-sm" />
                      </div>
                      <div class="ae-field">
                        <label class="ae-label">Category</label>
                        <select v-model="editingItem.data.category_id" class="form-select form-select-sm">
                          <option :value="null" disabled>Select</option>
                          <option v-for="cat in expenseCategories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
                        </select>
                      </div>
                      <div class="ae-field">
                        <label class="ae-label">Plantation</label>
                        <select v-model="editingItem.data.plantation_id" class="form-select form-select-sm">
                          <option :value="null">None</option>
                          <option v-for="pl in plantations" :key="pl.id" :value="pl.id">{{ pl.name }}</option>
                        </select>
                      </div>
                      <div class="ae-field">
                        <label class="ae-label">Vehicle</label>
                        <select v-model="editingItem.data.vehicle_id" class="form-select form-select-sm">
                          <option :value="null">None</option>
                          <option v-for="veh in vehicles" :key="veh.id" :value="veh.id">{{ veh.number }}</option>
                        </select>
                      </div>
                      <div class="ae-field ae-field-wide">
                        <label class="ae-label">Description</label>
                        <input v-model="editingItem.data.description" type="text" class="form-control form-control-sm" placeholder="Optional" />
                      </div>
                    </template>

                    <!-- CONSUMABLE_PURCHASE edit -->
                    <template v-if="req.type === 'CONSUMABLE_PURCHASE'">
                      <div class="ae-field">
                        <label class="ae-label">Consumable</label>
                        <span class="ae-readonly">{{ consumableName(editingItem.data.consumable_id) }}</span>
                      </div>
                      <div class="ae-field">
                        <label class="ae-label">Purchase Date</label>
                        <input v-model="editingItem.data.purchase_date" type="date" class="form-control form-control-sm" />
                      </div>
                      <div class="ae-field">
                        <label class="ae-label">Quantity</label>
                        <input v-model="editingItem.data.quantity" type="number" step="0.01" min="0" class="form-control form-control-sm" />
                      </div>
                      <div class="ae-field">
                        <label class="ae-label">Unit Cost</label>
                        <input v-model="editingItem.data.unit_cost" type="number" step="0.01" min="0" class="form-control form-control-sm" />
                      </div>
                      <div class="ae-field">
                        <label class="ae-label">Supplier</label>
                        <input v-model="editingItem.data.supplier" type="text" class="form-control form-control-sm" />
                      </div>
                      <div class="ae-field">
                        <label class="ae-label">Invoice #</label>
                        <input v-model="editingItem.data.invoice_number" type="text" class="form-control form-control-sm" />
                      </div>
                      <div class="ae-field ae-field-wide">
                        <label class="ae-label">Notes</label>
                        <textarea v-model="editingItem.data.notes" class="form-control form-control-sm" rows="2"></textarea>
                      </div>
                    </template>

                    <!-- TRANSFORMATION_COMPLETION edit -->
                    <template v-if="req.type === 'TRANSFORMATION_COMPLETION'">
                      <div class="ae-field">
                        <label class="ae-label">Transformation</label>
                        <span class="ae-readonly">#{{ editingItem.data.transformation_id }}</span>
                      </div>
                      <div class="ae-field">
                        <label class="ae-label">Completion Date</label>
                        <input v-model="editingItem.data.completion_date" type="date" class="form-control form-control-sm" />
                      </div>
                    </template>

                    <!-- PERSONNEL_PAYMENT edit -->
                    <template v-if="req.type === 'PERSONNEL_PAYMENT'">
                      <div class="ae-field">
                        <label class="ae-label">Transformation</label>
                        <span class="ae-readonly">#{{ editingItem.data.transformation_id }}</span>
                      </div>
                      <div class="ae-field">
                        <label class="ae-label">Personnel</label>
                        <span class="ae-readonly">{{ getPersonnelName(editingItem.data.transformation_id, editingItem.data.personnel_assignment_id) }}</span>
                      </div>
                      <div class="ae-field">
                        <label class="ae-label">Calculated Wage</label>
                        <span class="ae-readonly">{{ formatMoney(getCalculatedWage(editingItem.data.transformation_id, editingItem.data.personnel_assignment_id)) }}</span>
                      </div>
                      <div class="ae-field">
                        <label class="ae-label">Additional Payments</label>
                        <input v-model="editingItem.data.additional_payments" type="number" step="0.01" min="0" class="form-control form-control-sm" />
                      </div>
                      <div class="ae-field ae-field-wide">
                        <label class="ae-label">Add. Payments Description</label>
                        <input v-model="editingItem.data.additional_payments_description" type="text" class="form-control form-control-sm" />
                      </div>
                      <div class="ae-field ae-field-wide">
                        <label class="ae-label">Notes</label>
                        <textarea v-model="editingItem.data.notes" class="form-control form-control-sm" rows="2"></textarea>
                      </div>
                    </template>

                    <!-- TRANSFORMATION_EXPENSE edit -->
                    <template v-if="req.type === 'TRANSFORMATION_EXPENSE'">
                      <div class="ae-field">
                        <label class="ae-label">Transformation</label>
                        <span class="ae-readonly">#{{ editingItem.data.transformation_id }}</span>
                      </div>
                      <div class="ae-field">
                        <label class="ae-label">Amount</label>
                        <input v-model="editingItem.data.amount" type="number" step="0.01" min="0" class="form-control form-control-sm" />
                      </div>
                      <div class="ae-field">
                        <label class="ae-label">Category</label>
                        <select v-model="editingItem.data.category_id" class="form-select form-select-sm">
                          <option :value="null" disabled>Select</option>
                          <option v-for="cat in expenseCategories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
                        </select>
                      </div>
                      <div class="ae-field ae-field-wide">
                        <label class="ae-label">Description</label>
                        <input v-model="editingItem.data.description" type="text" class="form-control form-control-sm" />
                      </div>
                      <div class="ae-field">
                        <label class="ae-label">Date</label>
                        <input v-model="editingItem.data.date" type="date" class="form-control form-control-sm" />
                      </div>
                    </template>
                  </div>
                  <div class="approval-edit-btns">
                    <button class="btn-action-sm btn-approve" @click="submitApproveWithEdits(req.id, idx)">
                      <i class="bi bi-check-lg"></i> Save &amp; Approve
                    </button>
                    <button class="btn-action-sm btn-cancel-edit" @click="cancelEditApproval">
                      <i class="bi bi-x-lg"></i> Cancel
                    </button>
                  </div>
                </div>
              </template>

              <!-- Inline Reject form -->
              <template v-else-if="isRejecting(req.id, idx)">
                <div class="approval-edit-form">
                  <div class="approval-edit-fields">
                    <div class="ae-field ae-field-wide">
                      <label class="ae-label">Rejection Note</label>
                      <input
                        v-model="rejectingItem.note"
                        type="text"
                        class="form-control form-control-sm"
                        placeholder="Reason for rejection (optional)..."
                      />
                    </div>
                  </div>
                  <div class="approval-edit-btns">
                    <button class="btn-action-sm btn-reject" @click="submitReject(req.id, idx)">
                      <i class="bi bi-x-lg"></i> Confirm Reject
                    </button>
                    <button class="btn-action-sm btn-cancel-edit" @click="cancelReject">
                      Cancel
                    </button>
                  </div>
                </div>
              </template>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ══════════════════════════════════════════════ -->
    <!-- FILTER SIDEBAR                                 -->
    <!-- ══════════════════════════════════════════════ -->
    <Transition name="fade">
      <div v-if="filterOpen" class="filter-overlay" @click="filterOpen = false"></div>
    </Transition>
    <Transition name="slide-right">
      <aside v-if="filterOpen" class="filter-sidebar">
        <div class="filter-sidebar-header">
          <h5>Filters</h5>
          <button class="btn-close-filter" @click="filterOpen = false"><i class="bi bi-x-lg"></i></button>
        </div>

        <div class="filter-sidebar-body">
          <!-- Status -->
          <div class="filter-group">
            <label class="filter-label">Status</label>
            <div class="status-chips">
              <button :class="['chip', { active: !filters.status }]" @click="filters.status = null">All</button>
              <button :class="['chip', { active: filters.status === 'PENDING' }]" @click="filters.status = 'PENDING'">Pending</button>
              <button :class="['chip', { active: filters.status === 'PARTIAL' }]" @click="filters.status = 'PARTIAL'">Partial</button>
              <button :class="['chip', { active: filters.status === 'RESOLVED' }]" @click="filters.status = 'RESOLVED'">Resolved</button>
            </div>
          </div>

          <!-- Category / Type -->
          <div class="filter-group">
            <label class="filter-label">Category</label>
            <div class="status-chips">
              <button :class="['chip', { active: !filters.type }]" @click="filters.type = null">All</button>
              <button :class="['chip', { active: filters.type === 'EXPENSE' }]" @click="filters.type = 'EXPENSE'">Expense</button>
              <button :class="['chip', { active: filters.type === 'CONSUMABLE_PURCHASE' }]" @click="filters.type = 'CONSUMABLE_PURCHASE'">Consumable</button>
              <button :class="['chip', { active: filters.type === 'TRANSFORMATION_COMPLETION' }]" @click="filters.type = 'TRANSFORMATION_COMPLETION'">Completion</button>
              <button :class="['chip', { active: filters.type === 'PERSONNEL_PAYMENT' }]" @click="filters.type = 'PERSONNEL_PAYMENT'">Personnel Payment</button>
              <button :class="['chip', { active: filters.type === 'TRANSFORMATION_EXPENSE' }]" @click="filters.type = 'TRANSFORMATION_EXPENSE'">Transf. Expense</button>
            </div>
          </div>

          <!-- Date Range -->
          <div class="filter-group">
            <label class="filter-label">Date Range</label>
            <select v-model="filters.datePreset" class="form-select" @change="onDatePresetChange">
              <option value="all">All Time</option>
              <option value="this_week">This Week</option>
              <option value="this_month">This Month</option>
              <option value="last_month">Last Month</option>
              <option value="custom">Custom</option>
            </select>
            <div v-if="filters.datePreset === 'custom'" class="custom-dates">
              <input type="date" v-model="filters.dateFrom" class="form-control" />
              <span class="date-sep">to</span>
              <input type="date" v-model="filters.dateTo" class="form-control" />
            </div>
          </div>

          <!-- Created By (admin only) -->
          <div v-if="isAdmin && uniqueSubmitters.length > 0" class="filter-group">
            <label class="filter-label">Created By</label>
            <select v-model="filters.createdBy" class="form-select">
              <option :value="null">All Users</option>
              <option v-for="sub in uniqueSubmitters" :key="sub.id" :value="sub.id">{{ sub.email }}</option>
            </select>
          </div>
        </div>

        <div class="filter-sidebar-footer">
          <button class="btn-modal btn-modal-cancel" @click="clearFilters">Clear All</button>
          <button class="btn-modal btn-modal-confirm" @click="filterOpen = false">Done</button>
        </div>
      </aside>
    </Transition>
  </div>
</template>

<style scoped>
/* ── Page Layout ──────────────────────────────────── */
.approvals-page {
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

/* ── Filter Button ────────────────────────────────── */
.btn-filter {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 9px 18px;
  border: 1.5px solid var(--border);
  border-radius: 10px;
  background: var(--bg-card);
  color: var(--text-primary);
  font-family: var(--font-body);
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.btn-filter:hover {
  border-color: var(--moss);
  color: var(--moss);
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

/* ── Content Panel ────────────────────────────────── */
.content-panel {
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: 14px;
  box-shadow: var(--shadow-sm);
  overflow: hidden;
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

/* ── Approval Cards ───────────────────────────────── */
.approvals-list {
  position: relative;
}

.approval-card {
  border-bottom: 1px solid var(--border-light);
}

.approval-card:last-child {
  border-bottom: none;
}

.approval-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 18px;
  cursor: pointer;
  transition: background var(--transition-fast);
}

.approval-card-header:hover {
  background: rgba(138, 154, 123, 0.04);
}

.approval-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.approval-submitter,
.approval-date,
.approval-items-count {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 0.82rem;
  color: var(--text-secondary);
}

.approval-submitter {
  font-weight: 600;
  color: var(--text-primary);
}

.approval-submitter i,
.approval-date i {
  font-size: 0.78rem;
  color: var(--text-secondary);
}

.approval-card-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.expand-chevron {
  color: var(--text-secondary);
  font-size: 0.85rem;
  transition: transform var(--transition-fast);
}

/* ── Type Badges ──────────────────────────────────── */
.type-badge {
  display: inline-flex;
  align-items: center;
  font-size: 0.7rem;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 20px;
  white-space: nowrap;
  letter-spacing: 0.01em;
}

.type-expense {
  background: rgba(196, 163, 90, 0.14);
  color: #8a6f2a;
}

.type-consumable {
  background: rgba(74, 103, 65, 0.1);
  color: var(--moss);
}

.type-completion {
  background: rgba(96, 139, 193, 0.12);
  color: #4a7bad;
}

.type-personnel {
  background: rgba(181, 105, 77, 0.12);
  color: var(--sienna);
}

.type-transf-expense {
  background: rgba(138, 154, 123, 0.14);
  color: var(--sage);
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
  background: rgba(96, 139, 193, 0.12);
  color: #4a7bad;
}

/* ── Approval Items (expanded) ────────────────────── */
.approval-items-loading {
  border-top: 1px solid var(--border-light);
  background: var(--parchment-deep);
  padding: 1rem;
  text-align: center;
  color: var(--text-secondary);
  font-size: 0.85rem;
}

.spinning {
  display: inline-block;
  animation: spin 1s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

.approval-items {
  border-top: 1px solid var(--border-light);
  background: var(--parchment-deep);
}

.approval-item-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 18px;
  border-bottom: 1px solid var(--border-light);
  transition: background var(--transition-fast);
}

.approval-item-row:last-child {
  border-bottom: none;
}

.approval-item-row.item-status-approved {
  background: rgba(74, 103, 65, 0.04);
}

.approval-item-row.item-status-rejected {
  background: rgba(181, 105, 77, 0.04);
}

.approval-item-info {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  flex: 1;
  min-width: 0;
}

.item-field {
  font-size: 0.82rem;
  color: var(--text-primary);
}

.item-field.dimmed {
  color: var(--text-secondary);
  opacity: 0.8;
}

.item-amount {
  font-weight: 700;
  font-size: 0.88rem;
  color: var(--text-primary);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.item-amount::before {
  content: '\20B9';
}

.item-link {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--moss);
  text-decoration: none;
}

.item-link:hover {
  text-decoration: underline;
}

.approval-item-category {
  display: inline-flex;
  align-items: center;
  font-size: 0.7rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 20px;
  background: rgba(196, 163, 90, 0.14);
  color: #8a6f2a;
  white-space: nowrap;
}

.approval-item-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.7rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 20px;
  white-space: nowrap;
}

.tag-plantation {
  background: rgba(74, 103, 65, 0.08);
  color: var(--moss);
}

.tag-vehicle {
  background: rgba(138, 154, 123, 0.1);
  color: var(--sage);
}

.rejection-note {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 0.76rem;
  color: var(--sienna);
  font-style: italic;
}

.rejection-note i {
  font-size: 0.72rem;
}

/* ── Item Actions ─────────────────────────────────── */
.approval-item-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.btn-action-sm {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 12px;
  border: 1.5px solid var(--border);
  border-radius: 7px;
  background: transparent;
  color: var(--text-secondary);
  font-family: var(--font-body);
  font-size: 0.76rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.btn-action-sm i {
  font-size: 0.78rem;
}

.btn-approve {
  border-color: var(--moss);
  color: var(--moss);
}

.btn-approve:hover {
  background: rgba(74, 103, 65, 0.08);
}

.btn-approve-all {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border: 1.5px solid var(--moss);
  border-radius: 8px;
  background: transparent;
  color: var(--moss);
  font-family: var(--font-body);
  font-size: 0.78rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.btn-approve-all:hover {
  background: rgba(74, 103, 65, 0.08);
}

.btn-edit-approval {
  border-color: var(--harvest);
  color: #8a6f2a;
}

.btn-edit-approval:hover {
  background: rgba(196, 163, 90, 0.08);
}

.btn-reject {
  border-color: var(--sienna);
  color: var(--sienna);
}

.btn-reject:hover {
  background: rgba(181, 105, 77, 0.06);
}

.btn-cancel-edit {
  border-color: var(--border);
  color: var(--text-secondary);
}

.btn-cancel-edit:hover {
  border-color: var(--sienna);
  color: var(--sienna);
}

/* ── Edit Inline Form ─────────────────────────────── */
.approval-edit-form {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.approval-edit-fields {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  align-items: flex-end;
}

.ae-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 110px;
  flex: 1;
}

.ae-field-wide {
  min-width: 180px;
  flex: 2;
}

.ae-label {
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.ae-readonly {
  font-size: 0.82rem;
  color: var(--text-primary);
  padding: 4px 0;
  font-weight: 500;
}

.approval-edit-btns {
  display: flex;
  gap: 8px;
}

/* ── Bulk Reject Bar ──────────────────────────────── */
.bulk-reject-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 18px;
  background: rgba(181, 105, 77, 0.04);
  border-top: 1px solid var(--border-light);
}

.bulk-reject-bar .form-control {
  flex: 1;
  max-width: 400px;
}

/* ── Manager Edit Panel ───────────────────────────── */
.manager-edit-panel {
  border-top: 1px solid var(--border-light);
  background: var(--parchment-deep);
}

.manager-edit-header {
  padding: 12px 18px;
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--text-primary);
  border-bottom: 1px solid var(--border-light);
}

.manager-edit-item {
  padding: 12px 18px;
  border-bottom: 1px solid var(--border-light);
}

.manager-edit-item-label {
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--text-secondary);
  margin-bottom: 8px;
  letter-spacing: 0.04em;
}

.manager-edit-footer {
  display: flex;
  gap: 8px;
  padding: 12px 18px;
}

/* ── Filter Sidebar ───────────────────────────────── */
.filter-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.15);
  backdrop-filter: blur(2px);
  z-index: 1100;
}

.filter-sidebar {
  position: fixed;
  top: 0;
  right: 0;
  width: 340px;
  max-width: 85vw;
  height: 100vh;
  background: var(--bg-card);
  z-index: 1200;
  display: flex;
  flex-direction: column;
  box-shadow: -4px 0 24px rgba(0, 0, 0, 0.12);
}

.filter-sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 20px 16px;
  border-bottom: 1px solid var(--border-light);
}

.filter-sidebar-header h5 {
  font-family: var(--font-display);
  font-size: 1.1rem;
  margin: 0;
  color: var(--text-primary);
}

.btn-close-filter {
  border: none;
  background: none;
  color: var(--text-secondary);
  font-size: 1.1rem;
  cursor: pointer;
  padding: 4px;
}

.btn-close-filter:hover {
  color: var(--text-primary);
}

.filter-sidebar-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
}

.filter-group {
  margin-bottom: 20px;
}

.filter-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
  display: block;
}

.status-chips {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.chip {
  padding: 6px 14px;
  border-radius: 20px;
  border: 1.5px solid var(--border);
  background: transparent;
  color: var(--text-secondary);
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.chip:hover {
  border-color: var(--sage);
  color: var(--text-primary);
}

.chip.active {
  border-color: var(--moss);
  background: rgba(74, 103, 65, 0.08);
  color: var(--moss);
  font-weight: 600;
}

.custom-dates {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
}

.date-sep {
  font-size: 0.78rem;
  color: var(--text-secondary);
}

.filter-sidebar-footer {
  padding: 14px 20px;
  border-top: 1px solid var(--border-light);
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
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.btn-modal:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-modal-cancel { background: transparent; color: var(--text-secondary); }
.btn-modal-cancel:hover { background: var(--parchment-deep); color: var(--text-primary); }
.btn-modal-confirm { background: var(--moss); color: var(--white); }
.btn-modal-confirm:hover:not(:disabled) { background: var(--moss-light); }

/* ── Transitions ──────────────────────────────────── */
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.slide-right-enter-active { transition: transform 0.25s ease-out; }
.slide-right-leave-active { transition: transform 0.2s ease-in; }
.slide-right-enter-from, .slide-right-leave-to { transform: translateX(100%); }

/* ── Animations ───────────────────────────────────── */
.animate-fade-in-up {
  animation: fadeInUp 0.4s ease both;
}

.animate-delay-1 { animation-delay: 0.08s; }
.animate-delay-2 { animation-delay: 0.16s; }

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ── Responsive ───────────────────────────────────── */
@media (max-width: 767.98px) {
  .page-header { margin-bottom: 18px; }
  .page-title { font-size: 1.35rem; }

  .approval-card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .approval-card-right {
    width: 100%;
    flex-wrap: wrap;
  }

  .approval-item-row {
    flex-direction: column;
    gap: 8px;
  }

  .approval-item-actions {
    flex-wrap: wrap;
  }

  .approval-edit-fields {
    flex-direction: column;
  }

  .ae-field {
    min-width: 100%;
  }

  .bulk-reject-bar {
    flex-direction: column;
    align-items: stretch;
  }

  .bulk-reject-bar .form-control {
    max-width: 100%;
  }
}
</style>

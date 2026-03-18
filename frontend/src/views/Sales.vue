<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { Modal } from 'bootstrap'
import api from '../utils/api'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const isAdmin = auth.userRoles?.includes('admin')

// --- List state ---
const sales = ref([])
const loading = ref(true)
const salableStages = ref([])

// --- Filter sidebar ---
const filterOpen = ref(false)
const filterStatus = ref(null)
const filterStageId = ref(null)
const filterDatePreset = ref('all')
const filterDateFrom = ref('')
const filterDateTo = ref('')
const filterCustomerQ = ref('')

// --- Create sale modal ---
const createModalRef = ref(null)
let createModal = null
const saving = ref(false)
const formError = ref('')
const form = ref({
  customer_id: null,
  stage_id: null,
  sale_date: new Date().toISOString().slice(0, 10),
  quantity_sold: '',
  selling_price_per_kg: '',
  allocation_mode: 'FIFO',
  manual_allocations: [],
  notes: '',
})

// --- Customer search ---
const customerQuery = ref('')
const customerResults = ref([])
const selectedCustomer = ref(null)
const searchingCustomers = ref(false)
const suggestedCustomers = ref([])
const showCustomerDropdown = ref(false)
let customerSearchTimeout = null

// --- New customer modal ---
const newCustomerModalRef = ref(null)
let newCustomerModal = null
const newCustomerForm = ref({ name: '', phone: '', address: '', notes: '' })
const newCustomerError = ref('')
const savingCustomer = ref(false)

// --- Batch selection (for manual mode) ---
const availableBatches = ref([])
const selectedBatchIds = ref([])
const allocationPreview = ref([])
const loadingBatches = ref(false)

// --- Detail modal ---
const detailModalRef = ref(null)
let detailModal = null
const detailSale = ref(null)
const loadingDetail = ref(false)
const rejectReason = ref('')
const showRejectInput = ref(false)
const approving = ref(false)
const rejecting = ref(false)
const deleting = ref(false)
const showDeleteConfirm = ref(false)

// --- Computed ---
const totalAmount = computed(() => {
  const qty = parseFloat(form.value.quantity_sold) || 0
  const rate = parseFloat(form.value.selling_price_per_kg) || 0
  return qty * rate
})

const totalAvailableAtStage = computed(() => {
  return availableBatches.value.reduce((sum, b) => sum + b.remaining_weight_kg, 0)
})

const activeFilterCount = computed(() => {
  let count = 0
  if (filterStatus.value) count++
  if (filterStageId.value) count++
  if (filterDatePreset.value !== 'all') count++
  if (filterCustomerQ.value) count++
  return count
})

// --- Date preset logic ---
function computeDateRange(preset) {
  const now = new Date()
  const y = now.getFullYear()
  const m = now.getMonth()
  switch (preset) {
    case 'this_month':
      return { from: new Date(y, m, 1), to: new Date(y, m + 1, 0) }
    case 'prev_month':
      return { from: new Date(y, m - 1, 1), to: new Date(y, m, 0) }
    case 'this_quarter': {
      const qStart = Math.floor(m / 3) * 3
      return { from: new Date(y, qStart, 1), to: new Date(y, qStart + 3, 0) }
    }
    case 'prev_quarter': {
      const qStart = Math.floor(m / 3) * 3 - 3
      return { from: new Date(y, qStart, 1), to: new Date(y, qStart + 3, 0) }
    }
    case 'this_year':
      return { from: new Date(y, 0, 1), to: new Date(y, 11, 31) }
    default:
      return null
  }
}

function toDateString(d) {
  return d.toISOString().slice(0, 10)
}

function onDatePresetChange() {
  if (filterDatePreset.value === 'all') {
    filterDateFrom.value = ''
    filterDateTo.value = ''
  } else if (filterDatePreset.value !== 'custom') {
    const range = computeDateRange(filterDatePreset.value)
    if (range) {
      filterDateFrom.value = toDateString(range.from)
      filterDateTo.value = toDateString(range.to)
    }
  }
}

// --- Lifecycle ---
onMounted(() => {
  fetchSales()
  fetchSalableStages()
  fetchSuggestedCustomers()
  createModal = new Modal(createModalRef.value)
  newCustomerModal = new Modal(newCustomerModalRef.value)
  detailModal = new Modal(detailModalRef.value)
  document.addEventListener('click', handleClickOutside)
})

onBeforeUnmount(() => {
  createModal?.dispose()
  newCustomerModal?.dispose()
  detailModal?.dispose()
  document.removeEventListener('click', handleClickOutside)
})

function handleClickOutside(e) {
  // Close customer dropdown
  const wrap = document.querySelector('.customer-search-wrap')
  if (wrap && !wrap.contains(e.target)) {
    showCustomerDropdown.value = false
  }
  // Close filter sidebar on outside click
  const sidebar = document.querySelector('.filter-sidebar')
  const filterBtn = document.querySelector('.btn-filter')
  if (filterOpen.value && sidebar && !sidebar.contains(e.target) && filterBtn && !filterBtn.contains(e.target)) {
    filterOpen.value = false
  }
}

// --- Fetch data ---
async function fetchSales() {
  loading.value = true
  try {
    const params = {}
    if (filterStatus.value) params.status = filterStatus.value
    if (filterStageId.value) params.stage_id = filterStageId.value
    if (filterDateFrom.value) params.date_from = filterDateFrom.value + 'T00:00:00'
    if (filterDateTo.value) params.date_to = filterDateTo.value + 'T23:59:59'
    if (filterCustomerQ.value) params.customer_q = filterCustomerQ.value
    const { data } = await api.get('/sales/', { params })
    sales.value = data
  } catch (e) {
    console.error('Failed to fetch sales', e)
  } finally {
    loading.value = false
  }
}

async function fetchSalableStages() {
  try {
    const { data } = await api.get('/sales/stages')
    salableStages.value = data
  } catch (e) {
    console.error('Failed to fetch salable stages', e)
  }
}

async function fetchSuggestedCustomers() {
  try {
    const { data } = await api.get('/customers/suggested')
    suggestedCustomers.value = data
  } catch (e) {
    console.error('Failed to fetch suggested customers', e)
  }
}

async function fetchSalableBatches() {
  if (!form.value.stage_id) {
    availableBatches.value = []
    return
  }
  loadingBatches.value = true
  try {
    const { data } = await api.get('/sales/batches', { params: { stage_id: form.value.stage_id } })
    availableBatches.value = data
    selectedBatchIds.value = []
    computeAllocationPreview()
  } catch (e) {
    console.error('Failed to fetch batches', e)
  } finally {
    loadingBatches.value = false
  }
}

// --- Customer search ---
function onCustomerFocus() {
  showCustomerDropdown.value = true
  if (!customerQuery.value) {
    customerResults.value = []
  }
}

function onCustomerSearch() {
  clearTimeout(customerSearchTimeout)
  showCustomerDropdown.value = true
  if (customerQuery.value.length < 2) {
    customerResults.value = []
    return
  }
  customerSearchTimeout = setTimeout(async () => {
    searchingCustomers.value = true
    try {
      const { data } = await api.get('/customers/search', { params: { q: customerQuery.value } })
      customerResults.value = data
    } catch (e) {
      console.error('Customer search failed', e)
    } finally {
      searchingCustomers.value = false
    }
  }, 300)
}

const displayedCustomers = computed(() => {
  if (customerQuery.value.length >= 2) return customerResults.value
  return suggestedCustomers.value
})

function selectCustomer(c) {
  selectedCustomer.value = c
  form.value.customer_id = c.id
  customerQuery.value = ''
  customerResults.value = []
  showCustomerDropdown.value = false
}

function clearCustomer() {
  selectedCustomer.value = null
  form.value.customer_id = null
}

// --- New customer ---
function openNewCustomerModal() {
  newCustomerForm.value = { name: '', phone: '', address: '', notes: '' }
  newCustomerError.value = ''
  showCustomerDropdown.value = false
  newCustomerModal.show()
}

async function createCustomer() {
  if (!newCustomerForm.value.name || !newCustomerForm.value.phone) {
    newCustomerError.value = 'Name and phone are required'
    return
  }
  savingCustomer.value = true
  newCustomerError.value = ''
  try {
    const { data } = await api.post('/customers/', newCustomerForm.value)
    selectCustomer(data)
    newCustomerModal.hide()
    fetchSuggestedCustomers()
  } catch (e) {
    newCustomerError.value = e.response?.data?.detail || 'Failed to create customer'
  } finally {
    savingCustomer.value = false
  }
}

// --- Allocation preview ---
function computeAllocationPreview() {
  if (!form.value.quantity_sold || availableBatches.value.length === 0) {
    allocationPreview.value = []
    return
  }

  const qty = parseFloat(form.value.quantity_sold) || 0
  let remaining = qty
  const preview = []

  if (form.value.allocation_mode === 'FIFO') {
    for (const b of availableBatches.value) {
      if (remaining <= 0) break
      const alloc = Math.min(b.remaining_weight_kg, remaining)
      preview.push({ batch_code: b.batch_code, batch_id: b.id, quantity: alloc })
      remaining -= alloc
    }
  } else {
    for (const bid of selectedBatchIds.value) {
      if (remaining <= 0) break
      const b = availableBatches.value.find(x => x.id === bid)
      if (!b) continue
      const alloc = Math.min(b.remaining_weight_kg, remaining)
      preview.push({ batch_code: b.batch_code, batch_id: b.id, quantity: alloc })
      remaining -= alloc
    }
  }

  allocationPreview.value = preview
}

watch(() => form.value.quantity_sold, computeAllocationPreview)
watch(() => form.value.allocation_mode, computeAllocationPreview)
watch(() => selectedBatchIds.value, computeAllocationPreview, { deep: true })

function toggleBatchSelection(batchId) {
  const idx = selectedBatchIds.value.indexOf(batchId)
  if (idx >= 0) {
    selectedBatchIds.value.splice(idx, 1)
  } else {
    const qty = parseFloat(form.value.quantity_sold) || 0
    let covered = 0
    for (const bid of selectedBatchIds.value) {
      const b = availableBatches.value.find(x => x.id === bid)
      if (b) covered += b.remaining_weight_kg
    }
    if (covered >= qty) return
    selectedBatchIds.value.push(batchId)
  }
  computeAllocationPreview()
}

// --- Filter sidebar ---
function applyFilters() {
  filterOpen.value = false
  fetchSales()
}

function clearFilters() {
  filterStatus.value = null
  filterStageId.value = null
  filterDatePreset.value = 'all'
  filterDateFrom.value = ''
  filterDateTo.value = ''
  filterCustomerQ.value = ''
  fetchSales()
}

// --- Create sale ---
function openCreateModal() {
  form.value = {
    customer_id: null,
    stage_id: null,
    sale_date: new Date().toISOString().slice(0, 10),
    quantity_sold: '',
    selling_price_per_kg: '',
    allocation_mode: 'FIFO',
    manual_allocations: [],
    notes: '',
  }
  selectedCustomer.value = null
  customerQuery.value = ''
  customerResults.value = []
  showCustomerDropdown.value = false
  availableBatches.value = []
  selectedBatchIds.value = []
  allocationPreview.value = []
  formError.value = ''
  createModal.show()
}

async function submitSale() {
  formError.value = ''
  if (!form.value.customer_id) { formError.value = 'Select a customer'; return }
  if (!form.value.stage_id) { formError.value = 'Select a batch stage'; return }
  if (!form.value.quantity_sold || parseFloat(form.value.quantity_sold) <= 0) { formError.value = 'Enter a valid quantity'; return }
  if (!form.value.selling_price_per_kg || parseFloat(form.value.selling_price_per_kg) <= 0) { formError.value = 'Enter a valid rate'; return }

  const qty = parseFloat(form.value.quantity_sold)
  if (qty > totalAvailableAtStage.value) {
    formError.value = `Insufficient stock. Available: ${totalAvailableAtStage.value.toLocaleString('en-IN')} kg`
    return
  }

  if (form.value.allocation_mode === 'MANUAL' && selectedBatchIds.value.length === 0) {
    formError.value = 'Select at least one batch for manual allocation'
    return
  }

  saving.value = true
  try {
    const payload = {
      customer_id: form.value.customer_id,
      stage_id: form.value.stage_id,
      sale_date: form.value.sale_date + 'T00:00:00',
      quantity_sold: qty,
      selling_price: totalAmount.value,
      allocation_mode: form.value.allocation_mode,
      notes: form.value.notes || null,
    }
    if (form.value.allocation_mode === 'MANUAL') {
      payload.manual_allocations = selectedBatchIds.value.map(bid => ({ batch_id: bid }))
    }

    const endpoint = isAdmin ? '/sales/' : '/sales/request'
    await api.post(endpoint, payload)
    createModal.hide()
    fetchSales()
  } catch (e) {
    formError.value = e.response?.data?.detail || 'Failed to create sale'
  } finally {
    saving.value = false
  }
}

// --- Detail ---
async function openDetail(saleId) {
  loadingDetail.value = true
  showRejectInput.value = false
  showDeleteConfirm.value = false
  rejectReason.value = ''
  detailModal.show()
  try {
    const { data } = await api.get(`/sales/${saleId}`)
    detailSale.value = data
  } catch (e) {
    console.error('Failed to fetch sale detail', e)
  } finally {
    loadingDetail.value = false
  }
}

async function approveSale() {
  if (!detailSale.value) return
  approving.value = true
  try {
    await api.put(`/sales/${detailSale.value.id}/approve`)
    detailModal.hide()
    fetchSales()
  } catch (e) {
    console.error('Failed to approve', e)
  } finally {
    approving.value = false
  }
}

async function rejectSale() {
  if (!detailSale.value) return
  rejecting.value = true
  try {
    await api.put(`/sales/${detailSale.value.id}/reject`, { rejection_reason: rejectReason.value || null })
    detailModal.hide()
    fetchSales()
  } catch (e) {
    console.error('Failed to reject', e)
  } finally {
    rejecting.value = false
  }
}

async function deleteSale() {
  if (!detailSale.value) return
  deleting.value = true
  try {
    await api.delete(`/sales/${detailSale.value.id}`)
    detailModal.hide()
    fetchSales()
  } catch (e) {
    console.error('Failed to delete', e)
  } finally {
    deleting.value = false
    showDeleteConfirm.value = false
  }
}

// --- Helpers ---
function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
}
function formatCurrency(v) {
  return '\u20B9' + Number(v || 0).toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
}
function formatKg(v) {
  return Number(v || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
function statusClass(s) {
  return {
    'COMPLETED': 'status-completed',
    'PENDING': 'status-pending',
    'REJECTED': 'status-rejected',
  }[s] || ''
}

watch(() => form.value.stage_id, fetchSalableBatches)
</script>

<template>
  <div class="page-container">
    <!-- Header -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Sales</h1>
        <p class="page-subtitle">Track and manage product sales</p>
      </div>
      <div class="header-actions">
        <button class="btn-filter" @click="filterOpen = !filterOpen">
          <i class="bi bi-funnel"></i>
          <span>Filters</span>
          <span v-if="activeFilterCount" class="filter-count">{{ activeFilterCount }}</span>
        </button>
        <button class="btn-primary-action" @click="openCreateModal">
          <i class="bi bi-plus-lg"></i>
          {{ isAdmin ? 'New Sale' : 'Request Sale' }}
        </button>
      </div>
    </div>

    <!-- Table -->
    <div v-if="loading" class="content-panel">
      <div class="empty-state"><i class="bi bi-hourglass-split"></i><p>Loading...</p></div>
    </div>
    <div v-else-if="sales.length === 0" class="content-panel">
      <div class="empty-state"><i class="bi bi-cart-x"></i><p>No sales found</p></div>
    </div>
    <div v-else class="table-wrapper">
      <table class="sales-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Customer</th>
            <th>Stage</th>
            <th class="text-end">Qty (kg)</th>
            <th class="text-end">Rate/kg</th>
            <th class="text-end">Total</th>
            <th v-if="isAdmin" class="text-end">COGS</th>
            <th v-if="isAdmin" class="text-end">Profit</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in sales" :key="s.id" @click="openDetail(s.id)" class="clickable-row">
            <td>{{ formatDate(s.sale_date) }}</td>
            <td class="customer-cell">
              <span>{{ s.customer_name }}</span>
              <span class="customer-phone">Ph. No.: {{ s.customer_phone }}</span>
            </td>
            <td><span class="stage-badge">{{ s.stage_name }}</span></td>
            <td class="text-end">{{ formatKg(s.quantity_sold) }}</td>
            <td class="text-end">{{ formatCurrency(s.selling_price / s.quantity_sold) }}</td>
            <td class="text-end fw-semibold">{{ formatCurrency(s.selling_price) }}</td>
            <td v-if="isAdmin" class="text-end text-muted">{{ formatCurrency(s.cost_of_goods_sold) }}</td>
            <td v-if="isAdmin" class="text-end text-profit">{{ formatCurrency(s.profit) }}</td>
            <td><span :class="['status-badge', statusClass(s.status)]">{{ s.status }}</span></td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Filter Sidebar Overlay -->
    <Transition name="fade">
      <div v-if="filterOpen" class="filter-overlay" @click="filterOpen = false"></div>
    </Transition>
    <Transition name="slide-right">
      <aside v-if="filterOpen" class="filter-sidebar">
        <div class="filter-sidebar-header">
          <h5>Filters</h5>
          <button class="btn-close-filter" @click="filterOpen = false"><i class="bi bi-x-lg"></i></button>
        </div>

        <div class="filter-sidebar-count">
          <i class="bi bi-list-ul"></i>
          <span>{{ sales.length }} record{{ sales.length !== 1 ? 's' : '' }} found</span>
        </div>

        <div class="filter-sidebar-body">
          <!-- Status -->
          <div class="filter-group">
            <label class="filter-label">Status</label>
            <div class="status-chips">
              <button :class="['chip', { active: !filterStatus }]" @click="filterStatus = null">All</button>
              <button :class="['chip', { active: filterStatus === 'PENDING' }]" @click="filterStatus = 'PENDING'">Pending</button>
              <button :class="['chip', { active: filterStatus === 'COMPLETED' }]" @click="filterStatus = 'COMPLETED'">Completed</button>
              <button :class="['chip', { active: filterStatus === 'REJECTED' }]" @click="filterStatus = 'REJECTED'">Rejected</button>
            </div>
          </div>

          <!-- Date Range -->
          <div class="filter-group">
            <label class="filter-label">Date Range</label>
            <select v-model="filterDatePreset" class="form-select" @change="onDatePresetChange">
              <option value="all">All Time</option>
              <option value="this_month">This Month</option>
              <option value="prev_month">Previous Month</option>
              <option value="this_quarter">This Quarter</option>
              <option value="prev_quarter">Previous Quarter</option>
              <option value="this_year">This Year</option>
              <option value="custom">Custom</option>
            </select>
            <div v-if="filterDatePreset === 'custom'" class="custom-dates">
              <input type="date" v-model="filterDateFrom" class="form-control" />
              <span class="date-sep">to</span>
              <input type="date" v-model="filterDateTo" class="form-control" />
            </div>
          </div>

          <!-- Stage -->
          <div class="filter-group">
            <label class="filter-label">Batch Stage</label>
            <select v-model="filterStageId" class="form-select">
              <option :value="null">All Stages</option>
              <option v-for="s in salableStages" :key="s.id" :value="s.id">{{ s.name }}</option>
            </select>
          </div>

          <!-- Customer -->
          <div class="filter-group">
            <label class="filter-label">Customer</label>
            <input v-model="filterCustomerQ" type="text" class="form-control" placeholder="Search by name or phone..." />
          </div>
        </div>

        <div class="filter-sidebar-footer">
          <button class="btn-modal btn-modal-cancel" @click="clearFilters">Clear All</button>
          <button class="btn-modal btn-modal-confirm" @click="applyFilters">Apply Filters</button>
        </div>
      </aside>
    </Transition>

    <!-- Create Sale Modal -->
    <div class="modal fade" ref="createModalRef" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog modal-dialog-centered modal-lg">
        <div class="modal-content form-modal">
          <div class="modal-body">
            <div class="modal-icon icon-add"><i class="bi bi-cart-plus"></i></div>
            <h5 class="modal-title">{{ isAdmin ? 'New Sale' : 'Request Sale' }}</h5>
            <p v-if="formError" class="form-error">{{ formError }}</p>

            <form class="sale-form" @submit.prevent="submitSale">
              <!-- Customer -->
              <div class="form-group">
                <label class="form-label">Customer *</label>
                <div v-if="selectedCustomer" class="customer-chip">
                  <span>{{ selectedCustomer.name }} — Ph. No.: {{ selectedCustomer.phone }}</span>
                  <button type="button" class="chip-remove" @click="clearCustomer"><i class="bi bi-x"></i></button>
                </div>
                <div v-else class="customer-search-wrap">
                  <input
                    v-model="customerQuery"
                    type="text"
                    class="form-control"
                    placeholder="Search by name or phone..."
                    @input="onCustomerSearch"
                    @focus="onCustomerFocus"
                  />
                  <div v-if="showCustomerDropdown && (displayedCustomers.length || searchingCustomers || (customerQuery.length >= 2 && !searchingCustomers && customerResults.length === 0))" class="search-dropdown">
                    <div v-if="!customerQuery && suggestedCustomers.length" class="search-section-label">Suggested</div>
                    <div v-for="c in displayedCustomers" :key="c.id" class="search-item" @click="selectCustomer(c)">
                      <div class="search-item-info">
                        <span class="search-item-name">{{ c.name }}</span>
                        <span class="search-item-phone">Ph. No.: {{ c.phone }}</span>
                      </div>
                    </div>
                    <div v-if="searchingCustomers" class="search-item search-loading">
                      <i class="bi bi-hourglass-split"></i> Searching...
                    </div>
                    <div v-if="customerQuery.length >= 2 && !searchingCustomers && customerResults.length === 0" class="search-item search-empty">
                      No customers found.
                      <button type="button" class="btn-link-inline" @click="openNewCustomerModal">Create new</button>
                    </div>
                    <div class="search-item search-create" @click="openNewCustomerModal">
                      <i class="bi bi-plus-circle"></i> New Customer
                    </div>
                  </div>
                </div>
              </div>

              <!-- Date + Stage row -->
              <div class="form-row">
                <div class="form-group flex-1">
                  <label class="form-label">Sale Date *</label>
                  <input v-model="form.sale_date" type="date" class="form-control" />
                </div>
                <div class="form-group flex-1">
                  <label class="form-label">Batch Stage *</label>
                  <select v-model="form.stage_id" class="form-select">
                    <option :value="null" disabled>Select stage...</option>
                    <option v-for="s in salableStages" :key="s.id" :value="s.id">{{ s.name }}</option>
                  </select>
                </div>
              </div>

              <div v-if="form.stage_id" class="stock-info">
                Available: <strong>{{ formatKg(totalAvailableAtStage) }} kg</strong>
                <span v-if="loadingBatches"> (loading...)</span>
              </div>

              <!-- Allocation mode (above qty/rate) -->
              <div v-if="form.stage_id" class="form-group">
                <label class="form-label">Allocation Mode</label>
                <div class="toggle-group">
                  <button type="button" :class="['toggle-btn', { active: form.allocation_mode === 'FIFO' }]" @click="form.allocation_mode = 'FIFO'">FIFO (Auto)</button>
                  <button type="button" :class="['toggle-btn', { active: form.allocation_mode === 'MANUAL' }]" @click="form.allocation_mode = 'MANUAL'">Manual</button>
                </div>
              </div>

              <!-- Qty + Rate + Total row -->
              <div class="form-row">
                <div class="form-group flex-1">
                  <label class="form-label">Quantity (kg) *</label>
                  <input v-model="form.quantity_sold" type="number" step="0.01" min="0" class="form-control" placeholder="0.00" />
                </div>
                <div class="form-group flex-1">
                  <label class="form-label">Rate per kg *</label>
                  <input v-model="form.selling_price_per_kg" type="number" step="0.01" min="0" class="form-control" placeholder="0.00" />
                </div>
                <div class="form-group flex-1">
                  <label class="form-label">Total Amount</label>
                  <div class="form-value">{{ formatCurrency(totalAmount) }}</div>
                </div>
              </div>

              <!-- Allocation preview/selection (below qty/rate) -->
              <div v-if="form.stage_id && form.quantity_sold" class="form-group">
                <!-- Manual batch picker -->
                <div v-if="form.allocation_mode === 'MANUAL' && availableBatches.length" class="batch-picker">
                  <p class="picker-hint">Select batches in order of preference:</p>
                  <div v-for="b in availableBatches" :key="b.id"
                       :class="['batch-option', { selected: selectedBatchIds.includes(b.id), disabled: !selectedBatchIds.includes(b.id) && allocationPreview.reduce((s, p) => s + p.quantity, 0) >= parseFloat(form.quantity_sold || 0) }]"
                       @click="toggleBatchSelection(b.id)">
                    <span class="batch-code">{{ b.batch_code }}</span>
                    <span class="batch-qty">{{ formatKg(b.remaining_weight_kg) }} kg</span>
                    <span class="batch-cost">@ {{ formatCurrency(b.cost_per_kg) }}/kg</span>
                  </div>
                </div>

                <!-- Allocation preview -->
                <div v-if="allocationPreview.length" class="allocation-preview">
                  <p class="preview-label">Allocation Preview:</p>
                  <div v-for="a in allocationPreview" :key="a.batch_id" class="preview-item">
                    {{ formatKg(a.quantity) }} kg from <strong>{{ a.batch_code }}</strong>
                  </div>
                </div>
              </div>

              <!-- Notes (at the bottom) -->
              <div class="form-group">
                <label class="form-label">Notes</label>
                <textarea v-model="form.notes" class="form-control" rows="2" placeholder="Optional"></textarea>
              </div>
            </form>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn-modal btn-modal-cancel" data-bs-dismiss="modal">Cancel</button>
            <button type="button" class="btn-modal btn-modal-confirm" :disabled="saving" @click="submitSale">
              <i v-if="saving" class="bi bi-hourglass-split"></i>
              <span>{{ isAdmin ? 'Create Sale' : 'Submit Request' }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- New Customer Modal -->
    <div class="modal fade" ref="newCustomerModalRef" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content form-modal">
          <div class="modal-body">
            <div class="modal-icon icon-add"><i class="bi bi-person-plus"></i></div>
            <h5 class="modal-title">New Customer</h5>
            <p v-if="newCustomerError" class="form-error">{{ newCustomerError }}</p>

            <form class="sale-form" @submit.prevent="createCustomer">
              <div class="form-row">
                <div class="form-group flex-1">
                  <label class="form-label">Name *</label>
                  <input v-model="newCustomerForm.name" type="text" class="form-control" required />
                </div>
                <div class="form-group flex-1">
                  <label class="form-label">Phone *</label>
                  <input v-model="newCustomerForm.phone" type="text" class="form-control" required />
                </div>
              </div>
              <div class="form-group">
                <label class="form-label">Address</label>
                <input v-model="newCustomerForm.address" type="text" class="form-control" placeholder="Optional" />
              </div>
              <div class="form-group">
                <label class="form-label">Notes</label>
                <textarea v-model="newCustomerForm.notes" class="form-control" rows="2" placeholder="Optional"></textarea>
              </div>
            </form>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn-modal btn-modal-cancel" data-bs-dismiss="modal">Cancel</button>
            <button type="button" class="btn-modal btn-modal-confirm" :disabled="savingCustomer" @click="createCustomer">
              <i v-if="savingCustomer" class="bi bi-hourglass-split"></i>
              <span>Create Customer</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Detail Modal -->
    <div class="modal fade" ref="detailModalRef" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog modal-dialog-centered modal-lg">
        <div class="modal-content form-modal">
          <div class="modal-body" v-if="detailSale && !loadingDetail">
            <div class="modal-icon" :class="detailSale.status === 'COMPLETED' ? 'icon-add' : detailSale.status === 'REJECTED' ? 'icon-delete' : 'icon-edit'">
              <i class="bi" :class="detailSale.status === 'COMPLETED' ? 'bi-check-circle' : detailSale.status === 'REJECTED' ? 'bi-x-circle' : 'bi-hourglass-split'"></i>
            </div>
            <h5 class="modal-title">Sale Detail</h5>

            <div class="detail-content">
              <div class="detail-header">
                <span :class="['status-badge', statusClass(detailSale.status)]">{{ detailSale.status }}</span>
                <span class="detail-date">{{ formatDate(detailSale.sale_date) }}</span>
                <span class="detail-mode">{{ detailSale.allocation_mode }}</span>
                <span v-if="detailSale.invoice_number" class="detail-invoice">#{{ detailSale.invoice_number }}</span>
              </div>

              <div class="detail-section">
                <h6>Customer</h6>
                <p><strong>{{ detailSale.customer_name }}</strong> &middot; Ph. No.: {{ detailSale.customer_phone }}</p>
                <p v-if="detailSale.customer_address" class="dimmed">{{ detailSale.customer_address }}</p>
              </div>

              <div class="detail-section">
                <h6>Summary</h6>
                <div class="detail-grid">
                  <div><span class="detail-label">Stage</span><span>{{ detailSale.stage_name }}</span></div>
                  <div><span class="detail-label">Quantity</span><span>{{ formatKg(detailSale.quantity_sold) }} kg</span></div>
                  <div><span class="detail-label">Rate/kg</span><span>{{ formatCurrency(detailSale.unit_selling_price) }}</span></div>
                  <div><span class="detail-label">Total</span><span class="fw-semibold">{{ formatCurrency(detailSale.selling_price) }}</span></div>
                  <template v-if="isAdmin">
                    <div><span class="detail-label">COGS</span><span>{{ formatCurrency(detailSale.cost_of_goods_sold) }}</span></div>
                    <div><span class="detail-label">Profit</span><span class="text-profit">{{ formatCurrency(detailSale.profit) }}</span></div>
                    <div><span class="detail-label">Margin</span><span>{{ Number(detailSale.profit_margin).toFixed(1) }}%</span></div>
                  </template>
                </div>
              </div>

              <div class="detail-section">
                <h6>Batch Allocations</h6>
                <table class="alloc-table">
                  <thead>
                    <tr>
                      <th>Batch</th>
                      <th class="text-end">Qty (kg)</th>
                      <th v-if="isAdmin" class="text-end">Cost/kg</th>
                      <th v-if="isAdmin" class="text-end">Cost</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="a in detailSale.allocations" :key="a.id">
                      <td>{{ a.batch_code }}</td>
                      <td class="text-end">{{ formatKg(a.quantity_allocated) }}</td>
                      <td v-if="isAdmin" class="text-end">{{ formatCurrency(a.batch_cost_per_kg) }}</td>
                      <td v-if="isAdmin" class="text-end">{{ formatCurrency(a.cost_allocated) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div v-if="detailSale.notes" class="detail-section">
                <h6>Notes</h6>
                <p>{{ detailSale.notes }}</p>
              </div>
              <div v-if="detailSale.rejection_reason" class="detail-section">
                <h6>Rejection Reason</h6>
                <p class="text-danger">{{ detailSale.rejection_reason }}</p>
              </div>

              <div v-if="isAdmin && detailSale.status === 'PENDING'" class="admin-actions">
                <button class="btn-modal btn-modal-confirm" :disabled="approving" @click="approveSale">
                  <i class="bi bi-check-lg"></i> Approve
                </button>
                <div v-if="!showRejectInput">
                  <button class="btn-modal btn-modal-danger" @click="showRejectInput = true">
                    <i class="bi bi-x-lg"></i> Reject
                  </button>
                </div>
                <div v-else class="reject-form">
                  <input v-model="rejectReason" type="text" class="form-control" placeholder="Reason (optional)" />
                  <button class="btn-modal btn-modal-danger" :disabled="rejecting" @click="rejectSale">Confirm Reject</button>
                </div>
              </div>
            </div>
          </div>
          <div class="modal-body" v-else>
            <div class="empty-state"><i class="bi bi-hourglass-split"></i><p>Loading...</p></div>
          </div>
          <div class="modal-footer">
            <div v-if="isAdmin" class="delete-action">
              <button v-if="!showDeleteConfirm" class="btn-modal btn-modal-danger" @click="showDeleteConfirm = true">
                <i class="bi bi-trash"></i> Delete
              </button>
              <template v-else>
                <span class="delete-warning">This will reverse stock changes. Confirm?</span>
                <button class="btn-modal btn-modal-danger" :disabled="deleting" @click="deleteSale">
                  <i v-if="deleting" class="bi bi-hourglass-split"></i> Yes, Delete
                </button>
                <button class="btn-modal btn-modal-cancel" @click="showDeleteConfirm = false">Cancel</button>
              </template>
            </div>
            <button type="button" class="btn-modal btn-modal-cancel" data-bs-dismiss="modal">Close</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ── Page Layout ────────────────────────────── */
.page-container {
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
}

.header-actions {
    display: flex;
    gap: 8px;
    align-items: center;
}

.btn-primary-action {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 9px 18px;
    border-radius: 10px;
    border: none;
    background: var(--moss);
    color: var(--white);
    font-family: var(--font-body);
    font-weight: 600;
    font-size: 0.85rem;
    cursor: pointer;
    transition: all var(--transition-fast);
}

.btn-primary-action:hover {
    background: var(--moss-light);
    box-shadow: 0 4px 12px var(--moss-faded);
}

.btn-filter {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 9px 16px;
    border-radius: 10px;
    border: 1.5px solid var(--border);
    background: transparent;
    color: var(--text-secondary);
    font-family: var(--font-body);
    font-weight: 500;
    font-size: 0.85rem;
    cursor: pointer;
    transition: all var(--transition-fast);
}

.btn-filter:hover {
    border-color: var(--sage);
    color: var(--text-primary);
}

.filter-count {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 20px;
    height: 20px;
    padding: 0 5px;
    border-radius: 10px;
    background: var(--moss);
    color: var(--white);
    font-size: 0.7rem;
    font-weight: 700;
}

/* ── Filter Sidebar ─────────────────────────── */
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

.filter-sidebar-count {
    padding: 10px 20px;
    font-size: 0.8rem;
    color: var(--text-secondary);
    display: flex;
    align-items: center;
    gap: 6px;
    background: var(--parchment-deep);
    border-bottom: 1px solid var(--border-light);
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

/* ── Table ──────────────────────────────────── */
.table-wrapper {
    overflow-x: auto;
    background: var(--bg-card);
    border: 1px solid var(--border-light);
    border-radius: 14px;
    box-shadow: var(--shadow-sm);
}

.sales-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
}

.sales-table thead th {
    padding: 10px 12px;
    color: var(--text-secondary);
    font-weight: 600;
    font-size: 0.78rem;
    border-bottom: 2px solid var(--border-light);
    text-transform: uppercase;
    letter-spacing: 0.03em;
}

.sales-table tbody td {
    padding: 12px;
    border-bottom: 1px solid var(--border-light);
}

.clickable-row {
    cursor: pointer;
    transition: background var(--transition-fast);
}

.clickable-row:hover {
    background: rgba(138, 154, 123, 0.04);
}

.text-end { text-align: right; }
.text-muted { color: var(--text-secondary); }
.text-profit { color: #28a745; }
.text-danger { color: var(--sienna); }
.fw-semibold { font-weight: 600; }

.customer-cell {
    display: flex;
    flex-direction: column;
    gap: 2px;
}

.customer-cell span:first-child {
    font-weight: 500;
    color: var(--text-primary);
}

.customer-phone {
    font-size: 0.75rem;
    color: var(--text-secondary);
}

.stage-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    background: rgba(74, 103, 65, 0.1);
    color: var(--moss);
}

.status-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
}

.status-completed { background: rgba(74, 103, 65, 0.1); color: var(--moss); }
.status-pending { background: rgba(196, 163, 90, 0.15); color: #8a6f2a; }
.status-rejected { background: rgba(181, 105, 77, 0.1); color: var(--sienna); }

/* ── Content States ─────────────────────────── */
.content-panel {
    padding: 48px 24px;
    text-align: center;
    background: var(--bg-card);
    border: 1px solid var(--border-light);
    border-radius: 14px;
}

.empty-state { color: var(--text-secondary); }
.empty-state i { font-size: 2rem; display: block; margin-bottom: 8px; opacity: 0.4; }

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

.sale-form {
    text-align: left;
    margin-top: 20px;
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

.icon-add { background: rgba(74, 103, 65, 0.1); color: var(--moss); }
.icon-edit { background: rgba(196, 163, 90, 0.12); color: #8a6f2a; }
.icon-delete { background: rgba(181, 105, 77, 0.1); color: var(--sienna); }

.modal-title {
    font-family: var(--font-display);
    font-size: 1.15rem;
    margin: 0 0 8px;
    color: var(--text-primary);
}

.form-modal .modal-footer {
    border-top: 1px solid var(--border-light);
    padding: 12px 24px;
    display: flex;
    gap: 8px;
    justify-content: flex-end;
}

/* ── Form Elements ──────────────────────────── */
.form-group { margin-bottom: 16px; }

.form-label {
    font-size: 0.83rem;
    font-weight: 600;
    color: var(--text-primary);
    display: block;
    margin-bottom: 6px;
}

.form-row { display: flex; gap: 12px; }
.flex-1 { flex: 1; min-width: 0; }

.form-value {
    padding: 8px 12px;
    background: var(--parchment-deep);
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.85rem;
    color: var(--text-primary);
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

/* ── Buttons ────────────────────────────────── */
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
.btn-modal-danger { background: var(--sienna); color: var(--white); }
.btn-modal-danger:hover:not(:disabled) { background: var(--sienna-light); }

/* ── Customer Search Dropdown ───────────────── */
.customer-search-wrap {
    position: relative;
}

.search-dropdown {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    z-index: 20;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 0 0 10px 10px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
    max-height: 240px;
    overflow-y: auto;
    margin-top: -1px;
}

.search-section-label {
    padding: 6px 12px 4px;
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-secondary);
}

.search-item {
    padding: 10px 12px;
    cursor: pointer;
    font-size: 0.85rem;
    display: flex;
    align-items: center;
    gap: 8px;
    transition: background var(--transition-fast);
    border-bottom: 1px solid var(--border-light);
}

.search-item:last-child {
    border-bottom: none;
}

.search-item:hover {
    background: var(--parchment-deep);
}

.search-item-info {
    display: flex;
    flex-direction: column;
    gap: 1px;
}

.search-item-name {
    font-weight: 600;
    color: var(--text-primary);
    font-size: 0.85rem;
}

.search-item-phone {
    color: var(--text-secondary);
    font-size: 0.76rem;
}

.search-loading,
.search-empty {
    color: var(--text-secondary);
    font-size: 0.82rem;
    cursor: default;
}

.search-create {
    color: var(--moss);
    font-weight: 600;
    font-size: 0.82rem;
}

.search-create:hover {
    background: rgba(74, 103, 65, 0.06);
}

.customer-chip {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 14px;
    background: var(--parchment-deep);
    border: 1px solid var(--border-light);
    border-radius: 10px;
    font-size: 0.85rem;
    color: var(--text-primary);
}

.chip-remove {
    border: none;
    background: none;
    cursor: pointer;
    color: var(--text-secondary);
    font-size: 0.9rem;
    padding: 0;
    line-height: 1;
}

.chip-remove:hover { color: var(--sienna); }

.btn-link-inline {
    border: none;
    background: none;
    color: var(--moss);
    font-size: 0.78rem;
    cursor: pointer;
    text-decoration: underline;
    padding: 0;
}

.btn-link-inline:hover { color: var(--moss-light); }

/* ── Stock Info ─────────────────────────────── */
.stock-info {
    font-size: 0.8rem;
    color: var(--text-primary);
    margin-bottom: 12px;
    padding: 6px 12px;
    background: rgba(74, 103, 65, 0.06);
    border: 1px solid rgba(74, 103, 65, 0.12);
    border-radius: 8px;
}

/* ── Toggle ─────────────────────────────────── */
.toggle-group { display: flex; gap: 0; margin-bottom: 8px; }

.toggle-btn {
    padding: 6px 16px;
    border: 1.5px solid var(--border);
    background: var(--bg-card);
    font-size: 0.8rem;
    font-weight: 500;
    cursor: pointer;
    color: var(--text-secondary);
    transition: all var(--transition-fast);
}

.toggle-btn:first-child { border-radius: 8px 0 0 8px; }
.toggle-btn:last-child { border-radius: 0 8px 8px 0; }
.toggle-btn.active { background: var(--moss); color: var(--white); border-color: var(--moss); }

/* ── Batch Picker ───────────────────────────── */
.batch-picker { margin-top: 4px; }
.picker-hint { font-size: 0.78rem; color: var(--text-secondary); margin-bottom: 6px; }

.batch-option {
    display: flex;
    gap: 12px;
    align-items: center;
    padding: 8px 12px;
    border: 1.5px solid var(--border);
    border-radius: 8px;
    margin-bottom: 4px;
    cursor: pointer;
    font-size: 0.82rem;
    transition: all var(--transition-fast);
}

.batch-option:hover { background: var(--parchment-deep); border-color: var(--sage); }
.batch-option.selected { border-color: var(--moss); background: rgba(74, 103, 65, 0.06); }
.batch-option.disabled { opacity: 0.4; cursor: not-allowed; }
.batch-code { font-weight: 600; color: var(--text-primary); }
.batch-qty { color: var(--text-primary); }
.batch-cost { color: var(--text-secondary); font-size: 0.78rem; }

/* ── Allocation Preview ─────────────────────── */
.allocation-preview {
    margin-top: 8px;
    padding: 10px 12px;
    background: var(--parchment-deep);
    border: 1px solid var(--border-light);
    border-radius: 8px;
}

.preview-label { font-size: 0.78rem; font-weight: 600; color: var(--text-primary); margin-bottom: 4px; }
.preview-item { font-size: 0.82rem; color: var(--text-primary); padding: 2px 0; }

/* ── Detail Content ─────────────────────────── */
.detail-content { text-align: left; margin-top: 16px; }

.detail-header {
    display: flex;
    gap: 12px;
    align-items: center;
    margin-bottom: 16px;
    flex-wrap: wrap;
}

.detail-date { font-size: 0.85rem; color: var(--text-primary); }
.detail-mode { font-size: 0.72rem; padding: 2px 8px; background: var(--parchment-deep); border-radius: 10px; color: var(--text-secondary); }
.detail-invoice { font-size: 0.82rem; color: var(--text-secondary); }

.detail-section { margin-bottom: 16px; }
.detail-section h6 { font-size: 0.78rem; font-weight: 600; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px; }
.detail-section p { font-size: 0.85rem; color: var(--text-primary); margin: 0 0 4px; }
.dimmed { color: var(--text-secondary); }

.detail-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 8px; }
.detail-grid > div { display: flex; flex-direction: column; }
.detail-label { font-size: 0.72rem; color: var(--text-secondary); }

.alloc-table { width: 100%; border-collapse: collapse; font-size: 0.82rem; }
.alloc-table th { padding: 6px 8px; font-weight: 600; color: var(--text-secondary); border-bottom: 1px solid var(--border); font-size: 0.75rem; }
.alloc-table td { padding: 6px 8px; border-bottom: 1px solid var(--border-light); color: var(--text-primary); }

/* ── Admin Actions ──────────────────────────── */
.admin-actions {
    display: flex;
    gap: 12px;
    align-items: flex-start;
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid var(--border-light);
    flex-wrap: wrap;
}

.reject-form { display: flex; gap: 8px; align-items: center; }
.reject-form .form-control { min-width: 200px; }

.delete-action {
    display: flex;
    gap: 8px;
    align-items: center;
    margin-right: auto;
}
.delete-warning {
    font-size: 0.82rem;
    color: var(--sienna);
    font-weight: 500;
}

/* ── Transitions ────────────────────────────── */
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.slide-right-enter-active { transition: transform 0.25s ease-out; }
.slide-right-leave-active { transition: transform 0.2s ease-in; }
.slide-right-enter-from, .slide-right-leave-to { transform: translateX(100%); }

/* ── Responsive ─────────────────────────────── */
@media (max-width: 767.98px) {
    .page-header { margin-bottom: 18px; }
    .page-title { font-size: 1.35rem; }
    .form-row { flex-direction: column; gap: 0; }
    .detail-grid { grid-template-columns: repeat(2, 1fr); }
    .reject-form { flex-direction: column; width: 100%; }
    .reject-form .form-control { min-width: unset; width: 100%; }
}
</style>

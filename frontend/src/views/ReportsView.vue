<script setup>
import { ref, watch, onMounted } from 'vue'
import api from '@/utils/api'
import { useReportsStore } from '@/stores/reports'
import ReportsSales from '@/components/reports/ReportsSales.vue'
import ReportsExpenses from '@/components/reports/ReportsExpenses.vue'
import ReportsPlantations from '@/components/reports/ReportsPlantations.vue'
import ReportsTransformations from '@/components/reports/ReportsTransformations.vue'
import ReportsBatches from '@/components/reports/ReportsBatches.vue'
import ReportsPersonnel from '@/components/reports/ReportsPersonnel.vue'
import ReportsConsumables from '@/components/reports/ReportsConsumables.vue'

const reportsStore = useReportsStore()

// --- Tab definitions ---
const tabs = [
  { key: 'sales', label: 'Sales', icon: 'bi-receipt' },
  { key: 'expenses', label: 'Expenses', icon: 'bi-wallet2' },
  { key: 'plantations', label: 'Plantations', icon: 'bi-tree' },
  { key: 'transformations', label: 'Transformations', icon: 'bi-arrow-repeat' },
  { key: 'batches', label: 'Batches', icon: 'bi-box-seam' },
  { key: 'personnel', label: 'Personnel', icon: 'bi-people' },
  { key: 'consumables', label: 'Consumables', icon: 'bi-cart4' },
]

// --- Filter sidebar ---
const filterOpen = ref(false)

// --- Dropdown data ---
const stages = ref([])
const transformationTypes = ref([])
const expenseCategories = ref([])
const plantations = ref([])
const personnelList = ref([])
const consumableCategories = ref([])
const consumablesList = ref([])

// --- Tab data ---
const tabData = ref(null)

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
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function onDatePresetChange() {
  if (reportsStore.globalFilters.datePreset === 'all') {
    reportsStore.globalFilters.dateFrom = ''
    reportsStore.globalFilters.dateTo = ''
  } else if (reportsStore.globalFilters.datePreset !== 'custom') {
    const range = computeDateRange(reportsStore.globalFilters.datePreset)
    if (range) {
      reportsStore.globalFilters.dateFrom = toDateString(range.from)
      reportsStore.globalFilters.dateTo = toDateString(range.to)
    }
  }
}

// Initialize date range from preset on mount
function initDateRange() {
  if (reportsStore.globalFilters.datePreset !== 'all' && reportsStore.globalFilters.datePreset !== 'custom') {
    if (!reportsStore.globalFilters.dateFrom) {
      const range = computeDateRange(reportsStore.globalFilters.datePreset)
      if (range) {
        reportsStore.globalFilters.dateFrom = toDateString(range.from)
        reportsStore.globalFilters.dateTo = toDateString(range.to)
      }
    }
  }
}

// --- Switch tab ---
function switchTab(key) {
  reportsStore.activeTab = key
}

// --- Apply filters ---
async function applyFilters() {
  filterOpen.value = false
  await loadTabData()
}

// --- Clear filters ---
async function clearFilters() {
  reportsStore.globalFilters.datePreset = 'all'
  reportsStore.globalFilters.dateFrom = ''
  reportsStore.globalFilters.dateTo = ''
  const tab = reportsStore.activeTab
  const tf = reportsStore.tabFilters[tab]
  if (tf) {
    for (const key of Object.keys(tf)) {
      tf[key] = key === 'customer_q' ? '' : null
    }
  }
  filterOpen.value = false
  await loadTabData()
}

// --- Load data for current tab ---
async function loadTabData() {
  tabData.value = null  // Clear stale data before async fetch
  tabData.value = await reportsStore.fetchTab(reportsStore.activeTab)
}

// --- Fetch dropdown options ---
async function fetchDropdownData() {
  try {
    const [stagesRes, typesRes, categoriesRes, plantationsRes, personnelRes, consumableCatsRes, consumablesRes] = await Promise.all([
      api.get('/batches/stages'),
      api.get('/transformation-types/'),
      api.get('/settings/expense-categories'),
      api.get('/plantations/'),
      api.get('/personnel/'),
      api.get('/consumable-categories/'),
      api.get('/consumables/'),
    ])
    stages.value = stagesRes.data
    transformationTypes.value = typesRes.data
    expenseCategories.value = categoriesRes.data
    plantations.value = plantationsRes.data
    personnelList.value = personnelRes.data
    consumableCategories.value = consumableCatsRes.data
    consumablesList.value = consumablesRes.data
  } catch (e) {
    console.error('Failed to load dropdown data', e)
  }
}

// --- Lifecycle ---
onMounted(() => {
  initDateRange()
  fetchDropdownData()
  loadTabData()
})

watch(() => reportsStore.activeTab, () => {
  loadTabData()
})
</script>

<template>
  <div class="page-container">
    <!-- Header -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Reports</h1>
        <p class="page-subtitle">Analytics and insights across all operations</p>
      </div>
    </div>

    <!-- Tabs Bar -->
    <div class="tabs-bar">
      <div class="tabs">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          :class="['tab-btn', { active: reportsStore.activeTab === tab.key }]"
          @click="switchTab(tab.key)"
        >
          <i :class="['bi', tab.icon]"></i> {{ tab.label }}
        </button>
      </div>
      <div class="tab-actions">
        <button class="btn-filter" @click="filterOpen = !filterOpen">
          <i class="bi bi-funnel"></i>
          <span>Filters</span>
          <span v-if="reportsStore.activeFilterCount" class="filter-count">{{ reportsStore.activeFilterCount }}</span>
        </button>
      </div>
    </div>

    <!-- Tab Content -->
    <div class="tab-content">
      <div v-if="reportsStore.loading[reportsStore.activeTab]" class="content-panel">
        <div class="empty-state">
          <i class="bi bi-hourglass-split"></i>
          <p>Loading analytics...</p>
        </div>
      </div>
      <template v-else-if="tabData">
        <ReportsSales v-if="reportsStore.activeTab === 'sales'" :data="tabData" />
        <ReportsExpenses v-else-if="reportsStore.activeTab === 'expenses'" :data="tabData" />
        <ReportsPlantations v-else-if="reportsStore.activeTab === 'plantations'" :data="tabData" />
        <ReportsTransformations v-else-if="reportsStore.activeTab === 'transformations'" :data="tabData" />
        <ReportsBatches v-else-if="reportsStore.activeTab === 'batches'" :data="tabData" />
        <ReportsPersonnel v-else-if="reportsStore.activeTab === 'personnel'" :data="tabData" />
        <ReportsConsumables v-else-if="reportsStore.activeTab === 'consumables'" :data="tabData" />
      </template>
      <div v-else class="content-panel">
        <div class="empty-state">
          <i class="bi bi-bar-chart"></i>
          <p>No analytics data available</p>
        </div>
      </div>
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

        <div class="filter-sidebar-body">
          <!-- Global: Date Range -->
          <div class="filter-group">
            <label class="filter-label">Date Range</label>
            <select v-model="reportsStore.globalFilters.datePreset" class="form-select" @change="onDatePresetChange">
              <option value="all">All Time</option>
              <option value="this_month">This Month</option>
              <option value="prev_month">Previous Month</option>
              <option value="this_quarter">This Quarter</option>
              <option value="prev_quarter">Previous Quarter</option>
              <option value="this_year">This Year</option>
              <option value="custom">Custom</option>
            </select>
            <div v-if="reportsStore.globalFilters.datePreset === 'custom'" class="custom-dates">
              <input type="date" v-model="reportsStore.globalFilters.dateFrom" class="form-control" />
              <span class="date-sep">to</span>
              <input type="date" v-model="reportsStore.globalFilters.dateTo" class="form-control" />
            </div>
          </div>

          <!-- Tab-specific: Sales -->
          <template v-if="reportsStore.activeTab === 'sales'">
            <div class="filter-group">
              <label class="filter-label">Status</label>
              <div class="status-chips">
                <button :class="['chip', { active: !reportsStore.tabFilters.sales.status }]" @click="reportsStore.tabFilters.sales.status = null">All</button>
                <button :class="['chip', { active: reportsStore.tabFilters.sales.status === 'PENDING' }]" @click="reportsStore.tabFilters.sales.status = 'PENDING'">Pending</button>
                <button :class="['chip', { active: reportsStore.tabFilters.sales.status === 'COMPLETED' }]" @click="reportsStore.tabFilters.sales.status = 'COMPLETED'">Completed</button>
                <button :class="['chip', { active: reportsStore.tabFilters.sales.status === 'REJECTED' }]" @click="reportsStore.tabFilters.sales.status = 'REJECTED'">Rejected</button>
              </div>
            </div>
            <div class="filter-group">
              <label class="filter-label">Batch Stage</label>
              <select v-model="reportsStore.tabFilters.sales.stage_id" class="form-select">
                <option :value="null">All Stages</option>
                <option v-for="s in stages" :key="s.id" :value="s.id">{{ s.name }}</option>
              </select>
            </div>
            <div class="filter-group">
              <label class="filter-label">Customer</label>
              <input v-model="reportsStore.tabFilters.sales.customer_q" type="text" class="form-control" placeholder="Search by name or phone..." />
            </div>
          </template>

          <!-- Tab-specific: Expenses -->
          <template v-if="reportsStore.activeTab === 'expenses'">
            <div class="filter-group">
              <label class="filter-label">Category</label>
              <select v-model="reportsStore.tabFilters.expenses.category_id" class="form-select">
                <option :value="null">All Categories</option>
                <option v-for="c in expenseCategories" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select>
            </div>
            <div class="filter-group">
              <label class="filter-label">Plantation</label>
              <select v-model="reportsStore.tabFilters.expenses.plantation_id" class="form-select">
                <option :value="null">All Plantations</option>
                <option v-for="p in plantations" :key="p.id" :value="p.id">{{ p.name }}</option>
              </select>
            </div>
          </template>

          <!-- Tab-specific: Plantations -->
          <template v-if="reportsStore.activeTab === 'plantations'">
            <div class="filter-group">
              <label class="filter-label">Plantation</label>
              <select v-model="reportsStore.tabFilters.plantations.plantation_id" class="form-select">
                <option :value="null">All Plantations</option>
                <option v-for="p in plantations" :key="p.id" :value="p.id">{{ p.name }}</option>
              </select>
            </div>
            <div class="filter-group">
              <label class="filter-label">Status</label>
              <div class="status-chips">
                <button :class="['chip', { active: reportsStore.tabFilters.plantations.is_active === null }]" @click="reportsStore.tabFilters.plantations.is_active = null">All</button>
                <button :class="['chip', { active: reportsStore.tabFilters.plantations.is_active === true }]" @click="reportsStore.tabFilters.plantations.is_active = true">Active</button>
                <button :class="['chip', { active: reportsStore.tabFilters.plantations.is_active === false }]" @click="reportsStore.tabFilters.plantations.is_active = false">Inactive</button>
              </div>
            </div>
          </template>

          <!-- Tab-specific: Transformations -->
          <template v-if="reportsStore.activeTab === 'transformations'">
            <div class="filter-group">
              <label class="filter-label">Type</label>
              <select v-model="reportsStore.tabFilters.transformations.type_id" class="form-select">
                <option :value="null">All Types</option>
                <option v-for="t in transformationTypes" :key="t.id" :value="t.id">{{ t.name }}</option>
              </select>
            </div>
            <div class="filter-group">
              <label class="filter-label">Status</label>
              <div class="status-chips">
                <button :class="['chip', { active: !reportsStore.tabFilters.transformations.status }]" @click="reportsStore.tabFilters.transformations.status = null">All</button>
                <button :class="['chip', { active: reportsStore.tabFilters.transformations.status === 'ACTIVE' }]" @click="reportsStore.tabFilters.transformations.status = 'ACTIVE'">Active</button>
                <button :class="['chip', { active: reportsStore.tabFilters.transformations.status === 'COMPLETED' }]" @click="reportsStore.tabFilters.transformations.status = 'COMPLETED'">Completed</button>
              </div>
            </div>
          </template>

          <!-- Tab-specific: Batches -->
          <template v-if="reportsStore.activeTab === 'batches'">
            <div class="filter-group">
              <label class="filter-label">Stage</label>
              <select v-model="reportsStore.tabFilters.batches.stage_id" class="form-select">
                <option :value="null">All Stages</option>
                <option v-for="s in stages" :key="s.id" :value="s.id">{{ s.name }}</option>
              </select>
            </div>
            <div class="filter-group">
              <label class="filter-label">Plantation</label>
              <select v-model="reportsStore.tabFilters.batches.plantation_id" class="form-select">
                <option :value="null">All Plantations</option>
                <option v-for="p in plantations" :key="p.id" :value="p.id">{{ p.name }}</option>
              </select>
            </div>
            <div class="filter-group">
              <label class="filter-label">Depletion Status</label>
              <div class="status-chips">
                <button :class="['chip', { active: reportsStore.tabFilters.batches.is_depleted === null }]" @click="reportsStore.tabFilters.batches.is_depleted = null">All</button>
                <button :class="['chip', { active: reportsStore.tabFilters.batches.is_depleted === false }]" @click="reportsStore.tabFilters.batches.is_depleted = false">Active</button>
                <button :class="['chip', { active: reportsStore.tabFilters.batches.is_depleted === true }]" @click="reportsStore.tabFilters.batches.is_depleted = true">Depleted</button>
              </div>
            </div>
          </template>

          <!-- Tab-specific: Personnel -->
          <template v-if="reportsStore.activeTab === 'personnel'">
            <div class="filter-group">
              <label class="filter-label">Personnel</label>
              <select v-model="reportsStore.tabFilters.personnel.personnel_id" class="form-select">
                <option :value="null">All Personnel</option>
                <option v-for="p in personnelList" :key="p.id" :value="p.id">{{ p.name }}</option>
              </select>
            </div>
            <div class="filter-group">
              <label class="filter-label">Transformation Type</label>
              <select v-model="reportsStore.tabFilters.personnel.type_id" class="form-select">
                <option :value="null">All Types</option>
                <option v-for="t in transformationTypes" :key="t.id" :value="t.id">{{ t.name }}</option>
              </select>
            </div>
          </template>

          <!-- Tab-specific: Consumables -->
          <template v-if="reportsStore.activeTab === 'consumables'">
            <div class="filter-group">
              <label class="filter-label">Category</label>
              <select v-model="reportsStore.tabFilters.consumables.category_id" class="form-select">
                <option :value="null">All Categories</option>
                <option v-for="c in consumableCategories" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select>
            </div>
            <div class="filter-group">
              <label class="filter-label">Consumable</label>
              <select v-model="reportsStore.tabFilters.consumables.consumable_id" class="form-select">
                <option :value="null">All Consumables</option>
                <option v-for="c in consumablesList" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select>
            </div>
          </template>
        </div>

        <div class="filter-sidebar-footer">
          <button class="btn-modal btn-modal-cancel" @click="clearFilters">Clear All</button>
          <button class="btn-modal btn-modal-confirm" @click="applyFilters">Apply Filters</button>
        </div>
      </aside>
    </Transition>
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

/* ── Tabs ──────────────────────────────────── */
.tabs-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 20px;
    gap: 12px;
    flex-wrap: wrap;
}

.tabs {
    display: flex;
    gap: 4px;
    background: var(--parchment-deep);
    padding: 4px;
    border-radius: 10px;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: none;
}

.tabs::-webkit-scrollbar { display: none; }

.tab-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 18px;
    border-radius: 8px;
    border: none;
    background: transparent;
    color: var(--text-secondary);
    font-family: var(--font-body);
    font-weight: 500;
    font-size: 0.85rem;
    cursor: pointer;
    transition: all var(--transition-fast);
    white-space: nowrap;
}

.tab-btn.active {
    background: var(--bg-card);
    color: var(--text-primary);
    font-weight: 600;
    box-shadow: var(--shadow-sm);
}

.tab-actions {
    display: flex;
    gap: 8px;
    align-items: center;
}

/* ── Filter Button ─────────────────────────── */
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

    .tabs-bar {
        flex-direction: column;
        align-items: stretch;
    }

    .tabs {
        max-width: 100%;
    }

    .tab-actions {
        justify-content: flex-end;
    }
}
</style>

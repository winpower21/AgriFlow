import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import api from '@/utils/api'

// Tab → API endpoint mapping
const TAB_ENDPOINTS = {
  sales: '/reports/sales/analytics',
  expenses: '/reports/expenses/analytics',
  plantations: '/reports/plantations/analytics',
  transformations: '/reports/transformations/analytics',
  batches: '/reports/batches/analytics',
  personnel: '/reports/personnel/analytics',
  consumables: '/reports/consumables/analytics',
}

// Which domains get invalidated when a mutation happens on a domain
const CROSS_INVALIDATION = {
  sales: ['sales', 'batches'],
  batches: ['batches', 'transformations'],
  transformations: ['transformations', 'batches', 'consumables', 'personnel'],
  expenses: ['expenses'],
  plantations: ['plantations'],
  personnel: ['personnel'],
  consumables: ['consumables', 'transformations'],
}

export const useReportsStore = defineStore('reports', () => {
  const activeTab = ref('sales')

  // Global filters (date range)
  const globalFilters = ref({
    datePreset: 'all',
    dateFrom: '',
    dateTo: '',
  })

  // Per-tab specific filters
  const tabFilters = ref({
    sales: { stage_id: null, customer_q: '', status: null },
    expenses: { category_id: null, plantation_id: null },
    plantations: { plantation_id: null, is_active: null },
    transformations: { type_id: null, status: null },
    batches: { stage_id: null, plantation_id: null, is_depleted: null },
    personnel: { personnel_id: null, type_id: null },
    consumables: { category_id: null, consumable_id: null },
  })

  // Cache: { [tab]: { filterHash: string, data: any } }
  const cache = ref({})
  const loading = ref({})

  function buildParams(tab) {
    const params = {}
    // Global date filters
    if (globalFilters.value.dateFrom) params.date_from = globalFilters.value.dateFrom + 'T00:00:00'
    if (globalFilters.value.dateTo) params.date_to = globalFilters.value.dateTo + 'T23:59:59'
    // Tab-specific filters
    const tf = tabFilters.value[tab] || {}
    for (const [key, val] of Object.entries(tf)) {
      if (val !== null && val !== '' && val !== undefined) params[key] = val
    }
    return params
  }

  function filterHash(tab) {
    return JSON.stringify(buildParams(tab))
  }

  function getCachedData(tab) {
    const entry = cache.value[tab]
    if (entry && entry.filterHash === filterHash(tab)) return entry.data
    return null
  }

  async function fetchTab(tab) {
    // Check cache
    const cached = getCachedData(tab)
    if (cached) return cached

    loading.value = { ...loading.value, [tab]: true }
    try {
      const params = buildParams(tab)
      const endpoint = TAB_ENDPOINTS[tab]
      const { data } = await api.get(endpoint, { params })
      cache.value = { ...cache.value, [tab]: { filterHash: filterHash(tab), data } }
      return data
    } catch (e) {
      console.error(`Failed to fetch ${tab} analytics`, e)
      return null
    } finally {
      loading.value = { ...loading.value, [tab]: false }
    }
  }

  function invalidate(domain) {
    // Clear cache for the domain and any cross-invalidated domains
    const domains = CROSS_INVALIDATION[domain] || [domain]
    const newCache = { ...cache.value }
    for (const d of domains) {
      delete newCache[d]
    }
    cache.value = newCache
  }

  function clearAllCache() {
    cache.value = {}
  }

  const activeFilterCount = computed(() => {
    let count = 0
    if (globalFilters.value.datePreset !== 'all') count++
    const tf = tabFilters.value[activeTab.value] || {}
    for (const val of Object.values(tf)) {
      if (val !== null && val !== '' && val !== undefined) count++
    }
    return count
  })

  return {
    activeTab,
    globalFilters,
    tabFilters,
    cache,
    loading,
    activeFilterCount,
    buildParams,
    getCachedData,
    fetchTab,
    invalidate,
    clearAllCache,
  }
})

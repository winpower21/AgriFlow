import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import api from '../utils/api'

export const useSalesAnalyticsStore = defineStore('salesAnalytics', () => {
  const data = ref(null)
  const filters = ref({})
  const lastFetchedAt = ref(null)
  const loading = ref(false)

  const hasCachedData = computed(() => data.value !== null)

  function filtersMatch(newFilters) {
    return JSON.stringify(filters.value) === JSON.stringify(newFilters)
  }

  async function fetchAnalytics(newFilters = {}) {
    // Skip if cached data exists and filters match
    if (hasCachedData.value && filtersMatch(newFilters)) {
      return data.value
    }

    loading.value = true
    try {
      const params = {}
      if (newFilters.date_from) params.date_from = newFilters.date_from
      if (newFilters.date_to) params.date_to = newFilters.date_to
      if (newFilters.stage_id) params.stage_id = newFilters.stage_id
      if (newFilters.customer_q) params.customer_q = newFilters.customer_q
      if (newFilters.status) params.status = newFilters.status

      const res = await api.get('/sales/analytics', { params })
      data.value = res.data
      filters.value = { ...newFilters }
      lastFetchedAt.value = Date.now()
      return res.data
    } catch (e) {
      console.error('Failed to fetch analytics', e)
      return null
    } finally {
      loading.value = false
    }
  }

  function invalidateCache() {
    data.value = null
    lastFetchedAt.value = null
  }

  return {
    data,
    filters,
    lastFetchedAt,
    loading,
    hasCachedData,
    fetchAnalytics,
    invalidateCache,
  }
})

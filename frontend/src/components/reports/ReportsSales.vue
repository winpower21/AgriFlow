<script setup>
import SalesDashboard from '@/components/SalesDashboard.vue'
import { useAuthStore } from '@/stores/auth'

const props = defineProps({
  data: { type: Object, required: true }
})

const auth = useAuthStore()
const isAdmin = auth.userRoles?.includes('admin')

function formatCurrency(v) {
  return '\u20B9' + Number(v || 0).toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
}
function formatKg(v) {
  return Number(v || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
function formatPct(v) {
  return Number(v || 0).toFixed(1) + '%'
}
</script>

<template>
  <div class="reports-sales">
    <!-- Embedded Sales Dashboard -->
    <SalesDashboard
      v-if="data.sales_analytics"
      :data="data.sales_analytics"
      :is-admin="isAdmin"
    />

    <!-- Lease Cost Impact Panel -->
    <div v-if="isAdmin && data.lease_cost_impact && data.lease_cost_impact.length" class="lease-panel">
      <h6 class="panel-title">Lease Cost Impact on Sales</h6>

      <div class="table-responsive">
        <table class="lease-table">
          <thead>
            <tr>
              <th>Plantation</th>
              <th class="text-end">Lease Cost</th>
              <th class="text-end">Harvest (kg)</th>
              <th class="text-end">Cost/kg</th>
              <th class="text-end">Impact on Sold Goods</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in data.lease_cost_impact" :key="row.plantation_id">
              <td>{{ row.plantation_name }}</td>
              <td class="text-end">{{ formatCurrency(row.lease_cost) }}</td>
              <td class="text-end">{{ formatKg(row.total_harvest_kg) }}</td>
              <td class="text-end">{{ formatCurrency(row.lease_cost_per_kg) }}</td>
              <td class="text-end">{{ formatCurrency(row.impact_on_sold_goods) }}</td>
            </tr>
          </tbody>
          <tfoot>
            <tr class="summary-row">
              <td colspan="4" class="text-end"><strong>Total Lease Impact</strong></td>
              <td class="text-end"><strong>{{ formatCurrency(data.total_lease_impact) }}</strong></td>
            </tr>
            <tr class="summary-row">
              <td colspan="4" class="text-end"><strong>Lease-Adjusted Profit</strong></td>
              <td class="text-end"><strong class="profit-value">{{ formatCurrency(data.lease_adjusted_profit) }}</strong></td>
            </tr>
            <tr class="summary-row">
              <td colspan="4" class="text-end"><strong>Lease-Adjusted Margin</strong></td>
              <td class="text-end"><strong class="profit-value">{{ formatPct(data.lease_adjusted_margin_pct) }}</strong></td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  </div>
</template>

<style scoped>
.reports-sales {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.lease-panel {
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: 14px;
  padding: 18px;
  box-shadow: var(--shadow-sm);
}

.panel-title {
  font-family: var(--font-display);
  font-size: 0.95rem;
  margin: 0 0 14px;
  color: var(--text-primary);
}

.table-responsive {
  overflow-x: auto;
}

.lease-table {
  width: 100%;
  border-collapse: collapse;
  font-family: var(--font-body);
  font-size: 0.85rem;
}

.lease-table th {
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  font-size: 0.72rem;
  letter-spacing: 0.03em;
  padding: 8px 12px;
  border-bottom: 2px solid var(--border-light);
}

.lease-table td {
  padding: 8px 12px;
  color: var(--text-primary);
  border-bottom: 1px solid var(--border-light);
}

.lease-table tfoot td {
  border-bottom: none;
  padding-top: 10px;
}

.summary-row td {
  background: var(--bg-subtle, transparent);
}

.text-end {
  text-align: right;
}

.profit-value {
  color: #28a745;
}

@media (max-width: 767.98px) {
  .lease-table {
    font-size: 0.78rem;
  }

  .lease-table th,
  .lease-table td {
    padding: 6px 8px;
  }
}
</style>

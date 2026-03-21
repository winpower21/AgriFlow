<script setup>
import { computed, ref } from 'vue'
import { Bar, Chart } from 'vue-chartjs'
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement,
  PointElement, LineElement, Title, Tooltip, Legend, Filler
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, Title, Tooltip, Legend, Filler)

const props = defineProps({
  data: { type: Object, required: true }
})

const COLORS = {
  moss: '#4A6741', sage: '#8A9A7B', sienna: '#B5694D', harvest: '#C4A35A', mossLight: '#5E7D54',
  mossAlpha: 'rgba(74, 103, 65, 0.6)', sageAlpha: 'rgba(138, 154, 123, 0.6)',
  siennaAlpha: 'rgba(181, 105, 77, 0.6)', harvestAlpha: 'rgba(196, 163, 90, 0.6)',
  mossLightAlpha: 'rgba(94, 125, 84, 0.6)',
}

function formatCurrency(v) { return '\u20B9' + Number(v || 0).toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 }) }
function formatKg(v) { return Number(v || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }
function formatPeriod(p) {
  if (!p) return ''
  if (p.length === 10) { const d = new Date(p); return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short' }) }
  const [y, m] = p.split('-'); const d = new Date(parseInt(y), parseInt(m) - 1); return d.toLocaleDateString('en-IN', { month: 'short', year: '2-digit' })
}

/* ── Sorting ── */
const sortKey = ref('cost_per_kg')
const sortAsc = ref(true)

function toggleSort(key) {
  if (sortKey.value === key) {
    sortAsc.value = !sortAsc.value
  } else {
    sortKey.value = key
    sortAsc.value = true
  }
}

function sortIcon(key) {
  if (sortKey.value !== key) return 'bi-chevron-expand'
  return sortAsc.value ? 'bi-chevron-up' : 'bi-chevron-down'
}

const sortedRanking = computed(() => {
  const list = [...(props.data?.efficiency_ranking || [])]
  const key = sortKey.value
  const dir = sortAsc.value ? 1 : -1
  list.sort((a, b) => {
    const av = a[key] ?? 0
    const bv = b[key] ?? 0
    if (typeof av === 'string') return av.localeCompare(bv) * dir
    return (av - bv) * dir
  })
  return list
})

const lowestCostPerKg = computed(() => {
  const ranking = props.data?.efficiency_ranking || []
  if (!ranking.length) return null
  return Math.min(...ranking.map(r => r.cost_per_kg ?? Infinity))
})

/* ── Trend Chart ── */
const trendChartData = computed(() => {
  const trend = props.data?.payment_output_trend || []
  return {
    labels: trend.map(t => formatPeriod(t.period)),
    datasets: [
      {
        label: 'Total Wages',
        data: trend.map(t => t.total_wages),
        backgroundColor: COLORS.mossAlpha,
        borderColor: COLORS.moss,
        borderWidth: 1,
        type: 'bar',
        yAxisID: 'y',
        order: 2,
      },
      {
        label: 'Cost / kg',
        data: trend.map(t => t.cost_per_kg),
        borderColor: COLORS.sienna,
        backgroundColor: COLORS.siennaAlpha,
        borderWidth: 2,
        pointRadius: 3,
        tension: 0.3,
        fill: false,
        type: 'line',
        yAxisID: 'y1',
        order: 1,
      }
    ]
  }
})

const trendOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    tooltip: {
      callbacks: {
        label(ctx) {
          if (ctx.dataset.yAxisID === 'y1') return ctx.dataset.label + ': ' + formatCurrency(ctx.parsed.y) + '/kg'
          return ctx.dataset.label + ': ' + formatCurrency(ctx.parsed.y)
        }
      }
    }
  },
  scales: {
    y: { type: 'linear', position: 'left', ticks: { callback: (v) => formatCurrency(v) } },
    y1: { type: 'linear', position: 'right', grid: { drawOnChartArea: false }, ticks: { callback: (v) => formatCurrency(v) + '/kg' } },
    x: { ticks: { maxRotation: 45 } }
  }
}
</script>

<template>
  <div class="reports-personnel">
    <!-- KPI Cards -->
    <div class="kpi-grid" v-if="data?.kpis">
      <div class="kpi-card">
        <div class="kpi-label">Total Wages Paid</div>
        <div class="kpi-value">{{ formatCurrency(data.kpis.total_wages_paid) }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Avg Wage / Transformation</div>
        <div class="kpi-value">{{ formatCurrency(data.kpis.avg_wage_per_transformation) }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Total Output</div>
        <div class="kpi-value">{{ formatKg(data.kpis.total_output_kg) }} kg</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Active Personnel</div>
        <div class="kpi-value">{{ data.kpis.active_personnel_count }}</div>
      </div>
    </div>

    <!-- Efficiency Ranking Table -->
    <div class="chart-card" v-if="sortedRanking.length">
      <h6 class="chart-title">Efficiency Ranking</h6>
      <div class="table-responsive">
        <table class="ranking-table">
          <thead>
            <tr>
              <th>#</th>
              <th class="sortable" @click="toggleSort('personnel_name')">
                Personnel Name <i class="bi" :class="sortIcon('personnel_name')"></i>
              </th>
              <th class="text-end sortable" @click="toggleSort('total_wages')">
                Total Wages <i class="bi" :class="sortIcon('total_wages')"></i>
              </th>
              <th class="text-end sortable" @click="toggleSort('total_output_kg')">
                Total Output (kg) <i class="bi" :class="sortIcon('total_output_kg')"></i>
              </th>
              <th class="text-end sortable" @click="toggleSort('cost_per_kg')">
                Cost/kg <i class="bi" :class="sortIcon('cost_per_kg')"></i>
              </th>
              <th class="text-end sortable" @click="toggleSort('transformation_count')">
                Transformations <i class="bi" :class="sortIcon('transformation_count')"></i>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, idx) in sortedRanking" :key="row.personnel_id">
              <td>{{ idx + 1 }}</td>
              <td>{{ row.personnel_name }}</td>
              <td class="text-end">{{ formatCurrency(row.total_wages) }}</td>
              <td class="text-end">{{ formatKg(row.total_output_kg) }}</td>
              <td class="text-end" :class="{ 'best-efficiency': row.cost_per_kg === lowestCostPerKg }">
                {{ formatCurrency(row.cost_per_kg) }}
              </td>
              <td class="text-end">{{ row.transformation_count }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Payment / Output Trend -->
    <div class="chart-card" v-if="data?.payment_output_trend?.length">
      <h6 class="chart-title">Payment &amp; Output Trend</h6>
      <div class="chart-wrap">
        <Chart type="bar" :data="trendChartData" :options="trendOptions" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.reports-personnel {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 24px; }
.kpi-card { background: var(--bg-card); border: 1px solid var(--border-light); border-radius: 12px; padding: 16px 20px; }
.kpi-label { font-size: 0.78rem; color: var(--text-secondary); margin-bottom: 4px; font-weight: 500; }
.kpi-value { font-size: 1.4rem; font-family: var(--font-display); color: var(--text-primary); font-weight: 700; }
.chart-card { background: var(--bg-card); border: 1px solid var(--border-light); border-radius: 12px; padding: 20px; margin-bottom: 20px; }
.chart-title { font-family: var(--font-display); font-size: 1rem; color: var(--text-primary); margin: 0 0 16px; }
.chart-wrap { position: relative; height: 280px; }

.table-responsive {
  overflow-x: auto;
}

.ranking-table {
  width: 100%;
  border-collapse: collapse;
  font-family: var(--font-body);
  font-size: 0.85rem;
}

.ranking-table th {
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  font-size: 0.72rem;
  letter-spacing: 0.03em;
  padding: 8px 12px;
  border-bottom: 2px solid var(--border-light);
  white-space: nowrap;
}

.ranking-table th.sortable {
  cursor: pointer;
  user-select: none;
}

.ranking-table th.sortable:hover {
  color: var(--text-primary);
}

.ranking-table th .bi {
  font-size: 0.65rem;
  margin-left: 4px;
  vertical-align: middle;
}

.ranking-table td {
  padding: 8px 12px;
  color: var(--text-primary);
  border-bottom: 1px solid var(--border-light);
}

.text-end {
  text-align: right;
}

.best-efficiency {
  color: #28a745;
  font-weight: 700;
}

@media (max-width: 767.98px) {
  .ranking-table {
    font-size: 0.78rem;
  }
  .ranking-table th,
  .ranking-table td {
    padding: 6px 8px;
  }
}
</style>

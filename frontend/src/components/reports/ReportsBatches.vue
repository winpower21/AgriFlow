<template>
  <div class="reports-batches">
    <!-- KPI Cards -->
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">Total Batches</div>
        <div class="kpi-value">{{ kpis.total_batches ?? 0 }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Avg Cost/kg</div>
        <div class="kpi-value">{{ formatCurrency(kpis.avg_cost_per_kg) }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Total Weight</div>
        <div class="kpi-value">{{ formatKg(kpis.total_weight_kg) }} kg</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Depleted Count</div>
        <div class="kpi-value">{{ kpis.depleted_count ?? 0 }}</div>
      </div>
    </div>

    <!-- Avg Cost by Stage -->
    <div class="chart-card" v-if="data.avg_cost_by_stage?.length">
      <h3 class="chart-title">Avg Cost per kg by Stage</h3>
      <div class="chart-wrap">
        <Bar :data="costByStageChartData" :options="costByStageChartOptions" />
      </div>
    </div>

    <!-- Cost Trend -->
    <div class="chart-card" v-if="data.cost_trend?.length">
      <h3 class="chart-title">Cost Trend</h3>
      <div class="chart-wrap">
        <Line :data="costTrendChartData" :options="costTrendChartOptions" />
      </div>
    </div>

    <!-- Top Cost Contributors -->
    <div class="chart-card" v-if="data.top_cost_contributors?.length">
      <h3 class="chart-title">Top Cost Contributors</h3>
      <div class="table-responsive">
        <table class="styled-table">
          <thead>
            <tr>
              <th>Batch Code</th>
              <th class="text-end">Cost/kg</th>
              <th class="text-end">Input</th>
              <th class="text-end">Labor</th>
              <th class="text-end">Consumable</th>
              <th class="text-end">Vehicle</th>
              <th class="text-end">Expense</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in data.top_cost_contributors" :key="item.batch_code">
              <td class="batch-code-cell">{{ item.batch_code }}</td>
              <td class="text-end fw-600">{{ formatCurrency(item.cost_per_kg) }}</td>
              <td class="text-end cell-input">{{ formatCurrency(item.breakdown?.input_cost) }}</td>
              <td class="text-end cell-labor">{{ formatCurrency(item.breakdown?.labor_cost) }}</td>
              <td class="text-end cell-consumable">{{ formatCurrency(item.breakdown?.consumable_cost) }}</td>
              <td class="text-end cell-vehicle">{{ formatCurrency(item.breakdown?.vehicle_cost) }}</td>
              <td class="text-end cell-expense">{{ formatCurrency(item.breakdown?.expense_cost) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="isEmpty" class="text-center text-muted py-5">
      No batch data available for the selected period.
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Bar, Line } from 'vue-chartjs'
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement,
  PointElement, LineElement, Title, Tooltip, Legend, Filler
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, Title, Tooltip, Legend, Filler)

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

const props = defineProps({
  data: { type: Object, required: true }
})

const kpis = computed(() => props.data.kpis || {})

const isEmpty = computed(() => {
  return !kpis.value.total_batches
    && !props.data.avg_cost_by_stage?.length
    && !props.data.cost_trend?.length
})

// Avg Cost by Stage — Bar chart
const costByStageChartData = computed(() => {
  const items = props.data.avg_cost_by_stage || []
  return {
    labels: items.map(i => i.stage_name),
    datasets: [{
      label: 'Avg Cost/kg',
      data: items.map(i => i.avg_cost_per_kg),
      backgroundColor: COLORS.mossAlpha,
      borderColor: COLORS.moss,
      borderWidth: 1,
      borderRadius: 4,
    }]
  }
})

const costByStageChartOptions = computed(() => {
  const items = props.data.avg_cost_by_stage || []
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label(ctx) {
            return `Avg Cost/kg: ${formatCurrency(ctx.raw)}`
          },
          afterLabel(ctx) {
            const item = items[ctx.dataIndex]
            return item ? `Batch Count: ${item.batch_count}` : ''
          }
        }
      }
    },
    scales: {
      x: { grid: { display: false } },
      y: {
        title: { display: true, text: 'Cost/kg (\u20B9)' },
        grid: { color: 'rgba(0,0,0,0.05)' },
        ticks: { callback: v => formatCurrency(v) }
      }
    }
  }
})

// Cost Trend — Line chart
const costTrendChartData = computed(() => {
  const items = props.data.cost_trend || []
  return {
    labels: items.map(i => formatPeriod(i.period)),
    datasets: [{
      label: 'Avg Cost/kg',
      data: items.map(i => i.avg_cost_per_kg),
      borderColor: COLORS.moss,
      backgroundColor: COLORS.mossAlpha,
      fill: true,
      tension: 0.3,
      pointRadius: 4,
      pointBackgroundColor: COLORS.moss,
      pointBorderColor: '#fff',
      pointBorderWidth: 2,
    }]
  }
})

const costTrendChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        label(ctx) {
          return `Avg Cost/kg: ${formatCurrency(ctx.raw)}`
        }
      }
    }
  },
  scales: {
    x: { grid: { display: false } },
    y: {
      title: { display: true, text: 'Cost/kg (\u20B9)' },
      grid: { color: 'rgba(0,0,0,0.05)' },
      ticks: { callback: v => formatCurrency(v) }
    }
  }
}
</script>

<style scoped>
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 24px; }
.kpi-card { background: var(--bg-card); border: 1px solid var(--border-light); border-radius: 12px; padding: 16px 20px; }
.kpi-label { font-size: 0.78rem; color: var(--text-secondary); margin-bottom: 4px; font-weight: 500; }
.kpi-value { font-size: 1.4rem; font-family: var(--font-display); color: var(--text-primary); font-weight: 700; }
.chart-card { background: var(--bg-card); border: 1px solid var(--border-light); border-radius: 12px; padding: 20px; margin-bottom: 20px; }
.chart-title { font-family: var(--font-display); font-size: 1rem; color: var(--text-primary); margin: 0 0 16px; }
.chart-wrap { position: relative; height: 280px; }

.styled-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.88rem;
}

.styled-table thead th {
  background: var(--bg-card);
  color: var(--text-secondary);
  font-weight: 600;
  font-size: 0.76rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  padding: 10px 14px;
  border-bottom: 2px solid var(--border-light);
}

.styled-table tbody td {
  padding: 10px 14px;
  border-bottom: 1px solid var(--border-light);
  color: var(--text-primary);
}

.styled-table tbody tr:last-child td {
  border-bottom: none;
}

.batch-code-cell {
  font-weight: 600;
  font-family: var(--font-mono, monospace);
  font-size: 0.84rem;
}

.fw-600 { font-weight: 600; }
.text-end { text-align: right; }

.cell-input { background: rgba(74, 103, 65, 0.08); }
.cell-labor { background: rgba(138, 154, 123, 0.08); }
.cell-consumable { background: rgba(181, 105, 77, 0.08); }
.cell-vehicle { background: rgba(196, 163, 90, 0.08); }
.cell-expense { background: rgba(160, 120, 100, 0.08); }
</style>

<template>
  <div class="reports-transformations">
    <!-- KPI Cards -->
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">Total Transformations</div>
        <div class="kpi-value">{{ kpis.total_transformations ?? 0 }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Avg Completion Days</div>
        <div class="kpi-value">{{ Number(kpis.avg_completion_days || 0).toFixed(1) }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Total Cost</div>
        <div class="kpi-value">{{ formatCurrency(kpis.total_cost) }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Avg Cost</div>
        <div class="kpi-value">{{ formatCurrency(kpis.avg_cost) }}</div>
      </div>
    </div>

    <!-- Avg Completion by Type -->
    <div class="chart-card" v-if="data.avg_completion_by_type?.length">
      <h3 class="chart-title">Avg Completion Days by Type</h3>
      <div class="chart-wrap">
        <Bar :data="completionChartData" :options="completionChartOptions" />
      </div>
    </div>

    <!-- Avg Cost by Type (Stacked) -->
    <div class="chart-card" v-if="data.avg_cost_by_type?.length">
      <h3 class="chart-title">Avg Cost by Type</h3>
      <div class="chart-wrap">
        <Bar :data="costByTypeChartData" :options="costByTypeChartOptions" />
      </div>
    </div>

    <!-- Resource Utilization -->
    <div class="chart-card" v-if="data.resource_utilization?.length">
      <h3 class="chart-title">Resource Utilization by Type</h3>
      <div class="chart-wrap">
        <Bar :data="resourceChartData" :options="resourceChartOptions" />
      </div>
    </div>

    <!-- Consumable Usage by Type -->
    <div class="chart-card" v-if="consumableGroups.length">
      <h3 class="chart-title">Consumable Usage by Type</h3>
      <div class="table-responsive">
        <table class="styled-table">
          <thead>
            <tr>
              <th>Type</th>
              <th>Consumable</th>
              <th class="text-end">Avg Quantity</th>
              <th class="text-end">Avg Cost</th>
            </tr>
          </thead>
          <tbody>
            <template v-for="group in consumableGroups" :key="group.type_name">
              <tr v-for="(item, idx) in group.items" :key="group.type_name + '-' + item.consumable_name">
                <td v-if="idx === 0" :rowspan="group.items.length" class="type-cell">
                  {{ group.type_name }}
                </td>
                <td>{{ item.consumable_name }}</td>
                <td class="text-end">{{ formatKg(item.avg_quantity) }}</td>
                <td class="text-end">{{ formatCurrency(item.avg_cost) }}</td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="isEmpty" class="text-center text-muted py-5">
      No transformation data available for the selected period.
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Bar } from 'vue-chartjs'
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

const props = defineProps({
  data: { type: Object, required: true }
})

const kpis = computed(() => props.data.kpis || {})

const isEmpty = computed(() => {
  return !kpis.value.total_transformations
    && !props.data.avg_completion_by_type?.length
    && !props.data.avg_cost_by_type?.length
})

// Avg Completion by Type — Horizontal bar
const completionChartData = computed(() => {
  const items = props.data.avg_completion_by_type || []
  return {
    labels: items.map(i => i.type_name),
    datasets: [{
      label: 'Avg Days',
      data: items.map(i => i.avg_days),
      backgroundColor: COLORS.mossAlpha,
      borderColor: COLORS.moss,
      borderWidth: 1,
      borderRadius: 4,
    }]
  }
})

const completionChartOptions = computed(() => {
  const items = props.data.avg_completion_by_type || []
  return {
    indexAxis: 'y',
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          afterLabel(ctx) {
            const item = items[ctx.dataIndex]
            return item ? `Count: ${item.count}` : ''
          }
        }
      }
    },
    scales: {
      x: { title: { display: true, text: 'Avg Days' }, grid: { display: false } },
      y: { grid: { display: false } }
    }
  }
})

// Avg Cost by Type — Stacked bar
const costByTypeChartData = computed(() => {
  const items = props.data.avg_cost_by_type || []
  return {
    labels: items.map(i => i.type_name),
    datasets: [
      {
        label: 'Labor Cost',
        data: items.map(i => i.avg_labor_cost),
        backgroundColor: COLORS.mossAlpha,
        borderColor: COLORS.moss,
        borderWidth: 1,
        borderRadius: 4,
      },
      {
        label: 'Consumable Cost',
        data: items.map(i => i.avg_consumable_cost),
        backgroundColor: COLORS.siennaAlpha,
        borderColor: COLORS.sienna,
        borderWidth: 1,
        borderRadius: 4,
      }
    ]
  }
})

const costByTypeChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { position: 'bottom' },
    tooltip: {
      callbacks: {
        label(ctx) {
          return `${ctx.dataset.label}: ${formatCurrency(ctx.raw)}`
        }
      }
    }
  },
  scales: {
    x: { stacked: true, grid: { display: false } },
    y: {
      stacked: true,
      title: { display: true, text: 'Cost (\u20B9)' },
      grid: { color: 'rgba(0,0,0,0.05)' },
      ticks: { callback: v => formatCurrency(v) }
    }
  }
}

// Resource Utilization — Grouped bar
const resourceChartData = computed(() => {
  const items = props.data.resource_utilization || []
  return {
    labels: items.map(i => i.type_name),
    datasets: [
      {
        label: 'Avg Personnel Count',
        data: items.map(i => i.avg_personnel_count),
        backgroundColor: COLORS.sageAlpha,
        borderColor: COLORS.sage,
        borderWidth: 1,
        borderRadius: 4,
      },
      {
        label: 'Avg Vehicle Hours',
        data: items.map(i => i.avg_vehicle_hours),
        backgroundColor: COLORS.harvestAlpha,
        borderColor: COLORS.harvest,
        borderWidth: 1,
        borderRadius: 4,
      }
    ]
  }
})

const resourceChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { position: 'bottom' } },
  scales: {
    x: { grid: { display: false } },
    y: { grid: { color: 'rgba(0,0,0,0.05)' } }
  }
}

// Consumable Usage grouped by type
const consumableGroups = computed(() => {
  const items = props.data.consumable_usage_by_type || []
  const map = new Map()
  for (const item of items) {
    if (!map.has(item.type_name)) {
      map.set(item.type_name, { type_name: item.type_name, items: [] })
    }
    map.get(item.type_name).items.push(item)
  }
  return Array.from(map.values())
})
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

.type-cell {
  font-weight: 600;
  vertical-align: top;
  color: var(--text-primary);
}

.text-end { text-align: right; }
</style>

<script setup>
import { computed } from 'vue'
import { Bar, Line } from 'vue-chartjs'
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement,
  ArcElement, PointElement, LineElement,
  Title, Tooltip, Legend, Filler
} from 'chart.js'

ChartJS.register(
  CategoryScale, LinearScale, BarElement,
  ArcElement, PointElement, LineElement,
  Title, Tooltip, Legend, Filler
)

const props = defineProps({
  data: { type: Object, required: true }
})

// --- Color palette ---
const COLORS = {
  moss: '#4A6741',
  sage: '#8A9A7B',
  sienna: '#B5694D',
  harvest: '#C4A35A',
  mossLight: '#5E7D54',
  mossAlpha: 'rgba(74, 103, 65, 0.6)',
  sageAlpha: 'rgba(138, 154, 123, 0.6)',
  siennaAlpha: 'rgba(181, 105, 77, 0.6)',
  harvestAlpha: 'rgba(196, 163, 90, 0.6)',
  mossLightAlpha: 'rgba(94, 125, 84, 0.6)',
}

const lineColors = [
  { border: COLORS.moss, bg: COLORS.mossAlpha },
  { border: COLORS.harvest, bg: COLORS.harvestAlpha },
  { border: COLORS.sienna, bg: COLORS.siennaAlpha },
  { border: COLORS.sage, bg: COLORS.sageAlpha },
  { border: COLORS.mossLight, bg: COLORS.mossLightAlpha },
]

// --- Formatting helpers ---
function formatCurrency(v) {
  return '\u20B9' + Number(v || 0).toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
}
function formatKg(v) {
  return Number(v || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
function formatPeriod(p) {
  if (!p) return ''
  if (p.length === 10) {
    const d = new Date(p)
    return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })
  }
  const [y, m] = p.split('-')
  const d = new Date(parseInt(y), parseInt(m) - 1)
  return d.toLocaleDateString('en-IN', { month: 'short', year: '2-digit' })
}

const currencyCallback = (val) => formatCurrency(val)
const kgCallback = (val) => formatKg(val) + ' kg'

// --- KPI computed ---
const kpis = computed(() => props.data.kpis || {})

// --- Output Over Time: Line chart, one line per plantation ---
const outputData = computed(() => {
  const items = props.data.output_over_time || []
  // Collect unique periods and plantation names
  const periodSet = new Set()
  const plantationSet = new Set()
  items.forEach(i => {
    periodSet.add(i.period)
    plantationSet.add(i.plantation_name)
  })
  const periods = [...periodSet].sort()
  const plantations = [...plantationSet]

  // Build lookup: plantation_name -> { period -> harvest_kg }
  const lookup = {}
  items.forEach(i => {
    if (!lookup[i.plantation_name]) lookup[i.plantation_name] = {}
    lookup[i.plantation_name][i.period] = (lookup[i.plantation_name][i.period] || 0) + i.harvest_kg
  })

  const datasets = plantations.map((name, idx) => {
    const color = lineColors[idx % lineColors.length]
    return {
      label: name,
      data: periods.map(p => lookup[name]?.[p] || 0),
      borderColor: color.border,
      backgroundColor: color.bg,
      pointBackgroundColor: color.border,
      pointRadius: 3,
      fill: false,
      tension: 0.3,
    }
  })

  return {
    labels: periods.map(p => formatPeriod(p)),
    datasets,
  }
})

const outputOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: true, position: 'bottom', labels: { boxWidth: 12, padding: 10, font: { size: 11 } } } },
  scales: {
    y: {
      beginAtZero: true,
      ticks: { callback: kgCallback },
    },
  },
}

// --- Lease Cost Trends: Line chart, one line per plantation with long lease ---
const leaseData = computed(() => {
  const trends = (props.data.lease_cost_trends || []).filter(t => t.has_long_lease)
  if (!trends.length) return null

  // Collect all periods
  const periodSet = new Set()
  trends.forEach(t => (t.periods || []).forEach(p => periodSet.add(p.period)))
  const periods = [...periodSet].sort()

  const datasets = trends.map((t, idx) => {
    const color = lineColors[idx % lineColors.length]
    const lookup = {}
    ;(t.periods || []).forEach(p => { lookup[p.period] = p.lease_cost })
    return {
      label: t.plantation_name,
      data: periods.map(p => lookup[p] || 0),
      borderColor: color.border,
      backgroundColor: color.bg,
      pointBackgroundColor: color.border,
      pointRadius: 3,
      fill: false,
      tension: 0.3,
    }
  })

  return {
    labels: periods.map(p => formatPeriod(p)),
    datasets,
  }
})

const leaseOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: true, position: 'bottom', labels: { boxWidth: 12, padding: 10, font: { size: 11 } } } },
  scales: {
    y: {
      beginAtZero: true,
      ticks: { callback: currencyCallback },
    },
  },
}

// --- Lease-to-Output Ratio: Bar chart ---
const leaseOutputData = computed(() => {
  const items = props.data.lease_to_output_ratio || []
  return {
    labels: items.map(i => i.plantation_name),
    datasets: [{
      label: 'Cost per kg',
      data: items.map(i => i.cost_per_kg),
      backgroundColor: COLORS.harvestAlpha,
      borderColor: COLORS.harvest,
      borderWidth: 1,
    }],
  }
})

const leaseOutputOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: {
    y: {
      beginAtZero: true,
      ticks: { callback: currencyCallback },
    },
  },
}

// --- Lease-to-Revenue Ratio: Bar chart ---
const leaseRevenueData = computed(() => {
  const items = props.data.lease_to_revenue_ratio || []
  return {
    labels: items.map(i => i.plantation_name),
    datasets: [{
      label: 'Lease / Revenue Ratio',
      data: items.map(i => i.ratio),
      backgroundColor: COLORS.siennaAlpha,
      borderColor: COLORS.sienna,
      borderWidth: 1,
    }],
  }
})

const leaseRevenueOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: {
    y: {
      beginAtZero: true,
      ticks: { callback: (val) => val.toFixed(2) },
    },
  },
}
</script>

<template>
  <div class="reports-plantations">
    <!-- KPI Cards -->
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">Total Plantations</div>
        <div class="kpi-value">{{ kpis.total_plantations || 0 }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Active Count</div>
        <div class="kpi-value">{{ kpis.active_count || 0 }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Total Harvest</div>
        <div class="kpi-value">{{ formatKg(kpis.total_harvest_kg) }} kg</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Total Lease Cost</div>
        <div class="kpi-value">{{ formatCurrency(kpis.total_lease_cost) }}</div>
      </div>
    </div>

    <!-- Output Over Time -->
    <div v-if="data.output_over_time?.length" class="chart-section">
      <div class="chart-header">
        <h6>Harvest Output Over Time</h6>
      </div>
      <div class="chart-container">
        <Line :data="outputData" :options="outputOptions" />
      </div>
    </div>

    <!-- Lease Cost Trends -->
    <div v-if="leaseData" class="chart-section">
      <div class="chart-header">
        <h6>Lease Cost Trends</h6>
      </div>
      <div class="chart-container">
        <Line :data="leaseData" :options="leaseOptions" />
      </div>
    </div>

    <!-- Two-column: Lease-to-Output + Lease-to-Revenue -->
    <div v-if="data.lease_to_output_ratio?.length || data.lease_to_revenue_ratio?.length" class="two-col">
      <div class="chart-section">
        <div class="chart-header">
          <h6>Lease Cost per kg Harvested</h6>
        </div>
        <div class="chart-container">
          <Bar :data="leaseOutputData" :options="leaseOutputOptions" />
        </div>
      </div>

      <div class="chart-section">
        <div class="chart-header">
          <h6>Lease-to-Revenue Ratio</h6>
        </div>
        <div class="chart-container">
          <Bar :data="leaseRevenueData" :options="leaseRevenueOptions" />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.reports-plantations {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* --- KPI Grid --- */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
}

.kpi-card {
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 16px;
  box-shadow: var(--shadow-sm);
}

.kpi-label {
  font-family: var(--font-body);
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.03em;
  margin-bottom: 6px;
}

.kpi-value {
  font-family: var(--font-display);
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-primary);
}

/* --- Chart Sections --- */
.chart-section {
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: 14px;
  padding: 18px;
  box-shadow: var(--shadow-sm);
}

.chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
  flex-wrap: wrap;
  gap: 8px;
}

.chart-header h6 {
  font-family: var(--font-display);
  font-size: 0.95rem;
  margin: 0;
  color: var(--text-primary);
}

.chart-container {
  position: relative;
  height: 300px;
}

/* --- Two-column layout --- */
.two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

/* --- Responsive --- */
@media (max-width: 767.98px) {
  .kpi-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .kpi-value {
    font-size: 1.05rem;
  }

  .chart-container {
    height: 250px;
  }

  .two-col {
    grid-template-columns: 1fr;
  }
}
</style>

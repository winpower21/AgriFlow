<script setup>
import { ref, computed } from 'vue'
import { Bar, Pie, Line } from 'vue-chartjs'
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
  data: { type: Object, required: true },
  isAdmin: { type: Boolean, default: false }
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
function formatPct(v) {
  return Number(v || 0).toFixed(1) + '%'
}

// --- Toggles ---
const revenueToggle = ref('revenue')
const stageToggle = ref('revenue')
const customerToggle = ref('revenue')

// --- Chart options base ---
const currencyCallback = (val) => formatCurrency(val)
const kgCallback = (val) => formatKg(val) + ' kg'

// --- Section 2: Revenue Over Time ---
const revenueTimeLabels = computed(() =>
  (props.data.revenue_over_time || []).map(r => formatPeriod(r.period))
)

const revenueTimeData = computed(() => {
  const rot = props.data.revenue_over_time || []
  const mode = revenueToggle.value
  const datasets = []
  if (mode === 'revenue' || mode === 'both') {
    datasets.push({
      label: 'Revenue',
      data: rot.map(r => r.revenue),
      backgroundColor: COLORS.mossAlpha,
      borderColor: COLORS.moss,
      borderWidth: 1,
    })
  }
  if (mode === 'volume' || mode === 'both') {
    datasets.push({
      label: 'Volume (kg)',
      data: rot.map(r => r.volume_kg),
      backgroundColor: COLORS.harvestAlpha,
      borderColor: COLORS.harvest,
      borderWidth: 1,
      yAxisID: mode === 'both' ? 'y1' : 'y',
    })
  }
  return { labels: revenueTimeLabels.value, datasets }
})

const revenueTimeOptions = computed(() => {
  const mode = revenueToggle.value
  const opts = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: mode === 'both' } },
    scales: {
      y: {
        beginAtZero: true,
        ticks: { callback: mode === 'volume' ? kgCallback : currencyCallback },
      },
    },
  }
  if (mode === 'both') {
    opts.scales.y.position = 'left'
    opts.scales.y.ticks = { callback: currencyCallback }
    opts.scales.y1 = {
      position: 'right',
      beginAtZero: true,
      grid: { drawOnChartArea: false },
      ticks: { callback: kgCallback },
    }
  }
  return opts
})

// --- Section 3: Sales by Stage ---
const stageLabels = computed(() =>
  (props.data.sales_by_stage || []).map(s => s.stage_name)
)

const stageData = computed(() => {
  const sbs = props.data.sales_by_stage || []
  const mode = stageToggle.value
  const datasets = []
  if (mode === 'revenue' || mode === 'both') {
    datasets.push({
      label: 'Revenue',
      data: sbs.map(s => s.revenue),
      backgroundColor: COLORS.mossAlpha,
      borderColor: COLORS.moss,
      borderWidth: 1,
    })
  }
  if (mode === 'volume' || mode === 'both') {
    datasets.push({
      label: 'Volume (kg)',
      data: sbs.map(s => s.volume_kg),
      backgroundColor: COLORS.harvestAlpha,
      borderColor: COLORS.harvest,
      borderWidth: 1,
    })
  }
  return { labels: stageLabels.value, datasets }
})

const stageOptions = computed(() => {
  const mode = stageToggle.value
  return {
    responsive: true,
    maintainAspectRatio: false,
    indexAxis: 'y',
    plugins: { legend: { display: mode === 'both' } },
    scales: {
      x: {
        beginAtZero: true,
        ticks: { callback: mode === 'volume' ? kgCallback : currencyCallback },
      },
    },
  }
})

// --- Section 4a: Top Customers ---
const pieColors = [COLORS.moss, COLORS.harvest, COLORS.sienna, COLORS.sage, COLORS.mossLight]
const pieAlphaColors = [COLORS.mossAlpha, COLORS.harvestAlpha, COLORS.siennaAlpha, COLORS.sageAlpha, COLORS.mossLightAlpha]

const customerLabels = computed(() =>
  (props.data.top_customers || []).map(c => c.customer_name)
)

const customerChartData = computed(() => {
  const tc = props.data.top_customers || []
  const mode = customerToggle.value
  if (mode === 'both') {
    // Horizontal bar with 2 datasets
    const datasets = [
      {
        label: 'Revenue',
        data: tc.map(c => c.revenue),
        backgroundColor: COLORS.mossAlpha,
        borderColor: COLORS.moss,
        borderWidth: 1,
      },
      {
        label: 'Volume (kg)',
        data: tc.map(c => c.volume_kg),
        backgroundColor: COLORS.harvestAlpha,
        borderColor: COLORS.harvest,
        borderWidth: 1,
      },
    ]
    return { labels: customerLabels.value, datasets }
  }
  // Pie chart
  const field = mode === 'volume' ? 'volume_kg' : 'revenue'
  return {
    labels: customerLabels.value,
    datasets: [{
      data: tc.map(c => c[field]),
      backgroundColor: pieColors.slice(0, tc.length),
    }],
  }
})

const customerChartOptions = computed(() => {
  const mode = customerToggle.value
  if (mode === 'both') {
    return {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: 'y',
      plugins: { legend: { display: true } },
      scales: { x: { beginAtZero: true } },
    }
  }
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'bottom', labels: { boxWidth: 12, padding: 10, font: { size: 11 } } },
      tooltip: {
        callbacks: {
          label: (ctx) => {
            const val = ctx.parsed
            return mode === 'volume'
              ? `${ctx.label}: ${formatKg(val)} kg`
              : `${ctx.label}: ${formatCurrency(val)}`
          }
        }
      }
    },
  }
})

// --- Section 4b: Payment Breakdown ---
const paymentData = computed(() => {
  const pb = props.data.payment_breakdown || {}
  return {
    labels: ['Paid', 'Credit'],
    datasets: [{
      data: [pb.paid_amount || 0, pb.credit_amount || 0],
      backgroundColor: [COLORS.mossAlpha, COLORS.siennaAlpha],
    }],
  }
})

const paymentOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { position: 'bottom', labels: { boxWidth: 12, padding: 10, font: { size: 11 } } },
    tooltip: {
      callbacks: {
        label: (ctx) => `${ctx.label}: ${formatCurrency(ctx.parsed)}`
      }
    }
  },
}

// --- Section 5: Profitability (admin only) ---
const profitLabels = computed(() =>
  (props.data.profit_over_time || []).map(p => formatPeriod(p.period))
)

const profitData = computed(() => {
  const pot = props.data.profit_over_time || []
  return {
    labels: profitLabels.value,
    datasets: [
      {
        type: 'bar',
        label: 'Profit',
        data: pot.map(p => p.profit),
        backgroundColor: COLORS.mossAlpha,
        borderColor: COLORS.moss,
        borderWidth: 1,
        yAxisID: 'y',
        order: 2,
      },
      {
        type: 'line',
        label: 'Margin %',
        data: pot.map(p => p.margin_pct),
        borderColor: COLORS.sienna,
        backgroundColor: 'rgba(181, 105, 77, 0.1)',
        pointBackgroundColor: COLORS.sienna,
        pointRadius: 3,
        fill: true,
        tension: 0.3,
        yAxisID: 'y1',
        order: 1,
      },
    ],
  }
})

const profitOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: true } },
  scales: {
    y: {
      position: 'left',
      beginAtZero: true,
      ticks: { callback: currencyCallback },
    },
    y1: {
      position: 'right',
      beginAtZero: true,
      grid: { drawOnChartArea: false },
      ticks: { callback: (val) => val + '%' },
    },
  },
}
</script>

<template>
  <div class="sales-dashboard">
    <!-- Section 1: KPI Cards -->
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">Total Sales</div>
        <div class="kpi-value">{{ data.kpis.total_sales_count }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Total Revenue</div>
        <div class="kpi-value">{{ formatCurrency(data.kpis.total_revenue) }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Outstanding Credit</div>
        <div class="kpi-value kpi-orange">{{ formatCurrency(data.kpis.outstanding_credit_amount) }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Avg Sale Value</div>
        <div class="kpi-value">{{ formatCurrency(data.kpis.avg_sale_value) }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Total Volume</div>
        <div class="kpi-value">{{ formatKg(data.kpis.total_volume_kg) }} kg</div>
      </div>
      <div v-if="isAdmin" class="kpi-card">
        <div class="kpi-label">Total Profit</div>
        <div class="kpi-value kpi-green">{{ formatCurrency(data.kpis.total_profit) }}</div>
      </div>
      <div v-if="isAdmin" class="kpi-card">
        <div class="kpi-label">Avg Profit Margin</div>
        <div class="kpi-value kpi-green">{{ formatPct(data.kpis.avg_profit_margin) }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Paid / Credit</div>
        <div class="kpi-value">{{ data.kpis.paid_count }} / {{ data.kpis.credit_count }}</div>
      </div>
    </div>

    <!-- Section 2: Revenue Over Time -->
    <div class="chart-section">
      <div class="chart-header">
        <h6>Sales &amp; Revenue Over Time</h6>
        <div class="toggle-group">
          <button :class="['toggle-btn', { active: revenueToggle === 'revenue' }]" @click="revenueToggle = 'revenue'">Revenue</button>
          <button :class="['toggle-btn', { active: revenueToggle === 'volume' }]" @click="revenueToggle = 'volume'">Volume</button>
          <button :class="['toggle-btn', { active: revenueToggle === 'both' }]" @click="revenueToggle = 'both'">Both</button>
        </div>
      </div>
      <div class="chart-container">
        <Bar :data="revenueTimeData" :options="revenueTimeOptions" />
      </div>
    </div>

    <!-- Section 3: Sales by Stage -->
    <div class="chart-section">
      <div class="chart-header">
        <h6>Sales by Stage</h6>
        <div class="toggle-group">
          <button :class="['toggle-btn', { active: stageToggle === 'revenue' }]" @click="stageToggle = 'revenue'">Revenue</button>
          <button :class="['toggle-btn', { active: stageToggle === 'volume' }]" @click="stageToggle = 'volume'">Volume</button>
          <button :class="['toggle-btn', { active: stageToggle === 'both' }]" @click="stageToggle = 'both'">Both</button>
        </div>
      </div>
      <div class="chart-container">
        <Bar :data="stageData" :options="stageOptions" />
      </div>
    </div>

    <!-- Section 4: Two-column — Top Customers + Payment Breakdown -->
    <div class="two-col">
      <div class="chart-section">
        <div class="chart-header">
          <h6>Top 5 Customers</h6>
          <div class="toggle-group">
            <button :class="['toggle-btn', { active: customerToggle === 'revenue' }]" @click="customerToggle = 'revenue'">Revenue</button>
            <button :class="['toggle-btn', { active: customerToggle === 'volume' }]" @click="customerToggle = 'volume'">Volume</button>
            <button :class="['toggle-btn', { active: customerToggle === 'both' }]" @click="customerToggle = 'both'">Both</button>
          </div>
        </div>
        <div class="chart-container">
          <Bar v-if="customerToggle === 'both'" :data="customerChartData" :options="customerChartOptions" />
          <Pie v-else :data="customerChartData" :options="customerChartOptions" />
        </div>
      </div>
      <div class="chart-section">
        <div class="chart-header">
          <h6>Payment Breakdown</h6>
        </div>
        <div class="chart-container">
          <Pie :data="paymentData" :options="paymentOptions" />
        </div>
      </div>
    </div>

    <!-- Section 5: Profitability (admin only) -->
    <div v-if="isAdmin" class="chart-section">
      <div class="chart-header">
        <h6>Profitability Over Time</h6>
      </div>
      <div class="chart-container">
        <Bar :data="profitData" :options="profitOptions" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.sales-dashboard {
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

.kpi-orange { color: #c47a2a; }
.kpi-green { color: #28a745; }

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

/* --- Toggle Group --- */
.toggle-group {
  display: flex;
  gap: 0;
}

.toggle-btn {
  padding: 5px 14px;
  border: 1.5px solid var(--border);
  background: var(--bg-card);
  font-family: var(--font-body);
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  color: var(--text-secondary);
  transition: all 0.15s ease;
}

.toggle-btn:first-child { border-radius: 8px 0 0 8px; }
.toggle-btn:last-child { border-radius: 0 8px 8px 0; }
.toggle-btn.active {
  background: #4A6741;
  color: #fff;
  border-color: #4A6741;
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

  .chart-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>

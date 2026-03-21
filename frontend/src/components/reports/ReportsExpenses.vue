<script setup>
import { computed } from 'vue'
import { Bar, Pie } from 'vue-chartjs'
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

const pieColors = [COLORS.moss, COLORS.harvest, COLORS.sienna, COLORS.sage, COLORS.mossLight]

// --- Formatting helpers ---
function formatCurrency(v) {
  return '\u20B9' + Number(v || 0).toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
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

// --- KPI computed ---
const kpis = computed(() => props.data.kpis || {})

// --- Category Distribution Pie Chart ---
const categoryData = computed(() => {
  const cats = props.data.category_distribution || []
  return {
    labels: cats.map(c => c.category_name),
    datasets: [{
      data: cats.map(c => c.total),
      backgroundColor: pieColors.slice(0, cats.length).concat(
        cats.length > pieColors.length
          ? cats.slice(pieColors.length).map((_, i) => `hsl(${120 + i * 40}, 35%, 50%)`)
          : []
      ),
    }],
  }
})

const categoryOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { position: 'bottom', labels: { boxWidth: 12, padding: 10, font: { size: 11 } } },
    tooltip: {
      callbacks: {
        label: (ctx) => {
          const cat = props.data.category_distribution?.[ctx.dataIndex]
          const pct = cat ? ` (${Number(cat.percentage).toFixed(1)}%)` : ''
          return `${ctx.label}: ${formatCurrency(ctx.parsed)}${pct}`
        }
      }
    }
  },
}

// --- Time Distribution Bar Chart ---
const timeData = computed(() => {
  const td = props.data.time_distribution || []
  return {
    labels: td.map(t => formatPeriod(t.period)),
    datasets: [{
      label: 'Expenses',
      data: td.map(t => t.total),
      backgroundColor: COLORS.siennaAlpha,
      borderColor: COLORS.sienna,
      borderWidth: 1,
    }],
  }
})

const timeOptions = {
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
</script>

<template>
  <div class="reports-expenses">
    <!-- KPI Cards -->
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">Total Expenses</div>
        <div class="kpi-value">{{ formatCurrency(kpis.total_expenses) }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Avg Per Month</div>
        <div class="kpi-value">{{ formatCurrency(kpis.avg_per_period) }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Largest Category</div>
        <div class="kpi-value kpi-text">{{ kpis.largest_category || '-' }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Total Count</div>
        <div class="kpi-value">{{ kpis.expense_count || 0 }}</div>
      </div>
    </div>

    <!-- Two-column: Category Pie + Time Bar -->
    <div class="two-col">
      <div class="chart-section">
        <div class="chart-header">
          <h6>Category Distribution</h6>
        </div>
        <div class="chart-container">
          <Pie :data="categoryData" :options="categoryOptions" />
        </div>
      </div>

      <div class="chart-section">
        <div class="chart-header">
          <h6>Monthly Expenses</h6>
        </div>
        <div class="chart-container">
          <Bar :data="timeData" :options="timeOptions" />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.reports-expenses {
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

.kpi-text {
  font-size: 1.05rem;
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

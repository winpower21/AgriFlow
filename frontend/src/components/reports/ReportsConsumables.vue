<script setup>
import { computed, ref } from 'vue'
import { Bar, Pie } from 'vue-chartjs'
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement,
  ArcElement, PointElement, LineElement, Title, Tooltip, Legend, Filler
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, PointElement, LineElement, Title, Tooltip, Legend, Filler)

const props = defineProps({
  data: { type: Object, required: true }
})

const COLORS = {
  moss: '#4A6741', sage: '#8A9A7B', sienna: '#B5694D', harvest: '#C4A35A', mossLight: '#5E7D54',
  mossAlpha: 'rgba(74, 103, 65, 0.6)', sageAlpha: 'rgba(138, 154, 123, 0.6)',
  siennaAlpha: 'rgba(181, 105, 77, 0.6)', harvestAlpha: 'rgba(196, 163, 90, 0.6)',
  mossLightAlpha: 'rgba(94, 125, 84, 0.6)',
}

const PIE_COLORS = [
  COLORS.moss, COLORS.sage, COLORS.sienna, COLORS.harvest, COLORS.mossLight,
  '#7B9E89', '#C4856D', '#A89056', '#6B8C5E', '#D4A574',
]

function formatCurrency(v) { return '\u20B9' + Number(v || 0).toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 }) }
function formatPct(v) { return Number(v || 0).toFixed(1) + '%' }
function formatPeriod(p) {
  if (!p) return ''
  if (p.length === 10) { const d = new Date(p); return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short' }) }
  const [y, m] = p.split('-'); const d = new Date(parseInt(y), parseInt(m) - 1); return d.toLocaleDateString('en-IN', { month: 'short', year: '2-digit' })
}

/* ── KPIs ── */
const kpis = computed(() => props.data.kpis || {})

/* ── Utilization by Item (horizontal bar) ── */
const utilizationData = computed(() => {
  const items = props.data.utilization_by_item || []
  return {
    labels: items.map(i => i.consumable_name),
    datasets: [
      {
        label: 'Purchased',
        data: items.map(i => i.purchased_qty),
        backgroundColor: COLORS.mossAlpha,
        borderColor: COLORS.moss,
        borderWidth: 1,
      },
      {
        label: 'Consumed',
        data: items.map(i => i.consumed_qty),
        backgroundColor: COLORS.sageAlpha,
        borderColor: COLORS.sage,
        borderWidth: 1,
      },
    ],
  }
})

const utilizationOptions = {
  indexAxis: 'y',
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    tooltip: {
      callbacks: {
        afterBody(ctx) {
          const idx = ctx[0].dataIndex
          const items = props.data.utilization_by_item || []
          const item = items[idx]
          if (item) return `Utilization: ${formatPct(item.utilization_rate * 100)}`
          return ''
        },
      },
    },
    legend: { position: 'top' },
  },
  scales: {
    x: { beginAtZero: true },
  },
}

/* ── Category Cost Spread (Pie + drill-down) ── */
const selectedCategory = ref(null)

const categoryPieData = computed(() => {
  const cats = props.data.category_cost_spread || []
  return {
    labels: cats.map(c => c.category_name),
    datasets: [{
      data: cats.map(c => Number(c.total_cost)),
      backgroundColor: cats.map((_, i) => PIE_COLORS[i % PIE_COLORS.length]),
      borderWidth: 1,
      borderColor: '#fff',
    }],
  }
})

const categoryPieOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    tooltip: {
      callbacks: {
        label(ctx) {
          const cats = props.data.category_cost_spread || []
          const cat = cats[ctx.dataIndex]
          return `${cat.category_name}: ${formatCurrency(cat.total_cost)} (${formatPct(cat.percentage)})`
        },
      },
    },
    legend: { position: 'right' },
  },
  onClick(_, elements) {
    if (elements.length > 0) {
      const idx = elements[0].index
      const cats = props.data.category_cost_spread || []
      selectedCategory.value = selectedCategory.value === cats[idx]?.category_name ? null : cats[idx]?.category_name
    }
  },
}))

const drillDownItems = computed(() => {
  if (!selectedCategory.value) return []
  const cats = props.data.category_cost_spread || []
  const cat = cats.find(c => c.category_name === selectedCategory.value)
  return cat?.items || []
})

const drillDownData = computed(() => {
  const items = drillDownItems.value
  return {
    labels: items.map(i => i.consumable_name),
    datasets: [{
      label: selectedCategory.value,
      data: items.map(i => Number(i.cost)),
      backgroundColor: COLORS.mossAlpha,
      borderColor: COLORS.moss,
      borderWidth: 1,
    }],
  }
})

const drillDownOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    tooltip: {
      callbacks: { label: (ctx) => formatCurrency(ctx.raw) },
    },
    legend: { display: false },
  },
  scales: {
    y: { ticks: { callback: (v) => formatCurrency(v) } },
  },
}

/* ── Spend Over Time ── */
const spendTimeData = computed(() => {
  const items = props.data.spend_over_time || []
  return {
    labels: items.map(i => formatPeriod(i.period)),
    datasets: [{
      label: 'Spend',
      data: items.map(i => Number(i.total_cost)),
      backgroundColor: COLORS.mossAlpha,
      borderColor: COLORS.moss,
      borderWidth: 1,
    }],
  }
})

const spendTimeOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    tooltip: { callbacks: { label: (ctx) => formatCurrency(ctx.raw) } },
    legend: { display: false },
  },
  scales: {
    y: { ticks: { callback: (v) => formatCurrency(v) } },
    x: { ticks: { maxRotation: 45 } },
  },
}
</script>

<template>
  <div class="reports-consumables">
    <!-- KPIs -->
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">Total Spend</div>
        <div class="kpi-value">{{ formatCurrency(kpis.total_spend) }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Total Items</div>
        <div class="kpi-value">{{ kpis.total_items || 0 }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Top Category</div>
        <div class="kpi-value kpi-value-sm">{{ kpis.top_category || '—' }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Avg Utilization</div>
        <div class="kpi-value">{{ formatPct((kpis.avg_utilization_rate || 0) * 100) }}</div>
      </div>
    </div>

    <!-- Utilization by Item -->
    <div v-if="(data.utilization_by_item || []).length" class="chart-card">
      <h3 class="chart-title">Utilization by Item</h3>
      <div class="chart-wrap" :style="{ height: Math.max(280, (data.utilization_by_item || []).length * 40) + 'px' }">
        <Bar :data="utilizationData" :options="utilizationOptions" />
      </div>
    </div>

    <!-- Category Cost Spread -->
    <div v-if="(data.category_cost_spread || []).length" class="chart-card">
      <h3 class="chart-title">Category Cost Spread</h3>
      <p class="chart-hint">Click a segment to see item breakdown</p>
      <div class="chart-wrap pie-wrap">
        <Pie :data="categoryPieData" :options="categoryPieOptions" />
      </div>

      <!-- Drill-down -->
      <div v-if="selectedCategory" class="drill-down">
        <div class="drill-down-header">
          <h4 class="drill-down-title"><i class="bi bi-arrow-return-right"></i> {{ selectedCategory }}</h4>
          <button class="btn-close-drill" @click="selectedCategory = null"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="chart-wrap">
          <Bar :data="drillDownData" :options="drillDownOptions" />
        </div>
      </div>
    </div>

    <!-- Spend Over Time -->
    <div v-if="(data.spend_over_time || []).length" class="chart-card">
      <h3 class="chart-title">Spend Over Time</h3>
      <div class="chart-wrap">
        <Bar :data="spendTimeData" :options="spendTimeOptions" />
      </div>
    </div>

    <!-- Empty state -->
    <div v-if="!(data.utilization_by_item || []).length && !(data.category_cost_spread || []).length && !(data.spend_over_time || []).length" class="empty-state">
      <i class="bi bi-cart4"></i>
      <p>No consumable data for this period</p>
    </div>
  </div>
</template>

<style scoped>
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 24px; }
.kpi-card { background: var(--bg-card); border: 1px solid var(--border-light); border-radius: 12px; padding: 16px 20px; }
.kpi-label { font-size: 0.78rem; color: var(--text-secondary); margin-bottom: 4px; font-weight: 500; }
.kpi-value { font-size: 1.4rem; font-family: var(--font-display); color: var(--text-primary); font-weight: 700; }
.kpi-value-sm { font-size: 1.1rem; }

.chart-card { background: var(--bg-card); border: 1px solid var(--border-light); border-radius: 12px; padding: 20px; margin-bottom: 20px; }
.chart-title { font-family: var(--font-display); font-size: 1rem; color: var(--text-primary); margin: 0 0 16px; }
.chart-hint { font-size: 0.78rem; color: var(--text-secondary); margin: -10px 0 12px; }
.chart-wrap { position: relative; height: 280px; }
.pie-wrap { max-width: 420px; margin: 0 auto; }

.drill-down { margin-top: 20px; padding-top: 16px; border-top: 1px solid var(--border-light); }
.drill-down-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.drill-down-title { font-family: var(--font-display); font-size: 0.95rem; color: var(--text-primary); margin: 0; }
.drill-down-title i { color: var(--text-secondary); margin-right: 6px; }
.btn-close-drill { border: none; background: none; color: var(--text-secondary); cursor: pointer; padding: 4px; }
.btn-close-drill:hover { color: var(--text-primary); }

.empty-state { text-align: center; padding: 48px 20px; color: var(--text-secondary); }
.empty-state i { font-size: 2.4rem; margin-bottom: 12px; display: block; }
.empty-state p { font-size: 0.9rem; margin: 0; }
</style>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import axios from "axios";
import { DEFAULT_STAGE_COLOR, DEFAULT_STAGE_ICON } from "@/utils/colorPalette";
import { Bar } from "vue-chartjs";
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    Tooltip,
} from "chart.js";

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip);

const auth = useAuthStore();
const router = useRouter();

const summary = ref(null);
const dailyOutput = ref([]);
const recentActivity = ref([]);
const activeTransformations = ref([]);
const loading = ref(true);
const error = ref(null);

const BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
const headers = () => ({ Authorization: `Bearer ${auth.token}` });

const todayStr = new Date().toISOString().slice(0, 10);
const chartEndDate = ref(todayStr);

const isEndDateToday = computed(() => chartEndDate.value >= todayStr);

const dateRangeLabel = computed(() => {
    const end = new Date(chartEndDate.value + "T00:00:00");
    const start = new Date(end);
    start.setDate(start.getDate() - 6);
    const fmt = (d) =>
        d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
    return `${fmt(start)} – ${fmt(end)}`;
});

function shiftDate(days) {
    const d = new Date(chartEndDate.value + "T00:00:00");
    d.setDate(d.getDate() + days);
    const iso = d.toISOString().slice(0, 10);
    if (iso > todayStr) {
        chartEndDate.value = todayStr;
    } else {
        chartEndDate.value = iso;
    }
}

async function loadDailyOutput() {
    try {
        const res = await axios.get(
            `${BASE}/dashboard/daily-output?end_date=${chartEndDate.value}`,
            { headers: headers() },
        );
        dailyOutput.value = res.data;
    } catch (e) {
        // silently fail for chart reload
    }
}

async function loadAll() {
    loading.value = true;
    error.value = null;
    try {
        const [sumRes, dailyRes, actRes, txRes] = await Promise.all([
            axios.get(`${BASE}/dashboard/summary`, { headers: headers() }),
            axios.get(
                `${BASE}/dashboard/daily-output?end_date=${chartEndDate.value}`,
                { headers: headers() },
            ),
            axios.get(`${BASE}/dashboard/recent-activity`, {
                headers: headers(),
            }),
            axios.get(`${BASE}/transformations/?status=in_progress`, {
                headers: headers(),
            }),
        ]);
        summary.value = sumRes.data;
        dailyOutput.value = dailyRes.data;
        recentActivity.value = actRes.data;
        activeTransformations.value = txRes.data;
    } catch (e) {
        error.value = "Failed to load dashboard data.";
    } finally {
        loading.value = false;
    }
}

onMounted(loadAll);

watch(chartEndDate, () => {
    loadDailyOutput();
});

const stageSummaries = computed(() => {
    if (!summary.value?.stages) return [];
    return summary.value.stages.map((s) => ({
        key: s.stage_name,
        label: s.stage_name.charAt(0) + s.stage_name.slice(1).toLowerCase(),
        icon: s.icon || DEFAULT_STAGE_ICON,
        color: s.color || DEFAULT_STAGE_COLOR,
        count: s.batch_count,
        total_kg: Number(s.total_remaining_kg ?? 0),
    }));
});

const kpis = computed(() => {
    if (!summary.value)
        return {
            total_batches: 0,
            active_transformations: 0,
            avg_yield: null,
            total_kg: 0,
        };
    return {
        total_batches:
            summary.value.stages?.reduce((acc, s) => acc + s.batch_count, 0) ??
            0,
        active_transformations: summary.value.active_transformation_count ?? 0,
        avg_yield:
            summary.value.avg_yield_rate_30d != null
                ? Number(summary.value.avg_yield_rate_30d).toFixed(1)
                : null,
        total_kg: Number(summary.value.total_kg_in_pipeline ?? 0),
    };
});

const hasOutputData = computed(() =>
    dailyOutput.value.some((d) => d.total_output_kg > 0),
);

const chartData = computed(() => ({
    labels: dailyOutput.value.map((d) => d.date_label),
    datasets: [
        {
            data: dailyOutput.value.map((d) => d.total_output_kg),
            backgroundColor: "#4A6741",
            borderRadius: 6,
            barPercentage: 0.7,
        },
    ],
}));

function externalTooltipHandler(context) {
    const { chart, tooltip } = context;
    let tooltipEl = chart.canvas.parentNode.querySelector(
        ".chartjs-custom-tooltip",
    );

    if (!tooltipEl) {
        tooltipEl = document.createElement("div");
        tooltipEl.classList.add("chartjs-custom-tooltip");
        chart.canvas.parentNode.appendChild(tooltipEl);
    }

    if (tooltip.opacity === 0) {
        tooltipEl.style.opacity = "0";
        tooltipEl.style.pointerEvents = "none";
        return;
    }

    const dataIndex = tooltip.dataPoints?.[0]?.dataIndex;
    if (dataIndex == null) return;

    const item = dailyOutput.value[dataIndex];
    if (!item) return;

    let html = `<div class="tooltip-title">${item.date_label}</div>`;
    html += `<div class="tooltip-total">${formatKg(item.total_output_kg)}</div>`;

    if (item.stages && item.stages.length > 0) {
        html += '<div class="tooltip-stages">';
        for (const s of item.stages) {
            const color = s.stage_color || "#888";
            html += `<div class="tooltip-stage-row">
                <span class="tooltip-swatch" style="background:${color}"></span>
                <span class="tooltip-stage-name">${s.stage_name}</span>
                <span class="tooltip-stage-kg">${formatKg(s.output_kg)}</span>
            </div>`;
        }
        html += "</div>";
    }

    tooltipEl.innerHTML = html;
    tooltipEl.style.opacity = "1";
    tooltipEl.style.pointerEvents = "auto";

    const isMobile = window.innerWidth < 768;
    if (isMobile) {
        tooltipEl.style.left = "0";
        tooltipEl.style.right = "0";
        tooltipEl.style.bottom = "0";
        tooltipEl.style.top = "auto";
        tooltipEl.style.transform = "none";
        tooltipEl.style.width = "100%";
        tooltipEl.classList.add("mobile");
    } else {
        tooltipEl.classList.remove("mobile");
        tooltipEl.style.width = "";
        tooltipEl.style.right = "";
        tooltipEl.style.bottom = "";
        const left = tooltip.caretX;
        const top = tooltip.caretY;
        tooltipEl.style.left = left + "px";
        tooltipEl.style.top = top + "px";
        tooltipEl.style.transform = "translate(-50%, -110%)";
    }
}

const chartOptions = computed(() => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        tooltip: {
            enabled: false,
            external: externalTooltipHandler,
        },
    },
    scales: {
        x: {
            ticks: { maxRotation: 45, autoSkip: false, font: { size: 11 } },
            grid: { display: false },
        },
        y: {
            beginAtZero: true,
            ticks: { font: { size: 11 } },
            grid: { color: "rgba(0,0,0,0.05)" },
        },
    },
}));

function formatKg(kg) {
    const n = Number(kg);
    if (kg == null || isNaN(n)) return "—";
    if (n >= 1000) return (n / 1000).toFixed(1) + " t";
    return n.toFixed(1) + " kg";
}

function formatDate(dateStr) {
    if (!dateStr) return "—";
    return new Date(dateStr).toLocaleDateString("en-IN", {
        day: "numeric",
        month: "short",
    });
}

function activityIcon(type) {
    const map = {
        harvest: "bi-plus-circle-fill",
        batch_created: "bi-plus-circle-fill",
        transformation_complete: "bi-check-circle-fill",
        transformation_completed: "bi-check-circle-fill",
        transformation_started: "bi-play-circle-fill",
        batch_moved: "bi-arrow-right-circle-fill",
    };
    return map[type] ?? "bi-circle-fill";
}

function activityColor(type) {
    const map = {
        harvest: "var(--moss)",
        batch_created: "var(--moss)",
        transformation_complete: "var(--sienna)",
        transformation_completed: "var(--sienna)",
        transformation_started: "var(--harvest)",
        batch_moved: "#6f42c1",
    };
    return map[type] ?? "var(--text-secondary)";
}

function goToTransformation(id) {
    router.push({ name: "transformation-detail", params: { id } });
}

function newTransformation() {
    router.push({ name: "transformations", query: { new: "true" } });
}
</script>

<template>
    <div class="dashboard-page">
        <!-- PAGE HEADER -->
        <div class="page-header animate-fade-in-up">
            <div>
                <h2 class="page-title">
                    Welcome back{{ auth.name ? ", " + auth.name : "" }}
                </h2>
                <p class="page-subtitle">
                    Here's what's happening on the farm today.
                </p>
            </div>
            <button class="btn-add" @click="newTransformation">
                <i class="bi bi-plus-lg"></i>
                <span>New Transformation</span>
            </button>
        </div>

        <!-- ERROR -->
        <div v-if="error" class="alert-banner animate-fade-in-up">
            <i class="bi bi-exclamation-triangle-fill"></i> {{ error }}
        </div>

        <!-- LOADING -->
        <div v-if="loading" class="loading-state animate-fade-in-up">
            <div class="spinner-border text-secondary" role="status"></div>
            <span>Loading dashboard…</span>
        </div>

        <template v-else>
            <!-- STAGE SUMMARY BAR -->
            <div class="stage-bar animate-fade-in-up animate-delay-1">
                <div
                    v-for="stage in stageSummaries"
                    :key="stage.key"
                    class="stage-tile"
                    :style="{
                        borderLeftColor: stage.color,
                        '--stage-color': stage.color,
                    }"
                >
                    <i class="bi" :class="stage.icon + ' stage-icon'"></i>
                    <div class="stage-label">{{ stage.label }}</div>
                    <div class="stage-count">{{ stage.count }}</div>
                    <div class="stage-kg">{{ formatKg(stage.total_kg) }}</div>
                </div>
            </div>

            <!-- CHARTS ROW -->
            <div class="charts-row animate-fade-in-up animate-delay-2">
                <!-- OUTPUT TREND -->
                <div class="content-panel chart-panel">
                    <div class="panel-header">
                        <span class="panel-title">Output (7 Days)</span>
                    </div>
                    <div class="date-picker-row">
                        <button
                            class="btn-date-nav"
                            @click="shiftDate(-7)"
                            title="Previous 7 days"
                        >
                            <i class="bi bi-chevron-left"></i>
                        </button>
                        <span class="date-range-label">{{
                            dateRangeLabel
                        }}</span>
                        <button
                            class="btn-date-nav"
                            @click="shiftDate(7)"
                            :disabled="isEndDateToday"
                            title="Next 7 days"
                        >
                            <i class="bi bi-chevron-right"></i>
                        </button>
                        <input
                            type="date"
                            v-model="chartEndDate"
                            :max="todayStr"
                            class="date-picker-input"
                        />
                    </div>
                    <div class="panel-body">
                        <div
                            v-if="!hasOutputData"
                            class="empty-state small-empty"
                        >
                            <i class="bi bi-bar-chart"></i>
                            <p>No output data for this period</p>
                        </div>
                        <div v-else class="bar-chart-wrapper">
                            <Bar :data="chartData" :options="chartOptions" />
                        </div>
                    </div>
                </div>

                <!-- WEIGHT BY STAGE -->
                <div class="content-panel chart-panel">
                    <div class="panel-header">
                        <span class="panel-title">Weight by Stage</span>
                    </div>
                    <div class="panel-body">
                        <div
                            v-if="!stageSummaries.some((s) => s.total_kg > 0)"
                            class="empty-state small-empty"
                        >
                            <i class="bi bi-pie-chart"></i>
                            <p>No batches in pipeline</p>
                        </div>
                        <div v-else class="stage-weight-list">
                            <div
                                v-for="stage in stageSummaries.filter(
                                    (s) => s.total_kg > 0,
                                )"
                                :key="stage.key"
                                class="stage-weight-row"
                            >
                                <span
                                    class="stage-weight-badge"
                                    :style="{ background: stage.color }"
                                    >{{ stage.label }}</span
                                >
                                <div class="stage-weight-bar-wrap">
                                    <div
                                        class="stage-weight-bar"
                                        :style="{
                                            background: stage.color,
                                            width:
                                                Math.max(
                                                    4,
                                                    Math.round(
                                                        (stage.total_kg /
                                                            Math.max(
                                                                ...stageSummaries.map(
                                                                    (s) =>
                                                                        s.total_kg,
                                                                ),
                                                                1,
                                                            )) *
                                                            100,
                                                    ),
                                                ) + '%',
                                        }"
                                    ></div>
                                </div>
                                <span class="stage-weight-val">{{
                                    formatKg(stage.total_kg)
                                }}</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- KPI CARDS -->
                <div class="kpi-stack">
                    <div class="kpi-card animate-fade-in-up animate-delay-2">
                        <div class="kpi-icon kpi-green">
                            <i class="bi bi-layers"></i>
                        </div>
                        <div class="kpi-body">
                            <div class="kpi-value">
                                {{ kpis.total_batches }}
                            </div>
                            <div class="kpi-label">Batches in Pipeline</div>
                        </div>
                    </div>
                    <div class="kpi-card animate-fade-in-up animate-delay-2">
                        <div class="kpi-icon kpi-orange">
                            <i class="bi bi-arrow-repeat"></i>
                        </div>
                        <div class="kpi-body">
                            <div class="kpi-value">
                                {{ kpis.active_transformations }}
                            </div>
                            <div class="kpi-label">Active Transformations</div>
                        </div>
                    </div>
                    <div class="kpi-card animate-fade-in-up animate-delay-2">
                        <div class="kpi-icon kpi-blue">
                            <i class="bi bi-graph-up-arrow"></i>
                        </div>
                        <div class="kpi-body">
                            <div class="kpi-value">
                                {{
                                    kpis.avg_yield != null
                                        ? kpis.avg_yield + "%"
                                        : "—"
                                }}
                            </div>
                            <div class="kpi-label">Avg Yield Rate (30d)</div>
                        </div>
                    </div>
                    <div class="kpi-card animate-fade-in-up animate-delay-2">
                        <div class="kpi-icon kpi-purple">
                            <i class="bi bi-weight"></i>
                        </div>
                        <div class="kpi-body">
                            <div class="kpi-value">
                                {{ formatKg(kpis.total_kg) }}
                            </div>
                            <div class="kpi-label">
                                Total Weight in Pipeline
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- BOTTOM ROW -->
            <div class="bottom-row animate-fade-in-up animate-delay-3">
                <!-- ACTIVE TRANSFORMATIONS -->
                <div class="content-panel">
                    <div class="panel-header">
                        <span class="panel-title">Active Transformations</span>
                        <button
                            class="btn-panel-action"
                            @click="newTransformation"
                        >
                            <i class="bi bi-plus-lg"></i> New
                        </button>
                    </div>
                    <div class="panel-body no-pad">
                        <div
                            v-if="!activeTransformations.length"
                            class="empty-state"
                        >
                            <i class="bi bi-arrow-repeat"></i>
                            <p>No active transformations</p>
                            <button
                                class="btn-empty-action"
                                @click="newTransformation"
                            >
                                Start one
                            </button>
                        </div>
                        <div
                            v-for="tx in activeTransformations"
                            :key="tx.id"
                            class="tx-row"
                            @click="goToTransformation(tx.id)"
                        >
                            <div class="tx-id">T-{{ tx.id }}</div>
                            <div class="tx-info">
                                <div class="tx-type">
                                    {{
                                        tx.type_name ??
                                        tx.transformation_type?.name ??
                                        "Transformation"
                                    }}
                                </div>
                                <div class="tx-meta">
                                    Started {{ formatDate(tx.from_date) }}
                                    <template v-if="tx.batch_codes?.length">
                                        &middot;
                                        {{
                                            tx.batch_codes
                                                .slice(0, 2)
                                                .join(", ")
                                        }}{{
                                            tx.batch_codes.length > 2
                                                ? " +" +
                                                  (tx.batch_codes.length - 2)
                                                : ""
                                        }}
                                    </template>
                                </div>
                            </div>
                            <span class="status-dot active-dot"></span>
                        </div>
                    </div>
                </div>

                <!-- RECENT ACTIVITY -->
                <div class="content-panel">
                    <div class="panel-header">
                        <span class="panel-title">Recent Activity</span>
                    </div>
                    <div class="panel-body no-pad">
                        <div v-if="!recentActivity.length" class="empty-state">
                            <i class="bi bi-clock-history"></i>
                            <p>No recent activity</p>
                        </div>
                        <div
                            v-for="(item, i) in recentActivity"
                            :key="i"
                            class="activity-row"
                        >
                            <div
                                class="activity-icon"
                                :style="{
                                    color: activityColor(item.event_type),
                                }"
                            >
                                <i
                                    class="bi"
                                    :class="activityIcon(item.event_type)"
                                ></i>
                            </div>
                            <div class="activity-body">
                                <div class="activity-desc">
                                    {{ item.description }}
                                </div>
                                <div class="activity-time">
                                    {{ formatDate(item.date) }}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </template>
    </div>
</template>

<style scoped>
.dashboard-page {
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
    min-height: 100%;
}

/* -- PAGE HEADER -- */
.page-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 1rem;
    flex-wrap: wrap;
}
.page-title {
    font-family: var(--font-display);
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0 0 0.2rem;
}
.page-subtitle {
    font-size: 0.9rem;
    color: var(--text-secondary);
    margin: 0;
}
.btn-add {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.5rem 1.1rem;
    background: var(--moss);
    color: #fff;
    border: none;
    border-radius: 8px;
    font-size: 0.9rem;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
    transition: opacity 0.15s;
}
.btn-add:hover {
    opacity: 0.88;
}

/* -- ALERT -- */
.alert-banner {
    background: #fff3cd;
    border: 1px solid #ffc107;
    border-radius: 8px;
    padding: 0.75rem 1rem;
    color: #856404;
    font-size: 0.9rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* -- LOADING -- */
.loading-state {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 3rem;
    justify-content: center;
    color: var(--text-secondary);
}

/* ==============================
   STAGE BAR
============================== */
.stage-bar {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
    gap: 0.6rem;
}
.stage-tile {
    border-radius: 10px;
    padding: 0.85rem 0.5rem 0.75rem;
    text-align: center;
    color: var(--text-primary);
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.2rem;
    border-left: 4px solid var(--stage-color, #b0b8c1);
    background: color-mix(in srgb, var(--stage-color) 8%, var(--bg-card, #fff));
}
.stage-tile .stage-icon {
    font-size: 1.3rem;
    color: var(--stage-color);
}
.stage-label {
    font-size: 0.72rem;
    font-weight: 600;
    opacity: 0.9;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
.stage-count {
    font-size: 1.5rem;
    font-weight: 700;
    line-height: 1;
}
.stage-kg {
    font-size: 0.72rem;
    opacity: 0.85;
}

/* ==============================
   CHARTS ROW
============================== */
.charts-row {
    display: grid;
    grid-template-columns: 1fr 1fr auto;
    gap: 1rem;
    align-items: start;
}

/* -- Content panel -- */
.content-panel {
    background: var(--surface, #fff);
    border: 1px solid var(--border-light, #e5e7eb);
    border-radius: 12px;
    overflow: hidden;
}
.panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.85rem 1rem;
    border-bottom: 1px solid var(--border-light, #e5e7eb);
}
.panel-title {
    font-weight: 600;
    font-size: 0.92rem;
    color: var(--text-primary);
}
.panel-body {
    padding: 1rem;
}
.panel-body.no-pad {
    padding: 0;
}
.btn-panel-action {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.3rem 0.7rem;
    background: var(--moss);
    color: #fff;
    border: none;
    border-radius: 6px;
    font-size: 0.8rem;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 0.15s;
}
.btn-panel-action:hover {
    opacity: 0.88;
}

/* -- Date picker row -- */
.date-picker-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    border-bottom: 1px solid var(--border-light, #e5e7eb);
    background: var(--surface, #fff);
}
.btn-date-nav {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    border: 1px solid var(--border-light, #e5e7eb);
    border-radius: 6px;
    background: var(--surface, #fff);
    color: var(--text-primary);
    cursor: pointer;
    font-size: 0.8rem;
    transition:
        background 0.12s,
        opacity 0.12s;
}
.btn-date-nav:hover:not(:disabled) {
    background: var(--surface-hover, #f3f4f6);
}
.btn-date-nav:disabled {
    opacity: 0.4;
    cursor: not-allowed;
}
.date-range-label {
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text-primary);
    min-width: 120px;
    text-align: center;
}
.date-picker-input {
    margin-left: auto;
    border: 1px solid var(--border-light, #e5e7eb);
    border-radius: 6px;
    padding: 0.25rem 0.5rem;
    font-size: 0.78rem;
    color: var(--text-primary);
    background: var(--surface, #fff);
    cursor: pointer;
}
.date-picker-input:focus {
    outline: 2px solid var(--moss);
    outline-offset: -1px;
}

/* -- Bar chart wrapper (Chart.js) -- */
.bar-chart-wrapper {
    position: relative;
    height: 200px;
}

/* -- Custom tooltip (Chart.js external) -- */
:deep(.chartjs-custom-tooltip) {
    position: absolute;
    background: rgba(30, 30, 30, 0.88);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    color: #fff;
    border-radius: 8px;
    padding: 0.6rem 0.8rem;
    font-size: 0.78rem;
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.15s ease;
    z-index: 10;
    min-width: 140px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}
:deep(.chartjs-custom-tooltip.mobile) {
    border-radius: 8px 8px 0 0;
    position: absolute;
}
:deep(.tooltip-title) {
    font-weight: 700;
    font-size: 0.82rem;
    margin-bottom: 0.2rem;
}
:deep(.tooltip-total) {
    font-size: 1rem;
    font-weight: 700;
    margin-bottom: 0.35rem;
    color: #a8e6a0;
}
:deep(.tooltip-stages) {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
    border-top: 1px solid rgba(255, 255, 255, 0.15);
    padding-top: 0.3rem;
}
:deep(.tooltip-stage-row) {
    display: flex;
    align-items: center;
    gap: 0.4rem;
}
:deep(.tooltip-swatch) {
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 3px;
    flex-shrink: 0;
}
:deep(.tooltip-stage-name) {
    flex: 1;
    font-size: 0.74rem;
    opacity: 0.9;
}
:deep(.tooltip-stage-kg) {
    font-weight: 600;
    font-size: 0.74rem;
}

/* -- Stage weight list -- */
.stage-weight-list {
    display: flex;
    flex-direction: column;
    gap: 0.55rem;
}
.stage-weight-row {
    display: flex;
    align-items: center;
    gap: 0.6rem;
}
.stage-weight-badge {
    font-size: 0.7rem;
    font-weight: 600;
    color: #fff;
    border-radius: 4px;
    padding: 0.15rem 0.45rem;
    min-width: 56px;
    text-align: center;
}
.stage-weight-bar-wrap {
    flex: 1;
    height: 10px;
    background: var(--border-light, #e5e7eb);
    border-radius: 5px;
    overflow: hidden;
}
.stage-weight-bar {
    height: 100%;
    border-radius: 5px;
    transition: width 0.4s ease;
}
.stage-weight-val {
    font-size: 0.78rem;
    font-weight: 600;
    color: var(--text-primary);
    min-width: 52px;
    text-align: right;
}

/* -- KPI stack -- */
.kpi-stack {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
    min-width: 200px;
}
.kpi-card {
    background: var(--surface, #fff);
    border: 1px solid var(--border-light, #e5e7eb);
    border-radius: 10px;
    padding: 0.75rem 1rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
}
.kpi-icon {
    width: 36px;
    height: 36px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    flex-shrink: 0;
}
.kpi-green {
    background: #d1fae5;
    color: #065f46;
}
.kpi-orange {
    background: #ffedd5;
    color: #9a3412;
}
.kpi-blue {
    background: #dbeafe;
    color: #1e40af;
}
.kpi-purple {
    background: #ede9fe;
    color: #5b21b6;
}
.kpi-value {
    font-size: 1.2rem;
    font-weight: 700;
    color: var(--text-primary);
    line-height: 1;
}
.kpi-label {
    font-size: 0.72rem;
    color: var(--text-secondary);
    margin-top: 0.1rem;
}

/* ==============================
   BOTTOM ROW
============================== */
.bottom-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
    align-items: start;
}

/* -- Transaction rows -- */
.tx-row {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    border-bottom: 1px solid var(--border-light, #e5e7eb);
    cursor: pointer;
    transition: background 0.12s;
}
.tx-row:last-child {
    border-bottom: none;
}
.tx-row:hover {
    background: var(--surface-hover, #f9fafb);
}
.tx-id {
    font-size: 0.8rem;
    font-weight: 700;
    color: var(--moss);
    min-width: 42px;
}
.tx-info {
    flex: 1;
    min-width: 0;
}
.tx-type {
    font-size: 0.88rem;
    font-weight: 600;
    color: var(--text-primary);
}
.tx-meta {
    font-size: 0.75rem;
    color: var(--text-secondary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
}
.active-dot {
    background: #22c55e;
}

/* -- Activity rows -- */
.activity-row {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    border-bottom: 1px solid var(--border-light, #e5e7eb);
}
.activity-row:last-child {
    border-bottom: none;
}
.activity-icon {
    font-size: 1rem;
    margin-top: 0.1rem;
    flex-shrink: 0;
}
.activity-desc {
    font-size: 0.85rem;
    color: var(--text-primary);
}
.activity-time {
    font-size: 0.72rem;
    color: var(--text-secondary);
    margin-top: 0.15rem;
}

/* -- Empty state -- */
.empty-state {
    text-align: center;
    padding: 2rem 1rem;
    color: var(--text-secondary);
}
.empty-state i {
    font-size: 2rem;
    display: block;
    margin-bottom: 0.5rem;
}
.empty-state p {
    margin: 0 0 0.75rem;
    font-size: 0.9rem;
}
.small-empty {
    padding: 1.5rem 0.5rem;
}
.small-empty i {
    font-size: 1.5rem;
}
.btn-empty-action {
    padding: 0.4rem 1rem;
    background: var(--moss);
    color: #fff;
    border: none;
    border-radius: 6px;
    font-size: 0.85rem;
    cursor: pointer;
}

/* ==============================
   ANIMATIONS
============================== */
@keyframes fade-in-up {
    from {
        opacity: 0;
        transform: translateY(12px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
.animate-fade-in-up {
    animation: fade-in-up 0.35s ease both;
}
.animate-delay-1 {
    animation-delay: 0.08s;
}
.animate-delay-2 {
    animation-delay: 0.16s;
}
.animate-delay-3 {
    animation-delay: 0.24s;
}

/* ==============================
   RESPONSIVE
============================== */
@media (max-width: 1199.98px) {
    .charts-row {
        grid-template-columns: 1fr 1fr;
    }
    .kpi-stack {
        grid-column: 1 / -1;
        flex-direction: row;
        flex-wrap: wrap;
        min-width: unset;
    }
    .kpi-card {
        flex: 1 1 calc(50% - 0.3rem);
        min-width: 160px;
    }
}

@media (max-width: 991.98px) {
    .bottom-row {
        grid-template-columns: 1fr;
    }
}

@media (max-width: 767.98px) {
    .dashboard-page {
        padding: 1rem;
        gap: 1rem;
    }
    .stage-bar {
        gap: 0.4rem;
    }
    .stage-tile {
        padding: 0.6rem 0.3rem;
    }
    .stage-count {
        font-size: 1.2rem;
    }
    .charts-row {
        grid-template-columns: 1fr;
    }
    .kpi-stack {
        flex-direction: row;
        flex-wrap: wrap;
    }
    .kpi-card {
        flex: 1 1 calc(50% - 0.3rem);
    }
    .page-title {
        font-size: 1.3rem;
    }
    .date-picker-row {
        flex-wrap: wrap;
    }
    .date-picker-input {
        margin-left: 0;
        flex: 1;
        min-width: 0;
    }
}

@media (max-width: 479.98px) {
    .stage-label {
        display: none;
    }
    .stage-kg {
        display: none;
    }
}
</style>

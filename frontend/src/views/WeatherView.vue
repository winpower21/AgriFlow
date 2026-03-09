<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";
import { useWeatherStore } from "@/stores/weather";

const weather = useWeatherStore();

const searchInput = ref(null);
const showDropdown = ref(false);

/* ── Search ─────────────────────────────────────────────────────────── */

function onInput(e) {
    const val = e.target.value;
    weather.searchLocations(val);
    showDropdown.value = val.length >= 2;
}

function onFocus() {
    if (weather.searchResults.length > 0) showDropdown.value = true;
}

function onBlur() {
    setTimeout(() => {
        showDropdown.value = false;
    }, 200);
}

function selectResult(item) {
    showDropdown.value = false;
    if (item.source === "db") {
        weather.selectDbLocation(item);
    } else {
        weather.selectGooglePrediction(item);
    }
}

async function onSearchOnline() {
    await weather.searchOnline(weather.searchQuery);
    showDropdown.value = weather.searchResults.length > 0;
}

function clearSearch() {
    weather.clearSearch();
    showDropdown.value = false;
    if (searchInput.value) searchInput.value.focus();
}

/* ── Weather helpers ────────────────────────────────────────────────── */

function tempValue(tempObj) {
    if (!tempObj) return "--";
    const deg = tempObj.degrees ?? tempObj.value;
    return deg != null ? Math.round(deg) : "--";
}

function weatherIcon(condition) {
    if (!condition) return "bi-cloud";
    const desc = (
        condition.description?.text ||
        condition.type ||
        ""
    ).toLowerCase();
    if (desc.includes("clear") || desc.includes("sunny")) return "bi-sun";
    if (desc.includes("cloud") && desc.includes("part")) return "bi-cloud-sun";
    if (desc.includes("cloud")) return "bi-clouds";
    if (desc.includes("rain") || desc.includes("drizzle"))
        return "bi-cloud-rain";
    if (desc.includes("thunder") || desc.includes("storm"))
        return "bi-cloud-lightning-rain";
    if (desc.includes("snow")) return "bi-snow";
    if (desc.includes("fog") || desc.includes("mist") || desc.includes("haze"))
        return "bi-cloud-fog";
    return "bi-cloud";
}

function googleIconUrl(condition) {
    if (!condition) return null;
    const base = condition.iconBaseUri || condition.icon_base_uri;
    return base ? base + ".png" : null;
}

function weatherDescription(condition) {
    if (!condition) return "Unknown";
    if (condition.description?.text) return condition.description.text;
    if (condition.type)
        return condition.type
            .replace(/_/g, " ")
            .replace(/\b\w/g, (c) => c.toUpperCase());
    return "Unknown";
}

function formatHour(isoString) {
    if (!isoString) return "";
    return new Date(isoString).toLocaleTimeString("en-IN", {
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
    });
}

function formatDateTime(dt) {
    if (!dt) return "--";
    return new Date(dt).toLocaleString("en-IN", {
        day: "2-digit",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
    });
}

/* ── Computed from store ────────────────────────────────────────────── */

const currentCondition = computed(
    () => weather.currentWeather?.weatherCondition ?? null
);
const currentIcon = computed(() => googleIconUrl(currentCondition.value));
const currentIconFallback = computed(() => weatherIcon(currentCondition.value));

const currentTemp = computed(() => {
    if (!weather.currentWeather) return "--";
    return tempValue(weather.currentWeather.temperature);
});

const feelsLike = computed(() => {
    if (!weather.currentWeather?.feelsLikeTemperature) return "--";
    return tempValue(weather.currentWeather.feelsLikeTemperature);
});

const humidity = computed(
    () => weather.currentWeather?.relativeHumidity ?? "--"
);
const uvIndex = computed(() => weather.currentWeather?.uvIndex ?? "--");

const visibility = computed(() => {
    const vis = weather.currentWeather?.visibility;
    if (!vis) return "--";
    return `${vis.distance ?? vis.value ?? "--"} ${vis.unit ?? "km"}`;
});

const pressure = computed(() => {
    const p = weather.currentWeather?.airPressure;
    if (!p) return "--";
    return `${Math.round(p.meanSeaLevelMillibars ?? p.value ?? 0)}`;
});

const currentWind = computed(() => {
    const w = weather.currentWeather?.wind;
    if (!w) return { speed: "--", dir: "" };
    const speed = w.speed?.value ?? w.speed?.kilometers_per_hour ?? 0;
    return { speed: Math.round(speed), dir: w.direction?.cardinal ?? "" };
});

const precipitationProbability = computed(() => {
    const p = weather.currentWeather?.precipitation;
    return p?.probability?.percent ?? p?.probability ?? null;
});

/* ── Lifecycle ──────────────────────────────────────────────────────── */

onMounted(() => weather.fetchStoredLocations());
onUnmounted(() => weather.clearSearch());
</script>

<template>
    <div class="weather-page">
        <!-- Header -->
        <div class="weather-header">
            <div class="d-flex align-items-center justify-content-between mb-1">
                <div>
                    <h1 class="page-title">Weather</h1>
                    <p class="page-subtitle" v-if="!weather.hasLocation">
                        Select a location or search to view weather
                    </p>
                    <button
                        v-else
                        class="change-location-btn"
                        @click="weather.clearWeather()"
                    >
                        <i class="bi bi-arrow-left-short"></i>
                        Change location
                    </button>
                </div>
            </div>

            <!-- Search bar -->
            <div class="search-container">
                <div
                    class="search-wrapper"
                    :class="{
                        active: showDropdown && weather.searchResults.length,
                    }"
                >
                    <i class="bi bi-search search-icon"></i>
                    <input
                        ref="searchInput"
                        type="text"
                        class="search-input"
                        placeholder="Search city, district, or region..."
                        :value="weather.searchQuery"
                        @input="onInput"
                        @focus="onFocus"
                        @blur="onBlur"
                        autocomplete="off"
                        spellcheck="false"
                    />
                    <span v-if="weather.isSearching" class="search-spinner">
                        <span class="spinner-border spinner-border-sm"></span>
                    </span>
                    <button
                        v-else-if="weather.searchQuery"
                        class="search-clear"
                        @click="clearSearch"
                    >
                        <i class="bi bi-x-lg"></i>
                    </button>
                </div>

                <!-- Autocomplete dropdown -->
                <Transition name="dropdown">
                    <div
                        v-if="showDropdown && weather.searchResults.length"
                        class="search-dropdown"
                    >
                        <button
                            v-for="item in weather.searchResults"
                            :key="item.id ?? item.place_id"
                            class="dropdown-item"
                            @mousedown.prevent="selectResult(item)"
                        >
                            <i
                                class="bi me-2"
                                :class="
                                    item.source === 'db'
                                        ? 'bi-database text-sage'
                                        : 'bi-geo-alt text-sienna'
                                "
                            ></i>
                            <div class="dropdown-text">
                                <span class="dropdown-main">
                                    {{ item.city
                                    }}<span
                                        v-if="item.state"
                                        class="dropdown-state"
                                        >, {{ item.state }}</span
                                    >
                                </span>
                                <span
                                    v-if="
                                        item.source === 'google' &&
                                        item.description
                                    "
                                    class="dropdown-secondary"
                                >
                                    {{ item.description }}
                                </span>
                            </div>
                        </button>

                        <!-- Search online — only when Google not yet searched -->
                        <button
                            v-if="!weather.googleWasSearched"
                            class="dropdown-item dropdown-search-online"
                            @mousedown.prevent="onSearchOnline"
                        >
                            <i class="bi bi-cloud-download me-2"></i>
                            <span>Search online</span>
                        </button>
                    </div>
                </Transition>
            </div>
        </div>

        <!-- Error -->
        <div v-if="weather.error" class="error-bar animate-fade-in-up">
            <i class="bi bi-exclamation-circle me-2"></i>
            {{ weather.error }}
        </div>

        <!-- Loading -->
        <div v-if="weather.isLoadingWeather" class="loading-state animate-fade-in">
            <div class="loading-card">
                <div class="spinner-border text-moss mb-3" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="loading-text">Fetching weather data...</p>
            </div>
        </div>

        <!-- Weather content -->
        <div
            v-else-if="weather.hasWeather && weather.selectedLocation"
            class="weather-content"
        >
            <!-- Location badge + cache info -->
            <div class="location-badge animate-fade-in-up">
                <i class="bi bi-geo-alt-fill"></i>
                <span>
                    {{ weather.selectedLocation.city
                    }}<template v-if="weather.selectedLocation.state"
                        >, {{ weather.selectedLocation.state }}</template
                    >
                </span>
                <span class="badge-fetched-at">
                    <i class="bi bi-clock ms-2 me-1"></i>
                    {{ formatDateTime(weather.selectedWeather?.fetched_at) }}
                    <span
                        v-if="weather.selectedWeather?.is_manual"
                        class="badge-manual ms-1"
                        >manual</span
                    >
                </span>
            </div>

            <!-- Current conditions -->
            <div
                v-if="weather.currentWeather"
                class="current-card animate-fade-in-up animate-delay-1"
            >
                <div class="current-main">
                    <div class="current-temp-group">
                        <div class="current-icon">
                            <img
                                v-if="currentIcon"
                                :src="currentIcon"
                                alt="weather"
                                class="weather-img"
                            />
                            <i
                                v-else
                                :class="currentIconFallback"
                                class="weather-icon-fallback"
                            ></i>
                        </div>
                        <div class="current-temp">
                            <span class="temp-value">{{ currentTemp }}</span>
                            <span class="temp-unit">&deg;C</span>
                        </div>
                    </div>
                    <div class="current-details">
                        <p class="condition-text">
                            {{ weatherDescription(currentCondition) }}
                        </p>
                        <p class="feels-like">Feels like {{ feelsLike }}&deg;</p>
                        <button
                            class="refresh-btn"
                            :disabled="weather.isLoadingWeather"
                            @click="
                                weather.fetchWeatherForLocation(
                                    weather.selectedLocation.id,
                                    true
                                )
                            "
                            title="Refresh weather data"
                        >
                            <i
                                class="bi bi-arrow-clockwise"
                                :class="{ spin: weather.isLoadingWeather }"
                            ></i>
                            Refresh
                        </button>
                    </div>
                </div>

                <!-- Metrics grid -->
                <div class="metrics-grid">
                    <div class="metric">
                        <i class="bi bi-droplet"></i>
                        <div class="metric-info">
                            <span class="metric-value">{{ humidity }}%</span>
                            <span class="metric-label">Humidity</span>
                        </div>
                    </div>
                    <div class="metric">
                        <i class="bi bi-wind"></i>
                        <div class="metric-info">
                            <span class="metric-value"
                                >{{ currentWind.speed }}
                                <small>km/h</small></span
                            >
                            <span class="metric-label"
                                >Wind {{ currentWind.dir }}</span
                            >
                        </div>
                    </div>
                    <div class="metric">
                        <i class="bi bi-sun"></i>
                        <div class="metric-info">
                            <span class="metric-value">{{ uvIndex }}</span>
                            <span class="metric-label">UV Index</span>
                        </div>
                    </div>
                    <div class="metric">
                        <i class="bi bi-speedometer2"></i>
                        <div class="metric-info">
                            <span class="metric-value"
                                >{{ pressure }} <small>mb</small></span
                            >
                            <span class="metric-label">Pressure</span>
                        </div>
                    </div>
                    <div class="metric">
                        <i class="bi bi-eye"></i>
                        <div class="metric-info">
                            <span class="metric-value">{{ visibility }}</span>
                            <span class="metric-label">Visibility</span>
                        </div>
                    </div>
                    <div v-if="precipitationProbability !== null" class="metric">
                        <i class="bi bi-cloud-rain"></i>
                        <div class="metric-info">
                            <span class="metric-value"
                                >{{ precipitationProbability }}%</span
                            >
                            <span class="metric-label">Precipitation</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Hourly forecast strip -->
            <div
                v-if="weather.forecastHours.length"
                class="forecast-section animate-fade-in-up animate-delay-2"
            >
                <h2 class="section-title">Hourly Forecast</h2>
                <div class="hourly-strip">
                    <div
                        v-for="(h, idx) in weather.forecastHours.slice(0, 12)"
                        :key="idx"
                        class="hourly-item"
                    >
                        <span class="hourly-time">{{
                            formatHour(h.interval?.startTime)
                        }}</span>
                        <img
                            v-if="googleIconUrl(h.weatherCondition)"
                            :src="googleIconUrl(h.weatherCondition)"
                            class="hourly-img"
                            alt=""
                        />
                        <i
                            v-else
                            :class="weatherIcon(h.weatherCondition)"
                            class="hourly-icon-fallback"
                        ></i>
                        <span class="hourly-temp">
                            {{
                                h.temperature?.degrees != null
                                    ? Math.round(h.temperature.degrees) + "°"
                                    : "—"
                            }}
                        </span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Saved locations grid (shown when no weather selected) -->
        <div
            v-if="!weather.hasWeather && !weather.isLoadingWeather"
            class="animate-fade-in-up animate-delay-1"
        >
            <template v-if="weather.storedLocations.length">
                <h2 class="section-title">Saved Locations</h2>
                <div class="locations-grid">
                    <button
                        v-for="loc in weather.storedLocations"
                        :key="loc.id"
                        class="location-card"
                        @click="weather.selectDbLocation(loc)"
                    >
                        <i class="bi bi-geo-alt location-card-icon"></i>
                        <div class="location-card-body">
                            <span class="location-card-city">{{ loc.city }}</span>
                            <span
                                v-if="loc.state || loc.country"
                                class="location-card-sub"
                            >
                                {{
                                    [loc.state, loc.country]
                                        .filter(Boolean)
                                        .join(", ")
                                }}
                            </span>
                        </div>
                        <i class="bi bi-chevron-right location-card-arrow"></i>
                    </button>
                </div>
            </template>
            <div
                v-else-if="!weather.error"
                class="empty-state animate-fade-in-up animate-delay-1"
            >
                <div class="empty-illustration">
                    <i class="bi bi-cloud-sun"></i>
                </div>
                <p class="empty-text">Search for a location to get started</p>
            </div>
        </div>
    </div>
</template>

<style scoped>
.weather-page {
    max-width: 720px;
    margin: 0 auto;
    padding: 2rem 1.25rem 3rem;
}

/* ---- Header ---- */
.weather-header {
    margin-bottom: 1.5rem;
}

.page-title {
    font-family: var(--font-display);
    font-size: 2rem;
    color: var(--loam);
    margin: 0;
    line-height: 1.1;
}

.page-subtitle {
    color: var(--text-secondary);
    font-size: 0.9rem;
    margin: 0.35rem 0 0;
}

.change-location-btn {
    display: inline-flex;
    align-items: center;
    background: none;
    border: none;
    color: var(--sage);
    font-family: var(--font-body);
    font-size: 0.85rem;
    font-weight: 500;
    cursor: pointer;
    padding: 0;
    margin-top: 0.35rem;
    transition: color var(--transition-fast);
}

.change-location-btn:hover {
    color: var(--moss);
}

/* ---- Search ---- */
.search-container {
    position: relative;
    margin-top: 1.25rem;
}

.search-wrapper {
    position: relative;
    display: flex;
    align-items: center;
    background: var(--white);
    border: 1.5px solid var(--border);
    border-radius: 12px;
    transition: all var(--transition-fast);
    box-shadow: var(--shadow-sm);
}

.search-wrapper:focus-within,
.search-wrapper.active {
    border-color: var(--sage);
    box-shadow: 0 0 0 3px var(--moss-faded), var(--shadow-md);
}

.search-icon {
    position: absolute;
    left: 1rem;
    color: var(--text-secondary);
    font-size: 0.95rem;
    pointer-events: none;
}

.search-input {
    flex: 1;
    border: none;
    outline: none;
    background: transparent;
    padding: 0.85rem 2.5rem 0.85rem 2.75rem;
    font-family: var(--font-body);
    font-size: 0.95rem;
    color: var(--text-primary);
}

.search-input::placeholder {
    color: var(--border);
}

.search-spinner {
    position: absolute;
    right: 1rem;
    color: var(--sage);
}

.search-clear {
    position: absolute;
    right: 0.75rem;
    background: none;
    border: none;
    color: var(--text-secondary);
    cursor: pointer;
    padding: 0.25rem;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all var(--transition-fast);
}

.search-clear:hover {
    color: var(--sienna);
    background: var(--sienna-faded);
}

/* ---- Dropdown ---- */
.search-dropdown {
    position: absolute;
    top: calc(100% + 6px);
    left: 0;
    right: 0;
    background: var(--white);
    border: 1px solid var(--border-light);
    border-radius: 12px;
    box-shadow: var(--shadow-float);
    z-index: 100;
    overflow: hidden;
}

.dropdown-item {
    display: flex;
    align-items: center;
    width: 100%;
    padding: 0.75rem 1rem;
    background: none;
    border: none;
    border-bottom: 1px solid var(--border-light);
    cursor: pointer;
    text-align: left;
    transition: background var(--transition-fast);
    font-family: var(--font-body);
    color: var(--text-primary);
}

.dropdown-item:last-child {
    border-bottom: none;
}

.dropdown-item:hover {
    background: var(--parchment);
}

.dropdown-search-online {
    color: var(--sage);
    font-size: 0.85rem;
    font-weight: 500;
    border-top: 1px solid var(--border-light);
}

.dropdown-search-online:hover {
    background: rgba(138, 154, 123, 0.06);
    color: var(--moss);
}

.dropdown-text {
    display: flex;
    flex-direction: column;
    min-width: 0;
}

.dropdown-main {
    font-weight: 500;
    font-size: 0.9rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.dropdown-state {
    font-weight: 400;
    color: var(--text-secondary);
}

.dropdown-secondary {
    font-size: 0.8rem;
    color: var(--text-secondary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.text-sage {
    color: var(--sage);
}

.text-sienna {
    color: var(--sienna);
}

.dropdown-enter-active,
.dropdown-leave-active {
    transition: opacity 0.15s ease, transform 0.15s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
    opacity: 0;
    transform: translateY(-4px);
}

/* ---- Error ---- */
.error-bar {
    background: #fdf2f2;
    border: 1px solid #e8c4c4;
    color: #8b3a3a;
    border-radius: 10px;
    padding: 0.75rem 1rem;
    font-size: 0.875rem;
    margin-bottom: 1.25rem;
}

/* ---- Loading ---- */
.loading-state {
    display: flex;
    justify-content: center;
    padding: 4rem 0;
}

.loading-card {
    text-align: center;
}

.loading-text {
    color: var(--text-secondary);
    font-size: 0.9rem;
}

/* ---- Location badge ---- */
.location-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.35rem 0.85rem;
    background: var(--moss-faded);
    color: var(--moss);
    border-radius: 20px;
    font-size: 0.82rem;
    font-weight: 500;
    margin-bottom: 1.25rem;
    flex-wrap: wrap;
}

.badge-fetched-at {
    display: inline-flex;
    align-items: center;
    font-size: 0.75rem;
    opacity: 0.75;
    font-weight: 400;
}

.badge-manual {
    background: rgba(196, 163, 90, 0.2);
    color: #8a6f2a;
    font-size: 0.68rem;
    font-weight: 700;
    padding: 1px 6px;
    border-radius: 10px;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}

/* ---- Current conditions ---- */
.current-card {
    background: var(--white);
    border: 1px solid var(--border-light);
    border-radius: 16px;
    padding: 1.75rem;
    box-shadow: var(--shadow-sm);
    margin-bottom: 1.5rem;
}

.current-main {
    display: flex;
    align-items: center;
    gap: 1.5rem;
    margin-bottom: 1.5rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid var(--border-light);
}

.current-temp-group {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.current-icon {
    flex-shrink: 0;
}

.weather-img {
    width: 64px;
    height: 64px;
    object-fit: contain;
}

.weather-icon-fallback {
    font-size: 3rem;
    color: var(--harvest);
}

.current-temp {
    display: flex;
    align-items: flex-start;
}

.temp-value {
    font-family: var(--font-display);
    font-size: 3.5rem;
    line-height: 1;
    color: var(--loam);
}

.temp-unit {
    font-size: 1.25rem;
    color: var(--text-secondary);
    margin-top: 0.35rem;
    margin-left: 0.1rem;
}

.current-details {
    flex: 1;
    min-width: 0;
}

.condition-text {
    font-size: 1.1rem;
    font-weight: 500;
    color: var(--loam);
    margin: 0 0 0.2rem;
}

.feels-like {
    font-size: 0.85rem;
    color: var(--text-secondary);
    margin: 0 0 0.6rem;
}

.refresh-btn {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 5px 12px;
    border: 1.5px solid var(--border);
    border-radius: 8px;
    background: transparent;
    color: var(--text-secondary);
    font-size: 0.78rem;
    font-weight: 600;
    cursor: pointer;
    transition: all var(--transition-fast);
    font-family: var(--font-body);
}

.refresh-btn:hover:not(:disabled) {
    border-color: var(--moss);
    color: var(--moss);
    background: rgba(74, 103, 65, 0.06);
}

.refresh-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
}

.spin {
    animation: spin 1s linear infinite;
}

@keyframes spin {
    to {
        transform: rotate(360deg);
    }
}

/* ---- Metrics ---- */
.metrics-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
}

.metric {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.6rem;
    border-radius: 10px;
    background: var(--parchment);
}

.metric > i {
    font-size: 1.1rem;
    color: var(--sage);
    flex-shrink: 0;
}

.metric-info {
    display: flex;
    flex-direction: column;
    min-width: 0;
}

.metric-value {
    font-weight: 600;
    font-size: 0.88rem;
    color: var(--loam);
    line-height: 1.2;
}

.metric-value small {
    font-weight: 400;
    font-size: 0.72rem;
    color: var(--text-secondary);
}

.metric-label {
    font-size: 0.72rem;
    color: var(--text-secondary);
    line-height: 1.2;
}

/* ---- Hourly forecast strip ---- */
.forecast-section {
    margin-bottom: 2rem;
}

.section-title {
    font-family: var(--font-display);
    font-size: 1.35rem;
    color: var(--loam);
    margin: 0 0 1rem;
}

.hourly-strip {
    display: flex;
    gap: 8px;
    overflow-x: auto;
    padding-bottom: 6px;
    -webkit-overflow-scrolling: touch;
}

.hourly-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    min-width: 56px;
    padding: 10px 8px;
    background: var(--white);
    border: 1px solid var(--border-light);
    border-radius: 12px;
    font-size: 0.75rem;
    color: var(--text-secondary);
    flex-shrink: 0;
    text-align: center;
    box-shadow: var(--shadow-sm);
}

.hourly-time {
    font-size: 0.7rem;
    opacity: 0.7;
}

.hourly-img {
    width: 28px;
    height: 28px;
    object-fit: contain;
}

.hourly-icon-fallback {
    font-size: 1.15rem;
    color: var(--harvest);
}

.hourly-temp {
    font-weight: 700;
    font-size: 0.88rem;
    color: var(--loam);
}

/* ---- Saved locations grid ---- */
.locations-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
    margin-bottom: 1.5rem;
}

.location-card {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    background: var(--white);
    border: 1px solid var(--border-light);
    border-radius: 12px;
    padding: 0.85rem 1rem;
    cursor: pointer;
    text-align: left;
    font-family: var(--font-body);
    color: var(--text-primary);
    transition: all var(--transition-fast);
    box-shadow: var(--shadow-sm);
    width: 100%;
}

.location-card:hover {
    border-color: var(--sage);
    box-shadow: var(--shadow-md);
    transform: translateY(-1px);
}

.location-card-icon {
    font-size: 1.1rem;
    color: var(--sage);
    flex-shrink: 0;
}

.location-card-body {
    display: flex;
    flex-direction: column;
    min-width: 0;
    flex: 1;
}

.location-card-city {
    font-weight: 600;
    font-size: 0.88rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.location-card-sub {
    font-size: 0.75rem;
    color: var(--text-secondary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.location-card-arrow {
    font-size: 0.85rem;
    color: var(--border);
    flex-shrink: 0;
    transition: color var(--transition-fast);
}

.location-card:hover .location-card-arrow {
    color: var(--sage);
}

/* ---- Empty state ---- */
.empty-state {
    text-align: center;
    padding: 4rem 0;
}

.empty-illustration i {
    font-size: 4rem;
    color: var(--border);
    display: block;
    margin-bottom: 1rem;
}

.empty-text {
    color: var(--text-secondary);
    font-size: 0.95rem;
}

/* ---- Responsive ---- */
@media (max-width: 767.98px) {
    .weather-page {
        padding: 1.25rem 1rem 6rem;
    }

    .page-title {
        font-size: 1.6rem;
    }

    .current-main {
        flex-direction: column;
        align-items: flex-start;
        gap: 0.75rem;
    }

    .metrics-grid {
        grid-template-columns: repeat(2, 1fr);
    }

    .locations-grid {
        grid-template-columns: 1fr;
    }

    .temp-value {
        font-size: 2.75rem;
    }
}

@media (max-width: 575.98px) {
    .metrics-grid {
        grid-template-columns: 1fr 1fr;
        gap: 0.6rem;
    }
}
</style>

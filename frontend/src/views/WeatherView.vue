<script setup>
import { ref, computed, onUnmounted } from "vue";
import { useWeatherStore } from "@/stores/weather";

const weather = useWeatherStore();

const searchInput = ref(null);
const showDropdown = ref(false);

function onInput(e) {
    const val = e.target.value;
    weather.searchLocations(val);
    showDropdown.value = val.length >= 2;
}

function selectPrediction(prediction) {
    showDropdown.value = false;
    weather.selectLocation(prediction);
}

function onFocus() {
    if (weather.predictions.length > 0) {
        showDropdown.value = true;
    }
}

function onBlur() {
    // Delay to allow click on dropdown item
    setTimeout(() => {
        showDropdown.value = false;
    }, 200);
}

function clearSearch() {
    weather.clearAll();
    showDropdown.value = false;
    if (searchInput.value) searchInput.value.focus();
}

function loadSaved(location) {
    weather.loadSavedLocation(location);
}

function removeSaved(placeId) {
    weather.removeSavedLocation(placeId);
}

/* ---- Weather data helpers ---- */

function tempValue(tempObj) {
    if (!tempObj) return "--";
    // Google Weather API returns { degrees, unit } for Celsius
    const deg = tempObj.degrees ?? tempObj.value;
    if (deg === undefined || deg === null) return "--";
    return Math.round(deg);
}

function weatherIcon(condition) {
    if (!condition) return "bi-cloud";
    const iconUri = condition.iconBaseUri || condition.icon_base_uri || "";
    if (iconUri) return null; // We'll use the Google icon
    // Fallback to bootstrap icons based on description
    const desc = (condition.description?.text || condition.type || "").toLowerCase();
    if (desc.includes("clear") || desc.includes("sunny")) return "bi-sun";
    if (desc.includes("cloud") && desc.includes("part")) return "bi-cloud-sun";
    if (desc.includes("cloud")) return "bi-clouds";
    if (desc.includes("rain") || desc.includes("drizzle")) return "bi-cloud-rain";
    if (desc.includes("thunder") || desc.includes("storm")) return "bi-cloud-lightning-rain";
    if (desc.includes("snow")) return "bi-snow";
    if (desc.includes("fog") || desc.includes("mist") || desc.includes("haze")) return "bi-cloud-fog";
    return "bi-cloud";
}

function googleIconUrl(condition) {
    if (!condition) return null;
    const base = condition.iconBaseUri || condition.icon_base_uri;
    if (!base) return null;
    return base + ".png";
}

function weatherDescription(condition) {
    if (!condition) return "Unknown";
    if (condition.description?.text) return condition.description.text;
    if (condition.type) {
        return condition.type
            .replace(/_/g, " ")
            .replace(/\b\w/g, (c) => c.toUpperCase());
    }
    return "Unknown";
}

function windSpeed(wind) {
    if (!wind?.speed?.value && !wind?.speed?.kilometers_per_hour)
        return "--";
    return Math.round(
        wind.speed.value ?? wind.speed.kilometers_per_hour ?? 0,
    );
}

function windDirection(wind) {
    if (!wind?.direction?.cardinal) return "";
    return wind.direction.cardinal;
}

function formatDate(dateObj) {
    if (!dateObj) return "";
    const { year, month, day } = dateObj;
    if (!year) return "";
    const d = new Date(year, (month || 1) - 1, day || 1);
    return d.toLocaleDateString("en-IN", {
        weekday: "short",
        month: "short",
        day: "numeric",
    });
}

function formatShortDay(dateObj) {
    if (!dateObj) return "";
    const { year, month, day } = dateObj;
    if (!year) return "";
    const d = new Date(year, (month || 1) - 1, day || 1);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    d.setHours(0, 0, 0, 0);
    if (d.getTime() === today.getTime()) return "Today";
    const tomorrow = new Date(today);
    tomorrow.setDate(today.getDate() + 1);
    if (d.getTime() === tomorrow.getTime()) return "Tomorrow";
    return d.toLocaleDateString("en-IN", { weekday: "short" });
}

const currentTemp = computed(() => {
    if (!weather.currentWeather) return "--";
    return tempValue(weather.currentWeather.temperature);
});

const currentCondition = computed(() => {
    if (!weather.currentWeather) return null;
    return weather.currentWeather.weatherCondition;
});

const currentIcon = computed(() => {
    return googleIconUrl(currentCondition.value);
});

const currentIconFallback = computed(() => {
    return weatherIcon(currentCondition.value);
});

const humidity = computed(() => {
    return weather.currentWeather?.relativeHumidity ?? "--";
});

const uvIndex = computed(() => {
    return weather.currentWeather?.uvIndex ?? "--";
});

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
    return { speed: windSpeed(w), dir: windDirection(w) };
});

const feelsLike = computed(() => {
    if (!weather.currentWeather?.feelsLikeTemperature) return "--";
    return tempValue(weather.currentWeather.feelsLikeTemperature);
});

const precipitationProbability = computed(() => {
    const p = weather.currentWeather?.precipitation;
    if (!p) return null;
    return p.probability?.percent ?? p.probability ?? null;
});

onUnmounted(() => {
    weather.clearSearch();
});
</script>

<template>
    <div class="weather-page">
        <!-- Header section -->
        <div class="weather-header">
            <div class="d-flex align-items-center justify-content-between mb-1">
                <div>
                    <h1 class="page-title">Weather</h1>
                    <p class="page-subtitle" v-if="!weather.hasLocation">
                        Search for a location to view current conditions and forecast
                    </p>
                </div>
            </div>

            <!-- Search bar -->
            <div class="search-container">
                <div class="search-wrapper" :class="{ active: showDropdown && weather.predictions.length }">
                    <i class="bi bi-search search-icon"></i>
                    <input ref="searchInput" type="text" class="search-input" placeholder="Search city, district, or region..."
                        :value="weather.searchQuery" @input="onInput" @focus="onFocus" @blur="onBlur"
                        autocomplete="off" spellcheck="false" />
                    <span v-if="weather.isSearching" class="search-spinner">
                        <span class="spinner-border spinner-border-sm"></span>
                    </span>
                    <button v-else-if="weather.searchQuery" class="search-clear" @click="clearSearch">
                        <i class="bi bi-x-lg"></i>
                    </button>
                </div>

                <!-- Autocomplete dropdown -->
                <Transition name="dropdown">
                    <div v-if="showDropdown && weather.predictions.length" class="search-dropdown">
                        <button v-for="pred in weather.predictions" :key="pred.place_id" class="dropdown-item"
                            @mousedown.prevent="selectPrediction(pred)">
                            <i class="bi bi-geo-alt me-2 text-sienna"></i>
                            <div class="dropdown-text">
                                <span class="dropdown-main">{{ pred.main_text }}</span>
                                <span class="dropdown-secondary">{{ pred.secondary_text }}</span>
                            </div>
                        </button>
                    </div>
                </Transition>
            </div>
        </div>

        <!-- Error state -->
        <div v-if="weather.error" class="error-bar animate-fade-in-up">
            <i class="bi bi-exclamation-circle me-2"></i>
            {{ weather.error }}
        </div>

        <!-- Loading state -->
        <div v-if="weather.isLoadingWeather" class="loading-state animate-fade-in">
            <div class="loading-card">
                <div class="spinner-border text-moss mb-3" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="loading-text">Fetching weather data...</p>
            </div>
        </div>

        <!-- Weather content -->
        <div v-else-if="weather.hasWeather && weather.selectedLocation" class="weather-content">

            <!-- Location name -->
            <div class="location-badge animate-fade-in-up">
                <i class="bi bi-geo-alt-fill"></i>
                <span>{{ weather.selectedLocation.name || weather.selectedLocation.formatted_address }}</span>
            </div>

            <!-- Current conditions -->
            <div v-if="weather.currentWeather" class="current-card animate-fade-in-up animate-delay-1">
                <div class="current-main">
                    <div class="current-temp-group">
                        <div class="current-icon">
                            <img v-if="currentIcon" :src="currentIcon" alt="weather" class="weather-img" />
                            <i v-else :class="currentIconFallback" class="weather-icon-fallback"></i>
                        </div>
                        <div class="current-temp">
                            <span class="temp-value">{{ currentTemp }}</span>
                            <span class="temp-unit">&deg;C</span>
                        </div>
                    </div>
                    <div class="current-details">
                        <p class="condition-text">{{ weatherDescription(currentCondition) }}</p>
                        <p class="feels-like">Feels like {{ feelsLike }}&deg;</p>
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
                            <span class="metric-value">{{ currentWind.speed }} <small>km/h</small></span>
                            <span class="metric-label">Wind {{ currentWind.dir }}</span>
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
                            <span class="metric-value">{{ pressure }} <small>mb</small></span>
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
                    <div class="metric" v-if="precipitationProbability !== null">
                        <i class="bi bi-cloud-rain"></i>
                        <div class="metric-info">
                            <span class="metric-value">{{ precipitationProbability }}%</span>
                            <span class="metric-label">Precipitation</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Forecast -->
            <div v-if="weather.forecast.length" class="forecast-section animate-fade-in-up animate-delay-2">
                <h2 class="section-title">{{ weather.forecast.length }}-Day Forecast</h2>
                <div class="forecast-list">
                    <div v-for="(day, idx) in weather.forecast" :key="idx" class="forecast-row"
                        :class="{ 'animate-fade-in-up': true }" :style="{ animationDelay: `${0.1 + idx * 0.06}s` }">
                        <div class="forecast-day">
                            {{ formatShortDay(day.date || day.displayDate) }}
                        </div>
                        <div class="forecast-icon">
                            <img v-if="googleIconUrl(day.daytimeForecast?.weatherCondition)"
                                :src="googleIconUrl(day.daytimeForecast?.weatherCondition)" alt=""
                                class="forecast-weather-img" />
                            <i v-else
                                :class="weatherIcon(day.daytimeForecast?.weatherCondition)"
                                class="forecast-icon-fallback"></i>
                        </div>
                        <div class="forecast-condition">
                            {{ weatherDescription(day.daytimeForecast?.weatherCondition) }}
                        </div>
                        <div class="forecast-precip" v-if="day.daytimeForecast?.precipitation?.probability?.percent">
                            <i class="bi bi-droplet-fill"></i>
                            {{ day.daytimeForecast.precipitation.probability.percent }}%
                        </div>
                        <div class="forecast-temps">
                            <span class="temp-high">{{ tempValue(day.maxTemperature) }}&deg;</span>
                            <span class="temp-divider">/</span>
                            <span class="temp-low">{{ tempValue(day.minTemperature) }}&deg;</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Saved locations (shown when no weather is displayed) -->
        <div v-if="!weather.hasWeather && !weather.isLoadingWeather && weather.savedLocations.length"
            class="saved-section animate-fade-in-up">
            <h2 class="section-title">Recent Locations</h2>
            <div class="saved-list">
                <button v-for="loc in weather.savedLocations" :key="loc.place_id" class="saved-item"
                    @click="loadSaved(loc)">
                    <div class="saved-info">
                        <i class="bi bi-clock-history me-2"></i>
                        <div>
                            <span class="saved-name">{{ loc.name }}</span>
                            <span class="saved-address">{{ loc.formatted_address }}</span>
                        </div>
                    </div>
                    <button class="saved-remove" @click.stop="removeSaved(loc.place_id)"
                        title="Remove">
                        <i class="bi bi-x"></i>
                    </button>
                </button>
            </div>
        </div>

        <!-- Empty state -->
        <div v-if="!weather.hasWeather && !weather.isLoadingWeather && !weather.savedLocations.length && !weather.error"
            class="empty-state animate-fade-in-up animate-delay-1">
            <div class="empty-illustration">
                <i class="bi bi-cloud-sun"></i>
            </div>
            <p class="empty-text">Search for a location to get started</p>
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

.dropdown-secondary {
    font-size: 0.8rem;
    color: var(--text-secondary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
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
    margin: 0;
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

/* ---- Forecast ---- */
.forecast-section {
    margin-bottom: 2rem;
}

.section-title {
    font-family: var(--font-display);
    font-size: 1.35rem;
    color: var(--loam);
    margin: 0 0 1rem;
}

.forecast-list {
    background: var(--white);
    border: 1px solid var(--border-light);
    border-radius: 16px;
    overflow: hidden;
    box-shadow: var(--shadow-sm);
}

.forecast-row {
    display: grid;
    grid-template-columns: 5.5rem 2.5rem 1fr auto 5rem;
    align-items: center;
    gap: 0.75rem;
    padding: 0.85rem 1.25rem;
    border-bottom: 1px solid var(--border-light);
    transition: background var(--transition-fast);
}

.forecast-row:last-child {
    border-bottom: none;
}

.forecast-row:hover {
    background: var(--parchment);
}

.forecast-day {
    font-weight: 500;
    font-size: 0.88rem;
    color: var(--loam);
}

.forecast-icon {
    display: flex;
    align-items: center;
    justify-content: center;
}

.forecast-weather-img {
    width: 32px;
    height: 32px;
    object-fit: contain;
}

.forecast-icon-fallback {
    font-size: 1.25rem;
    color: var(--harvest);
}

.forecast-condition {
    font-size: 0.82rem;
    color: var(--text-secondary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.forecast-precip {
    font-size: 0.78rem;
    color: var(--sage);
    white-space: nowrap;
}

.forecast-precip i {
    font-size: 0.7rem;
}

.forecast-temps {
    text-align: right;
    white-space: nowrap;
    font-size: 0.9rem;
}

.temp-high {
    font-weight: 600;
    color: var(--loam);
}

.temp-divider {
    color: var(--border);
    margin: 0 0.15rem;
}

.temp-low {
    color: var(--text-secondary);
}

/* ---- Saved locations ---- */
.saved-section {
    margin-top: 1.5rem;
}

.saved-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.saved-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: var(--white);
    border: 1px solid var(--border-light);
    border-radius: 12px;
    padding: 0.75rem 1rem;
    cursor: pointer;
    transition: all var(--transition-fast);
    font-family: var(--font-body);
    color: var(--text-primary);
    width: 100%;
    text-align: left;
}

.saved-item:hover {
    border-color: var(--sage);
    box-shadow: var(--shadow-sm);
}

.saved-info {
    display: flex;
    align-items: center;
    min-width: 0;
    flex: 1;
}

.saved-info > div {
    display: flex;
    flex-direction: column;
    min-width: 0;
}

.saved-info i {
    color: var(--sage);
    flex-shrink: 0;
}

.saved-name {
    font-weight: 500;
    font-size: 0.88rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.saved-address {
    font-size: 0.78rem;
    color: var(--text-secondary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.saved-remove {
    background: none;
    border: none;
    color: var(--text-secondary);
    cursor: pointer;
    padding: 0.25rem;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    transition: all var(--transition-fast);
    flex-shrink: 0;
}

.saved-remove:hover {
    color: var(--sienna);
    background: var(--sienna-faded);
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

    .forecast-row {
        grid-template-columns: 4rem 2rem 1fr auto 4.5rem;
        gap: 0.5rem;
        padding: 0.75rem 0.85rem;
        font-size: 0.85rem;
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

    .forecast-row {
        grid-template-columns: 3.5rem 2rem 1fr 4rem;
    }

    .forecast-condition {
        display: none;
    }

    .forecast-precip {
        display: none;
    }
}
</style>

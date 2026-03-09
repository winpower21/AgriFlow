import { defineStore } from "pinia";
import { ref, computed } from "vue";
import api from "@/utils/api";

export const useWeatherStore = defineStore("weather", () => {
    /* ── State ─────────────────────────────────────────────────────────── */

    // All DB-persisted locations (shown in saved-locations grid)
    const storedLocations = ref([]);

    // The currently selected DB location object
    // { id, city, state, country, latitude, longitude }
    const selectedLocation = ref(null);

    // The most recent WeatherSchema record for the selected location
    // { id, location_id, fetched_at, is_manual, raw_json: { current, hourly } }
    const selectedWeather = ref(null);

    // Location search state
    const searchQuery = ref("");
    const searchResults = ref([]);      // DB + possibly Google results
    const googleWasSearched = ref(false); // true if Google was queried this search
    const isSearching = ref(false);

    // Weather load state
    const isLoadingWeather = ref(false);

    const error = ref(null);

    /* ── Computed ───────────────────────────────────────────────────────── */

    const hasLocation = computed(() => selectedLocation.value !== null);
    const hasWeather = computed(() => selectedWeather.value !== null);

    // Convenience accessors into raw_json
    const currentWeather = computed(
        () => selectedWeather.value?.raw_json?.current ?? null
    );
    const forecastHours = computed(
        () => selectedWeather.value?.raw_json?.hourly?.forecastHours ?? []
    );

    /* ── Actions ────────────────────────────────────────────────────────── */

    /** Load all DB locations for the saved-locations grid. */
    async function fetchStoredLocations() {
        try {
            const { data } = await api.get("/api/weather/locations");
            storedLocations.value = data;
        } catch (err) {
            console.error("Failed to load stored locations:", err);
        }
    }

    /** DB-first search (300 ms debounce). Google auto-runs only if DB has 0 results. */
    let searchTimeout = null;
    async function searchLocations(query) {
        searchQuery.value = query;
        error.value = null;
        clearTimeout(searchTimeout);

        if (!query || query.length < 2) {
            searchResults.value = [];
            googleWasSearched.value = false;
            return;
        }

        searchTimeout = setTimeout(async () => {
            isSearching.value = true;
            try {
                const { data } = await api.get("/locations/search", {
                    params: { q: query },
                });
                searchResults.value = data.results || [];
                googleWasSearched.value = data.google_searched || false;
            } catch (err) {
                console.error("Location search failed:", err);
                error.value = "Failed to search locations";
                searchResults.value = [];
            } finally {
                isSearching.value = false;
            }
        }, 300);
    }

    /** Explicitly trigger a Google search (user clicked "Search online"). */
    async function searchOnline(query) {
        if (!query || query.length < 2) return;
        isSearching.value = true;
        try {
            const { data } = await api.get("/locations/search", {
                params: { q: query, force_google: true },
            });
            searchResults.value = data.results || [];
            googleWasSearched.value = true;
        } catch (err) {
            console.error("Online location search failed:", err);
            error.value = "Failed to search online";
        } finally {
            isSearching.value = false;
        }
    }

    /** Select a DB location and load its weather. */
    async function selectDbLocation(loc) {
        error.value = null;
        searchQuery.value = loc.city + (loc.state ? `, ${loc.state}` : "");
        searchResults.value = [];
        selectedLocation.value = loc;
        await fetchWeatherForLocation(loc.id, false);
    }

    /** Resolve a Google prediction to DB, then load weather. */
    async function selectGooglePrediction(pred) {
        error.value = null;
        isLoadingWeather.value = true;
        try {
            const { data: loc } = await api.post("/locations/resolve", null, {
                params: { place_id: pred.place_id },
            });
            // Refresh stored locations so the new entry appears in the grid
            await fetchStoredLocations();
            searchQuery.value = loc.city + (loc.state ? `, ${loc.state}` : "");
            searchResults.value = [];
            selectedLocation.value = loc;
            await fetchWeatherForLocation(loc.id, false);
        } catch (err) {
            console.error("Failed to resolve Google prediction:", err);
            error.value = "Failed to load location";
        } finally {
            isLoadingWeather.value = false;
        }
    }

    /** Fetch weather for a location. manual=true bypasses the 6h TTL. */
    async function fetchWeatherForLocation(locationId, manual = false) {
        isLoadingWeather.value = true;
        error.value = null;
        try {
            let res;
            if (manual) {
                res = await api.post(`/api/weather/by-location/${locationId}/refresh`);
            } else {
                res = await api.get(`/api/weather/by-location/${locationId}`);
            }
            selectedWeather.value = res.data;
        } catch (err) {
            console.error("Weather fetch failed:", err);
            error.value =
                err.response?.data?.detail || "Failed to load weather data";
            selectedWeather.value = null;
        } finally {
            isLoadingWeather.value = false;
        }
    }

    /** Clear selected location and weather; return to the locations grid. */
    function clearWeather() {
        selectedLocation.value = null;
        selectedWeather.value = null;
        searchQuery.value = "";
        searchResults.value = [];
        error.value = null;
    }

    function clearSearch() {
        searchQuery.value = "";
        searchResults.value = [];
        googleWasSearched.value = false;
    }

    return {
        // State
        storedLocations,
        selectedLocation,
        selectedWeather,
        searchQuery,
        searchResults,
        googleWasSearched,
        isSearching,
        isLoadingWeather,
        error,
        // Computed
        hasLocation,
        hasWeather,
        currentWeather,
        forecastHours,
        // Actions
        fetchStoredLocations,
        searchLocations,
        searchOnline,
        selectDbLocation,
        selectGooglePrediction,
        fetchWeatherForLocation,
        clearWeather,
        clearSearch,
    };
});

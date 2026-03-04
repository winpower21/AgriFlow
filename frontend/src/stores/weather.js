import { defineStore } from "pinia";
import { ref, computed } from "vue";
import api from "@/utils/api";

export const useWeatherStore = defineStore("weather", () => {
    /* -------------------------
       State
    --------------------------*/
    const searchQuery = ref("");
    const predictions = ref([]);
    const isSearching = ref(false);

    const selectedLocation = ref(null);
    // { name, formatted_address, latitude, longitude, address_components }

    const currentWeather = ref(null);
    const forecast = ref([]);
    const isLoadingWeather = ref(false);

    const savedLocations = ref([]);
    // Array of { name, formatted_address, latitude, longitude, place_id }

    const error = ref(null);

    /* -------------------------
       Computed
    --------------------------*/
    const hasLocation = computed(() => selectedLocation.value !== null);
    const hasWeather = computed(
        () => currentWeather.value !== null || forecast.value.length > 0,
    );

    /* -------------------------
       Actions
    --------------------------*/

    let searchTimeout = null;

    async function searchLocations(query) {
        searchQuery.value = query;
        error.value = null;

        if (!query || query.length < 2) {
            predictions.value = [];
            return;
        }

        // Debounce — wait 300ms after user stops typing
        clearTimeout(searchTimeout);
        return new Promise((resolve) => {
            searchTimeout = setTimeout(async () => {
                isSearching.value = true;
                try {
                    const { data } = await api.get(
                        "/api/weather/search-locations",
                        { params: { query } },
                    );
                    predictions.value = data.predictions || [];
                } catch (err) {
                    console.error("Location search failed:", err);
                    error.value = "Failed to search locations";
                    predictions.value = [];
                } finally {
                    isSearching.value = false;
                    resolve();
                }
            }, 300);
        });
    }

    async function selectLocation(prediction) {
        error.value = null;
        predictions.value = [];
        searchQuery.value = prediction.description;
        isLoadingWeather.value = true;

        try {
            // Fetch place details to get lat/lng
            const { data } = await api.get("/api/weather/place-details", {
                params: { place_id: prediction.place_id },
            });

            selectedLocation.value = {
                ...data,
                place_id: prediction.place_id,
            };

            // Fetch weather data in parallel
            await Promise.all([
                fetchCurrentWeather(data.latitude, data.longitude),
                fetchForecast(data.latitude, data.longitude),
            ]);

            // Add to saved locations if not already there
            const exists = savedLocations.value.some(
                (loc) => loc.place_id === prediction.place_id,
            );
            if (!exists) {
                savedLocations.value.unshift({
                    name: data.name,
                    formatted_address: data.formatted_address,
                    latitude: data.latitude,
                    longitude: data.longitude,
                    place_id: prediction.place_id,
                });
                // Keep only last 5 locations
                if (savedLocations.value.length > 5) {
                    savedLocations.value.pop();
                }
            }
        } catch (err) {
            console.error("Failed to select location:", err);
            error.value = "Failed to load location details";
        } finally {
            isLoadingWeather.value = false;
        }
    }

    async function fetchCurrentWeather(lat, lng) {
        try {
            const { data } = await api.get("/api/weather/current", {
                params: { lat, lng },
            });
            currentWeather.value = data;
        } catch (err) {
            console.error("Current weather fetch failed:", err);
            currentWeather.value = null;
        }
    }

    async function fetchForecast(lat, lng, days = 5) {
        try {
            const { data } = await api.get("/api/weather/forecast", {
                params: { lat, lng, days },
            });
            forecast.value = data.forecastDays || [];
        } catch (err) {
            console.error("Forecast fetch failed:", err);
            forecast.value = [];
        }
    }

    async function loadSavedLocation(location) {
        error.value = null;
        searchQuery.value = location.formatted_address || location.name;
        selectedLocation.value = location;
        isLoadingWeather.value = true;

        try {
            await Promise.all([
                fetchCurrentWeather(location.latitude, location.longitude),
                fetchForecast(location.latitude, location.longitude),
            ]);
        } catch (err) {
            error.value = "Failed to load weather data";
        } finally {
            isLoadingWeather.value = false;
        }
    }

    function removeSavedLocation(placeId) {
        savedLocations.value = savedLocations.value.filter(
            (loc) => loc.place_id !== placeId,
        );
    }

    function clearSearch() {
        searchQuery.value = "";
        predictions.value = [];
    }

    function clearAll() {
        searchQuery.value = "";
        predictions.value = [];
        selectedLocation.value = null;
        currentWeather.value = null;
        forecast.value = [];
        error.value = null;
    }

    return {
        // State
        searchQuery,
        predictions,
        isSearching,
        selectedLocation,
        currentWeather,
        forecast,
        isLoadingWeather,
        savedLocations,
        error,
        // Computed
        hasLocation,
        hasWeather,
        // Actions
        searchLocations,
        selectLocation,
        fetchCurrentWeather,
        fetchForecast,
        loadSavedLocation,
        removeSavedLocation,
        clearSearch,
        clearAll,
    };
});

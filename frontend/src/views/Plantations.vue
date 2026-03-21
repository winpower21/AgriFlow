<template>
    <div class="plantations-page">
        <!-- Page Header -->
        <div class="page-header animate-fade-in-up">
            <div>
                <h2 class="page-title">Plantations</h2>
                <p class="page-subtitle">
                    {{ plantations.length }} registered &mdash;
                    {{ activePlantations.length }} active
                </p>
            </div>
            <button v-if="isAdmin" class="btn-add" @click="openAddModal">
                <i class="bi bi-plus-lg"></i>
                <span>Add Plantation</span>
            </button>
        </div>

        <!-- Tab Bar -->
        <div class="tab-bar animate-fade-in-up animate-delay-1">
            <button
                class="tab-btn"
                :class="{ active: activeTab === 'active' }"
                @click="activeTab = 'active'"
            >
                <i class="bi bi-check-circle-fill"></i>
                <span class="tab-label">Active</span>
                <span class="tab-count">{{ activePlantations.length }}</span>
            </button>
            <button
                class="tab-btn"
                :class="{ active: activeTab === 'all' }"
                @click="activeTab = 'all'"
            >
                <i class="bi bi-list-ul"></i>
                <span class="tab-label">All Plantations</span>
                <span class="tab-count">{{ plantations.length }}</span>
            </button>
        </div>

        <!-- Cards for active tab -->
        <template v-if="activeTab === 'active'">
            <div
                v-if="activePlantations.length > 0"
                class="cards-grid animate-fade-in-up animate-delay-2"
            >
                <div
                    v-for="(p, i) in activePlantations"
                    :key="p.id"
                    class="plantation-card"
                    :style="{ animationDelay: `${i * 0.05}s` }"
                    @click="openDetailsModal(p)"
                >
                    <div class="card-top">
                        <div class="card-identity">
                            <span class="card-icon">
                                <i class="bi bi-tree"></i>
                            </span>
                            <span class="card-name">{{ p.name }}</span>
                        </div>
                        <span class="status-chip status-active">
                            <i class="bi bi-circle-fill"></i> Active
                        </span>
                        <span v-if="leaseExpiryInfo(p)" class="lease-expiry-dot"></span>
                    </div>
                    <div class="card-body">
                        <div v-if="p.location" class="card-location">
                            <i class="bi bi-geo-alt"></i>
                            {{ p.location.city
                            }}<template v-if="p.location.state"
                                >, {{ p.location.state }}</template
                            >
                        </div>
                        <div v-if="p.area_hectares" class="card-area">
                            <i class="bi bi-bounding-box"></i>
                            {{ formatHa(p.area_hectares) }}
                        </div>
                        <div v-if="latestLease(p)" class="card-lease">
                            <i class="bi bi-calendar2-range"></i>
                            {{ formatDate(latestLease(p).start_date) }}
                            <template v-if="latestLease(p).end_date">
                                &rarr; {{ formatDate(latestLease(p).end_date) }}
                            </template>
                            <template v-else> &rarr; open-ended</template>
                        </div>
                        <div v-if="leaseExpiryInfo(p)" class="lease-expiry-warning" :class="leaseExpiryInfo(p).type">
                            <i class="bi" :class="leaseExpiryInfo(p).type === 'expired' ? 'bi-x-circle-fill' : 'bi-exclamation-circle-fill'"></i>
                            {{ leaseExpiryInfo(p).text }}
                        </div>
                    </div>
                    <div class="card-actions" @click.stop>
                        <button
                            class="btn-action btn-details"
                            title="Details &amp; Weather"
                            @click="openDetailsModal(p)"
                        >
                            <i class="bi bi-info-circle"></i>
                        </button>
                        <template v-if="isAdmin">
                            <button
                                class="btn-action btn-edit"
                                title="Edit"
                                @click="openEditModal(p)"
                            >
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button
                                class="btn-action btn-delete"
                                title="Delete"
                                @click="openDeleteModal(p)"
                            >
                                <i class="bi bi-trash3"></i>
                            </button>
                        </template>
                    </div>
                </div>
            </div>
            <div
                v-else-if="!loading"
                class="empty-state animate-fade-in-up animate-delay-2"
            >
                <i class="bi bi-tree"></i>
                <p>No active plantations</p>
            </div>
        </template>

        <!-- Cards for all tab -->
        <template v-else>
            <div
                v-if="plantations.length > 0"
                class="cards-grid animate-fade-in-up animate-delay-2"
            >
                <div
                    v-for="(p, i) in plantations"
                    :key="p.id"
                    class="plantation-card"
                    :class="{ 'plantation-card-inactive': !p.is_active }"
                    :style="{ animationDelay: `${i * 0.04}s` }"
                    @click="openDetailsModal(p)"
                >
                    <div class="card-top">
                        <div class="card-identity">
                            <span
                                class="card-icon"
                                :class="{ 'card-icon-inactive': !p.is_active }"
                            >
                                <i class="bi bi-tree"></i>
                            </span>
                            <span class="card-name">{{ p.name }}</span>
                        </div>
                        <span
                            class="status-chip"
                            :class="p.is_active ? 'status-active' : 'status-inactive'"
                        >
                            <i class="bi" :class="p.is_active ? 'bi-circle-fill' : 'bi-circle'"></i>
                            {{ p.is_active ? "Active" : "Inactive" }}
                        </span>
                        <span v-if="leaseExpiryInfo(p)" class="lease-expiry-dot"></span>
                    </div>
                    <div class="card-body">
                        <div v-if="p.location" class="card-location">
                            <i class="bi bi-geo-alt"></i>
                            {{ p.location.city
                            }}<template v-if="p.location.state"
                                >, {{ p.location.state }}</template
                            >
                        </div>
                        <div v-if="p.area_hectares" class="card-area">
                            <i class="bi bi-bounding-box"></i>
                            {{ formatHa(p.area_hectares) }}
                        </div>
                        <div v-if="leaseExpiryInfo(p)" class="lease-expiry-warning" :class="leaseExpiryInfo(p).type">
                            <i class="bi" :class="leaseExpiryInfo(p).type === 'expired' ? 'bi-x-circle-fill' : 'bi-exclamation-circle-fill'"></i>
                            {{ leaseExpiryInfo(p).text }}
                        </div>
                    </div>
                    <div class="card-actions" @click.stop>
                        <button
                            class="btn-action btn-details"
                            title="Details"
                            @click="openDetailsModal(p)"
                        >
                            <i class="bi bi-info-circle"></i>
                        </button>
                        <template v-if="isAdmin">
                            <button
                                class="btn-action btn-edit"
                                title="Edit"
                                @click="openEditModal(p)"
                            >
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button
                                class="btn-action btn-delete"
                                title="Delete"
                                @click="openDeleteModal(p)"
                            >
                                <i class="bi bi-trash3"></i>
                            </button>
                        </template>
                    </div>
                </div>
            </div>
            <div
                v-else-if="!loading"
                class="empty-state animate-fade-in-up animate-delay-2"
            >
                <i class="bi bi-tree"></i>
                <p>No plantations yet. Add your first one.</p>
            </div>
        </template>

        <!-- ══════════ DETAIL MODAL ══════════ -->
        <div
            class="modal fade"
            id="detailModal"
            tabindex="-1"
            aria-hidden="true"
            ref="detailModalRef"
        >
            <div class="modal-dialog modal-xl modal-dialog-centered modal-dialog-scrollable">
                <div class="modal-content detail-modal-content">
                    <div class="modal-header detail-modal-header">
                        <div class="detail-modal-title">
                            <span class="card-icon">
                                <i class="bi bi-tree"></i>
                            </span>
                            <h5 class="modal-title">
                                {{ selectedPlantation?.name }}
                            </h5>
                        </div>
                        <button
                            type="button"
                            class="btn-close-modal"
                            data-bs-dismiss="modal"
                        >
                            <i class="bi bi-x-lg"></i>
                        </button>
                    </div>
                    <div class="modal-body detail-modal-body" v-if="selectedPlantation">
                        <div class="detail-layout">
                            <!-- Left panel: info + leases -->
                            <div class="detail-left">
                                <!-- Plantation Info -->
                                <div class="detail-section">
                                    <h6 class="detail-section-title">
                                        <i class="bi bi-info-circle"></i>
                                        Plantation Info
                                    </h6>
                                    <div class="detail-info-grid">
                                        <div class="detail-info-item" v-if="selectedPlantation.location">
                                            <span class="detail-info-label">Location</span>
                                            <span class="detail-info-value">
                                                <i class="bi bi-geo-alt text-muted me-1"></i>
                                                {{ selectedPlantation.location.city
                                                }}<template v-if="selectedPlantation.location.state">, {{ selectedPlantation.location.state }}</template>
                                            </span>
                                        </div>
                                        <div class="detail-info-item" v-if="selectedPlantation.area_hectares">
                                            <span class="detail-info-label">Area</span>
                                            <span class="detail-info-value">{{ formatHa(selectedPlantation.area_hectares) }}</span>
                                        </div>
                                        <div class="detail-info-item">
                                            <span class="detail-info-label">Status</span>
                                            <span class="status-chip" :class="selectedPlantation.is_active ? 'status-active' : 'status-inactive'">
                                                <i class="bi" :class="selectedPlantation.is_active ? 'bi-circle-fill' : 'bi-circle'"></i>
                                                {{ selectedPlantation.is_active ? "Active" : "Inactive" }}
                                            </span>
                                        </div>
                                    </div>
                                </div>

                                <!-- Lease History -->
                                <div class="detail-section">
                                    <div class="detail-section-header">
                                        <h6 class="detail-section-title">
                                            <i class="bi bi-calendar2-range"></i>
                                            Lease History
                                        </h6>
                                        <button
                                            v-if="isAdmin"
                                            class="btn-sm-action"
                                            @click="showAddLease = !showAddLease"
                                        >
                                            <i class="bi bi-plus-lg"></i>
                                            Add Lease
                                        </button>
                                    </div>

                                    <!-- Add Lease Form -->
                                    <div v-if="showAddLease" class="add-lease-form">
                                        <div class="row g-2 mb-2">
                                            <div class="col-6">
                                                <label class="form-label">Start Date *</label>
                                                <input
                                                    v-model="leaseForm.start_date"
                                                    type="date"
                                                    class="form-control form-control-sm"
                                                />
                                            </div>
                                            <div class="col-6">
                                                <label class="form-label">End Date</label>
                                                <input
                                                    v-model="leaseForm.end_date"
                                                    type="date"
                                                    class="form-control form-control-sm"
                                                />
                                            </div>
                                            <div class="col-12">
                                                <label class="form-label">Cost (&#8377;)</label>
                                                <input
                                                    v-model="leaseForm.cost"
                                                    type="number"
                                                    min="0"
                                                    step="0.01"
                                                    class="form-control form-control-sm"
                                                    placeholder="Optional"
                                                />
                                            </div>
                                        </div>
                                        <div class="d-flex gap-2">
                                            <button
                                                class="btn-sm-primary"
                                                :disabled="!leaseForm.start_date || leaseSaving"
                                                @click="submitAddLease"
                                            >
                                                <i class="bi bi-check-lg"></i>
                                                Save Lease
                                            </button>
                                            <button
                                                class="btn-sm-cancel"
                                                @click="showAddLease = false; leaseForm = { start_date: '', end_date: '', cost: '' }"
                                            >
                                                Cancel
                                            </button>
                                        </div>
                                    </div>

                                    <!-- Lease Records -->
                                    <div v-if="selectedPlantation.lease?.length" class="lease-list">
                                        <div
                                            v-for="lease in selectedPlantation.lease"
                                            :key="lease.id"
                                            class="lease-row"
                                        >
                                            <div class="lease-dates-text">
                                                <i class="bi bi-calendar3"></i>
                                                {{ formatDate(lease.start_date) }}
                                                <span class="lease-arrow">&#8594;</span>
                                                {{ lease.end_date ? formatDate(lease.end_date) : "open-ended" }}
                                            </div>
                                            <div class="lease-row-actions">
                                                <span v-if="lease.cost" class="lease-cost-badge">
                                                    {{ formatCurrency(lease.cost) }}
                                                </span>
                                                <button
                                                    v-if="lease.cost > 0"
                                                    class="btn-sm-action"
                                                    @click.stop="openLeasePaymentForm(lease)"
                                                    title="Record lease payment"
                                                >
                                                    <i class="bi bi-receipt"></i> Record Payment
                                                </button>
                                            </div>
                                        </div>

                                        <!-- Lease Payment Inline Form -->
                                        <div v-if="leasePaymentLease" class="lease-payment-form">
                                            <h6 class="lease-payment-title">
                                                <i class="bi bi-receipt"></i>
                                                Record Lease Payment
                                            </h6>
                                            <div class="row g-2 mb-2">
                                                <div class="col-6">
                                                    <label class="form-label">Amount (&#8377;) *</label>
                                                    <input
                                                        v-model="leasePaymentForm.amount"
                                                        type="number"
                                                        min="0"
                                                        step="0.01"
                                                        class="form-control form-control-sm"
                                                    />
                                                </div>
                                                <div class="col-6">
                                                    <label class="form-label">Date *</label>
                                                    <input
                                                        v-model="leasePaymentForm.date"
                                                        type="date"
                                                        class="form-control form-control-sm"
                                                    />
                                                </div>
                                                <div class="col-12">
                                                    <label class="form-label">Description</label>
                                                    <input
                                                        v-model="leasePaymentForm.description"
                                                        type="text"
                                                        class="form-control form-control-sm"
                                                    />
                                                </div>
                                            </div>
                                            <div class="d-flex gap-2">
                                                <button
                                                    class="btn-sm-primary"
                                                    :disabled="!leasePaymentForm.amount || !leasePaymentForm.date || leasePaymentSaving"
                                                    @click="submitLeasePayment"
                                                >
                                                    <i class="bi bi-check-lg"></i>
                                                    Save Payment
                                                </button>
                                                <button
                                                    class="btn-sm-cancel"
                                                    @click="cancelLeasePayment"
                                                >
                                                    Cancel
                                                </button>
                                            </div>
                                        </div>

                                        <!-- Lease Expense Summary -->
                                        <div v-if="leaseExpenseSummary.total > 0" class="lease-expense-summary">
                                            <i class="bi bi-wallet2"></i>
                                            Lease expenses: {{ formatCurrency(leaseExpenseSummary.recorded) }} recorded / {{ formatCurrency(leaseExpenseSummary.total) }} total
                                        </div>
                                    </div>
                                    <div v-else class="lease-empty">
                                        <i class="bi bi-calendar-x"></i>
                                        No lease records
                                    </div>
                                </div>
                            </div>

                            <!-- Right panel: weather -->
                            <div class="detail-right">
                                <div class="detail-section">
                                    <div class="detail-section-header">
                                        <h6 class="detail-section-title">
                                            <i class="bi bi-cloud-sun"></i>
                                            Weather
                                        </h6>
                                        <button
                                            class="btn-sm-action"
                                            :disabled="weatherLoading"
                                            @click="loadWeather(selectedPlantation.id, true)"
                                            title="Refresh weather"
                                        >
                                            <i class="bi bi-arrow-clockwise" :class="{ 'spin': weatherLoading }"></i>
                                            Refresh
                                        </button>
                                    </div>

                                    <!-- Loading -->
                                    <div v-if="weatherLoading" class="weather-loading">
                                        <i class="bi bi-cloud-download"></i>
                                        Loading weather...
                                    </div>

                                    <!-- Error -->
                                    <div v-else-if="weatherError" class="weather-error">
                                        <i class="bi bi-exclamation-triangle"></i>
                                        {{ weatherError }}
                                    </div>

                                    <!-- No location -->
                                    <div v-else-if="!selectedPlantation.location_id" class="weather-no-location">
                                        <i class="bi bi-geo-alt-fill"></i>
                                        <p>Assign a location to this plantation to see weather data.</p>
                                    </div>

                                    <!-- Weather data -->
                                    <div v-else-if="weatherData" class="weather-panel">
                                        <!-- Current conditions -->
                                        <div class="weather-current">
                                            <div class="weather-temp-block">
                                                <span class="weather-temp">
                                                    {{ weatherData.raw_json?.current?.temperature?.degrees != null
                                                        ? Math.round(weatherData.raw_json.current.temperature.degrees) + '°'
                                                        : '—' }}
                                                </span>
                                                <span class="weather-unit">
                                                    {{ weatherData.raw_json?.current?.temperature?.unit === 'FAHRENHEIT' ? 'F' : 'C' }}
                                                </span>
                                            </div>
                                            <div class="weather-meta">
                                                <div class="weather-condition">
                                                    {{ weatherData.raw_json?.current?.weatherCondition?.description?.text || '—' }}
                                                </div>
                                                <div class="weather-details">
                                                    <span v-if="weatherData.raw_json?.current?.humidity?.value != null">
                                                        <i class="bi bi-droplet"></i>
                                                        {{ weatherData.raw_json.current.humidity.value }}%
                                                    </span>
                                                    <span v-if="weatherData.raw_json?.current?.wind?.speed?.value != null">
                                                        <i class="bi bi-wind"></i>
                                                        {{ Math.round(weatherData.raw_json.current.wind.speed.value) }}
                                                        {{ weatherData.raw_json.current.wind.speed.unit || 'km/h' }}
                                                    </span>
                                                    <span v-if="weatherData.raw_json?.current?.feelsLike?.degrees != null">
                                                        Feels {{ Math.round(weatherData.raw_json.current.feelsLike.degrees) }}°
                                                    </span>
                                                </div>
                                                <div class="weather-fetched-at">
                                                    <i class="bi bi-clock"></i>
                                                    {{ formatDateTime(weatherData.fetched_at) }}
                                                    <span v-if="weatherData.is_manual" class="badge-manual">manual</span>
                                                </div>
                                            </div>
                                        </div>

                                        <!-- Hourly forecast strip -->
                                        <div
                                            v-if="weatherData.raw_json?.hourly?.forecastHours?.length"
                                            class="hourly-section"
                                        >
                                            <p class="hourly-label">Hourly forecast</p>
                                            <div class="hourly-strip">
                                                <div
                                                    v-for="(h, idx) in weatherData.raw_json.hourly.forecastHours.slice(0, 12)"
                                                    :key="idx"
                                                    class="hourly-item"
                                                >
                                                    <span class="hourly-time">{{ formatHour(h.interval?.startTime) }}</span>
                                                    <span class="hourly-temp">
                                                        {{ h.temperature?.degrees != null
                                                            ? Math.round(h.temperature.degrees) + '°'
                                                            : '—' }}
                                                    </span>
                                                    <span class="hourly-cond">
                                                        {{ h.weatherCondition?.description?.text || '' }}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <!-- No weather yet -->
                                    <div v-else class="weather-no-data">
                                        <i class="bi bi-cloud"></i>
                                        <p>No weather data yet.</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- ══════════ ADD / EDIT MODAL ══════════ -->
        <div
            class="modal fade"
            id="formModal"
            tabindex="-1"
            aria-hidden="true"
            ref="formModalRef"
        >
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content form-modal-content">
                    <div class="modal-header form-modal-header">
                        <h5 class="modal-title">
                            {{ editingPlantation ? "Edit Plantation" : "Add Plantation" }}
                        </h5>
                        <button type="button" class="btn-close-modal" data-bs-dismiss="modal">
                            <i class="bi bi-x-lg"></i>
                        </button>
                    </div>
                    <div class="modal-body">
                        <div class="mb-3">
                            <label class="form-label fw-semibold">Name *</label>
                            <input
                                v-model="form.name"
                                type="text"
                                class="form-control"
                                placeholder="e.g. North Field"
                            />
                        </div>

                        <!-- Location search -->
                        <div class="mb-3">
                            <label class="form-label fw-semibold">Location</label>
                            <div class="location-search-wrapper">
                                <input
                                    :value="formLocationLabel"
                                    type="text"
                                    class="form-control"
                                    placeholder="Search city..."
                                    autocomplete="off"
                                    @input="onLocationInput"
                                />
                                <div v-if="locationResults.length" class="location-results">
                                    <div
                                        v-for="loc in locationResults"
                                        :key="loc.place_id || loc.id"
                                        class="location-result-item"
                                        @click="selectLocation(loc)"
                                    >
                                        <i :class="loc.source === 'db' ? 'bi bi-database text-muted' : 'bi bi-geo-alt text-muted'"></i>
                                        <span>{{ loc.description || (loc.city + (loc.state ? ', ' + loc.state : '')) }}</span>
                                        <span class="location-result-source">{{ loc.source === 'db' ? 'saved' : 'google' }}</span>
                                    </div>
                                    <div
                                        v-if="!locationGoogleWasSearched"
                                        class="location-search-online"
                                        @click="onLocationSearchOnline"
                                    >
                                        <i class="bi bi-search"></i>
                                        <span>Search online</span>
                                    </div>
                                </div>
                            </div>
                            <small v-if="form.location_id" class="text-muted">
                                <i class="bi bi-check-circle-fill text-success"></i>
                                Location selected
                            </small>
                        </div>

                        <!-- Area -->
                        <div class="mb-3">
                            <label class="form-label fw-semibold">Area (hectares)</label>
                            <div class="area-input-row">
                                <input
                                    v-model="form.area_hectares"
                                    type="number"
                                    step="0.0001"
                                    min="0"
                                    class="form-control"
                                    placeholder="e.g. 2.5"
                                />
                                <span v-if="areaAcresHint" class="area-hint">{{ areaAcresHint }}</span>
                            </div>
                        </div>

                        <!-- Initial lease -->
                        <hr class="my-3" style="border-color: var(--border-light);" />
                        <p class="form-section-label">Initial Lease <span class="text-muted">(optional)</span></p>
                        <div class="row g-2 mb-2">
                            <div class="col-6">
                                <label class="form-label">Start Date</label>
                                <input v-model="form.lease_start" type="date" class="form-control" />
                            </div>
                            <div class="col-6">
                                <label class="form-label">End Date</label>
                                <input v-model="form.lease_end" type="date" class="form-control" />
                            </div>
                            <div class="col-12">
                                <label class="form-label">Lease Cost (&#8377;)</label>
                                <input
                                    v-model="form.lease_cost"
                                    type="number"
                                    min="0"
                                    step="0.01"
                                    class="form-control"
                                    placeholder="Optional"
                                />
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer form-modal-footer">
                        <button type="button" class="btn-modal btn-modal-cancel" data-bs-dismiss="modal">
                            Cancel
                        </button>
                        <button
                            type="button"
                            class="btn-modal btn-modal-confirm"
                            :disabled="!form.name.trim()"
                            @click="submitForm"
                        >
                            {{ editingPlantation ? "Save Changes" : "Add Plantation" }}
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- ══════════ DELETE MODAL ══════════ -->
        <div
            class="modal fade"
            id="deleteModal"
            tabindex="-1"
            aria-hidden="true"
            ref="deleteModalRef"
        >
            <div class="modal-dialog modal-dialog-centered modal-sm">
                <div class="modal-content confirm-modal">
                    <div class="modal-body">
                        <div class="modal-icon icon-delete">
                            <i class="bi bi-trash3"></i>
                        </div>
                        <h5 class="modal-title">Delete Plantation</h5>
                        <p class="modal-desc">
                            Remove <strong>{{ deleteTarget?.name }}</strong>? This will also delete all lease history.
                        </p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn-modal btn-modal-cancel" data-bs-dismiss="modal">
                            Cancel
                        </button>
                        <button type="button" class="btn-modal btn-modal-danger" @click="confirmDelete">
                            Delete
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from "vue";
import { Modal } from "bootstrap";
import { useAuthStore } from "../stores/auth";
import api from "../utils/api";
import { useReportsStore } from "@/stores/reports";

const auth = useAuthStore();
const reportsStore = useReportsStore();
const isAdmin = computed(() => auth.userRoles?.includes("admin"));

// ── Data ─────────────────────────────────────────────────────────────────────
const plantations = ref([]);
const loading = ref(false);
const haToAcRate = ref(2.47105);

const activeTab = ref("active");

const activePlantations = computed(() => plantations.value.filter((p) => p.is_active));

// ── Fetch ─────────────────────────────────────────────────────────────────────
async function fetchAll() {
    loading.value = true;
    try {
        const [pRes, rateRes] = await Promise.allSettled([
            api.get("/plantations/"),
            api.get("/settings/app-config/hectares_to_acres_rate"),
        ]);
        if (pRes.status === "fulfilled") plantations.value = pRes.value.data;
        if (rateRes.status === "fulfilled")
            haToAcRate.value = parseFloat(rateRes.value.data.value) || 2.47105;
    } finally {
        loading.value = false;
    }
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function formatHa(ha) {
    if (ha == null) return "—";
    const acres = (parseFloat(ha) * haToAcRate.value).toFixed(2);
    return `${parseFloat(ha).toFixed(2)} ha / ${acres} ac`;
}

function latestLease(p) {
    return p.lease?.[0] ?? null;
}

function leaseExpiryInfo(plantation) {
    const lease = latestLease(plantation)
    if (!lease || !lease.end_date) return null
    const endDate = new Date(lease.end_date)
    endDate.setHours(0, 0, 0, 0)
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const diffDays = Math.ceil((endDate - today) / (1000 * 60 * 60 * 24))
    if (diffDays < 0) return { type: 'expired', text: 'Lease expired', days: diffDays }
    if (diffDays <= 30) return { type: 'expiring', text: `Lease expires in ${diffDays} day${diffDays !== 1 ? 's' : ''}`, days: diffDays }
    return null
}

function formatDate(d) {
    if (!d) return "—";
    return new Date(d).toLocaleDateString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric",
    });
}

function formatDateTime(d) {
    if (!d) return "—";
    return new Date(d).toLocaleString("en-IN", {
        day: "2-digit",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
    });
}

function formatHour(isoString) {
    if (!isoString) return "";
    return new Date(isoString).toLocaleTimeString("en-IN", {
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
    });
}

function formatCurrency(v) {
    if (v == null) return "—";
    return new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: "INR",
        maximumFractionDigits: 0,
    }).format(v);
}

// ── Detail Modal ──────────────────────────────────────────────────────────────
const detailModalRef = ref(null);
let bsDetailModal = null;
const selectedPlantation = ref(null);
const weatherData = ref(null);
const weatherLoading = ref(false);
const weatherError = ref(null);
const showAddLease = ref(false);
const leaseForm = ref({ start_date: "", end_date: "", cost: "" });
const leaseSaving = ref(false);

async function openDetailsModal(p) {
    selectedPlantation.value = p;
    weatherData.value = null;
    weatherError.value = null;
    showAddLease.value = false;
    leaseForm.value = { start_date: "", end_date: "", cost: "" };
    leasePaymentLease.value = null;
    leaseExpenseSummary.value = { recorded: 0, total: 0 };
    if (!bsDetailModal) bsDetailModal = new Modal(detailModalRef.value);
    bsDetailModal.show();
    fetchLeaseExpenseSummary();
    if (p.location_id) await loadWeather(p.id, false);
}

async function loadWeather(plantationId, isManual) {
    weatherLoading.value = true;
    weatherError.value = null;
    try {
        const url = `/plantations/${plantationId}/weather${isManual ? "/refresh" : ""}`;
        const method = isManual ? "post" : "get";
        const res = await api[method](url);
        weatherData.value = res.data;
    } catch (e) {
        weatherError.value =
            e.response?.data?.detail || "Could not load weather data.";
    } finally {
        weatherLoading.value = false;
    }
}

async function submitAddLease() {
    if (!leaseForm.value.start_date) return;
    leaseSaving.value = true;
    try {
        const payload = {
            start_date: leaseForm.value.start_date,
            end_date: leaseForm.value.end_date || null,
            cost: leaseForm.value.cost ? parseFloat(leaseForm.value.cost) : null,
        };
        await api.post(`/plantations/${selectedPlantation.value.id}/leases`, payload);
        reportsStore.invalidate('plantations');
        // Refresh plantation list so lease history updates
        await fetchAll();
        selectedPlantation.value = plantations.value.find(
            (p) => p.id === selectedPlantation.value.id
        );
        showAddLease.value = false;
        leaseForm.value = { start_date: "", end_date: "", cost: "" };
    } catch (e) {
        console.error("Failed to add lease:", e);
    } finally {
        leaseSaving.value = false;
    }
}

// ── Lease Payment ────────────────────────────────────────────────────────────
const leaseCostCategoryId = ref(null);
const leasePaymentLease = ref(null);
const leasePaymentForm = ref({ amount: '', date: '', description: '' });
const leasePaymentSaving = ref(false);
const leaseExpenseSummary = ref({ recorded: 0, total: 0 });

async function fetchLeaseCostCategory() {
    try {
        const res = await api.get('/settings/expense-categories');
        const cat = res.data.find((c) => c.name === 'Lease Cost');
        if (cat) leaseCostCategoryId.value = cat.id;
    } catch (e) {
        console.error('Failed to fetch expense categories:', e);
    }
}

function openLeasePaymentForm(lease) {
    leasePaymentLease.value = lease;
    const today = new Date().toISOString().slice(0, 10);
    const pName = selectedPlantation.value?.name || '';
    const startStr = formatDate(lease.start_date);
    const endStr = lease.end_date ? formatDate(lease.end_date) : 'open-ended';
    leasePaymentForm.value = {
        amount: lease.cost || '',
        date: today,
        description: `Lease payment for ${pName} (${startStr} – ${endStr})`,
    };
}

function cancelLeasePayment() {
    leasePaymentLease.value = null;
    leasePaymentForm.value = { amount: '', date: '', description: '' };
}

async function submitLeasePayment() {
    if (!leasePaymentForm.value.amount || !leasePaymentForm.value.date || !leaseCostCategoryId.value) return;
    leasePaymentSaving.value = true;
    try {
        await api.post('/expenses/', {
            amount: parseFloat(leasePaymentForm.value.amount),
            category_id: leaseCostCategoryId.value,
            plantation_id: selectedPlantation.value.id,
            date: leasePaymentForm.value.date,
            description: leasePaymentForm.value.description,
        });
        reportsStore.invalidate('expenses');
        reportsStore.invalidate('plantations');
        cancelLeasePayment();
        await fetchLeaseExpenseSummary();
    } catch (e) {
        console.error('Failed to record lease payment:', e);
    } finally {
        leasePaymentSaving.value = false;
    }
}

async function fetchLeaseExpenseSummary() {
    if (!selectedPlantation.value || !leaseCostCategoryId.value) return;
    try {
        const res = await api.get(`/expenses/?plantation_id=${selectedPlantation.value.id}&category_id=${leaseCostCategoryId.value}`);
        const expenses = res.data;
        const recorded = expenses.reduce((sum, e) => sum + parseFloat(e.amount || 0), 0);
        const totalLeaseCost = (selectedPlantation.value.lease || []).reduce(
            (sum, l) => sum + parseFloat(l.cost || 0), 0
        );
        leaseExpenseSummary.value = { recorded, total: totalLeaseCost };
    } catch (e) {
        leaseExpenseSummary.value = { recorded: 0, total: 0 };
    }
}

// ── Create / Edit Modal ───────────────────────────────────────────────────────
const formModalRef = ref(null);
let bsFormModal = null;
const editingPlantation = ref(null);
const form = ref({
    name: "",
    location_id: null,
    area_hectares: "",
    lease_start: "",
    lease_end: "",
    lease_cost: "",
});
const formLocationLabel = ref("");
const locationResults = ref([]);
const locationGoogleWasSearched = ref(false);
let locationSearchTimer = null;

const areaAcresHint = computed(() => {
    const ha = parseFloat(form.value.area_hectares);
    if (isNaN(ha) || ha <= 0) return "";
    return `≈ ${(ha * haToAcRate.value).toFixed(2)} ac`;
});

function openAddModal() {
    editingPlantation.value = null;
    form.value = {
        name: "",
        location_id: null,
        area_hectares: "",
        lease_start: "",
        lease_end: "",
        lease_cost: "",
    };
    formLocationLabel.value = "";
    locationResults.value = [];
    locationGoogleWasSearched.value = false;
    if (!bsFormModal) bsFormModal = new Modal(formModalRef.value);
    bsFormModal.show();
}

function openEditModal(p) {
    editingPlantation.value = p;
    form.value = {
        name: p.name,
        location_id: p.location_id,
        area_hectares: p.area_hectares ?? "",
        lease_start: "",
        lease_end: "",
        lease_cost: "",
    };
    formLocationLabel.value = p.location
        ? `${p.location.city}${p.location.state ? ", " + p.location.state : ""}`
        : "";
    locationResults.value = [];
    locationGoogleWasSearched.value = false;
    if (!bsFormModal) bsFormModal = new Modal(formModalRef.value);
    bsFormModal.show();
}

async function onLocationInput(e) {
    const q = (e.target.value || "").trim();
    formLocationLabel.value = q;
    form.value.location_id = null;
    locationGoogleWasSearched.value = false;
    clearTimeout(locationSearchTimer);
    if (q.length < 2) {
        locationResults.value = [];
        return;
    }
    locationSearchTimer = setTimeout(async () => {
        try {
            const res = await api.get(
                `/locations/search?q=${encodeURIComponent(q)}`
            );
            locationResults.value = (res.data.results || []).slice(0, 8);
            locationGoogleWasSearched.value = res.data.google_searched || false;
        } catch {
            locationResults.value = [];
        }
    }, 300);
}

async function onLocationSearchOnline() {
    const q = formLocationLabel.value.trim();
    if (q.length < 2) return;
    try {
        const res = await api.get(
            `/locations/search?q=${encodeURIComponent(q)}&force_google=true`
        );
        locationResults.value = (res.data.results || []).slice(0, 8);
        locationGoogleWasSearched.value = true;
    } catch {
        locationResults.value = [];
    }
}

async function selectLocation(loc) {
    if (loc.source === "db") {
        form.value.location_id = loc.id;
        formLocationLabel.value = `${loc.city}${loc.state ? ", " + loc.state : ""}`;
    } else {
        try {
            const res = await api.post(
                `/locations/resolve?place_id=${encodeURIComponent(loc.place_id)}`
            );
            form.value.location_id = res.data.id;
            formLocationLabel.value = `${res.data.city}${res.data.state ? ", " + res.data.state : ""}`;
        } catch (e) {
            console.error("Failed to resolve location:", e);
        }
    }
    locationResults.value = [];
}

async function submitForm() {
    if (!form.value.name.trim()) return;
    const payload = {
        name: form.value.name.trim(),
        location_id: form.value.location_id,
        area_hectares: form.value.area_hectares
            ? parseFloat(form.value.area_hectares)
            : null,
        lease_start: form.value.lease_start || null,
        lease_end: form.value.lease_end || null,
        lease_cost: form.value.lease_cost
            ? parseFloat(form.value.lease_cost)
            : null,
    };
    try {
        if (editingPlantation.value) {
            await api.put(`/plantations/${editingPlantation.value.id}`, payload);
        } else {
            await api.post("/plantations/", payload);
        }
        reportsStore.invalidate('plantations');
        await fetchAll();
        bsFormModal?.hide();
    } catch (e) {
        console.error("Failed to save plantation:", e);
    }
}

// ── Delete Modal ──────────────────────────────────────────────────────────────
const deleteModalRef = ref(null);
let bsDeleteModal = null;
const deleteTarget = ref(null);

function openDeleteModal(p) {
    deleteTarget.value = p;
    if (!bsDeleteModal) bsDeleteModal = new Modal(deleteModalRef.value);
    bsDeleteModal.show();
}

async function confirmDelete() {
    if (!deleteTarget.value) return;
    try {
        await api.delete(`/plantations/${deleteTarget.value.id}?force=true`);
        reportsStore.invalidate('plantations');
        plantations.value = plantations.value.filter(
            (p) => p.id !== deleteTarget.value.id
        );
    } catch (e) {
        console.error("Delete failed:", e);
    }
    bsDeleteModal?.hide();
}

// ── Lifecycle ─────────────────────────────────────────────────────────────────
onMounted(() => {
    fetchAll();
    fetchLeaseCostCategory();
});

onBeforeUnmount(() => {
    bsDetailModal?.dispose();
    bsFormModal?.dispose();
    bsDeleteModal?.dispose();
});
</script>

<style scoped>
/* ── Page Layout ────────────────────────────────── */
.plantations-page {
    max-width: 100vw;
}

.page-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 24px;
    gap: 16px;
}

.page-title {
    font-family: var(--font-display);
    font-size: 1.6rem;
    color: var(--text-primary);
    margin: 0 0 4px;
}

.page-subtitle {
    font-size: 0.85rem;
    color: var(--text-secondary);
    margin: 0;
}


/* ── Tab Bar ────────────────────────────────────── */
.tab-bar {
    display: flex;
    gap: 6px;
    margin-bottom: 20px;
}

.tab-btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 10px 18px;
    border: 1.5px solid var(--border);
    border-radius: 10px;
    background: transparent;
    color: var(--text-secondary);
    font-family: var(--font-body);
    font-size: 0.84rem;
    font-weight: 500;
    cursor: pointer;
    transition: all var(--transition-fast);
    white-space: nowrap;
}

.tab-btn:hover {
    border-color: var(--sage);
    color: var(--text-primary);
    background: rgba(138, 154, 123, 0.06);
}

.tab-btn.active {
    border-color: var(--moss);
    color: var(--moss);
    background: rgba(74, 103, 65, 0.08);
    font-weight: 600;
}

.tab-btn i {
    font-size: 0.95rem;
}

.tab-label {
    display: inline;
}

.tab-count {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 22px;
    height: 22px;
    padding: 0 6px;
    border-radius: 11px;
    background: var(--border-light);
    font-size: 0.72rem;
    font-weight: 700;
    color: var(--text-secondary);
    transition: all var(--transition-fast);
}

.tab-btn.active .tab-count {
    background: rgba(74, 103, 65, 0.15);
    color: var(--moss);
}

/* ── Add Button ─────────────────────────────────── */
.btn-add {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 9px 18px;
    border: none;
    border-radius: 10px;
    background: var(--moss);
    color: var(--white);
    font-family: var(--font-body);
    font-size: 0.84rem;
    font-weight: 600;
    cursor: pointer;
    transition: all var(--transition-fast);
    white-space: nowrap;
}

.btn-add:hover {
    background: var(--moss-light);
    box-shadow: 0 4px 12px var(--moss-faded);
}

/* ── Cards Grid ─────────────────────────────────── */
.cards-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 14px;
    margin-bottom: 12px;
}

/* ── Plantation Card ────────────────────────────── */
.plantation-card {
    position: relative;
    background: var(--bg-card);
    border: 1px solid var(--border-light);
    border-radius: 14px;
    box-shadow: var(--shadow-sm);
    padding: 16px;
    cursor: pointer;
    transition: all var(--transition-fast);
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.plantation-card:hover {
    border-color: var(--sage);
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
}

.plantation-card-inactive {
    opacity: 0.72;
}

.plantation-card-inactive:hover {
    opacity: 1;
}

.card-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
}

.card-identity {
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
}

.card-icon {
    width: 32px;
    height: 32px;
    border-radius: 9px;
    background: rgba(74, 103, 65, 0.1);
    color: var(--moss);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 0.95rem;
    flex-shrink: 0;
}

.card-icon-inactive {
    background: var(--border-light);
    color: var(--text-secondary);
}

.card-name {
    font-weight: 600;
    font-size: 0.92rem;
    color: var(--text-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.card-body {
    display: flex;
    flex-direction: column;
    gap: 5px;
    font-size: 0.82rem;
    color: var(--text-secondary);
}

.card-location,
.card-area,
.card-lease {
    display: flex;
    align-items: center;
    gap: 6px;
}

.card-location i,
.card-area i,
.card-lease i {
    font-size: 0.8rem;
    opacity: 0.6;
    flex-shrink: 0;
}

/* ── Status Chips ───────────────────────────────── */
.status-chip {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    white-space: nowrap;
    flex-shrink: 0;
}

.status-active {
    background: rgba(74, 103, 65, 0.1);
    color: var(--moss);
}

.status-active i {
    font-size: 0.5rem;
}

.status-inactive {
    background: var(--border-light);
    color: var(--text-secondary);
}

/* ── Card Actions ───────────────────────────────── */
.card-actions {
    display: flex;
    gap: 6px;
    padding-top: 6px;
    border-top: 1px solid var(--border-light);
}

.btn-action {
    width: 30px;
    height: 30px;
    border-radius: 8px;
    border: 1.5px solid var(--border);
    background: transparent;
    color: var(--text-secondary);
    font-size: 0.85rem;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    transition: all var(--transition-fast);
}

.btn-details:hover {
    border-color: var(--sage);
    color: var(--sage);
    background: rgba(138, 154, 123, 0.08);
}

.btn-edit:hover {
    border-color: var(--harvest);
    color: #8a6f2a;
    background: rgba(196, 163, 90, 0.08);
}

.btn-delete:hover {
    border-color: var(--sienna);
    color: var(--sienna);
    background: rgba(181, 105, 77, 0.06);
}

/* ── Empty State ────────────────────────────────── */
.empty-state {
    text-align: center;
    padding: 36px 20px;
    color: var(--text-secondary);
    background: var(--bg-card);
    border: 1px dashed var(--border);
    border-radius: 14px;
}

.empty-state i {
    font-size: 2.2rem;
    opacity: 0.25;
    margin-bottom: 10px;
    display: block;
}

.empty-state p {
    font-size: 0.88rem;
    margin: 0;
}

/* ── Detail Modal ───────────────────────────────── */
.detail-modal-content {
    border: none;
    border-radius: 16px;
    box-shadow: var(--shadow-lg);
    background: var(--bg-card);
    overflow: hidden;
}

.detail-modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 18px 22px;
    border-bottom: 1px solid var(--border-light);
    background: var(--parchment-deep);
}

.detail-modal-title {
    display: flex;
    align-items: center;
    gap: 10px;
}

.detail-modal-title .modal-title {
    font-family: var(--font-display);
    font-size: 1.15rem;
    color: var(--text-primary);
    margin: 0;
}

.btn-close-modal {
    width: 32px;
    height: 32px;
    border: none;
    background: transparent;
    border-radius: 8px;
    color: var(--text-secondary);
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    transition: all var(--transition-fast);
}

.btn-close-modal:hover {
    background: var(--border-light);
    color: var(--text-primary);
}

.detail-modal-body {
    padding: 20px 22px;
}

.detail-layout {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
}

@media (max-width: 767.98px) {
    .detail-layout {
        grid-template-columns: 1fr;
    }
}

.detail-section {
    margin-bottom: 20px;
}

.detail-section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
}

.detail-section-title {
    display: flex;
    align-items: center;
    gap: 7px;
    font-size: 0.88rem;
    font-weight: 700;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin: 0;
}

.detail-info-grid {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.detail-info-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    font-size: 0.85rem;
}

.detail-info-label {
    color: var(--text-secondary);
    flex-shrink: 0;
}

.detail-info-value {
    color: var(--text-primary);
    font-weight: 500;
    text-align: right;
}

/* ── Small action button ────────────────────────── */
.btn-sm-action {
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

.btn-sm-action:hover:not(:disabled) {
    border-color: var(--moss);
    color: var(--moss);
    background: rgba(74, 103, 65, 0.06);
}

.btn-sm-action:disabled {
    opacity: 0.4;
    cursor: not-allowed;
}

.btn-sm-primary {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 6px 14px;
    border: none;
    border-radius: 8px;
    background: var(--moss);
    color: var(--white);
    font-size: 0.82rem;
    font-weight: 600;
    cursor: pointer;
    transition: all var(--transition-fast);
    font-family: var(--font-body);
}

.btn-sm-primary:hover:not(:disabled) {
    background: var(--moss-light);
}

.btn-sm-primary:disabled {
    opacity: 0.4;
    cursor: not-allowed;
}

.btn-sm-cancel {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 6px 14px;
    border: 1.5px solid var(--border);
    border-radius: 8px;
    background: transparent;
    color: var(--text-secondary);
    font-size: 0.82rem;
    font-weight: 600;
    cursor: pointer;
    font-family: var(--font-body);
}

/* ── Add Lease Form ─────────────────────────────── */
.add-lease-form {
    background: rgba(196, 163, 90, 0.05);
    border: 1px solid var(--border-light);
    border-radius: 10px;
    padding: 14px;
    margin-bottom: 12px;
}

.add-lease-form .form-label {
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--text-secondary);
    margin-bottom: 4px;
}

/* ── Lease List ─────────────────────────────────── */
.lease-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.lease-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    padding: 8px 12px;
    background: var(--parchment-deep);
    border-radius: 8px;
    font-size: 0.82rem;
}

.lease-dates-text {
    display: flex;
    align-items: center;
    gap: 6px;
    color: var(--text-secondary);
}

.lease-arrow {
    opacity: 0.5;
}

.lease-cost-badge {
    font-size: 0.78rem;
    font-weight: 600;
    color: var(--moss);
    background: rgba(74, 103, 65, 0.08);
    padding: 2px 8px;
    border-radius: 12px;
    white-space: nowrap;
}

.lease-empty {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.82rem;
    color: var(--text-secondary);
    opacity: 0.6;
    padding: 8px 0;
}

/* ── Weather Panel ──────────────────────────────── */
.weather-panel {
    background: var(--parchment-deep);
    border-radius: 12px;
    padding: 14px;
}

.weather-loading,
.weather-error,
.weather-no-location,
.weather-no-data {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.84rem;
    color: var(--text-secondary);
    padding: 12px 0;
}

.weather-error {
    color: var(--sienna);
}

.weather-no-location,
.weather-no-data {
    flex-direction: column;
    text-align: center;
    padding: 20px 0;
}

.weather-no-location i,
.weather-no-data i {
    font-size: 1.8rem;
    opacity: 0.3;
}

.weather-no-location p,
.weather-no-data p {
    margin: 0;
    font-size: 0.82rem;
}

.weather-current {
    display: flex;
    gap: 14px;
    align-items: flex-start;
    margin-bottom: 14px;
}

.weather-temp-block {
    display: flex;
    align-items: baseline;
    gap: 3px;
}

.weather-temp {
    font-family: var(--font-display);
    font-size: 2.4rem;
    color: var(--text-primary);
    line-height: 1;
}

.weather-unit {
    font-size: 1rem;
    color: var(--text-secondary);
    align-self: flex-start;
    margin-top: 4px;
}

.weather-meta {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.weather-condition {
    font-weight: 600;
    font-size: 0.9rem;
    color: var(--text-primary);
}

.weather-details {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    font-size: 0.8rem;
    color: var(--text-secondary);
}

.weather-details i {
    margin-right: 2px;
}

.weather-fetched-at {
    font-size: 0.75rem;
    color: var(--text-secondary);
    opacity: 0.7;
    display: flex;
    align-items: center;
    gap: 5px;
}

.badge-manual {
    background: rgba(196, 163, 90, 0.15);
    color: #8a6f2a;
    font-size: 0.68rem;
    font-weight: 700;
    padding: 1px 6px;
    border-radius: 10px;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}

.hourly-section {
    border-top: 1px solid var(--border-light);
    padding-top: 10px;
}

.hourly-label {
    font-size: 0.75rem;
    font-weight: 700;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 8px;
}

.hourly-strip {
    display: flex;
    gap: 6px;
    overflow-x: auto;
    padding-bottom: 4px;
    -webkit-overflow-scrolling: touch;
}

.hourly-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 3px;
    min-width: 52px;
    padding: 8px 6px;
    background: var(--bg-card);
    border: 1px solid var(--border-light);
    border-radius: 10px;
    font-size: 0.72rem;
    color: var(--text-secondary);
    flex-shrink: 0;
    text-align: center;
}

.hourly-time {
    font-size: 0.7rem;
    opacity: 0.7;
}

.hourly-temp {
    font-weight: 700;
    font-size: 0.88rem;
    color: var(--text-primary);
}

.hourly-cond {
    font-size: 0.65rem;
    line-height: 1.2;
    opacity: 0.7;
    max-width: 50px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.spin {
    animation: spin 1s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

/* ── Form Modal ─────────────────────────────────── */
.form-modal-content {
    border: none;
    border-radius: 16px;
    box-shadow: var(--shadow-lg);
    background: var(--bg-card);
    overflow: hidden;
}

.form-modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 18px 22px;
    border-bottom: 1px solid var(--border-light);
    background: var(--parchment-deep);
}

.form-modal-header .modal-title {
    font-family: var(--font-display);
    font-size: 1.1rem;
    color: var(--text-primary);
    margin: 0;
}

.form-modal-footer {
    border-top: 1px solid var(--border-light);
    padding: 12px 22px;
    display: flex;
    gap: 8px;
    justify-content: flex-end;
}

.form-section-label {
    font-size: 0.82rem;
    font-weight: 700;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 10px;
}

/* ── Location Search ────────────────────────────── */
.location-search-wrapper {
    position: relative;
}

.location-results {
    position: absolute;
    top: calc(100% + 4px);
    left: 0;
    right: 0;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    box-shadow: var(--shadow-md);
    z-index: 1050;
    max-height: 220px;
    overflow-y: auto;
}

.location-result-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 9px 14px;
    cursor: pointer;
    font-size: 0.84rem;
    border-bottom: 1px solid var(--border-light);
    transition: background var(--transition-fast);
}

.location-result-item:last-child {
    border-bottom: none;
}

.location-result-item:hover {
    background: rgba(138, 154, 123, 0.07);
}

.location-result-source {
    font-size: 0.7rem;
    color: var(--text-secondary);
    opacity: 0.6;
    margin-left: auto;
    flex-shrink: 0;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}

.location-search-online {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 14px;
    cursor: pointer;
    font-size: 0.82rem;
    color: var(--moss);
    border-top: 1px solid var(--border-light);
    transition: background var(--transition-fast);
}

.location-search-online:hover {
    background: rgba(138, 154, 123, 0.07);
}

/* ── Area Input ─────────────────────────────────── */
.area-input-row {
    display: flex;
    align-items: center;
    gap: 10px;
}

.area-hint {
    font-size: 0.82rem;
    color: var(--text-secondary);
    white-space: nowrap;
}

/* ── Confirm / Delete Modal ─────────────────────── */
.confirm-modal {
    border: none;
    border-radius: 16px;
    box-shadow: var(--shadow-lg);
    overflow: hidden;
    background: var(--bg-card);
}

.confirm-modal .modal-body {
    padding: 28px 24px 16px;
    text-align: center;
}

.modal-icon {
    width: 48px;
    height: 48px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.3rem;
    margin: 0 auto 16px;
}

.icon-delete {
    background: rgba(181, 105, 77, 0.1);
    color: var(--sienna);
}

.modal-title {
    font-family: var(--font-display);
    font-size: 1.1rem;
    margin: 0 0 8px;
    color: var(--text-primary);
}

.modal-desc {
    font-size: 0.84rem;
    color: var(--text-secondary);
    margin: 0;
    line-height: 1.5;
}

.confirm-modal .modal-footer {
    border-top: 1px solid var(--border-light);
    padding: 12px 24px;
    display: flex;
    gap: 8px;
    justify-content: flex-end;
}

/* ── Modal Buttons ──────────────────────────────── */
.btn-modal {
    border: none;
    border-radius: 9px;
    padding: 8px 18px;
    font-size: 0.85rem;
    font-weight: 600;
    font-family: var(--font-body);
    cursor: pointer;
    transition: all var(--transition-fast);
}

.btn-modal-cancel {
    background: transparent;
    color: var(--text-secondary);
    border: 1.5px solid var(--border);
}

.btn-modal-cancel:hover {
    background: var(--parchment-deep);
    color: var(--text-primary);
}

.btn-modal-confirm {
    background: var(--moss);
    color: var(--white);
}

.btn-modal-confirm:hover:not(:disabled) {
    background: var(--moss-light);
}

.btn-modal-confirm:disabled {
    opacity: 0.4;
    cursor: not-allowed;
}

.btn-modal-danger {
    background: var(--sienna);
    color: var(--white);
}

.btn-modal-danger:hover {
    background: var(--sienna-light);
}

/* ── Lease Expiry Warnings ─────────────────────── */
.lease-expiry-dot {
    position: absolute;
    top: 12px;
    right: 12px;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: #dc3545;
    box-shadow: 0 0 0 3px rgba(220, 53, 69, 0.2);
}

.lease-expiry-warning {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.78rem;
    font-weight: 600;
    padding: 4px 0;
}

.lease-expiry-warning.expiring {
    color: #e67e22;
}

.lease-expiry-warning.expired {
    color: #dc3545;
}

/* ── Lease Row Actions ─────────────────────────── */
.lease-row-actions {
    display: flex;
    align-items: center;
    gap: 8px;
}

/* ── Lease Payment Form ────────────────────────── */
.lease-payment-form {
    background: var(--parchment-deep);
    border: 1px solid var(--border-light);
    border-radius: 10px;
    padding: 12px;
    margin-top: 4px;
}

.lease-payment-title {
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 6px;
}

/* ── Lease Expense Summary ─────────────────────── */
.lease-expense-summary {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.78rem;
    font-weight: 600;
    color: var(--text-secondary);
    padding: 8px 12px;
    background: rgba(74, 103, 65, 0.06);
    border-radius: 8px;
    margin-top: 4px;
}

/* ── Responsive ─────────────────────────────────── */
@media (max-width: 575.98px) {
    .cards-grid {
        grid-template-columns: 1fr;
    }

    .page-title {
        font-size: 1.3rem;
    }
}
</style>

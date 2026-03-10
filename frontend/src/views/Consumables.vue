<template>
    <div class="consumables-page">
        <!-- Page Header -->
        <div class="page-header animate-fade-in-up">
            <div>
                <h2 class="page-title">Consumables</h2>
                <p class="page-subtitle">
                    Manage consumable items, track purchases and stock levels
                </p>
            </div>
            <div class="header-actions">
                <template v-if="isAdmin">
                    <button
                        v-if="activeTab === 'items'"
                        class="btn-add"
                        @click="openItemModal(null)"
                    >
                        <i class="bi bi-plus-lg"></i>
                        <span>Add Item</span>
                    </button>
                    <button
                        v-if="activeTab === 'purchases'"
                        class="btn-add"
                        @click="openPurchaseModal"
                    >
                        <i class="bi bi-cart-plus"></i>
                        <span>Add Purchase</span>
                    </button>
                </template>
                <template v-else>
                    <button
                        v-if="activeTab === 'purchases'"
                        class="btn-add btn-add-secondary"
                        @click="openRequestModal"
                    >
                        <i class="bi bi-send"></i>
                        <span>Submit Purchase Request</span>
                    </button>
                </template>
            </div>
        </div>

        <!-- Tab Navigation -->
        <div class="tab-bar animate-fade-in-up animate-delay-1">
            <button
                class="tab-btn"
                :class="{ active: activeTab === 'items' }"
                @click="activeTab = 'items'"
            >
                <i class="bi bi-box-seam"></i>
                <span class="tab-label">Items</span>
                <span class="tab-count">{{ items.length }}</span>
            </button>
            <button
                class="tab-btn"
                :class="{ active: activeTab === 'purchases' }"
                @click="activeTab = 'purchases'"
            >
                <i class="bi bi-receipt"></i>
                <span class="tab-label">Purchases</span>
                <span class="tab-count">{{ purchases.length }}</span>
            </button>
        </div>

        <!-- ══════════════════════════════════════════════ -->
        <!-- ITEMS TAB                                      -->
        <!-- ══════════════════════════════════════════════ -->
        <div v-if="activeTab === 'items'" class="animate-fade-in-up animate-delay-2">
            <!-- Search bar -->
            <div class="filter-bar">
                <div class="search-wrap">
                    <i class="bi bi-search search-icon"></i>
                    <input
                        v-model="searchItems"
                        type="text"
                        class="form-control search-input"
                        placeholder="Search items by name..."
                        @input="fetchItems"
                    />
                </div>
            </div>

            <!-- Items list -->
            <div class="content-panel">
                <div v-if="items.length === 0" class="empty-state">
                    <i class="bi bi-box-seam"></i>
                    <p>No consumable items found</p>
                </div>

                <div v-else class="items-list">
                    <div
                        v-for="item in items"
                        :key="item.id"
                        class="item-row"
                        :class="{ inactive: !item.is_active }"
                    >
                        <div class="item-info">
                            <span class="item-id">#{{ item.id }}</span>
                            <span class="item-name">{{ item.name }}</span>
                            <span class="badge-unit">{{ item.unit }}</span>
                            <span
                                class="status-chip"
                                :class="item.is_active ? 'status-active' : 'status-inactive'"
                            >
                                <i
                                    class="bi"
                                    :class="item.is_active ? 'bi-check-circle-fill' : 'bi-pause-circle-fill'"
                                ></i>
                                {{ item.is_active ? "Active" : "Inactive" }}
                            </span>
                            <span v-if="item.description" class="item-desc">
                                {{ item.description }}
                            </span>
                        </div>
                        <div class="item-stock">
                            <span class="stock-label">Purchased</span>
                            <span class="stock-value">{{ formatQty(item.total_purchased) }} {{ item.unit }}</span>
                            <span class="stock-sep">/</span>
                            <span class="stock-label">Remaining</span>
                            <span class="stock-value stock-remaining">{{ formatQty(item.total_remaining) }} {{ item.unit }}</span>
                        </div>
                        <div v-if="isAdmin" class="item-actions">
                            <button
                                class="btn-action btn-edit"
                                title="Edit"
                                @click="openItemModal(item)"
                            >
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button
                                class="btn-action"
                                :class="item.is_active ? 'btn-toggle-off' : 'btn-toggle-on'"
                                :title="item.is_active ? 'Deactivate' : 'Activate'"
                                @click="toggleActive(item)"
                            >
                                <i
                                    class="bi"
                                    :class="item.is_active ? 'bi-pause-circle' : 'bi-play-circle'"
                                ></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- ══════════════════════════════════════════════ -->
        <!-- PURCHASES TAB                                  -->
        <!-- ══════════════════════════════════════════════ -->
        <div v-if="activeTab === 'purchases'" class="animate-fade-in-up animate-delay-2">

            <!-- Admin: Pending Approvals panel -->
            <div v-if="isAdmin && pendingApprovals.length > 0" class="approvals-panel">
                <div class="approvals-panel-header">
                    <i class="bi bi-hourglass-split"></i>
                    <span>Pending Approvals</span>
                    <span class="approvals-count">{{ pendingApprovals.length }}</span>
                </div>

                <div
                    v-for="req in pendingApprovals"
                    :key="req.id"
                    class="approval-card"
                >
                    <div class="approval-card-header" @click="toggleExpanded(req.id)">
                        <div class="approval-meta">
                            <span class="approval-submitter">
                                <i class="bi bi-person"></i>
                                {{ req.submitted_by_name || req.submitted_by || "Unknown" }}
                            </span>
                            <span class="approval-date">
                                <i class="bi bi-calendar3"></i>
                                {{ formatDate(req.created_at) }}
                            </span>
                            <span class="approval-items-count">
                                {{ req.items?.length || 0 }} item{{ (req.items?.length || 0) !== 1 ? "s" : "" }}
                            </span>
                        </div>
                        <div class="approval-card-right">
                            <span class="status-chip" :class="statusChipClass(req.status)">
                                {{ req.status }}
                            </span>
                            <button class="btn-approve-all" @click.stop="approveAll(req.id)">
                                <i class="bi bi-check-all"></i>
                                Approve All
                            </button>
                            <i
                                class="bi expand-chevron"
                                :class="expandedRequests.has(req.id) ? 'bi-chevron-up' : 'bi-chevron-down'"
                            ></i>
                        </div>
                    </div>

                    <div v-if="expandedRequests.has(req.id)" class="approval-items">
                        <div
                            v-for="(item, idx) in req.items"
                            :key="idx"
                            class="approval-item-row"
                            :class="`item-status-${(item.status || 'pending').toLowerCase()}`"
                        >
                            <!-- Normal view -->
                            <template v-if="!(editingApprovalItem && editingApprovalItem.requestId === req.id && editingApprovalItem.index === idx)">
                                <div class="approval-item-info">
                                    <span class="approval-item-name">
                                        {{ consumableName(item.data?.consumable_id) }}
                                    </span>
                                    <span class="approval-item-detail">
                                        {{ formatQty(item.data?.quantity) }} units
                                    </span>
                                    <span class="approval-item-detail">
                                        ₹{{ formatMoney(item.data?.unit_cost) }}/unit
                                    </span>
                                    <span v-if="item.data?.supplier" class="approval-item-detail dimmed">
                                        {{ item.data.supplier }}
                                    </span>
                                    <span class="approval-item-detail dimmed">
                                        {{ formatDate(item.data?.purchase_date) }}
                                    </span>
                                    <span
                                        v-if="item.status && item.status !== 'PENDING'"
                                        class="status-chip status-chip-sm"
                                        :class="statusChipClass(item.status)"
                                    >
                                        {{ item.status }}
                                    </span>
                                </div>
                                <div v-if="item.status === 'PENDING' || !item.status" class="approval-item-actions">
                                    <button class="btn-action-sm btn-approve" @click="approveItem(req.id, idx)">
                                        <i class="bi bi-check-lg"></i>
                                        Approve
                                    </button>
                                    <button class="btn-action-sm btn-edit-approval" @click="startEditApproval(req.id, idx, item.data)">
                                        <i class="bi bi-pencil"></i>
                                        Edit &amp; Approve
                                    </button>
                                    <button class="btn-action-sm btn-reject" @click="promptReject(req.id, idx)">
                                        <i class="bi bi-x-lg"></i>
                                        Reject
                                    </button>
                                </div>
                            </template>

                            <!-- Edit-approve inline form -->
                            <template v-else>
                                <div class="approval-edit-form">
                                    <div class="approval-edit-fields">
                                        <div class="ae-field">
                                            <label class="ae-label">Consumable</label>
                                            <select v-model="editingApprovalItem.data.consumable_id" class="form-select form-select-sm">
                                                <option v-for="ci in items" :key="ci.id" :value="ci.id">
                                                    {{ ci.name }}
                                                </option>
                                            </select>
                                        </div>
                                        <div class="ae-field">
                                            <label class="ae-label">Date</label>
                                            <input
                                                v-model="editingApprovalItem.data.purchase_date"
                                                type="date"
                                                class="form-control form-control-sm"
                                            />
                                        </div>
                                        <div class="ae-field">
                                            <label class="ae-label">Qty</label>
                                            <input
                                                v-model="editingApprovalItem.data.quantity"
                                                type="number"
                                                step="0.01"
                                                class="form-control form-control-sm"
                                            />
                                        </div>
                                        <div class="ae-field">
                                            <label class="ae-label">Unit Cost</label>
                                            <input
                                                v-model="editingApprovalItem.data.unit_cost"
                                                type="number"
                                                step="0.01"
                                                class="form-control form-control-sm"
                                            />
                                        </div>
                                        <div class="ae-field">
                                            <label class="ae-label">Supplier</label>
                                            <input
                                                v-model="editingApprovalItem.data.supplier"
                                                type="text"
                                                class="form-control form-control-sm"
                                                placeholder="Optional"
                                            />
                                        </div>
                                    </div>
                                    <div class="approval-edit-btns">
                                        <button class="btn-action-sm btn-approve" @click="submitApproveWithEdits">
                                            <i class="bi bi-check-lg"></i>
                                            Save &amp; Approve
                                        </button>
                                        <button class="btn-action-sm btn-cancel-edit" @click="cancelEditApproval">
                                            <i class="bi bi-x-lg"></i>
                                            Cancel
                                        </button>
                                    </div>
                                </div>
                            </template>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Filter bar -->
            <div class="filter-bar">
                <select
                    v-model="filterConsumableId"
                    class="form-select filter-select"
                    @change="fetchPurchases"
                >
                    <option :value="null">All Consumables</option>
                    <option v-for="ci in items" :key="ci.id" :value="ci.id">
                        {{ ci.name }}
                    </option>
                </select>
                <input
                    v-model="filterFromDate"
                    type="date"
                    class="form-control filter-date"
                    placeholder="From date"
                    @change="fetchPurchases"
                />
                <input
                    v-model="filterToDate"
                    type="date"
                    class="form-control filter-date"
                    placeholder="To date"
                    @change="fetchPurchases"
                />
                <button class="btn-filter-clear" @click="clearFilters" title="Clear filters">
                    <i class="bi bi-x-circle"></i>
                </button>
            </div>

            <!-- Purchases list -->
            <div class="content-panel">
                <div v-if="purchases.length === 0" class="empty-state">
                    <i class="bi bi-receipt"></i>
                    <p>No purchases found</p>
                </div>

                <div v-else>
                    <!-- Desktop table -->
                    <div class="table-wrapper d-none d-md-block">
                        <table class="purchases-table">
                            <thead>
                                <tr>
                                    <th>Date</th>
                                    <th>Consumable</th>
                                    <th class="th-num">Quantity</th>
                                    <th class="th-num">Unit Cost</th>
                                    <th class="th-num">Remaining</th>
                                    <th>Supplier</th>
                                    <th>Invoice</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="p in purchases" :key="p.id" class="purchase-row">
                                    <td class="date-cell">{{ formatDate(p.purchase_date) }}</td>
                                    <td>
                                        <span class="consumable-name-cell">
                                            {{ consumableName(p.consumable_id) }}
                                        </span>
                                    </td>
                                    <td class="num-cell">{{ formatQty(p.quantity) }}</td>
                                    <td class="num-cell">₹{{ formatMoney(p.unit_cost) }}</td>
                                    <td class="num-cell">
                                        <span
                                            class="remaining-chip"
                                            :class="remainingClass(p.quantity_remaining, p.quantity)"
                                        >
                                            {{ formatQty(p.quantity_remaining) }}
                                        </span>
                                    </td>
                                    <td class="secondary-cell">{{ p.supplier || "—" }}</td>
                                    <td class="secondary-cell">{{ p.invoice_number || "—" }}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>

                    <!-- Mobile cards -->
                    <div class="d-md-none purchases-mobile">
                        <div
                            v-for="p in purchases"
                            :key="p.id"
                            class="purchase-card"
                        >
                            <div class="purchase-card-top">
                                <span class="consumable-name-cell">{{ consumableName(p.consumable_id) }}</span>
                                <span class="date-cell">{{ formatDate(p.purchase_date) }}</span>
                            </div>
                            <div class="purchase-card-chips">
                                <span class="chip-data">
                                    <i class="bi bi-box"></i>
                                    {{ formatQty(p.quantity) }} units
                                </span>
                                <span class="chip-data chip-cost">
                                    ₹{{ formatMoney(p.unit_cost) }}/unit
                                </span>
                                <span
                                    class="remaining-chip"
                                    :class="remainingClass(p.quantity_remaining, p.quantity)"
                                >
                                    {{ formatQty(p.quantity_remaining) }} rem.
                                </span>
                            </div>
                            <div v-if="p.supplier || p.invoice_number" class="purchase-card-meta">
                                <span v-if="p.supplier">
                                    <i class="bi bi-truck"></i> {{ p.supplier }}
                                </span>
                                <span v-if="p.invoice_number">
                                    <i class="bi bi-file-text"></i> {{ p.invoice_number }}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Non-admin: My Requests section -->
            <div v-if="!isAdmin && myRequests.length > 0" class="my-requests-panel">
                <div class="my-requests-header">
                    <i class="bi bi-clock-history"></i>
                    <span>My Requests</span>
                </div>

                <div
                    v-for="req in myRequests"
                    :key="req.id"
                    class="my-request-card"
                >
                    <div class="my-request-top">
                        <span class="my-request-date">
                            <i class="bi bi-calendar3"></i>
                            {{ formatDate(req.created_at) }}
                        </span>
                        <span class="status-chip" :class="statusChipClass(req.status)">
                            {{ req.status }}
                        </span>
                    </div>
                    <div class="my-request-items">
                        <div
                            v-for="(item, idx) in req.items"
                            :key="idx"
                            class="my-request-item"
                        >
                            <span class="mri-name">{{ consumableName(item.data?.consumable_id) }}</span>
                            <span class="mri-qty">{{ formatQty(item.data?.quantity) }} units</span>
                            <span class="mri-cost">₹{{ formatMoney(item.data?.unit_cost) }}/unit</span>
                            <span
                                class="status-chip status-chip-sm"
                                :class="statusChipClass(item.status || 'PENDING')"
                            >
                                {{ item.status || "PENDING" }}
                            </span>
                            <span v-if="item.rejection_note" class="mri-note">
                                <i class="bi bi-chat-text"></i> {{ item.rejection_note }}
                            </span>
                        </div>
                    </div>
                    <div v-if="req.notes" class="my-request-notes">
                        <i class="bi bi-sticky"></i> {{ req.notes }}
                    </div>
                </div>
            </div>
        </div>

        <!-- ══════════════════════════════════════════════ -->
        <!-- MODALS                                         -->
        <!-- ══════════════════════════════════════════════ -->

        <!-- Item Modal (Admin) -->
        <div
            class="modal fade"
            id="itemModal"
            tabindex="-1"
            aria-hidden="true"
            ref="itemModalRef"
        >
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content form-modal">
                    <div class="modal-body">
                        <div class="modal-icon" :class="editingItem ? 'icon-edit' : 'icon-add'">
                            <i class="bi" :class="editingItem ? 'bi-pencil' : 'bi-plus-lg'"></i>
                        </div>
                        <h5 class="modal-title">
                            {{ editingItem ? "Edit Consumable" : "Add Consumable" }}
                        </h5>
                        <p v-if="itemFormError" class="form-error">{{ itemFormError }}</p>

                        <form class="consumable-form" @submit.prevent="submitItemForm">
                            <div class="form-group">
                                <label class="form-label" for="ciName">Name</label>
                                <input
                                    id="ciName"
                                    v-model="itemForm.name"
                                    type="text"
                                    class="form-control"
                                    placeholder="e.g. Fertiliser NPK"
                                    required
                                />
                            </div>
                            <div class="form-group">
                                <label class="form-label" for="ciUnit">Unit</label>
                                <input
                                    id="ciUnit"
                                    v-model="itemForm.unit"
                                    type="text"
                                    class="form-control"
                                    placeholder="e.g. kg, L, bags"
                                    required
                                />
                            </div>
                            <div class="form-group">
                                <label class="form-label" for="ciDesc">Description</label>
                                <textarea
                                    id="ciDesc"
                                    v-model="itemForm.description"
                                    class="form-control"
                                    rows="2"
                                    placeholder="Optional description"
                                ></textarea>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn-modal btn-modal-cancel" data-bs-dismiss="modal">
                            Cancel
                        </button>
                        <button
                            type="button"
                            class="btn-modal btn-modal-confirm"
                            :disabled="!itemForm.name.trim() || !itemForm.unit.trim()"
                            @click="submitItemForm"
                        >
                            {{ editingItem ? "Save Changes" : "Add Item" }}
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Purchase Modal (Admin) -->
        <div
            class="modal fade"
            id="purchaseModal"
            tabindex="-1"
            aria-hidden="true"
            ref="purchaseModalRef"
        >
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content form-modal">
                    <div class="modal-body">
                        <div class="modal-icon icon-add">
                            <i class="bi bi-cart-plus"></i>
                        </div>
                        <h5 class="modal-title">Add Purchase</h5>
                        <p v-if="purchaseFormError" class="form-error">{{ purchaseFormError }}</p>

                        <form class="consumable-form" @submit.prevent="submitPurchaseForm">
                            <div class="form-group">
                                <label class="form-label" for="pConsumable">Consumable</label>
                                <select
                                    id="pConsumable"
                                    v-model="purchaseForm.consumable_id"
                                    class="form-select"
                                    required
                                >
                                    <option :value="null" disabled>Select consumable</option>
                                    <option v-for="ci in items" :key="ci.id" :value="ci.id">
                                        {{ ci.name }} ({{ ci.unit }})
                                    </option>
                                </select>
                            </div>
                            <div class="form-row">
                                <div class="form-group flex-1">
                                    <label class="form-label" for="pDate">Purchase Date</label>
                                    <input
                                        id="pDate"
                                        v-model="purchaseForm.purchase_date"
                                        type="date"
                                        class="form-control"
                                        required
                                    />
                                </div>
                                <div class="form-group flex-1">
                                    <label class="form-label" for="pQty">Quantity</label>
                                    <input
                                        id="pQty"
                                        v-model="purchaseForm.quantity"
                                        type="number"
                                        step="0.01"
                                        min="0.01"
                                        class="form-control"
                                        placeholder="0.00"
                                        required
                                    />
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="form-group flex-1">
                                    <label class="form-label" for="pUnitCost">Unit Cost (₹)</label>
                                    <input
                                        id="pUnitCost"
                                        v-model="purchaseForm.unit_cost"
                                        type="number"
                                        step="0.01"
                                        min="0"
                                        class="form-control"
                                        placeholder="0.00"
                                        required
                                    />
                                </div>
                                <div class="form-group flex-1">
                                    <label class="form-label" for="pSupplier">Supplier</label>
                                    <input
                                        id="pSupplier"
                                        v-model="purchaseForm.supplier"
                                        type="text"
                                        class="form-control"
                                        placeholder="Optional"
                                    />
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="form-group flex-1">
                                    <label class="form-label" for="pInvoice">Invoice Number</label>
                                    <input
                                        id="pInvoice"
                                        v-model="purchaseForm.invoice_number"
                                        type="text"
                                        class="form-control"
                                        placeholder="Optional"
                                    />
                                </div>
                            </div>
                            <div class="form-group">
                                <label class="form-label" for="pNotes">Notes</label>
                                <textarea
                                    id="pNotes"
                                    v-model="purchaseForm.notes"
                                    class="form-control"
                                    rows="2"
                                    placeholder="Optional notes"
                                ></textarea>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn-modal btn-modal-cancel" data-bs-dismiss="modal">
                            Cancel
                        </button>
                        <button
                            type="button"
                            class="btn-modal btn-modal-confirm"
                            :disabled="!isPurchaseFormValid"
                            @click="submitPurchaseForm"
                        >
                            Add Purchase
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Request Modal (Non-admin) -->
        <div
            class="modal fade"
            id="requestModal"
            tabindex="-1"
            aria-hidden="true"
            ref="requestModalRef"
        >
            <div class="modal-dialog modal-dialog-centered modal-lg">
                <div class="modal-content form-modal">
                    <div class="modal-body">
                        <div class="modal-icon icon-add">
                            <i class="bi bi-send"></i>
                        </div>
                        <h5 class="modal-title">Submit Purchase Request</h5>

                        <div class="request-rows-container">
                            <div
                                v-for="(row, idx) in requestRows"
                                :key="idx"
                                class="request-row-item"
                            >
                                <div class="request-row-header">
                                    <span class="request-row-num">Item {{ idx + 1 }}</span>
                                    <button
                                        v-if="requestRows.length > 1"
                                        type="button"
                                        class="btn-remove-row"
                                        @click="removeRequestRow(idx)"
                                    >
                                        <i class="bi bi-x-lg"></i>
                                    </button>
                                </div>
                                <div class="request-row-fields">
                                    <div class="form-group">
                                        <label class="form-label">Consumable</label>
                                        <select v-model="row.consumable_id" class="form-select form-select-sm">
                                            <option :value="null" disabled>Select</option>
                                            <option v-for="ci in items" :key="ci.id" :value="ci.id">
                                                {{ ci.name }} ({{ ci.unit }})
                                            </option>
                                        </select>
                                    </div>
                                    <div class="form-row-sm">
                                        <div class="form-group flex-1">
                                            <label class="form-label">Date</label>
                                            <input
                                                v-model="row.purchase_date"
                                                type="date"
                                                class="form-control form-control-sm"
                                            />
                                        </div>
                                        <div class="form-group flex-1">
                                            <label class="form-label">Quantity</label>
                                            <input
                                                v-model="row.quantity"
                                                type="number"
                                                step="0.01"
                                                min="0.01"
                                                class="form-control form-control-sm"
                                                placeholder="0.00"
                                            />
                                        </div>
                                        <div class="form-group flex-1">
                                            <label class="form-label">Unit Cost (₹)</label>
                                            <input
                                                v-model="row.unit_cost"
                                                type="number"
                                                step="0.01"
                                                min="0"
                                                class="form-control form-control-sm"
                                                placeholder="0.00"
                                            />
                                        </div>
                                        <div class="form-group flex-1">
                                            <label class="form-label">Supplier</label>
                                            <input
                                                v-model="row.supplier"
                                                type="text"
                                                class="form-control form-control-sm"
                                                placeholder="Optional"
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <button type="button" class="btn-add-row" @click="addRequestRow">
                            <i class="bi bi-plus-lg"></i>
                            Add Another Item
                        </button>

                        <div class="form-group mt-3">
                            <label class="form-label" for="reqNotes">Request Notes</label>
                            <textarea
                                id="reqNotes"
                                v-model="requestNotes"
                                class="form-control"
                                rows="2"
                                placeholder="Optional notes for this request"
                            ></textarea>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn-modal btn-modal-cancel" data-bs-dismiss="modal">
                            Cancel
                        </button>
                        <button
                            type="button"
                            class="btn-modal btn-modal-confirm"
                            :disabled="!isRequestFormValid"
                            @click="submitRequest"
                        >
                            <i class="bi bi-send"></i>
                            Submit Request
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Reject Prompt Modal -->
        <div
            class="modal fade"
            id="rejectModal"
            tabindex="-1"
            aria-hidden="true"
            ref="rejectModalRef"
        >
            <div class="modal-dialog modal-dialog-centered modal-sm">
                <div class="modal-content confirm-modal">
                    <div class="modal-body">
                        <div class="modal-icon icon-delete">
                            <i class="bi bi-x-circle"></i>
                        </div>
                        <h5 class="modal-title">Reject Item</h5>
                        <p class="modal-desc">Provide a reason for rejection (optional).</p>
                        <textarea
                            v-model="rejectNote"
                            class="form-control mt-2"
                            rows="2"
                            placeholder="Rejection note..."
                        ></textarea>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn-modal btn-modal-cancel" data-bs-dismiss="modal">
                            Cancel
                        </button>
                        <button type="button" class="btn-modal btn-modal-confirm btn-modal-danger" @click="confirmReject">
                            Reject
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
import api from "../utils/api";
import { useAuthStore } from "../stores/auth";

// ── Auth ─────────────────────────────────────────────
const auth = useAuthStore();
const isAdmin = computed(() => {
    const roles = auth.userRoles;
    if (!roles) return false;
    if (Array.isArray(roles)) return roles.includes("admin");
    if (typeof roles === "string") return roles === "admin";
    if (roles && typeof roles === "object") return roles.name === "admin";
    return false;
});

// ── Tab ──────────────────────────────────────────────
const activeTab = ref("items");

// ── Items tab state ──────────────────────────────────
const items = ref([]);
const searchItems = ref("");

// ── Purchases tab state ──────────────────────────────
const purchases = ref([]);
const filterConsumableId = ref(null);
const filterFromDate = ref("");
const filterToDate = ref("");

// ── Approval state ───────────────────────────────────
const approvals = ref([]);
const expandedRequests = ref(new Set());
const editingApprovalItem = ref(null); // { requestId, index, data }

// Reject flow
const rejectTarget = ref(null); // { requestId, index }
const rejectNote = ref("");

// ── Modal refs ───────────────────────────────────────
const itemModalRef = ref(null);
const purchaseModalRef = ref(null);
const requestModalRef = ref(null);
const rejectModalRef = ref(null);
let bsItemModal = null;
let bsPurchaseModal = null;
let bsRequestModal = null;
let bsRejectModal = null;

// ── Item form ────────────────────────────────────────
const editingItem = ref(null);
const itemForm = ref({ name: "", unit: "", description: "" });
const itemFormError = ref("");

// ── Purchase form ────────────────────────────────────
const purchaseForm = ref({
    consumable_id: null,
    purchase_date: "",
    quantity: "",
    unit_cost: "",
    supplier: "",
    invoice_number: "",
    notes: "",
});
const purchaseFormError = ref("");

const isPurchaseFormValid = computed(() => {
    const f = purchaseForm.value;
    return (
        f.consumable_id !== null &&
        f.purchase_date !== "" &&
        String(f.quantity).trim() !== "" &&
        Number(f.quantity) > 0 &&
        String(f.unit_cost).trim() !== "" &&
        Number(f.unit_cost) >= 0
    );
});

// ── Request form (non-admin) ─────────────────────────
const requestNotes = ref("");
const requestRows = ref([
    { consumable_id: null, purchase_date: "", quantity: "", unit_cost: "", supplier: "" },
]);

const isRequestFormValid = computed(() => {
    return requestRows.value.every(
        (r) =>
            r.consumable_id !== null &&
            r.purchase_date !== "" &&
            String(r.quantity).trim() !== "" &&
            Number(r.quantity) > 0 &&
            String(r.unit_cost).trim() !== "" &&
            Number(r.unit_cost) >= 0
    );
});

// ── Computed ─────────────────────────────────────────
const pendingApprovals = computed(() =>
    approvals.value.filter((a) => a.status === "PENDING" || a.status === "PARTIAL")
);

const myRequests = computed(() => approvals.value);

// ── Helpers ──────────────────────────────────────────
function formatDate(d) {
    return d
        ? new Date(d).toLocaleDateString("en-IN", {
              day: "2-digit",
              month: "short",
              year: "numeric",
          })
        : "—";
}

function consumableName(id) {
    return items.value.find((i) => i.id === id)?.name || (id ? `#${id}` : "—");
}

function formatQty(v) {
    if (v == null || v === "") return "—";
    const n = Number(v);
    return isNaN(n) ? v : n.toLocaleString("en-IN", { maximumFractionDigits: 3 });
}

function formatMoney(v) {
    if (v == null || v === "") return "—";
    const n = Number(v);
    return isNaN(n)
        ? v
        : n.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function remainingClass(remaining, total) {
    if (remaining == null || total == null) return "remaining-unknown";
    const r = Number(remaining);
    const t = Number(total);
    if (t === 0) return "remaining-unknown";
    const pct = r / t;
    if (pct <= 0) return "remaining-empty";
    if (pct <= 0.25) return "remaining-low";
    return "remaining-ok";
}

function statusChipClass(status) {
    if (!status) return "";
    const s = status.toUpperCase();
    if (s === "PENDING") return "status-pending";
    if (s === "PARTIAL") return "status-partial";
    if (s === "APPROVED") return "status-active";
    if (s === "REJECTED") return "status-inactive";
    return "";
}

// ── Fetch ────────────────────────────────────────────
async function fetchItems() {
    try {
        const params = {};
        if (searchItems.value) params.search = searchItems.value;
        const res = await api.get("/consumables/", { params });
        items.value = res.data;
    } catch (err) {
        console.error("Failed to fetch consumables:", err);
    }
}

async function fetchPurchases() {
    try {
        const params = {};
        if (filterConsumableId.value) params.consumable_id = filterConsumableId.value;
        if (filterFromDate.value) params.from_date = filterFromDate.value;
        if (filterToDate.value) params.to_date = filterToDate.value;
        const res = await api.get("/consumables/purchases", { params });
        purchases.value = res.data;
    } catch (err) {
        console.error("Failed to fetch purchases:", err);
    }
}

async function fetchApprovals() {
    try {
        const res = await api.get("/approvals/");
        approvals.value = res.data.filter((a) => a.type === "CONSUMABLE_PURCHASE");
    } catch (err) {
        console.error("Failed to fetch approvals:", err);
    }
}

function clearFilters() {
    filterConsumableId.value = null;
    filterFromDate.value = "";
    filterToDate.value = "";
    fetchPurchases();
}

// ── Item Modal ───────────────────────────────────────
function openItemModal(item) {
    editingItem.value = item;
    itemFormError.value = "";
    if (item) {
        itemForm.value = { name: item.name, unit: item.unit, description: item.description || "" };
    } else {
        itemForm.value = { name: "", unit: "", description: "" };
    }
    if (!bsItemModal) bsItemModal = new Modal(itemModalRef.value);
    bsItemModal.show();
}

async function submitItemForm() {
    itemFormError.value = "";
    if (!itemForm.value.name.trim() || !itemForm.value.unit.trim()) return;
    try {
        const payload = {
            name: itemForm.value.name.trim(),
            unit: itemForm.value.unit.trim(),
            description: itemForm.value.description.trim() || null,
        };
        if (editingItem.value) {
            const res = await api.put(`/consumables/${editingItem.value.id}`, payload);
            const idx = items.value.findIndex((i) => i.id === editingItem.value.id);
            if (idx !== -1) items.value[idx] = res.data;
        } else {
            const res = await api.post("/consumables/", payload);
            items.value.push(res.data);
        }
        bsItemModal.hide();
    } catch (err) {
        itemFormError.value =
            err.response?.data?.detail || "Failed to save item. Please try again.";
    }
}

async function toggleActive(item) {
    try {
        const res = await api.put(`/consumables/${item.id}`, {
            name: item.name,
            unit: item.unit,
            description: item.description || null,
            is_active: !item.is_active,
        });
        const idx = items.value.findIndex((i) => i.id === item.id);
        if (idx !== -1) items.value[idx] = res.data;
    } catch (err) {
        console.error("Failed to toggle active state:", err);
    }
}

// ── Purchase Modal ───────────────────────────────────
function openPurchaseModal() {
    purchaseFormError.value = "";
    purchaseForm.value = {
        consumable_id: null,
        purchase_date: "",
        quantity: "",
        unit_cost: "",
        supplier: "",
        invoice_number: "",
        notes: "",
    };
    if (!bsPurchaseModal) bsPurchaseModal = new Modal(purchaseModalRef.value);
    bsPurchaseModal.show();
}

async function submitPurchaseForm() {
    purchaseFormError.value = "";
    if (!isPurchaseFormValid.value) return;
    try {
        const payload = {
            purchase_date: purchaseForm.value.purchase_date,
            quantity: String(purchaseForm.value.quantity),
            unit_cost: String(purchaseForm.value.unit_cost),
            supplier: purchaseForm.value.supplier.trim() || null,
            invoice_number: purchaseForm.value.invoice_number.trim() || null,
            notes: purchaseForm.value.notes.trim() || null,
        };
        const res = await api.post(
            `/consumables/${purchaseForm.value.consumable_id}/purchases`,
            payload
        );
        purchases.value.unshift(res.data);
        bsPurchaseModal.hide();
        // Refresh items to update stock totals
        await fetchItems();
    } catch (err) {
        purchaseFormError.value =
            err.response?.data?.detail || "Failed to add purchase. Please try again.";
    }
}

// ── Request Modal ────────────────────────────────────
function openRequestModal() {
    requestNotes.value = "";
    requestRows.value = [
        { consumable_id: null, purchase_date: "", quantity: "", unit_cost: "", supplier: "" },
    ];
    if (!bsRequestModal) bsRequestModal = new Modal(requestModalRef.value);
    bsRequestModal.show();
}

function addRequestRow() {
    requestRows.value.push({
        consumable_id: null,
        purchase_date: "",
        quantity: "",
        unit_cost: "",
        supplier: "",
    });
}

function removeRequestRow(idx) {
    requestRows.value.splice(idx, 1);
}

async function submitRequest() {
    if (!isRequestFormValid.value) return;
    try {
        const requestItems = requestRows.value.map((row, idx) => ({
            index: idx,
            status: "pending",
            data: {
                consumable_id: row.consumable_id,
                purchase_date: row.purchase_date
                    ? new Date(row.purchase_date).toISOString()
                    : null,
                quantity: String(row.quantity),
                unit_cost: String(row.unit_cost),
                supplier: row.supplier.trim() || null,
            },
        }));
        await api.post("/approvals/", {
            type: "CONSUMABLE_PURCHASE",
            items: requestItems,
            notes: requestNotes.value.trim() || "",
        });
        bsRequestModal.hide();
        await fetchApprovals();
    } catch (err) {
        console.error("Failed to submit request:", err);
    }
}

// ── Approval Actions ─────────────────────────────────
function toggleExpanded(requestId) {
    const s = new Set(expandedRequests.value);
    if (s.has(requestId)) {
        s.delete(requestId);
    } else {
        s.add(requestId);
    }
    expandedRequests.value = s;
}

async function approveItem(requestId, index) {
    try {
        await api.patch(`/approvals/${requestId}/items/${index}`, { action: "approve" });
        await fetchApprovals();
        await fetchPurchases();
        await fetchItems();
    } catch (err) {
        console.error("Failed to approve item:", err);
    }
}

function startEditApproval(requestId, index, data) {
    editingApprovalItem.value = {
        requestId,
        index,
        data: {
            consumable_id: data?.consumable_id ?? null,
            purchase_date: data?.purchase_date
                ? data.purchase_date.slice(0, 10)
                : "",
            quantity: data?.quantity ?? "",
            unit_cost: data?.unit_cost ?? "",
            supplier: data?.supplier ?? "",
        },
    };
}

function cancelEditApproval() {
    editingApprovalItem.value = null;
}

async function submitApproveWithEdits() {
    if (!editingApprovalItem.value) return;
    const { requestId, index, data } = editingApprovalItem.value;
    try {
        await api.patch(`/approvals/${requestId}/items/${index}`, {
            action: "approve_with_edits",
            modified_data: {
                consumable_id: data.consumable_id,
                purchase_date: data.purchase_date
                    ? new Date(data.purchase_date).toISOString()
                    : null,
                quantity: String(data.quantity),
                unit_cost: String(data.unit_cost),
                supplier: data.supplier?.trim() || null,
            },
        });
        editingApprovalItem.value = null;
        await fetchApprovals();
        await fetchPurchases();
        await fetchItems();
    } catch (err) {
        console.error("Failed to approve with edits:", err);
    }
}

function promptReject(requestId, index) {
    rejectTarget.value = { requestId, index };
    rejectNote.value = "";
    if (!bsRejectModal) bsRejectModal = new Modal(rejectModalRef.value);
    bsRejectModal.show();
}

async function confirmReject() {
    if (!rejectTarget.value) return;
    const { requestId, index } = rejectTarget.value;
    try {
        await api.patch(`/approvals/${requestId}/items/${index}`, {
            action: "reject",
            rejection_note: rejectNote.value.trim() || null,
        });
        bsRejectModal.hide();
        await fetchApprovals();
    } catch (err) {
        console.error("Failed to reject item:", err);
    }
}

async function approveAll(requestId) {
    try {
        await api.post(`/approvals/${requestId}/approve-all`);
        await fetchApprovals();
        await fetchPurchases();
        await fetchItems();
    } catch (err) {
        console.error("Failed to approve all:", err);
    }
}

// ── Lifecycle ────────────────────────────────────────
onMounted(async () => {
    await Promise.all([fetchItems(), fetchPurchases(), fetchApprovals()]);
});

onBeforeUnmount(() => {
    bsItemModal?.dispose();
    bsPurchaseModal?.dispose();
    bsRequestModal?.dispose();
    bsRejectModal?.dispose();
});
</script>

<style scoped>
/* ── Page Layout ────────────────────────────── */
.consumables-page {
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
    letter-spacing: 0.01em;
}

.header-actions {
    display: flex;
    gap: 8px;
    align-items: center;
    flex-shrink: 0;
}

/* ── Buttons ────────────────────────────────── */
.btn-add {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    padding: 9px 18px;
    border: none;
    border-radius: 10px;
    background: var(--moss);
    color: var(--white);
    font-family: var(--font-body);
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    transition: all var(--transition-fast);
    white-space: nowrap;
}

.btn-add:hover {
    background: var(--moss-light);
    box-shadow: 0 4px 12px var(--moss-faded);
}

.btn-add i {
    font-size: 1rem;
}

.btn-add-secondary {
    background: var(--sienna);
}

.btn-add-secondary:hover {
    background: var(--sienna-light);
    box-shadow: 0 4px 12px rgba(181, 105, 77, 0.25);
}

/* ── Tab Bar ────────────────────────────────── */
.tab-bar {
    display: flex;
    gap: 6px;
    margin-bottom: 20px;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    padding-bottom: 2px;
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
    flex-shrink: 0;
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
    font-size: 1rem;
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
    background: var(--moss-faded);
    color: var(--moss);
}

/* ── Filter Bar ─────────────────────────────── */
.filter-bar {
    display: flex;
    gap: 10px;
    margin-bottom: 16px;
    flex-wrap: wrap;
    align-items: center;
}

.search-wrap {
    position: relative;
    flex: 1;
    min-width: 200px;
}

.search-icon {
    position: absolute;
    left: 12px;
    top: 50%;
    transform: translateY(-50%);
    color: var(--text-secondary);
    font-size: 0.85rem;
    pointer-events: none;
}

.search-input {
    padding-left: 34px;
    font-size: 0.85rem;
}

.filter-select {
    min-width: 180px;
    font-size: 0.85rem;
    flex-shrink: 0;
}

.filter-date {
    min-width: 140px;
    font-size: 0.85rem;
    flex-shrink: 0;
}

.btn-filter-clear {
    border: none;
    background: transparent;
    color: var(--text-secondary);
    font-size: 1.1rem;
    cursor: pointer;
    padding: 4px 6px;
    border-radius: 7px;
    transition: color var(--transition-fast);
    flex-shrink: 0;
}

.btn-filter-clear:hover {
    color: var(--sienna);
}

/* ── Content Panel ──────────────────────────── */
.content-panel {
    background: var(--bg-card);
    border: 1px solid var(--border-light);
    border-radius: 14px;
    box-shadow: var(--shadow-sm);
    overflow: hidden;
}

/* ── Items List ─────────────────────────────── */
.items-list {
    position: relative;
}

.item-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px 18px;
    border-bottom: 1px solid var(--border-light);
    transition: background var(--transition-fast);
}

.item-row:last-child {
    border-bottom: none;
}

.item-row:hover {
    background: rgba(138, 154, 123, 0.04);
}

.item-row.inactive {
    opacity: 0.6;
}

.item-info {
    display: flex;
    align-items: center;
    gap: 10px;
    flex: 1;
    min-width: 0;
    flex-wrap: wrap;
}

.item-id {
    font-size: 0.72rem;
    font-weight: 600;
    color: var(--text-secondary);
    opacity: 0.6;
    font-variant-numeric: tabular-nums;
    flex-shrink: 0;
}

.item-name {
    font-weight: 600;
    font-size: 0.9rem;
    color: var(--text-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.badge-unit {
    display: inline-flex;
    align-items: center;
    font-size: 0.7rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 20px;
    background: rgba(138, 154, 123, 0.14);
    color: var(--sage);
    letter-spacing: 0.04em;
    text-transform: uppercase;
    white-space: nowrap;
    flex-shrink: 0;
}

.item-desc {
    font-size: 0.78rem;
    color: var(--text-secondary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    min-width: 0;
}

.item-desc::before {
    content: "—";
    margin-right: 6px;
    opacity: 0.4;
}

.item-stock {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-shrink: 0;
    font-size: 0.8rem;
}

.stock-label {
    color: var(--text-secondary);
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.02em;
    text-transform: uppercase;
}

.stock-value {
    font-weight: 600;
    font-variant-numeric: tabular-nums;
    color: var(--text-primary);
    font-size: 0.84rem;
}

.stock-remaining {
    color: var(--moss);
}

.stock-sep {
    color: var(--border);
    margin: 0 2px;
}

.item-actions {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-shrink: 0;
}

/* ── Action Buttons ─────────────────────────── */
.btn-action {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    border: 1.5px solid var(--border);
    background: transparent;
    color: var(--text-secondary);
    font-size: 0.9rem;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    transition: all var(--transition-fast);
}

.btn-edit:hover {
    border-color: var(--harvest);
    color: #8a6f2a;
    background: rgba(196, 163, 90, 0.08);
}

.btn-toggle-off:hover {
    border-color: var(--sienna);
    color: var(--sienna);
    background: rgba(181, 105, 77, 0.06);
}

.btn-toggle-on:hover {
    border-color: var(--moss);
    color: var(--moss);
    background: rgba(74, 103, 65, 0.06);
}

/* ── Status Chips ───────────────────────────── */
.status-chip {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 0.72rem;
    font-weight: 600;
    padding: 3px 9px;
    border-radius: 20px;
    letter-spacing: 0.01em;
    white-space: nowrap;
    flex-shrink: 0;
}

.status-chip i {
    font-size: 0.68rem;
}

.status-chip-sm {
    font-size: 0.66rem;
    padding: 2px 7px;
}

.status-active {
    background: rgba(74, 103, 65, 0.1);
    color: var(--moss);
}

.status-inactive {
    background: rgba(181, 105, 77, 0.1);
    color: var(--sienna);
}

.status-pending {
    background: rgba(196, 163, 90, 0.14);
    color: #8a6f2a;
}

.status-partial {
    background: rgba(138, 154, 123, 0.14);
    color: var(--sage);
}

/* ── Purchases Table ────────────────────────── */
.table-wrapper {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
}

.purchases-table {
    width: 100%;
    min-width: 680px;
    border-collapse: collapse;
}

.purchases-table thead th {
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--text-secondary);
    padding: 14px 18px;
    border-bottom: 1px solid var(--border-light);
    background: var(--parchment-deep);
    text-align: left;
    white-space: nowrap;
}

.th-num {
    text-align: right !important;
}

.purchases-table tbody tr {
    transition: background var(--transition-fast);
}

.purchases-table tbody tr:hover {
    background: rgba(138, 154, 123, 0.05);
}

.purchases-table tbody td {
    padding: 12px 18px;
    border-bottom: 1px solid var(--border-light);
    vertical-align: middle;
    font-size: 0.88rem;
}

.purchases-table tbody tr:last-child td {
    border-bottom: none;
}

.date-cell {
    font-size: 0.82rem;
    color: var(--text-secondary);
    white-space: nowrap;
    font-variant-numeric: tabular-nums;
}

.consumable-name-cell {
    font-weight: 600;
    color: var(--text-primary);
    font-size: 0.88rem;
}

.num-cell {
    text-align: right;
    font-variant-numeric: tabular-nums;
    font-weight: 600;
    font-size: 0.88rem;
}

.secondary-cell {
    font-size: 0.82rem;
    color: var(--text-secondary);
}

.remaining-chip {
    display: inline-flex;
    align-items: center;
    font-size: 0.75rem;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 20px;
    font-variant-numeric: tabular-nums;
}

.remaining-ok {
    background: rgba(74, 103, 65, 0.1);
    color: var(--moss);
}

.remaining-low {
    background: rgba(196, 163, 90, 0.14);
    color: #8a6f2a;
}

.remaining-empty {
    background: rgba(181, 105, 77, 0.1);
    color: var(--sienna);
}

.remaining-unknown {
    background: var(--border-light);
    color: var(--text-secondary);
}

/* ── Mobile Purchase Cards ──────────────────── */
.purchases-mobile {
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.purchase-card {
    background: var(--parchment-deep);
    border: 1px solid var(--border-light);
    border-radius: 12px;
    padding: 14px;
}

.purchase-card-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 10px;
}

.purchase-card-chips {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-bottom: 8px;
}

.chip-data {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 0.78rem;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 20px;
    background: rgba(138, 154, 123, 0.1);
    color: var(--text-primary);
}

.chip-data i {
    font-size: 0.7rem;
    color: var(--text-secondary);
}

.chip-cost {
    background: rgba(181, 105, 77, 0.08);
    color: var(--sienna);
}

.purchase-card-meta {
    display: flex;
    gap: 14px;
    font-size: 0.78rem;
    color: var(--text-secondary);
    flex-wrap: wrap;
}

.purchase-card-meta i {
    margin-right: 4px;
    font-size: 0.72rem;
}

/* ── Approvals Panel ────────────────────────── */
.approvals-panel {
    background: var(--bg-card);
    border: 1.5px solid rgba(196, 163, 90, 0.3);
    border-radius: 14px;
    box-shadow: var(--shadow-sm);
    overflow: hidden;
    margin-bottom: 20px;
}

.approvals-panel-header {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 14px 18px;
    background: rgba(196, 163, 90, 0.06);
    border-bottom: 1px solid rgba(196, 163, 90, 0.2);
    font-size: 0.85rem;
    font-weight: 700;
    color: #8a6f2a;
    letter-spacing: 0.01em;
}

.approvals-panel-header i {
    font-size: 1rem;
}

.approvals-count {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 22px;
    height: 22px;
    padding: 0 6px;
    border-radius: 11px;
    background: rgba(196, 163, 90, 0.18);
    font-size: 0.72rem;
    font-weight: 700;
    color: #8a6f2a;
}

.approval-card {
    border-bottom: 1px solid var(--border-light);
}

.approval-card:last-child {
    border-bottom: none;
}

.approval-card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 14px 18px;
    cursor: pointer;
    transition: background var(--transition-fast);
}

.approval-card-header:hover {
    background: rgba(138, 154, 123, 0.04);
}

.approval-meta {
    display: flex;
    align-items: center;
    gap: 14px;
    flex-wrap: wrap;
}

.approval-submitter,
.approval-date,
.approval-items-count {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 0.82rem;
    color: var(--text-secondary);
}

.approval-submitter {
    font-weight: 600;
    color: var(--text-primary);
}

.approval-submitter i,
.approval-date i {
    font-size: 0.78rem;
    color: var(--text-secondary);
}

.approval-card-right {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-shrink: 0;
}

.expand-chevron {
    color: var(--text-secondary);
    font-size: 0.85rem;
    transition: transform var(--transition-fast);
}

.btn-approve-all {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    border: 1.5px solid var(--moss);
    border-radius: 8px;
    background: transparent;
    color: var(--moss);
    font-family: var(--font-body);
    font-size: 0.78rem;
    font-weight: 600;
    cursor: pointer;
    transition: all var(--transition-fast);
    white-space: nowrap;
}

.btn-approve-all:hover {
    background: rgba(74, 103, 65, 0.08);
}

.approval-items {
    border-top: 1px solid var(--border-light);
    background: var(--parchment-deep);
}

.approval-item-row {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;
    padding: 12px 18px;
    border-bottom: 1px solid var(--border-light);
    transition: background var(--transition-fast);
}

.approval-item-row:last-child {
    border-bottom: none;
}

.approval-item-row.item-status-approved {
    background: rgba(74, 103, 65, 0.04);
}

.approval-item-row.item-status-rejected {
    background: rgba(181, 105, 77, 0.04);
}

.approval-item-info {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    flex: 1;
    min-width: 0;
}

.approval-item-name {
    font-weight: 600;
    font-size: 0.88rem;
    color: var(--text-primary);
}

.approval-item-detail {
    font-size: 0.78rem;
    color: var(--text-secondary);
    font-variant-numeric: tabular-nums;
}

.approval-item-detail.dimmed {
    opacity: 0.7;
}

.approval-item-actions {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-shrink: 0;
}

.btn-action-sm {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 5px 12px;
    border: 1.5px solid var(--border);
    border-radius: 7px;
    background: transparent;
    color: var(--text-secondary);
    font-family: var(--font-body);
    font-size: 0.76rem;
    font-weight: 600;
    cursor: pointer;
    transition: all var(--transition-fast);
    white-space: nowrap;
}

.btn-action-sm i {
    font-size: 0.78rem;
}

.btn-approve {
    border-color: var(--moss);
    color: var(--moss);
}

.btn-approve:hover {
    background: rgba(74, 103, 65, 0.08);
}

.btn-edit-approval {
    border-color: var(--harvest);
    color: #8a6f2a;
}

.btn-edit-approval:hover {
    background: rgba(196, 163, 90, 0.08);
}

.btn-reject {
    border-color: var(--sienna);
    color: var(--sienna);
}

.btn-reject:hover {
    background: rgba(181, 105, 77, 0.06);
}

.btn-cancel-edit {
    border-color: var(--border);
    color: var(--text-secondary);
}

.btn-cancel-edit:hover {
    border-color: var(--sienna);
    color: var(--sienna);
}

/* ── Approval Edit Inline Form ──────────────── */
.approval-edit-form {
    width: 100%;
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.approval-edit-fields {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    align-items: flex-end;
}

.ae-field {
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 120px;
    flex: 1;
}

.ae-label {
    font-size: 0.7rem;
    font-weight: 600;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

.approval-edit-btns {
    display: flex;
    gap: 8px;
}

/* ── My Requests Panel ──────────────────────── */
.my-requests-panel {
    margin-top: 24px;
    background: var(--bg-card);
    border: 1.5px solid var(--border-light);
    border-radius: 14px;
    overflow: hidden;
    box-shadow: var(--shadow-sm);
}

.my-requests-header {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 14px 18px;
    border-bottom: 1px solid var(--border-light);
    font-size: 0.85rem;
    font-weight: 700;
    color: var(--text-primary);
    background: var(--parchment-deep);
}

.my-request-card {
    padding: 14px 18px;
    border-bottom: 1px solid var(--border-light);
}

.my-request-card:last-child {
    border-bottom: none;
}

.my-request-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}

.my-request-date {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 0.8rem;
    color: var(--text-secondary);
}

.my-request-items {
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.my-request-item {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    padding: 6px 10px;
    background: var(--parchment-deep);
    border-radius: 8px;
    font-size: 0.82rem;
}

.mri-name {
    font-weight: 600;
    color: var(--text-primary);
}

.mri-qty,
.mri-cost {
    font-variant-numeric: tabular-nums;
    color: var(--text-secondary);
}

.mri-note {
    font-size: 0.76rem;
    color: var(--sienna);
    font-style: italic;
    display: inline-flex;
    align-items: center;
    gap: 4px;
    width: 100%;
}

.my-request-notes {
    margin-top: 8px;
    font-size: 0.78rem;
    color: var(--text-secondary);
    font-style: italic;
    display: flex;
    align-items: flex-start;
    gap: 6px;
}

/* ── Empty State ────────────────────────────── */
.empty-state {
    text-align: center;
    padding: 48px 20px;
    color: var(--text-secondary);
}

.empty-state i {
    font-size: 2.4rem;
    opacity: 0.3;
    margin-bottom: 10px;
    display: block;
}

.empty-state p {
    font-size: 0.9rem;
    margin: 0;
}

/* ── Form Modal ─────────────────────────────── */
.form-modal {
    border: none;
    border-radius: 16px;
    box-shadow: var(--shadow-lg);
    overflow: hidden;
    background: var(--bg-card);
}

.form-modal .modal-body {
    padding: 28px 24px 8px;
    text-align: center;
}

.consumable-form {
    text-align: left;
    margin-top: 20px;
}

.form-group {
    margin-bottom: 16px;
}

.form-row {
    display: flex;
    gap: 12px;
}

.form-row-sm {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}

.flex-1 {
    flex: 1;
}

.form-error {
    margin-top: 8px;
    padding: 8px 12px;
    border-radius: 8px;
    background: rgba(181, 105, 77, 0.08);
    border: 1px solid rgba(181, 105, 77, 0.2);
    color: var(--sienna);
    font-size: 0.82rem;
    text-align: left;
}

/* ── Confirm Modal ──────────────────────────── */
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

.icon-add {
    background: rgba(74, 103, 65, 0.1);
    color: var(--moss);
}

.icon-edit {
    background: rgba(196, 163, 90, 0.12);
    color: #8a6f2a;
}

.icon-delete {
    background: rgba(181, 105, 77, 0.1);
    color: var(--sienna);
}

.modal-title {
    font-family: var(--font-display);
    font-size: 1.15rem;
    margin: 0 0 8px;
    color: var(--text-primary);
}

.modal-desc {
    font-size: 0.85rem;
    color: var(--text-secondary);
    margin: 0;
    line-height: 1.5;
}

/* ── Modal Footers ──────────────────────────── */
.form-modal .modal-footer,
.confirm-modal .modal-footer {
    border-top: 1px solid var(--border-light);
    padding: 12px 24px;
    display: flex;
    gap: 8px;
    justify-content: flex-end;
}

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

.btn-modal:disabled {
    opacity: 0.4;
    cursor: not-allowed;
}

.btn-modal-cancel {
    background: transparent;
    color: var(--text-secondary);
}

.btn-modal-cancel:hover {
    background: var(--parchment-deep);
    color: var(--text-primary);
}

.btn-modal-confirm {
    background: var(--moss);
    color: var(--white);
    display: inline-flex;
    align-items: center;
    gap: 6px;
}

.btn-modal-confirm:hover:not(:disabled) {
    background: var(--moss-light);
}

.btn-modal-danger {
    background: var(--sienna);
}

.btn-modal-danger:hover:not(:disabled) {
    background: var(--sienna-light);
}

/* ── Request Form ───────────────────────────── */
.request-rows-container {
    text-align: left;
    margin-top: 20px;
    display: flex;
    flex-direction: column;
    gap: 14px;
    max-height: 55vh;
    overflow-y: auto;
}

.request-row-item {
    background: var(--parchment-deep);
    border: 1px solid var(--border-light);
    border-radius: 10px;
    padding: 14px;
}

.request-row-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}

.request-row-num {
    font-size: 0.78rem;
    font-weight: 700;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

.btn-remove-row {
    width: 24px;
    height: 24px;
    border-radius: 6px;
    border: 1.5px solid var(--border);
    background: transparent;
    color: var(--text-secondary);
    font-size: 0.7rem;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    transition: all var(--transition-fast);
}

.btn-remove-row:hover {
    border-color: var(--sienna);
    color: var(--sienna);
    background: rgba(181, 105, 77, 0.06);
}

.request-row-fields {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.btn-add-row {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    margin-top: 12px;
    padding: 7px 14px;
    border: 1.5px dashed var(--border);
    border-radius: 9px;
    background: transparent;
    color: var(--text-secondary);
    font-family: var(--font-body);
    font-size: 0.82rem;
    font-weight: 600;
    cursor: pointer;
    transition: all var(--transition-fast);
    width: 100%;
    justify-content: center;
}

.btn-add-row:hover {
    border-color: var(--moss);
    color: var(--moss);
    background: rgba(74, 103, 65, 0.04);
}

.mt-3 {
    margin-top: 1rem;
}

/* ── Responsive ─────────────────────────────── */
@media (max-width: 767.98px) {
    .page-title {
        font-size: 1.35rem;
    }

    .page-header {
        margin-bottom: 18px;
    }

    .header-actions .btn-add span {
        display: none;
    }

    .header-actions .btn-add i {
        font-size: 1.15rem;
    }

    .tab-bar {
        gap: 4px;
        margin-bottom: 16px;
    }

    .tab-btn {
        padding: 8px 12px;
        font-size: 0.78rem;
        gap: 6px;
    }

    .tab-label {
        display: none;
    }

    .tab-btn.active .tab-label {
        display: inline;
    }

    .filter-bar {
        gap: 8px;
    }

    .filter-select,
    .filter-date {
        min-width: 0;
        flex: 1;
    }

    .item-row {
        flex-direction: column;
        align-items: flex-start;
        padding: 12px 14px;
        gap: 8px;
    }

    .item-info {
        gap: 6px 8px;
    }

    .item-stock {
        font-size: 0.76rem;
        gap: 4px;
    }

    .item-actions {
        align-self: flex-end;
    }

    .approval-card-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 10px;
    }

    .approval-card-right {
        align-self: flex-end;
    }

    .approval-item-row {
        flex-direction: column;
        align-items: flex-start;
        gap: 8px;
    }

    .approval-item-actions {
        align-self: flex-end;
    }

    .form-row {
        flex-direction: column;
        gap: 0;
    }

    .form-row-sm {
        flex-direction: column;
        gap: 0;
    }

    .ae-field {
        min-width: 0;
    }
}

@media (max-width: 575.98px) {
    .tab-btn {
        padding: 8px 10px;
        font-size: 0.75rem;
    }

    .approval-card-right {
        flex-wrap: wrap;
        justify-content: flex-end;
    }

    .btn-action-sm {
        font-size: 0.7rem;
        padding: 5px 10px;
    }
}
</style>

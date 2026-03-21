<template>
    <div class="t-detail-page" v-if="transformation">
        <!-- Header -->
        <div class="page-header animate-fade-in-up">
            <div class="header-left">
                <button class="btn-back" @click="$router.push({ name: 'transformations' })">
                    <i class="bi bi-arrow-left"></i>
                </button>
                <div>
                    <div class="header-title-row">
                        <h2 class="page-title">T-{{ transformation.id }}</h2>
                        <span class="type-label">{{ transformation.transformation_type?.name }}</span>
                        <span class="status-badge" :class="transformation.to_date ? 'badge-complete' : 'badge-in-progress'">
                            {{ transformation.to_date ? 'Complete' : 'In Progress' }}
                        </span>
                    </div>
                    <p class="page-subtitle">
                        {{ formatDate(transformation.from_date) }}
                        <span v-if="transformation.to_date"> → {{ formatDate(transformation.to_date) }}</span>
                        <span v-else> → In Progress</span>
                    </p>
                </div>
            </div>
            <div class="header-actions">
                <button v-if="isAdmin && !transformation.to_date && transformation.outputs?.length > 0"
                    class="btn-complete" @click="markComplete" :disabled="completing">
                    <i class="bi bi-check-circle"></i>
                    <span v-if="completing">Completing...</span>
                    <span v-else>Mark Complete</span>
                </button>
                <button v-if="isAdmin" class="btn-secondary" @click="openEditModal">
                    <i class="bi bi-pencil"></i> Edit
                </button>
                <button v-if="isAdmin" class="btn-danger-outline" @click="openDeleteModal">
                    <i class="bi bi-trash3"></i>
                </button>
            </div>
        </div>
        <p v-if="completeError" class="global-error animate-fade-in">{{ completeError }}</p>

        <div class="panels-grid animate-fade-in-up animate-delay-1">
            <!-- Input Batches -->
            <div class="content-panel" v-if="!transformation.transformation_type?.is_root">
                <div class="panel-header">
                    <span><i class="bi bi-box-arrow-in-down"></i> Input Batches</span>
                    <button v-if="isAdmin && !transformation.to_date" class="btn-panel-add" @click="openInputModal">
                        <i class="bi bi-plus-lg"></i> Add
                    </button>
                </div>
                <div class="panel-body">
                    <div v-if="!transformation.inputs?.length" class="empty-state small">
                        <p>No input batches yet</p>
                    </div>
                    <div v-else class="resource-list">
                        <div v-for="inp in transformation.inputs" :key="inp.id" class="resource-row">
                            <div class="resource-main">
                                <RouterLink :to="{ name: 'batch-detail', params: { id: inp.batch_id } }" class="resource-name">{{ inp.batch_code }}</RouterLink>
                                <span v-if="inp.stage_name" class="stage-badge-sm" :class="stageBadgeClass(inp.stage_name)">{{ inp.stage_name }}</span>
                            </div>
                            <div class="resource-meta">
                                <span class="weight-val">{{ formatKg(inp.input_weight) }} kg</span>
                                <button v-if="isAdmin && !transformation.to_date" class="btn-icon-danger" @click="removeInput(inp.id)" title="Remove">
                                    <i class="bi bi-x"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Output Batches -->
            <div class="content-panel">
                <div class="panel-header">
                    <span><i class="bi bi-box-arrow-up"></i> Output Batches</span>
                    <button v-if="isAdmin && !transformation.to_date" class="btn-panel-add" @click="openOutputModal">
                        <i class="bi bi-plus-lg"></i> Add
                    </button>
                </div>
                <div class="panel-body">
                    <div v-if="!transformation.outputs?.length" class="empty-state small">
                        <p v-if="!transformation.to_date" class="hint-text">Add output batches before marking complete</p>
                        <p v-else>No output batches</p>
                    </div>
                    <div v-else class="resource-list">
                        <div v-for="out in transformation.outputs" :key="out.id" class="resource-row">
                            <div class="resource-main">
                                <RouterLink :to="{ name: 'batch-detail', params: { id: out.batch_id } }" class="resource-name">{{ out.batch_code }}</RouterLink>
                                <span v-if="out.stage_name" class="stage-badge-sm" :class="stageBadgeClass(out.stage_name)">{{ out.stage_name }}</span>
                            </div>
                            <div class="resource-meta">
                                <span class="weight-val">{{ formatKg(out.output_weight) }} kg</span>
                                <button v-if="isAdmin && !transformation.to_date" class="btn-icon-danger" @click="removeOutput(out.id)" title="Remove">
                                    <i class="bi bi-x"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                    <div v-if="transformation.inputs?.length && transformation.outputs?.length" class="yield-summary">
                        <span class="yield-label">Yield:</span>
                        <span class="yield-val">{{ yieldRate }}%</span>
                    </div>
                </div>
            </div>

            <!-- Personnel -->
            <div class="content-panel">
                <div class="panel-header">
                    <span>
                        <i class="bi bi-people"></i> Personnel
                        <span v-if="transformation.remaining_assignable_output_qty != null" class="info-badge">
                            {{ formatKg(transformation.remaining_assignable_output_qty) }} kg assignable
                        </span>
                    </span>
                    <button v-if="isAdmin" class="btn-panel-add" @click="openPersonnelModal(null)">
                        <i class="bi bi-plus-lg"></i> Assign
                    </button>
                </div>
                <div class="panel-body">
                    <div v-if="!transformation.personnel_assignments?.length" class="empty-state small"><p>No personnel assigned</p></div>
                    <div v-else class="resource-list">
                        <div v-for="p in transformation.personnel_assignments" :key="p.id" class="resource-row">
                            <div class="resource-main">
                                <span class="resource-name">{{ p.personnel_name }}</span>
                                <span class="resource-sub">{{ p.wage_type_name }} · ₹{{ formatNum(p.rate_at_time) }}/{{ p.wage_type_name === 'DAILY' ? 'day' : 'kg' }}</span>
                                <span v-if="p.additional_payments" class="resource-sub">+₹{{ formatNum(p.additional_payments) }} extra</span>
                                <span class="stage-badge-sm" :class="p.is_paid ? 'stage-pack' : 'stage-dry'">{{ p.is_paid ? 'Paid' : 'Unpaid' }}</span>
                            </div>
                            <div class="resource-meta">
                                <span class="weight-val">₹{{ formatNum(p.total_wages_payable) }}</span>
                                <button v-if="isAdmin && !p.is_paid" class="btn-icon-edit" @click="markPersonnelPaid(p.id)" title="Mark Paid"><i class="bi bi-check-lg"></i></button>
                                <button v-if="isAdmin && p.is_paid" class="btn-icon-edit" @click="markPersonnelUnpaid(p.id)" title="Mark Unpaid"><i class="bi bi-arrow-counterclockwise"></i></button>
                                <button v-if="isAdmin" class="btn-icon-edit" @click="openPersonnelModal(p)" title="Edit"><i class="bi bi-pencil"></i></button>
                                <button v-if="isAdmin" class="btn-icon-danger" @click="removePersonnel(p.id)" title="Remove"><i class="bi bi-x"></i></button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Vehicles -->
            <div class="content-panel">
                <div class="panel-header">
                    <span><i class="bi bi-truck"></i> Vehicles</span>
                    <button v-if="isAdmin" class="btn-panel-add" @click="openVehicleModal(null)">
                        <i class="bi bi-plus-lg"></i> Assign
                    </button>
                </div>
                <div class="panel-body">
                    <div v-if="!transformation.vehicle_usage?.length" class="empty-state small"><p>No vehicles assigned</p></div>
                    <div v-else class="resource-list">
                        <div v-for="v in transformation.vehicle_usage" :key="v.id" class="resource-row">
                            <div class="resource-main">
                                <span class="resource-name">{{ v.vehicle_number }}</span>
                                <span v-if="v.vehicle_type" class="resource-sub">{{ v.vehicle_type }}</span>
                                <span class="resource-sub">{{ v.hours_used }}h · {{ v.fuel_qty }}L fuel</span>
                                <span v-if="v.fuel_consumable_name" class="resource-sub">{{ v.fuel_consumable_name }}</span>
                            </div>
                            <div class="resource-meta">
                                <span class="weight-val">₹{{ formatNum(v.fuel_cost) }}</span>
                                <button v-if="isAdmin" class="btn-icon-edit" @click="openVehicleModal(v)" title="Edit"><i class="bi bi-pencil"></i></button>
                                <button v-if="isAdmin" class="btn-icon-danger" @click="removeVehicle(v.id)" title="Remove"><i class="bi bi-x"></i></button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Consumables -->
            <div class="content-panel panel-full">
                <div class="panel-header">
                    <span><i class="bi bi-box-seam"></i> Consumables</span>
                    <button v-if="isAdmin" class="btn-panel-add" @click="openConsumableModal">
                        <i class="bi bi-plus-lg"></i> Record Usage
                    </button>
                </div>
                <div class="panel-body">
                    <div v-if="!transformation.consumable_consumptions?.length" class="empty-state small"><p>No consumables recorded</p></div>
                    <div v-else class="resource-list">
                        <div v-for="c in transformation.consumable_consumptions" :key="c.id" class="resource-row">
                            <div class="resource-main">
                                <span class="resource-name">{{ c.consumable_name }}</span>
                                <span class="resource-sub">{{ formatNum(c.quantity_used) }} {{ c.consumable_unit }}</span>
                            </div>
                            <div class="resource-meta">
                                <span class="weight-val">₹{{ formatNum(c.total_cost) }}</span>
                                <span class="resource-date">{{ formatDate(c.consumption_date) }}</span>
                                <button v-if="isAdmin" class="btn-icon-danger" @click="removeConsumable(c.id)" title="Remove"><i class="bi bi-x"></i></button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Expenses -->
            <div class="content-panel panel-full">
                <div class="panel-header">
                    <span><i class="bi bi-receipt"></i> Expenses</span>
                    <button v-if="isAdmin" class="btn-panel-add" @click="openExpenseModal">
                        <i class="bi bi-plus-lg"></i> Add
                    </button>
                </div>
                <div class="panel-body">
                    <div v-if="!transformation.expenses?.length" class="empty-state small"><p>No expenses recorded</p></div>
                    <div v-else class="resource-list">
                        <div v-for="e in transformation.expenses" :key="e.id" class="resource-row">
                            <div class="resource-main">
                                <span class="resource-name">{{ e.category_name }}</span>
                                <span class="resource-sub">{{ e.description || '' }}</span>
                                <span v-if="e.is_wage_expense" class="stage-badge-sm stage-clean">Wage</span>
                            </div>
                            <div class="resource-meta">
                                <span class="weight-val">₹{{ formatNum(e.amount) }}</span>
                                <span class="resource-date">{{ formatDate(e.date) }}</span>
                                <button v-if="isAdmin && !e.is_wage_expense" class="btn-icon-danger" @click="removeExpense(e.id)" title="Remove">
                                    <i class="bi bi-x"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- ── Modals ── -->

        <!-- Edit Transformation -->
        <div class="modal fade" id="editTModal" tabindex="-1" ref="editModalRef">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content agri-modal">
                    <div class="agri-modal-header">
                        <h5 class="modal-title">Edit Transformation</h5>
                        <button type="button" class="btn-close-modal" data-bs-dismiss="modal"><i class="bi bi-x-lg"></i></button>
                    </div>
                    <div class="agri-modal-body">
                        <div class="form-group">
                            <label class="form-label">Start Date</label>
                            <input v-model="editForm.from_date" type="datetime-local" class="form-control" />
                        </div>
                        <div class="form-group">
                            <label class="form-label">End Date (leave blank if in progress)</label>
                            <input v-model="editForm.to_date" type="datetime-local" class="form-control" />
                        </div>
                        <div class="form-group">
                            <label class="form-label">Notes</label>
                            <textarea v-model="editForm.notes" class="form-control" rows="2"></textarea>
                        </div>
                        <p v-if="modalError" class="form-error">{{ modalError }}</p>
                    </div>
                    <div class="agri-modal-footer">
                        <button type="button" class="btn-modal-cancel" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn-modal-confirm" :disabled="modalSaving" @click="saveEdit">
                            <span v-if="modalSaving"><i class="bi bi-hourglass-split"></i></span>
                            <span v-else>Save</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Delete Transformation -->
        <div class="modal fade" id="deleteTModal" tabindex="-1" ref="deleteModalRef">
            <div class="modal-dialog modal-dialog-centered modal-sm">
                <div class="modal-content agri-modal">
                    <div class="agri-modal-header">
                        <h5 class="modal-title">Delete Transformation</h5>
                        <button type="button" class="btn-close-modal" data-bs-dismiss="modal"><i class="bi bi-x-lg"></i></button>
                    </div>
                    <div class="agri-modal-body">
                        <p class="confirm-text">Delete T-{{ transformation.id }}? This cannot be undone.</p>
                        <p v-if="modalError" class="form-error">{{ modalError }}</p>
                    </div>
                    <div class="agri-modal-footer">
                        <button type="button" class="btn-modal-cancel" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn-modal-danger" :disabled="modalSaving" @click="deleteTransformation">
                            <span v-if="modalSaving"><i class="bi bi-hourglass-split"></i></span>
                            <span v-else>Delete</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Add Input Batch -->
        <div class="modal fade" id="inputModal" tabindex="-1" ref="inputModalRef">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content agri-modal">
                    <div class="agri-modal-header">
                        <h5 class="modal-title">Add Input Batch</h5>
                        <button type="button" class="btn-close-modal" data-bs-dismiss="modal"><i class="bi bi-x-lg"></i></button>
                    </div>
                    <div class="agri-modal-body">
                        <div class="form-group">
                            <label class="form-label">Batch *</label>
                            <select v-model="inputForm.batch_id" class="form-control form-select">
                                <option :value="null" disabled>Select batch...</option>
                                <option v-for="b in availableBatches" :key="b.id" :value="b.id">
                                    {{ b.batch_code }} ({{ formatKg(b.remaining_weight_kg) }} kg remaining)
                                </option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Input Weight (kg) *</label>
                            <input v-model="inputForm.input_weight" type="number" step="0.01" min="0.01" class="form-control" />
                        </div>
                        <p v-if="modalError" class="form-error">{{ modalError }}</p>
                    </div>
                    <div class="agri-modal-footer">
                        <button type="button" class="btn-modal-cancel" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn-modal-confirm" :disabled="!inputForm.batch_id || !inputForm.input_weight || modalSaving" @click="saveInput">
                            <span v-if="modalSaving"><i class="bi bi-hourglass-split"></i></span>
                            <span v-else>Add Input</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Add Output Batch -->
        <div class="modal fade" id="outputModal" tabindex="-1" ref="outputModalRef">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content agri-modal">
                    <div class="agri-modal-header">
                        <h5 class="modal-title">Add Output Batch</h5>
                        <button type="button" class="btn-close-modal" data-bs-dismiss="modal"><i class="bi bi-x-lg"></i></button>
                    </div>
                    <div class="agri-modal-body">
                        <div class="form-group">
                            <label class="form-label">Batch Code *</label>
                            <input v-model="outputForm.batch_code" type="text" class="form-control" placeholder="e.g. GA-002" />
                        </div>
                        <div class="form-group">
                            <label class="form-label">Stage *</label>
                            <select v-model="outputForm.stage_id" class="form-control form-select">
                                <option :value="null" disabled>Select stage...</option>
                                <option v-for="s in stages" :key="s.id" :value="s.id">{{ s.name }}</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Output Weight (kg) *</label>
                            <input v-model="outputForm.output_weight" type="number" step="0.01" min="0.01" class="form-control" />
                        </div>
                        <div class="form-group" v-if="transformation.transformation_type?.is_root">
                            <label class="form-label">Plantation *</label>
                            <select v-model="outputForm.plantation_id" class="form-control form-select">
                                <option :value="null" disabled>Select plantation...</option>
                                <option v-for="pl in plantations" :key="pl.id" :value="pl.id">{{ pl.name }}</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Notes</label>
                            <textarea v-model="outputForm.notes" class="form-control" rows="2"></textarea>
                        </div>
                        <p v-if="modalError" class="form-error">{{ modalError }}</p>
                    </div>
                    <div class="agri-modal-footer">
                        <button type="button" class="btn-modal-cancel" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn-modal-confirm" :disabled="!outputForm.batch_code || !outputForm.stage_id || !outputForm.output_weight || modalSaving" @click="saveOutput">
                            <span v-if="modalSaving"><i class="bi bi-hourglass-split"></i></span>
                            <span v-else>Add Output</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Assign Personnel -->
        <div class="modal fade" id="personnelModal" tabindex="-1" ref="personnelModalRef">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content agri-modal">
                    <div class="agri-modal-header">
                        <h5 class="modal-title">{{ editingPersonnel ? 'Edit Assignment' : 'Assign Personnel' }}</h5>
                        <button type="button" class="btn-close-modal" data-bs-dismiss="modal"><i class="bi bi-x-lg"></i></button>
                    </div>
                    <div class="agri-modal-body">
                        <div v-if="!editingPersonnel" class="form-group">
                            <label class="form-label">Personnel *</label>
                            <select v-model="personnelForm.personnel_id" class="form-control form-select">
                                <option :value="null" disabled>Select worker...</option>
                                <option v-for="p in allPersonnel" :key="p.id" :value="p.id">{{ p.name }} ({{ p.wage_type_name }} · ₹{{ formatNum(p.rate) }}/{{ p.wage_type_name === 'DAILY' ? 'day' : 'kg' }})</option>
                            </select>
                        </div>
                        <div v-if="editingPersonnel" class="form-group">
                            <p class="resource-sub">{{ editingPersonnel.wage_type_name }} · ₹{{ formatNum(editingPersonnel.rate_at_time) }}/{{ editingPersonnel.wage_type_name === 'DAILY' ? 'day' : 'kg' }}</p>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label class="form-label">Days Worked *</label>
                                <input v-model="personnelForm.days_worked" type="number" step="0.5" min="0" class="form-control" placeholder="0" />
                            </div>
                            <div class="form-group">
                                <label class="form-label">Output Weight (kg)</label>
                                <input v-model="personnelForm.output_weight_considered" type="number" step="0.01" min="0" class="form-control" placeholder="0" />
                            </div>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Additional Payments (₹)</label>
                            <input v-model="personnelForm.additional_payments" type="number" step="0.01" min="0" class="form-control" placeholder="0" />
                        </div>
                        <div class="form-group">
                            <label class="form-label">Additional Payments Description</label>
                            <input v-model="personnelForm.additional_payments_description" type="text" class="form-control" placeholder="Optional description..." />
                        </div>
                        <div class="form-group">
                            <label class="form-label">Notes</label>
                            <input v-model="personnelForm.notes" type="text" class="form-control" />
                        </div>
                        <p v-if="modalError" class="form-error">{{ modalError }}</p>
                    </div>
                    <div class="agri-modal-footer">
                        <button type="button" class="btn-modal-cancel" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn-modal-confirm" :disabled="(!editingPersonnel && !personnelForm.personnel_id) || !personnelForm.days_worked || modalSaving" @click="savePersonnel">
                            <span v-if="modalSaving"><i class="bi bi-hourglass-split"></i></span>
                            <span v-else>{{ editingPersonnel ? 'Save' : 'Assign' }}</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Assign Vehicle -->
        <div class="modal fade" id="vehicleModal" tabindex="-1" ref="vehicleModalRef">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content agri-modal">
                    <div class="agri-modal-header">
                        <h5 class="modal-title">{{ editingVehicle ? 'Edit Vehicle Usage' : 'Assign Vehicle' }}</h5>
                        <button type="button" class="btn-close-modal" data-bs-dismiss="modal"><i class="bi bi-x-lg"></i></button>
                    </div>
                    <div class="agri-modal-body">
                        <div v-if="!editingVehicle" class="form-group">
                            <label class="form-label">Vehicle *</label>
                            <select v-model="vehicleForm.vehicle_id" class="form-control form-select">
                                <option :value="null" disabled>Select vehicle...</option>
                                <option v-for="v in allVehicles" :key="v.id" :value="v.id">{{ v.number }} {{ v.vehicle_type ? '— ' + v.vehicle_type : '' }}</option>
                            </select>
                            <p v-if="vehicleForm.vehicle_id && selectedVehicleFuelName" class="resource-sub">Fuel: {{ selectedVehicleFuelName }}</p>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label class="form-label">Hours Used *</label>
                                <input v-model="vehicleForm.hours_used" type="number" step="0.5" min="0" class="form-control" />
                            </div>
                            <div class="form-group">
                                <label class="form-label">Fuel Qty (L) *</label>
                                <input v-model="vehicleForm.fuel_qty" type="number" step="0.1" min="0" class="form-control" />
                            </div>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Notes</label>
                            <input v-model="vehicleForm.notes" type="text" class="form-control" />
                        </div>
                        <p v-if="modalError" class="form-error">{{ modalError }}</p>
                    </div>
                    <div class="agri-modal-footer">
                        <button type="button" class="btn-modal-cancel" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn-modal-confirm" :disabled="(!editingVehicle && !vehicleForm.vehicle_id) || !vehicleForm.hours_used || !vehicleForm.fuel_qty || modalSaving" @click="saveVehicle">
                            <span v-if="modalSaving"><i class="bi bi-hourglass-split"></i></span>
                            <span v-else>{{ editingVehicle ? 'Save' : 'Assign' }}</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Add Expense -->
        <div class="modal fade" id="expenseModal" tabindex="-1" ref="expenseModalRef">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content agri-modal">
                    <div class="agri-modal-header">
                        <h5 class="modal-title">Add Expense</h5>
                        <button type="button" class="btn-close-modal" data-bs-dismiss="modal"><i class="bi bi-x-lg"></i></button>
                    </div>
                    <div class="agri-modal-body">
                        <div class="form-group">
                            <label class="form-label">Category *</label>
                            <select v-model="expenseForm.category_id" class="form-control form-select">
                                <option :value="null" disabled>Select category...</option>
                                <option v-for="c in expenseCategories" :key="c.id" :value="c.id">{{ c.name }}</option>
                            </select>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label class="form-label">Amount (₹) *</label>
                                <input v-model="expenseForm.amount" type="number" step="0.01" min="0.01" class="form-control" />
                            </div>
                            <div class="form-group">
                                <label class="form-label">Date *</label>
                                <input v-model="expenseForm.date" type="date" class="form-control" />
                            </div>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Description</label>
                            <input v-model="expenseForm.description" type="text" class="form-control" placeholder="Optional description..." />
                        </div>
                        <p v-if="modalError" class="form-error">{{ modalError }}</p>
                    </div>
                    <div class="agri-modal-footer">
                        <button type="button" class="btn-modal-cancel" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn-modal-confirm" :disabled="!expenseForm.category_id || !expenseForm.amount || !expenseForm.date || modalSaving" @click="saveExpense">
                            <span v-if="modalSaving"><i class="bi bi-hourglass-split"></i></span>
                            <span v-else>Add Expense</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Record Consumable Usage -->
        <div class="modal fade" id="consumableModal" tabindex="-1" ref="consumableModalRef">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content agri-modal">
                    <div class="agri-modal-header">
                        <h5 class="modal-title">Record Consumable Usage</h5>
                        <button type="button" class="btn-close-modal" data-bs-dismiss="modal"><i class="bi bi-x-lg"></i></button>
                    </div>
                    <div class="agri-modal-body">
                        <div class="form-group">
                            <label class="form-label">Consumable *</label>
                            <select v-model="consumableForm.consumable_id" class="form-control form-select">
                                <option :value="null" disabled>Select consumable...</option>
                                <option v-for="c in allConsumables" :key="c.id" :value="c.id">{{ c.name }} ({{ c.unit }})</option>
                            </select>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label class="form-label">Quantity Used *</label>
                                <input v-model="consumableForm.quantity_used" type="number" step="0.01" min="0.01" class="form-control" />
                            </div>
                            <div class="form-group">
                                <label class="form-label">Date *</label>
                                <input v-model="consumableForm.consumption_date" type="date" class="form-control" />
                            </div>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Notes</label>
                            <input v-model="consumableForm.notes" type="text" class="form-control" />
                        </div>
                        <p v-if="modalError" class="form-error">{{ modalError }}</p>
                    </div>
                    <div class="agri-modal-footer">
                        <button type="button" class="btn-modal-cancel" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn-modal-confirm" :disabled="!consumableForm.consumable_id || !consumableForm.quantity_used || !consumableForm.consumption_date || modalSaving" @click="saveConsumable">
                            <span v-if="modalSaving"><i class="bi bi-hourglass-split"></i></span>
                            <span v-else>Record</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div v-else-if="loadError" class="empty-page">
        <i class="bi bi-exclamation-triangle"></i>
        <p>{{ loadError }}</p>
        <button class="btn-primary" @click="$router.push({ name: 'transformations' })">Back</button>
    </div>

    <div v-else class="empty-page">
        <i class="bi bi-hourglass-split"></i><p>Loading...</p>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Modal } from 'bootstrap'
import api from '../utils/api'
import { useAuthStore } from '@/stores/auth'
import { useReportsStore } from '@/stores/reports'

const auth = useAuthStore()
const reportsStore = useReportsStore()
const route = useRoute()
const router = useRouter()
const isAdmin = auth.userRoles?.includes('admin')

const transformation = ref(null)
const loadError = ref('')
const completing = ref(false)
const completeError = ref('')
const modalSaving = ref(false)
const modalError = ref('')

// Lookup data
const stages = ref([])
const availableBatches = ref([])
const allPersonnel = ref([])
const allVehicles = ref([])
const allConsumables = ref([])
const plantations = ref([])
const expenseCategories = ref([])

// Forms
const editForm = ref({ from_date: '', to_date: '', notes: '' })
const inputForm = ref({ batch_id: null, input_weight: '' })
const outputForm = ref({ batch_code: '', stage_id: null, output_weight: '', notes: '', plantation_id: null })
const personnelForm = ref({ personnel_id: null, days_worked: '', output_weight_considered: '', additional_payments: 0, additional_payments_description: '', notes: '' })
const vehicleForm = ref({ vehicle_id: null, hours_used: '', fuel_qty: '', notes: '' })
const consumableForm = ref({ consumable_id: null, quantity_used: '', consumption_date: todayStr(), notes: '' })
const expenseForm = ref({ category_id: null, amount: '', date: todayStr(), description: '' })
const editingPersonnel = ref(null)
const editingVehicle = ref(null)

// Modal refs
const editModalRef = ref(null)
const deleteModalRef = ref(null)
const inputModalRef = ref(null)
const outputModalRef = ref(null)
const personnelModalRef = ref(null)
const vehicleModalRef = ref(null)
const consumableModalRef = ref(null)
const expenseModalRef = ref(null)

let bsEdit, bsDelete, bsInput, bsOutput, bsPersonnel, bsVehicle, bsConsumable, bsExpense

const selectedVehicleFuelName = computed(() => {
    if (!vehicleForm.value.vehicle_id) return null
    const v = allVehicles.value.find(x => x.id === vehicleForm.value.vehicle_id)
    return v?.fuel_consumable_name || null
})

const yieldRate = computed(() => {
    if (!transformation.value) return '0'
    const totalIn = transformation.value.inputs?.reduce((s, i) => s + Number(i.input_weight), 0) || 0
    const totalOut = transformation.value.outputs?.reduce((s, o) => s + Number(o.output_weight), 0) || 0
    if (totalIn === 0) return '0'
    return (totalOut / totalIn * 100).toFixed(1)
})

function todayStr() {
    return new Date().toISOString().slice(0, 10)
}

function toLocalDatetimeStr(isoStr) {
    if (!isoStr) return ''
    const d = new Date(isoStr)
    d.setSeconds(0, 0)
    return d.toISOString().slice(0, 16)
}

function formatDate(val) {
    if (!val) return '—'
    return new Date(val).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
}

function formatKg(val) {
    if (val == null) return '—'
    return Number(val).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function formatNum(val) {
    if (val == null) return '0'
    return Number(val).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function stageBadgeClass(name) {
    if (!name) return 'stage-default'
    const n = name.toUpperCase()
    if (n.includes('HARVEST')) return 'stage-harvest'
    if (n.includes('CLEAN')) return 'stage-clean'
    if (n.includes('DRY')) return 'stage-dry'
    if (n.includes('BAG')) return 'stage-bag'
    if (n.includes('GRADE')) return 'stage-grade'
    if (n.includes('PACK')) return 'stage-pack'
    if (n.includes('RETAIL')) return 'stage-retail'
    return 'stage-default'
}

async function fetchTransformation() {
    try {
        const res = await api.get(`/transformations/${route.params.id}`)
        transformation.value = res.data
    } catch (err) {
        loadError.value = err.response?.status === 404 ? 'Transformation not found.' : 'Failed to load.'
    }
}

async function refreshTransformation() {
    const res = await api.get(`/transformations/${route.params.id}`)
    transformation.value = res.data
}

async function markComplete() {
    completing.value = true
    completeError.value = ''
    try {
        await api.post(`/transformations/${route.params.id}/complete`)
        reportsStore.invalidate('transformations')
        await refreshTransformation()
    } catch (err) {
        completeError.value = err.response?.data?.detail || 'Failed to mark complete.'
    } finally {
        completing.value = false
    }
}

// ── Edit ──────────────────────────────────────────────────────────────────────
function openEditModal() {
    editForm.value = {
        from_date: toLocalDatetimeStr(transformation.value.from_date),
        to_date: toLocalDatetimeStr(transformation.value.to_date),
        notes: transformation.value.notes || '',
    }
    modalError.value = ''
    if (!bsEdit) bsEdit = new Modal(editModalRef.value)
    bsEdit.show()
}

async function saveEdit() {
    modalSaving.value = true
    modalError.value = ''
    try {
        const payload = {
            from_date: editForm.value.from_date ? new Date(editForm.value.from_date).toISOString() : undefined,
            to_date: editForm.value.to_date ? new Date(editForm.value.to_date).toISOString() : null,
            notes: editForm.value.notes || null,
        }
        await api.put(`/transformations/${route.params.id}`, payload)
        reportsStore.invalidate('transformations')
        bsEdit.hide()
        await refreshTransformation()
    } catch (err) {
        modalError.value = err.response?.data?.detail || 'Failed to save.'
    } finally {
        modalSaving.value = false
    }
}

function openDeleteModal() {
    modalError.value = ''
    if (!bsDelete) bsDelete = new Modal(deleteModalRef.value)
    bsDelete.show()
}

async function deleteTransformation() {
    modalSaving.value = true
    modalError.value = ''
    try {
        await api.delete(`/transformations/${route.params.id}`)
        reportsStore.invalidate('transformations')
        bsDelete.hide()
        router.push({ name: 'transformations' })
    } catch (err) {
        if (err.response?.status === 409) {
            modalError.value = 'Cannot delete: transformation has output batches.'
        } else {
            modalError.value = err.response?.data?.detail || 'Failed to delete.'
        }
    } finally {
        modalSaving.value = false
    }
}

// ── Input ─────────────────────────────────────────────────────────────────────
async function openInputModal() {
    inputForm.value = { batch_id: null, input_weight: '' }
    modalError.value = ''
    try {
        const res = await api.get('/batches/', { params: { is_depleted: false } })
        availableBatches.value = res.data
    } catch {}
    if (!bsInput) bsInput = new Modal(inputModalRef.value)
    bsInput.show()
}

async function saveInput() {
    modalSaving.value = true
    modalError.value = ''
    try {
        await api.post(`/transformations/${route.params.id}/inputs`, {
            batch_id: inputForm.value.batch_id,
            input_weight: parseFloat(inputForm.value.input_weight),
        })
        reportsStore.invalidate('transformations')
        bsInput.hide()
        await refreshTransformation()
    } catch (err) {
        modalError.value = err.response?.data?.detail || 'Failed to add input.'
    } finally {
        modalSaving.value = false
    }
}

async function removeInput(inputId) {
    if (!confirm('Remove this input batch?')) return
    try {
        await api.delete(`/transformations/${route.params.id}/inputs/${inputId}`)
        reportsStore.invalidate('transformations')
        await refreshTransformation()
    } catch (err) {
        alert(err.response?.data?.detail || 'Failed to remove.')
    }
}

// ── Output ────────────────────────────────────────────────────────────────────
async function openOutputModal() {
    outputForm.value = { batch_code: '', stage_id: null, output_weight: '', notes: '', plantation_id: null }
    modalError.value = ''
    if (!stages.value.length) {
        const res = await api.get('/batches/stages')
        stages.value = res.data
    }
    if (transformation.value?.transformation_type?.is_root && !plantations.value.length) {
        try {
            const res = await api.get('/plantations/')
            plantations.value = res.data
        } catch {}
    }
    if (!bsOutput) bsOutput = new Modal(outputModalRef.value)
    bsOutput.show()
}

async function saveOutput() {
    modalSaving.value = true
    modalError.value = ''
    try {
        const payload = {
            batch_code: outputForm.value.batch_code.trim(),
            stage_id: outputForm.value.stage_id,
            output_weight: parseFloat(outputForm.value.output_weight),
            notes: outputForm.value.notes || null,
        }
        if (transformation.value?.transformation_type?.is_root) {
            payload.plantation_id = outputForm.value.plantation_id || null
        }
        await api.post(`/transformations/${route.params.id}/outputs`, payload)
        reportsStore.invalidate('transformations')
        bsOutput.hide()
        await refreshTransformation()
    } catch (err) {
        modalError.value = err.response?.data?.detail || 'Failed to add output.'
    } finally {
        modalSaving.value = false
    }
}

async function removeOutput(outputId) {
    if (!confirm('Remove this output batch? The batch record will also be deleted.')) return
    try {
        await api.delete(`/transformations/${route.params.id}/outputs/${outputId}`)
        reportsStore.invalidate('transformations')
        await refreshTransformation()
    } catch (err) {
        alert(err.response?.data?.detail || 'Failed to remove.')
    }
}

// ── Personnel ─────────────────────────────────────────────────────────────────
async function openPersonnelModal(existing) {
    editingPersonnel.value = existing
    modalError.value = ''
    if (!allPersonnel.value.length) {
        const res = await api.get('/personnel/')
        allPersonnel.value = res.data
    }
    if (existing) {
        personnelForm.value = {
            personnel_id: existing.personnel_id,
            days_worked: existing.days_worked || '',
            output_weight_considered: existing.output_weight_considered || '',
            additional_payments: existing.additional_payments || 0,
            additional_payments_description: existing.additional_payments_description || '',
            notes: existing.notes || '',
        }
    } else {
        personnelForm.value = { personnel_id: null, days_worked: '', output_weight_considered: '', additional_payments: 0, additional_payments_description: '', notes: '' }
    }
    if (!bsPersonnel) bsPersonnel = new Modal(personnelModalRef.value)
    bsPersonnel.show()
}

async function savePersonnel() {
    modalSaving.value = true
    modalError.value = ''
    try {
        const payload = {
            days_worked: personnelForm.value.days_worked ? parseFloat(personnelForm.value.days_worked) : null,
            output_weight_considered: personnelForm.value.output_weight_considered ? parseFloat(personnelForm.value.output_weight_considered) : null,
            additional_payments: parseFloat(personnelForm.value.additional_payments) || 0,
            additional_payments_description: personnelForm.value.additional_payments_description || null,
            notes: personnelForm.value.notes || null,
        }
        if (editingPersonnel.value) {
            await api.put(`/transformations/${route.params.id}/personnel/${editingPersonnel.value.id}`, payload)
        } else {
            await api.post(`/transformations/${route.params.id}/personnel`, {
                ...payload,
                personnel_id: personnelForm.value.personnel_id,
            })
        }
        reportsStore.invalidate('transformations')
        bsPersonnel.hide()
        await refreshTransformation()
    } catch (err) {
        modalError.value = err.response?.data?.detail || 'Failed to save.'
    } finally {
        modalSaving.value = false
    }
}

async function markPersonnelPaid(tpId) {
    try {
        await api.post(`/transformations/${route.params.id}/personnel/${tpId}/mark-paid`)
        reportsStore.invalidate('transformations')
        await refreshTransformation()
    } catch (err) {
        alert(err.response?.data?.detail || 'Failed to mark as paid.')
    }
}

async function markPersonnelUnpaid(tpId) {
    if (!confirm('Mark as unpaid? The linked expense will be deleted.')) return
    try {
        await api.post(`/transformations/${route.params.id}/personnel/${tpId}/mark-unpaid`)
        reportsStore.invalidate('transformations')
        await refreshTransformation()
    } catch (err) {
        alert(err.response?.data?.detail || 'Failed to mark as unpaid.')
    }
}

async function removePersonnel(tpId) {
    if (!confirm('Remove this personnel assignment?')) return
    try {
        await api.delete(`/transformations/${route.params.id}/personnel/${tpId}`)
        reportsStore.invalidate('transformations')
        await refreshTransformation()
    } catch (err) {
        alert(err.response?.data?.detail || 'Failed to remove.')
    }
}

// ── Vehicles ──────────────────────────────────────────────────────────────────
async function openVehicleModal(existing) {
    editingVehicle.value = existing
    modalError.value = ''
    if (!allVehicles.value.length) {
        const res = await api.get('/vehicles/')
        allVehicles.value = res.data
    }
    if (existing) {
        vehicleForm.value = {
            vehicle_id: existing.vehicle_id,
            hours_used: existing.hours_used,
            fuel_qty: existing.fuel_qty,
            notes: existing.notes || '',
        }
    } else {
        vehicleForm.value = { vehicle_id: null, hours_used: '', fuel_qty: '', notes: '' }
    }
    if (!bsVehicle) bsVehicle = new Modal(vehicleModalRef.value)
    bsVehicle.show()
}

async function saveVehicle() {
    modalSaving.value = true
    modalError.value = ''
    try {
        const payload = {
            hours_used: parseFloat(vehicleForm.value.hours_used),
            fuel_qty: parseFloat(vehicleForm.value.fuel_qty) || 0,
            notes: vehicleForm.value.notes || null,
        }
        if (editingVehicle.value) {
            await api.put(`/transformations/${route.params.id}/vehicles/${editingVehicle.value.id}`, payload)
        } else {
            await api.post(`/transformations/${route.params.id}/vehicles`, {
                ...payload,
                vehicle_id: vehicleForm.value.vehicle_id,
            })
        }
        reportsStore.invalidate('transformations')
        bsVehicle.hide()
        await refreshTransformation()
    } catch (err) {
        modalError.value = err.response?.data?.detail || 'Failed to save.'
    } finally {
        modalSaving.value = false
    }
}

async function removeVehicle(tvId) {
    if (!confirm('Remove this vehicle assignment?')) return
    try {
        await api.delete(`/transformations/${route.params.id}/vehicles/${tvId}`)
        reportsStore.invalidate('transformations')
        await refreshTransformation()
    } catch (err) {
        alert(err.response?.data?.detail || 'Failed to remove.')
    }
}

// ── Consumables ───────────────────────────────────────────────────────────────
async function openConsumableModal() {
    consumableForm.value = { consumable_id: null, quantity_used: '', consumption_date: todayStr(), notes: '' }
    modalError.value = ''
    if (!allConsumables.value.length) {
        const res = await api.get('/consumables/')
        allConsumables.value = res.data
    }
    if (!bsConsumable) bsConsumable = new Modal(consumableModalRef.value)
    bsConsumable.show()
}

async function saveConsumable() {
    modalSaving.value = true
    modalError.value = ''
    try {
        await api.post(`/transformations/${route.params.id}/consumables`, {
            consumable_id: consumableForm.value.consumable_id,
            quantity_used: parseFloat(consumableForm.value.quantity_used),
            consumption_date: new Date(consumableForm.value.consumption_date).toISOString(),
            notes: consumableForm.value.notes || null,
        })
        reportsStore.invalidate('transformations')
        bsConsumable.hide()
        await refreshTransformation()
    } catch (err) {
        modalError.value = err.response?.data?.detail || 'Failed to record usage.'
    } finally {
        modalSaving.value = false
    }
}

async function removeConsumable(tcId) {
    if (!confirm('Remove this consumable usage? FIFO allocations will be reversed.')) return
    try {
        await api.delete(`/transformations/${route.params.id}/consumables/${tcId}`)
        reportsStore.invalidate('transformations')
        await refreshTransformation()
    } catch (err) {
        alert(err.response?.data?.detail || 'Failed to remove.')
    }
}

// ── Expenses ───────────────────────────────────────────────────────────────────
async function openExpenseModal() {
    expenseForm.value = { category_id: null, amount: '', date: todayStr(), description: '' }
    modalError.value = ''
    if (!expenseCategories.value.length) {
        try {
            const res = await api.get('/settings/expense-categories/')
            expenseCategories.value = res.data
        } catch {}
    }
    if (!bsExpense) bsExpense = new Modal(expenseModalRef.value)
    bsExpense.show()
}

async function saveExpense() {
    modalSaving.value = true
    modalError.value = ''
    try {
        await api.post(`/transformations/${route.params.id}/expenses`, {
            category_id: expenseForm.value.category_id,
            amount: parseFloat(expenseForm.value.amount),
            date: expenseForm.value.date,
            description: expenseForm.value.description || null,
        })
        reportsStore.invalidate('transformations')
        bsExpense.hide()
        await refreshTransformation()
    } catch (err) {
        modalError.value = err.response?.data?.detail || 'Failed to add expense.'
    } finally {
        modalSaving.value = false
    }
}

async function removeExpense(expenseId) {
    if (!confirm('Remove this expense?')) return
    try {
        await api.delete(`/transformations/${route.params.id}/expenses/${expenseId}`)
        reportsStore.invalidate('transformations')
        await refreshTransformation()
    } catch (err) {
        alert(err.response?.data?.detail || 'Failed to remove.')
    }
}

onMounted(async () => {
    await fetchTransformation()
    // Preload stages
    try {
        const res = await api.get('/batches/stages')
        stages.value = res.data
    } catch {}
})

onBeforeUnmount(() => {
    [bsEdit, bsDelete, bsInput, bsOutput, bsPersonnel, bsVehicle, bsConsumable, bsExpense].forEach(m => m?.dispose())
})
</script>

<style scoped>
.t-detail-page { max-width: 100vw; }
.empty-page { text-align: center; padding: 80px 20px; color: var(--text-secondary); }
.empty-page i { font-size: 2.5rem; opacity: 0.3; display: block; margin-bottom: 12px; }
.empty-page p { margin-bottom: 16px; }

.page-header {
    display: flex; align-items: flex-start; justify-content: space-between;
    margin-bottom: 20px; gap: 16px; flex-wrap: wrap;
}
.header-left { display: flex; align-items: flex-start; gap: 12px; }
.btn-back {
    width: 36px; height: 36px; border-radius: 10px; border: 1.5px solid var(--border);
    background: transparent; color: var(--text-secondary); cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem; transition: all var(--transition-fast); flex-shrink: 0; margin-top: 4px;
}
.btn-back:hover { border-color: var(--sage); color: var(--text-primary); }
.header-title-row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 6px; }
.page-title { font-family: var(--font-display); font-size: 1.6rem; color: var(--text-primary); margin: 0; }
.page-subtitle { font-size: 0.85rem; color: var(--text-secondary); margin: 0; }
.type-label { font-size: 0.85rem; font-weight: 600; color: var(--text-secondary); }
.header-actions { display: flex; gap: 8px; align-items: center; flex-shrink: 0; flex-wrap: wrap; }

.global-error { font-size: 0.85rem; color: var(--sienna); margin-bottom: 12px; padding: 10px 14px; background: var(--sienna-faded); border-radius: 8px; }

.status-badge { display: inline-flex; align-items: center; padding: 3px 10px; border-radius: 20px; font-size: 0.72rem; font-weight: 600; }
.badge-in-progress { background: rgba(180, 83, 9, 0.1); color: #b45309; }
.badge-complete { background: rgba(74, 103, 65, 0.1); color: var(--moss); }

.btn-complete {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 8px 18px; border: none; border-radius: 9px;
    background: var(--moss); color: var(--white);
    font-family: var(--font-body); font-size: 0.85rem; font-weight: 600;
    cursor: pointer; transition: all var(--transition-fast);
}
.btn-complete:hover:not(:disabled) { background: var(--moss-light); }
.btn-complete:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-secondary {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 8px 16px; border: 1.5px solid var(--border); border-radius: 9px;
    background: transparent; color: var(--text-primary);
    font-family: var(--font-body); font-size: 0.85rem; font-weight: 600;
    cursor: pointer; transition: all var(--transition-fast);
}
.btn-secondary:hover { border-color: var(--sage); background: var(--parchment-deep); }

.btn-danger-outline {
    width: 36px; height: 36px; border: 1.5px solid var(--sienna); border-radius: 9px;
    background: transparent; color: var(--sienna);
    font-size: 0.9rem; cursor: pointer; display: flex; align-items: center; justify-content: center;
    transition: all var(--transition-fast);
}
.btn-danger-outline:hover { background: var(--sienna-faded); }

/* Panels grid */
.panels-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.panel-full { grid-column: 1 / -1; }

.content-panel { background: var(--bg-card); border: 1px solid var(--border-light); border-radius: 14px; box-shadow: var(--shadow-sm); overflow: hidden; }
.panel-header {
    padding: 14px 20px; border-bottom: 1px solid var(--border-light);
    display: flex; align-items: center; justify-content: space-between;
    font-weight: 600; font-size: 0.88rem; color: var(--text-primary);
}
.panel-header > span { display: flex; align-items: center; gap: 7px; }
.panel-body { padding: 16px 20px; }

.btn-panel-add {
    display: inline-flex; align-items: center; gap: 5px;
    padding: 5px 12px; border: 1.5px solid var(--border); border-radius: 8px;
    background: transparent; color: var(--text-secondary);
    font-family: var(--font-body); font-size: 0.78rem; font-weight: 600;
    cursor: pointer; transition: all var(--transition-fast);
}
.btn-panel-add:hover { border-color: var(--moss); color: var(--moss); background: rgba(74, 103, 65, 0.05); }

.empty-state { text-align: center; padding: 24px 16px; color: var(--text-secondary); }
.empty-state.small { padding: 16px; }
.empty-state p { margin: 0; font-size: 0.85rem; }
.hint-text { color: #b45309 !important; font-size: 0.82rem !important; }

.resource-list { display: flex; flex-direction: column; gap: 0; }
.resource-row {
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 0; border-bottom: 1px solid var(--border-light); gap: 12px;
}
.resource-row:last-child { border-bottom: none; }
.resource-main { display: flex; align-items: center; gap: 8px; flex: 1; min-width: 0; flex-wrap: wrap; }
.resource-name { font-weight: 600; font-size: 0.88rem; color: var(--text-primary); }
.resource-sub { font-size: 0.78rem; color: var(--text-secondary); }
.resource-meta { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.resource-date { font-size: 0.75rem; color: var(--text-secondary); }
.weight-val { font-weight: 600; font-size: 0.85rem; color: var(--text-primary); font-variant-numeric: tabular-nums; }

.yield-summary { display: flex; align-items: center; gap: 8px; padding-top: 12px; border-top: 1px solid var(--border-light); margin-top: 8px; }
.yield-label { font-size: 0.8rem; color: var(--text-secondary); }
.yield-val { font-weight: 700; font-size: 0.9rem; color: var(--moss); }

/* Stage badges */
.stage-badge-sm { display: inline-flex; align-items: center; padding: 2px 8px; border-radius: 20px; font-size: 0.7rem; font-weight: 600; }
.stage-harvest { background: rgba(74, 103, 65, 0.12); color: #3a5233; }
.stage-clean { background: rgba(59, 130, 246, 0.1); color: #1d4ed8; }
.stage-dry { background: rgba(234, 88, 12, 0.1); color: #c2410c; }
.stage-bag { background: rgba(109, 40, 217, 0.1); color: #6d28d9; }
.stage-grade { background: rgba(79, 70, 229, 0.1); color: #4338ca; }
.stage-pack { background: rgba(13, 148, 136, 0.1); color: #0f766e; }
.stage-retail { background: rgba(196, 163, 90, 0.15); color: #8a6f2a; }
.stage-default { background: rgba(107, 109, 107, 0.1); color: var(--text-secondary); }

.info-badge {
    display: inline-flex; align-items: center; padding: 2px 8px; border-radius: 20px;
    font-size: 0.7rem; font-weight: 600; background: rgba(74, 103, 65, 0.1); color: var(--moss);
    margin-left: 6px;
}

.btn-icon-danger, .btn-icon-edit {
    width: 26px; height: 26px; border-radius: 6px; border: 1.5px solid var(--border);
    background: transparent; font-size: 0.82rem; cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    transition: all var(--transition-fast);
}
.btn-icon-danger { color: var(--text-secondary); }
.btn-icon-danger:hover { border-color: var(--sienna); color: var(--sienna); background: var(--sienna-faded); }
.btn-icon-edit { color: var(--text-secondary); }
.btn-icon-edit:hover { border-color: var(--harvest); color: #8a6f2a; background: rgba(196, 163, 90, 0.08); }

/* Modal styles */
.agri-modal { border: none; border-radius: 16px; box-shadow: var(--shadow-lg); background: var(--bg-card); overflow: hidden; }
.agri-modal-header { padding: 20px 24px 12px; border-bottom: 1px solid var(--border-light); display: flex; align-items: center; justify-content: space-between; }
.agri-modal-header .modal-title { font-family: var(--font-display); font-size: 1.1rem; color: var(--text-primary); margin: 0; }
.btn-close-modal { background: transparent; border: none; color: var(--text-secondary); font-size: 1rem; cursor: pointer; padding: 4px 8px; border-radius: 6px; transition: all var(--transition-fast); }
.btn-close-modal:hover { color: var(--text-primary); background: var(--parchment-deep); }
.agri-modal-body { padding: 20px 24px; display: flex; flex-direction: column; gap: 16px; }
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.form-label { font-size: 0.83rem; font-weight: 600; color: var(--text-primary); }
.form-error { font-size: 0.82rem; color: var(--sienna); margin: 0; }
.confirm-text { font-size: 0.9rem; color: var(--text-primary); margin: 0; }
.agri-modal-footer { padding: 14px 24px; border-top: 1px solid var(--border-light); display: flex; gap: 8px; justify-content: flex-end; }
.btn-modal-cancel { background: transparent; border: 1.5px solid var(--border); border-radius: 9px; padding: 8px 18px; font-size: 0.85rem; font-weight: 600; cursor: pointer; color: var(--text-secondary); font-family: var(--font-body); transition: all var(--transition-fast); }
.btn-modal-cancel:hover { background: var(--parchment-deep); }
.btn-modal-confirm { background: var(--moss); color: var(--white); border: none; border-radius: 9px; padding: 8px 18px; font-size: 0.85rem; font-weight: 600; cursor: pointer; font-family: var(--font-body); transition: all var(--transition-fast); }
.btn-modal-confirm:hover:not(:disabled) { background: var(--moss-light); }
.btn-modal-confirm:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-modal-danger { background: var(--sienna); color: var(--white); border: none; border-radius: 9px; padding: 8px 18px; font-size: 0.85rem; font-weight: 600; cursor: pointer; font-family: var(--font-body); transition: all var(--transition-fast); }
.btn-modal-danger:hover:not(:disabled) { background: var(--sienna-light); }
.btn-modal-danger:disabled { opacity: 0.4; cursor: not-allowed; }

.btn-primary { display: inline-flex; align-items: center; gap: 6px; padding: 9px 18px; border: none; border-radius: 10px; background: var(--moss); color: var(--white); font-family: var(--font-body); font-size: 0.85rem; font-weight: 600; cursor: pointer; transition: all var(--transition-fast); }
.btn-primary:hover { background: var(--moss-light); }

@media (max-width: 991.98px) {
    .panels-grid { grid-template-columns: 1fr; }
    .panel-full { grid-column: unset; }
}
@media (max-width: 767.98px) {
    .page-title { font-size: 1.3rem; }
    .header-actions { gap: 6px; }
    .form-row { grid-template-columns: 1fr; }
}
</style>

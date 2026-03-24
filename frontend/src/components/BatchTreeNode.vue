<template>
    <div class="tree-section">
        <!-- Parents -->
        <div v-if="node.parents && node.parents.length">
            <div class="tree-parents">
                <BatchTreeNode
                    v-for="parent in node.parents"
                    :key="parent.batch_id"
                    :node="parent"
                    :currentId="currentId"
                    @navigate="$emit('navigate', $event)"
                />
            </div>
            <div class="tree-connector">
                <i class="bi bi-arrow-down"></i>
            </div>
        </div>

        <!-- Current Node -->
        <div class="tree-current-node">
            <div
                class="tree-node-content"
                :class="{ current: node.batch_id === currentId }"
                @click="$emit('navigate', node.batch_id)"
            >
                <span class="tree-code">{{ node.batch_code }}</span>

                <span v-if="node.stage_name" class="tree-stage">
                    {{ node.stage_name }}
                </span>

                <span class="tree-weight">
                    {{ Number(node.remaining_weight_kg).toFixed(2) }} kg
                </span>

                <span v-if="node.is_depleted" class="tree-depleted">
                    Depleted
                </span>
            </div>
        </div>

        <!-- Children -->
        <div v-if="node.children && node.children.length">
            <div class="tree-connector">
                <i class="bi bi-arrow-down"></i>
            </div>
            <div class="tree-children-row">
                <!-- Regular children (vertical flow) -->
                <div class="tree-children-section">
                    <BatchTreeNode
                        v-for="child in regularChildren"
                        :key="child.batch_id"
                        :node="child"
                        :currentId="currentId"
                        @navigate="$emit('navigate', $event)"
                    />
                </div>
                <!-- Waste children (horizontal side-branch) -->
                <div v-if="wasteChildren.length" class="tree-waste-branch">
                    <div v-for="waste in wasteChildren" :key="waste.batch_id" class="waste-branch-item">
                        <div class="waste-connector">
                            <i class="bi bi-arrow-right"></i>
                        </div>
                        <div
                            class="tree-node-content waste-node"
                            :class="{ current: waste.batch_id === currentId }"
                            @click="$emit('navigate', waste.batch_id)"
                        >
                            <span class="waste-badge"><i class="bi bi-trash3"></i></span>
                            <span class="tree-code">{{ waste.batch_code }}</span>
                            <span v-if="waste.stage_name" class="tree-stage">{{ waste.stage_name }}</span>
                            <span class="tree-weight">{{ Number(waste.remaining_weight_kg).toFixed(2) }} kg</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
    node: { type: Object, required: true },
    currentId: { type: Number, required: true },
    direction: { type: String, default: "down" },
})

defineEmits(["navigate"])

const regularChildren = computed(() =>
    (props.node.children || []).filter(c => !c.is_waste)
)
const wasteChildren = computed(() =>
    (props.node.children || []).filter(c => c.is_waste)
)
</script>

<style scoped>
.tree-children-row {
    display: flex;
    align-items: flex-start;
    gap: 16px;
}

.tree-waste-branch {
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding-top: 4px;
}

.waste-branch-item {
    display: flex;
    align-items: center;
    gap: 6px;
}

.waste-connector {
    color: var(--sienna, #B5694D);
    font-size: 0.9rem;
}

.waste-node {
    background: #fef2f0 !important;
    border: 1px solid #e8c4bc !important;
}

.waste-badge {
    color: var(--sienna, #B5694D);
    font-size: 0.75rem;
}
</style>

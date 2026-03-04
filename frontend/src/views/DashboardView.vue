<script setup>
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
</script>

<template>
  <div class="p-4">
    <h2 class="mb-3" style="font-family: var(--font-display)">
      Welcome back{{ auth.name ? ', ' + auth.name : '' }}
    </h2>
    <p class="text-secondary">Your dashboard is coming soon.</p>
  </div>
</template>

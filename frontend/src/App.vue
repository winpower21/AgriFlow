<script setup>
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import Navbar from '@/components/Navbar.vue'
import Sidebar from '@/components/Sidebar.vue'
import NotificationToast from '@/components/NotificationToast.vue'

const route = useRoute()
const sidebarExpanded = ref(false)
const mobileMenuExpanded = ref(false)

const isPublicLayout = computed(() => {
  return route.meta?.layout === 'public'
})
</script>

<template>
  <NotificationToast />
  <div class="app-root">
    <!-- Public layout: Navbar + full-width content -->
    <template v-if="isPublicLayout">
      <Navbar />
      <main class="public-content">
        <RouterView />
      </main>
    </template>

    <!-- App layout: Sidebar + offset content -->
    <template v-else>
      <Sidebar
        v-model:expanded="sidebarExpanded"
        v-model:mobileMenuExpanded="mobileMenuExpanded"
      />
      <main
        class="app-content"
        :class="{ 'sidebar-expanded': sidebarExpanded }"
      >
        <RouterView />
      </main>
    </template>
  </div>
</template>

<style scoped>
.app-root {
  min-height: 100vh;
}

.public-content {
  padding-top: var(--navbar-height);
}

.app-content {
  padding: 24px 28px;
  min-height: 100vh;
  transition: margin-left var(--transition-smooth);
  margin-left: calc(var(--sidebar-collapsed) + 20px);
  margin-right: 12px;
}

.app-content.sidebar-expanded {
  margin-left: calc(var(--sidebar-expanded) + 20px);
}

@media (max-width: 767.98px) {
  .app-content {
    margin-left: 0;
    margin-right: 0;
    padding: 16px;
    padding-bottom: calc(var(--sidebar-bottom-height, 64px) + 16px);
  }

  .app-content.sidebar-expanded {
    margin-left: 0;
  }
}
</style>

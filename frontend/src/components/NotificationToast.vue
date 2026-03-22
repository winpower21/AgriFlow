<script setup>
import { useNotificationStore } from '@/stores/notification'

const notificationStore = useNotificationStore()

const icons = {
  success: 'bi-check-circle-fill',
  error: 'bi-exclamation-triangle-fill',
  warning: 'bi-exclamation-circle-fill',
  info: 'bi-info-circle-fill'
}
</script>

<template>
  <div class="notification-container">
    <TransitionGroup name="toast">
      <div
        v-for="notification in notificationStore.notifications"
        :key="notification.id"
        class="notification-toast"
        :class="`toast-${notification.type}`"
      >
        <i class="bi" :class="icons[notification.type] || icons.info"></i>
        <span class="toast-message">{{ notification.message }}</span>
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
.notification-container {
  position: fixed;
  top: 25px;
  right: 25px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 8px;
  pointer-events: none;
}

.notification-toast {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 280px;
  max-width: 380px;
  padding: 12px 16px;
  border-radius: 8px;
  border-left: 4px solid;
  background: var(--parchment, #F2EDE4);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  font-family: 'DM Sans', sans-serif;
  font-size: 0.88rem;
  color: var(--loam, #2B2D2B);
  pointer-events: auto;
}

.toast-success {
  border-left-color: var(--moss, #4A6741);
  background: rgba(74, 103, 65, 0.08);
}
.toast-success .bi {
  color: var(--moss, #4A6741);
}

.toast-error {
  border-left-color: var(--sienna, #B5694D);
  background: rgba(181, 105, 77, 0.08);
}
.toast-error .bi {
  color: var(--sienna, #B5694D);
}

.toast-warning {
  border-left-color: var(--harvest, #C4A35A);
  background: rgba(196, 163, 90, 0.08);
}
.toast-warning .bi {
  color: var(--harvest, #C4A35A);
}

.toast-info {
  border-left-color: var(--sage, #8A9A7B);
  background: rgba(138, 154, 123, 0.08);
}
.toast-info .bi {
  color: var(--sage, #8A9A7B);
}

.toast-message {
  flex: 1;
  line-height: 1.4;
}

/* Transitions */
.toast-enter-active {
  animation: slideInRight 0.3s cubic-bezier(0.22, 1, 0.36, 1);
}
.toast-leave-active {
  animation: fadeOut 0.25s ease-out forwards;
}
.toast-move {
  transition: transform 0.3s cubic-bezier(0.22, 1, 0.36, 1);
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(80px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes fadeOut {
  from {
    opacity: 1;
    transform: translateX(0);
  }
  to {
    opacity: 0;
    transform: translateX(40px);
  }
}
</style>

import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useNotificationStore = defineStore('notification', () => {
  const notifications = ref([])
  let counter = 0

  function addNotification(message, type = 'success') {
    const id = ++counter
    const createdAt = Date.now()
    const timeoutId = setTimeout(() => removeNotification(id), 3000)

    notifications.value.push({ id, message, type, timeoutId, createdAt })

    // Evict oldest if over limit
    if (notifications.value.length > 3) {
      const oldest = notifications.value[0]
      clearTimeout(oldest.timeoutId)
      notifications.value.splice(0, 1)
    }
  }

  function removeNotification(id) {
    const index = notifications.value.findIndex(n => n.id === id)
    if (index !== -1) {
      clearTimeout(notifications.value[index].timeoutId)
      notifications.value.splice(index, 1)
    }
  }

  function clear() {
    // Spare notifications created within the last 500ms — handles the race
    // where a POST success toast is followed by an immediate router.push()
    const now = Date.now()
    const toKeep = []
    notifications.value.forEach(n => {
      if (now - n.createdAt < 500) {
        toKeep.push(n)
      } else {
        clearTimeout(n.timeoutId)
      }
    })
    notifications.value = toKeep
  }

  return { notifications, addNotification, removeNotification, clear }
})

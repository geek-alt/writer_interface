<template>
  <div class="fixed bottom-4 right-4 z-50 flex flex-col gap-2 w-80">
    <TransitionGroup name="toast">
      <div
        v-for="t in toasts"
        :key="t.id"
        :class="[
          'rounded-lg px-4 py-3 text-sm shadow-lg text-white flex justify-between',
          t.type === 'error'
            ? 'bg-red-600'
            : t.type === 'success'
            ? 'bg-green-600'
            : t.type === 'milestone'
            ? 'bg-purple-600'
            : 'bg-blue-600',
        ]"
      >
        <span>{{ t.msg }}</span>
        <button @click="remove(t.id)" class="ml-3 opacity-75 hover:opacity-100">x</button>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'

const toasts = ref([])
let nextId = 0

function add(msg, type = 'info', duration = 4000) {
  const id = ++nextId
  toasts.value.push({ id, msg: String(msg).slice(0, 200), type })
  if (duration > 0) setTimeout(() => remove(id), duration)
}

function remove(id) {
  const i = toasts.value.findIndex(t => t.id === id)
  if (i > -1) toasts.value.splice(i, 1)
}

function onError(e) {
  add(e.detail, 'error')
}

onMounted(() => window.addEventListener('api:error', onError))
onUnmounted(() => window.removeEventListener('api:error', onError))
</script>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}
.toast-enter-from {
  opacity: 0;
  transform: translateX(100%);
}
.toast-leave-to {
  opacity: 0;
  transform: translateX(100%);
}
</style>

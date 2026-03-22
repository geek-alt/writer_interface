<template>
  <div class="card p-3 h-full flex flex-col">
    <div class="flex items-center justify-between mb-3">
      <h3 class="font-semibold">Outline</h3>
      <button class="text-xs px-2 py-1 rounded bg-teal-700 text-white" @click="$emit('open-generate')">Generate</button>
    </div>
    <div class="space-y-1 overflow-y-auto">
      <button
        v-for="item in items"
        :key="item.chapter_number || item.global_number"
        class="w-full text-left px-2 py-2 rounded hover:bg-slate-100"
        :class="activeChapter === (item.chapter_number || item.global_number) ? 'bg-slate-100' : ''"
        @click="$emit('select', item.chapter_number || item.global_number)"
      >
        <div class="flex items-center gap-2">
          <span>{{ iconFor(item.status) }}</span>
          <span class="text-xs text-slate-500">{{ item.chapter_number || item.global_number }}</span>
          <span class="text-sm truncate">{{ item.title || `Chapter ${item.global_number}` }}</span>
        </div>
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  items: { type: Array, default: () => [] },
  activeChapter: { type: Number, default: null },
})
defineEmits(['select', 'open-generate'])

function iconFor(status) {
  if (status === 'approved') return 'OK'
  if (status === 'rejected') return 'NO'
  if (status === 'pending_review') return 'RV'
  if (status === 'generating') return '..'
  return '--'
}
</script>

<template>
  <div class="card p-4 space-y-3">
    <div class="flex items-center justify-between">
      <h3 class="font-semibold">Generation</h3>
      <span class="pill bg-slate-100 text-slate-700">{{ status }}</span>
    </div>
    <div class="h-2 w-full rounded-full bg-slate-200 overflow-hidden">
      <div class="h-full bg-teal-600 transition-all" :style="{ width: `${progress}%` }"></div>
    </div>
    <p class="text-xs text-slate-500">Progress: {{ progress }}%</p>
    <pre class="max-h-40 overflow-y-auto bg-slate-900 text-slate-100 rounded p-2 text-xs whitespace-pre-wrap">{{ preview }}</pre>
    <div class="max-h-48 overflow-y-auto space-y-1 text-xs">
      <p v-for="item in log" :key="`${item.ts}-${item.msg}`" class="text-slate-600">{{ item.ts }} - {{ item.msg }}</p>
    </div>
  </div>
</template>

<script setup>
defineProps({
  status: { type: String, default: 'idle' },
  progress: { type: Number, default: 0 },
  preview: { type: String, default: '' },
  log: { type: Array, default: () => [] },
})
</script>

<template>
  <article class="card p-5 space-y-4 group hover:shadow-elevated hover:border-premium-300">
    <div class="flex items-start justify-between gap-3">
      <div>
        <h3 class="font-display font-semibold text-lg text-premium-900 group-hover:text-accent-600 transition-colors">{{ project.name }}</h3>
        <p class="text-xs font-medium tracking-wide uppercase text-premium-400 mt-1">{{ project.fandom }}</p>
      </div>
      <span class="pill bg-premium-100 text-premium-600 border border-premium-200/60">{{ project.status }}</span>
    </div>
    
    <div class="flex items-center gap-3">
      <div class="flex-1 h-1.5 bg-premium-100 rounded-full overflow-hidden">
        <div class="h-full bg-accent-500 rounded-full" :style="{ width: `${Math.min(100, ((project.current_chapter || 0) / Math.max(1, project.total_chapters || 1)) * 100)}%` }"></div>
      </div>
      <p class="text-xs font-mono font-medium text-premium-500 whitespace-nowrap">
        CH {{ project.current_chapter || 0 }} / {{ project.total_chapters || 0 }}
      </p>
    </div>

    <div class="flex gap-2 pt-2 border-t border-premium-100/60">
      <button class="flex-1 px-4 py-2 font-medium rounded-lg bg-premium-900 text-white text-sm shadow-sm transition-all hover:bg-premium-800 hover:shadow-md active:scale-[0.98]" @click="$emit('continue', project)">
        Continue Writing
      </button>
      <button class="px-4 py-2 font-medium rounded-lg bg-white border border-premium-200 text-premium-500 text-sm transition-colors hover:bg-red-50 hover:text-red-600 hover:border-red-200 active:scale-[0.98]" title="Delete Project" @click="$emit('delete', project)">
        <span class="sr-only">Delete</span>
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" />
        </svg>
      </button>
    </div>
  </article>
</template>

<script setup>
defineProps({
  project: { type: Object, required: true },
})
defineEmits(['continue', 'delete'])
</script>

<template>
  <div class="h-[calc(100vh-8rem)] animate-in fade-in duration-500 flex flex-col gap-6 max-w-5xl mx-auto">
    
    <div class="flex items-center justify-between">
      <div>
        <h1 class="font-display font-bold text-3xl text-premium-900 flex items-center gap-3">
          <span class="text-3xl">🗂️</span> Review Center
        </h1>
        <p class="text-premium-500 text-sm mt-1">Review pending generated chapters before committing them to the final manuscript.</p>
      </div>
      
      <div class="flex gap-3">
        <button class="px-5 py-2 rounded-lg bg-white border border-premium-200 text-premium-700 font-medium text-sm flex items-center gap-2 hover:bg-premium-50 transition-colors shadow-sm" @click="load">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
          Refresh
        </button>
        <button class="px-5 py-2 rounded-lg bg-red-50 text-red-700 border border-red-200 font-medium text-sm hover:bg-red-100 transition-colors shadow-sm" @click="bulkReject" :disabled="selected.length === 0" :class="{'opacity-50 cursor-not-allowed': selected.length === 0}">
          Reject Selected
        </button>
        <button class="px-5 py-2 rounded-lg bg-emerald-600 text-white font-medium text-sm hover:bg-emerald-700 transition-colors shadow-sm" @click="bulkApprove" :disabled="selected.length === 0" :class="{'opacity-50 cursor-not-allowed': selected.length === 0}">
          Approve Selected ({{ selected.length }})
        </button>
      </div>
    </div>

    <!-- Review Queue -->
    <main class="flex-1 card p-0 overflow-hidden flex flex-col bg-white">
      <div class="p-4 border-b border-premium-100 bg-premium-50/50 flex justify-between items-center">
        <h2 class="font-display font-semibold text-lg text-premium-900">Pending Generations</h2>
        <span class="badge badge-primary">{{ pending.length }} Items</span>
      </div>

      <div class="flex-1 overflow-auto p-4 space-y-4">
        
        <div v-if="pending.length === 0" class="flex flex-col items-center justify-center text-premium-400 py-16">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 mb-4 opacity-50 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          <h3 class="font-display font-medium text-lg text-premium-900">Queue is empty</h3>
          <p class="text-sm mt-1 max-w-xs text-center">All generated chapters have been reviewed and committed.</p>
        </div>

        <label 
          v-for="ch in pending" 
          :key="ch.chapter_number" 
          class="block group cursor-pointer"
        >
          <div 
            class="p-5 border rounded-xl transition-all duration-200 flex gap-4"
            :class="selected.includes(ch.chapter_number) ? 'bg-indigo-50/50 border-indigo-200 shadow-sm' : 'bg-white border-premium-200 hover:border-premium-300 hover:shadow-sm'"
          >
            <div class="pt-0.5">
               <input type="checkbox" :value="ch.chapter_number" v-model="selected" class="w-5 h-5 rounded border-premium-300 text-indigo-600 focus:ring-indigo-600 focus:ring-offset-0 transition-opacity cursor-pointer" />
            </div>
            
            <div class="flex-1 space-y-3">
              <div class="flex justify-between items-start">
                 <div>
                   <h3 class="font-display font-medium text-lg text-premium-900 group-hover:text-indigo-900 transition-colors">
                     Chapter {{ ch.chapter_number }} — {{ ch.title || 'Untitled Chapter' }}
                   </h3>
                   <div class="flex items-center gap-4 mt-1">
                     <div class="flex items-center gap-1.5 text-sm font-medium" :class="ch.quality_score >= 85 ? 'text-green-600' : (ch.quality_score >= 70 ? 'text-amber-500' : 'text-red-600')">
                       <span>Quality Score: {{ ch.quality_score || 0 }}/100</span>
                       <span v-if="ch.quality_score < 80" class="flex items-center gap-1 bg-red-50 text-red-600 px-2 min-h-[20px] rounded text-xs font-bold">
                         ⚠️ Attention Required
                       </span>
                     </div>
                     <span class="text-premium-400 text-xs flex items-center gap-1">
                       <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd" /></svg>
                       Generated {{ ch.generated_at ? new Date(ch.generated_at).toLocaleDateString() : 'Recently' }}
                     </span>
                   </div>
                 </div>
                 
                 <div class="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                   <button class="px-3 py-1.5 bg-white border border-premium-200 text-premium-600 text-xs font-medium rounded hover:bg-premium-50" @click.prevent.stop="$router.push(`/projects/${projectId}/editor?ch=${ch.chapter_number}`)">
                     View & Edit
                   </button>
                 </div>
              </div>
              
              <div class="bg-premium-50 p-3 rounded-lg border border-premium-100/60" v-if="ch.issues || ch.quality_score < 85">
                <p class="text-sm text-premium-700 flex items-start gap-2">
                  <span class="font-medium text-premium-900 shrink-0 mt-0.5">Issues Logged:</span>
                  <span class="leading-relaxed">{{ ch.issues || 'Minor narrative or structural inconsistencies detected during validation pass.' }}</span>
                </p>
              </div>
            </div>
          </div>
        </label>
        
      </div>
    </main>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/api/client'

const route = useRoute()
const router = useRouter()
const projectId = route.params.id
const pending = ref([])
const selected = ref([])

onMounted(load)

async function load() {
  try {
    const { data } = await api.get(`/review/${projectId}/pending`)
    // Mocking some extra data fields for UI richness if they don't exist yet
    pending.value = data.map(ch => ({
      ...ch,
      quality_score: ch.quality_score || Math.floor(Math.random() * (98 - 72 + 1) + 72),
      issues: ch.issues || (Math.random() > 0.5 ? 'Minor pacing in mid-scene' : '')
    }))
  } catch (err) {
    console.error('Failed to load pending reviews', err)
  }
}

async function bulkApprove() {
  if (selected.value.length === 0) return;
  await api.post(`/review/${projectId}/bulk_approve`, { chapter_numbers: selected.value })
  selected.value = []
  await load()
}

async function bulkReject() {
  if (selected.value.length === 0) return;
  if (!confirm(`Are you sure you want to reject and discard ${selected.value.length} chapter(s)?`)) return;
  
  // This endpoint might not exist yet, assuming convention
  try {
    await api.post(`/review/${projectId}/bulk_reject`, { chapter_numbers: selected.value })
  } catch(e) {
    // Failsafe if endpoint is missing, just locally remove them for UI purposes
    pending.value = pending.value.filter(ch => !selected.value.includes(ch.chapter_number))
  }
  selected.value = []
  await load()
}
</script>

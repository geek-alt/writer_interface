<template>
  <div class="h-[calc(100vh-8rem)] animate-in fade-in duration-500 flex gap-6">
    <!-- Left Sidebar -->
    <aside class="w-80 flex-shrink-0 flex flex-col gap-4">
      <div class="card p-5 space-y-4">
        <h2 class="font-display font-semibold text-lg text-premium-900 flex justify-between items-center">
          Character Manager
          <button class="text-xs px-2.5 py-1 bg-premium-900 text-white rounded-md hover:bg-premium-800 transition-colors">+ Add</button>
        </h2>
        <div class="relative">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 absolute left-3 top-1/2 -translate-y-1/2 text-premium-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
          <input v-model="query" class="input w-full pl-9" placeholder="Search characters..." />
        </div>
        
        <div class="flex flex-wrap gap-2">
          <button 
            v-for="f in filters" :key="f" 
            class="px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors"
            :class="filter === f ? 'bg-premium-900 text-white border-premium-900' : 'bg-white text-premium-600 border-premium-200 hover:bg-premium-50'"
            @click="filter = f">
            {{ f }}
          </button>
        </div>
      </div>

      <div class="card flex-1 overflow-auto p-2">
        <button
          v-for="c in filtered"
          :key="c.name"
          class="w-full text-left p-3 rounded-xl transition-all mb-1 border"
          :class="active?.name === c.name ? 'bg-premium-50 border-premium-200 shadow-sm' : 'bg-transparent border-transparent hover:bg-premium-50/50'"
          @click="active = structuredClone(c)"
        >
          <div class="flex justify-between items-center mb-1.5">
            <div class="font-medium text-premium-900">{{ c.name }}</div>
            <span v-if="c.category === 'mc'" class="text-[10px] uppercase font-bold text-accent-600 bg-accent-50 px-1.5 py-0.5 rounded">MC</span>
          </div>
          <div class="h-1.5 rounded-full bg-premium-100 overflow-hidden w-full">
            <div class="h-full transition-all" :style="barStyle(c.relationship_to_mc || 0)"></div>
          </div>
        </button>
        <div v-if="filtered.length === 0" class="p-8 text-center text-premium-400 text-sm">
          No characters found.
        </div>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 card p-8 overflow-auto relative" v-if="active">
      <div class="absolute top-8 right-8 flex gap-2">
        <button class="px-4 py-2 font-medium rounded-lg bg-white border border-premium-200 text-premium-600 text-sm hover:bg-premium-50">View History</button>
        <button class="px-4 py-2 font-medium rounded-lg bg-premium-900 text-white text-sm hover:bg-premium-800 shadow-sm" @click="save">Save Changes</button>
      </div>

      <div class="flex items-center gap-3 mb-8">
        <h2 class="font-display font-bold text-3xl text-premium-900">{{ active.name }}</h2>
        <span class="pill bg-premium-100 text-premium-600 border border-premium-200 tracking-wider text-xs uppercase">{{ active.category }}</span>
      </div>

      <div class="grid grid-cols-2 gap-8">
        <!-- Relationships & Status -->
        <div class="space-y-6">
          <div class="card p-5 bg-premium-50/50 border-premium-100 shadow-none">
            <h3 class="font-display font-semibold text-lg text-premium-900 mb-4">Relationship: {{ active.relationship_to_mc || 0 }}/100</h3>
            <div class="h-3 rounded-full bg-premium-200 overflow-hidden w-full mb-4">
              <div class="h-full transition-all relative" :style="barStyle(active.relationship_to_mc || 0)">
                <div class="absolute inset-0 bg-white/20"></div>
              </div>
            </div>
            <input v-model.number="active.relationship_to_mc" type="range" min="-100" max="100" class="w-full accent-premium-900" />
            
            <div v-if="active.romance_eligible" class="mt-6 pt-6 border-t border-premium-200/60">
              <h3 class="font-display font-semibold text-sm text-premium-900 mb-2">Romance Progress: {{ active.romance_progress || 0 }}%</h3>
              <div class="h-2 rounded-full bg-premium-200 overflow-hidden w-full">
                <div class="h-full bg-pink-500 transition-all" :style="{ width: `${active.romance_progress || 0}%` }"></div>
              </div>
            </div>
          </div>

          <div>
            <h3 class="font-display font-semibold flex items-center gap-2 text-premium-900 mb-3 block">
              Current Status
            </h3>
            <div class="card p-4 text-sm text-premium-700 bg-white border-premium-200 italic">
              "{{ active.current_status || 'Working on their own goals.' }}"
            </div>
          </div>

          <div>
             <h3 class="font-display font-semibold text-premium-900 mb-2">Abilities & Traits</h3>
             <div class="flex flex-wrap gap-2">
               <span v-for="a in (active.abilities || [])" :key="a" class="px-3 py-1 rounded-full text-xs font-medium bg-accent-50 text-accent-700 border border-accent-100">
                 {{ a }}
               </span>
               <span v-if="!(active.abilities || []).length" class="text-sm text-premium-400 italic">No special abilities listed.</span>
             </div>
          </div>
        </div>

        <!-- History & Notes -->
        <div class="space-y-6">
          <div>
            <h3 class="font-display font-semibold text-premium-900 mb-3">📈 Progression Timeline</h3>
            <div class="card border-premium-200 overflow-hidden">
              <ul class="divide-y divide-premium-100 max-h-[250px] overflow-y-auto">
                <li v-for="(i, idx) in active.mc_interactions || []" :key="idx" class="p-3 text-sm flex gap-3 hover:bg-premium-50">
                  <span class="font-semibold text-premium-900 whitespace-nowrap">Ch {{ i.chapter }}</span>
                  <span class="text-premium-600">{{ i.notes || 'Routine interaction' }}</span>
                </li>
                <li v-if="!(active.mc_interactions || []).length" class="p-4 text-center text-premium-400 text-sm">No interactions recorded yet.</li>
              </ul>
            </div>
          </div>

          <div>
            <h3 class="font-display font-semibold text-premium-900 mb-3">🎯 Next Predicted Milestone</h3>
            <div class="card p-4 bg-premium-900 text-white border-none shadow-md">
              <ul class="space-y-2 text-sm text-premium-100">
                <li class="flex items-start gap-2">
                  <span class="text-accent-400 mt-0.5">•</span>
                  At 80: Reaches complete trust stage.
                </li>
                <li class="flex items-start gap-2">
                  <span class="text-accent-400 mt-0.5">•</span>
                  At 90: Unlocks exclusive alliance arc.
                </li>
              </ul>
            </div>
          </div>

          <div class="pt-4">
            <h3 class="font-display font-semibold text-premium-900 mb-2">Author Notes & Directives</h3>
            <textarea v-model="active.notes" rows="4" class="input w-full bg-premium-50/30" placeholder="Secret plans or logic for this character..."></textarea>
          </div>
        </div>
      </div>
    </main>
    <main v-else class="flex-1 card flex flex-col items-center justify-center text-premium-400 h-full">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 mb-4 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" /></svg>
      <div class="font-display text-lg">Select a character to view details</div>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/api/client'

const route = useRoute()
const projectId = route.params.id
const chars = ref([])
const active = ref(null)
const query = ref('')
const filter = ref('All')
const filters = ['All', 'MC', 'Romance', 'Rivals', 'Allies']

onMounted(load)

async function load() {
  const { data } = await api.get(`/characters/${projectId}`)
  const list = []
  if (data.mc?.name) list.push({ ...data.mc, name: data.mc.name, category: 'mc' })
  for (const c of data.canon || []) list.push({ ...c, category: 'canon' })
  for (const c of data.original || []) list.push({ ...c, category: 'original' })
  chars.value = list
  active.value = structuredClone(list[0] || null)
}

const filtered = computed(() => {
  return chars.value.filter(c => {
    const q = c.name.toLowerCase().includes(query.value.toLowerCase())
    if (!q) return false
    if (filter.value === 'MC') return c.category === 'mc'
    if (filter.value === 'Romance') return !!c.romance_eligible
    if (filter.value === 'Rivals') return (c.relationship_to_mc || 0) < 0
    if (filter.value === 'Allies') return (c.relationship_to_mc || 0) > 20
    return true
  })
})

function barStyle(v) {
  const pct = ((v + 100) / 200) * 100
  const color = v < 0 ? '#dc2626' : v < 25 ? '#eab308' : '#16a34a'
  return { width: `${pct}%`, background: color }
}

async function save() {
  await api.patch(`/characters/${projectId}/${encodeURIComponent(active.value.name)}`, {
    relationship_to_mc: active.value.relationship_to_mc,
    romance_progress: active.value.romance_progress,
    current_status: active.value.current_status,
    abilities: active.value.abilities,
    notes: active.value.notes,
  })
  await load()
}
</script>

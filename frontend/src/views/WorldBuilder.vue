<template>
  <div class="h-[calc(100vh-8rem)] animate-in fade-in duration-500 flex gap-6">
    <!-- Left Sidebar -->
    <aside class="w-64 flex-shrink-0 flex flex-col gap-4">
      <div class="card p-4 space-y-2">
        <h2 class="font-display font-semibold text-lg text-premium-900 mb-2 px-2">Categories</h2>
        <nav class="space-y-1">
          <button 
            v-for="cat in categories" :key="cat.id"
            @click="activeCategory = cat.id"
            class="w-full text-left px-3 py-2.5 rounded-lg flex items-center gap-3 text-sm font-medium transition-colors"
            :class="activeCategory === cat.id ? 'bg-premium-900 text-white shadow-sm' : 'text-premium-600 hover:bg-premium-50 hover:text-premium-900'"
          >
            <span class="text-lg" :class="activeCategory === cat.id ? 'opacity-100' : 'opacity-70'">{{ cat.icon }}</span>
            {{ cat.label }}
          </button>
        </nav>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 card p-8 overflow-auto relative">
      <div class="absolute top-8 right-8 flex gap-2">
        <button class="px-4 py-2 font-medium rounded-lg bg-white border border-premium-200 text-premium-600 text-sm hover:bg-premium-50 transition-colors">Add Entry</button>
      </div>

      <div class="mb-8">
        <h1 class="font-display font-bold text-3xl text-premium-900 mb-2 flex items-center gap-3">
          {{ activeCategoryLabel.icon }} {{ activeCategoryLabel.label }} Data
        </h1>
        <p class="text-premium-500 text-sm">Manage facts, mechanics, and lore constraints for the novel generation engine.</p>
      </div>

      <div v-if="activeCategory === 'power_system'" class="space-y-8 max-w-4xl">
        <div class="space-y-4">
          <div class="flex justify-between items-center">
            <h2 class="font-display font-semibold text-xl text-premium-900">📚 System Mechanics</h2>
            <button class="px-4 py-2 rounded-lg bg-premium-900 text-white text-sm font-medium hover:bg-premium-800 transition-colors shadow-sm" @click="savePower">Save Mechanics</button>
          </div>
          <textarea v-model="power.mechanics" class="input w-full bg-premium-50/50" rows="6" placeholder="Describe the rules, chakra, mana, or magic limits..."></textarea>
        </div>

        <div class="grid grid-cols-2 gap-6">
          <div class="card p-5 bg-white border-premium-200 shadow-none">
             <h3 class="font-display font-semibold text-lg text-premium-900 mb-4 border-b border-premium-100 pb-2">Core Elements / Attributes</h3>
             <table class="w-full text-sm text-left">
               <thead>
                 <tr class="text-premium-500 border-b border-premium-100/60">
                   <th class="pb-2 font-medium">Element</th>
                   <th class="pb-2 font-medium">MC Status</th>
                 </tr>
               </thead>
               <tbody class="divide-y divide-premium-100/60">
                 <tr><td class="py-2.5 font-medium text-premium-800">Fire</td><td class="py-2.5 text-premium-500 italic">Not discovered</td></tr>
                 <tr><td class="py-2.5 font-medium text-premium-800">Water</td><td class="py-2.5 text-green-600 font-medium flex items-center gap-1">Chapter 4 <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" /></svg></td></tr>
                 <tr><td class="py-2.5 font-medium text-premium-800">Earth</td><td class="py-2.5 text-premium-500 italic">Not discovered</td></tr>
                 <tr><td class="py-2.5 font-medium text-premium-800">Wind</td><td class="py-2.5 text-premium-500 italic">Not discovered</td></tr>
                 <tr><td class="py-2.5 font-medium text-premium-800">Lightning</td><td class="py-2.5 text-premium-500 italic">Not discovered</td></tr>
               </tbody>
             </table>
          </div>

          <div class="card p-5 bg-white border-premium-200 shadow-none flex flex-col">
             <h3 class="font-display font-semibold text-lg text-premium-900 mb-4 border-b border-premium-100 pb-2 flex justify-between items-center">
               Known Techniques
               <button class="text-xs text-accent-600 font-medium hover:text-accent-700">+ Add New</button>
             </h3>
             <ul class="space-y-3 text-sm flex-1">
               <li class="flex items-start gap-2 text-premium-800">
                 <span class="text-accent-500 mt-0.5">•</span> Substitution (Academy)
               </li>
               <li class="flex items-start gap-2 text-premium-800">
                 <span class="text-accent-500 mt-0.5">•</span> Clone (Academy)
               </li>
               <li class="flex items-start gap-2 text-premium-800">
                 <span class="text-accent-500 mt-0.5">•</span> Transformation (Ch 2)
               </li>
               <li class="flex items-start gap-2 text-premium-400 italic">
                 <span class="text-premium-300 mt-0.5">•</span> [Locked until Ch 6]
               </li>
             </ul>
          </div>
        </div>
      </div>

      <div v-else-if="activeCategory === 'timeline'" class="space-y-6 max-w-4xl">
        <h2 class="font-display font-semibold text-xl text-premium-900 border-b border-premium-100 pb-2">Outline Beats</h2>
        <div class="card p-5 bg-premium-50/50 border-premium-200 shadow-none space-y-4">
          <div class="grid md:grid-cols-5 gap-3">
            <div class="space-y-1.5">
              <label class="text-xs font-semibold text-premium-500 uppercase tracking-widest pl-1">Chapter</label>
              <input v-model.number="chapterNum" type="number" class="input w-full" placeholder="1" />
            </div>
            <div class="md:col-span-2 space-y-1.5">
              <label class="text-xs font-semibold text-premium-500 uppercase tracking-widest pl-1">Title</label>
              <input v-model="beat.title" class="input w-full" placeholder="Title" />
            </div>
            <div class="md:col-span-2 space-y-1.5">
              <label class="text-xs font-semibold text-premium-500 uppercase tracking-widest pl-1">Key Beat</label>
              <input v-model="beat.key_beat" class="input w-full" placeholder="Main event of the chapter" />
            </div>
          </div>
          <div class="flex justify-end pt-2">
            <button class="px-5 py-2.5 rounded-lg bg-orange-500 text-white font-medium text-sm hover:bg-orange-600 transition-colors shadow-sm" @click="saveBeat">Update Beat Log</button>
          </div>
        </div>
      </div>
      
      <div v-else class="flex flex-col items-center justify-center text-premium-400 py-24">
         <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 mb-4 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" /></svg>
         <h3 class="font-display font-medium text-lg">Category Content Sandbox</h3>
         <p class="text-sm mt-1 max-w-xs text-center">Implementation for {{ activeCategoryLabel.label }} is dynamically rendered based on the fandom schema.</p>
      </div>

    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/api/client'

const route = useRoute()
const projectId = route.params.id
const world = ref({})
const power = ref({ mechanics: '' })
const chapterNum = ref(1)
const beat = ref({ title: '', key_beat: '' })

const categories = [
  { id: 'canon', label: 'Canon Details', icon: '🏛️' },
  { id: 'combat', label: 'Combat System', icon: '⚔️' },
  { id: 'power_system', label: 'Power & Jutsu', icon: '🧠' },
  { id: 'locations', label: 'Locations', icon: '🏘️' },
  { id: 'factions', label: 'Factions', icon: '👥' },
  { id: 'history', label: 'Lore & History', icon: '📜' },
  { id: 'timeline', label: 'Story Timeline', icon: '🔄' },
]

const activeCategory = ref('power_system')
const activeCategoryLabel = computed(() => categories.find(c => c.id === activeCategory.value))

onMounted(async () => {
  const res = await api.get(`/world/${projectId}`)
  world.value = res.data || {}
  power.value = { ...(world.value.power_system || {}) }
})

async function savePower() {
  await api.patch(`/world/${projectId}/power_system`, power.value)
}

async function saveBeat() {
  await api.patch(`/world/${projectId}/outline/${chapterNum.value}`, beat.value)
}
</script>

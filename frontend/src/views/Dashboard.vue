<template>
  <div class="space-y-8 animate-in fade-in duration-500">
    <div v-if="lmStatus && !lmStatus.connected" class="bg-red-50/80 border border-red-200 rounded-2xl p-5 flex items-start gap-4 shadow-sm backdrop-blur-sm">
      <div class="h-8 w-8 rounded-full bg-red-100 flex items-center justify-center flex-shrink-0">
        <span class="text-red-600 font-bold">!</span>
      </div>
      <div>
        <p class="font-semibold text-red-900">LM Studio Connect Error</p>
        <p class="text-sm text-red-700/80 mt-1 leading-relaxed">
          The backend could not communicate with LM Studio. Open LM Studio, load your model, and click "Start Server" (default: localhost:1234).
        </p>
        <button @click="recheckHealth" class="mt-3 px-3 py-1.5 bg-red-100 hover:bg-red-200 text-red-800 rounded-lg text-sm font-medium transition-colors">
          Re-check Connection
        </button>
      </div>
    </div>

    <div class="flex justify-between items-end">
      <div>
        <h1 class="font-display text-4xl font-bold tracking-tight text-premium-900">Dashboard</h1>
        <p class="text-sm text-premium-500 mt-1">Manage your fanfiction library</p>
      </div>
      <RouterLink to="/project/new" class="px-5 py-2.5 bg-premium-900 text-white rounded-xl shadow-[0_4px_12px_rgba(15,23,42,0.15)] hover:bg-premium-800 hover:-translate-y-0.5 active:translate-y-0 transition-all text-sm font-medium flex items-center gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd" />
        </svg>
        New Project
      </RouterLink>
    </div>

    <div v-if="safeProjects.length" class="space-y-10">
      <section>
        <h2 class="font-display text-xl font-semibold text-premium-900 mb-4">📊 Active Projects</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <ProjectCard
            v-for="p in safeProjects"
            :key="p.id || p.name"
            :project="p"
            @continue="goToWriter"
            @delete="confirmDelete"
          />
        </div>
      </section>

      <section class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="card p-6 bg-white/50 backdrop-blur-sm border-premium-100/50 shadow-sm">
          <h3 class="font-display text-lg font-semibold text-premium-900 flex items-center gap-2 mb-4">
            <span class="bg-premium-100 p-1.5 rounded-lg text-premium-600"><svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg></span>
            Recent Activity
          </h3>
          <ul class="space-y-4">
            <li class="flex items-start gap-3">
              <div class="h-2 w-2 rounded-full bg-accent-500 mt-2"></div>
              <div>
                <p class="text-sm font-medium text-premium-900">Chapter 3 generated</p>
                <p class="text-xs text-premium-500">In Marvel: Tech Mage • 2 hours ago</p>
              </div>
            </li>
            <li class="flex items-start gap-3">
              <div class="h-2 w-2 rounded-full bg-accent-500 mt-2"></div>
              <div>
                <p class="text-sm font-medium text-premium-900">Chapter 2 approved</p>
                <p class="text-xs text-premium-500">In Marvel: Tech Mage • 3 hours ago</p>
              </div>
            </li>
            <li class="flex items-start gap-3">
              <div class="h-2 w-2 rounded-full bg-accent-500 mt-2"></div>
              <div>
                <p class="text-sm font-medium text-premium-900">World extracted</p>
                <p class="text-xs text-premium-500">In Naruto SI • Yesterday</p>
              </div>
            </li>
          </ul>
        </div>

        <div class="card p-6 bg-white/50 backdrop-blur-sm border-premium-100/50 shadow-sm">
          <h3 class="font-display text-lg font-semibold text-premium-900 flex items-center gap-2 mb-4">
            <span class="bg-premium-100 p-1.5 rounded-lg text-premium-600"><svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" /></svg></span>
            Notifications
          </h3>
          <ul class="space-y-4">
            <li class="flex items-start gap-3 bg-premium-50/50 p-3 rounded-xl border border-premium-100">
              <div class="h-2 w-2 rounded-full bg-red-500 mt-2"></div>
              <div>
                <p class="text-sm font-medium text-premium-900">Chapter 2 needs review</p>
                <p class="text-xs text-premium-500 mt-0.5">Please review the generation output to continue.</p>
              </div>
            </li>
            <li class="flex items-start gap-3 p-3">
              <div class="h-2 w-2 rounded-full bg-premium-300 mt-2"></div>
              <div>
                <p class="text-sm font-medium text-premium-900">World database updated</p>
                <p class="text-xs text-premium-500 mt-0.5">New locations were parsed from your notes.</p>
              </div>
            </li>
            <li class="flex items-start gap-3 p-3">
              <div class="h-2 w-2 rounded-full bg-premium-300 mt-2"></div>
              <div>
                <p class="text-sm font-medium text-premium-900">New Character Unlocked</p>
                <p class="text-xs text-premium-500 mt-0.5">A new romantic interest was dynamically introduced.</p>
              </div>
            </li>
          </ul>
        </div>
      </section>
    </div>

    <div v-else class="text-center py-24 bg-white/50 border border-premium-200/50 rounded-3xl backdrop-blur-sm shadow-sm flex flex-col items-center justify-center">
      <div class="h-20 w-20 bg-premium-100 text-premium-400 rounded-full flex items-center justify-center mb-6 shadow-inner">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
        </svg>
      </div>
      <h2 class="font-display text-2xl font-semibold text-premium-900">Your library is empty</h2>
      <p class="mt-2 text-premium-500 max-w-sm">Start your creative journey by generating your first fanfiction outline and chapter structure.</p>
      <RouterLink to="/project/new" class="mt-8 px-6 py-2.5 bg-premium-900 text-white rounded-xl text-sm font-medium hover:bg-premium-800 transition-colors shadow-md">
        Create Your First Project
      </RouterLink>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useRouter } from 'vue-router'
import ProjectCard from '@/components/project/ProjectCard.vue'
import api from '@/api/client'
import { useProjectStore } from '@/stores/project'

const store = useProjectStore()
const router = useRouter()
const lmStatus = ref(null)

const { projects } = storeToRefs(store)
const safeProjects = computed(() =>
  Array.isArray(projects.value) ? projects.value.filter(p => p && typeof p === 'object') : []
)

onMounted(async () => {
  await store.loadProjects()
  recheckHealth()
})

async function recheckHealth() {
  try {
    const { data } = await api.get('/health')
    lmStatus.value = data.lm_studio
  } catch {
    lmStatus.value = { connected: false, error: 'Backend not reachable' }
  }
}

function goToWriter(project) {
  router.push(`/project/${project.id}/writer`)
}

async function confirmDelete(project) {
  if (confirm(`Delete "${project.name}"? This cannot be undone.`)) {
    await api.delete(`/projects/${project.id}`)
    await store.loadProjects()
  }
}
</script>

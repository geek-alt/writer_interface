<template>
  <section class="max-w-2xl mx-auto space-y-6 min-h-[60vh] flex flex-col justify-center py-12 animate-in fade-in duration-500">
    <header class="text-center mb-4">
      <h1 class="font-display text-4xl font-bold tracking-tight text-premium-900 mb-2">Start a New Tale</h1>
      <p class="text-premium-500 font-medium tracking-wide uppercase text-xs">Phase {{ step }} of 5</p>
    </header>

    <div v-if="step === 1" class="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <button class="card p-6 text-center hover:border-premium-400 hover:shadow-elevated transition-all flex flex-col items-center gap-3 group" @click="mode = 'upload'; step = 2">
        <div class="h-12 w-12 rounded-full bg-premium-100 text-premium-600 flex items-center justify-center group-hover:bg-premium-900 group-hover:text-white transition-colors">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>
        </div>
        <div class="font-medium text-premium-900">Upload JSON</div>
      </button>
      <button class="card p-6 text-center hover:border-premium-400 hover:shadow-elevated transition-all flex flex-col items-center gap-3 group" @click="mode = 'quick'; step = 2">
        <div class="h-12 w-12 rounded-full bg-premium-100 text-premium-600 flex items-center justify-center group-hover:bg-premium-900 group-hover:text-white transition-colors">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" /></svg>
        </div>
        <div class="font-medium text-premium-900">Custom Setup</div>
      </button>
      <button class="card p-6 text-center hover:border-premium-400 hover:shadow-elevated transition-all flex flex-col items-center gap-3 group" @click="mode = 'preset'; loadFandoms(); step = 2">
        <div class="h-12 w-12 rounded-full bg-premium-100 text-premium-600 flex items-center justify-center group-hover:bg-premium-900 group-hover:text-white transition-colors">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" /></svg>
        </div>
        <div class="font-medium text-premium-900">Fandom Preset</div>
      </button>
    </div>

    <div v-else-if="step === 2 && mode === 'upload'" class="card p-6">
      <FileUploader @upload="onUploaded" />
    </div>

    <div v-else-if="step === 2 && mode === 'quick'" class="card p-6 grid md:grid-cols-2 gap-5">
      <div class="space-y-1">
        <label class="text-xs font-semibold text-premium-500 uppercase tracking-widest">Project Name</label>
        <input v-model="quick.project_name" class="w-full rounded-lg border border-premium-200 bg-premium-50 px-4 py-2.5 focus:bg-white focus:ring-2 focus:ring-premium-900/10 focus:border-premium-400 outline-none transition-all" placeholder="Enter title..." />
      </div>
      <div class="space-y-1">
        <label class="text-xs font-semibold text-premium-500 uppercase tracking-widest">Fandom</label>
        <select v-model="quick.fandom" class="w-full rounded-lg border border-premium-200 bg-premium-50 px-4 py-2.5 focus:bg-white focus:ring-2 focus:ring-premium-900/10 focus:border-premium-400 outline-none transition-all appearance-none cursor-pointer">
          <option v-for="f in fandoms" :key="f" :value="f">{{ f }}</option>
        </select>
      </div>
      <div class="space-y-1">
        <label class="text-xs font-semibold text-premium-500 uppercase tracking-widest">MC Name</label>
        <input v-model="quick.mc_name" class="w-full rounded-lg border border-premium-200 bg-premium-50 px-4 py-2.5 focus:bg-white focus:ring-2 focus:ring-premium-900/10 focus:border-premium-400 outline-none transition-all" placeholder="Character Name" />
      </div>
      <div class="space-y-1">
        <label class="text-xs font-semibold text-premium-500 uppercase tracking-widest">Progression Type</label>
        <select v-model="quick.power_progression_type" class="w-full rounded-lg border border-premium-200 bg-premium-50 px-4 py-2.5 focus:bg-white focus:ring-2 focus:ring-premium-900/10 focus:border-premium-400 outline-none transition-all appearance-none cursor-pointer">
          <option v-for="p in getOption('power_progression_type', ['Innovation','Bloodline','Hardwork','System'])" :key="p" :value="p">{{ p }}</option>
        </select>
      </div>
      <div class="space-y-2 pt-2">
        <div class="flex justify-between items-center"><label class="text-xs font-semibold text-premium-500 uppercase tracking-widest">Intelligence</label><span class="text-sm font-mono bg-premium-100 text-premium-600 px-2 py-0.5 rounded">{{ quick.iq }}</span></div>
        <input v-model.number="quick.iq" type="range" min="80" max="200" class="w-full accent-premium-900" />
      </div>
      <div class="space-y-2 pt-2">
        <div class="flex justify-between items-center"><label class="text-xs font-semibold text-premium-500 uppercase tracking-widest">Emotional EQ</label><span class="text-sm font-mono bg-premium-100 text-premium-600 px-2 py-0.5 rounded">{{ quick.eq }}</span></div>
        <input v-model.number="quick.eq" type="range" min="80" max="200" class="w-full accent-premium-900" />
      </div>
      <div class="space-y-1">
        <label class="text-xs font-semibold text-premium-500 uppercase tracking-widest">Starting Age</label>
        <input v-model.number="quick.age_at_start" type="number" class="w-full rounded-lg border border-premium-200 bg-premium-50 px-4 py-2.5 focus:bg-white focus:ring-2 focus:ring-premium-900/10 focus:border-premium-400 outline-none transition-all" />
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div class="space-y-1">
          <label class="text-xs font-semibold text-premium-500 uppercase tracking-widest">Volumes</label>
          <input v-model.number="quick.volume_count" type="number" class="w-full rounded-lg border border-premium-200 bg-premium-50 px-4 py-2.5 focus:bg-white" />
        </div>
        <div class="space-y-1">
          <label class="text-xs font-semibold text-premium-500 uppercase tracking-widest">Ch. per vol</label>
          <input v-model.number="quick.chapters_per_volume" type="number" class="w-full rounded-lg border border-premium-200 bg-premium-50 px-4 py-2.5 focus:bg-white" />
        </div>
      </div>
      <div class="md:col-span-2 pt-4">
        <button class="w-full py-3 rounded-lg bg-premium-900 text-white font-semibold shadow-md transition-all hover:bg-premium-800 hover:shadow-lg active:scale-[0.99]" @click="buildQuickConfig">Compile Configuration</button>
      </div>
    </div>

    <div v-else-if="step === 2 && mode === 'preset'" class="card p-6 max-w-sm mx-auto w-full">
      <h3 class="font-display font-semibold text-center text-lg mb-4 text-premium-900">Select Universe</h3>
      <div class="space-y-3">
        <button v-for="f in fandoms" :key="f" class="w-full px-5 py-4 border border-premium-200 rounded-xl bg-premium-50 hover:bg-white hover:border-premium-400 hover:shadow-sm transition-all font-medium text-premium-800 flex justify-between items-center group" @click="pickPreset(f)">
          {{ f }}
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-premium-300 group-hover:text-premium-600 transition-colors" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M12.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-2.293-2.293a1 1 0 010-1.414z" clip-rule="evenodd" /></svg>
        </button>
      </div>
    </div>

    <div v-else-if="step === 3" class="card p-12 text-center max-w-md mx-auto w-full flex flex-col items-center">
      <div class="w-16 h-16 relative flex items-center justify-center mb-6">
        <div class="absolute inset-0 border-4 border-premium-100 rounded-full"></div>
        <div class="absolute inset-0 border-4 border-premium-900 rounded-full border-t-transparent animate-spin"></div>
        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-premium-900" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" /></svg>
      </div>
        <h3 class="font-display font-semibold text-xl text-premium-900 mb-2">Analyzing Universe</h3>
        <p class="text-sm text-premium-500 font-medium max-w-[250px] leading-relaxed transition-all duration-300">
          {{ creationStatusMessage }}
        </p>
      </div>

      <div v-else-if="step === 4" class="space-y-3">
        <CharacterTable :characters="reviewCharacters" />
        <div class="card p-4 text-sm text-slate-700">
          Characters found: {{ extractionSummary.canon_characters || 0 }}
          <br />
          Chapters planned: {{ extractionSummary.chapters_planned || 0 }}
        </div>
        <button class="px-4 py-2 rounded bg-teal-700 text-white" @click="step = 5">Continue to settings</button>
      </div>
    <div v-else-if="step === 5" class="card p-4 space-y-3">
      <div class="grid md:grid-cols-3 gap-3">
        <select v-model.number="settings.words_per_chapter" class="rounded border px-3 py-2">
          <option :value="2000">2000</option>
          <option :value="3000">3000</option>
          <option :value="3500">3500</option>
          <option :value="5000">5000</option>
        </select>
        <label class="flex items-center gap-2 text-sm"><input v-model="settings.review_required" type="checkbox" /> Review required</label>
        <select v-model="settings.style" class="rounded border px-3 py-2">
          <option v-for="s in getOption('style', ['Balanced'])" :key="s" :value="s">{{ s }}</option>
        </select>
      </div>
      <button class="px-4 py-2 rounded bg-orange-500 text-white" @click="launch">Launch Project</button>
    </div>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api/client'
import CharacterTable from '@/components/project/CharacterTable.vue'
import FileUploader from '@/components/project/FileUploader.vue'

const router = useRouter()
const step = ref(1)
const mode = ref('upload')
const templateOptions = ref({})
const fandoms = ref(['Naruto', 'Marvel', 'Harry_Potter'])
const config = ref(null)
const projectId = ref('')
const extractionSummary = ref({})
const reviewCharacters = ref({ canon: {}, original: {} })
const creationStatusMessage = ref('Initializing...')

const quick = reactive({
  project_name: 'My Story',
  fandom: 'Naruto',
  mc_name: 'MC',
  iq: 130,
  eq: 120,
  age_at_start: 12,
  power_progression_type: 'Hardwork',
  volume_count: 2,
  chapters_per_volume: 10,
})

const settings = reactive({ words_per_chapter: 3000, review_required: true, style: 'Balanced' })

onMounted(loadTemplate)

function normalizeFandomName(value) {
  return String(value || '')
    .split('_')
    .filter(Boolean)
    .map(part => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    .join('_')
}

async function loadTemplate() {
  try {
    const { data } = await api.get('/projects/templates/download', { responseType: 'json' })
    templateOptions.value = data._options || {}
  } catch {
    templateOptions.value = {}
  }
}

function getOption(key, fallback) {
  return templateOptions.value[key] || fallback
}

function onUploaded(clean, options) {
  config.value = clean
  templateOptions.value = { ...templateOptions.value, ...options }
  createProject()
}

function buildQuickConfig() {
  const volumes = Array.from({ length: quick.volume_count }).map((_, i) => ({
    name: `Volume ${i + 1}`,
    chapters: quick.chapters_per_volume,
    arc_goals: [],
  }))
  config.value = {
    project_name: quick.project_name,
    fandom: quick.fandom,
    main_character: {
      name: quick.mc_name,
      iq: quick.iq,
      eq: quick.eq,
      age_at_start: quick.age_at_start,
      power_progression_type: quick.power_progression_type,
    },
    structure: { type: 'volume_based', volumes },
    generation_preferences: { ...settings },
  }
  createProject()
}

async function loadFandoms() {
  try {
    const { data } = await api.get('/projects/templates/fandoms')
    const normalized = Array.from(new Set((Array.isArray(data) ? data : []).map(normalizeFandomName)))
    fandoms.value = normalized.length ? normalized : ['Naruto', 'Marvel', 'Harry_Potter']
  } catch {
    fandoms.value = ['Naruto', 'Marvel', 'Harry_Potter']
  }

  if (!fandoms.value.includes(quick.fandom)) {
    quick.fandom = fandoms.value[0] || 'Naruto'
  }
}

function pickPreset(fandom) {
  quick.fandom = fandom
  mode.value = 'quick'
}

async function createProject() {
  step.value = 3
  creationStatusMessage.value = 'Initializing...'
  
  try {
    const fd = new FormData()
    fd.append('config', JSON.stringify(config.value))
    
    // Start background creation
    const { data: initialData } = await api.post('/projects/', fd)
    const jobId = initialData.job_id
    
    // Poll for status
    while (true) {
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      const { data: statusData } = await api.get(`/projects/status/${jobId}`)
      creationStatusMessage.value = statusData.message || 'Processing...'
      
      if (statusData.status === 'completed') {
        projectId.value = statusData.result.project_id
        extractionSummary.value = statusData.result.extraction_summary || {}
        reviewCharacters.value = (await api.get(`/characters/${projectId.value}`)).data || { canon: {}, original: {} }
        step.value = 4
        break
      } else if (statusData.status === 'error') {
        throw new Error(statusData.error || 'Extraction failed on backend')
      }
    }
  } catch (e) {
    window.dispatchEvent(new CustomEvent('api:error', { detail: e.message || 'Project creation failed' }))
    step.value = 2
  }
}

function launch() {
  router.push(`/project/${projectId.value}/writer`)
}
</script>

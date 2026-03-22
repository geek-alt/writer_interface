<template>
  <div class="space-y-4">
    <div
      class="border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors"
      :class="dragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-blue-400'"
      @dragover.prevent="dragging = true"
      @dragleave="dragging = false"
      @drop.prevent="handleDrop"
      @click="fileInput.click()"
    >
      <div class="text-4xl mb-2">[ ]</div>
      <p class="font-medium text-gray-700">Drop your config JSON here</p>
      <p class="text-sm text-gray-400 mt-1">or click to browse</p>
      <p v-if="fileName" class="mt-3 text-blue-600 font-medium">{{ fileName }}</p>
    </div>

    <input ref="fileInput" type="file" accept=".json" class="hidden" @change="handleInput" />

    <ul v-if="errors.length" class="bg-red-50 border border-red-200 rounded-lg p-3 space-y-1">
      <li v-for="e in errors" :key="e" class="text-sm text-red-700">Warning: {{ e }}</li>
    </ul>

    <div v-if="parsed && !errors.length" class="bg-green-50 border border-green-200 rounded-lg p-3">
      <p class="text-sm font-medium text-green-800">Valid configuration</p>
      <p class="text-xs text-green-700 mt-1">
        Project: <strong>{{ parsed.project_name }}</strong> | Fandom: <strong>{{ parsed.fandom }}</strong> |
        Volumes: <strong>{{ parsed.structure?.volumes?.length || 0 }}</strong>
      </p>
    </div>

    <div class="flex gap-3">
      <a href="/api/projects/templates/download" class="text-sm text-blue-600 underline hover:no-underline" download>
        Download blank template
      </a>
      <span class="text-gray-300">|</span>
      <a
        v-for="fandom in ['naruto', 'marvel', 'harry_potter']"
        :key="fandom"
        href="#"
        class="text-sm text-gray-500 hover:text-blue-600"
        @click.prevent="loadFandomTemplate(fandom)"
      >
        {{ fandom.replace('_', ' ') }} preset
      </a>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import api from '@/api/client'

const emit = defineEmits(['upload'])
const fileInput = ref(null)
const dragging = ref(false)
const fileName = ref('')
const parsed = ref(null)
const errors = ref([])

const REQUIRED_KEYS = ['project_name', 'fandom', 'main_character', 'structure']

function parseAndValidate(text) {
  errors.value = []
  parsed.value = null
  try {
    const data = JSON.parse(text)
    const clean = Object.fromEntries(Object.entries(data).filter(([k]) => !k.startsWith('_')))
    for (const key of REQUIRED_KEYS) {
      if (!clean[key]) errors.value.push(`Missing required field: ${key}`)
    }
    if (!clean.main_character?.name) errors.value.push('main_character.name is required')
    if (!clean.structure?.volumes?.length) errors.value.push('structure.volumes must have at least one entry')
    if (!errors.value.length) {
      parsed.value = clean
      emit('upload', clean, data._options || {})
    }
  } catch {
    errors.value = ['File is not valid JSON. Please check the format.']
  }
}

async function handleDrop(e) {
  dragging.value = false
  const file = e.dataTransfer.files[0]
  if (!file) return
  fileName.value = file.name
  parseAndValidate(await file.text())
}

function handleInput(e) {
  const file = e.target.files[0]
  if (!file) return
  fileName.value = file.name
  const reader = new FileReader()
  reader.onload = ev => parseAndValidate(ev.target.result)
  reader.readAsText(file)
}

async function loadFandomTemplate(fandom) {
  try {
    await api.get(`/projects/templates/fandoms/${fandom}`)
    const draft = {
      project_name: `My ${fandom.replace('_', ' ')} Story`,
      fandom: fandom.charAt(0).toUpperCase() + fandom.slice(1).replace('_', ' '),
      main_character: { name: '', iq: 130, eq: 120, age_at_start: 12, power_progression_type: 'Hardwork' },
      structure: { type: 'volume_based', volumes: [{ name: 'Volume 1', chapters: 10, arc_goals: [] }] },
      generation_preferences: { words_per_chapter: 3000, review_required: true },
    }
    fileName.value = `${fandom}_preset`
    parsed.value = draft
    errors.value = []
    emit('upload', draft, {})
  } catch {
    errors.value = [`Could not load ${fandom} preset`]
  }
}
</script>

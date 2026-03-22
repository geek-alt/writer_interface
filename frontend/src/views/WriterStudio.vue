<template>
  <div class="space-y-3">
    <div v-if="lmStatus && !lmStatus.connected" class="bg-red-50 border border-red-300 rounded-xl p-3 text-sm text-red-700">
      LM Studio disconnected. Open LM Studio and start server on localhost:1234.
    </div>

    <div class="grid grid-cols-1 xl:grid-cols-12 gap-3 h-[78vh]">
      <aside class="xl:col-span-3 h-full">
        <OutlineTree :items="outlineItems" :active-chapter="selectedChapter" @select="loadChapter" @open-generate="showGenerate = true" />
      </aside>

      <section class="xl:col-span-6 h-full card overflow-hidden flex flex-col">
        <div class="px-4 py-3 border-b border-premium-200/60 bg-white/80 backdrop-blur-md">
          <label for="chapterTitle" class="sr-only">Chapter Title</label>
          <input id="chapterTitle" v-model="chapterTitle" class="w-full rounded-md border-0 bg-transparent px-2 py-1 font-display text-xl font-medium text-premium-900 focus:ring-2 focus:ring-premium-900/10 placeholder:text-premium-300 outline-none transition-all" placeholder="Enter chapter title..." />
        </div>
        <ChapterEditor v-model="chapterText" :quality-score="qualityScore" @save="saveChapter" />
      </section>

              <aside class="xl:col-span-3 space-y-4 h-full overflow-y-auto pr-2">
          <GenerationProgress :status="generation.status" :progress="generation.progress" :preview="generation.preview" :log="generation.log" />
          
          <div class="card p-5 bg-white/50 backdrop-blur-sm border-premium-100/50 shadow-sm">
            <h3 class="font-display font-semibold text-lg text-premium-900 mb-4 flex items-center gap-2">
              <span class="bg-premium-100 p-1.5 rounded-lg text-premium-600">📊</span> Live Stats
            </h3>
            <div class="space-y-2 mb-6">
              <div class="flex justify-between items-center text-sm">
                <span class="text-premium-500">Words</span>
                <span class="font-medium text-premium-900">{{ wordCount }}</span>
              </div>
              <div class="flex justify-between items-center text-sm">
                <span class="text-premium-500">Quality</span>
                <span class="font-medium" :class="qualityScore > 80 ? 'text-green-600' : 'text-amber-600'">{{ qualityScore }}/100</span>
              </div>
              <div class="flex justify-between items-center text-sm">
                <span class="text-premium-500">Consistency</span>
                <span class="font-medium text-green-600">✓ Passes</span>
              </div>
            </div>

            <h3 class="font-display font-semibold text-premium-900 mt-6 mb-3 text-sm flex items-center gap-2 border-t border-premium-100 pt-4">
               Character Appearances
            </h3>
            <ul class="text-sm text-premium-600 space-y-2 mb-6">
              <li v-for="n in currentOutline.characters_involved || []" :key="n" class="flex items-center gap-2">
                <div class="h-1.5 w-1.5 rounded-full bg-accent-500"></div> {{ n }}
              </li>
              <li v-if="!(currentOutline.characters_involved || []).length" class="text-premium-400 italic">No mapped characters.</li>
            </ul>

            <h3 class="font-display font-semibold text-premium-900 mt-6 mb-3 text-sm flex items-center gap-2 border-t border-premium-100 pt-4">
               🔔 Alerts
            </h3>
            <ul class="text-sm space-y-2 mb-4">
              <li v-for="i in issues" :key="i" class="text-amber-700 bg-amber-50 p-2 rounded-lg border border-amber-200/50 leading-snug">
                ⚠️ {{ i }}
              </li>
              <li v-if="!issues.length" class="text-premium-500 bg-premium-50 p-2 rounded-lg border border-premium-100">No issues reported.</li>
            </ul>

            <button class="w-full mt-2 py-2 text-sm font-medium text-premium-600 bg-white border border-premium-200 rounded-lg hover:bg-premium-50 transition-colors">
              View Full Report
            </button>
          </div>

          <div v-if="chapterStatus === 'pending_review'" class="card p-5 bg-gradient-to-br from-white to-premium-50 border-premium-200 shadow-elevated">
            <h3 class="font-display font-semibold text-premium-900 mb-3">Review Action Required</h3>
            <p class="text-xs text-premium-500 mb-4">You have unsaved generated changes. Please approve or reject to continue.</p>
            <div class="flex gap-2">
              <button class="flex-1 px-3 py-2 rounded-lg bg-green-600 text-white font-medium text-sm hover:bg-green-700 transition-colors shadow-sm" @click="approve">Approve</button>
              <button class="flex-1 px-3 py-2 rounded-lg bg-white border border-red-200 text-red-600 font-medium text-sm hover:bg-red-50 transition-colors" @click="reject">Reject</button>
            </div>
          </div>
        </aside>
    </div>

    <div v-if="showGenerate" class="fixed inset-0 bg-premium-900/40 backdrop-blur-sm grid place-items-center z-40 transition-all">
      <div class="card p-6 w-full max-w-md space-y-5 shadow-elevated">
        <h3 class="font-display font-semibold text-xl text-premium-900">Generate Chapters</h3>
        <div class="grid grid-cols-2 gap-4">
          <div class="space-y-1.5">
            <label for="generateStart" class="text-xs font-semibold text-premium-500 uppercase tracking-widest">Start Chapter</label>
            <input id="generateStart" v-model.number="range.start" type="number" min="1" class="w-full rounded-lg border border-premium-200 bg-premium-50 px-4 py-2.5 focus:bg-white focus:ring-2 focus:ring-premium-900/10 focus:border-premium-400 outline-none transition-all" placeholder="1" />
          </div>
          <div class="space-y-1.5">
            <label for="generateEnd" class="text-xs font-semibold text-premium-500 uppercase tracking-widest">End Chapter</label>
            <input id="generateEnd" v-model.number="range.end" type="number" min="1" class="w-full rounded-lg border border-premium-200 bg-premium-50 px-4 py-2.5 focus:bg-white focus:ring-2 focus:ring-premium-900/10 focus:border-premium-400 outline-none transition-all" placeholder="1" />
          </div>
        </div>
        <label class="text-sm font-medium text-premium-700 flex items-center gap-3 p-3 bg-premium-50 rounded-lg border border-premium-100 cursor-pointer hover:bg-premium-100/50 transition-colors">
          <input v-model="range.wait" type="checkbox" class="w-4 h-4 rounded border-premium-300 text-premium-900 focus:ring-premium-900/20" /> 
          Wait for approval after each chapter
        </label>
        <div class="flex justify-end gap-3 pt-2">
          <button class="px-5 py-2.5 rounded-lg border border-premium-200 text-premium-600 font-medium hover:bg-premium-50 hover:text-premium-900 transition-colors" @click="showGenerate = false">Cancel</button>
          <button class="px-5 py-2.5 rounded-lg bg-premium-900 text-white font-medium shadow-md transition-all hover:bg-premium-800 hover:shadow-lg active:scale-[0.98]" @click="startBatch">Start Generation</button>
        </div>
      </div>
    </div>

    <div v-if="generation.pendingApproval" class="fixed inset-0 bg-black/60 z-50 overflow-auto">
      <div class="max-w-4xl mx-auto my-8 card p-5 space-y-4">
        <h3 class="font-semibold text-lg">Review Chapter {{ generation.pendingApproval.chapter }}</h3>
        <pre class="bg-slate-900 text-slate-100 rounded p-3 text-sm whitespace-pre-wrap max-h-80 overflow-y-auto">{{ chapterText }}</pre>
        <ul class="text-sm space-y-1">
          <li v-for="i in issues" :key="i">- {{ i }}</li>
        </ul>
        <textarea v-model="feedback" class="w-full rounded border px-3 py-2" rows="4" placeholder="Feedback for regeneration"></textarea>
        <div class="flex justify-end gap-2">
          <button class="px-3 py-2 rounded bg-green-600 text-white" @click="approveAndContinue">Approve and Continue</button>
          <button class="px-3 py-2 rounded bg-orange-600 text-white" @click="regenWithFeedback">Regenerate with Feedback</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import OutlineTree from '@/components/writer/OutlineTree.vue'
import ChapterEditor from '@/components/writer/ChapterEditor.vue'
import GenerationProgress from '@/components/writer/GenerationProgress.vue'
import api from '@/api/client'
import { useGenerationStore } from '@/stores/generation'
import { useProjectStore } from '@/stores/project'

const route = useRoute()
const projectId = route.params.id
const store = useProjectStore()
const generation = useGenerationStore()

const selectedChapter = ref(1)
const chapterText = ref('')
const chapterTitle = ref('')
const chapterStatus = ref('pending_review')
const qualityScore = ref(0)
const wordCount = computed(() => chapterText.value ? chapterText.value.replace(/<[^>]*>?/gm, '').split(/\s+/).filter(w => w.length > 0).length : 0)
const issues = ref([])
const feedback = ref('')
const lmStatus = ref(null)
const showGenerate = ref(false)

const range = ref({ start: 1, end: 1, wait: true })

watch(() => generation.preview, (newPreview) => {
  if (generation.currentChapter === selectedChapter.value && newPreview) {
    chapterText.value = newPreview
  }
})

watch(() => generation.status, async (newStatus) => {
  if (newStatus === 'complete' || newStatus === 'waiting_approval') {
    await store.refreshChapters()
    if (generation.currentChapter === selectedChapter.value) {
      await loadChapter(selectedChapter.value)
    }
  } else if (newStatus === 'generating' && generation.currentChapter) {
    if (generation.currentChapter !== selectedChapter.value) {
      await loadChapter(generation.currentChapter)
    }
  }
})


onMounted(async () => {
  await store.selectProject(projectId)
  await recheckHealth()
  if (store.chapters.length) {
    const first = store.chapters[0].chapter_number
    range.value.start = first
    range.value.end = first
    await loadChapter(first)
  }
})

const outlineItems = computed(() => {
  const map = new Map(store.chapters.map(ch => [ch.chapter_number, ch]))
  return (store.outline?.chapters || []).map(ch => ({
    ...ch,
    chapter_number: ch.global_number,
    status: map.get(ch.global_number)?.status || 'pending',
  }))
})

const currentOutline = computed(() =>
  (store.outline?.chapters || []).find(ch => ch.global_number === selectedChapter.value) || {}
)

async function recheckHealth() {
  try {
    const { data } = await api.get('/health')
    lmStatus.value = data.lm_studio
  } catch {
    lmStatus.value = { connected: false }
  }
}

async function loadChapter(num) {
  selectedChapter.value = num
  const { data } = await api.get(`/chapters/${projectId}/${num}`)
  chapterText.value = data.content || ''
  chapterTitle.value = data.title || `Chapter ${num}`
  chapterStatus.value = data.status || 'pending_review'
  qualityScore.value = data.quality_score || 0
  issues.value = data.consistency_issues || []
}

async function saveChapter(content) {
  await api.patch(`/chapters/${projectId}/${selectedChapter.value}`, { content })
  await store.refreshChapters()
}

async function approve() {
  await store.approveChapter(selectedChapter.value)
  chapterStatus.value = 'approved'
}

async function reject() {
  const reason = prompt('Feedback for regeneration (optional):') || ''
  await store.rejectChapter(selectedChapter.value, reason)
  chapterStatus.value = 'rejected'
}

function startBatch() {
  generation.startGeneration(projectId, range.value.start, range.value.end, range.value.wait)
  showGenerate.value = false
}

function approveAndContinue() {
  generation.continueAfterApproval()
}

function regenWithFeedback() {
  generation.requestRegeneration(feedback.value)
  feedback.value = ''
}
</script>

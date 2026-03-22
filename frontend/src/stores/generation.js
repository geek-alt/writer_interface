import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useWebSocketStore } from './websocket'

export const useGenerationStore = defineStore('generation', () => {
  const isGenerating = ref(false)
  const currentChapter = ref(null)
  const progress = ref(0)
  const status = ref('idle')
  const preview = ref('')
  const errorMessage = ref('')
  const pendingApproval = ref(null)
  const log = ref([])

  function addLog(msg, type = 'info') {
    log.value.unshift({ ts: new Date().toLocaleTimeString(), msg, type })
    if (log.value.length > 200) log.value.pop()
  }

  function startGeneration(projectId, start, end, waitApproval) {
    const ws = useWebSocketStore()
    ws.connect(projectId)
    isGenerating.value = true
    progress.value = 0
    status.value = 'generating'
    log.value = []

    const unsub = ws.onMessage(data => {
      switch (data.type) {
        case 'chapter_start':
          currentChapter.value = data.chapter
          status.value = 'generating'
          progress.value = 5
          addLog(`Starting Chapter ${data.chapter}...`)
          break
        case 'progress':
          if (data.progress) progress.value = data.progress
          if (data.preview) preview.value = data.preview
          break
        case 'chapter_complete':
          progress.value = 100
          status.value = 'complete'
          addLog(
            `Chapter ${data.chapter} done - ${data.word_count} words, quality ${data.quality_score}/100`,
            'success'
          )
          ;(data.milestones || []).forEach(m =>
            addLog(`Milestone: ${m.character} - ${m.milestone}`, 'milestone')
          )
          break
        case 'waiting_approval':
          status.value = 'waiting_approval'
          pendingApproval.value = { chapter: data.chapter }
          addLog(`Review required for Chapter ${data.chapter}`, 'warning')
          break
        case 'chapter_error':
          addLog(`Chapter ${data.chapter} failed: ${data.error}`, 'error')
          break
        case 'lm_studio_error':
          status.value = 'lm_studio_error'
          errorMessage.value = data.error
          isGenerating.value = false
          unsub()
          addLog(`LM Studio error: ${data.error}`, 'error')
          break
        case 'batch_complete':
          isGenerating.value = false
          status.value = 'idle'
          pendingApproval.value = null
          unsub()
          addLog('Batch complete!', 'success')
          break
        case 'fatal_error':
          isGenerating.value = false
          status.value = 'error'
          errorMessage.value = data.error
          unsub()
          break
      }
    })

    ws.send({
      action: 'generate_chapters',
      start_chapter: start,
      end_chapter: end,
      wait_for_approval: waitApproval,
    })
  }

  function continueAfterApproval() {
    useWebSocketStore().send({ action: 'continue' })
    pendingApproval.value = null
    status.value = 'generating'
  }

  function requestRegeneration(feedback) {
    useWebSocketStore().send({ action: 'regenerate', feedback })
    pendingApproval.value = null
    status.value = 'generating'
    addLog(`Regenerating with feedback: "${feedback.slice(0, 60)}..."`, 'info')
  }

  return {
    isGenerating,
    currentChapter,
    progress,
    status,
    preview,
    errorMessage,
    pendingApproval,
    log,
    startGeneration,
    continueAfterApproval,
    requestRegeneration,
  }
})

import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import api from '@/api/client'

export const useProjectStore = defineStore('project', () => {
  const projects = ref([])
  const currentProject = ref(null)
  const chapters = ref([])
  const characters = ref({ mc: {}, canon: [], original: [] })
  const worldData = ref({})
  const outline = ref({})

  const approvedCount = computed(() => chapters.value.filter(c => c.status === 'approved').length)
  const pendingCount = computed(() => chapters.value.filter(c => c.status === 'pending_review').length)

  async function loadProjects() {
    const { data } = await api.get('/projects/')
    if (Array.isArray(data)) {
      projects.value = data
      return
    }
    projects.value = []
    window.dispatchEvent(
      new CustomEvent('api:error', {
        detail: 'Projects API returned unexpected data. Please refresh or check backend logs.',
      })
    )
  }

  async function selectProject(projectId) {
    const { data: project } = await api.get(`/projects/${projectId}`)
    currentProject.value = project
    const { data: chapterData } = await api.get(`/chapters/${projectId}?limit=200`)
    chapters.value = Array.isArray(chapterData?.chapters) ? chapterData.chapters : []
    const { data: charData } = await api.get(`/characters/${projectId}`)
    characters.value = charData && typeof charData === 'object' ? charData : { mc: {}, canon: [], original: [] }
    const { data: world } = await api.get(`/world/${projectId}`)
    worldData.value = world && typeof world === 'object' ? world : {}
    const { data: ol } = await api.get(`/world/${projectId}/outline`)
    outline.value = ol && typeof ol === 'object' ? ol : {}
  }

  async function refreshChapters() {
    if (!currentProject.value) return
    const { data } = await api.get(`/chapters/${currentProject.value.id}?limit=200`)
    chapters.value = Array.isArray(data?.chapters) ? data.chapters : []
  }

  async function approveChapter(chapterNum) {
    await api.post(`/chapters/${currentProject.value.id}/${chapterNum}/approve`)
    const ch = chapters.value.find(c => c.chapter_number === chapterNum)
    if (ch) ch.status = 'approved'
  }

  async function rejectChapter(chapterNum, feedback) {
    await api.post(`/chapters/${currentProject.value.id}/${chapterNum}/reject`, {
      approved: false,
      feedback,
    })
    const ch = chapters.value.find(c => c.chapter_number === chapterNum)
    if (ch) ch.status = 'rejected'
  }

  return {
    projects,
    currentProject,
    chapters,
    characters,
    worldData,
    outline,
    approvedCount,
    pendingCount,
    loadProjects,
    selectProject,
    refreshChapters,
    approveChapter,
    rejectChapter,
  }
})

<template>
  <div class="flex flex-col h-full bg-[#FAFAFA]">
    <div v-if="editor" class="flex gap-2 p-3 border-b border-premium-200/60 bg-white/80 backdrop-blur-md flex-wrap items-center">
      <div class="flex items-center bg-premium-50 rounded-lg p-1 border border-premium-100">
        <button
          @click="editor.chain().focus().toggleBold().run()"
          :class="['w-8 h-8 rounded-md flex items-center justify-center text-sm font-semibold transition-colors', editor.isActive('bold') ? 'bg-white shadow-sm text-premium-900 border border-premium-200/50' : 'text-premium-500 hover:text-premium-800 hover:bg-premium-100']"
        >
          B
        </button>
        <button
          @click="editor.chain().focus().toggleItalic().run()"
          :class="['w-8 h-8 rounded-md flex items-center justify-center text-sm italic py-1 transition-colors', editor.isActive('italic') ? 'bg-white shadow-sm text-premium-900 border border-premium-200/50' : 'text-premium-500 hover:text-premium-800 hover:bg-premium-100']"
        >
          I
        </button>
      </div>
      <div class="flex-1"></div>
      <div class="flex items-center gap-3">
        <span class="text-xs font-medium text-premium-400 uppercase tracking-widest">{{ wordCount }} words</span>
        <button @click="saveManually" class="px-4 py-1.5 bg-premium-900 text-white text-xs font-medium rounded-md shadow-sm transition-all hover:bg-premium-800 active:scale-95 flex items-center gap-1.5">
          <svg v-if="saving" class="animate-spin h-3.5 w-3.5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" /></svg>
          {{ saved ? 'Saved' : 'Save' }}
        </button>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto px-8 md:px-16 py-12 scroll-smooth">
      <EditorContent :editor="editor" class="prose prose-slate max-w-[65ch] mx-auto min-h-full font-display text-[1.1rem] leading-relaxed text-premium-800" />
    </div>

    <div class="flex items-center gap-6 px-6 py-3 border-t border-premium-200/60 bg-white/80 backdrop-blur-md text-[0.7rem] font-medium uppercase tracking-widest text-premium-500">
      <div class="flex items-center gap-2">
        <span class="w-1.5 h-1.5 rounded-full bg-accent-500"></span>
        Words: {{ wordCount }}
      </div>
      <div class="flex items-center gap-2">
        <span class="w-1.5 h-1.5 rounded-full" :class="props.qualityScore > 80 ? 'bg-green-500' : 'bg-amber-400'"></span>
        Quality: {{ props.qualityScore }}/100
      </div>
      <div class="flex-1"></div>
      <div class="text-xs transition-opacity duration-300" :class="saving ? 'opacity-100 text-premium-600' : saved ? 'opacity-100 text-emerald-600' : 'opacity-0'">
        {{ saving ? 'Saving to disk...' : 'All changes saved.' }}
      </div>
    </div>
  </div>
</template>

<script setup>
import CharacterCount from '@tiptap/extension-character-count'
import Placeholder from '@tiptap/extension-placeholder'
import StarterKit from '@tiptap/starter-kit'
import { EditorContent, useEditor } from '@tiptap/vue-3'
import { computed, onBeforeUnmount, ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  qualityScore: { type: Number, default: 0 },
})
const emit = defineEmits(['update:modelValue', 'save'])

const saving = ref(false)
const saved = ref(false)
let saveTimer = null

const editor = useEditor({
  extensions: [
    StarterKit,
    Placeholder.configure({ placeholder: 'The blank page awaits your story...' }),
    CharacterCount,
  ],
  content: props.modelValue,
  onUpdate({ editor: ed }) {
    const plain = ed.getText({ blockSeparator: '\n\n' })
    emit('update:modelValue', plain)
    saved.value = false
    clearTimeout(saveTimer)
    saveTimer = setTimeout(autoSave, 2000)
  },
})

watch(
  () => props.modelValue,
  val => {
    if (editor.value && editor.value.getText({ blockSeparator: '\n\n' }) !== val) {
      editor.value.commands.setContent(val || '', false)
    }
  }
)

const wordCount = computed(() => {
  if (!editor.value) return 0
  return editor.value.getText().split(/\s+/).filter(Boolean).length
})

async function autoSave() {
  if (!editor.value) return
  saving.value = true
  emit('save', editor.value.getText({ blockSeparator: '\n\n' }))
  await new Promise(r => setTimeout(r, 600))
  saving.value = false
  saved.value = true
}

function saveManually() {
  clearTimeout(saveTimer)
  autoSave()
}

onBeforeUnmount(() => {
  clearTimeout(saveTimer)
  editor.value?.destroy()
})
</script>

<style>
.ProseMirror p {
  margin-bottom: 1.5em;
  line-height: 1.85;
  text-indent: 1.5em;
}
.ProseMirror p:first-child {
  text-indent: 0;
}
.ProseMirror p.is-editor-empty:first-child::before {
  content: attr(data-placeholder);
  color: #94a3b8;
  pointer-events: none;
  float: left;
  height: 0;
  font-family: 'Inter', sans-serif;
  font-style: italic;
  font-size: 1rem;
}
.ProseMirror:focus {
  outline: none;
}
</style>

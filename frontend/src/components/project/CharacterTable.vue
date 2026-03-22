<template>
  <div class="card p-4 overflow-auto">
    <h3 class="font-semibold mb-3">Character Snapshot</h3>
    <table class="w-full text-sm">
      <thead>
        <tr class="text-left text-slate-500 border-b">
          <th class="py-2">Name</th>
          <th class="py-2">Rel.</th>
          <th class="py-2">Romance</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="ch in rows" :key="ch.name" class="border-b border-slate-100">
          <td class="py-2">{{ ch.name }}</td>
          <td class="py-2">
            <input v-model.number="ch.relationship_to_mc" type="number" min="-100" max="100" class="w-20 rounded border px-2 py-1" />
          </td>
          <td class="py-2">{{ ch.romance_eligible ? ch.romance_progress || 0 : '-' }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  characters: { type: Object, default: () => ({ canon: {}, original: {} }) },
})

const rows = computed(() => {
  const canon = Object.entries(props.characters?.canon || {}).map(([name, d]) => ({ name, ...d }))
  const original = Object.entries(props.characters?.original || {}).map(([name, d]) => ({ name, ...d }))
  return [...canon, ...original]
})
</script>

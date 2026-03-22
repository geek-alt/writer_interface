<template>
  <div class="min-h-screen bg-gray-50 text-gray-900">
    <AppHeader />
    <main class="max-w-screen-xl mx-auto px-4 py-6">
      <RouterView />
    </main>
    <Toast />
  </div>
</template>

<script setup>
import AppHeader from '@/components/common/AppHeader.vue'
import Toast from '@/components/common/Toast.vue'
</script>

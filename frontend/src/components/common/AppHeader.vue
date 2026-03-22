<template>
  <header class="sticky top-0 z-30 border-b border-premium-200/60 bg-white/70 backdrop-blur-md">
    <div class="max-w-screen-xl mx-auto px-6 py-4 flex items-center justify-between">
      <RouterLink to="/" class="flex items-center gap-3 transition-opacity hover:opacity-80">
        <div class="h-10 w-10 text-white rounded-lg bg-premium-900 grid place-items-center font-display font-bold shadow-sm">
          <span class="tracing-tighter text-lg leading-none">N</span>
        </div>
        <div class="flex flex-col justify-center">
          <p class="font-display font-semibold text-lg leading-tight tracking-tight text-premium-900 mt-0.5">NovelForge</p>
          <p class="text-[0.65rem] font-medium tracking-widest text-premium-400 uppercase">Studio</p>
        </div>
      </RouterLink>
      <nav class="flex items-center gap-4 text-sm font-medium">
        <RouterLink to="/" class="px-3 py-2 rounded-md text-premium-600 transition-colors hover:text-premium-900 hover:bg-premium-100/50">Dashboard</RouterLink>
        <RouterLink to="/project/new" class="px-4 py-2 rounded-md bg-premium-900 text-white shadow-sm transition-all hover:bg-premium-800 hover:shadow-md active:scale-95">
          New Project
        </RouterLink>
      </nav>
    </div>
  </header>
</template>

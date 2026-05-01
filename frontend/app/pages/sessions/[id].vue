<script setup lang="ts">
const route = useRoute()
const sid = route.params.id as string
const api = useApi()

const { data: session } = await useAsyncData(
  `session:${sid}:shell`,
  () => api.getSession(sid),
)

// Re-fetch on every navigation within the wizard so the sidebar's "done" badges
// stay accurate after the user advances a step.
watch(() => route.path, async () => {
  const fresh = await api.getSession(sid)
  session.value = fresh
})

const steps = computed(() => {
  const status = session.value?.status ?? ''
  const at = (...s: string[]) => s.includes(status)
  return [
    { key: 'extract', label: 'Extract source',
      done: !at('created') && !!session.value },
    { key: 'analyze', label: 'Analyze',
      done: at('analyzed', 'source_profile_confirmed', 'destination_profile_confirmed', 'decisions_answered', 'prompt_built', 'pipeline_submitted', 'pipeline_completed', 'pipeline_failed') },
    { key: 'source-profile', label: 'Source profile',
      done: at('source_profile_confirmed', 'destination_profile_confirmed', 'decisions_answered', 'prompt_built', 'pipeline_submitted', 'pipeline_completed', 'pipeline_failed') },
    { key: 'destination-profile', label: 'Destination profile',
      done: at('destination_profile_confirmed', 'decisions_answered', 'prompt_built', 'pipeline_submitted', 'pipeline_completed', 'pipeline_failed') },
    { key: 'decisions', label: 'Design decisions',
      done: at('decisions_answered', 'prompt_built', 'pipeline_submitted', 'pipeline_completed', 'pipeline_failed') },
    { key: 'prompt', label: 'Assembled prompt',
      done: at('prompt_built', 'pipeline_submitted', 'pipeline_completed', 'pipeline_failed') },
    { key: 'pipeline', label: 'AI Pipeline',
      done: at('pipeline_completed') },
  ]
})

function isActive(key: string) {
  const path = route.path.replace(/\/$/, '')
  return path === `/sessions/${sid}/${key}` || (key === '' && path === `/sessions/${sid}`)
}
</script>

<template>
  <div class="lg:flex min-h-screen">
    <aside
      class="lg:w-72 lg:shrink-0 lg:border-r border-default p-4 space-y-4 bg-elevated/50"
    >
      <div class="space-y-2">
        <NuxtLink to="/" class="text-xs text-neutral-500 hover:underline">← All sessions</NuxtLink>
        <p class="text-[10px] uppercase tracking-wide text-neutral-500 mt-2">Session</p>
        <h2 class="text-sm font-mono break-all">{{ session?.id ?? '—' }}</h2>
        <UBadge
          v-if="session"
          size="xs"
          variant="subtle"
          :color="session.status.includes('failed') ? 'error' : 'neutral'"
        >
          {{ session.status }}
        </UBadge>
      </div>

      <nav>
        <p class="text-[10px] uppercase tracking-wide text-neutral-500 mb-1">Wizard</p>
        <ol class="space-y-0.5">
          <li v-for="step in steps" :key="step.key">
            <NuxtLink
              :to="`/sessions/${sid}/${step.key}`"
              class="flex items-center gap-2 py-1.5 px-2 rounded text-sm transition-colors hover:bg-elevated"
              :class="isActive(step.key) ? 'bg-elevated font-medium' : ''"
            >
              <UIcon
                :name="step.done ? 'i-lucide-circle-check' : 'i-lucide-circle'"
                :class="step.done ? 'text-green-500' : 'text-neutral-400'"
                class="shrink-0"
              />
              <span class="truncate">{{ step.label }}</span>
            </NuxtLink>
          </li>
        </ol>
      </nav>
    </aside>

    <main class="flex-1 min-w-0">
      <NuxtPage />
    </main>
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const sid = route.params.id as string
const api = useApi()
const { data: session } = await useAsyncData(`session:${sid}`, () => api.getSession(sid))

const steps = computed(() => [
  { key: 'extract', label: 'Extract source', done: session.value && session.value.status !== 'created' },
  { key: 'analyze', label: 'Analyze (Phase 1: fake)', done: ['analyzed','source_profile_confirmed','destination_profile_confirmed','decisions_answered','prompt_built','pipeline_submitted','pipeline_completed','pipeline_failed'].includes(session.value?.status ?? '') },
  { key: 'source-profile', label: 'Confirm source profile', done: ['source_profile_confirmed','destination_profile_confirmed','decisions_answered','prompt_built','pipeline_submitted','pipeline_completed','pipeline_failed'].includes(session.value?.status ?? '') },
  { key: 'destination-profile', label: 'Confirm destination profile', done: ['destination_profile_confirmed','decisions_answered','prompt_built','pipeline_submitted','pipeline_completed','pipeline_failed'].includes(session.value?.status ?? '') },
  { key: 'prompt', label: 'Build prompt', done: ['prompt_built','pipeline_submitted','pipeline_completed','pipeline_failed'].includes(session.value?.status ?? '') },
  { key: 'pipeline', label: 'Run AI Pipeline', done: ['pipeline_completed'].includes(session.value?.status ?? '') },
])
</script>

<template>
  <div class="min-h-screen p-6 max-w-3xl mx-auto space-y-4">
    <UCard v-if="session">
      <template #header>
        <div class="flex items-center justify-between">
          <h1 class="text-xl font-semibold font-mono">{{ session.id }}</h1>
          <UBadge>{{ session.status }}</UBadge>
        </div>
      </template>
      <ol class="space-y-2">
        <li v-for="step in steps" :key="step.key">
          <NuxtLink
            :to="`/sessions/${sid}/${step.key}`"
            class="flex items-center gap-3 py-2 px-3 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800"
          >
            <UIcon
              :name="step.done ? 'i-lucide-circle-check' : 'i-lucide-circle'"
              :class="step.done ? 'text-green-500' : 'text-neutral-400'"
            />
            <span>{{ step.label }}</span>
          </NuxtLink>
        </li>
      </ol>
    </UCard>
  </div>
</template>

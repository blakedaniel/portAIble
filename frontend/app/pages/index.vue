<script setup lang="ts">
const api = useApi()
const router = useRouter()

const { data: health } = await useAsyncData('health', () => api.health())
const { data: sessions, refresh } = await useAsyncData('sessions', () => api.listSessions())

const creating = ref(false)
async function startNew() {
  creating.value = true
  try {
    const s = await api.createSession()
    await router.push(`/sessions/${s.id}/extract`)
  } finally {
    creating.value = false
  }
}

async function remove(sid: string) {
  await api.deleteSession(sid)
  await refresh()
}
</script>

<template>
  <div class="min-h-screen p-6 max-w-3xl mx-auto space-y-6">
    <UCard>
      <template #header>
        <h1 class="text-2xl font-semibold">portAIble</h1>
        <p class="text-sm text-neutral-500">
          Interactive prompt-building experience for AI-driven code porting.
        </p>
      </template>

      <div class="space-y-3">
        <div v-if="health?.ok" class="flex items-center gap-2 text-sm">
          <UIcon name="i-lucide-circle-check" class="text-green-500" />
          <span>Backend reachable — workspace at <code>{{ health.workspace_dir }}</code></span>
        </div>
        <div v-else class="flex items-center gap-2 text-sm">
          <UIcon name="i-lucide-circle-alert" class="text-red-500" />
          <span>Backend not reachable</span>
        </div>
      </div>

      <template #footer>
        <UButton
          color="primary"
          icon="i-lucide-rocket"
          :loading="creating"
          label="Start a new porting session"
          @click="startNew"
        />
      </template>
    </UCard>

    <UCard v-if="sessions && sessions.sessions.length > 0">
      <template #header>
        <h2 class="text-lg font-medium">Recent sessions</h2>
      </template>
      <ul class="divide-y divide-neutral-200 dark:divide-neutral-800">
        <li v-for="s in sessions.sessions" :key="s.id" class="py-2 flex items-center gap-3">
          <NuxtLink :to="`/sessions/${s.id}`" class="font-mono text-sm hover:underline">
            {{ s.id }}
          </NuxtLink>
          <UBadge variant="subtle" :color="s.status.includes('failed') ? 'red' : 'gray'">
            {{ s.status }}
          </UBadge>
          <span class="text-xs text-neutral-500 ml-auto">
            {{ new Date(s.updated_at).toLocaleString() }}
          </span>
          <UButton
            color="red"
            variant="ghost"
            icon="i-lucide-trash-2"
            size="xs"
            @click="remove(s.id)"
          />
        </li>
      </ul>
    </UCard>
  </div>
</template>

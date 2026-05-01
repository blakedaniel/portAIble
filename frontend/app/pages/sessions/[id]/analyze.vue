<script setup lang="ts">
const route = useRoute()
const router = useRouter()
const sid = route.params.id as string
const api = useApi()

const running = ref(false)
const error = ref<string | null>(null)

async function run() {
  running.value = true
  error.value = null
  try {
    await api.analyze(sid)
    await router.push(`/sessions/${sid}/source-profile`)
  } catch (e: any) {
    error.value = e?.data?.detail ?? e?.message ?? String(e)
  } finally {
    running.value = false
  }
}
</script>

<template>
  <div class="min-h-screen p-6 max-w-2xl mx-auto space-y-4">
    <UCard>
      <template #header>
        <h1 class="text-xl font-semibold">Analyze source</h1>
        <p class="text-sm text-neutral-500">
          Phase 1 returns a canned profile (Django → Spring Boot). Phase 2 swaps in DSPy + Ollama.
        </p>
      </template>

      <div v-if="error" class="text-sm text-red-600">{{ error }}</div>

      <template #footer>
        <div class="flex gap-2">
          <UButton variant="ghost" :to="`/sessions/${sid}`">Back</UButton>
          <UButton color="primary" icon="i-lucide-sparkles" :loading="running" label="Run analyzer" @click="run" />
        </div>
      </template>
    </UCard>
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const router = useRouter()
const sid = route.params.id as string
const api = useApi()

const building = ref(false)
const error = ref<string | null>(null)

const { data: session, refresh } = await useAsyncData(
  `session:${sid}:prompt`, () => api.getSession(sid),
)

async function build() {
  building.value = true
  error.value = null
  try {
    await api.buildPrompt(sid)
    await refresh()
  } catch (e: any) {
    error.value = e?.data?.detail ?? e?.message ?? String(e)
  } finally {
    building.value = false
  }
}

async function submit() {
  await api.submitPipeline(sid)
  await router.push(`/sessions/${sid}/pipeline`)
}
</script>

<template>
  <div class="min-h-screen p-6 max-w-4xl mx-auto space-y-4">
    <UCard>
      <template #header>
        <h1 class="text-xl font-semibold">Assembled prompt</h1>
        <p class="text-sm text-neutral-500">Build the final prompt and ship it to the AI Pipeline.</p>
      </template>

      <div v-if="error" class="text-sm text-red-600 mb-2">{{ error }}</div>

      <div v-if="session?.assembled_prompt">
        <pre class="text-xs whitespace-pre-wrap bg-neutral-900 text-neutral-100 p-4 rounded max-h-[60vh] overflow-auto">{{ session.assembled_prompt.instructions }}</pre>
        <p class="text-xs text-neutral-500 mt-2">
          Source ZIP: <code>{{ session.assembled_prompt.source_zip_path }}</code>
        </p>
      </div>
      <UAlert v-else color="neutral" title="No prompt yet — click Build." />

      <template #footer>
        <div class="flex gap-2">
          <UButton variant="ghost" :to="`/sessions/${sid}`">Back</UButton>
          <UButton color="primary" icon="i-lucide-hammer" :loading="building" label="Build prompt" @click="build" />
          <UButton
            v-if="session?.assembled_prompt"
            color="green"
            icon="i-lucide-rocket"
            label="Submit to AI Pipeline"
            @click="submit"
          />
        </div>
      </template>
    </UCard>
  </div>
</template>

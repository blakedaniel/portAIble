<script setup lang="ts">
const route = useRoute()
const router = useRouter()
const sid = route.params.id as string
const api = useApi()

const jobId = ref<string | null>(null)
const status = ref<string>('idle')
const progressPct = ref<number>(0)
const progressMsg = ref<string>('')
const error = ref<string | null>(null)
let timer: ReturnType<typeof setTimeout> | null = null

async function poll() {
  if (!jobId.value) return
  try {
    const j = await api.getJob(sid, jobId.value)
    status.value = j.status
    progressPct.value = j.progress_percentage
    progressMsg.value = j.progress_message
    if (j.status === 'completed') {
      await router.push(`/sessions/${sid}/source-profile`)
      return
    }
    if (j.status === 'failed') {
      error.value = j.error || 'Analyzer failed'
      return
    }
  } catch (e: any) {
    error.value = e?.message || 'Polling error'
    return
  }
  timer = setTimeout(poll, 1500)
}

async function run() {
  error.value = null
  status.value = 'pending'
  try {
    const r = await api.analyze(sid)
    jobId.value = r.job_id
    poll()
  } catch (e: any) {
    error.value = e?.data?.detail ?? e?.message ?? String(e)
    status.value = 'idle'
  }
}

onBeforeUnmount(() => { if (timer) clearTimeout(timer) })
</script>

<template>
  <div class="min-h-screen p-6 max-w-2xl mx-auto space-y-4">
    <UCard>
      <template #header>
        <h1 class="text-xl font-semibold">Analyze source</h1>
        <p class="text-sm text-neutral-500">
          Runs the DSPy SourceAnalyzer in the background; redirects to the profile editor on completion.
        </p>
      </template>

      <div v-if="status !== 'idle'" class="space-y-3">
        <div class="flex items-center gap-2 text-sm">
          <UIcon
            v-if="status === 'completed'"
            name="i-lucide-circle-check"
            class="text-green-500"
          />
          <UIcon
            v-else-if="status === 'failed'"
            name="i-lucide-circle-x"
            class="text-red-500"
          />
          <UIcon v-else name="i-lucide-loader-circle" class="animate-spin" />
          <span class="capitalize">{{ status }}</span>
          <UBadge size="xs" variant="subtle">{{ progressPct }}%</UBadge>
        </div>
        <UProgress :value="progressPct" :color="status === 'failed' ? 'error' : 'primary'" />
        <p v-if="progressMsg" class="text-sm text-neutral-600 dark:text-neutral-300">
          {{ progressMsg }}
        </p>
      </div>

      <p v-if="error" class="text-sm text-red-600">{{ error }}</p>

      <template #footer>
        <div class="flex gap-2">
          <UButton variant="ghost" :to="`/sessions/${sid}`">Back</UButton>
          <UButton
            color="primary"
            icon="i-lucide-sparkles"
            :disabled="status !== 'idle' && status !== 'failed'"
            label="Run analyzer"
            @click="run"
          />
        </div>
      </template>
    </UCard>
  </div>
</template>

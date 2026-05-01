<script setup lang="ts">
const route = useRoute()
const api = useApi()
const sessionId = route.params.id as string
const { showError } = useErrorToast()

const status = ref<string>('pending')
const progress = ref<number>(0)
const message = ref<string>('')
const errorMsg = ref<string | null>(null)
const polling = ref<boolean>(true)

const intervalSec = ref<number>(2)
let timer: ReturnType<typeof setTimeout> | null = null

async function poll() {
  try {
    const r = await api.pollPipeline(sessionId)
    status.value = r.status
    progress.value = r.progress_percentage
    message.value = r.progress_message
    errorMsg.value = r.error
    if (r.status === 'failed') {
      showError(r.error ?? 'AI Pipeline failed', 'Pipeline failed')
    }
    if (r.status === 'completed' || r.status === 'failed') {
      polling.value = false
      return
    }
    // Exponential-ish backoff: 2s → 5s after 30s
    intervalSec.value = Math.min(intervalSec.value + 1, 5)
    timer = setTimeout(poll, intervalSec.value * 1000)
  } catch (e: any) {
    errorMsg.value = e?.message || 'Polling error'
    showError(e, 'Lost connection to backend while polling')
    polling.value = false
  }
}

onMounted(() => { poll() })
onUnmounted(() => { if (timer) clearTimeout(timer) })

const resultUrl = computed(() => api.pipelineResultUrl(sessionId))
</script>

<template>
  <div class="min-h-screen p-6 max-w-2xl mx-auto space-y-4">
    <NuxtLink to="/" class="text-sm text-neutral-500 hover:underline">← All sessions</NuxtLink>

    <UCard>
      <template #header>
        <h1 class="text-xl font-semibold">AI Pipeline</h1>
        <p class="text-xs text-neutral-500 font-mono">session: {{ sessionId }}</p>
      </template>

      <div class="space-y-3">
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
          <UIcon
            v-else
            name="i-lucide-loader-circle"
            class="animate-spin"
          />
          <span class="capitalize">{{ status }}</span>
          <UBadge size="xs" color="neutral" variant="subtle">{{ progress }}%</UBadge>
        </div>

        <UProgress :value="progress" :color="status === 'failed' ? 'error' : 'primary'" />

        <p v-if="message" class="text-sm text-neutral-600 dark:text-neutral-300">
          {{ message }}
        </p>
        <p v-if="errorMsg" class="text-sm text-red-600">
          <UIcon name="i-lucide-circle-alert" class="mr-1" />
          {{ errorMsg }}
        </p>
      </div>

      <template #footer>
        <UButton
          v-if="status === 'completed'"
          color="primary"
          icon="i-lucide-download"
          :to="resultUrl"
          external
          target="_blank"
          label="Download output.sh"
        />
        <UButton
          v-else
          color="neutral"
          variant="outline"
          icon="i-lucide-arrow-left"
          to="/"
          label="Back to sessions"
        />
      </template>
    </UCard>
  </div>
</template>

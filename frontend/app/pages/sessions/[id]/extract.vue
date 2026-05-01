<script setup lang="ts">
const route = useRoute()
const router = useRouter()
const sid = route.params.id as string
const api = useApi()

const file = ref<File | null>(null)
const uploading = ref(false)
const error = ref<string | null>(null)

function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  file.value = input.files?.[0] ?? null
}

async function upload() {
  if (!file.value) return
  uploading.value = true
  error.value = null
  try {
    await api.uploadZip(sid, file.value)
    await router.push(`/sessions/${sid}`)
  } catch (e: any) {
    error.value = e?.data?.detail ?? e?.message ?? String(e)
  } finally {
    uploading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen p-6 max-w-2xl mx-auto space-y-4">
    <UCard>
      <template #header>
        <h1 class="text-xl font-semibold">Extract source</h1>
        <p class="text-sm text-neutral-500">Upload a ZIP of the codebase to port.</p>
      </template>

      <div class="space-y-4">
        <input
          type="file"
          accept=".zip,application/zip"
          class="block w-full text-sm"
          @change="onFileChange"
        />
        <div v-if="file" class="text-sm text-neutral-600">
          Selected: <code>{{ file.name }}</code> ({{ Math.round(file.size / 1024) }} KB)
        </div>
        <div v-if="error" class="text-sm text-red-600">
          <UIcon name="i-lucide-circle-alert" class="inline mr-1" />{{ error }}
        </div>

        <UAlert
          color="neutral"
          variant="subtle"
          icon="i-lucide-info"
          title="GitHub coming in Phase 5"
          description="Public + private (PAT) GitHub URL extraction will land in a later phase."
        />
      </div>

      <template #footer>
        <div class="flex gap-2">
          <UButton variant="ghost" :to="`/sessions/${sid}`">Back</UButton>
          <UButton
            color="primary"
            icon="i-lucide-upload"
            :disabled="!file"
            :loading="uploading"
            label="Upload"
            @click="upload"
          />
        </div>
      </template>
    </UCard>
  </div>
</template>

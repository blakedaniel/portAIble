<script setup lang="ts">
const route = useRoute()
const router = useRouter()
const sid = route.params.id as string
const api = useApi()
const { showError } = useErrorToast()

const tab = ref<'zip' | 'github'>('zip')

// ZIP state
const file = ref<File | null>(null)
const uploading = ref(false)

// GitHub state
const ghUrl = ref('')
const ghRef = ref('')
const ghKind = ref<'public' | 'private'>('public')
const ghPat = ref('')
const cloning = ref(false)
const cloneProgress = ref('')

const error = ref<string | null>(null)

function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  file.value = input.files?.[0] ?? null
}

async function uploadZip() {
  if (!file.value) return
  uploading.value = true
  error.value = null
  try {
    await api.uploadZip(sid, file.value)
    await router.push(`/sessions/${sid}`)
  } catch (e: any) {
    error.value = showError(e, 'ZIP upload failed')
  } finally {
    uploading.value = false
  }
}

async function cloneGithub() {
  if (!ghUrl.value) {
    error.value = 'GitHub URL is required'
    return
  }
  if (ghKind.value === 'private' && !ghPat.value) {
    error.value = 'Private clones require a personal access token'
    return
  }
  cloning.value = true
  error.value = null
  cloneProgress.value = 'submitting...'
  try {
    const r = await api.extractGithub(sid, {
      url: ghUrl.value,
      ref: ghRef.value || null,
      pat: ghKind.value === 'private' ? ghPat.value : null,
      kind: ghKind.value,
    })
    // Drop the PAT from memory immediately after submit.
    ghPat.value = ''
    await pollClone(r.job_id)
  } catch (e: any) {
    error.value = showError(e, 'GitHub clone failed')
    cloning.value = false
  }
}

async function pollClone(jobId: string) {
  // Poll until the github extract job completes; redirect to session overview.
  const max = 60 // ~60 seconds at 1s intervals
  for (let i = 0; i < max; i++) {
    const j = await api.getJob(sid, jobId)
    cloneProgress.value = j.progress_message
    if (j.status === 'completed') {
      cloning.value = false
      await router.push(`/sessions/${sid}`)
      return
    }
    if (j.status === 'failed') {
      cloning.value = false
      error.value = j.error || 'Clone failed'
      return
    }
    await new Promise(r => setTimeout(r, 1000))
  }
  cloning.value = false
  error.value = 'Clone did not complete within 60s — check backend logs'
}
</script>

<template>
  <div class="min-h-screen p-6 max-w-2xl mx-auto space-y-4">
    <UCard>
      <template #header>
        <h1 class="text-xl font-semibold">Extract source</h1>
        <p class="text-sm text-neutral-500">Upload a ZIP, or shallow-clone from GitHub.</p>
      </template>

      <div class="flex gap-2 mb-4">
        <UButton :variant="tab === 'zip' ? 'solid' : 'ghost'" size="sm" @click="tab = 'zip'">ZIP upload</UButton>
        <UButton :variant="tab === 'github' ? 'solid' : 'ghost'" size="sm" @click="tab = 'github'">GitHub URL</UButton>
      </div>

      <div v-if="tab === 'zip'" class="space-y-4">
        <input type="file" accept=".zip,application/zip" class="block w-full text-sm" @change="onFileChange" />
        <div v-if="file" class="text-sm text-neutral-600">
          Selected: <code>{{ file.name }}</code> ({{ Math.round(file.size / 1024) }} KB)
        </div>
      </div>

      <div v-else class="space-y-3">
        <UInput v-model="ghUrl" placeholder="https://github.com/owner/repo" />
        <UInput v-model="ghRef" placeholder="Branch / tag / SHA (optional, defaults to HEAD)" />
        <div class="flex gap-3 items-center text-sm">
          <label class="flex items-center gap-1">
            <input type="radio" value="public" v-model="ghKind" /> Public
          </label>
          <label class="flex items-center gap-1">
            <input type="radio" value="private" v-model="ghKind" /> Private
          </label>
        </div>
        <UInput
          v-if="ghKind === 'private'"
          v-model="ghPat"
          type="password"
          placeholder="Personal Access Token (kept in memory only, never persisted)"
        />
        <p v-if="cloneProgress && cloning" class="text-sm text-neutral-500">
          <UIcon name="i-lucide-loader-circle" class="animate-spin mr-1" />
          {{ cloneProgress }}
        </p>
      </div>

      <div v-if="error" class="text-sm text-red-600 mt-3">
        <UIcon name="i-lucide-circle-alert" class="inline mr-1" />{{ error }}
      </div>

      <template #footer>
        <div class="flex gap-2">
          <UButton variant="ghost" :to="`/sessions/${sid}`">Back</UButton>
          <UButton
            v-if="tab === 'zip'"
            color="primary"
            icon="i-lucide-upload"
            :disabled="!file"
            :loading="uploading"
            label="Upload"
            @click="uploadZip"
          />
          <UButton
            v-else
            color="primary"
            icon="i-lucide-git-branch"
            :disabled="!ghUrl || (ghKind === 'private' && !ghPat)"
            :loading="cloning"
            label="Clone"
            @click="cloneGithub"
          />
        </div>
      </template>
    </UCard>
  </div>
</template>

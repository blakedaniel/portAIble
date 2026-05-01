<script setup lang="ts">
import type { SourceProfile } from '~/composables/useApi'

const route = useRoute()
const router = useRouter()
const sid = route.params.id as string
const api = useApi()

const { data: session } = await useAsyncData(`session:${sid}:source`, () => api.getSession(sid))
const profile = ref<SourceProfile | null>(session.value?.source_profile ?? null)

const saving = ref(false)
async function save() {
  if (!profile.value) return
  saving.value = true
  try {
    await api.putSource(sid, profile.value)
  } finally {
    saving.value = false
  }
}

async function confirm() {
  await save()
  await api.confirmSource(sid)
  await router.push(`/sessions/${sid}/destination-profile`)
}
</script>

<template>
  <div class="min-h-screen p-6 max-w-3xl mx-auto space-y-4">
    <UCard v-if="profile">
      <template #header>
        <h1 class="text-xl font-semibold">Source profile</h1>
        <p class="text-sm text-neutral-500">Edit the analyzer's draft and confirm.</p>
      </template>

      <div class="space-y-4">
        <details open>
          <summary class="font-medium">Languages</summary>
          <div class="mt-2 space-y-2">
            <div v-for="(lang, i) in profile.languages" :key="i" class="flex gap-2">
              <UInput v-model="lang.name" placeholder="name" class="flex-1" />
              <UInput v-model="lang.version" placeholder="version" />
              <UButton color="red" variant="ghost" icon="i-lucide-x" @click="profile.languages.splice(i, 1)" />
            </div>
            <UButton size="xs" variant="soft" icon="i-lucide-plus"
              @click="profile.languages.push({ name: '', version: null })">Add language</UButton>
          </div>
        </details>

        <details open>
          <summary class="font-medium">Frameworks</summary>
          <div class="mt-2 space-y-2">
            <div v-for="(fw, i) in profile.frameworks" :key="i" class="flex gap-2">
              <UInput v-model="fw.name" placeholder="name" class="flex-1" />
              <UInput v-model="fw.version" placeholder="version" />
              <UButton color="red" variant="ghost" icon="i-lucide-x" @click="profile.frameworks.splice(i, 1)" />
            </div>
            <UButton size="xs" variant="soft" icon="i-lucide-plus"
              @click="profile.frameworks.push({ name: '', version: null })">Add framework</UButton>
          </div>
        </details>

        <details>
          <summary class="font-medium">Packages</summary>
          <div class="mt-2 space-y-2">
            <div v-for="(pkg, i) in profile.packages" :key="i" class="flex gap-2">
              <UInput v-model="pkg.name" placeholder="name" class="flex-1" />
              <UInput v-model="pkg.version" placeholder="version" />
              <UButton color="red" variant="ghost" icon="i-lucide-x" @click="profile.packages.splice(i, 1)" />
            </div>
            <UButton size="xs" variant="soft" icon="i-lucide-plus"
              @click="profile.packages.push({ name: '', version: null, alternatives: [] })">Add package</UButton>
          </div>
        </details>

        <div>
          <label class="font-medium block mb-1">Important information</label>
          <UTextarea v-model="profile.important_information" :rows="6" />
        </div>
      </div>

      <template #footer>
        <div class="flex gap-2">
          <UButton variant="ghost" :to="`/sessions/${sid}`">Back</UButton>
          <UButton variant="soft" :loading="saving" label="Save draft" @click="save" />
          <UButton color="primary" icon="i-lucide-check" label="Confirm + continue" @click="confirm" />
        </div>
      </template>
    </UCard>
    <UAlert v-else color="neutral" title="No profile yet — run the analyzer first." />
  </div>
</template>

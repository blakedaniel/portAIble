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
        <EditableList
          v-model="profile.languages"
          label="Languages"
          placeholder="Add language (e.g. Python 3.12)"
        />
        <EditableList
          v-model="profile.frameworks"
          label="Frameworks"
          placeholder="Add framework (e.g. Django 4.2)"
        />
        <EditableList
          v-model="profile.packages"
          label="Packages"
          placeholder="Add package (e.g. requests)"
          with-alternatives
        />

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

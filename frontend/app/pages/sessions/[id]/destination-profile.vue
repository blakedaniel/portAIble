<script setup lang="ts">
import type { DestinationProfile } from '~/composables/useApi'

const route = useRoute()
const router = useRouter()
const sid = route.params.id as string
const api = useApi()

const { data: session, refresh } = await useAsyncData(`session:${sid}:dest`, () => api.getSession(sid))
const profile = ref<DestinationProfile | null>(session.value?.destination_profile ?? null)
const targetHint = ref('Spring Boot 3.5')
const suggesting = ref(false)

async function suggest() {
  suggesting.value = true
  try {
    const updated = await api.suggestDestination(sid, targetHint.value || null)
    profile.value = updated.destination_profile
    await refresh()
  } finally {
    suggesting.value = false
  }
}

async function save() {
  if (!profile.value) return
  await api.putDestination(sid, profile.value)
}

async function confirm() {
  await save()
  await api.confirmDestination(sid)
  await router.push(`/sessions/${sid}/decisions`)
}
</script>

<template>
  <div class="min-h-screen p-6 max-w-3xl mx-auto space-y-4">
    <UCard>
      <template #header>
        <h1 class="text-xl font-semibold">Destination profile</h1>
        <p class="text-sm text-neutral-500">Suggest from source, edit, then confirm.</p>
      </template>

      <div class="flex gap-2 mb-4">
        <UInput v-model="targetHint" placeholder="Target hint (e.g. Spring Boot 3.5)" class="flex-1" />
        <UButton color="primary" :loading="suggesting" icon="i-lucide-wand-2" @click="suggest">Suggest</UButton>
      </div>

      <div v-if="profile" class="space-y-4">
        <EditableList
          v-model="profile.languages"
          label="Languages"
          placeholder="Add language (e.g. Java 21)"
        />
        <EditableList
          v-model="profile.frameworks"
          label="Frameworks"
          placeholder="Add framework (e.g. Spring Boot 3.5)"
        />
        <EditableList
          v-model="profile.packages"
          label="Packages"
          placeholder="Add package (e.g. spring-boot-starter-web)"
          with-alternatives
        />

        <div>
          <label class="font-medium block mb-1">Target notes</label>
          <UTextarea v-model="profile.target_notes" :rows="6" />
        </div>
      </div>
      <UAlert v-else color="neutral" title="Click Suggest to draft a destination from the source profile." />

      <template #footer>
        <div class="flex gap-2">
          <UButton variant="ghost" :to="`/sessions/${sid}`">Back</UButton>
          <UButton v-if="profile" variant="soft" label="Save draft" @click="save" />
          <UButton v-if="profile" color="primary" icon="i-lucide-check" label="Confirm + continue" @click="confirm" />
        </div>
      </template>
    </UCard>
  </div>
</template>

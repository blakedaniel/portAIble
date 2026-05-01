<script setup lang="ts">
const route = useRoute()
const sid = route.params.id as string
const api = useApi()

const { data: session } = await useAsyncData(
  `session:${sid}:landing`,
  () => api.getSession(sid),
)
</script>

<template>
  <div class="p-6 max-w-3xl">
    <UCard v-if="session">
      <template #header>
        <div class="flex items-center justify-between gap-3">
          <h1 class="text-xl font-semibold">Session overview</h1>
          <UBadge
            size="xs"
            variant="subtle"
            :color="session.status.includes('failed') ? 'error' : 'neutral'"
          >
            {{ session.status }}
          </UBadge>
        </div>
      </template>
      <dl class="text-sm space-y-2">
        <div class="flex gap-3">
          <dt class="w-32 text-neutral-500">ID</dt>
          <dd class="font-mono">{{ session.id }}</dd>
        </div>
        <div v-if="session.extraction_kind" class="flex gap-3">
          <dt class="w-32 text-neutral-500">Source</dt>
          <dd>
            <UBadge size="xs" variant="subtle">{{ session.extraction_kind }}</UBadge>
            <code v-if="session.source_uri" class="ml-2 text-xs">{{ session.source_uri }}</code>
          </dd>
        </div>
        <div class="flex gap-3">
          <dt class="w-32 text-neutral-500">Files extracted</dt>
          <dd>{{ session.extracted_file_count }}</dd>
        </div>
        <div class="flex gap-3">
          <dt class="w-32 text-neutral-500">Created</dt>
          <dd>{{ new Date(session.created_at).toLocaleString() }}</dd>
        </div>
        <div class="flex gap-3">
          <dt class="w-32 text-neutral-500">Updated</dt>
          <dd>{{ new Date(session.updated_at).toLocaleString() }}</dd>
        </div>
      </dl>
      <p class="text-sm text-neutral-500 mt-4">
        Pick a step from the sidebar to continue the wizard.
      </p>
    </UCard>
  </div>
</template>

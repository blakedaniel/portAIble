<script setup lang="ts">
import MarkdownIt from 'markdown-it'

const route = useRoute()
const router = useRouter()
const sid = route.params.id as string
const api = useApi()
const { showError, showSuccess } = useErrorToast()

const md = new MarkdownIt({ html: false, linkify: true, breaks: false })

const building = ref(false)

const { data: session, refresh } = await useAsyncData(
  `session:${sid}:prompt`, () => api.getSession(sid),
)

const renderedHtml = computed(() =>
  session.value?.assembled_prompt
    ? md.render(session.value.assembled_prompt.instructions)
    : '',
)

async function build() {
  building.value = true
  try {
    await api.buildPrompt(sid)
    await refresh()
    showSuccess('Prompt built')
  } catch (e) {
    showError(e, 'Could not build prompt')
  } finally {
    building.value = false
  }
}

async function submit() {
  try {
    await api.submitPipeline(sid)
    await router.push(`/sessions/${sid}/pipeline`)
  } catch (e) {
    showError(e, 'Could not submit to AI Pipeline')
  }
}
</script>

<template>
  <div class="min-h-screen p-6 max-w-4xl mx-auto space-y-4">
    <UCard>
      <template #header>
        <h1 class="text-xl font-semibold">Assembled prompt</h1>
        <p class="text-sm text-neutral-500">Build the final prompt and ship it to the AI Pipeline.</p>
      </template>

      <div v-if="session?.assembled_prompt">
        <div
          class="prose-prompt bg-neutral-900 text-neutral-100 p-4 rounded max-h-[60vh] overflow-auto"
          v-html="renderedHtml"
        />
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

<style scoped>
.prose-prompt {
  font-size: 0.875rem;
  line-height: 1.6;
}
.prose-prompt :deep(h1),
.prose-prompt :deep(h2),
.prose-prompt :deep(h3),
.prose-prompt :deep(h4) {
  font-weight: 600;
  margin-top: 1.25em;
  margin-bottom: 0.5em;
  color: #f5f5f5;
}
.prose-prompt :deep(h1) { font-size: 1.5rem; }
.prose-prompt :deep(h2) { font-size: 1.25rem; }
.prose-prompt :deep(h3) { font-size: 1.05rem; }
.prose-prompt :deep(h4) { font-size: 0.95rem; }
.prose-prompt :deep(p) { margin: 0.6em 0; }
.prose-prompt :deep(ul),
.prose-prompt :deep(ol) {
  margin: 0.6em 0;
  padding-left: 1.5em;
}
.prose-prompt :deep(ul) { list-style: disc; }
.prose-prompt :deep(ol) { list-style: decimal; }
.prose-prompt :deep(li) { margin: 0.2em 0; }
.prose-prompt :deep(strong) { font-weight: 700; color: #fafafa; }
.prose-prompt :deep(em) { font-style: italic; }
.prose-prompt :deep(code) {
  background: rgba(255, 255, 255, 0.1);
  padding: 0.1em 0.35em;
  border-radius: 3px;
  font-size: 0.85em;
}
.prose-prompt :deep(pre) {
  background: #0a0a0a;
  padding: 0.85em 1em;
  border-radius: 4px;
  overflow-x: auto;
  margin: 0.8em 0;
}
.prose-prompt :deep(pre code) {
  background: transparent;
  padding: 0;
  font-size: 0.85em;
}
.prose-prompt :deep(a) {
  color: #93c5fd;
  text-decoration: underline;
}
.prose-prompt :deep(blockquote) {
  border-left: 3px solid #525252;
  padding-left: 1em;
  margin: 0.8em 0;
  color: #d4d4d4;
}
.prose-prompt :deep(hr) {
  border: none;
  border-top: 1px solid #404040;
  margin: 1em 0;
}
</style>

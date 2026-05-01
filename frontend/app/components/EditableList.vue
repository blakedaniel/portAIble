<script setup lang="ts">
interface Item {
  name: string
  version?: string | null
  alternatives?: string[]
}

const props = defineProps<{
  modelValue: Item[]
  label: string
  placeholder?: string
  /** Items in this list carry an `alternatives: []` field (packages do, lang/fw don't). */
  withAlternatives?: boolean
}>()
const emit = defineEmits<{ 'update:modelValue': [Item[]] }>()

const items = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const draftName = ref('')
const draftVersion = ref('')

function remove(i: number) {
  const next = items.value.slice()
  next.splice(i, 1)
  items.value = next
}

function add() {
  const name = draftName.value.trim()
  if (!name) return
  const next: Item = {
    name,
    version: draftVersion.value.trim() || null,
  }
  if (props.withAlternatives) next.alternatives = []
  items.value = [...items.value, next]
  draftName.value = ''
  draftVersion.value = ''
}
</script>

<template>
  <details open>
    <summary class="font-medium">{{ label }}</summary>
    <div class="mt-2 space-y-2">
      <div
        v-for="(item, i) in items"
        :key="i"
        class="flex gap-2 items-center"
      >
        <UButton
          color="red"
          variant="ghost"
          icon="i-lucide-x"
          size="xs"
          :aria-label="`Remove ${item.name || 'item'}`"
          @click="remove(i)"
        />
        <UInput v-model="item.name" placeholder="name" class="flex-1" />
        <UInput v-model="item.version" placeholder="version" />
      </div>
      <div class="flex gap-2 items-center pt-1">
        <UButton
          color="primary"
          variant="ghost"
          icon="i-lucide-plus"
          size="xs"
          :aria-label="`Add ${label.toLowerCase().replace(/s$/, '')}`"
          :disabled="!draftName.trim()"
          @click="add"
        />
        <UInput
          v-model="draftName"
          :placeholder="placeholder ?? `Add ${label.toLowerCase().replace(/s$/, '')}`"
          class="flex-1"
          @keydown.enter.prevent="add"
        />
        <UInput
          v-model="draftVersion"
          placeholder="version"
          @keydown.enter.prevent="add"
        />
      </div>
    </div>
  </details>
</template>

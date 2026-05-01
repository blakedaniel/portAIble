# Nuxt 2.x / Vue 2.x → Nuxt 4.x / Vue 3.x — Frontend Migration Guide

> **Purpose:** Migration-specific seed document. Bridges the gap between the Nuxt 2 / Vue 2 context doc and the Nuxt 4 / Vue 3 context doc, highlighting key translation patterns, conceptual shifts, and common pitfalls. Use alongside both framework context documents.

---

## 1. Migration Overview

- **Source:** Nuxt 2.15+ / Vue 2.6+ (or 2.7) with Options API, webpack 4, Vuex 3
- **Target:** Nuxt 4 / Vue 3.5+ with Composition API + `<script setup>`, Vite, Pinia
- **Migration complexity:** High
- **Key reasons for complexity:**
  - Paradigm shift: Options API (`data/computed/methods/watch`) → Composition API (`ref/reactive/computed/watch`) and `<script setup>` sugar
  - Build tool change: webpack 4 → Vite (import resolution, HMR, bundle splitting, env var handling all differ)
  - `srcDir` change: everything moves from project root into `app/` subdirectory
  - Data-fetching API replacement: `asyncData` / `fetch` hook → `useAsyncData` / `useFetch` composables
  - State management rewrite: Vuex 3 auto-discovered modules → Pinia setup stores
  - Plugin system changes: `inject()` helper → `defineNuxtPlugin` with `provide` return
  - SSR guards: `process.server` / `process.client` → `import.meta.server` / `import.meta.client`
  - Removal of `nuxtServerInit`, `router.extendRoutes`, and the `build.extend` webpack escape hatch
  - Dynamic route filename convention: `_id.vue` → `[id].vue`
- **What stays the same:**
  - File-based routing concept (one `.vue` file per route)
  - Layouts concept (`layouts/default.vue` wraps all pages)
  - Vue SFC structure (`<template>` / `<script>` / `<style>`)
  - Scoped CSS via `<style scoped>`
  - Slots model (default, named, scoped — same semantics)
  - `<NuxtLink>` and `<NuxtPage>` component names (Nuxt 2 already had PascalCase aliases)
  - `<ClientOnly>` component for browser-only subtrees
  - Convention-over-configuration philosophy
  - `.env` file support for environment variables
- **What fundamentally changes:**
  - State declaration: `data()` returning an object → `ref()` / `reactive()` calls in `<script setup>`
  - Reactivity caveats: `Vue.set` / `this.$set` are gone; Vue 3 uses Proxy-based deep reactivity that tracks property addition automatically
  - Computed and watch APIs: `this.computedProp` → `computed(() => ...)` returning a ref; `watch` receives reactive sources, not string keys
  - Lifecycle hook names: `beforeDestroy` → `onBeforeUnmount`, `destroyed` → `onUnmounted`, plus `beforeCreate`/`created` → setup body
  - Props: `props: { ... }` option → `defineProps<{...}>()` compiler macro
  - Emits: `this.$emit` → `defineEmits` macro + returned emit function
  - `v-model`: `value` prop + `input` event → `modelValue` prop + `update:modelValue` event; `.sync` modifier is gone
  - Old slot syntax (`slot="name"`, `slot-scope`) removed; only `v-slot:` / `#` shorthand survives
  - Template refs: `this.$refs.foo` → `const foo = ref(null)` + `ref="foo"` attribute
  - Store pattern: Vuex `state/getters/mutations/actions` four-section modules → Pinia setup functions mirroring Composition API
  - Data-fetching mental model: hooks that block the component (`asyncData` returns merge into `data()`) → composables that return reactive refs and serialize payloads
  - SEO / head: `vue-meta` and the `head()` option → `useHead` / `useSeoMeta` composables
  - `nuxt.config.js` (CommonJS-compatible) → `nuxt.config.ts` (`defineNuxtConfig` wrapper, TypeScript)
  - `~/` alias resolves to project root in Nuxt 2; resolves to `app/` (the new `srcDir`) in Nuxt 4

---

## 2. Project Structure Mapping

| Source path / concept | Target equivalent | Notes |
|---|---|---|
| `pages/` (project root) | `app/pages/` | `srcDir` is now `app/` in Nuxt 4; all framework dirs move inside it |
| `layouts/` | `app/layouts/` | Same concept; `<nuxt />` outlet replaced by `<slot />` |
| `components/` | `app/components/` | Auto-import still works; same subdirectory-prefix convention |
| `store/` (Vuex modules) | `app/stores/` (Pinia stores) | No auto-registration; each store is an explicitly exported composable |
| `plugins/` | `app/plugins/` | Auto-registered; `inject()` replaced by `provide:` return object |
| `middleware/` | `app/middleware/` | Named and `.global.ts` suffix; same directory, same concept |
| `assets/` | `app/assets/` | Still Vite-processed (was webpack-processed); alias `~/assets/` still works |
| `static/` | `public/` | Renamed to align with Vite/Nitro conventions; served verbatim |
| `nuxt.config.js` | `nuxt.config.ts` | `defineNuxtConfig()` wrapper; TypeScript; many key names changed |
| `store/index.js` (root store) | No equivalent | `nuxtServerInit` lived here; see §20 |
| `pages/_id.vue` | `app/pages/[id].vue` | Dynamic segment syntax changes from `_param` to `[param]` |
| `pages/_.vue` (catch-all) | `app/pages/[...slug].vue` | Explicit catch-all syntax |
| N/A | `server/` | Nitro server (API routes, server middleware) lives at project root, outside `app/` |
| `.nuxt/` | `.nuxt/` | Still generated; still gitignored; never edit |

**Alias change:** In Nuxt 2, `~/` and `@/` both resolved to the project root. In Nuxt 4, they resolve to `app/` (the `srcDir`). If you have imports like `~/store/` or `~/nuxt.config.js` they will break.

---

## 3. Component Syntax Translation

The translation from Options API to `<script setup>` is the most pervasive change in the migration.

**Before (Nuxt 2 / Vue 2 Options API):**

```vue
<!-- components/UserCard.vue -->
<template>
  <div class="user-card">
    <h2>{{ fullName }}</h2>
    <p>{{ greeting }}</p>
    <button @click="greet">Say Hello</button>
  </div>
</template>

<script>
export default {
  name: 'UserCard',

  props: {
    firstName: {
      type: String,
      required: true
    },
    lastName: {
      type: String,
      default: ''
    }
  },

  data() {
    return {
      greeting: null
    }
  },

  computed: {
    fullName() {
      return `${this.firstName} ${this.lastName}`.trim()
    }
  },

  methods: {
    greet() {
      this.greeting = `Hello, ${this.fullName}!`
      this.$emit('greeted', this.fullName)
    }
  }
}
</script>

<style scoped>
.user-card {
  border: 1px solid #ccc;
  padding: 1rem;
}
</style>
```

**After (Nuxt 4 / Vue 3 `<script setup>`):**

```vue
<!-- app/components/UserCard.vue -->
<script setup lang="ts">
const props = defineProps<{
  firstName: string
  lastName?: string
}>()

const emit = defineEmits<{
  greeted: [fullName: string]
}>()

const greeting = ref<string | null>(null)

const fullName = computed(() =>
  `${props.firstName} ${props.lastName ?? ''}`.trim()
)

function greet() {
  greeting.value = `Hello, ${fullName.value}!`
  emit('greeted', fullName.value)
}
</script>

<template>
  <div class="user-card">
    <h2>{{ fullName }}</h2>
    <p>{{ greeting }}</p>
    <button @click="greet">Say Hello</button>
  </div>
</template>

<style scoped>
.user-card {
  border: 1px solid #ccc;
  padding: 1rem;
}
</style>
```

Key differences:

- The `<script>` block becomes `<script setup lang="ts">`. No `export default`, no explicit `return`. Everything declared in setup is directly available in the template.
- `props` is defined with the `defineProps<T>()` compiler macro (no import needed). The `required` field is encoded by TypeScript — a non-optional type implies required.
- `data()` is gone. Each piece of local state is its own `ref()` call. Access and mutation always go through `.value` in script code (not in templates — templates auto-unwrap refs).
- `computed` becomes the `computed()` function returning a computed ref.
- `methods` is gone. Functions are declared directly in setup scope.
- `this` does not exist. Props are accessed via the `props` variable; emits via the `emit` function; refs via their `.value`.
- The `name` component option is no longer needed — Nuxt 4 infers the component name from its filename.
- `<style scoped>` is unchanged. The deep selector changes from `>>>` / `::v-deep` to `:deep()` (see §12).

---

## 4. Reactivity & State Translation

| Source concept | Target equivalent | Notes |
|---|---|---|
| `data() { return { x: 1 } }` | `const x = ref(1)` | Or `const state = reactive({ x: 1 })` for a group of related values |
| `this.x` (read) | `x.value` in script; `x` in template | Templates auto-unwrap `ref`; script always needs `.value` |
| `this.x = val` (write) | `x.value = val` | Direct assignment; no `Vue.set` needed |
| `Vue.set(obj, 'key', val)` | `obj.key = val` | Vue 3 Proxy tracks property addition automatically |
| `this.$set(arr, 0, val)` | `arr[0] = val` or `arr.value[0] = val` | Array index assignment is reactive in Vue 3 |
| `computed: { foo() {} }` | `const foo = computed(() => ...)` | Returns a readonly `ComputedRef`; access via `foo.value` |
| `watch: { x(newVal) {} }` | `watch(x, (newVal, oldVal) => {})` | First arg is the source ref or getter |
| `watch: { x: { deep: true, handler } }` | `watch(x, handler, { deep: true })` | Options as third argument |
| `watch: { x: { immediate: true, handler } }` | `watch(x, handler, { immediate: true })` | Same pattern |
| N/A | `watchEffect(() => {})` | Auto-tracks dependencies; runs immediately; no explicit source |

**Before (Nuxt 2 reactivity caveats):**

```vue
<script>
export default {
  data() {
    return {
      user: { name: 'Alice' },
      items: ['a', 'b', 'c']
    }
  },

  methods: {
    addProperty() {
      // Non-reactive without Vue.set — property added after init
      Vue.set(this.user, 'age', 30)
      // Or: this.$set(this.user, 'age', 30)
    },

    updateItem() {
      // Non-reactive direct index assignment in Vue 2:
      // this.items[0] = 'z'   ← DOES NOT trigger update

      // Correct approach in Vue 2:
      this.$set(this.items, 0, 'z')
      // Or: this.items.splice(0, 1, 'z')
    }
  }
}
</script>
```

**After (Nuxt 4 — Proxy-based reactivity, no caveats):**

```vue
<script setup lang="ts">
const user = reactive({ name: 'Alice' })
const items = ref(['a', 'b', 'c'])

function addProperty() {
  // Fully reactive — Proxy tracks new property assignment
  user.age = 30
}

function updateItem() {
  // Direct index assignment is reactive in Vue 3
  items.value[0] = 'z'
}
</script>
```

**`ref` vs `reactive` guidance:**
- Use `ref` for primitives (`string`, `number`, `boolean`) and for any value that may need to be replaced wholesale (e.g., swapping an array reference).
- Use `reactive` for objects where you always access the same reference and want dot-notation access without `.value`.
- Avoid destructuring a `reactive` object — it breaks reactivity. Use `toRefs(state)` if you need destructured reactive bindings.

---

## 5. Lifecycle Hook Translation

| Source hook (Options API) | Target equivalent (`<script setup>`) | Behavior difference |
|---|---|---|
| `beforeCreate` | setup body (top of `<script setup>`) | `beforeCreate` runs before reactivity init; setup runs after. No direct equivalent needed. |
| `created` | setup body | Both run on server + client. In `<script setup>`, the entire synchronous setup body is the equivalent. |
| `beforeMount` | `onBeforeMount` | Client-only in SSR. Rarely needed. |
| `mounted` | `onMounted` | Client-only in SSR. Safe for DOM access, `window`, third-party lib init. |
| `beforeUpdate` | `onBeforeUpdate` | Before reactive re-render. Same semantics. |
| `updated` | `onUpdated` | After reactive re-render. Same semantics. |
| `beforeDestroy` | `onBeforeUnmount` | **Name changed.** Begin teardown. |
| `destroyed` | `onUnmounted` | **Name changed.** Final cleanup — cancel timers, remove event listeners. |
| `errorCaptured` | `onErrorCaptured` | Same semantics. |
| `activated` | `onActivated` | `<KeepAlive>` re-activation. Same semantics. |
| `deactivated` | `onDeactivated` | `<KeepAlive>` de-activation. Same semantics. |

All hook functions are auto-imported inside `app/`. No `import { onMounted } from 'vue'` needed in a Nuxt 4 component (though explicit imports still work and are preferred in standalone composables for clarity).

**SSR behavior:** The setup body (equivalent to `created`) runs on both server and client. `onMounted` and below run only on the client. This is the same conceptual split as Nuxt 2's `created` (server-safe) vs. `mounted` (client-only). The difference is that in Nuxt 2 you guarded browser APIs with `process.client`; in Nuxt 4 you use `import.meta.client` or simply move code into `onMounted`.

**Before:**

```vue
<script>
export default {
  mounted() {
    window.addEventListener('resize', this.onResize)
  },
  beforeDestroy() {
    window.removeEventListener('resize', this.onResize)
  },
  methods: {
    onResize() {
      this.width = window.innerWidth
    }
  }
}
</script>
```

**After:**

```vue
<script setup lang="ts">
const width = ref(0)

function onResize() {
  width.value = window.innerWidth
}

onMounted(() => {
  window.addEventListener('resize', onResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
})
</script>
```

---

## 6. Props & Events Translation

**Before (Vue 2 / Options API):**

```vue
<!-- Child component -->
<script>
export default {
  props: {
    title: { type: String, required: true },
    count: { type: Number, default: 0 }
  },

  model: {
    prop: 'checked',
    event: 'change'
  },

  methods: {
    submit() {
      this.$emit('submit', { value: this.localValue })
    },
    updateTitle(newTitle) {
      this.$emit('update:title', newTitle)  // .sync pattern
    }
  }
}
</script>

<!-- Parent usage -->
<template>
  <ChildForm
    :title.sync="pageTitle"
    v-model="isChecked"
    @submit="handleSubmit"
  />
</template>
```

**After (Vue 3 / `<script setup>`):**

```vue
<!-- app/components/ChildForm.vue -->
<script setup lang="ts">
const props = defineProps<{
  title: string
  count?: number
}>()

const emit = defineEmits<{
  'update:title': [value: string]
  submit: [payload: { value: string }]
}>()

// For a single v-model binding, defineModel is the cleanest pattern (Vue 3.4+):
const checked = defineModel<boolean>('checked')

function submit() {
  emit('submit', { value: 'example' })
}

function updateTitle(newTitle: string) {
  emit('update:title', newTitle)  // .sync is replaced by v-model:title on parent
}
</script>

<!-- Parent usage -->
<template>
  <ChildForm
    v-model:title="pageTitle"
    v-model:checked="isChecked"
    @submit="handleSubmit"
  />
</template>
```

Key changes:

- `props` option → `defineProps<T>()` compiler macro with TypeScript interface
- `this.$emit` → `const emit = defineEmits<...>()` followed by `emit('event', payload)`
- `model: { prop, event }` option is gone; use `defineModel<T>(name?)` for any `v-model` binding
- `.sync` modifier (`@update:prop`) is gone; replaced by `v-model:propName` on the parent
- Multiple `v-model` bindings per component are now first-class (Vue 3 supports `v-model:foo` and `v-model:bar` simultaneously)
- Default values for props use `withDefaults(defineProps<T>(), { prop: defaultValue })`

---

## 7. Composables / Mixins / Shared Logic Translation

| Source pattern | Target equivalent | Notes |
|---|---|---|
| Mixin (local, via `mixins: []`) | Composable (a `use*` function) | No name conflicts, explicit return, trackable source |
| Global mixin (`Vue.mixin(...)` in a plugin) | No direct equivalent | Global mixins affect all component instances including third-party; redesign as a plugin that calls `app.mixin()` only if absolutely necessary [VERIFY whether `app.mixin()` is still supported in Vue 3] |
| Mixin `data()` properties | `ref` / `reactive` returned from composable | Caller explicitly receives and names the reactive refs |
| Mixin `computed` properties | `computed` returned from composable | Same |
| Mixin methods | Functions returned from composable | Same |
| Mixin lifecycle hooks | Lifecycle hooks called inside the composable body | Composable hooks are registered on the calling component's instance |

**Before (Nuxt 2 mixin):**

```js
// mixins/useFormatters.js
export default {
  data() {
    return {
      locale: 'en-US'
    }
  },

  methods: {
    formatCurrency(value, currency = 'USD') {
      return new Intl.NumberFormat(this.locale, {
        style: 'currency',
        currency
      }).format(value)
    }
  }
}
```

```vue
<!-- consuming component -->
<script>
import FormattersMixin from '~/mixins/useFormatters'

export default {
  mixins: [FormattersMixin],
  // this.formatCurrency is now available — but where it came from is non-obvious
}
</script>
```

**After (Nuxt 4 composable):**

```ts
// app/composables/useFormatters.ts
export function useFormatters() {
  const locale = ref('en-US')

  function formatCurrency(value: number, currency = 'USD') {
    return new Intl.NumberFormat(locale.value, {
      style: 'currency',
      currency
    }).format(value)
  }

  return { locale, formatCurrency }
}
```

```vue
<!-- consuming component — auto-imported, no import statement needed -->
<script setup lang="ts">
const { locale, formatCurrency } = useFormatters()
// Source is explicit; no silent namespace collision possible
</script>
```

Key structural differences:

- A composable is a plain function. There is no framework magic merging it — the caller destructures what it needs and names it explicitly.
- Lifecycle hooks called inside the composable body (`onMounted`, `onUnmounted`) are registered on the **calling component's instance**, just as mixin hooks were in Vue 2. This works correctly as long as the composable is called synchronously during component setup.
- Multiple composables with the same internal variable names do not conflict — the caller renames at destructure time.
- Composables in `app/composables/` are auto-imported in Nuxt 4. No `import` statement needed in SFCs.

---

## 8. Routing Translation

| Source pattern | Target equivalent | Notes |
|---|---|---|
| `pages/_id.vue` | `app/pages/[id].vue` | Dynamic segment uses bracket syntax, not underscore prefix |
| `pages/_.vue` (catch-all) | `app/pages/[...slug].vue` | Explicit spread syntax |
| `pages/users/_id/edit.vue` | `app/pages/users/[id]/edit.vue` | Same nesting, new filename convention |
| `this.$router.push(...)` | `const router = useRouter(); router.push(...)` or `navigateTo(...)` | `navigateTo` is the Nuxt-idiomatic universal navigation helper |
| `this.$route.params.id` | `const route = useRoute(); route.params.id` | Composable-based access |
| `middleware: 'auth'` (page option) | `definePageMeta({ middleware: ['auth'] })` | Compiler macro in `<script setup>` |
| `router.extendRoutes(routes, resolve)` in config | `router.options` in `nuxt.config.ts` + separate router plugin | No direct webpack-era equivalent; see §20 |
| Global middleware in `nuxt.config.js router.middleware` | `app/middleware/auth.global.ts` | `.global.ts` suffix auto-applies to every route |
| `<nuxt-link to="...">` / `<NuxtLink>` | `<NuxtLink>` | PascalCase form is identical in Nuxt 4 |
| `<nuxt-child />` (nested route outlet) | `<NuxtPage />` | Component name changed |

**Route naming:** In Nuxt 2, route names were generated from file paths with dashes separating segments (e.g., `users-id`). In Nuxt 4, route names follow the same pattern but use the bracket convention in filenames. Verify any `{ name: 'route-name' }` usages in `router.push` calls — names may differ for dynamic segments.

**Middleware signature change:**

```ts
// Nuxt 2 — receives context object
export default function ({ store, redirect, route }) {
  if (!store.state.auth.loggedIn) redirect('/login')
}

// Nuxt 4 — receives (to, from) route objects; returns navigateTo for redirects
export default defineNuxtRouteMiddleware((to, from) => {
  const auth = useAuthStore()
  if (!auth.isLoggedIn) return navigateTo('/login')
})
```

The Nuxt context object passed to middleware in Nuxt 2 (with `store`, `redirect`, `$axios`, etc.) does not exist in Nuxt 4. All context is accessed via composables inside the middleware function.

---

## 9. Layout Translation

The layout concept is preserved but the implementation details change significantly.

**Nuxt 2:** The layout file contains `<nuxt />` as the page outlet. Pages declare their layout via a `layout` option (string or function). Nuxt auto-applies `layouts/default.vue` when no layout is specified.

**Nuxt 4:** The layout file contains `<slot />` as the page outlet (it is a normal Vue component). Pages declare their layout via `definePageMeta({ layout: 'name' })`. `app.vue` must contain `<NuxtLayout><NuxtPage /></NuxtLayout>` for layouts to apply.

**Before (Nuxt 2):**

```vue
<!-- layouts/default.vue -->
<template>
  <div>
    <AppHeader />
    <main><nuxt /></main>
    <AppFooter />
  </div>
</template>
```

```vue
<!-- pages/dashboard.vue -->
<script>
export default {
  layout: 'dashboard'
}
</script>
```

**After (Nuxt 4):**

```vue
<!-- app/layouts/default.vue -->
<template>
  <div class="app-shell">
    <AppHeader />
    <main><slot /></main>
    <AppFooter />
  </div>
</template>
```

```vue
<!-- app/app.vue — required root component -->
<template>
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
</template>
```

```vue
<!-- app/pages/dashboard.vue -->
<script setup lang="ts">
definePageMeta({ layout: 'dashboard' })
</script>
```

**Dynamic layout (Nuxt 2 context function → Nuxt 4 reactive assignment):**

The Nuxt 2 `layout(context)` function that returned a layout name based on store state has no direct `definePageMeta` equivalent (it is a static compiler macro). For dynamic layouts in Nuxt 4, set `definePageMeta({ layout: false })` and wrap the page content manually with `<NuxtLayout :name="layoutName">`.

**Error layout:** `layouts/error.vue` in Nuxt 2 becomes `app/error.vue` in Nuxt 4. The error page receives `useError()` rather than an `error` prop. [VERIFY exact Nuxt 4 error page API — Nuxt 3 used `~/error.vue` at the project root; Nuxt 4 moves it to `app/error.vue` with the `srcDir` change.]

---

## 10. State Management Translation

See Nuxt 2 context §10 for the Vuex `state/getters/mutations/actions` four-export shape being translated from, and Nuxt 4 context §10 for the Pinia setup store pattern being translated to.

| Source concept | Target equivalent | Notes |
|---|---|---|
| `store/cart.js` (auto-discovered module) | `app/stores/useCartStore.ts` (explicit export) | No auto-registration; must import and call the store function |
| `export const state = () => ({})` | `const items = ref([])` inside `defineStore` | State is individual reactive refs in the setup store pattern |
| `export const getters = { ... }` | `const total = computed(() => ...)` | Computed refs inside the setup store |
| `export const mutations = { SET_X(state, val) }` | Direct assignment: `items.value = val` | Mutations are eliminated; state is mutated directly |
| `export const actions = { async fetch() {} }` | `async function fetchItems() {}` | Regular async functions inside the setup store |
| `this.$store.commit('cart/ADD_ITEM', item)` | `cartStore.items.push(item)` or a store action | Direct state mutation or action call |
| `this.$store.dispatch('cart/checkout')` | `await cartStore.checkout()` | Actions are plain async functions |
| `mapState`, `mapGetters`, `mapActions` | `storeToRefs(store)` for state/getters; actions destructured directly | `storeToRefs` preserves reactivity; plain destructure does not |
| `nuxtServerInit` | Server plugin or server route initialization | See §20 — no direct equivalent |

**Before (Nuxt 2 Vuex module + component usage):**

```js
// store/cart.js
export const state = () => ({
  items: []
})

export const getters = {
  totalItems(state) {
    return state.items.reduce((sum, item) => sum + item.qty, 0)
  }
}

export const mutations = {
  ADD_ITEM(state, item) {
    const existing = state.items.find(i => i.id === item.id)
    existing ? existing.qty++ : state.items.push({ ...item, qty: 1 })
  },
  CLEAR_CART(state) {
    state.items = []
  }
}

export const actions = {
  async checkout({ state, commit }) {
    await this.$axios.post('/api/orders', { items: state.items })
    commit('CLEAR_CART')
  }
}
```

```vue
<!-- Component usage (Nuxt 2) -->
<script>
import { mapState, mapGetters, mapActions } from 'vuex'

export default {
  computed: {
    ...mapState('cart', ['items']),
    ...mapGetters('cart', ['totalItems'])
  },
  methods: {
    ...mapActions('cart', ['checkout']),
    addItem(item) {
      this.$store.commit('cart/ADD_ITEM', item)
    }
  }
}
</script>
```

**After (Nuxt 4 Pinia setup store + component usage):**

```ts
// app/stores/useCartStore.ts
import { defineStore } from 'pinia'

interface CartItem {
  id: number
  name: string
  price: number
  qty: number
}

export const useCartStore = defineStore('cart', () => {
  const items = ref<CartItem[]>([])

  const totalItems = computed(() =>
    items.value.reduce((sum, item) => sum + item.qty, 0)
  )

  function addItem(item: Omit<CartItem, 'qty'>) {
    const existing = items.value.find(i => i.id === item.id)
    if (existing) {
      existing.qty++
    } else {
      items.value.push({ ...item, qty: 1 })
    }
  }

  async function checkout() {
    await $fetch('/api/orders', {
      method: 'POST',
      body: { items: items.value }
    })
    items.value = []
  }

  return { items, totalItems, addItem, checkout }
})
```

```vue
<!-- Component usage (Nuxt 4) -->
<script setup lang="ts">
const cartStore = useCartStore()
const { items, totalItems } = storeToRefs(cartStore)

function addItem(item) {
  cartStore.addItem(item)
}

async function checkout() {
  await cartStore.checkout()
}
</script>
```

---

## 11. Data Fetching Translation

This is one of the highest-impact changes. The Nuxt 2 model used component hooks (`asyncData`, `fetch`) that had implicit side effects (merging into `data()`, blocking navigation). The Nuxt 4 model uses composables that return reactive refs.

| Source pattern | Target equivalent | Notes |
|---|---|---|
| `asyncData({ $axios, params })` | `useAsyncData` or `useFetch` in `<script setup>` | No longer merges into `data()`; returns `{ data, status, error }` |
| `async fetch() { this.posts = ... }` | `useFetch` / `useAsyncData` | `$fetchState.pending` → `status === 'pending'` |
| `this.$axios.get(url)` | `await $fetch(url)` | `$fetch` is the Nuxt 4 low-level utility (based on `ofetch`) |
| `fetchOnServer: false` | `useFetch(url, { server: false })` | Skips SSR fetch; data loads client-side only |
| Client-only fetch in `mounted()` | `useLazyFetch` or `useFetch` with `server: false` | More explicit intent |
| `error({ statusCode: 404 })` | `throw createError({ statusCode: 404, message: '...' })` | Standard H3 error creation |
| `$fetch` for manual trigger | `const { refresh } = useFetch(...)` then `await refresh()` | Or `refreshNuxtData(key)` for cross-component invalidation |

**Before (Nuxt 2 `asyncData` pattern):**

```vue
<script>
export default {
  async asyncData({ $axios, params, error }) {
    try {
      const { data } = await $axios.get(`/api/posts/${params.id}`)
      return { post: data }   // merged into component data
    } catch (e) {
      error({ statusCode: 404, message: 'Post not found' })
    }
  },

  data() {
    return { post: null }
  }
}
</script>

<template>
  <article v-if="post">
    <h1>{{ post.title }}</h1>
    <p>{{ post.body }}</p>
  </article>
</template>
```

**After (Nuxt 4 `useFetch` pattern):**

```vue
<script setup lang="ts">
interface Post {
  id: number
  title: string
  body: string
}

const route = useRoute()

const { data: post, status, error } = await useFetch<Post>(
  () => `/api/posts/${route.params.id}`,
  {
    key: `post-${route.params.id}`,
  }
)

if (error.value) {
  throw createError({ statusCode: 404, message: 'Post not found' })
}
</script>

<template>
  <div v-if="status === 'pending'">Loading...</div>
  <article v-else-if="post">
    <h1>{{ post.title }}</h1>
    <p>{{ post.body }}</p>
  </article>
</template>
```

**Critical difference — return merge vs. explicit refs:**

In Nuxt 2, `asyncData` returned a plain object that was silently merged into the component's `data()`. This made the data appear as if it had always been there. In Nuxt 4, `useFetch` and `useAsyncData` return `{ data, status, error, refresh }`. The `data` ref starts as `null` (or your `default` value) and is populated when the fetch completes. You must explicitly destructure and reference `data.value` — there is no merge.

**Before (Nuxt 2 `fetch` hook with `$fetchState`):**

```vue
<template>
  <div>
    <p v-if="$fetchState.pending">Loading...</p>
    <p v-else-if="$fetchState.error">{{ $fetchState.error.message }}</p>
    <ul v-else>
      <li v-for="post in posts" :key="post.id">{{ post.title }}</li>
    </ul>
    <button @click="$fetch">Refresh</button>
  </div>
</template>

<script>
export default {
  data() { return { posts: [] } },
  async fetch() {
    const { data } = await this.$axios.get('/api/posts')
    this.posts = data
  }
}
</script>
```

**After (Nuxt 4 `useFetch` with status):**

```vue
<script setup lang="ts">
const { data: posts, status, error, refresh } = await useFetch<Post[]>('/api/posts', {
  default: () => []
})
</script>

<template>
  <div>
    <p v-if="status === 'pending'">Loading...</p>
    <p v-else-if="error">{{ error.message }}</p>
    <ul v-else>
      <li v-for="post in posts" :key="post.id">{{ post.title }}</li>
    </ul>
    <button @click="refresh">Refresh</button>
  </div>
</template>
```

---

## 12. Styling Changes

The scoped styling system is preserved but the deep selector syntax changes.

| Source syntax | Target equivalent | Notes |
|---|---|---|
| `>>> .child` | `:deep(.child)` | Old piercing combinator removed |
| `/deep/ .child` | `:deep(.child)` | `/deep/` was a Vue 2 alias for `>>>`; also removed |
| `::v-deep .child` | `:deep(.child)` | Vue 2.6+ pseudo-element form; replaced in Vue 3 |
| `::v-slotted .slot-content` | `:slotted(.slot-content)` | New in Vue 3 — targets slotted content from parent |
| `::v-global .anything` | `:global(.anything)` | New in Vue 3 — opt out of scoping for one rule |

Global styles, `css` key in config, and preprocessor support work the same conceptually. The difference is that webpack's `node-sass` / `sass-loader` setup is replaced by Vite's native Sass support (install `sass` — no loader config needed):

```ts
// nuxt.config.ts — global styles (same concept, different file extension)
export default defineNuxtConfig({
  css: ['~/assets/css/main.scss'],
})
```

`@nuxtjs/style-resources` (which auto-injected SCSS variables into every SFC) is not needed in Nuxt 4. Use Vite's `preprocessorOptions` instead:

```ts
// nuxt.config.ts
export default defineNuxtConfig({
  vite: {
    css: {
      preprocessorOptions: {
        scss: {
          additionalData: '@use "~/assets/scss/_variables.scss" as *;'
        }
      }
    }
  }
})
```

Dynamic class and style binding syntax is unchanged: `:class="{ active: isActive }"` and `:style="{ color: textColor }"` work identically.

---

## 13. Slots & Content Projection Translation

| Source concept | Target equivalent | Notes |
|---|---|---|
| `<slot />` (default) | `<slot />` | Unchanged |
| `<slot name="header" />` (named) | `<slot name="header" />` | Unchanged |
| `<slot :row="row" />` (scoped) | `<slot :row="row" />` | Unchanged in child |
| `slot="header"` (old attr syntax) | `<template #header>` or `<template v-slot:header>` | **`slot=` attribute syntax is removed in Vue 3** |
| `slot-scope="{ row }"` (old scoped syntax) | `<template #default="{ row }">` | **`slot-scope` attribute syntax is removed in Vue 3** |
| `v-slot:header` | `v-slot:header` or `#header` | Only syntax that works in both Vue 2.6+ and Vue 3 |
| `$slots.default` | `$slots.default()` | Slots are now functions in Vue 3; must be called |
| `$scopedSlots.row` | `$slots.row` | `$scopedSlots` is gone; all slots unified under `$slots` |

The `v-slot:` directive (introduced in Vue 2.6) and its `#` shorthand carry over unchanged. The old `slot=` attribute and `slot-scope=` attribute syntaxes are fully removed. If the codebase uses the old forms, all slot usage in parent templates must be converted.

**Before (Vue 2 old slot syntax — will not compile in Vue 3):**

```vue
<AppModal>
  <template slot="header">
    <h2>Confirm</h2>
  </template>
  <template slot="footer" slot-scope="{ onConfirm }">
    <button @click="onConfirm">Yes</button>
  </template>
</AppModal>
```

**After (Vue 3 — only `v-slot:` / `#` syntax):**

```vue
<AppModal>
  <template #header>
    <h2>Confirm</h2>
  </template>
  <template #footer="{ onConfirm }">
    <button @click="onConfirm">Yes</button>
  </template>
</AppModal>
```

---

## 14. Plugins & Middleware Translation

**Plugin registration changes significantly.** Nuxt 2 plugins used a `(context, inject)` signature. Nuxt 4 plugins use `defineNuxtPlugin` returning a `provide` object.

**Before (Nuxt 2 plugin with `inject`):**

```js
// plugins/api.js
import axios from 'axios'

export default function ({ $config, store }, inject) {
  const api = axios.create({ baseURL: $config.apiBaseUrl })

  api.interceptors.request.use(config => {
    const token = store.state.auth.token
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
  })

  inject('api', api)
  // Now available as:
  // this.$api  in components
  // context.$api  in asyncData/middleware
  // this.$api  in Vuex actions
}
```

```js
// nuxt.config.js
export default {
  plugins: [
    '~/plugins/api.js',
    { src: '~/plugins/chart.js', mode: 'client' }
  ]
}
```

**After (Nuxt 4 plugin with `defineNuxtPlugin`):**

```ts
// app/plugins/api.client.ts  (filename suffix controls client/server; no config needed)
import axios from 'axios'

export default defineNuxtPlugin(() => {
  const config = useRuntimeConfig()
  const authStore = useAuthStore()

  const api = axios.create({ baseURL: config.public.apiBase })

  api.interceptors.request.use(cfg => {
    if (authStore.token) {
      cfg.headers.Authorization = `Bearer ${authStore.token}`
    }
    return cfg
  })

  return {
    provide: {
      api,   // available as useNuxtApp().$api or const { $api } = useNuxtApp()
    },
  }
})
```

Key differences:

- No `inject` function; use the `provide` key in the return object.
- The Nuxt context object (`context.store`, `context.$axios`, etc.) is gone. Access store via Pinia, config via `useRuntimeConfig()`.
- Client/server split: either use the filename suffix (`.client.ts`, `.server.ts`) or `mode` in `nuxt.config.ts`. Filename suffix is the idiomatic Nuxt 4 approach.
- `$api` accessed in components via `const { $api } = useNuxtApp()` — no longer `this.$api` since `this` is gone.

**Middleware migration** is covered in §8. The `(context)` argument signature becomes `(to, from)` with `defineNuxtRouteMiddleware`.

---

## 15. Build & Config Changes

| Source concept | Target equivalent | Notes |
|---|---|---|
| `nuxt.config.js` (CJS/ESM) | `nuxt.config.ts` with `defineNuxtConfig()` | TypeScript with IDE autocomplete |
| `head: { ... }` (vue-meta) | `app.head` in config, or `useHead()` / `useSeoMeta()` composables per-page | vue-meta is gone |
| `buildModules: [...]` | `modules: [...]` | `buildModules` distinction is gone; all modules use `modules` |
| `build.extend(config)` (webpack) | `vite: { plugins: [...] }` | No webpack escape hatch; Vite plugin API instead |
| `publicRuntimeConfig` / `privateRuntimeConfig` | `runtimeConfig: { public: {}, ...serverOnly }` | Unified object; public values nested under `public` key |
| `process.env.VAR` at build time | `useRuntimeConfig()` at runtime | Prefer runtime config; `NUXT_*` env vars auto-map to `runtimeConfig` |
| `router.extendRoutes` | `router.options` or a custom router plugin | No direct equivalent; see §20 |
| `generate.routes` | `routeRules` or a hook in `nitro.hooks` | [VERIFY exact Nuxt 4 API for dynamic route generation at SSG time] |
| `ssr: true/false` | `ssr: true/false` | Same key; works in Nuxt 4 |
| `mode: 'universal'` / `mode: 'spa'` | Removed | Use `ssr: true` / `ssr: false` |
| `nuxt build` / `nuxt start` | `nuxi build` / `nuxi preview` | CLI renamed from `nuxt` to `nuxi` |
| Output in `.nuxt/` + `server/` | Output in `.output/` | Production output directory changed |
| `@nuxtjs/style-resources` for SCSS globals | `vite.css.preprocessorOptions.scss.additionalData` | Native Vite config; no module needed |
| `@nuxt/typescript-build` | Built-in | TypeScript support is native in Nuxt 4; no separate build module |

**`nuxt.config.ts` structure comparison:**

```ts
// nuxt.config.ts (Nuxt 4)
export default defineNuxtConfig({
  compatibilityDate: '2024-11-01',  // [VERIFY] required field in Nuxt 4
  future: { compatibilityVersion: 4 },  // [VERIFY] used during Nuxt 3→4 opt-in period

  modules: [
    '@pinia/nuxt',
    '@nuxtjs/tailwindcss',
    '@nuxt/image',
  ],

  runtimeConfig: {
    apiSecret: process.env.API_SECRET ?? '',
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE ?? '/api',
    },
  },

  routeRules: {
    '/': { prerender: true },
    '/dashboard/**': { ssr: true },
  },

  vite: {
    css: {
      preprocessorOptions: {
        scss: {
          additionalData: '@use "~/assets/scss/_vars.scss" as *;'
        }
      }
    }
  },
})
```

---

## 16. SSR Behavior Changes

**`process.server` / `process.client` are deprecated.** In Nuxt 4, prefer `import.meta.server` / `import.meta.client`. The old forms may still work but produce deprecation warnings. [VERIFY whether `process.server`/`process.client` throw or only warn in Nuxt 4 stable.]

**Before:**

```vue
<script>
export default {
  created() {
    if (process.client) {
      const saved = localStorage.getItem('draft')
    }
  }
}
</script>
```

**After:**

```vue
<script setup lang="ts">
// In setup, which runs server-side too — guard with import.meta.client:
if (import.meta.client) {
  const saved = localStorage.getItem('draft')
}
// Better: move browser-only code to onMounted, which never runs on the server
onMounted(() => {
  const saved = localStorage.getItem('draft')
})
</script>
```

**`<client-only>` → `<ClientOnly>`:** The component is renamed to PascalCase. The `#placeholder` slot name is preserved. [VERIFY: `<client-only>` (kebab) may still work as an alias in Nuxt 4.]

**Hydration model:** The SSR → client hydration mechanism is unchanged in concept (server renders HTML; Vue attaches on the client). Nuxt 4 uses Vue 3's Proxy-based reactivity, which means there are fewer hydration mismatch sources related to reactive object caveats. The most common new source of mismatches is reading browser APIs (or `Date.now()`) in the synchronous `<script setup>` body, which now runs during SSR.

**Module-level singletons are a server-side data leak.** A top-level `const state = ref({})` in a composable file creates one object shared across all concurrent SSR requests. In Nuxt 2 this was less common because `data()` was always a factory. In Nuxt 4, use `useState('key', () => defaultValue)` for any shared reactive state — it is scoped per request on the server and per app instance on the client.

**`$fetch` vs `useFetch` in SSR context:** `$fetch` called in `<script setup>` during SSR will execute a real HTTP request to your own server routes (going through the network). `useFetch` and `useAsyncData` are smart enough to call the handler directly without an HTTP round-trip when running on the server (server-to-server shortcut via Nitro). Always prefer `useFetch` / `useAsyncData` in component setup; reserve `$fetch` for event handlers and Pinia actions.

---

## 17. Common Migration Pitfalls

1. **`Vue.set` / `this.$set` calls left in the codebase.** These do not exist in Vue 3. A codebase search for `Vue.set` and `this.$set` is a required first step. The fix is simply direct property assignment — Vue 3's Proxy-based reactivity tracks it automatically.

   ```js
   // Broken in Vue 3:
   Vue.set(this.user, 'role', 'admin')
   this.$set(this.items, 0, updatedItem)

   // Fixed:
   user.role = 'admin'           // reactive object
   items.value[0] = updatedItem  // ref wrapping an array
   ```

2. **`this.$emit` called in `<script setup>`.** There is no `this` in `<script setup>`. Emits must be declared with `defineEmits` and called via the returned function.

   ```ts
   // Broken:
   this.$emit('close')

   // Fixed:
   const emit = defineEmits<{ close: [] }>()
   emit('close')
   ```

3. **`asyncData` return values not appearing in template.** In Nuxt 2, `asyncData` returned an object that merged into `data()`. In Nuxt 4, `useFetch` returns `{ data, status, error }`. Developers often access `post` directly instead of `post.value` in script, or forget that `data` is a `Ref<T | null>`.

   ```ts
   // Pitfall:
   const post = await useFetch('/api/post/1')
   console.log(post.title)       // undefined — post is the { data, status, error } object

   // Correct:
   const { data: post } = await useFetch<Post>('/api/post/1')
   console.log(post.value?.title) // correct
   ```

4. **`process.server` / `process.client` in Vite context.** Vite does not statically replace `process.server` the way webpack did. Code that relies on these being tree-shaken at build time may behave incorrectly. Replace with `import.meta.server` / `import.meta.client` which Vite and Nitro handle correctly.

5. **`nuxtServerInit` removal.** There is no Nuxt 4 equivalent of the root store's `nuxtServerInit` action. Code that hydrated auth state, cookies, or user sessions via `nuxtServerInit` must be rewritten. The recommended approach is a server plugin (`app/plugins/auth.server.ts`) that reads cookies and populates a Pinia store or `useState`. See §20.

6. **`~/store/` auto-registration is gone.** Nuxt 2 auto-discovered every file in `store/` and registered it as a namespaced Vuex module. In Nuxt 4, you must explicitly create a Pinia store file, export a `use*Store` composable, and call it in each component that needs it. There is no directory scan.

7. **`slot="name"` / `slot-scope` syntax removed.** Vue 3 only accepts `v-slot:name` / `#name`. Any template using the old attribute form will silently render nothing (or fail to compile in strict mode). Run a codebase search for `slot=` (without the colon) and `slot-scope=`.

8. **`mounted()` code breaking in SSR.** In Vue 3, `onMounted` is client-only — just like Vue 2's `mounted`. However, the `<script setup>` body runs on the server, unlike `mounted`. Code that was in `mounted()` and accidentally moved to the `<script setup>` top level will fail on the server with `window is not defined`.

9. **`$fetchState` missing.** Nuxt 2's `fetch` hook exposed `this.$fetchState.pending`, `this.$fetchState.error`, and `this.$fetch()`. These do not exist in Nuxt 4. Use the `status` and `error` refs from `useFetch` / `useAsyncData` and the `refresh` function instead.

10. **`@nuxt/content` v1 → v2/v3 schema differences.** If the project uses `@nuxt/content`, the v1 API (`.body` as an AST, `$content(path).fetch()`, `<nuxt-content :document="doc" />`) is entirely replaced in v2+. Documents now use MDC syntax, the query API is `queryContent()`, and the renderer is `<ContentRenderer>`. This is effectively a separate migration within the migration.

11. **`head()` method gone.** The Options API `head() { return { title: ... } }` method powered by `vue-meta` does not exist in Vue 3 / Nuxt 4. Replace with `useHead({ title: ... })` or `useSeoMeta({ title: ... })` in `<script setup>`.

12. **`@nuxtjs/axios` not compatible.** The `@nuxtjs/axios` module and its `this.$axios` injection are Nuxt 2–only. In Nuxt 4, use `$fetch` (built-in) or install and configure a third-party HTTP client manually in a plugin. All `this.$axios.get(...)` calls must be replaced.

13. **Dynamic route file naming in navigation.** Code using `router.push({ name: 'users-id', params: { id } })` must be verified. Route names in Nuxt 4 are generated from the bracket filename (`[id].vue`) and may differ from Nuxt 2's underscore convention (`_id.vue`). The route name for `app/pages/users/[id].vue` is `users-id` in Nuxt 4 [VERIFY exact route naming convention — Nuxt 4 may use a slightly different separator or prefix], but test all named navigation after migration.

14. **`definePageMeta` cannot use reactive values.** It is a compiler macro processed at build time. Passing a computed value or a ref as the `layout` or `middleware` option will not work. Use `<NuxtLayout :name="dynamicName">` for runtime-dynamic layout selection.

---

## 18. Conceptual Shifts to Internalize

- **`this` is gone.** In Vue 2 Options API, `this` was the component instance — the central access point for props, data, computed, methods, `$router`, `$store`, `$axios`, etc. In Nuxt 4 `<script setup>`, there is no `this`. Each concern has its own composable or variable. This is the most fundamental mental model shift and the root cause of most beginner mistakes during migration.

- **Refs need `.value` in script but not in templates.** Vue 3 auto-unwraps refs in templates. A `ref(0)` renders as `{{ count }}` in the template but is accessed as `count.value` in script. This inconsistency trips up developers who write logic in script files and forget `.value`, or who try to use `.value` in templates (which is harmless but unnecessary).

- **`setup()` / `<script setup>` runs on the server.** In Vue 2, the equivalent entry point was `created()`, which also ran on the server. But because the migration moves so much code from `mounted()` and `methods` into the flat setup body, it is easy to accidentally move browser-API code where it will run server-side. The rule is: `<script setup>` top level = server-safe only; `onMounted` = browser-safe.

- **Composables are not mixins with a new name.** Mixins merged implicitly. Composables return explicitly. A composable does not inject anything into `this` — it returns reactive values that the caller assigns to local variables. The caller has full control over naming. This eliminates the collision and origin-obscurity problems that made large mixin chains unmaintainable.

- **Pinia mutations vs. Vuex mutations.** In Vuex, all state changes had to go through mutations (synchronous, named, tracked in devtools). In Pinia setup stores, there are no mutations — you mutate state directly (`store.count++`). Devtools still records changes via Proxy observation. The discipline of naming and routing all changes through mutations is replaced by the discipline of keeping mutations inside store actions for testability. Developers comfortable with Vuex's strict mutation pattern may find this unsettling; it is intentional.

- **`useFetch` deduplication key semantics.** In Nuxt 2, `asyncData` ran once per server request with no key concept. In Nuxt 4, `useAsyncData` and `useFetch` use a key to deduplicate requests across the server render and client hydration. If two components use the same key, they share the same payload (by design). If the same component is used on multiple routes with route-specific data, the key must include the route param — a static key will serve stale data from a previous navigation. [VERIFY Nuxt 4 key deduplication behavior change from Nuxt 3.]

- **`import.meta.server` vs `process.server` is not just a rename.** `process.server` was statically replaced by webpack's DefinePlugin — the dead branch was tree-shaken. `import.meta.server` is replaced by Vite and Rollup during build. The semantics are the same but the toolchain is different. Code that assumed static branch elimination (e.g., requiring a Node.js-only module inside an `if (process.server)` block) should be verified to confirm Vite performs the same elimination. [VERIFY Vite/Rollup tree-shaking of `import.meta.server` branches.]

- **`$fetch` in component setup causes double-fetch in SSR.** Unlike `useFetch`, a bare `await $fetch(url)` in `<script setup>` runs once on the server and then again on the client (because the payload is not transferred). This is a silent performance regression. Always use `useFetch` or `useAsyncData` for data needed at render time.

---

## 19. Recommended Migration Order

A team migrating a real Nuxt 2 application should follow this sequence to minimize risk and maintain a deployable state at each phase.

1. **Audit and inventory.** Before touching code, document every: Vuex module and its dependencies, mixin and its consumers, plugin injections and where `this.$inject` is used, `asyncData` / `fetch` usage per page, and `@nuxtjs/axios` call sites. This map is the migration checklist.

2. **Scaffold the Nuxt 4 project alongside the existing app.** Create a fresh Nuxt 4 project with the correct `srcDir: 'app/'` structure. Do not try to in-place upgrade Nuxt 2 → 4. The webpack → Vite and directory restructure changes make an in-place upgrade hazardous. Run both apps in parallel during migration.

3. **Migrate configuration and infrastructure.** Port `nuxt.config.js` → `nuxt.config.ts`. Translate `publicRuntimeConfig` / `privateRuntimeConfig` → `runtimeConfig`. Replace `buildModules` + `modules` with the unified `modules` list. Verify that equivalent Nuxt 4 modules exist for every Nuxt 2 module in use (some have no equivalent; see §20).

4. **Migrate state management (Vuex → Pinia) first.** The store is a dependency of almost everything else. Convert each Vuex module (`store/cart.js`) to a Pinia setup store (`app/stores/useCartStore.ts`). Translate `state/getters/mutations/actions` to `ref/computed/functions`. Address `nuxtServerInit` (see §20) before moving on. Write store-level unit tests for each store before and after migration to confirm behavioral equivalence.

5. **Migrate plugins and middleware.** Convert each plugin from `(context, inject)` to `defineNuxtPlugin` + `provide`. Port route middleware to `defineNuxtRouteMiddleware`. Verify client-only plugins use `.client.ts` filename suffix.

6. **Migrate shared composables (from mixins).** Convert each mixin in `mixins/` to a composable in `app/composables/`. Start with stateless formatters and utilities (lowest risk), then stateful ones that manage lifecycle side effects.

7. **Migrate layouts.** Replace `<nuxt />` with `<slot />` in each layout file. Add `<NuxtLayout><NuxtPage /></NuxtLayout>` to `app/app.vue`. Test that the default layout and all named layouts render correctly. Port `layouts/error.vue` to `app/error.vue`.

8. **Migrate pages one by one, starting with the simplest.** For each page:
   - Rename `_param.vue` → `[param].vue`
   - Convert the Options API `<script>` to `<script setup lang="ts">`
   - Replace `asyncData` / `fetch` with `useFetch` / `useAsyncData`
   - Replace the `head()` option with `useSeoMeta()` / `useHead()`
   - Replace `middleware: 'auth'` option with `definePageMeta({ middleware: ['auth'] })`
   - Replace `layout: 'name'` option with `definePageMeta({ layout: 'name' })`

9. **Migrate components.** Convert each component from Options API to `<script setup lang="ts">`. Audit all `slot="name"` / `slot-scope` usages in parent templates and convert to `#name` / `v-slot:name`. Verify template ref usages (`this.$refs.foo` → `const foo = ref(null)`).

10. **Replace `@nuxtjs/axios` throughout.** After all pages and components are migrated, do a final pass replacing all `this.$axios` and `context.$axios` calls with `$fetch` or `useFetch`. This is left late because it is mechanical and can be done in bulk after the component structure is settled.

11. **Run type checking and fix TypeScript errors.** `nuxi typecheck` will surface prop type issues, missing `defineEmits`, and store typing gaps that may not be visible at runtime.

12. **Run Playwright e2e tests against the Nuxt 4 build.** Verify routing (especially named navigation and dynamic routes), form submissions, auth flows, and SSR-rendered pages. Pay special attention to hydration mismatches by checking the browser console for Vue hydration warnings.

---

## 20. Things That Don't Migrate Directly

- **`nuxtServerInit`.** The root Vuex action that Nuxt called once per server request (before page rendering) to hydrate cookies, tokens, and server-side user sessions has no single equivalent in Nuxt 4. The recommended replacement is a **server plugin** (`app/plugins/auth.server.ts`) that runs once per server request, reads cookies using `useCookie()` or `useRequestHeaders()`, and populates a `useState` key or a Pinia store. This is architecturally equivalent but requires explicitly splitting the concern into a plugin instead of embedding it in the store.

  ```ts
  // app/plugins/auth.server.ts
  export default defineNuxtPlugin(async () => {
    const token = useCookie('auth_token')
    if (token.value) {
      const user = await $fetch('/api/me', {
        headers: { Authorization: `Bearer ${token.value}` }
      }).catch(() => null)
      if (user) {
        const authStore = useAuthStore()
        authStore.user = user
      }
    }
  })
  ```

- **Vuex plugin patterns.** Vuex allowed `store.subscribe()` and `store.subscribeAction()` to hook into every mutation or action globally — commonly used for persistence (writing state to `localStorage` after every mutation) or analytics. Pinia's equivalent is `store.$subscribe()` (called on a specific store instance) and `pinia.$onAction()`. There is no global "intercept all stores" mechanism. Vuex plugins that patched the entire store need to be redesigned as Pinia plugins registered via `pinia.use()`. [VERIFY Pinia plugin API surface for global action interception.]

- **`build.extend` webpack escape hatch.** Nuxt 2 provided `build.extend(config, ctx)` in `nuxt.config.js` to arbitrarily modify the webpack configuration (add loaders, set aliases, configure webpack plugins). Nuxt 4 uses Vite; there is no webpack and no `extend` hook. Custom webpack configuration must be re-expressed as Vite plugins (`vite.plugins: [...]`) or PostCSS plugins. This is usually straightforward for common cases (SVG loaders, custom aliases) but can require significant work for projects that relied heavily on webpack-specific loaders or plugins with no Vite equivalent.

- **Mixin-based shared logic that does not translate cleanly to composables.** Mixins that relied on the Options API merge behavior for lifecycle hooks (`mounted` from three different mixins all firing in order) translate to composables with explicit lifecycle hook calls. However, mixins that read or mutated `this.$data` generically, or that intercepted `beforeCreate` to install dynamic reactivity, have no composable equivalent. These must be redesigned. Global mixins (`Vue.mixin(...)`) that patched every component instance (e.g., to add a `$log` method) should become either a plugin providing `$log` via `defineNuxtPlugin` + `provide`, or a composable that each component opts into.

- **`router.extendRoutes` in `nuxt.config.js`.** The Nuxt 2 `router.extendRoutes(routes, resolve)` hook let you push custom routes (with arbitrary `component` paths) into the auto-generated router config. In Nuxt 4, file-based routing is more opinionated. Custom routes can be added via `app/router.options.ts` (exporting a custom `routes` function) or a Nuxt hook in a module. This works but is less ergonomic than Nuxt 2's escape hatch. [VERIFY exact `router.options.ts` API and whether it supports async route generators in Nuxt 4.]

- **`@nuxtjs/auth-next` (Nuxt 2 auth module).** This module integrated deeply with `@nuxtjs/axios` and Vuex and has no Nuxt 4 port. Authentication must be reimplemented using one of: `nuxt-auth-utils` (lightweight session-based auth), `@sidebase/nuxt-auth` (NextAuth.js adapter), or a fully custom implementation using server API routes, `useCookie`, and a Pinia auth store. The migration effort depends on which auth strategies (JWT, OAuth, local) were in use.

- **`@nuxt/content` v1 API.** The `$content(path).fetch()` API, the `<nuxt-content>` renderer component, and the v1 document schema (with raw AST body) were replaced in v2 and again refined in v3. Projects using `@nuxt/content` must treat this as a separate migration effort: re-express all content queries using `queryContent()`, replace `<nuxt-content :document="doc" />` with `<ContentRenderer :value="doc" />`, and validate that MDC frontmatter fields match expectations.

- **`generate.routes` callback for dynamic SSG.** In Nuxt 2, `generate.routes` in `nuxt.config.js` allowed an async function to return a list of paths for `nuxt generate` to pre-render. In Nuxt 4, the equivalent is `nitro.prerender.routes` (static list) or the `nitro:config` hook for dynamic lists, or `routeRules` with `prerender: true` combined with a crawler. The exact API surface for async dynamic route generation in Nuxt 4 SSG mode should be verified against the Nitro and Nuxt 4 changelogs. [VERIFY]

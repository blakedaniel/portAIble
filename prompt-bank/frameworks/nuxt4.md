# Nuxt 4.x / Vue 3.x — Frontend Context Document

> **Purpose:** Seed document for AI-assisted framework migration. Covers the key structural and behavioral patterns of this frontend framework so a model can understand source or target code during a port.

---

## 1. Overview

- **Language:** TypeScript-first (JavaScript still supported; all official examples and generated code default to `.ts`)
- **Version covered:** Nuxt 4 (stable release line, requires Vue 3.5+)
- **Underlying UI library:** Vue 3 with Composition API and `<script setup>` syntax
- **Rendering modes supported:**
  - **Universal (SSR + client hydration)** — default; server renders HTML on each request, Vue takes over on the client
  - **Static Site Generation (SSG / `nuxi generate`)** — pre-renders all routes at build time
  - **SPA** — server sends an empty shell, all rendering is client-side (`ssr: false` in `nuxt.config.ts`)
  - **Hybrid** — per-route rendering rules via `routeRules` in `nuxt.config.ts` (some routes SSR, others SSG or SPA)
  - **Edge rendering** — Nitro targets (Cloudflare Workers, Vercel Edge, Netlify Edge) for low-latency universal rendering
- **Key design philosophy:** Convention over configuration. The filesystem is the API surface: directory names encode intent (pages, layouts, components, composables, etc.), eliminating most manual wiring. Vue 3 Composition API is the idiomatic abstraction layer; Nuxt adds universal rendering, auto-imports, and a server engine (Nitro) on top.
- **Package manager / toolchain:** pnpm (recommended), npm, yarn, or bun. Build tool: Vite (default, replaces webpack). Server engine: Nitro. CLI: `nuxi`.

---

## 2. Project Structure

Nuxt 4 changes the default `srcDir` from the project root to `app/`. This is one of the headline breaking changes from Nuxt 3. All framework-special directories (`pages/`, `components/`, `composables/`, etc.) now live inside `app/` by default.

```
project-root/
├── app/                          # srcDir (Nuxt 4 default — was project root in Nuxt 3)
│   ├── app.vue                   # Root component (wraps <NuxtLayout> + <NuxtPage>)
│   ├── pages/                    # File-based routing; each file = a route
│   │   ├── index.vue
│   │   ├── about.vue
│   │   └── posts/
│   │       ├── index.vue         # /posts
│   │       └── [id].vue          # /posts/:id (dynamic segment)
│   ├── layouts/                  # Named layouts consumed via <NuxtLayout>
│   │   ├── default.vue
│   │   └── dashboard.vue
│   ├── components/               # Auto-imported; subdirectory = name prefix
│   │   ├── AppHeader.vue
│   │   └── ui/
│   │       └── Button.vue        # auto-imported as <UiButton>
│   ├── composables/              # Auto-imported; use* naming convention
│   │   └── useAuth.ts
│   ├── utils/                    # Auto-imported utility functions
│   │   └── formatDate.ts
│   ├── middleware/               # Route middleware (named or global)
│   │   └── auth.ts
│   ├── plugins/                  # Nuxt plugins; run once at app init
│   │   └── analytics.client.ts   # .client suffix = client-only
│   └── assets/                   # Processed by Vite (Sass, PostCSS, images)
│       └── css/
│           └── main.css
├── server/                       # Nitro server (always at project root, outside srcDir)
│   ├── api/                      # API route handlers
│   │   └── hello.get.ts          # GET /api/hello
│   ├── routes/                   # Non-/api server routes
│   └── middleware/               # Server-side middleware (Nitro H3)
├── public/                       # Static files served as-is (favicon, robots.txt)
├── nuxt.config.ts                # Framework configuration
├── tsconfig.json                 # Auto-extended by Nuxt; do not delete
└── package.json
```

**Entry point:** `app/app.vue` is the root. `.nuxt/` (auto-generated, gitignored) holds the compiled router, auto-import manifests, and type stubs. Never edit `.nuxt/` manually.

**Auto-generated vs. manually managed:** `.nuxt/`, `.output/` are generated. Everything under `app/` and `server/` is author-managed. `nuxt.config.ts` and `tsconfig.json` at the root are manually managed (Nuxt extends `tsconfig.json` via `extends: "./.nuxt/tsconfig.json"`).

**Assets vs. public:** `app/assets/` files are processed by Vite (imported via `~/assets/...`). `public/` files bypass Vite and are served verbatim at `/`.

---

## 3. Component Architecture

Components are Vue 3 Single File Components (SFCs) with `.vue` extension. The `<script setup lang="ts">` block is the idiomatic pattern — it compiles to a more optimized render function and eliminates the need for explicit `return` statements.

**Naming convention:** PascalCase file names. Subdirectory structure becomes part of the auto-import name: `components/ui/Button.vue` is accessible as `<UiButton>`.

**Registration:** All components inside `app/components/` are globally auto-imported — no manual `import` or `components:` option needed. Third-party components must still be explicitly imported or registered via a plugin.

**Lazy loading:** Prefix any auto-imported component with `Lazy` to make it dynamically imported: `<LazyMyHeavyChart />`. Nuxt generates the async component wrapper automatically.

```vue
<!-- app/components/ui/PostCard.vue -->
<script setup lang="ts">
interface Post {
  id: number
  title: string
  excerpt: string
}

const props = defineProps<{
  post: Post
  featured?: boolean
}>()

const emit = defineEmits<{
  click: [postId: number]
}>()
</script>

<template>
  <article
    :class="['post-card', { 'post-card--featured': featured }]"
    @click="emit('click', post.id)"
  >
    <h2>{{ post.title }}</h2>
    <p>{{ post.excerpt }}</p>
  </article>
</template>

<style scoped>
.post-card {
  padding: 1rem;
  border: 1px solid #e2e8f0;
}
.post-card--featured {
  border-color: #3b82f6;
}
</style>
```

---

## 4. Reactivity & State (Component Level)

Vue 3 reactivity is built on `ref` (primitive wrapper) and `reactive` (object proxy). Both are auto-imported inside `app/` — no explicit import needed.

- **`ref<T>(value)`** — wraps any value; access/mutate via `.value` in script, unwrapped automatically in templates.
- **`reactive(obj)`** — makes a plain object deeply reactive; destructuring breaks reactivity (use `toRefs` to preserve it).
- **`computed(() => expr)`** — lazy, cached derived value; re-evaluates only when reactive dependencies change.
- **`watch(source, callback, options)`** — explicit, runs callback when source changes; can be lazy or immediate.
- **`watchEffect(callback)`** — eagerly tracks all reactive accesses inside the callback; re-runs when any dependency changes.
- **`shallowRef` / `shallowReactive`** — top-level reactivity only; useful for large objects where deep observation is too expensive.

```vue
<!-- app/components/Counter.vue -->
<script setup lang="ts">
import { ref, computed, watch } from 'vue'

const count = ref(0)
const step = ref(1)

const doubled = computed(() => count.value * 2)

function increment() {
  count.value += step.value
}

// Watch a single ref
watch(count, (newVal, oldVal) => {
  console.log(`count changed from ${oldVal} to ${newVal}`)
})

// watchEffect auto-tracks dependencies
watchEffect(() => {
  document.title = `Count: ${count.value}`
})
</script>

<template>
  <div>
    <p>Count: {{ count }} (doubled: {{ doubled }})</p>
    <input v-model.number="step" type="number" min="1" />
    <button @click="increment">+{{ step }}</button>
  </div>
</template>
```

**SSR note:** Reactive state declared at the top level of a `<script setup>` is component-instance-scoped and therefore safe for SSR. Avoid module-level mutable singletons — use `useState` (see §11) for shared SSR-safe state.

---

## 5. Component Lifecycle Hooks

All hooks are imported from `vue` (or auto-imported in Nuxt). In `<script setup>`, `setup()` itself is the equivalent of the Options API `created` hook — it runs synchronously on both server and client.

| Hook | When it runs | Common use |
|---|---|---|
| `setup()` (implicit) | Before component is mounted; runs on server + client | Initial reactive state, sync data access |
| `onBeforeMount` | After setup, before DOM is inserted | Rare; prefer `onMounted` |
| `onMounted` | After DOM is inserted — **client only in SSR** | DOM manipulation, third-party lib init, `window` access |
| `onBeforeUpdate` | Before DOM re-render after reactive change | Read pre-update DOM state |
| `onUpdated` | After DOM re-render | Post-update DOM reads (avoid mutations here) |
| `onBeforeUnmount` | Before component is destroyed | Begin teardown |
| `onUnmounted` | After component is destroyed | Clear timers, remove event listeners, cancel requests |
| `onErrorCaptured` | When a descendant throws | Error boundary logic |
| `onActivated` | When a `<KeepAlive>`-cached component is re-inserted | Resume paused work |
| `onDeactivated` | When a `<KeepAlive>`-cached component is removed | Pause work |

**SSR difference:** `onMounted`, `onBeforeMount`, `onUpdated`, `onUnmounted` etc. do **not** run on the server. Only the synchronous `setup()` body runs server-side. Any code that touches `window`, `document`, or browser APIs must be inside `onMounted` or guarded with `import.meta.client` (see §17).

```vue
<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'

let timer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  timer = setInterval(() => console.log('tick'), 1000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>
```

---

## 6. Props & Component Communication

**Declaring props** with `defineProps` (compiler macro, no import needed):

```vue
<script setup lang="ts">
// Runtime + type inference — preferred in Nuxt
const props = defineProps<{
  title: string
  count?: number          // optional
  tags: string[]
}>()

// With defaults (withDefaults)
const propsWithDefaults = withDefaults(
  defineProps<{ label: string; disabled?: boolean }>(),
  { disabled: false }
)
</script>
```

**Emitting events** with `defineEmits`:

```vue
<script setup lang="ts">
const emit = defineEmits<{
  update: [value: string]         // named tuple syntax (Vue 3.3+)
  close: []
  'item-selected': [id: number, label: string]
}>()

function handleClick() {
  emit('update', 'new value')
}
</script>
```

**Two-way binding (`v-model`):** Vue 3.4+ supports multiple `v-model` bindings per component. By default `v-model` maps to `modelValue` prop + `update:modelValue` emit.

```vue
<!-- Child: app/components/TextInput.vue -->
<script setup lang="ts">
const model = defineModel<string>()  // Vue 3.4+ shorthand
</script>
<template>
  <input v-model="model" />
</template>

<!-- Parent usage -->
<!-- <TextInput v-model="username" /> -->
```

**Provide / Inject** for deeply nested communication without prop-drilling:

```vue
<!-- Ancestor -->
<script setup lang="ts">
import { provide, ref } from 'vue'
const theme = ref<'light' | 'dark'>('light')
provide('theme', theme)
</script>

<!-- Deep descendant -->
<script setup lang="ts">
import { inject, type Ref } from 'vue'
const theme = inject<Ref<'light' | 'dark'>>('theme')
</script>
```

---

## 7. Composables / Shared Logic

The primary pattern for reusable logic is **composables**: plain TypeScript functions whose names start with `use`, which call Vue Composition API functions internally. All composables inside `app/composables/` are auto-imported.

A composable can own reactive state, manage side effects, and return refs that remain reactive in the consuming component.

```ts
// app/composables/useLocalStorage.ts
import { ref, watch } from 'vue'

export function useLocalStorage<T>(key: string, defaultValue: T) {
  const stored = import.meta.client
    ? localStorage.getItem(key)
    : null

  const value = ref<T>(stored ? JSON.parse(stored) : defaultValue)

  watch(value, (newVal) => {
    if (import.meta.client) {
      localStorage.setItem(key, JSON.stringify(newVal))
    }
  }, { deep: true })

  return value
}
```

```vue
<!-- Usage — no import needed inside app/ -->
<script setup lang="ts">
const darkMode = useLocalStorage('darkMode', false)
</script>
```

**Framework-provided composables (auto-imported everywhere):**

| Composable | Purpose |
|---|---|
| `useFetch` | SSR-aware data fetching with deduplication |
| `useAsyncData` | SSR-aware data fetching with a key |
| `useState` | SSR-safe shared reactive state (replaces module-level singletons) |
| `useRoute` | Access current route object |
| `useRouter` | Programmatic navigation |
| `useRuntimeConfig` | Access `nuxt.config.ts` `runtimeConfig` values |
| `useCookie` | SSR-safe reactive cookie |
| `useHead` | Manage `<head>` tags reactively |
| `useSeoMeta` | Type-safe SEO meta tag management |
| `useNuxtApp` | Access the Nuxt app instance (plugins, hooks) |
| `navigateTo` | Universal programmatic navigation |
| `useRequestHeaders` | Access incoming request headers on the server |

---

## 8. Routing

Routing is **file-based**. Every `.vue` file inside `app/pages/` becomes a route. The router is generated automatically; manual configuration is only needed for advanced cases via `nuxt.config.ts` (`router.options`).

**Route file naming conventions:**

| File | Route path |
|---|---|
| `pages/index.vue` | `/` |
| `pages/about.vue` | `/about` |
| `pages/posts/index.vue` | `/posts` |
| `pages/posts/[id].vue` | `/posts/:id` |
| `pages/posts/[...slug].vue` | `/posts/*` (catch-all) |
| `pages/[[optional]].vue` | `/:optional?` (optional param) |
| `pages/(group)/settings.vue` | `/settings` (route grouping, no path segment) |

**Accessing route params and query:**

```vue
<script setup lang="ts">
const route = useRoute()

// Dynamic segment
const id = computed(() => route.params.id as string)

// Query string
const page = computed(() => Number(route.query.page ?? 1))
</script>
```

**Programmatic navigation:**

```vue
<script setup lang="ts">
const router = useRouter()

async function goToPost(id: number) {
  await navigateTo(`/posts/${id}`)
  // or: await router.push(`/posts/${id}`)
}

// Redirect with status (e.g., in middleware or setup)
// await navigateTo('/login', { redirectCode: 302 })
</script>
```

**`definePageMeta`** — compiler macro for per-route metadata (runs at build time, cannot reference runtime values):

```vue
<script setup lang="ts">
definePageMeta({
  layout: 'dashboard',          // which layout to use
  middleware: ['auth'],         // named middleware to run
  title: 'My Posts',            // [VERIFY] availability depends on your head integration
  keepalive: true,              // wrap page in <KeepAlive>
})
</script>
```

[VERIFY] Some `definePageMeta` options that were available or planned in Nuxt 3 may have changed in Nuxt 4. Specifically, `pageTransition` and `layoutTransition` options inside `definePageMeta` should be verified against the Nuxt 4 release notes, as transition configuration was under revision.

**Route middleware** (defined in `app/middleware/`):

```ts
// app/middleware/auth.ts
export default defineNuxtRouteMiddleware((to, from) => {
  const { loggedIn } = useAuth()
  if (!loggedIn.value) {
    return navigateTo('/login')
  }
})
```

Named middleware files match the string passed to `middleware: ['auth']` in `definePageMeta`. Suffix `.global.ts` to run on every route without explicit declaration.

---

## 9. Layouts

Layouts are Vue components in `app/layouts/` that wrap page content via a `<slot>`. They must include exactly one `<slot />` where the page will be rendered.

**Default layout:** `app/layouts/default.vue` is used automatically for all pages unless overridden.

```vue
<!-- app/layouts/default.vue -->
<script setup lang="ts">
// No special setup required for a basic layout
</script>

<template>
  <div class="app-shell">
    <AppHeader />
    <main>
      <slot />        <!-- page content renders here -->
    </main>
    <AppFooter />
  </div>
</template>
```

**Named layout:** Create `app/layouts/dashboard.vue` and reference it in `definePageMeta`:

```vue
<!-- app/pages/settings.vue -->
<script setup lang="ts">
definePageMeta({ layout: 'dashboard' })
</script>
```

**Dynamic layout switching** (e.g., for authenticated vs. public views):

```vue
<!-- app/app.vue -->
<template>
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
</template>
```

```vue
<!-- Inside a page, to change layout dynamically -->
<script setup lang="ts">
definePageMeta({ layout: false })  // disable automatic layout

const layout = ref<string>('default')
</script>

<template>
  <NuxtLayout :name="layout">
    <div>Custom layout control</div>
  </NuxtLayout>
</template>
```

**Nested layouts** are not a first-class feature; compose them by nesting layout components manually or using parent route layouts with `<NuxtPage>` inside a layout's slot.

---

## 10. State Management (App Level)

**Pinia** is the officially recommended store for Nuxt. It is SSR-safe, has Vue Devtools integration, and is fully tree-shakeable.

Install: `pnpm add pinia @pinia/nuxt`. Add `@pinia/nuxt` to `modules` in `nuxt.config.ts`. All stores in `app/stores/` can be auto-imported [VERIFY auto-import path convention — `stores/` may need explicit `imports` config or rely on explicit import].

**Define a store:**

```ts
// app/stores/useUserStore.ts
import { defineStore } from 'pinia'

interface User {
  id: number
  name: string
  email: string
}

export const useUserStore = defineStore('user', () => {
  // Setup store syntax (preferred — mirrors Composition API)
  const user = ref<User | null>(null)
  const isLoggedIn = computed(() => user.value !== null)

  async function fetchUser(id: number) {
    const data = await $fetch<User>(`/api/users/${id}`)
    user.value = data
  }

  function logout() {
    user.value = null
  }

  return { user, isLoggedIn, fetchUser, logout }
})
```

**Consume in a component:**

```vue
<script setup lang="ts">
const userStore = useUserStore()

// Access state (reactive)
const { user, isLoggedIn } = storeToRefs(userStore)  // storeToRefs preserves reactivity

// Call actions directly
await userStore.fetchUser(42)
</script>
```

**For lightweight shared state without Pinia**, use `useState`:

```ts
// app/composables/useCounter.ts
export const useCounter = () => useState<number>('counter', () => 0)
```

`useState` is SSR-safe because the key ensures the same value is shared between server and client during hydration. It replaces the anti-pattern of module-level `ref()` singletons.

---

## 11. Data Fetching

Nuxt provides SSR-aware data fetching composables that run on the server and transfer their payload to the client, preventing double-fetching.

### `useFetch`

Convenience wrapper around `useAsyncData` + `$fetch`. Reactive to URL changes. Best for straightforward API calls tied to a component.

```vue
<script setup lang="ts">
interface Post {
  id: number
  title: string
  body: string
}

const route = useRoute()

const { data: post, status, error, refresh } = await useFetch<Post>(
  () => `/api/posts/${route.params.id}`,
  {
    key: `post-${route.params.id}`,   // deduplication key
    lazy: false,                        // true = non-blocking, renders before data arrives
    server: true,                       // default; set false to skip SSR fetch
    default: () => null,
  }
)
</script>

<template>
  <div v-if="status === 'pending'">Loading...</div>
  <div v-else-if="error">Error: {{ error.message }}</div>
  <article v-else-if="post">
    <h1>{{ post.title }}</h1>
    <p>{{ post.body }}</p>
  </article>
</template>
```

### `useAsyncData`

More flexible; accepts any async function, not just fetch calls. Used when you need to compose multiple requests or use a non-HTTP data source.

```vue
<script setup lang="ts">
const { data: posts } = await useAsyncData('posts-list', async () => {
  // Can call any async code here
  const result = await $fetch<Post[]>('/api/posts')
  return result.filter(p => p.published)
})
</script>
```

### Nuxt 4 `useAsyncData` key behavior change

[VERIFY] In Nuxt 3, multiple components using `useAsyncData` with the **same key** would share and deduplicate the request. Nuxt 4 changes this behavior: a unique key is now required per component instance to avoid unintended data sharing across page navigations. Calling `clearNuxtData(key)` or `refreshNuxtData(key)` still works, but key collision semantics may have changed. Always generate keys that include route params when the data is route-specific.

### `$fetch`

The lower-level fetch utility (based on `ofetch`). Does not deduplicate, does not transfer payload to client. Use it inside event handlers, Pinia actions, and server routes where SSR deduplication is not needed.

```ts
// Inside an action or event handler — not in component setup
const result = await $fetch<Post>('/api/posts', {
  method: 'POST',
  body: { title: 'Hello', body: 'World' },
})
```

**Lazy fetching:** `useLazyFetch` and `useLazyAsyncData` are non-blocking — the page renders immediately with `status === 'pending'` and data populates asynchronously. Useful when the data is secondary to the page render.

**Refresh and invalidation:**

```vue
<script setup lang="ts">
const { data, refresh } = await useFetch('/api/posts')
// Later:
// await refresh()                    // re-run the fetch
// clearNuxtData('posts-list')        // clear a useAsyncData payload
</script>
```

---

## 12. Styling

**Scoped styles** (default approach for component-level isolation):

```vue
<style scoped>
/* Only applies to elements in this component */
.card { padding: 1rem; }
/* Deep selector for child components */
:deep(.child-class) { color: red; }
</style>
```

**CSS Modules:**

```vue
<script setup lang="ts">
import styles from './Card.module.css'
// or use $style in template when using <style module>
</script>

<style module>
.card { padding: 1rem; }
</style>

<template>
  <div :class="$style.card">...</div>
</template>
```

**Global styles:** Add to `nuxt.config.ts`:

```ts
// nuxt.config.ts
export default defineNuxtConfig({
  css: ['~/assets/css/main.css'],
})
```

Or import in `app/app.vue`:
```vue
<style>
/* global, unscoped block in app.vue */
</style>
```

**Tailwind CSS:** Install `@nuxtjs/tailwindcss` module. Adds Tailwind via PostCSS with no manual Vite config. JIT mode is the default.

```ts
// nuxt.config.ts
export default defineNuxtConfig({
  modules: ['@nuxtjs/tailwindcss'],
})
```

**Dynamic/conditional classes:**

```vue
<template>
  <!-- Object syntax -->
  <div :class="{ active: isActive, 'text-error': hasError }">...</div>
  <!-- Array syntax -->
  <div :class="[baseClass, isActive ? 'active' : '']">...</div>
</template>
```

**Preprocessors (Sass/Less/Stylus):** Install the preprocessor (`pnpm add -D sass`) and use `<style lang="scss">` — Vite handles compilation with no additional config.

---

## 13. Forms & User Input

**`v-model`** binds form inputs bidirectionally to reactive state:

```vue
<script setup lang="ts">
const form = reactive({
  email: '',
  password: '',
  rememberMe: false,
  role: 'user',
})

async function submit() {
  await $fetch('/api/auth/login', { method: 'POST', body: form })
}
</script>

<template>
  <form @submit.prevent="submit">
    <input v-model="form.email" type="email" />
    <input v-model="form.password" type="password" />
    <input v-model="form.rememberMe" type="checkbox" />
    <select v-model="form.role">
      <option value="user">User</option>
      <option value="admin">Admin</option>
    </select>
    <button type="submit">Login</button>
  </form>
</template>
```

**`v-model` modifiers:** `.lazy` (sync on `change` instead of `input`), `.number` (auto-cast to number), `.trim` (auto-trim whitespace).

**Validation libraries:**

- **VeeValidate v4** — schema-based or rule-based; integrates with Yup, Zod, or Valibot.
- **Zod** — TypeScript-first schema validation; commonly paired with VeeValidate or used standalone in server routes.

```ts
// Example with VeeValidate + Zod
import { useForm } from 'vee-validate'
import { toTypedSchema } from '@vee-validate/zod'
import { z } from 'zod'

const schema = toTypedSchema(z.object({
  email: z.string().email(),
  password: z.string().min(8),
}))

const { handleSubmit, errors } = useForm({ validationSchema: schema })
```

For simple cases, manual validation with `computed` properties and reactive error objects is perfectly adequate and avoids external dependencies.

---

## 14. Slots & Content Projection

Vue slots allow a parent to inject template content into a child component.

**Default slot:**

```vue
<!-- app/components/Card.vue -->
<template>
  <div class="card">
    <slot />   <!-- parent content renders here -->
  </div>
</template>

<!-- Usage -->
<!-- <Card><p>Hello from parent</p></Card> -->
```

**Named slots:**

```vue
<!-- app/components/Modal.vue -->
<template>
  <dialog>
    <header>
      <slot name="header" />
    </header>
    <main>
      <slot />   <!-- default slot -->
    </main>
    <footer>
      <slot name="footer" />
    </footer>
  </dialog>
</template>

<!-- Usage -->
<!--
<Modal>
  <template #header><h2>Confirm</h2></template>
  <p>Are you sure?</p>
  <template #footer><button>OK</button></template>
</Modal>
-->
```

**Scoped slots** (child exposes data back to parent's template):

```vue
<!-- app/components/DataList.vue -->
<script setup lang="ts">
defineProps<{ items: string[] }>()
</script>

<template>
  <ul>
    <li v-for="(item, index) in items" :key="index">
      <slot :item="item" :index="index" />
    </li>
  </ul>
</template>

<!-- Usage -->
<!--
<DataList :items="names">
  <template #default="{ item, index }">
    <strong>{{ index + 1 }}.</strong> {{ item }}
  </template>
</DataList>
-->
```

**`v-slot` shorthand:** `#default`, `#header`, `#footer`.

**Fallback content:** Any content inside `<slot>fallback text</slot>` renders when the parent provides nothing.

---

## 15. Plugins & Middleware

### Nuxt Plugins

Plugins in `app/plugins/` run once when the Nuxt app is initialized (before any component is mounted). They are auto-registered in alphabetical order. Use them to add global properties, register third-party libraries, or provide composables.

**Filename suffixes control environment:**
- `myPlugin.ts` — runs on both server and client
- `myPlugin.client.ts` — runs only in the browser
- `myPlugin.server.ts` — runs only on the server

```ts
// app/plugins/toast.client.ts
import { defineNuxtPlugin } from '#app'
import ToastLibrary from 'some-toast-lib'

export default defineNuxtPlugin((nuxtApp) => {
  nuxtApp.vueApp.use(ToastLibrary)

  // Provide a helper accessible everywhere via useNuxtApp().$toast
  return {
    provide: {
      toast: (msg: string) => ToastLibrary.show(msg),
    },
  }
})
```

Access provided values in components:

```vue
<script setup lang="ts">
const { $toast } = useNuxtApp()
$toast('Saved successfully')
</script>
```

### Route Middleware

Route middleware runs before navigating to a route. Defined in `app/middleware/`. Two types:

1. **Named middleware** (`auth.ts`) — referenced explicitly in `definePageMeta({ middleware: ['auth'] })`
2. **Global middleware** (`auth.global.ts`) — runs before every route automatically

```ts
// app/middleware/auth.global.ts
export default defineNuxtRouteMiddleware((to) => {
  const { isLoggedIn } = useAuth()
  const publicRoutes = ['/', '/login', '/register']

  if (!publicRoutes.includes(to.path) && !isLoggedIn.value) {
    return navigateTo('/login')
  }
})
```

### Server Middleware (Nitro)

Server middleware lives in `server/middleware/` and uses H3 event handlers. Runs for every incoming request to the Nitro server — useful for logging, auth headers, CORS.

```ts
// server/middleware/logger.ts
export default defineEventHandler((event) => {
  console.log(`[${event.method}] ${event.path}`)
  // Call next implicitly (no return = pass through)
})
```

---

## 16. Build & Configuration

### `nuxt.config.ts`

The single source of truth for framework configuration:

```ts
// nuxt.config.ts
export default defineNuxtConfig({
  compatibilityDate: '2024-11-01',   // [VERIFY] Nuxt 4 requires this field; locks behavior to a date
  future: {
    compatibilityVersion: 4,          // [VERIFY] opt-in flag used during Nuxt 3→4 migration period
  },

  srcDir: 'app/',                     // default in Nuxt 4 (explicit here for clarity)

  modules: [
    '@pinia/nuxt',
    '@nuxtjs/tailwindcss',
    '@nuxt/image',
  ],

  runtimeConfig: {
    // Server-only secrets (not exposed to client)
    databaseUrl: process.env.DATABASE_URL ?? '',
    apiSecret: process.env.API_SECRET ?? '',
    // Public values (accessible on client via useRuntimeConfig().public)
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE ?? '/api',
      appName: 'My App',
    },
  },

  routeRules: {
    // Hybrid rendering
    '/': { prerender: true },           // SSG
    '/dashboard/**': { ssr: true },     // SSR
    '/blog/**': { isr: 3600 },          // ISR (incremental static regen, 1 hr) [VERIFY Nitro support]
    '/api/**': { cors: true },
  },

  vite: {
    // Pass Vite config directly
    plugins: [],
  },

  nitro: {
    // Nitro server config
    preset: 'node-server',              // deployment target
  },
})
```

### Environment Variables

Nuxt reads `.env` files via `dotenv`. Variables prefixed `NUXT_` map to `runtimeConfig` entries automatically (e.g., `NUXT_API_SECRET` → `runtimeConfig.apiSecret`; `NUXT_PUBLIC_API_BASE` → `runtimeConfig.public.apiBase`).

Access in components:

```ts
const config = useRuntimeConfig()
// config.public.apiBase  — available client + server
// config.apiSecret       — server only (empty string on client)
```

Access in server routes:

```ts
// server/api/hello.get.ts
export default defineEventHandler((event) => {
  const config = useRuntimeConfig(event)
  return { secret: config.apiSecret }
})
```

### Build Commands

```bash
nuxi dev          # Start dev server
nuxi build        # Build for production (outputs to .output/)
nuxi generate     # Full static generation (SSG)
nuxi preview      # Preview .output/ locally
nuxi typecheck    # Run vue-tsc type checking
```

---

## 17. SSR Considerations

### Server vs. Client Guards

Prefer the Vite/Nuxt-idiomatic `import.meta` guards over the deprecated `process.server` / `process.client`:

```ts
if (import.meta.server) {
  // Runs only on the server (Node.js / Nitro)
  // Safe to use: process.env, Node APIs, server-only imports
}

if (import.meta.client) {
  // Runs only in the browser
  // Safe to use: window, document, localStorage, browser APIs
}
```

In templates, use `<ClientOnly>` to completely skip SSR for a subtree:

```vue
<template>
  <ClientOnly>
    <HeavyBrowserOnlyChart />
    <template #fallback>
      <div>Loading chart...</div>
    </template>
  </ClientOnly>
</template>
```

### Hydration

After SSR, Vue's client runtime "hydrates" the server-rendered HTML by attaching event listeners and making the DOM reactive. Hydration mismatches (server HTML ≠ client render) cause Vue to warn and re-render the subtree, resulting in flicker.

**Common causes of hydration mismatch:**
- Reading `window`, `localStorage`, or `Date.now()` in `<script setup>` (runs on server too)
- Conditional rendering based on `Math.random()` or timestamps
- Browser extensions modifying the DOM before hydration

**Fix pattern:** Delay browser-API access to `onMounted`, or gate with `import.meta.client`.

### `useState` for SSR-Safe Shared State

Module-level `ref()` in composables creates a **singleton shared across all requests** on the server — this is a data leak between users. Use `useState` instead:

```ts
// app/composables/useTheme.ts
export const useTheme = () => useState<'light' | 'dark'>('theme', () => 'light')
```

`useState` serializes its value in the HTML payload and rehydrates it on the client — the state is per-request on the server and per-app-instance on the client.

### Server Routes and `useFetch` Payload Transfer

When `useFetch` or `useAsyncData` runs on the server, its result is serialized into the page's HTML payload (`__NUXT_DATA__`). On the client, Nuxt reads from this payload instead of re-fetching. This is the mechanism that prevents double-fetching; it requires that the returned data be JSON-serializable.

---

## 18. Key Conventions & Gotchas

### Nuxt 4 vs. Nuxt 3 Migration Points

1. **`srcDir` is now `app/`** — The single biggest structural change. All framework directories (`pages/`, `components/`, `composables/`, etc.) moved inside `app/`. Server routes stay at `server/` (project root). The alias `~/` resolves to `app/` in Nuxt 4.

2. **`compatibilityDate` is required** — Nuxt 4 introduces a `compatibilityDate` field in `nuxt.config.ts` that gates behavior changes. Omitting it triggers a warning. [VERIFY exact required value and whether it's enforced or just recommended]

3. **`process.server` / `process.client` deprecated** — Replace with `import.meta.server` / `import.meta.client`. The old forms still work but produce deprecation warnings. [VERIFY whether they are fully removed or only warned in Nuxt 4]

4. **`useAsyncData` key behavior** — [VERIFY] Nuxt 4 may change how keys are scoped when the same key is used in multiple component instances across navigations. Review the Nuxt 4 changelog for exact semantics before relying on shared keys for cross-component state.

5. **`definePageMeta` is a compiler macro** — It cannot reference reactive state or runtime variables. Strings and static expressions only. Errors here are sometimes confusing at runtime.

6. **No `pages/` = no router** — If `app/pages/` does not exist, Nuxt does not generate a router and `app.vue` renders directly. Add a single page file to activate the router. This is intentional for single-view apps.

7. **Auto-import scope** — Auto-imports apply to `app/` directories (components, composables, utils) but NOT to `server/`. Inside `server/api/` and `server/middleware/`, you must explicitly import `defineEventHandler`, `useRuntimeConfig`, etc. (though `#imports` can be used as a barrel [VERIFY]).

8. **Nitro and Vue are separate contexts** — `server/` code runs in Nitro (a separate Node.js/edge runtime). You cannot use Vue composables, `ref`, `computed`, or any Vue API in server routes — they are plain TypeScript with H3 utilities.

9. **`useFetch` URL reactivity** — If you pass a function `() => url` instead of a string, `useFetch` becomes reactive to its dependencies and re-fetches when they change. Forgetting the function wrapper means no reactivity on URL changes.

10. **`storeToRefs` is required for reactive Pinia destructuring** — Destructuring a Pinia store without `storeToRefs` gives you plain (non-reactive) values. Actions can be destructured directly without `storeToRefs`.

11. **Layouts must have exactly one `<slot />`** — Multiple default slots or missing slots will cause silent layout breakage.

12. **Plugin order matters** — Plugins are loaded alphabetically. Prefix filenames with numbers (`01.auth.ts`, `02.analytics.ts`) to control order explicitly.

---

## 19. Ecosystem & Common Libraries

| Concern | Typical Library |
|---|---|
| State management | Pinia (`@pinia/nuxt`) — official recommendation |
| Forms & validation | VeeValidate v4 + Zod or Valibot |
| UI component library | Nuxt UI v3 (`@nuxt/ui`), Vuetify (`vuetify` + `@vuetify/nuxt`), Shadcn-Vue, Headless UI |
| Data fetching | Built-in (`useFetch`, `useAsyncData`, `$fetch` via ofetch) |
| HTTP client (server routes) | `ofetch` (included), or native `fetch` in Nitro context |
| Icons | `@nuxt/icon`, `unplugin-icons` |
| Images | `@nuxt/image` |
| i18n | `@nuxtjs/i18n` (Vue I18n under the hood) |
| Auth | `nuxt-auth-utils`, `@sidebase/nuxt-auth` (NextAuth adapter), or custom with H3 sessions |
| SEO | Built-in `useSeoMeta` + `useHead`; `@nuxtjs/sitemap` for sitemaps |
| Testing (unit/component) | Vitest + `@vue/test-utils` + `@nuxt/test-utils` |
| E2E testing | Playwright (`@nuxt/test-utils/e2e`) or Cypress |
| ORM / DB (server) | Drizzle ORM, Prisma, or `@nuxtjs/supabase` |
| CSS framework | `@nuxtjs/tailwindcss`, UnoCSS (`@unocss/nuxt`) |
| Animation | `@vueuse/motion`, Transition API (built-in Vue) |
| Utilities | VueUse (`@vueuse/nuxt`) — 200+ composables for browser/sensor/network APIs |
| Deployment | Vercel (`@nuxtjs/vercel`), Netlify, Cloudflare Pages/Workers (via Nitro presets) |

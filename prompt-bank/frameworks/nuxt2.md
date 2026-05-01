# Nuxt 2.x / Vue 2.x — Frontend Context Document

> **Purpose:** Seed document for AI-assisted framework migration. Covers the key structural and behavioral patterns of Nuxt 2 / Vue 2 so a model can understand source or target code during a port.

---

## 1. Overview

- **Language:** JavaScript (ES2017+). TypeScript supported via `@nuxt/typescript-build` and `@nuxt/types`; adds `lang="ts"` to SFCs and a `tsconfig.json`, but is opt-in and not universal in Nuxt 2 codebases.
- **Version covered:** Nuxt 2.15.x running on Vue 2.6.x or 2.7.x. Vue 2.7 ("Naruto") backported `ref`, `reactive`, `computed`, `watch`, and `defineComponent` from Vue 3, so you may occasionally see Composition API code inside a Nuxt 2 project — treat it as valid but non-canonical for this era.
- **Underlying UI library:** Vue 2 (Options API is the dominant and expected pattern throughout Nuxt 2 tooling, devtools, and documentation).
- **Rendering modes supported:**
  - **SSR (default):** `mode: 'universal'` — HTML rendered on server per request, hydrated on the client.
  - **SSG:** `nuxt generate` — crawls routes at build time and outputs static HTML files.
  - **SPA:** `mode: 'spa'` — no server rendering; pure client-side Vue app served from a single `index.html`. [VERIFY: `ssr: false` was introduced as the preferred toggle in Nuxt 2.13+, alongside the deprecated `mode` key; both are valid in 2.15.]
- **Key design philosophy:** Convention over configuration. The filesystem drives routing, layouts, stores, middleware, and plugins. A developer who knows the directory convention can read any Nuxt 2 project without a config file.
- **Package manager / toolchain:** npm or yarn. Build tool is **webpack 4** (not Vite — that arrived with Nuxt 3). `@nuxt/cli` (`nuxt` binary) orchestrates dev, build, generate, and start commands.

---

## 2. Project Structure

Canonical Nuxt 2 project layout:

```
project-root/
├── assets/              # Unprocessed assets (SCSS, images) — imported and processed by webpack
├── components/          # Vue components — auto-imported (Nuxt 2.13+ with components: true in nuxt.config)
├── layouts/             # Page wrapper layouts (default.vue, error.vue, custom ones)
├── middleware/          # Route middleware functions (run before page components render)
├── pages/               # File-based router — every .vue file becomes a route
│   ├── index.vue
│   ├── about.vue
│   └── users/
│       ├── index.vue    # → /users
│       └── _id.vue      # → /users/:id  (dynamic segment)
├── plugins/             # JS/TS files injected into the Vue app (and optionally the server context)
├── static/              # Served as-is at root — no webpack processing (favicons, robots.txt)
├── store/               # Vuex store modules — auto-registered by Nuxt
│   ├── index.js         # Root store (required if any store file exists)
│   └── cart.js          # → namespaced module 'cart'
├── nuxt.config.js       # Central configuration file
├── package.json
└── .nuxt/               # Generated build artifacts — never edit manually, gitignored
```

**Entry point:** Nuxt manages its own entry points inside `.nuxt/`. The developer entry is `nuxt.config.js` and `pages/index.vue`.

**Auto-generated vs. manually managed:**
- `.nuxt/` is entirely generated on `nuxt dev` or `nuxt build` — do not edit.
- `pages/`, `layouts/`, `store/`, `middleware/`, `plugins/` are manually managed but have special framework meaning.
- `components/` auto-import requires `components: true` in `nuxt.config.js` (Nuxt 2.13+); without it, components must be imported manually.

**Assets vs. static:**
- `assets/` — webpack processes files here; reference via `~/assets/logo.png` (resolves to an hashed URL).
- `static/` — served verbatim at `/`; reference via `/logo.png` (no hashing, no processing).

---

## 3. Component Architecture

**Definition format:** Single File Components (SFCs) — `.vue` files with `<template>`, `<script>`, and `<style>` blocks.

**Options API structure:**

```vue
<template>
  <div class="user-card">
    <h2>{{ fullName }}</h2>
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

**Naming conventions:**
- Files: `PascalCase.vue` is idiomatic for components (`UserCard.vue`). Page files in `pages/` are typically `kebab-case.vue` or `lowercase.vue` since they map to URL segments.
- The `name` option is optional but strongly recommended for devtools and recursive components.

**Component registration:**
- **Local:** Import and declare in the `components` option of the consuming component.
- **Global (manual):** Create a plugin in `plugins/` that calls `Vue.component('MyComponent', MyComponent)`.
- **Auto-import (Nuxt 2.13+):** Set `components: true` in `nuxt.config.js`; Nuxt scans `components/` and registers every component globally by its filename. Subdirectory structure becomes a prefix: `components/base/Button.vue` registers as `<BaseButton>`.

```js
// nuxt.config.js — enable auto-import
export default {
  components: true
}
```

---

## 4. Reactivity & State (Component Level)

**Local state:** Always declared as a function `data()` returning a plain object. Vue 2's reactivity system walks the returned object at component creation and makes every property reactive via `Object.defineProperty`.

**Key constraint:** Properties added to a reactive object *after* initialization are NOT reactive unless you use `Vue.set(object, key, value)` (or `this.$set`). Likewise, array mutations must use splice-based methods or `Vue.set` — direct index assignment (`arr[0] = val`) does not trigger reactivity.

**Computed properties:** Defined under `computed`. They are lazy and cached by their reactive dependencies.

**Watchers:** Defined under `watch`. Use the object form for `immediate` or `deep` options.

```vue
<template>
  <div>
    <input v-model="query" placeholder="Search..." />
    <p>Results for: {{ normalizedQuery }}</p>
    <p>Cart total: ${{ cartTotal }}</p>
  </div>
</template>

<script>
export default {
  data() {
    return {
      query: '',
      items: [
        { name: 'Widget', price: 9.99, qty: 2 },
        { name: 'Gadget', price: 24.99, qty: 1 }
      ]
    }
  },

  computed: {
    normalizedQuery() {
      return this.query.trim().toLowerCase()
    },

    cartTotal() {
      return this.items.reduce((sum, item) => sum + item.price * item.qty, 0).toFixed(2)
    }
  },

  watch: {
    // Simple watcher
    query(newVal, oldVal) {
      console.log('Query changed:', oldVal, '→', newVal)
    },

    // Watcher with options
    items: {
      deep: true,
      handler(newItems) {
        console.log('Items updated:', newItems)
      }
    }
  },

  methods: {
    addItem() {
      // Reactive push — array mutation methods are patched by Vue 2
      this.items.push({ name: 'New', price: 5, qty: 1 })

      // Non-reactive — WRONG:
      // this.items[0].qty = 5  ← does NOT trigger updates in Vue 2

      // Correct for property update:
      this.$set(this.items[0], 'qty', 5)
      // Or: Vue.set(this.items[0], 'qty', 5)
    }
  }
}
</script>
```

**Vue 2.7 note:** If you see `import { ref, reactive, computed } from 'vue'` inside a Nuxt 2 project, it is using the backported Composition API. This is syntactically valid in 2.7 but is not the conventional Nuxt 2 pattern. Do not conflate it with Options API or assume all 2.x codebases use it.

---

## 5. Component Lifecycle Hooks

| Hook | When it runs | Common use |
|---|---|---|
| `beforeCreate` | Before reactivity and instance properties are set up | Rarely used directly |
| `created` | After reactivity is initialized; **runs on server in SSR** | Fetch data that must be server-rendered, initialize state |
| `beforeMount` | Before the component is mounted to the DOM | Rarely used |
| `mounted` | After the component is mounted to the DOM; **client only** | DOM manipulation, third-party lib init, client-only fetches |
| `beforeUpdate` | Before a reactive re-render | Capture pre-update DOM state |
| `updated` | After a reactive re-render | React to DOM changes (avoid infinite loops) |
| `beforeDestroy` | Before component teardown | Remove event listeners, cancel timers |
| `destroyed` | After teardown | Final cleanup |
| `errorCaptured` | When a descendant component throws | Error boundary handling |
| `activated` | When a `<keep-alive>` component is re-activated | Refresh cached component data |
| `deactivated` | When a `<keep-alive>` component is hidden | Pause timers inside cached components |

**SSR behavior:**
- `beforeCreate` and `created` **run on the server** during SSR. Code inside these hooks must not reference browser globals (`window`, `document`, `localStorage`).
- `beforeMount`, `mounted`, and everything after **only run on the client**. Any DOM-dependent or browser-API code must live in `mounted` or be guarded by `process.client`.

```vue
<script>
export default {
  created() {
    // Safe in SSR — no DOM access
    console.log('running on server or client')
  },

  mounted() {
    // Client-only — safe to access window
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

---

## 6. Props & Component Communication

**Props declaration:** Either an array of strings (quick form) or an object (recommended, enables validation):

```vue
<script>
export default {
  props: {
    title: {
      type: String,
      required: true
    },
    count: {
      type: Number,
      default: 0,
      validator(value) {
        return value >= 0
      }
    },
    items: {
      type: Array,
      default: () => []   // Object/Array defaults MUST be factory functions
    }
  }
}
</script>
```

**Emitting events (child → parent):**

```vue
<!-- Child -->
<script>
export default {
  methods: {
    submit() {
      this.$emit('submit', { value: this.localValue })
    }
  }
}
</script>

<!-- Parent -->
<template>
  <MyForm @submit="handleSubmit" />
</template>
```

**Two-way binding via `v-model`:** By default, `v-model` on a component binds `value` prop and listens for `input` event. Override with the `model` option:

```vue
<script>
export default {
  model: {
    prop: 'checked',
    event: 'change'
  },
  props: {
    checked: Boolean
  }
}
</script>
```

**`.sync` modifier:** A shorthand for updating a specific prop from the child without using `v-model`:

```vue
<!-- Parent — equivalent to @update:title="title = $event" -->
<ChildComponent :title.sync="pageTitle" />

<!-- Child -->
<script>
export default {
  methods: {
    updateTitle(newTitle) {
      this.$emit('update:title', newTitle)
    }
  }
}
</script>
```

**Event bus:** In Vue 2, a common (though discouraged) pattern for cross-component communication is a shared Vue instance used as an event bus. Prefer Vuex for app-level state instead.

---

## 7. Composables / Mixins / Shared Logic

**Primary pattern in Vue 2 / Nuxt 2: Mixins.** There are no composables in the Vue 3 sense (unless the project uses Vue 2.7's backported API). Mixins merge `data`, `methods`, `computed`, lifecycle hooks, and `watch` into consuming components.

**Defining a mixin:**

```js
// mixins/useFormatters.js
export default {
  methods: {
    formatCurrency(value, currency = 'USD') {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency
      }).format(value)
    },

    formatDate(dateStr) {
      return new Date(dateStr).toLocaleDateString('en-US')
    }
  }
}
```

**Using a mixin locally:**

```vue
<script>
import FormattersMixin from '~/mixins/useFormatters'

export default {
  mixins: [FormattersMixin],

  data() {
    return { price: 1234.56 }
  }
  // this.formatCurrency is now available
}
</script>
```

**Registering a mixin globally (plugin):**

```js
// plugins/mixins.js
import Vue from 'vue'
import FormattersMixin from '~/mixins/useFormatters'

Vue.mixin(FormattersMixin)
```

```js
// nuxt.config.js
export default {
  plugins: ['~/plugins/mixins.js']
}
```

**Mixin pitfalls:**
- If both the mixin and the component define a method with the same name, the component wins silently — no error.
- `data` properties from multiple mixins are merged; key collisions are overwritten by later mixins or the component.
- Lifecycle hooks from mixins and the component all run — mixin hooks first, then the component hook.
- Global mixins (via `Vue.mixin`) affect every component instance, including third-party components. Use sparingly.

**Vue 2.7 Composition API (if present in codebase):**

```vue
<script>
import { ref, computed, onMounted } from 'vue'  // Valid in Vue 2.7+

export default {
  setup() {
    const count = ref(0)
    const doubled = computed(() => count.value * 2)

    onMounted(() => {
      console.log('mounted via setup')
    })

    return { count, doubled }
  }
}
</script>
```

---

## 8. Routing

**File-based routing:** Nuxt 2 generates a `vue-router` configuration automatically from the `pages/` directory. No `router.js` configuration file is needed (though one can be added via `router.extendRoutes` in `nuxt.config.js`).

**Route mapping conventions:**

| File path | Generated route |
|---|---|
| `pages/index.vue` | `/` |
| `pages/about.vue` | `/about` |
| `pages/users/index.vue` | `/users` |
| `pages/users/_id.vue` | `/users/:id` |
| `pages/users/_id/edit.vue` | `/users/:id/edit` |
| `pages/_.vue` | Catch-all (404 handler) |

**Nested routes:** Create a directory and a same-named `.vue` file alongside it. The parent file must contain `<nuxt-child />` (or `<NuxtChild />`):

```
pages/
  users.vue          ← parent, contains <nuxt-child />
  users/
    index.vue        ← /users (rendered inside users.vue)
    _id.vue          ← /users/:id (rendered inside users.vue)
```

**Navigation:**

```vue
<template>
  <div>
    <!-- Declarative — nuxt-link is the Nuxt 2 alias for router-link -->
    <nuxt-link to="/about">About</nuxt-link>

    <!-- NuxtLink (PascalCase) also works in 2.x [VERIFY: exact version it was aliased] -->
    <NuxtLink :to="{ name: 'users-id', params: { id: 42 } }">User 42</NuxtLink>
  </div>
</template>

<script>
export default {
  methods: {
    goHome() {
      this.$router.push('/')
    },
    goToUser(id) {
      this.$router.push({ name: 'users-id', params: { id } })
    }
  }
}
</script>
```

**Accessing route params and query:**

```vue
<script>
export default {
  computed: {
    userId() {
      return this.$route.params.id
    },
    searchQuery() {
      return this.$route.query.q
    }
  }
}
</script>
```

**Route middleware:** Define in `middleware/` and assign to pages or layouts via the `middleware` property:

```js
// middleware/auth.js
export default function ({ store, redirect }) {
  if (!store.state.auth.loggedIn) {
    return redirect('/login')
  }
}
```

```vue
<script>
export default {
  middleware: 'auth'  // or an array: ['auth', 'role-check']
}
</script>
```

**Global middleware:** List in `nuxt.config.js` under `router.middleware`:

```js
// nuxt.config.js
export default {
  router: {
    middleware: ['auth']
  }
}
```

---

## 9. Layouts

**Default layout:** `layouts/default.vue` wraps every page automatically unless overridden. It must include `<nuxt />` (or `<Nuxt />`) to render the page component.

```vue
<!-- layouts/default.vue -->
<template>
  <div>
    <AppHeader />
    <main>
      <nuxt />
    </main>
    <AppFooter />
  </div>
</template>

<script>
export default {
  name: 'DefaultLayout'
}
</script>
```

**Custom layout:** Create any `.vue` file in `layouts/` and reference it by name from a page component:

```vue
<!-- layouts/minimal.vue -->
<template>
  <div class="minimal">
    <nuxt />
  </div>
</template>
```

```vue
<!-- pages/landing.vue -->
<script>
export default {
  layout: 'minimal'   // string name of the layout file
}
</script>
```

**Dynamic layout selection:**

```vue
<script>
export default {
  layout(context) {
    return context.store.state.auth.loggedIn ? 'dashboard' : 'public'
  }
}
</script>
```

**Error layout:** `layouts/error.vue` is a special layout Nuxt renders when an error is thrown. It receives an `error` prop:

```vue
<!-- layouts/error.vue -->
<template>
  <div>
    <h1>{{ error.statusCode }}</h1>
    <p>{{ error.message }}</p>
    <nuxt-link to="/">Go home</nuxt-link>
  </div>
</template>

<script>
export default {
  props: {
    error: {
      type: Object,
      required: true
    }
  }
}
</script>
```

**Nested layouts:** Nuxt 2 does not have first-class nested layouts. The workaround is to compose layout-like wrapper components inside child layouts and slot content manually. [VERIFY: There is no official nested layout API in Nuxt 2; some codebases simulate it by creating wrapper components used inside layout files.]

---

## 10. State Management (App Level)

Nuxt 2 uses **Vuex 3** (the Vue 2 compatible version). Nuxt auto-discovers and registers store modules from the `store/` directory — no manual store creation is needed.

**Auto-registration rules:**
- `store/index.js` — root store module (must exist if any store file is present).
- `store/cart.js` — becomes the namespaced module `cart`.
- `store/user/profile.js` — becomes the namespaced module `user/profile`.

**Module file format (classic modules mode):**

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
    if (existing) {
      existing.qty += 1
    } else {
      state.items.push({ ...item, qty: 1 })
    }
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

**State must be a factory function** (`state = () => ({})`) when using modules, to avoid state being shared across server requests in SSR.

**`nuxtServerInit`:** A special action in the **root store** (`store/index.js`) that Nuxt calls once per server request before rendering. Use it to hydrate server-side data (e.g., read cookies, fetch the current user):

```js
// store/index.js
export const actions = {
  async nuxtServerInit({ commit }, { req, $cookies }) {
    const token = req.headers.cookie  // or use cookie-universal-nuxt
    if (token) {
      try {
        const user = await this.$axios.get('/api/me')
        commit('auth/SET_USER', user.data)
      } catch (e) {
        // token invalid — silently ignore
      }
    }
  }
}
```

**Accessing the store from components:**

```vue
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

---

## 11. Data Fetching

Nuxt 2 provides two special hooks for server-side data fetching: `asyncData` and `fetch`. Both are page-component-only (not available in regular components).

### `asyncData` (all Nuxt 2 versions)

Runs **before** the component is instantiated — `this` is unavailable. The returned plain object is merged into the component's `data`. Runs on the server for SSR, and on the client during client-side navigation.

```vue
<script>
export default {
  async asyncData({ $axios, params, error }) {
    try {
      const { data } = await $axios.get(`/api/users/${params.id}`)
      return { user: data }       // merged into component data
    } catch (e) {
      error({ statusCode: 404, message: 'User not found' })
    }
  },

  data() {
    return {
      user: null   // default — overwritten by asyncData return
    }
  }
}
</script>
```

### `fetch` hook (Nuxt 2.12+)

Unlike `asyncData`, the `fetch` hook **has access to `this`**, can access the store, and exposes `$fetchState` for managing loading/error UI. It runs after the component instance is created.

```vue
<template>
  <div>
    <p v-if="$fetchState.pending">Loading...</p>
    <p v-else-if="$fetchState.error">Error: {{ $fetchState.error.message }}</p>
    <ul v-else>
      <li v-for="post in posts" :key="post.id">{{ post.title }}</li>
    </ul>
    <button @click="$fetch">Refresh</button>
  </div>
</template>

<script>
export default {
  data() {
    return {
      posts: []
    }
  },

  async fetch() {
    const { data } = await this.$axios.get('/api/posts')
    this.posts = data
  },

  // Optional: re-fetch when component is kept alive and revisited
  fetchOnServer: true,   // default true
  fetchDelay: 200        // minimum ms to show loading state
}
</script>
```

### Client-only fetching

Use `mounted()` for data that should only load in the browser (e.g., user-specific data that must not be SSR'd):

```vue
<script>
export default {
  data() {
    return { profile: null, loading: false }
  },

  async mounted() {
    this.loading = true
    try {
      const { data } = await this.$axios.get('/api/profile')
      this.profile = data
    } finally {
      this.loading = false
    }
  }
}
</script>
```

### `asyncData` vs `fetch` — key differences

| | `asyncData` | `fetch` (2.12+) |
|---|---|---|
| `this` available | No | Yes |
| Blocks navigation | Yes (page waits) | No (renders immediately, then fills in) |
| Available in child components | No | Yes (2.12+ child fetch support) |
| `$fetchState` UI helpers | No | Yes |
| Merges into `data()` | Yes (returned object) | No (set `this.x` directly) |

---

## 12. Styling

**Scoped styles:** Add `scoped` to the `<style>` tag. Vue adds a unique data attribute to the component's elements and scopes CSS selectors to it.

```vue
<style scoped>
.button {
  background: blue;   /* Only affects .button inside THIS component */
}

/* Deep selector — reaches into child component DOM */
.button >>> .icon { color: white; }
/* Or the /deep/ alias: */
.button /deep/ .icon { color: white; }
/* Or ::v-deep (Vue 2.6+): */
.button ::v-deep .icon { color: white; }
</style>
```

**CSS Modules:** Use `<style module>` to opt in to CSS Modules. Classes are accessed as `$style.className`:

```vue
<template>
  <button :class="$style.primary">Click</button>
</template>

<style module>
.primary { background: blue; color: white; }
</style>
```

**Global styles:** Declare in `nuxt.config.js` under the `css` key; these are injected globally:

```js
// nuxt.config.js
export default {
  css: [
    '~/assets/styles/main.scss',
    'normalize.css'
  ]
}
```

**SCSS / preprocessors:** Install `node-sass` (or `sass`) and `sass-loader`. Nuxt will automatically use them for `.scss` files and `<style lang="scss">` blocks. For globally available SCSS variables/mixins without importing per-file, use `@nuxtjs/style-resources`:

```js
// nuxt.config.js
export default {
  buildModules: ['@nuxtjs/style-resources'],
  styleResources: {
    scss: ['~/assets/styles/_variables.scss', '~/assets/styles/_mixins.scss']
  }
}
```

**Dynamic / conditional styles:**

```vue
<template>
  <!-- Object syntax -->
  <div :class="{ active: isActive, 'text-danger': hasError }">...</div>

  <!-- Array syntax -->
  <div :class="[baseClass, isActive ? 'active' : '']">...</div>

  <!-- Inline style binding -->
  <div :style="{ color: textColor, fontSize: `${size}px` }">...</div>
</template>
```

---

## 13. Forms & User Input

**`v-model` on native inputs:**

```vue
<template>
  <form @submit.prevent="submit">
    <input v-model="form.email" type="email" />
    <input v-model.trim="form.name" type="text" />
    <input v-model.number="form.age" type="number" />
    <select v-model="form.role">
      <option value="admin">Admin</option>
      <option value="user">User</option>
    </select>
    <textarea v-model="form.bio" />
    <input v-model="form.agree" type="checkbox" />
    <button type="submit">Submit</button>
  </form>
</template>

<script>
export default {
  data() {
    return {
      form: {
        email: '',
        name: '',
        age: null,
        role: 'user',
        bio: '',
        agree: false
      }
    }
  },

  methods: {
    submit() {
      console.log(this.form)
    }
  }
}
</script>
```

**Common `v-model` modifiers:** `.trim` (trims whitespace), `.number` (coerces to Number), `.lazy` (syncs on `change` instead of `input`).

**Manual validation pattern (without library):**

```vue
<script>
export default {
  data() {
    return {
      form: { email: '' },
      errors: {}
    }
  },

  methods: {
    validate() {
      this.errors = {}
      if (!this.form.email.includes('@')) {
        this.errors.email = 'Invalid email address'
      }
      return Object.keys(this.errors).length === 0
    },

    submit() {
      if (!this.validate()) return
      // proceed
    }
  }
}
</script>
```

**Common form libraries for Nuxt 2:**
- **Vee-Validate v3** — template-based validation using a `ValidationProvider` / `ValidationObserver` component API (v3 is the Vue 2 compatible version; v4 targets Vue 3).
- **Vuelidate** — model-based validation defined as a `validations` option on the component.

---

## 14. Slots & Content Projection

**Default slot:**

```vue
<!-- BaseCard.vue -->
<template>
  <div class="card">
    <slot />   <!-- default slot — replaced by whatever the parent passes -->
  </div>
</template>

<!-- Parent usage -->
<template>
  <BaseCard>
    <p>This content goes into the slot.</p>
  </BaseCard>
</template>
```

**Named slots:**

```vue
<!-- AppModal.vue -->
<template>
  <div class="modal">
    <header>
      <slot name="header" />
    </header>
    <section>
      <slot />
    </section>
    <footer>
      <slot name="footer">
        <!-- Fallback content if parent doesn't fill the slot -->
        <button>Close</button>
      </slot>
    </footer>
  </div>
</template>

<!-- Parent usage (Vue 2.6+ v-slot syntax) -->
<template>
  <AppModal>
    <template v-slot:header>
      <h2>Confirm Action</h2>
    </template>

    <p>Are you sure you want to delete this item?</p>

    <template v-slot:footer>
      <button @click="confirm">Yes</button>
      <button @click="cancel">No</button>
    </template>
  </AppModal>
</template>
```

**Shorthand:** `v-slot:header` can be written `#header`.

**Scoped slots:** Allow the child to pass data up to the parent's slot content:

```vue
<!-- DataTable.vue — child exposes row data to parent -->
<template>
  <table>
    <tr v-for="row in rows" :key="row.id">
      <slot name="row" :row="row" :index="index" />
    </tr>
  </table>
</template>

<!-- Parent — receives row data from child -->
<template>
  <DataTable :rows="users">
    <template #row="{ row }">
      <td>{{ row.name }}</td>
      <td>{{ row.email }}</td>
    </template>
  </DataTable>
</template>
```

**`$slots` and `$scopedSlots`:** Accessible programmatically on the component instance. In Vue 2, `$slots` holds non-scoped VNodes; `$scopedSlots` holds functions for scoped slots. [VERIFY: In Vue 2.6+, all slots are unified under `$scopedSlots`; `$slots` remains for backwards compatibility but `$scopedSlots` is the canonical API.]

---

## 15. Plugins & Middleware

### Plugins

Plugins in `plugins/` are executed once when the Nuxt application boots. They receive the **context** object and can inject properties into the Vue instance, the store, and the Nuxt context.

```js
// plugins/api.js
import axios from 'axios'

export default function ({ $config, store }, inject) {
  const api = axios.create({
    baseURL: $config.apiBaseUrl,
    headers: { 'Content-Type': 'application/json' }
  })

  // Intercept to attach auth token
  api.interceptors.request.use(config => {
    const token = store.state.auth.token
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
  })

  // inject makes $api available as:
  // - this.$api in components
  // - context.$api in asyncData/fetch/middleware
  // - store.$api in Vuex actions (via this.$api)
  inject('api', api)
}
```

```js
// nuxt.config.js
export default {
  plugins: [
    '~/plugins/api.js',
    { src: '~/plugins/chart.js', mode: 'client' },   // client-only
    { src: '~/plugins/ssr-utils.js', mode: 'server' } // server-only
  ]
}
```

**`mode: 'client'` vs `mode: 'server'`:** Use `mode: 'client'` for plugins that rely on browser APIs. Older Nuxt 2 docs use a `.client.js` or `.server.js` filename suffix as an equivalent convention [VERIFY: both the `mode` property and the filename suffix convention are supported; the suffix approach may have been introduced before the `mode` option existed in earlier 2.x releases].

**`inject(name, value)`:** Injects `value` as `this.$name` on every Vue component, `context.$name` in Nuxt context hooks, and `this.$name` in Vuex actions.

### Route Middleware

Middleware functions run before a route is rendered. They receive the Nuxt context object.

```js
// middleware/require-admin.js
export default function ({ store, redirect, route }) {
  if (!store.getters['auth/isAdmin']) {
    redirect({ name: 'index', query: { from: route.fullPath } })
  }
}
```

**Assigning middleware:**

```vue
<!-- Page-level -->
<script>
export default {
  middleware: ['auth', 'require-admin']
}
</script>
```

```js
// Global — nuxt.config.js
export default {
  router: {
    middleware: ['auth']
  }
}
```

**Middleware execution order:** Global (nuxt.config) → Layout → Page.

---

## 16. Build & Configuration

**Build tool:** webpack 4 (Nuxt 2 does not support Vite natively; several community modules attempted Vite integration but it was not stable or official). [VERIFY: `nuxt-vite` was an experimental community module; it is not the standard Nuxt 2 toolchain.]

**`nuxt.config.js` — key shape:**

```js
// nuxt.config.js
export default {
  // Rendering mode
  ssr: true,                // true = SSR/universal; false = SPA. Replaces deprecated `mode` key in 2.13+
  // mode: 'universal',    // Legacy equivalent of ssr: true

  // HTML head defaults (vue-meta)
  head: {
    title: 'My App',
    meta: [
      { charset: 'utf-8' },
      { name: 'viewport', content: 'width=device-width, initial-scale=1' }
    ],
    link: [
      { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' }
    ]
  },

  // Global CSS
  css: ['~/assets/styles/main.scss'],

  // Plugins
  plugins: ['~/plugins/axios.js'],

  // Auto-import components (2.13+)
  components: true,

  // Modules that run at build time only (no runtime cost)
  buildModules: [
    '@nuxt/typescript-build',
    '@nuxtjs/tailwindcss',
    '@nuxtjs/style-resources'
  ],

  // Modules that run at runtime (add server middleware, etc.)
  modules: [
    '@nuxtjs/axios',
    '@nuxtjs/auth-next',
    '@nuxtjs/i18n'
  ],

  // @nuxtjs/axios config
  axios: {
    baseURL: process.env.API_BASE_URL || 'http://localhost:8000'
  },

  // Runtime config (Nuxt 2.13+)
  publicRuntimeConfig: {
    apiBaseUrl: process.env.API_BASE_URL   // exposed to client + server
  },
  privateRuntimeConfig: {
    apiSecret: process.env.API_SECRET      // server-only
  },

  // Router customization
  router: {
    middleware: ['auth'],
    extendRoutes(routes, resolve) {
      routes.push({
        name: 'custom-404',
        path: '*',
        component: resolve(__dirname, 'pages/404.vue')
      })
    }
  },

  // Build config
  build: {
    // Extend webpack config
    extend(config, { isDev, isClient }) {
      if (isDev && isClient) {
        config.module.rules.push({
          enforce: 'pre',
          test: /\.(js|vue)$/,
          loader: 'eslint-loader',
          exclude: /(node_modules)/
        })
      }
    },
    transpile: ['some-esm-package']
  }
}
```

**Environment variables:**

- `process.env.VAR_NAME` works at build time for values baked into the bundle.
- `publicRuntimeConfig` / `privateRuntimeConfig` (Nuxt 2.13+): Values are evaluated at server start, not build time. Preferred for containerized deployments where env vars change between environments without rebuilding.
- `@nuxtjs/dotenv` was common pre-2.13 to load `.env` into `process.env`. Post-2.13 the runtime config approach is idiomatic.

**Build output:**
- `nuxt build` → `.nuxt/` + `server/` directories (Node.js server for SSR).
- `nuxt generate` → `dist/` directory of static HTML files.
- `nuxt start` → starts the production SSR server (requires prior `nuxt build`).

---

## 17. SSR Considerations

**`process.server` and `process.client`:** Webpack replaces these at compile time. Use them to guard code that must not run in the wrong environment:

```vue
<script>
export default {
  created() {
    if (process.client) {
      // safe to access localStorage, window, etc.
      const saved = localStorage.getItem('draft')
    }

    if (process.server) {
      // only runs during SSR; req/res accessible via asyncData context
    }
  }
}
</script>
```

**`<client-only>` component:** Wraps components that must not be rendered on the server. The slot content is rendered client-side only after hydration:

```vue
<template>
  <div>
    <p>This part is SSR'd normally.</p>

    <client-only>
      <!-- Charts, maps, or anything that calls window APIs -->
      <ClientSideChart :data="chartData" />

      <template #placeholder>
        <!-- Optional: shown server-side and during hydration -->
        <p>Loading chart...</p>
      </template>
    </client-only>
  </div>
</template>
```

**Context object:** `asyncData`, `fetch` (in some variants), middleware, plugins, and `nuxtServerInit` receive a context object with:

| Property | Description |
|---|---|
| `app` | Vue app instance |
| `store` | Vuex store |
| `route` | Current vue-router route |
| `params` | Route params shorthand |
| `query` | Route query shorthand |
| `req` | Node.js `http.IncomingMessage` (server only) |
| `res` | Node.js `http.ServerResponse` (server only) |
| `redirect(location)` | Redirect function |
| `error(params)` | Trigger error page |
| `$axios` | If @nuxtjs/axios is installed |
| `$config` | Runtime config (2.13+) |

**Hydration mismatches:** If the HTML rendered on the server differs from what Vue renders on the client during hydration, Vue will silently patch the DOM (in development, a warning is logged). Common causes:
- Accessing `Date.now()`, `Math.random()`, or user-specific data during `created()` without guarding with `process.client`.
- Rendering different markup based on a browser cookie or `localStorage` value that the server cannot read.
- Using `v-if="mounted"` patterns to defer rendering — set the flag in `mounted()` so the server renders the `false` branch.

**`window is not defined` errors:** The most common Nuxt 2 SSR error. Third-party libraries that call `window` at import time must be:
1. Wrapped in `<client-only>`
2. Loaded via a `mode: 'client'` plugin
3. Lazily imported inside `mounted()` or a `process.client` guard

---

## 18. Key Conventions & Gotchas

**`nuxt-link` vs `<NuxtLink>`:** Both resolve to vue-router's `<RouterLink>`. `nuxt-link` (kebab-case HTML element) is the historically documented form in Nuxt 2 docs; `<NuxtLink>` (PascalCase) also works and is more consistent with Vue 3 / Nuxt 3 naming. Use either, but be consistent within a codebase. [VERIFY: exact version in which `<NuxtLink>` PascalCase was officially registered as an alias in Nuxt 2.]

**`<nuxt />` vs `<Nuxt />`:** Same situation — both are valid in Nuxt 2 for the page outlet inside layouts. The capital form aligns with Nuxt 3.

**`mode: 'universal'` / `mode: 'spa'` deprecation:** In Nuxt 2.13+, the `mode` key was soft-deprecated in favor of `ssr: true` / `ssr: false`. Both still work in 2.15 but new projects should use `ssr`. [VERIFY: the deprecation timeline across 2.x point releases.]

**Store state as factory function:** `export const state = () => ({})` — the arrow function form prevents state from being shared across server requests. Using `export const state = {}` (plain object) is a silent SSR bug where all concurrent requests share the same state object.

**`asyncData` has no `this`:** A common mistake is trying to call `this.$axios` or `this.$store` inside `asyncData`. Use the destructured context argument instead: `asyncData({ $axios, store })`.

**`_` prefix for dynamic routes:** `pages/users/_id.vue` becomes `/users/:id`. The underscore is purely a Nuxt file naming convention — it has no meaning at runtime beyond route generation.

**`_.vue` catch-all:** A file named `_.vue` (just an underscore) in a directory catches all unmatched sub-paths. Use it for custom 404 pages within a section.

**`@nuxtjs/axios` vs raw `axios`:** Nuxt 2 projects almost universally use `@nuxtjs/axios`, which integrates the Axios instance into the Nuxt context (`$axios`) and Vue components (`this.$axios`). It also handles proxy, retry, and auth token injection via `@nuxtjs/auth-next`. Using raw `axios` without the module means manually wiring up interceptors and context injection.

**`head()` method for per-page SEO:** Nuxt 2 uses `vue-meta` under the hood. Pages (and layouts) can export a `head()` method or object to set `<title>`, `<meta>`, etc.:

```vue
<script>
export default {
  head() {
    return {
      title: `User ${this.user.name} — My App`,
      meta: [
        {
          hid: 'description',
          name: 'description',
          content: this.user.bio
        }
      ]
    }
  }
}
</script>
```

The `hid` key prevents duplicate meta tags when parent and child both define the same meta name.

**`$nuxt` global:** `window.$nuxt` is available in the browser as a bridge to the Nuxt app. `$nuxt.refresh()` re-runs `asyncData` and `fetch` for the current page. Useful for debugging, rarely used in production code.

**Vuex modules — classic vs namespaced:** Nuxt 2's auto-discovered store files are always namespaced. Accessing them requires the module name prefix: `store.commit('cart/ADD_ITEM')`, not `store.commit('ADD_ITEM')`.

**`generate.routes`:** For dynamic routes under `nuxt generate`, Nuxt cannot auto-detect which param values exist. You must declare them in `nuxt.config.js`:

```js
// nuxt.config.js
export default {
  generate: {
    async routes() {
      const { data } = await axios.get('https://api.example.com/users')
      return data.map(user => `/users/${user.id}`)
    }
  }
}
```

---

## 19. Ecosystem & Common Libraries

| Concern | Typical Library | Notes |
|---|---|---|
| State management | `vuex` (v3) | Auto-integrated by Nuxt 2; v4 is Vue 3 only |
| HTTP client | `@nuxtjs/axios` | Wraps axios; injects `$axios` into context and components |
| Authentication | `@nuxtjs/auth-next` | Token/cookie auth with Vuex integration; pairs with `@nuxtjs/axios` |
| Forms validation | `vee-validate` (v3) or `vuelidate` | vee-validate v4+ targets Vue 3; use v3.x for Nuxt 2 |
| UI component library | Vuetify 2.x, Buefy, Element UI, Ant Design Vue 1.x | Vuetify 3 targets Vue 3; use Vuetify 2.x for Nuxt 2 |
| CSS framework | `@nuxtjs/tailwindcss` | Integrates Tailwind CSS 2.x/3.x via PostCSS |
| Internationalization | `@nuxtjs/i18n` (v7.x) | File-based locale loading, lazy imports, SEO meta |
| SEO / head management | `vue-meta` (v2) | Built into Nuxt 2 — use the `head()` option; no separate install |
| Testing (unit) | `@vue/test-utils` (v1) + `jest` | v1 targets Vue 2; v2 targets Vue 3 |
| Testing (e2e) | Cypress or Playwright | No Nuxt-specific integration needed |
| SCSS globals | `@nuxtjs/style-resources` | Auto-injects SCSS variables/mixins into every SFC |
| SVG handling | `@nuxtjs/svg` or `vue-svg-loader` | Inline SVG import as Vue component |
| PWA | `@nuxt/pwa` | Service worker, manifest, offline support |
| Image optimization | `@nuxt/image` | `<nuxt-img>` / `<nuxt-picture>` components with lazy loading |
| Analytics | `@nuxtjs/google-analytics` or `vue-gtag` | Client-only plugin pattern |
| Error tracking | Sentry via `@nuxtjs/sentry` | SSR-aware; captures both server and client errors |

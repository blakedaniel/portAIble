# Prompt Bank

Curated markdown documents that get spliced into the assembled prompt when their language / framework / src→dst pair appears in a session's confirmed profiles.

## Layout

```
prompt-bank/
├── languages/{slug}.md         # e.g. python.md, typescript.md
├── frameworks/{slug}.md        # e.g. django.md, springboot.md, nuxt.md
└── transitions/{src}-{dst}.md  # e.g. django-springboot.md, nuxt2-nuxt4.md
```

Slug rules: lowercase, alphanumeric only, no spaces or dots. Lookup applies the same normalization (`Spring Boot 3.5` → `springboot`, `Nuxt 2` → `nuxt2`) — keep filenames terse.

## Document structure

Each doc is freeform markdown but should follow these section headers when applicable:

```md
# <Subject>

## Critical Caveats
Things that will silently break a port if overlooked. Highest priority.

## Common Pitfalls
Frequent mistakes that compile but misbehave.

## Idiomatic Patterns
The "right way" to express common shapes in this language/framework.

## Cross-references
Links to related transition or framework docs in this bank.
```

The `Build Prompt` use case concatenates these documents under labeled sections — keep them focused; verbosity dilutes signal.

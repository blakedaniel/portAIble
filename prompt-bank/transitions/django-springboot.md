# Django → Spring Boot

## Critical Caveats

- **ORM semantics differ.** Django's lazy querysets ↔ Spring Data JPA returns concrete collections by default. Wrap large fetches with pagination (`Pageable`) or streaming queries to preserve memory profile.
- **Auth model.** Django bundles `auth.User` + sessions + CSRF; Spring Boot expects you to choose (Spring Security + JWT, or session-based). Don't try to mirror Django's `User` table 1:1; map to JPA entities and use Spring Security's `UserDetails`.
- **URL → routing.** `urls.py` regex/path patterns become `@RequestMapping` / `@GetMapping` annotations on controllers. Capture groups become `@PathVariable`.
- **Migrations.** Django's `migrations/` history does not translate. Use Flyway or Liquibase from a clean baseline; do NOT try to replay Django migration files.

## Component mapping

| Django | Spring Boot |
|---|---|
| `models.Model` subclass | `@Entity` + JPA annotations |
| `Manager` / queryset | `JpaRepository` + derived queries |
| Function/class view | `@RestController` method |
| DRF serializer | DTO + MapStruct (or manual mapping) |
| `Form` / `ModelForm` | DTO with `jakarta.validation` constraints |
| `urls.py` | `@RequestMapping` on controllers |
| `settings.py` | `application.yml` + `@ConfigurationProperties` |
| Middleware | Servlet `Filter` or `OncePerRequestFilter` |
| Signals (`post_save`) | Spring `ApplicationEventPublisher` + `@EventListener` |
| `manage.py` commands | `CommandLineRunner` beans or Spring Shell |
| `tests/test_*.py` | `@SpringBootTest` / `@DataJpaTest` / `@WebMvcTest` |

## Common Pitfalls

- Translating Django admin auto-CRUD: there is no equivalent. Either ship a separate admin UI or use a generator (e.g. JHipster) — don't try to recreate the admin from scratch.
- Many-to-many through-tables: Django's implicit `through` becomes an explicit `@Entity` join table in JPA. Forgetting this strips the relation.
- Ignoring the build tool choice early — Maven (`pom.xml`) and Gradle (`build.gradle.kts`) generate very different project layouts and CI configs.

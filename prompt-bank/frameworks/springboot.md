# Spring Boot

## Critical Caveats

- **Spring Boot 3.x requires Jakarta EE namespaces** (`jakarta.persistence.*`, `jakarta.servlet.*`) — not `javax.*`. Mixing is a compile-time fail.
- **Component scanning is package-scoped from the `@SpringBootApplication` class.** Beans outside that package tree are invisible without explicit `@ComponentScan`.
- **`application.yml` profiles** (`spring.profiles.active`) toggle whole sets of config — port equivalent of Django settings splits.

## Common Pitfalls

- `@Transactional` on private methods is silently ignored — the proxy can't intercept self-calls.
- Field injection (`@Autowired` on a field) hides cyclic dependencies until startup; prefer constructor injection.
- `@RequestParam` vs `@PathVariable` vs `@RequestBody` — wrong choice often only fails at runtime with a confusing 400.

## Idiomatic Patterns

- Layered packaging: `controller/`, `service/`, `repository/`, `entity/`, `dto/`, `config/`.
- Spring Data JPA: extend `JpaRepository<Entity, ID>`; query derivation from method names; `@Query` for custom JPQL.
- DTOs separate from entities; map with MapStruct or manual constructors. Don't expose entities directly through controllers.
- Exception handling via `@RestControllerAdvice` + `@ExceptionHandler`.

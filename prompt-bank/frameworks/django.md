# Django

## Critical Caveats

- **App layout is settings-driven.** `INSTALLED_APPS` and `urls.py` wiring is implicit and easy to miss when reading a single app — trace from `settings.py` first.
- **Database migrations live in version control.** When porting, treat `app/migrations/*.py` as authoritative for schema even if models drift.
- **Middleware order matters.** Authentication, sessions, and CSRF stacks are sequential; reordering changes behavior.

## Common Pitfalls

- Signals (`post_save`, `pre_delete`) act as hidden coupling; grep `@receiver` and `connect(` before assuming a model write has no side effects.
- Class-based vs function-based views differ in mixin handling — don't blindly translate `as_view()` semantics.
- The Django ORM's lazy querysets evaluate on iteration; equivalent ports must preserve the lazy/eager boundary or N+1 issues will silently appear.

## Idiomatic Patterns

- Apps are vertical slices: `models.py`, `views.py`, `urls.py`, `forms.py`, `admin.py` per app.
- DRF (Django REST Framework) for APIs: `serializers.py` + `viewsets.py` + `routers.DefaultRouter()`.
- Settings split with `base.py` / `dev.py` / `prod.py` and `DJANGO_SETTINGS_MODULE` env var.

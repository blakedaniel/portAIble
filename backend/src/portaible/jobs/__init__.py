"""Background job machinery — backed by SQLite (jobs table) for restart-survivability."""

from .registry import JobRegistry

__all__ = ["JobRegistry"]

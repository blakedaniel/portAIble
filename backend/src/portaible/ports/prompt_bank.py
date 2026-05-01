"""PromptBankPort — looks up curated markdown context by language/framework/transition."""

from __future__ import annotations

from abc import ABC, abstractmethod


class PromptBankPort(ABC):
    @abstractmethod
    def fetch_language_doc(self, name: str) -> str | None:
        ...

    @abstractmethod
    def fetch_framework_doc(self, name: str) -> str | None:
        ...

    @abstractmethod
    def fetch_transition_doc(self, src_framework: str, dst_framework: str) -> str | None:
        ...

    @abstractmethod
    def index(self) -> dict[str, list[str]]:
        """Return {languages: [...], frameworks: [...], transitions: [...]} for UI hints."""
        ...

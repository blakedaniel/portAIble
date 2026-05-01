"""DesignDecisionsPort — generates a per-(src,dst) decision questionnaire."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..domain import DesignDecision, DestinationProfile, SourceProfile


class DesignDecisionsPort(ABC):
    @abstractmethod
    async def generate(
        self,
        *,
        source: SourceProfile,
        destination: DestinationProfile,
    ) -> list[DesignDecision]:
        ...

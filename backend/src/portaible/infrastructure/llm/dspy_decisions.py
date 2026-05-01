"""DSPy-backed DesignDecisionsPort — generates per-(src,dst) decision questions."""

from __future__ import annotations

import asyncio
import logging

import dspy

from ...config import settings
from ...domain import DesignDecision, DestinationProfile, SourceProfile
from ...ports import DesignDecisionsPort
from .dspy_config import create_dspy_lm
from .signatures import DesignDecisionsSignature

logger = logging.getLogger(__name__)


class DSPyDesignDecisions(DesignDecisionsPort):
    def __init__(self, model: str | None = None):
        self.model = model or settings.design_decisions_model

    async def generate(
        self,
        *,
        source: SourceProfile,
        destination: DestinationProfile,
    ) -> list[DesignDecision]:
        lm = create_dspy_lm(settings, model_override=self.model)
        module = dspy.Predict(DesignDecisionsSignature)

        def _run():
            with dspy.context(lm=lm):
                return module(
                    source_profile_json=source.model_dump_json(),
                    destination_profile_json=destination.model_dump_json(),
                )

        logger.info("[decisions] generate model=%s", self.model)
        pred = await asyncio.to_thread(_run)
        decisions = list(getattr(pred, "decisions", []) or [])
        logger.info("[decisions] generated %d decision(s)", len(decisions))
        return decisions

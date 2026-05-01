"""Pure domain entities — no I/O, no infrastructure imports."""

from .design_decision import DecisionAnswer, DecisionOption, DesignDecision
from .destination_profile import DestinationProfile
from .pipeline_job import PipelineJob, PipelineJobStatus
from .prompt import AssembledPrompt
from .session import (
    ExtractionKind,
    IllegalTransitionError,
    Session,
    SessionStatus,
)
from .source_profile import FrameworkEntry, LanguageEntry, PackageEntry, SourceProfile

__all__ = [
    "AssembledPrompt",
    "DecisionAnswer",
    "DecisionOption",
    "DesignDecision",
    "DestinationProfile",
    "ExtractionKind",
    "FrameworkEntry",
    "IllegalTransitionError",
    "LanguageEntry",
    "PackageEntry",
    "PipelineJob",
    "PipelineJobStatus",
    "Session",
    "SessionStatus",
    "SourceProfile",
]

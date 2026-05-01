"""DSPy Signatures — structured-output specs for portAIble LLM calls.

Pattern mirrors local-chat-agent/src/local_chat_agent/agent/signatures.py:
Pydantic-typed input/output fields, validation at the boundary.
"""

from __future__ import annotations

import dspy
from pydantic import BaseModel

from ...domain import (
    DesignDecision,
    FrameworkEntry,
    LanguageEntry,
    PackageEntry,
)


class FileSnippet(BaseModel):
    """A bounded slice of a source file shown to the analyzer."""

    path: str
    content: str


class SourceProfileSignature(dspy.Signature):
    """Analyze the provided source code listing and contents and produce a structured
    profile of languages, frameworks, packages, and notes a porting engineer must know.

    Be conservative with versions — only assert a version if the file evidence shows it
    (manifests like requirements.txt, package.json, pom.xml, build.gradle). Otherwise
    leave the version field as null. For each notable package, propose 1-3 idiomatic
    alternatives in widely-used porting targets."""

    file_listing: str = dspy.InputField(
        desc="Newline-separated list of relative file paths in the source codebase"
    )
    representative_files: list[FileSnippet] = dspy.InputField(
        desc=(
            "A bounded selection of dependency manifests, build files, and 5-10 "
            "representative source files (each capped in length)."
        )
    )

    languages: list[LanguageEntry] = dspy.OutputField(
        desc="Languages used; include version only when evidenced by manifest/runtime files"
    )
    frameworks: list[FrameworkEntry] = dspy.OutputField(
        desc="Frameworks/major libraries used; include version when evidenced"
    )
    packages: list[PackageEntry] = dspy.OutputField(
        desc="Notable third-party packages with version when known + 1-3 alternatives each"
    )
    important_information: str = dspy.OutputField(
        desc=(
            "Markdown notes covering nontrivial design choices, tight coupling, "
            "deprecated APIs, bespoke patterns, or anything else a porting engineer "
            "MUST know before starting."
        )
    )


class DestinationProfileSuggestionSignature(dspy.Signature):
    """Given a confirmed source profile and an optional user target hint, propose a
    reasonable destination profile (languages, frameworks, packages, target_notes).
    Bias toward mainstream, well-documented destinations unless the hint says otherwise."""

    source_profile_json: str = dspy.InputField(
        desc="JSON-serialized SourceProfile from the confirmed source"
    )
    target_hint: str = dspy.InputField(
        desc="Free-form user hint, e.g. 'Spring Boot 3.5' — empty if no preference"
    )

    languages: list[LanguageEntry] = dspy.OutputField(
        desc="Destination language(s) and version(s)"
    )
    frameworks: list[FrameworkEntry] = dspy.OutputField(
        desc="Destination framework(s) and version(s)"
    )
    packages: list[PackageEntry] = dspy.OutputField(
        desc="Notable destination packages and short list of equivalents"
    )
    target_notes: str = dspy.OutputField(
        desc="Markdown notes explaining destination choices and any caveats"
    )


class DesignDecisionsSignature(dspy.Signature):
    """Given confirmed source and destination profiles, enumerate the design decisions
    a human porting engineer must make BEFORE code generation begins. Focus on
    decisions whose answer materially changes the generated code: ORM choice, auth
    strategy, build tool, dependency injection style, async vs sync, packaging layout,
    test framework, etc. Each question must have 2-5 concrete options. Set
    allow_freeform=true only when answers are genuinely open-ended."""

    source_profile_json: str = dspy.InputField()
    destination_profile_json: str = dspy.InputField()

    decisions: list[DesignDecision] = dspy.OutputField(
        desc=(
            "3-10 decisions. Each: stable id (slug), question, 2-5 options "
            "(each with id+label+description), allow_freeform, rationale."
        )
    )

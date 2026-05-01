"""Use case: assemble the final prompt that ships to the AI Pipeline."""

from __future__ import annotations

import os
import zipfile
from dataclasses import dataclass
from pathlib import Path

from ..config import settings
from ..domain import (
    AssembledPrompt,
    DesignDecision,
    DestinationProfile,
    Session,
    SessionStatus,
    SourceProfile,
)
from ..ports import PromptBankPort, SessionRepositoryPort


def _zip_directory(src_dir: Path, dest_zip: Path) -> Path:
    dest_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest_zip, "w", zipfile.ZIP_DEFLATED) as z:
        for dirpath, _, filenames in os.walk(src_dir):
            for fname in filenames:
                if fname.startswith("._") or fname == ".DS_Store":
                    continue
                full = Path(dirpath) / fname
                z.write(full, full.relative_to(src_dir))
    return dest_zip


def _format_profile(label: str, profile: SourceProfile | DestinationProfile) -> str:
    lines = [f"### {label}"]
    if profile.languages:
        lines.append("**Languages**:")
        for lang in profile.languages:
            v = f" {lang.version}" if lang.version else ""
            lines.append(f"- {lang.name}{v}")
    if profile.frameworks:
        lines.append("**Frameworks**:")
        for fw in profile.frameworks:
            v = f" {fw.version}" if fw.version else ""
            lines.append(f"- {fw.name}{v}")
    if profile.packages:
        lines.append("**Packages**:")
        for pkg in profile.packages:
            v = f" {pkg.version}" if pkg.version else ""
            alts = f" (alternatives: {', '.join(pkg.alternatives)})" if pkg.alternatives else ""
            lines.append(f"- {pkg.name}{v}{alts}")
    notes = getattr(profile, "important_information", None) or getattr(profile, "target_notes", "")
    if notes:
        lines.append("**Notes**:")
        lines.append(notes)
    return "\n".join(lines)


def _format_decisions(
    decisions: list[DesignDecision], answers_by_id: dict[str, str]
) -> str:
    if not decisions:
        return ""
    lines = ["### Design Decisions (answered by user)"]
    for d in decisions:
        ans = answers_by_id.get(d.id, "(unanswered)")
        lines.append(f"- **{d.question}** → {ans}")
    return "\n".join(lines)


@dataclass
class BuildPromptUseCase:
    sessions: SessionRepositoryPort
    bank: PromptBankPort

    async def execute(self, session_id: str, *, allow_skip_decisions: bool = True) -> Session:
        session = await self._require(session_id)
        if session.source_profile is None or session.destination_profile is None:
            raise ValueError("source and destination profiles must be confirmed before build")

        # Zip the workspace src/ for upload to the AI Pipeline.
        src_dir = settings.session_dir(session_id) / "src"
        if not src_dir.is_dir():
            raise FileNotFoundError(f"missing extracted source at {src_dir}")
        zip_path = settings.session_dir(session_id) / "source.zip"
        _zip_directory(src_dir, zip_path)

        instructions = self._compose(session)

        # Persist the assembled prompt as a sidecar text file for inspection.
        (settings.session_dir(session_id) / "assembled-prompt.txt").write_text(
            instructions, encoding="utf-8"
        )

        session.assembled_prompt = AssembledPrompt(
            instructions=instructions,
            source_zip_path=str(zip_path),
        )
        # Allow skipping decisions in early-dev: transition through DECISIONS_ANSWERED if needed.
        if (
            session.status == SessionStatus.DESTINATION_PROFILE_CONFIRMED
            and allow_skip_decisions
            and not session.decision_answers
        ):
            session.transition(SessionStatus.PROMPT_BUILT)
        else:
            if session.status != SessionStatus.DECISIONS_ANSWERED:
                # Try to bridge from confirmed-destination if user answered no decisions.
                pass
            session.transition(SessionStatus.PROMPT_BUILT)

        await self.sessions.save(session)
        return session

    def _compose(self, session: Session) -> str:
        assert session.source_profile is not None and session.destination_profile is not None

        parts: list[str] = []
        parts.append(
            "# Code Porting Brief\n\n"
            "You are porting a codebase from a source stack to a destination stack. "
            "Use the structured profiles, the bundled reference docs, and the answered "
            "design decisions below as your authoritative input. Honor exact framework "
            "versions named in the destination profile."
        )
        parts.append(_format_profile("Source Profile", session.source_profile))
        parts.append(_format_profile("Destination Profile", session.destination_profile))

        # Splice in matching prompt-bank docs.
        parts.append("### Reference Documents")
        seen: set[str] = set()
        for lang in session.source_profile.languages + session.destination_profile.languages:
            doc = self.bank.fetch_language_doc(lang.name)
            if doc and doc not in seen:
                parts.append(f"#### Language: {lang.name}\n\n{doc}")
                seen.add(doc)
        for fw in session.source_profile.frameworks + session.destination_profile.frameworks:
            doc = self.bank.fetch_framework_doc(fw.name)
            if doc and doc not in seen:
                parts.append(f"#### Framework: {fw.name}\n\n{doc}")
                seen.add(doc)
        for src_fw in session.source_profile.frameworks:
            for dst_fw in session.destination_profile.frameworks:
                doc = self.bank.fetch_transition_doc(src_fw.name, dst_fw.name)
                if doc and doc not in seen:
                    parts.append(f"#### Transition: {src_fw.name} → {dst_fw.name}\n\n{doc}")
                    seen.add(doc)

        # Decisions
        answers_by_id: dict[str, str] = {}
        for a in session.decision_answers:
            answers_by_id[a.decision_id] = (
                a.freeform_answer
                or next(
                    (
                        opt.label
                        for d in session.design_decisions
                        if d.id == a.decision_id
                        for opt in d.options
                        if opt.id == a.selected_option_id
                    ),
                    "(unanswered)",
                )
            )
        decision_block = _format_decisions(session.design_decisions, answers_by_id)
        if decision_block:
            parts.append(decision_block)

        parts.append(
            "### Output Expectations\n"
            "Produce a complete, compilable port of the uploaded source. "
            "Do not leave TODOs unless an aspect is genuinely unknowable."
        )
        return "\n\n".join(parts)

    async def _require(self, session_id: str) -> Session:
        session = await self.sessions.get(session_id)
        if session is None:
            raise LookupError(f"session {session_id} not found")
        return session


@dataclass
class UpdatePromptInstructionsUseCase:
    """Replace the assembled prompt's instructions text with a user-edited version.

    The prompt remains locked once the pipeline has accepted it (submitted/completed),
    but stays editable in pipeline_failed so the user can fix-and-retry.
    """

    sessions: SessionRepositoryPort

    async def execute(self, session_id: str, instructions: str) -> Session:
        session = await self.sessions.get(session_id)
        if session is None:
            raise LookupError(f"session {session_id} not found")
        if session.assembled_prompt is None:
            raise ValueError("no assembled prompt to edit — build it first")
        if session.status in {
            SessionStatus.PIPELINE_SUBMITTED,
            SessionStatus.PIPELINE_COMPLETED,
        }:
            raise ValueError("prompt is locked once submitted to the AI Pipeline")
        if not instructions.strip():
            raise ValueError("instructions cannot be empty")
        session.assembled_prompt.instructions = instructions
        await self.sessions.save(session)
        return session

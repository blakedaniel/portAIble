"""Session FSM transition tests."""

from __future__ import annotations

import pytest

from portaible.domain import IllegalTransitionError, Session, SessionStatus


def test_session_starts_created():
    s = Session(id="abc")
    assert s.status == SessionStatus.CREATED


def test_legal_forward_chain():
    s = Session(id="abc")
    for status in [
        SessionStatus.EXTRACTED,
        SessionStatus.ANALYZED,
        SessionStatus.SOURCE_PROFILE_CONFIRMED,
        SessionStatus.DESTINATION_PROFILE_CONFIRMED,
        SessionStatus.DECISIONS_ANSWERED,
        SessionStatus.PROMPT_BUILT,
        SessionStatus.PIPELINE_SUBMITTED,
        SessionStatus.PIPELINE_COMPLETED,
    ]:
        s.transition(status)
        assert s.status == status


def test_illegal_skip_raises():
    s = Session(id="abc")
    with pytest.raises(IllegalTransitionError):
        s.transition(SessionStatus.PIPELINE_COMPLETED)


def test_idempotent_reentry():
    s = Session(id="abc")
    s.transition(SessionStatus.EXTRACTED)
    s.transition(SessionStatus.EXTRACTED)  # no error
    assert s.status == SessionStatus.EXTRACTED


def test_decisions_can_be_skipped_directly_to_prompt_built():
    s = Session(id="abc")
    for status in [
        SessionStatus.EXTRACTED,
        SessionStatus.ANALYZED,
        SessionStatus.SOURCE_PROFILE_CONFIRMED,
        SessionStatus.DESTINATION_PROFILE_CONFIRMED,
        SessionStatus.PROMPT_BUILT,
    ]:
        s.transition(status)
    assert s.status == SessionStatus.PROMPT_BUILT


def test_pipeline_failed_can_retry():
    s = Session(id="abc")
    for status in [
        SessionStatus.EXTRACTED, SessionStatus.ANALYZED,
        SessionStatus.SOURCE_PROFILE_CONFIRMED, SessionStatus.DESTINATION_PROFILE_CONFIRMED,
        SessionStatus.PROMPT_BUILT, SessionStatus.PIPELINE_SUBMITTED, SessionStatus.PIPELINE_FAILED,
    ]:
        s.transition(status)
    s.transition(SessionStatus.PIPELINE_SUBMITTED)
    assert s.status == SessionStatus.PIPELINE_SUBMITTED

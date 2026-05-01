"""FakeDesignDecisions — canned decisions for tests / no-Ollama dev."""

from __future__ import annotations

from ...domain import (
    DecisionOption,
    DesignDecision,
    DestinationProfile,
    SourceProfile,
)
from ...ports import DesignDecisionsPort


class FakeDesignDecisions(DesignDecisionsPort):
    """Returns 3 canned design decisions covering the most common porting choices."""

    async def generate(
        self,
        *,
        source: SourceProfile,
        destination: DestinationProfile,
    ) -> list[DesignDecision]:
        return [
            DesignDecision(
                id="persistence-layer",
                question="Which persistence approach should the destination use?",
                options=[
                    DecisionOption(id="jpa", label="Spring Data JPA",
                                    description="Repository abstraction + entity annotations."),
                    DecisionOption(id="jdbc", label="Spring JDBC Template",
                                    description="Lower-level, explicit SQL."),
                    DecisionOption(id="mybatis", label="MyBatis",
                                    description="SQL-mapper with annotated XML or interfaces."),
                ],
                allow_freeform=False,
                rationale="Materially affects entity layer and query style.",
            ),
            DesignDecision(
                id="auth-strategy",
                question="How should authentication be handled in the destination?",
                options=[
                    DecisionOption(id="spring-security-jwt", label="Spring Security + JWT"),
                    DecisionOption(id="spring-security-session", label="Spring Security session-cookie"),
                    DecisionOption(id="external-oidc", label="External OIDC provider"),
                ],
                allow_freeform=True,
                rationale="Determines filter chain, token storage, and login endpoints.",
            ),
            DesignDecision(
                id="build-tool",
                question="Build tool for the destination project?",
                options=[
                    DecisionOption(id="maven", label="Maven (pom.xml)"),
                    DecisionOption(id="gradle-kts", label="Gradle (Kotlin DSL)"),
                ],
                allow_freeform=False,
                rationale="Shapes the entire on-disk project layout and CI configuration.",
            ),
        ]

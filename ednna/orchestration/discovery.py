from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from .contracts import Capability, SpecialistDescriptor
from .registry import SpecialistRegistry
from ednna.specialists.availability import SpecialistAvailabilityStore


@dataclass(frozen=True)
class CapabilityMatch:
    specialist_id: str
    capability: Capability
    score: float


class CapabilityDiscovery:
    """Deterministic capability discovery over registered specialist metadata."""

    def __init__(
        self,
        registry: SpecialistRegistry,
        availability: SpecialistAvailabilityStore | None = None,
    ) -> None:
        self._registry = registry
        self._availability = availability

    def search(self, query: str, limit: int = 5) -> tuple[CapabilityMatch, ...]:
        query_tokens = self._tokens(query)
        matches: list[CapabilityMatch] = []

        if not query_tokens:
            return ()

        for specialist in self._registry.list_specialists():
            if (
                self._availability is not None
                and not self._availability.is_routable(specialist.specialist_id)
            ):
                continue

            for capability in specialist.capabilities:
                score = self._score(query_tokens, specialist, capability)
                if score > 0:
                    matches.append(
                        CapabilityMatch(
                            specialist_id=specialist.specialist_id,
                            capability=capability,
                            score=score,
                        )
                    )

        matches.sort(key=lambda item: (-item.score, item.capability.name))
        return tuple(matches[:limit])

    @staticmethod
    def _tokens(text: str) -> set[str]:
        normalized = unicodedata.normalize("NFKD", text.lower())
        ascii_text = "".join(char for char in normalized if not unicodedata.combining(char))
        base_tokens = {
            token
            for token in re.findall(r"[a-z0-9]+", ascii_text)
            if len(token) >= 3
        }

        expanded = set(base_tokens)
        for token in base_tokens:
            if len(token) >= 6:
                expanded.add(token[:6])

        return expanded

    def _score(
        self,
        query_tokens: set[str],
        specialist: SpecialistDescriptor,
        capability: Capability,
    ) -> float:
        capability_name_tokens = self._tokens(capability.name.replace(".", " "))
        description_tokens = self._tokens(capability.description)
        specialist_tokens = self._tokens(
            f"{specialist.name} {specialist.domain} {specialist.description}"
        )

        weighted_tokens = (
            (capability_name_tokens, 3.0),
            (description_tokens, 2.0),
            (specialist_tokens, 1.0),
        )

        score = 0.0
        for tokens, weight in weighted_tokens:
            score += len(query_tokens & tokens) * weight

        return score

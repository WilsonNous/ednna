from __future__ import annotations

from dataclasses import dataclass


class ActionNotAuthorizedError(PermissionError):
    pass


@dataclass(frozen=True)
class CapabilityPolicy:
    capability: str
    allow_autonomous_action: bool = False
    requires_human_approval: bool = True


class GovernancePolicyRegistry:
    """Explicit capability policies. Actions are denied by default."""

    def __init__(self) -> None:
        self._policies: dict[str, CapabilityPolicy] = {}

    def register(self, policy: CapabilityPolicy) -> None:
        self._policies[policy.capability] = policy

    def get(self, capability: str) -> CapabilityPolicy:
        return self._policies.get(capability, CapabilityPolicy(capability=capability))

    def assert_action_allowed(self, capability: str) -> None:
        policy = self.get(capability)
        if not policy.allow_autonomous_action:
            raise ActionNotAuthorizedError(
                f"Autonomous action is not authorized for capability '{capability}'"
            )

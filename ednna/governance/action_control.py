from __future__ import annotations

from dataclasses import dataclass

from .approvals import ApprovalStatus, ApprovalStore
from .policies import GovernancePolicyRegistry


class IdempotencyKeyRequiredError(ValueError):
    pass


class HumanApprovalRequiredError(PermissionError):
    pass


@dataclass(frozen=True)
class ActionAuthorization:
    capability: str
    idempotency_key: str
    approval_id: str | None = None


class ActionAuthorizer:
    def __init__(
        self,
        policies: GovernancePolicyRegistry,
        approvals: ApprovalStore,
    ) -> None:
        self._policies = policies
        self._approvals = approvals

    def authorize(self, authorization: ActionAuthorization) -> None:
        if not authorization.idempotency_key.strip():
            raise IdempotencyKeyRequiredError("idempotency_key is required")

        policy = self._policies.get(authorization.capability)

        if policy.allow_autonomous_action:
            return

        if not policy.requires_human_approval:
            raise HumanApprovalRequiredError(
                f"Action is not authorized for capability '{authorization.capability}'"
            )

        if not authorization.approval_id:
            raise HumanApprovalRequiredError(
                f"Human approval is required for capability '{authorization.capability}'"
            )

        approval = self._approvals.get(authorization.approval_id)
        if approval is None or approval.status is not ApprovalStatus.APPROVED:
            raise HumanApprovalRequiredError(
                f"Approval is not valid for capability '{authorization.capability}'"
            )

        if approval.capability != authorization.capability:
            raise HumanApprovalRequiredError(
                "Approval capability does not match requested action"
            )

        if (
            approval.action_idempotency_key is not None
            and approval.action_idempotency_key != authorization.idempotency_key
        ):
            raise HumanApprovalRequiredError(
                "Approval is already bound to another action"
            )

    def bind(self, authorization: ActionAuthorization) -> None:
        policy = self._policies.get(authorization.capability)
        if policy.allow_autonomous_action:
            return

        if policy.requires_human_approval:
            if not authorization.approval_id:
                raise HumanApprovalRequiredError(
                    "Human approval is required before action binding"
                )
            self._approvals.bind_action(
                authorization.approval_id,
                authorization.idempotency_key,
            )

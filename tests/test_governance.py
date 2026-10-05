import pytest

from ednna.governance.policies import (
    ActionNotAuthorizedError,
    CapabilityPolicy,
    GovernancePolicyRegistry,
)


def test_actions_are_denied_by_default():
    policies = GovernancePolicyRegistry()

    with pytest.raises(ActionNotAuthorizedError):
        policies.assert_action_allowed("edi.operation.execute")


def test_explicit_policy_can_allow_autonomous_action():
    policies = GovernancePolicyRegistry()
    policies.register(
        CapabilityPolicy(
            capability="edi.operation.execute",
            allow_autonomous_action=True,
            requires_human_approval=False,
        )
    )

    policies.assert_action_allowed("edi.operation.execute")

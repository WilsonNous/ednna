import pytest

from ednna.identity.authorization import AuthorizationDeniedError, AuthorizationService
from ednna.identity.principal import Principal


def test_query_requires_explicit_permission():
    service = AuthorizationService()
    principal = Principal(
        user_id="wilson",
        tenant_id="netunna",
        permissions=("edi.status.get:query",),
    )

    service.require_query(principal, "edi.status.get")


def test_query_is_denied_without_permission():
    service = AuthorizationService()
    principal = Principal(
        user_id="wilson",
        tenant_id="netunna",
        permissions=(),
    )

    with pytest.raises(AuthorizationDeniedError):
        service.require_query(principal, "edi.status.get")


def test_action_permission_is_separate_from_query_permission():
    service = AuthorizationService()
    principal = Principal(
        user_id="wilson",
        tenant_id="netunna",
        permissions=("edi.operation.execute:query",),
    )

    with pytest.raises(AuthorizationDeniedError):
        service.require_action(principal, "edi.operation.execute")

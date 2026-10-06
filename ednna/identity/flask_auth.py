from __future__ import annotations

from functools import wraps
from typing import Callable, TypeVar

from flask import g, jsonify, request

from .oidc import AuthenticationError, OIDCAuthenticator

F = TypeVar("F", bound=Callable)


def bearer_token() -> str:
    header = request.headers.get("Authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise AuthenticationError("Bearer token is required")
    return token.strip()


def require_auth(authenticator: OIDCAuthenticator):
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapped(*args, **kwargs):
            try:
                g.principal = authenticator.authenticate(bearer_token())
            except AuthenticationError:
                return jsonify({"error": "unauthorized"}), 401
            return func(*args, **kwargs)

        return wrapped  # type: ignore[return-value]

    return decorator

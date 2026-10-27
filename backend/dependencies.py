"""FastAPI dependencies shared by the routers."""

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from services import user_service
from utils import security
from utils.exceptions import NotAuthenticatedError, TokenInvalidError

# auto_error=False so WE decide the error shape (the standard JSON body).
bearer_scheme = HTTPBearer(
    auto_error=False,
    description="Paste the access_token returned by POST /api/auth/login",
)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    """Protects a route: needs 'Authorization: Bearer <jwt>' and returns the user.

    Authentication = proving who you are. Checks, in order:
      1. a Bearer token was sent                      -> else 401 not_authenticated
      2. signature valid, not expired, right claims   -> else 401 token_expired / invalid_token
      3. the user still exists in the database        -> else 401 invalid_token
    The role is read from the database, not from the token, so a role change
    or deleted account takes effect immediately.
    """
    if credentials is None or not credentials.credentials:
        raise NotAuthenticatedError(
            "Authentication required. Send 'Authorization: Bearer <token>'."
        )

    payload = security.decode_access_token(credentials.credentials)

    user = user_service.get_user_by_id(payload["sub"])
    if user is None:
        raise TokenInvalidError("Invalid access token.")
    return user

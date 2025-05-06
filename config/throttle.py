# config/throttle.py

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def rate_limit_key(request: Request) -> str:
    """
    Si viene un usuario autenticado (Django), usa su user.id;
    si no, la IP remota.
    """
    user = getattr(request.state, "user", None) or request.scope.get("user")
    if user and getattr(user, "is_authenticated", False):
        return str(user.id)
    return get_remote_address(request)

# Creamos un singleton Limiter
limiter = Limiter(key_func=rate_limit_key)

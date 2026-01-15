"""
General utilities for the application
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import jwt
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.config import security_settings

# Template directory for email templates
APP_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = APP_DIR / "templates"

# URL-safe token serializers
_verification_serializer = URLSafeTimedSerializer(security_settings.JWT_SECRET)
_password_reset_serializer = URLSafeTimedSerializer(
    security_settings.JWT_SECRET,
    salt="password-reset"
)
_review_serializer = URLSafeTimedSerializer(
    security_settings.JWT_SECRET,
    salt="review"
)

# Reexportar funciones de core.security para compatibilidad
from app.core.security import (
    create_access_token,
    verify_token,
    hash_password,
    verify_password,
    get_password_context,
    oauth2_scheme
)

__all__ = [
    'create_access_token',
    'verify_token', 
    'hash_password',
    'verify_password',
    'get_password_context',
    'oauth2_scheme',
    'generate_access_token',
    'decode_access_token',
]


def generate_access_token(
    data: dict,
    expiry: timedelta = timedelta(days=7),
) -> str:
    """
    Generate a JWT access token with JTI for blacklisting.
    This is the new token generation function used by Section 16.
    """
    return jwt.encode(
        payload={
            **data,
            "jti": str(uuid4()),
            "exp": datetime.now(timezone.utc) + expiry,
        },
        algorithm=security_settings.JWT_ALGORITHM,
        key=security_settings.JWT_SECRET,
    )


def decode_access_token(token: str) -> dict | None:
    """
    Decode and validate a JWT access token.
    This is the new token decoding function used by Section 16.
    """
    try:
        return jwt.decode(
            jwt=token,
            key=security_settings.JWT_SECRET,
            algorithms=[security_settings.JWT_ALGORITHM],
        )
    except jwt.PyJWTError:
        return None


# URL-safe token utilities for email verification and password reset
def generate_url_safe_token(
    data: dict, 
    salt: str | None = None,
    expiry: timedelta | None = None
) -> str:
    """
    Generate a URL-safe token for email verification, password reset, or review links.
    
    Uses itsdangerous for URL-safe serialization (safe for use in URLs/emails).
    Different from JWT tokens which are used for authentication.
    
    Args:
        data: Dictionary to encode in token (typically contains user ID)
        salt: Optional salt to use different serializer (e.g., "password-reset", "review")
        expiry: Optional timedelta for expiration (default: 7 days)
        
    Returns:
        URL-safe token string
    """
    # Select serializer based on salt
    if salt == "password-reset":
        serializer = _password_reset_serializer
    elif salt == "review":
        serializer = _review_serializer
    else:
        serializer = _verification_serializer
    
    # If expiry is provided, encode it in the data
    if expiry:
        # itsdangerous URLSafeTimedSerializer handles expiry via max_age in loads
        # We'll pass expiry as max_age when decoding
        return serializer.dumps(data)
    else:
        return serializer.dumps(data)


def decode_url_safe_token(
    token: str, 
    salt: str | None = None,
    expiry: timedelta | None = None,
    max_age_days: int = 7,  # Deprecated: use expiry instead
) -> dict | None:
    """
    Decode a URL-safe token for email verification, password reset, or review.
    
    Args:
        token: URL-safe token string
        salt: Optional salt to use different serializer (e.g., "password-reset", "review")
        expiry: Optional timedelta for expiration (overrides max_age_days)
        max_age_days: Maximum age of token in days (default: 7, deprecated - use expiry)
        
    Returns:
        Decoded data dictionary or None if invalid/expired
    """
    try:
        # Select serializer based on salt
        if salt == "password-reset":
            serializer = _password_reset_serializer
        elif salt == "review":
            serializer = _review_serializer
        else:
            serializer = _verification_serializer
        
        # Use expiry if provided, otherwise use max_age_days
        if expiry is not None:
            max_age_seconds = int(expiry.total_seconds())
        else:
            max_age_seconds = max_age_days * 24 * 60 * 60 if max_age_days else None
        
        return serializer.loads(token, max_age=max_age_seconds)
    except (BadSignature, SignatureExpired):
        return None


# Other general utilities
def generate_random_string(length: int = 10) -> str:
    """Generate a random string"""
    import random
    import string
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

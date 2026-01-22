"""
Security module - Authentication, passwords, JWT, OAuth2 schemes
"""
from datetime import datetime, timedelta
from typing import Optional
import uuid

from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import security_settings


# Centralized configuration via SecuritySettings
SECRET_KEY = security_settings.JWT_SECRET
ALGORITHM = security_settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# Password hashing context
# Note: bcrypt has a 72-byte limit. Passlib will raise ValueError if password exceeds this.
# We handle truncation in _truncate_password() before calling hash/verify.
password_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__ident="2b",  # Use bcrypt 2b format
)


def _truncate_password(password: str) -> str:
    """Truncate password to 71 bytes, ensuring bcrypt compatibility
    
    Note: bcrypt has a 72-byte limit, but some implementations are strict
    and reject passwords that are exactly 72 bytes. We truncate to 71
    bytes to be safe.
    """
    if not isinstance(password, str):
        password = str(password)
    
    # Encode to bytes and truncate if necessary
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 71:
        # Truncate to exactly 71 bytes (safe limit for bcrypt)
        password_bytes = password_bytes[:71]
        # Decode back to string
        try:
            password = password_bytes.decode("utf-8")
        except UnicodeDecodeError:
            # If truncation breaks UTF-8 sequence, decode with error handling
            password = password_bytes.decode("utf-8", errors="ignore")
    
    # Double-check: ensure final encoded length is <= 71
    final_bytes = password.encode("utf-8")
    if len(final_bytes) > 71:
        # This should rarely happen, but truncate again if needed
        password = final_bytes[:71].decode("utf-8", errors="ignore")
    
    return password


# OAuth2 schemes for different user types
oauth2_scheme_seller = OAuth2PasswordBearer(tokenUrl="/seller/token")
oauth2_scheme_partner = OAuth2PasswordBearer(tokenUrl="/partner/token")

# Backward compatibility alias
oauth2_scheme = oauth2_scheme_seller


def hash_password(password: str) -> str:
    """Hash una contraseña, manejando límite de 72 bytes de bcrypt"""
    # Ensure password is a string
    if not isinstance(password, str):
        password = str(password)
    
    # Truncate password to ensure it's <= 72 bytes
    # This MUST happen before passing to password_context.hash()
    # because passlib/bcrypt checks the byte length and raises ValueError if > 72
    password = _truncate_password(password)
    
    # Verify final byte length is safe before calling bcrypt
    final_check = password.encode("utf-8")
    if len(final_check) > 71:
        # Emergency truncation - should never happen, but safety check
        password = final_check[:71].decode("utf-8", errors="ignore")
    
    # Hash using passlib/bcrypt
    # At this point, password is guaranteed to be <= 72 bytes when encoded
    try:
        return password_context.hash(password)
    except ValueError as e:
        if "72 bytes" in str(e) or "longer than" in str(e).lower():
            # Final safety: if somehow we still get the error, truncate and retry
            password_bytes = password.encode("utf-8")[:71]
            password = password_bytes.decode("utf-8", errors="ignore")
            return password_context.hash(password)
        raise


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contraseña contra su hash"""
    # Ensure password is a string
    if not isinstance(plain_password, str):
        plain_password = str(plain_password)
    
    # Truncate password to ensure it's <= 72 bytes
    plain_password = _truncate_password(plain_password)
    
    # Verify final byte length is safe
    final_check = plain_password.encode("utf-8")
    if len(final_check) > 71:
        plain_password = final_check[:71].decode("utf-8", errors="ignore")
    
    # Verify using passlib/bcrypt
    try:
        return password_context.verify(plain_password, hashed_password)
    except ValueError as e:
        if "72 bytes" in str(e) or "longer than" in str(e).lower():
            # Final safety: if somehow we still get the error, truncate and retry
            password_bytes = plain_password.encode("utf-8")[:71]
            plain_password = password_bytes.decode("utf-8", errors="ignore")
            return password_context.verify(plain_password, hashed_password)
        raise


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crea un token JWT con JTI único para posible invalidación"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # Añadir JTI (JWT ID) único para poder invalidar tokens individualmente
    to_encode.update(
        {
            "exp": expire,
            "jti": str(uuid.uuid4()),  # Identificador único del token
            "type": "access",
        }
    )

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verifica y decodifica un token JWT"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def get_password_context() -> CryptContext:
    """Retorna el contexto de contraseñas configurado"""
    return password_context

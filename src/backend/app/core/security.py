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
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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
    
    # Always truncate to 72 bytes to avoid bcrypt errors
    # bcrypt has a hard limit of 72 bytes, and passlib enforces this strictly
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
        # Decode back to string, using error handling to avoid encoding issues
        try:
            password = password_bytes.decode("utf-8")
        except UnicodeDecodeError:
            # If truncation breaks UTF-8, decode with error handling
            password = password_bytes.decode("utf-8", errors="ignore")
        print(f"⚠️  Contraseña truncada a {len(password_bytes)} bytes para bcrypt")
    
    # Ensure we never pass more than 72 bytes to bcrypt
    # Double-check the byte length before hashing
    final_bytes = password.encode("utf-8")
    if len(final_bytes) > 72:
        password = password.encode("utf-8")[:72].decode("utf-8", errors="ignore")
    
    return password_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contraseña contra su hash"""
    # Ensure password is a string
    if not isinstance(plain_password, str):
        plain_password = str(plain_password)
    
    # Always truncate to 72 bytes to avoid bcrypt errors
    password_bytes = plain_password.encode("utf-8")
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
        try:
            plain_password = password_bytes.decode("utf-8")
        except UnicodeDecodeError:
            plain_password = password_bytes.decode("utf-8", errors="ignore")
    
    # Double-check the byte length before verification
    final_bytes = plain_password.encode("utf-8")
    if len(final_bytes) > 72:
        plain_password = plain_password.encode("utf-8")[:72].decode("utf-8", errors="ignore")

    return password_context.verify(plain_password, hashed_password)


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

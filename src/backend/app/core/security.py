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
    # Truncar si es muy larga para bcrypt
    if len(password.encode("utf-8")) > 72:
        password_bytes = password.encode("utf-8")[:72]
        password = password_bytes.decode("utf-8", errors="ignore")
        print(f"⚠️  Contraseña truncada a {len(password_bytes)} bytes para bcrypt")

    return password_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contraseña contra su hash"""
    # Truncar si es muy larga para bcrypt
    if len(plain_password.encode("utf-8")) > 72:
        password_bytes = plain_password.encode("utf-8")[:72]
        plain_password = password_bytes.decode("utf-8", errors="ignore")

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

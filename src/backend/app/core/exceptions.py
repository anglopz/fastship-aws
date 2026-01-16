"""
Custom exceptions for the application
Section 26: Error Handling Integration
"""
from fastapi import status


class FastShipError(Exception):
    """Base exception for all exceptions in fastship api"""
    # status_code to be returned for this exception when it is handled
    status = status.HTTP_400_BAD_REQUEST

    def __init__(self, message: str = None):
        self.message = message or self.__doc__ or "An error occurred"
        self.status_code = self.status  # For backward compatibility with AppError
        super().__init__(self.message)


# Backward compatibility: AppError is an alias for FastShipError
AppError = FastShipError


# Section 26: New exception classes
class EntityNotFound(FastShipError):
    """Entity not found in database"""
    status = status.HTTP_404_NOT_FOUND


class ClientNotAuthorized(FastShipError):
    """Client is not authorized to perform the action"""
    status = status.HTTP_401_UNAUTHORIZED


class ClientNotVerified(FastShipError):
    """Client is not verified"""
    status = status.HTTP_401_UNAUTHORIZED


class NothingToUpdate(FastShipError):
    """No data provided to update"""
    status = status.HTTP_400_BAD_REQUEST


class BadCredentials(FastShipError):
    """User email or password is incorrect"""
    status = status.HTTP_401_UNAUTHORIZED


class InvalidToken(FastShipError):
    """Access token is invalid or expired"""
    status = status.HTTP_401_UNAUTHORIZED


class DeliveryPartnerNotAvailable(FastShipError):
    """Delivery partner/s do not service the destination"""
    status = status.HTTP_406_NOT_ACCEPTABLE


class DeliveryPartnerCapacityExceeded(FastShipError):
    """Delivery partner has reached their max handling capacity"""
    status = status.HTTP_406_NOT_ACCEPTABLE


# Existing exceptions (kept for backward compatibility, now inherit from FastShipError)
class NotFoundError(FastShipError):
    """Recurso no encontrado (Legacy - use EntityNotFound)"""
    status = status.HTTP_404_NOT_FOUND

    def __init__(self, resource: str = "Resource"):
        super().__init__(f"{resource} not found")


class AlreadyExistsError(FastShipError):
    """Recurso ya existe"""
    status = status.HTTP_409_CONFLICT

    def __init__(self, resource: str = "Resource"):
        super().__init__(f"{resource} already exists")


class ValidationError(FastShipError):
    """Error de validación"""
    status = status.HTTP_422_UNPROCESSABLE_ENTITY

    def __init__(self, message: str = "Validation error"):
        super().__init__(message)


class UnauthorizedError(FastShipError):
    """No autorizado (Legacy - use ClientNotAuthorized)"""
    status = status.HTTP_401_UNAUTHORIZED

    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message)


class ForbiddenError(FastShipError):
    """Prohibido"""
    status = status.HTTP_403_FORBIDDEN

    def __init__(self, message: str = "Forbidden"):
        super().__init__(message)

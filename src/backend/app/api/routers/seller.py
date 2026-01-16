"""
Seller router
"""
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from pydantic import EmailStr

from app.config import app_settings
from app.database.redis import add_jti_to_blacklist
from app.utils import TEMPLATE_DIR

from ..dependencies import (
    SellerServiceDep,
    SellerDep,
    ShipmentServiceDep,
    get_seller_access_token,
)
from ..schemas.seller import SellerCreate, SellerRead
from ..schemas.shipment import ShipmentRead
from sqlmodel import select
from app.database.models import Shipment


router = APIRouter(prefix="/seller", tags=["Seller"])

# Jinja2 templates for HTML responses
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


### Register a new seller
@router.post(
    "/signup",
    response_model=SellerRead,
    summary="Register a new seller account",
    description="""
    Register a new seller account in the FastShip system.
    
    **Process:**
    1. Validates seller information (name, email, password)
    2. Checks if email is already registered
    3. Creates seller account with hashed password
    4. Sends verification email to the provided email address
    
    **Note:** The seller must verify their email before they can login.
    """,
    response_description="Successfully registered seller account",
    responses={
        200: {
            "description": "Seller registered successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "Acme Shipping Co.",
                        "email": "seller@example.com"
                    }
                }
            }
        },
        409: {
            "description": "Email already exists",
            "content": {
                "application/json": {
                    "example": {
                        "error": "AlreadyExistsError",
                        "message": "Email seller@example.com already exists",
                        "status_code": 409
                    }
                }
            }
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "error": "ValidationError",
                        "message": "Validation error",
                        "details": [
                            {
                                "loc": ["body", "email"],
                                "msg": "value is not a valid email address",
                                "type": "value_error.email"
                            }
                        ]
                    }
                }
            }
        }
    },
    operation_id="register_seller",
    tags=["Seller"]
)
async def register_seller(
    seller: SellerCreate,
    service: SellerServiceDep,
):
    """Register a new seller"""
    # Phase 3: Celery tasks are used directly by services (no BackgroundTasks needed)
    return await service.add(seller)


### Login a seller
@router.post(
    "/token",
    summary="Login and get access token",
    description="""
    Authenticate a seller and receive a JWT access token.
    
    **Authentication:**
    - Uses OAuth2 password flow
    - Requires valid email and password
    - Email must be verified before login
    
    **Response:**
    - Returns JWT access token
    - Token expires after configured time
    - Use token in Authorization header: `Bearer <token>`
    """,
    response_description="Successfully authenticated and token generated",
    responses={
        200: {
            "description": "Login successful",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer"
                    }
                }
            }
        },
        401: {
            "description": "Invalid credentials or email not verified",
            "content": {
                "application/json": {
                    "example": {
                        "error": "BadCredentials",
                        "message": "Email or password is incorrect",
                        "status_code": 401
                    }
                }
            }
        }
    },
    operation_id="login_seller",
    tags=["Seller"]
)
async def login_seller(
    request_form: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: SellerServiceDep,
):
    """Login and get access token for seller"""
    token = await service.token(request_form.username, request_form.password)
    return {
        "access_token": token,
        "token_type": "bearer",
    }


### Verify seller email
@router.get(
    "/verify",
    summary="Verify seller email address",
    description="""
    Verify a seller's email address using the verification token sent via email.
    
    **Process:**
    1. Validates the verification token
    2. Marks the seller's email as verified
    3. Seller can now login to the system
    
    **Token:**
    - Sent via email after registration
    - URL-safe token format
    - Has expiration time
    """,
    response_description="Email verification result",
    responses={
        200: {
            "description": "Email verified successfully",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Email verified successfully"
                    }
                }
            }
        },
        400: {
            "description": "Invalid or expired token",
            "content": {
                "application/json": {
                    "example": {
                        "error": "InvalidToken",
                        "message": "Invalid or expired verification token",
                        "status_code": 400
                    }
                }
            }
        },
        404: {
            "description": "User not found",
            "content": {
                "application/json": {
                    "example": {
                        "error": "EntityNotFound",
                        "message": "User not found",
                        "status_code": 404
                    }
                }
            }
        }
    },
    operation_id="verify_seller_email",
    tags=["Seller"]
)
async def verify_seller_email(
    token: str,
    service: SellerServiceDep,
):
    """Verify seller email using verification token"""
    await service.verify_email(token)
    return {"detail": "Email verified successfully"}


### Email Password Reset Link
@router.get(
    "/forgot_password",
    summary="Request password reset link",
    description="""
    Request a password reset link to be sent via email.
    
    **Security:**
    - Does not reveal if email exists (prevents email enumeration)
    - Sends reset link only if email is registered
    - Reset link expires after 24 hours
    
    **Process:**
    1. Validates email format
    2. If email exists, sends reset link via email
    3. Returns success message (always, for security)
    """,
    response_description="Password reset request processed",
    responses={
        200: {
            "description": "Password reset link sent (if email exists)",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Check email for password reset link"
                    }
                }
            }
        }
    },
    operation_id="forgot_password",
    tags=["Seller"]
)
async def forgot_password(
    email: EmailStr,
    service: SellerServiceDep,
):
    """Request password reset link via email"""
    # Phase 3: Celery tasks are used directly by services (no BackgroundTasks needed)
    await service.send_password_reset_link(email, router.prefix)
    return {"detail": "Check email for password reset link"}


### Password Reset Form
@router.get("/reset_password_form")
async def get_reset_password_form(
    request: Request,
    token: str,
):
    """Redirect to frontend password reset form"""
    from fastapi.responses import RedirectResponse
    # Redirect to frontend reset password page with token
    frontend_url = app_settings.FRONTEND_URL
    return RedirectResponse(
        url=f"{frontend_url}/seller/reset-password?token={token}",
        status_code=302
    )


### Reset Seller Password
@router.post("/reset_password")
async def reset_password(
    request: Request,
    token: str,
    password: Annotated[str, Form()],
    service: SellerServiceDep,
):
    """Process password reset"""
    is_success = await service.reset_password(token, password)
    
    return templates.TemplateResponse(
        request=request,
        name="password/reset_success.html" if is_success else "password/reset_failed.html",
    )


### Logout a seller
@router.get(
    "/logout",
    summary="Logout and invalidate token",
    description="""
    Logout the current seller and invalidate their access token.
    
    **Process:**
    1. Extracts JWT ID (jti) from the access token
    2. Adds token to blacklist in Redis
    3. Token can no longer be used for authentication
    
    **Security:**
    - Requires valid authentication token
    - Token is immediately invalidated
    - Cannot be reused after logout
    """,
    response_description="Logout successful",
    responses={
        200: {
            "description": "Successfully logged out",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Successfully logged out"
                    }
                }
            }
        },
        401: {
            "description": "Invalid or expired token",
            "content": {
                "application/json": {
                    "example": {
                        "error": "InvalidToken",
                        "message": "Invalid or expired access token",
                        "status_code": 401
                    }
                }
            }
        }
    },
    operation_id="logout_seller",
    tags=["Seller"]
)
async def logout_seller(
    token_data: Annotated[dict, Depends(get_seller_access_token)],
):
    """Logout and invalidate the current token"""
    await add_jti_to_blacklist(token_data["jti"])
    return {"detail": "Successfully logged out"}


### Get all shipments for the authenticated seller
@router.get(
    "/shipments",
    response_model=list[ShipmentRead],
    summary="Get all shipments for seller",
    description="""
    Retrieve all shipments created by the authenticated seller.
    
    **Returns:**
    - List of all shipments created by the seller
    - Includes shipment details (content, weight, destination, status)
    - Includes client contact information
    - Includes estimated delivery dates
    - Includes associated tags (if any)
    
    **Access:**
    - Requires authentication (JWT token)
    - Only returns shipments created by the authenticated seller
    """,
    response_description="List of seller's shipments",
    responses={
        200: {
            "description": "List of shipments",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "content": "Electronics",
                            "weight": 5.5,
                            "destination": 887,
                            "status": "in_transit",
                            "estimated_delivery": "2026-01-10T12:00:00",
                            "client_contact_email": "client@example.com",
                            "client_contact_phone": "+34601539533",
                            "tags": ["express", "fragile"]
                        }
                    ]
                }
            }
        },
        401: {
            "description": "Not authenticated",
            "content": {
                "application/json": {
                    "example": {
                        "error": "InvalidToken",
                        "message": "Invalid or expired access token",
                        "status_code": 401
                    }
                }
            }
        }
    },
    operation_id="get_seller_shipments",
    tags=["Seller"]
)
async def get_seller_shipments(
    seller: SellerDep,
    shipment_service: ShipmentServiceDep,
):
    """Get all shipments for the authenticated seller"""
    # Query all shipments for this seller
    statement = select(Shipment).where(Shipment.seller_id == seller.id)
    result = await shipment_service.session.execute(statement)
    shipments = result.scalars().all()
    
    # Refresh each shipment to load relationships (tags, events)
    for shipment in shipments:
        await shipment_service.session.refresh(shipment, ["tags", "events"])
    
    return shipments


### Get current seller profile
@router.get(
    "/me",
    response_model=SellerRead,
    summary="Get current seller profile",
    description="""
    Get the profile information of the currently authenticated seller.
    
    **Returns:**
    - Seller ID, name, and email
    - Account information
    
    **Access:**
    - Requires authentication (JWT token)
    - Returns the seller associated with the current token
    """,
    response_description="Current seller profile",
    responses={
        200: {
            "description": "Seller profile",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "Acme Shipping Co.",
                        "email": "seller@example.com"
                    }
                }
            }
        },
        401: {
            "description": "Not authenticated",
            "content": {
                "application/json": {
                    "example": {
                        "error": "InvalidToken",
                        "message": "Invalid or expired access token",
                        "status_code": 401
                    }
                }
            }
        }
    },
    operation_id="get_seller_profile",
    tags=["Seller"]
)
async def get_seller_profile(
    seller: SellerDep,
):
    """Get the current authenticated seller's profile"""
    return seller

"""
Delivery Partner router
"""
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from pydantic import EmailStr

from app.config import app_settings
from app.core.exceptions import NothingToUpdate
from app.database.redis import add_jti_to_blacklist
from app.utils import TEMPLATE_DIR

from ..dependencies import (
    DeliveryPartnerDep,
    DeliveryPartnerServiceDep,
    ShipmentServiceDep,
    get_partner_access_token,
)
from ..schemas.delivery_partner import (
    DeliveryPartnerCreate,
    DeliveryPartnerRead,
    DeliveryPartnerUpdate,
)
from ..schemas.shipment import ShipmentRead
from sqlmodel import select
from app.database.models import Shipment

router = APIRouter(prefix="/partner", tags=["Delivery Partner"])

# Jinja2 templates for HTML responses
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


### Register a new delivery partner
@router.post(
    "/signup",
    response_model=DeliveryPartnerRead,
    summary="Register a new delivery partner account",
    description="""
    Register a new delivery partner account in the FastShip system.
    
    **Process:**
    1. Validates partner information (name, email, password, locations, capacity)
    2. Checks if email is already registered
    3. Creates partner account with hashed password
    4. Creates/links serviceable locations based on zip codes
    5. Sends verification email to the provided email address
    
    **Serviceable Locations:**
    - List of zip codes where the partner can deliver
    - Locations are automatically created if they don't exist
    - Linked via many-to-many relationship
    
    **Note:** The partner must verify their email before they can login.
    """,
    response_description="Successfully registered delivery partner account",
    responses={
        200: {
            "description": "Delivery partner registered successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "FastDelivery Co.",
                        "email": "partner@example.com",
                        "servicable_locations": [887, 8020, 28001],
                        "max_handling_capacity": 50
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
                        "message": "Email partner@example.com already exists",
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
                                "loc": ["body", "servicable_locations"],
                                "msg": "ensure this value has at least 1 item",
                                "type": "value_error.list.min_items"
                            }
                        ]
                    }
                }
            }
        }
    },
    operation_id="register_delivery_partner",
    tags=["Delivery Partner"]
)
async def register_delivery_partner(
    partner: DeliveryPartnerCreate,
    service: DeliveryPartnerServiceDep,
):
    """Register a new delivery partner"""
    # Phase 3: Celery tasks are used directly by services (no BackgroundTasks needed)
    # Phase 2: add() method now populates servicable_locations
    partner_obj = await service.add(partner)
    # Refresh to ensure servicable_locations is loaded
    await service.session.refresh(partner_obj, ["servicable_locations"])
    return partner_obj


### Verify delivery partner email
@router.get("/verify")
async def verify_partner_email(
    token: str,
    service: DeliveryPartnerServiceDep,
):
    """Verify delivery partner email using verification token"""
    await service.verify_email(token)
    return {"detail": "Email verified successfully"}


### Email Password Reset Link
@router.get("/forgot_password")
async def forgot_password(
    email: EmailStr,
    service: DeliveryPartnerServiceDep,
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
        url=f"{frontend_url}/partner/reset-password?token={token}",
        status_code=302
    )


### Reset Delivery Partner Password
@router.post("/reset_password")
async def reset_password(
    request: Request,
    token: str,
    password: Annotated[str, Form()],
    service: DeliveryPartnerServiceDep,
):
    """Process password reset"""
    is_success = await service.reset_password(token, password)
    
    return templates.TemplateResponse(
        request=request,
        name="password/reset_success.html" if is_success else "password/reset_failed.html",
    )


### Login a delivery partner
@router.post(
    "/token",
    summary="Login and get access token",
    description="""
    Authenticate a delivery partner and receive a JWT access token.
    
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
    operation_id="login_delivery_partner",
    tags=["Delivery Partner"]
)
async def login_delivery_partner(
    request_form: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: DeliveryPartnerServiceDep,
):
    """Login and get access token for delivery partner"""
    token = await service.token(request_form.username, request_form.password)
    return {
        "access_token": token,
        "token_type": "bearer",
    }


### Update the logged in delivery partner
@router.post(
    "/",
    response_model=DeliveryPartnerRead,
    summary="Update delivery partner information",
    description="""
    Update the authenticated delivery partner's information.
    
    **Updatable Fields:**
    - `servicable_locations`: List of zip codes for serviceable locations
    - `max_handling_capacity`: Maximum number of shipments the partner can handle
    
    **Process:**
    1. Validates update data
    2. Updates partner fields
    3. Updates serviceable locations relationship if provided
    4. Returns updated partner information
    
    **Note:** Only the authenticated partner can update their own information.
    """,
    response_description="Successfully updated delivery partner",
    responses={
        200: {
            "description": "Partner updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "FastDelivery Co.",
                        "email": "partner@example.com",
                        "servicable_locations": [887, 8020, 28001, 28002],
                        "max_handling_capacity": 75
                    }
                }
            }
        },
        400: {
            "description": "No data provided to update",
            "content": {
                "application/json": {
                    "example": {
                        "error": "NothingToUpdate",
                        "message": "No data provided to update",
                        "status_code": 400
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
    operation_id="update_delivery_partner",
    tags=["Delivery Partner"]
)
async def update_delivery_partner(
    partner_update: DeliveryPartnerUpdate,
    partner: DeliveryPartnerDep,
    service: DeliveryPartnerServiceDep,
):
    """Update the currently logged in delivery partner"""
    # Update data with given fields
    update = partner_update.model_dump(exclude_none=True)

    if not update:
        raise NothingToUpdate("No data provided to update")

    # Phase 3: Handle servicable_locations separately (it's a relationship, not a field)
    servicable_locations = update.pop("servicable_locations", None)
    
    # Update other partner fields
    for key, value in update.items():
        if hasattr(partner, key):
            setattr(partner, key, value)
    
    # Update servicable_locations relationship if provided
    if servicable_locations is not None:
        from app.database.models import Location
        from sqlmodel import select
        locations = []
        for zip_code in servicable_locations:
            # Get or create Location
            location = await service.session.scalar(
                select(Location).where(Location.zip_code == zip_code)
            )
            if not location:
                location = Location(zip_code=zip_code)
                await service._add(location)
            locations.append(location)
        partner.servicable_locations = locations
    
    updated_partner = await service.update(partner)
    # Refresh to ensure servicable_locations is loaded
    await service.session.refresh(updated_partner, ["servicable_locations"])
    return updated_partner


### Logout a delivery partner
@router.get("/logout")
async def logout_delivery_partner(
    token_data: Annotated[dict, Depends(get_partner_access_token)],
):
    """Logout and invalidate the current token"""
    await add_jti_to_blacklist(token_data["jti"])
    return {"detail": "Successfully logged out"}


### Get all shipments for the authenticated delivery partner
@router.get(
    "/shipments",
    response_model=list[ShipmentRead],
    summary="Get all shipments for delivery partner",
    description="""
    Retrieve all shipments assigned to the authenticated delivery partner.
    
    **Returns:**
    - List of all shipments assigned to the partner
    - Includes shipment details (content, weight, destination, status)
    - Includes client contact information
    - Includes estimated delivery dates
    - Includes associated tags (if any)
    
    **Access:**
    - Requires authentication (JWT token)
    - Only returns shipments assigned to the authenticated partner
    """,
    response_description="List of partner's shipments",
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
    operation_id="get_partner_shipments",
    tags=["Delivery Partner"]
)
async def get_partner_shipments(
    partner: DeliveryPartnerDep,
    shipment_service: ShipmentServiceDep,
):
    """Get all shipments assigned to the authenticated delivery partner"""
    # Query all shipments assigned to this partner
    statement = select(Shipment).where(Shipment.delivery_partner_id == partner.id)
    result = await shipment_service.session.execute(statement)
    shipments = result.scalars().all()
    
    # Refresh each shipment to load relationships (tags, events)
    for shipment in shipments:
        await shipment_service.session.refresh(shipment, ["tags", "events"])
    
    return shipments


### Get current delivery partner profile
@router.get(
    "/me",
    response_model=DeliveryPartnerRead,
    summary="Get current delivery partner profile",
    description="""
    Get the profile information of the currently authenticated delivery partner.
    
    **Returns:**
    - Partner ID, name, email
    - Serviceable locations
    - Maximum handling capacity
    
    **Access:**
    - Requires authentication (JWT token)
    - Returns the partner associated with the current token
    """,
    response_description="Current delivery partner profile",
    responses={
        200: {
            "description": "Delivery partner profile",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "FastDelivery Co.",
                        "email": "partner@example.com",
                        "servicable_locations": [887, 8020, 28001],
                        "max_handling_capacity": 50
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
    operation_id="get_delivery_partner_profile",
    tags=["Delivery Partner"]
)
async def get_delivery_partner_profile(
    partner: DeliveryPartnerDep,
    service: DeliveryPartnerServiceDep,
):
    """Get the current authenticated delivery partner's profile"""
    # Refresh to ensure servicable_locations is loaded
    await service.session.refresh(partner, ["servicable_locations"])
    return partner


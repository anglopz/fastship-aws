"""
Shipment router
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Form, Request, status
from fastapi.templating import Jinja2Templates
from typing import Annotated

from app.config import app_settings
from app.core.exceptions import EntityNotFound, NothingToUpdate
from app.utils import TEMPLATE_DIR
from ..dependencies import DeliveryPartnerDep, SellerDep, ShipmentServiceDep
from ..schemas.shipment import ShipmentCreate, ShipmentRead, ShipmentUpdate
from app.database.models import ShipmentEvent, TagName


router = APIRouter(prefix="/shipment", tags=["Shipment"])

# Jinja2 templates for HTML responses
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


### Read a shipment by id
@router.get(
    "/",
    response_model=ShipmentRead,
    summary="Get shipment by ID",
    description="""
    Retrieve detailed information about a specific shipment.
    
    **Returns:**
    - Shipment details (content, weight, destination, status)
    - Client contact information
    - Estimated delivery date
    - Associated tags (if any)
    - Current status
    
    **Access:**
    - Public endpoint (no authentication required)
    - Useful for tracking shipments
    """,
    response_description="Shipment details",
    responses={
        200: {
            "description": "Shipment found",
            "content": {
                "application/json": {
                    "example": {
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
                }
            }
        },
        404: {
            "description": "Shipment not found",
            "content": {
                "application/json": {
                    "example": {
                        "error": "EntityNotFound",
                        "message": "Given id doesn't exist!",
                        "status_code": 404
                    }
                }
            }
        }
    },
    operation_id="get_shipment",
    tags=["Shipment"]
)
async def get_shipment(id: UUID, service: ShipmentServiceDep):
    """Get a shipment by ID"""
    # Check for shipment with given id
    shipment = await service.get(id)

    if shipment is None:
        raise EntityNotFound("Given id doesn't exist!")
    
    # Refresh to load tags and events relationships
    await service.session.refresh(shipment, ["tags", "events"])

    return shipment


### Create a new shipment
@router.post(
    "/",
    response_model=ShipmentRead,
    summary="Create a new shipment",
    description="""
    Create a new shipment and automatically assign a delivery partner.
    
    **Process:**
    1. Validates shipment data (content, weight, destination, client contact)
    2. Finds available delivery partner for the destination zip code
    3. Assigns shipment to partner (if available)
    4. Sets initial status to "placed"
    5. Sends notification email to client
    6. Creates initial shipment event
    
    **Automatic Assignment:**
    - System finds delivery partners that service the destination zip code
    - Selects partner with available capacity
    - If no partner available, shipment is created but unassigned
    
    **Requirements:**
    - Authenticated seller (JWT token required)
    - Valid client contact email
    - Weight must be ≤ 25 kg
    """,
    response_description="Successfully created shipment",
    responses={
        200: {
            "description": "Shipment created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "content": "Electronics",
                        "weight": 5.5,
                        "destination": 887,
                        "status": "placed",
                        "estimated_delivery": "2026-01-10T12:00:00",
                        "client_contact_email": "client@example.com",
                        "client_contact_phone": "+34601539533",
                        "tags": []
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
        },
        406: {
            "description": "No delivery partner available",
            "content": {
                "application/json": {
                    "example": {
                        "error": "DeliveryPartnerNotAvailable",
                        "message": "No delivery partner available",
                        "status_code": 406
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
                                "loc": ["body", "weight"],
                                "msg": "ensure this value is less than or equal to 25",
                                "type": "value_error.number.not_le"
                            }
                        ]
                    }
                }
            }
        }
    },
    operation_id="create_shipment",
    tags=["Shipment"]
)
async def submit_shipment(
    seller: SellerDep,
    shipment: ShipmentCreate,
    service: ShipmentServiceDep,
):
    """Create a new shipment (authenticated seller required)"""
    # Phase 3: Celery tasks are used directly by services (no BackgroundTasks needed)
    return await service.add(shipment, seller)


### Update fields of a shipment
@router.patch(
    "/",
    response_model=ShipmentRead,
    summary="Update shipment status and location",
    description="""
    Update shipment status, location, and other fields.
    
    **Authorization:**
    - Only the assigned delivery partner can update the shipment
    - Partner must be authenticated with valid JWT token
    
    **Updatable Fields:**
    - `status`: Current shipment status (in_transit, out_for_delivery, delivered, etc.)
    - `location`: Current location (zip code)
    - `description`: Additional description or notes
    - `estimated_delivery`: Updated delivery estimate
    - `verification_code`: Required when marking as "delivered"
    
    **Special Requirements:**
    - When status is "delivered", `verification_code` is required
    - Verification code is sent to client via email/SMS
    - System creates shipment event for status/location changes
    - Client receives notification of status changes
    """,
    response_description="Successfully updated shipment",
    responses={
        200: {
            "description": "Shipment updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "content": "Electronics",
                        "weight": 5.5,
                        "destination": 887,
                        "status": "out_for_delivery",
                        "location": 887,
                        "estimated_delivery": "2026-01-10T12:00:00",
                        "client_contact_email": "client@example.com",
                        "client_contact_phone": "+34601539533",
                        "tags": ["express"]
                    }
                }
            }
        },
        400: {
            "description": "No data provided or validation error",
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
        422: {
            "description": "Validation error - shipment cannot be updated",
            "content": {
                "application/json": {
                    "examples": {
                        "cancelled": {
                            "summary": "Shipment is cancelled",
                            "value": {
                                "error": "ValidationError",
                                "message": "Cannot update a cancelled shipment",
                                "status_code": 422
                            }
                        },
                        "delivered": {
                            "summary": "Shipment is delivered",
                            "value": {
                                "error": "ValidationError",
                                "message": "Cannot update a delivered shipment",
                                "status_code": 422
                            }
                        }
                    }
                }
            }
        },
        401: {
            "description": "Not authorized or invalid token",
            "content": {
                "application/json": {
                    "example": {
                        "error": "ClientNotAuthorized",
                        "message": "Not authorized",
                        "status_code": 401
                    }
                }
            }
        },
        404: {
            "description": "Shipment not found",
            "content": {
                "application/json": {
                    "example": {
                        "error": "EntityNotFound",
                        "message": "Shipment not found",
                        "status_code": 404
                    }
                }
            }
        }
    },
    operation_id="update_shipment",
    tags=["Shipment"]
)
async def update_shipment(
    id: UUID,
    shipment_update: ShipmentUpdate,
    partner: DeliveryPartnerDep,
    service: ShipmentServiceDep,
):
    """Update a shipment (only the assigned delivery partner can update)"""
    # Update data with given fields
    update = shipment_update.model_dump(exclude_none=True)

    if not update:
        raise NothingToUpdate("No data provided to update")
    
    # Get shipment for update
    shipment = await service.get(id)
    
    if shipment is None:
        raise EntityNotFound("Shipment not found")

    # Phase 3: Celery tasks are used directly by services (no BackgroundTasks needed)
    # Update shipment with event creation (partner passed for authorization check)
    updated_shipment = await service.update(shipment, shipment_update, partner=partner)
    
    # Ensure events are loaded before returning
    await service.session.refresh(updated_shipment, ["events", "tags"])
    
    return updated_shipment


### Get shipment timeline
@router.get("/timeline", response_model=list[ShipmentEvent])
async def get_shipment_timeline(
    id: UUID,
    service: ShipmentServiceDep,
):
    """Get timeline of events for a shipment"""
    shipment = await service.get(id)
    
    if shipment is None:
        raise EntityNotFound("Shipment not found")
    
    # Refresh to load events
    await service.session.refresh(shipment, ["events"])
    return shipment.timeline


### Cancel a shipment
@router.post(
    "/cancel",
    response_model=ShipmentRead,
    summary="Cancel a shipment",
    description="""
    Cancel a shipment. Only the seller who created it can cancel.
    
    **Authorization:**
    - Only the seller who created the shipment can cancel it
    - Seller must be authenticated with valid JWT token
    
    **Process:**
    1. Validates seller owns the shipment
    2. Updates status to "cancelled"
    3. Creates cancellation event
    4. Sends notification to client
    
    **Note:** Once cancelled, shipment cannot be reactivated.
    """,
    response_description="Successfully cancelled shipment",
    responses={
        200: {
            "description": "Shipment cancelled successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "content": "Electronics",
                        "weight": 5.5,
                        "destination": 887,
                        "status": "cancelled",
                        "estimated_delivery": "2026-01-10T12:00:00",
                        "client_contact_email": "client@example.com",
                        "client_contact_phone": "+34601539533",
                        "tags": []
                    }
                }
            }
        },
        401: {
            "description": "Not authorized",
            "content": {
                "application/json": {
                    "example": {
                        "error": "ClientNotAuthorized",
                        "message": "Not authorized to cancel this shipment",
                        "status_code": 401
                    }
                }
            }
        },
        404: {
            "description": "Shipment not found",
            "content": {
                "application/json": {
                    "example": {
                        "error": "EntityNotFound",
                        "message": "Shipment not found",
                        "status_code": 404
                    }
                }
            }
        }
    },
    operation_id="cancel_shipment",
    tags=["Shipment"]
)
async def cancel_shipment(
    id: UUID,
    seller: SellerDep,
    service: ShipmentServiceDep,
):
    """Cancel a shipment (only the seller who created it can cancel)"""
    # Phase 3: Celery tasks are used directly by services (no BackgroundTasks needed)
    return await service.cancel(id, seller)


### Track shipment (HTML response)
@router.get("/track", include_in_schema=False)
async def get_tracking(
    request: Request,
    id: UUID,
    service: ShipmentServiceDep,
):
    """Get shipment tracking page (HTML response)"""
    # Check for shipment with given id
    shipment = await service.get(id)
    
    if shipment is None:
        raise EntityNotFound("Shipment not found")
    
    # Refresh to load relationships
    await service.session.refresh(shipment, ["delivery_partner", "events"])
    
    # Prepare context for template
    # Pass shipment object directly so template can access id.hex
    context = {
        "request": request,
        "id": shipment.id,  # UUID object for .hex access
        "content": shipment.content,
        "weight": shipment.weight,
        "destination": shipment.destination,
        "status": shipment.status,
        "estimated_delivery": shipment.estimated_delivery,
        "created_at": shipment.created_at,
        "partner": shipment.delivery_partner.name,
        "timeline": shipment.timeline,  # Already reversed (newest first)
    }
    
    return templates.TemplateResponse(
        request=request,
        name="track.html",
        context=context,
    )


### Delete a shipment by id
@router.delete("/")
async def delete_shipment(id: UUID, service: ShipmentServiceDep) -> dict[str, str]:
    """Delete a shipment by ID"""
    # Remove from database
    await service.delete(id)

    return {"detail": f"Shipment with id #{id} is deleted!"}


### Submit a review for a shipment (HTML form)
@router.get("/review", include_in_schema=False)
async def get_review_form(
    request: Request,
    token: str,
):
    """Display review submission form"""
    return templates.TemplateResponse(
        request=request,
        name="review.html",
        context={
            "review_url": f"http://{app_settings.APP_DOMAIN}/shipment/review?token={token}",
        },
    )


### Submit a review for a shipment
@router.post("/review", include_in_schema=False)
async def submit_review(
    token: str,
    service: ShipmentServiceDep,
    rating: Annotated[int, Form(ge=1, le=5)],
    comment: Annotated[str | None, Form()] = None,
):
    """Submit a review for a shipment"""
    await service.rate(token, rating, comment)
    return {"detail": "Review submitted successfully"}


### Add tag to shipment
@router.get("/tag", response_model=ShipmentRead)
async def add_tag_to_shipment(
    id: UUID,
    tag_name: TagName,
    service: ShipmentServiceDep,
):
    """Add a tag to a shipment"""
    return await service.add_tag(id, tag_name)


### Remove tag from shipment
@router.delete("/tag", response_model=ShipmentRead)
async def remove_tag_from_shipment(
    id: UUID,
    tag_name: TagName,
    service: ShipmentServiceDep,
):
    """Remove a tag from a shipment"""
    return await service.remove_tag(id, tag_name)

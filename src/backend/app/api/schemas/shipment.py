"""
Shipment schemas
Section 28: API Documentation - Model Metadata
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator

from app.database.models import ShipmentStatus, TagName


class BaseShipment(BaseModel):
    """Base shipment schema with common fields"""
    content: str = Field(
        ...,
        description="Description of shipment contents",
        example="Electronics - Laptop and accessories",
        min_length=1,
        max_length=500
    )
    weight: float = Field(
        ...,
        description="Weight in kilograms (maximum 25 kg)",
        example=5.5,
        gt=0,
        le=25
    )
    destination: int = Field(
        ...,
        description="Destination zip code where shipment should be delivered",
        example=887,
        gt=0
    )


class ShipmentRead(BaseShipment):
    """Schema for reading shipment information"""
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "content": "Electronics - Laptop and accessories",
                "weight": 5.5,
                "destination": 887,
                "status": "in_transit",
                "estimated_delivery": "2026-01-10T12:00:00",
                "client_contact_email": "client@example.com",
                "client_contact_phone": "+34601539533",
                "tags": ["express", "fragile"]
            }
        }
    )
    
    id: UUID = Field(
        ...,
        description="Unique shipment identifier",
        example="123e4567-e89b-12d3-a456-426614174000"
    )
    status: ShipmentStatus = Field(
        ...,
        description="Current status of the shipment",
        example=ShipmentStatus.in_transit
    )
    estimated_delivery: datetime = Field(
        ...,
        description="Estimated delivery date and time",
        example="2026-01-10T12:00:00"
    )
    client_contact_email: str = Field(
        ...,
        description="Client's email address for notifications",
        example="client@example.com"
    )
    client_contact_phone: str | None = Field(
        default=None,
        description="Client's phone number for SMS notifications (E.164 format)",
        example="+34601539533"
    )
    tags: Optional[list[TagName]] = Field(
        default=None,
        description="List of tags associated with the shipment for special handling instructions (e.g., express, fragile, temperature_controlled)"
    )
    timeline: Optional[list[dict]] = Field(
        default=None,
        description="List of shipment events (timeline) showing status changes and location updates",
        example=[
            {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "created_at": "2026-01-10T10:00:00",
                "location": 887,
                "status": "in_transit",
                "description": "Package is in transit"
            }
        ]
    )
    
    @field_validator('tags', mode='before')
    @classmethod
    def extract_tag_names(cls, v):
        """Extract tag names from Tag objects if needed"""
        if v is None:
            return None
        if isinstance(v, list):
            # If list contains Tag objects, extract names
            # Check if first item has a 'name' attribute (Tag object)
            if v and hasattr(v[0], 'name'):
                return [tag.name for tag in v]
            # If already TagName enum values, return as is
            return v
        return v
    
    @field_validator('timeline', mode='before')
    @classmethod
    def extract_timeline_events(cls, v):
        """Extract timeline events from ShipmentEvent objects if needed"""
        if v is None:
            return None
        if isinstance(v, list):
            # If list contains ShipmentEvent objects, convert to dict
            if v and hasattr(v[0], 'id'):
                return [
                    {
                        "id": str(event.id),
                        "created_at": event.created_at.isoformat() if hasattr(event.created_at, 'isoformat') else str(event.created_at),
                        "location": event.location,
                        "status": event.status.value if hasattr(event.status, 'value') else str(event.status),
                        "description": event.description
                    }
                    for event in v
                ]
            # If already dicts, return as is
            return v
        return v


class ShipmentCreate(BaseShipment):
    """Schema for creating a new shipment"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": "Electronics - Laptop and accessories",
                "weight": 5.5,
                "destination": 887,
                "client_contact_email": "client@example.com",
                "client_contact_phone": "+34601539533"
            }
        }
    )
    
    # Phase 2: client_contact_email is now required
    client_contact_email: EmailStr = Field(
        ...,
        description="Client's email address (required for notifications)",
        example="client@example.com"
    )
    client_contact_phone: str | None = Field(
        default=None,
        description="Client's phone number for SMS notifications (E.164 format, e.g., +34601539533). Optional but recommended for delivery updates.",
        example="+34601539533"
    )


class ShipmentUpdate(BaseModel):
    """Schema for updating shipment status and location"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "out_for_delivery",
                "location": 887,
                "description": "Package is out for delivery",
                "estimated_delivery": "2026-01-10T14:00:00"
            }
        }
    )
    
    status: ShipmentStatus | None = Field(
        default=None,
        description="New shipment status. When set to 'delivered', verification_code is required.",
        example=ShipmentStatus.out_for_delivery
    )
    location: int | None = Field(
        default=None,
        description="Current location zip code where the shipment event occurred",
        example=887,
        gt=0
    )
    description: str | None = Field(
        default=None,
        description="Additional description or notes about the shipment status update",
        example="Package is out for delivery",
        max_length=500
    )
    verification_code: str | None = Field(
        default=None,
        description="Verification code required when marking shipment as 'delivered'. Code is sent to client via email/SMS.",
        example="321686",
        min_length=4,
        max_length=10
    )
    estimated_delivery: datetime | None = Field(
        default=None,
        description="Updated estimated delivery date and time",
        example="2026-01-10T14:00:00"
    )

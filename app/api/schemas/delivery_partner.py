"""
Delivery Partner schemas
"""
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator

from app.database.models import Location


class BaseDeliveryPartner(BaseModel):
    """Base delivery partner schema with common fields"""
    name: str = Field(
        ...,
        description="Business or delivery partner name",
        example="FastDelivery Co.",
        min_length=2,
        max_length=100
    )
    email: EmailStr = Field(
        ...,
        description="Valid email address (must be unique)",
        example="partner@example.com"
    )
    servicable_locations: list[int] = Field(
        ...,
        description="List of zip codes for serviceable locations (Phase 3: uses relationship). Locations are automatically created if they don't exist.",
        example=[887, 8020, 28001],
        min_length=1
    )
    max_handling_capacity: int = Field(
        ...,
        description="Maximum number of shipments the partner can handle simultaneously",
        example=50,
        gt=0
    )


class DeliveryPartnerRead(BaseDeliveryPartner):
    """Schema for reading delivery partner information"""
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "FastDelivery Co.",
                "email": "partner@example.com",
                "servicable_locations": [887, 8020, 28001],
                "max_handling_capacity": 50
            }
        }
    )
    
    id: UUID = Field(
        ...,
        description="Unique delivery partner identifier",
        example="123e4567-e89b-12d3-a456-426614174000"
    )
    
    @field_validator('servicable_locations', mode='before')
    @classmethod
    def extract_zip_codes(cls, v):
        """Extract zip codes from Location objects if needed"""
        if v is None:
            return None
        if isinstance(v, list):
            # If list contains Location objects, extract zip_code
            if v and hasattr(v[0], 'zip_code'):
                return [location.zip_code for location in v]
            # If already integers, return as is
            return v
        return v


class DeliveryPartnerUpdate(BaseModel):
    """Schema for updating delivery partner information"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "servicable_locations": [887, 8020, 28001, 28002],
                "max_handling_capacity": 75
            }
        }
    )
    
    servicable_locations: list[int] | None = Field(
        default=None,
        description="List of zip codes for serviceable locations (Phase 3: uses relationship). Updates the relationship with Location entities.",
        example=[887, 8020, 28001, 28002],
        min_length=1
    )
    max_handling_capacity: int | None = Field(
        default=None,
        description="Maximum number of shipments the partner can handle simultaneously",
        example=75,
        gt=0
    )


class DeliveryPartnerCreate(BaseDeliveryPartner):
    """Schema for creating a new delivery partner account"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "FastDelivery Co.",
                "email": "partner@example.com",
                "servicable_locations": [887, 8020, 28001],
                "max_handling_capacity": 50,
                "password": "SecurePassword123!"
            }
        }
    )
    
    password: str = Field(
        ...,
        description="Account password (minimum 8 characters recommended)",
        example="SecurePassword123!",
        min_length=8
    )


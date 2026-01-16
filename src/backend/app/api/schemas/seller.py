"""
Seller schemas
Section 28: API Documentation - Model Metadata
"""
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class BaseSeller(BaseModel):
    """Base seller schema with common fields"""
    name: str = Field(
        ...,
        description="Business or seller name",
        example="Acme Shipping Co.",
        min_length=2,
        max_length=100
    )
    email: EmailStr = Field(
        ...,
        description="Valid email address (must be unique)",
        example="seller@example.com"
    )


class SellerRead(BaseSeller):
    """Schema for reading seller information"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Acme Shipping Co.",
                "email": "seller@example.com"
            }
        }
    )
    
    id: UUID = Field(
        ...,
        description="Unique seller identifier",
        example="123e4567-e89b-12d3-a456-426614174000"
    )


class SellerCreate(BaseSeller):
    """Schema for creating a new seller account"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Acme Shipping Co.",
                "email": "seller@example.com",
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

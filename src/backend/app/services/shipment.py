"""
Shipment service - refactored to use BaseService and partner assignment
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

# Phase 3: BackgroundTasks removed, using Celery as primary method
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.shipment import ShipmentCreate, ShipmentUpdate
from app.core.exceptions import (
    AlreadyExistsError,
    ClientNotAuthorized,
    EntityNotFound,
    InvalidToken,
    ValidationError,
)
from app.core.mail import MailClient
from app.database.models import DeliveryPartner, Review, Seller, Shipment, ShipmentStatus, Tag, TagName
from app.database.redis import get_shipment_verification_code
from app.utils import decode_url_safe_token
from sqlmodel import select

from .base import BaseService
from .delivery_partner import DeliveryPartnerService
from .event import ShipmentEventService

logger = logging.getLogger(__name__)


class ShipmentService(BaseService):
    """Service for shipment operations"""
    
    def __init__(
        self,
        session: AsyncSession,
        partner_service: DeliveryPartnerService,
        event_service: ShipmentEventService,
        mail_client: Optional[MailClient] = None,
    ):
        super().__init__(Shipment, session)
        self.partner_service = partner_service
        self.event_service = event_service
        self.mail_client = mail_client
        # Phase 3: BackgroundTasks removed, using Celery as primary method

    async def get(self, id: UUID) -> Shipment | None:
        """Get a shipment by ID"""
        return await self._get(id)

    async def add(self, shipment_create: ShipmentCreate, seller: Seller) -> Shipment:
        """Create a new shipment and assign a delivery partner"""
        new_shipment = Shipment(
            **shipment_create.model_dump(),
            status=ShipmentStatus.placed,
            estimated_delivery=datetime.now() + timedelta(days=3),
            seller_id=seller.id,
        )
        # Assign delivery partner to the shipment
        partner = await self.partner_service.assign_shipment(new_shipment)
        # Add the delivery partner foreign key
        new_shipment.delivery_partner_id = partner.id

        shipment = await self._add(new_shipment)
        
        # Create initial placed event (this will also send email notification)
        await self.event_service.create_event(
            shipment=shipment,
            status=ShipmentStatus.placed,
            location=seller.zip_code if hasattr(seller, 'zip_code') else shipment.destination,
            description=f"assigned to {partner.name}",
        )
        
        # Refresh shipment to load events
        await self.session.refresh(shipment, ["events"])
        
        return shipment

    async def update(
        self, 
        shipment: Shipment, 
        shipment_update: ShipmentUpdate,
        partner: Optional[DeliveryPartner] = None,
    ) -> Shipment:
        """
        Update an existing shipment and create event if status/location changed
        
        Args:
            shipment: The shipment to update
            shipment_update: Update data
            partner: Optional delivery partner (for authorization check)
            
        Returns:
            Updated Shipment
            
        Raises:
            ValidationError: If shipment is cancelled or delivered (cannot be updated)
        """
        # Validation: Cannot update cancelled or delivered shipments
        if shipment.status == ShipmentStatus.cancelled:
            raise ValidationError("Cannot update a cancelled shipment")
        if shipment.status == ShipmentStatus.delivered:
            raise ValidationError("Cannot update a delivered shipment")
        
        # Phase 1: Partner authorization check (optional - only if partner provided)
        if partner is not None:
            if shipment.delivery_partner_id != partner.id:
                raise ClientNotAuthorized("Not authorized")
        
        # Phase 2: Verification code is now required for delivery
        if shipment_update.status == ShipmentStatus.delivered:
            if not shipment_update.verification_code:
                raise ValidationError("Verification code is required to mark shipment as delivered")
            stored_code = await get_shipment_verification_code(shipment.id)
            if not stored_code or stored_code != shipment_update.verification_code:
                raise InvalidToken("Invalid or expired verification code")
        
        old_status = shipment.status
        
        # Update shipment fields (exclude verification_code from update data)
        update_data = shipment_update.model_dump(exclude_none=True, exclude=["verification_code"])
        
        # Update estimated_delivery if provided
        # Convert timezone-aware datetime to timezone-naive (database expects TIMESTAMP WITHOUT TIME ZONE)
        if shipment_update.estimated_delivery:
            est_delivery = shipment_update.estimated_delivery
            # If datetime is timezone-aware, convert to UTC and remove timezone info
            if est_delivery.tzinfo is not None:
                est_delivery = est_delivery.replace(tzinfo=None)
            shipment.estimated_delivery = est_delivery
        
        # Update status if provided
        if shipment_update.status:
            shipment.status = shipment_update.status
        
        # Save changes
        updated_shipment = await self._update(shipment)
        
        # Create event if status or location changed
        # Note: location is stored in events, not in shipment model
        status_changed = shipment_update.status and shipment_update.status != old_status
        location_provided = shipment_update.location is not None
        
        if status_changed or location_provided:
            await self.event_service.create_event(
                shipment=updated_shipment,
                status=shipment_update.status or old_status,
                location=shipment_update.location,
                description=shipment_update.description,
            )
        
        # Always refresh events before returning to ensure timeline is loaded
        await self.session.refresh(updated_shipment, ["events", "tags"])
        
        return updated_shipment

    async def cancel(self, id: UUID, seller: Seller) -> Shipment:
        """
        Cancel a shipment (only the seller who created it can cancel)
        
        Args:
            id: UUID of the shipment to cancel
            seller: The seller attempting to cancel (must be the owner)
            
        Returns:
            Updated Shipment with cancelled status
            
        Raises:
            EntityNotFound: If shipment not found
            ClientNotAuthorized: If seller not authorized
        """
        shipment = await self.get(id)
        
        if shipment is None:
            raise EntityNotFound("Shipment not found")
        
        # Validate seller owns this shipment
        if shipment.seller_id != seller.id:
            raise ClientNotAuthorized("Not authorized to cancel this shipment")
        
        # Update status to cancelled
        shipment.status = ShipmentStatus.cancelled
        
        # Save changes
        updated_shipment = await self._update(shipment)
        
        # Create cancellation event (this will also send email notification)
        await self.event_service.create_event(
            shipment=updated_shipment,
            status=ShipmentStatus.cancelled,
            description="cancelled by seller",
        )
        
        # Refresh to load new event
        await self.session.refresh(updated_shipment, ["events"])
        
        return updated_shipment

    async def delete(self, id: UUID) -> None:
        """Delete a shipment"""
        shipment = await self.get(id)
        if shipment:
            await self._delete(shipment)

    async def rate(self, token: str, rating: int, comment: str | None = None) -> None:
        """
        Submit a review for a shipment using a token.
        
        Args:
            token: URL-safe token containing shipment ID
            rating: Rating from 1 to 5
            comment: Optional review comment
            
        Raises:
            InvalidToken: If token is invalid or expired
            EntityNotFound: If shipment not found
            AlreadyExistsError: If review already exists
        """
        # Decode token (use "review" salt to match generation)
        token_data = decode_url_safe_token(
            token,
            salt="review",
            expiry=timedelta(days=30),  # 30-day expiry for reviews
        )
        
        if not token_data:
            raise InvalidToken("Invalid or expired review token")
        
        shipment = await self.get(UUID(token_data["id"]))
        if not shipment:
            raise EntityNotFound("Shipment not found")
        
        # Refresh to load review relationship
        await self.session.refresh(shipment, ["review"])
        
        # Check if review already exists
        if shipment.review:
            raise AlreadyExistsError("Review already submitted for this shipment")
        
        # Create review
        new_review = Review(
            rating=rating,
            comment=comment if comment else None,
            shipment_id=shipment.id,
        )
        
        await self._add(new_review)
        logger.info(f"Review submitted for shipment {shipment.id} with rating {rating}")

    async def add_tag(self, shipment_id: UUID, tag_name: TagName) -> Shipment:
        """
        Add a tag to a shipment.
        
        Args:
            shipment_id: UUID of the shipment
            tag_name: TagName enum value
            
        Returns:
            Updated Shipment with tag added
            
        Raises:
            EntityNotFound: If shipment not found
            AlreadyExistsError: If tag already exists on shipment
        """
        shipment = await self.get(shipment_id)
        if not shipment:
            raise EntityNotFound("Shipment not found")
        
        # Refresh to load tags relationship
        await self.session.refresh(shipment, ["tags"])
        
        # Get or create tag
        tag = await self.session.scalar(
            select(Tag).where(Tag.name == tag_name)
        )
        
        if not tag:
            # Create tag with default instruction
            tag = Tag(
                name=tag_name,
                instruction=f"Handle with care: {tag_name.value}",
            )
            await self._add(tag)
        
        # Check if tag already exists on shipment
        if tag in shipment.tags:
            raise AlreadyExistsError(f"Tag '{tag_name.value}' already exists on this shipment")
        
        # Add tag to shipment
        shipment.tags.append(tag)
        await self.session.commit()
        await self.session.refresh(shipment, ["tags"])
        
        logger.info(f"Added tag '{tag_name.value}' to shipment {shipment_id}")
        return shipment

    async def remove_tag(self, shipment_id: UUID, tag_name: TagName) -> Shipment:
        """
        Remove a tag from a shipment.
        
        Args:
            shipment_id: UUID of the shipment
            tag_name: TagName enum value
            
        Returns:
            Updated Shipment with tag removed
            
        Raises:
            EntityNotFound: If shipment not found or tag doesn't exist
        """
        shipment = await self.get(shipment_id)
        if not shipment:
            raise EntityNotFound("Shipment not found")
        
        # Refresh to load tags relationship
        await self.session.refresh(shipment, ["tags"])
        
        # Find tag
        tag = await self.session.scalar(
            select(Tag).where(Tag.name == tag_name)
        )
        
        if not tag or tag not in shipment.tags:
            raise EntityNotFound(f"Tag '{tag_name.value}' not found on this shipment")
        
        # Remove tag from shipment
        shipment.tags.remove(tag)
        await self.session.commit()
        await self.session.refresh(shipment, ["tags"])
        
        logger.info(f"Removed tag '{tag_name.value}' from shipment {shipment_id}")
        return shipment

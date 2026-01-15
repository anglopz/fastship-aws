"""
Delivery Partner service
"""
from typing import Optional, Sequence

from typing import Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.schemas.delivery_partner import DeliveryPartnerCreate
from app.core.exceptions import DeliveryPartnerNotAvailable
from app.core.mail import MailClient
from app.database.models import DeliveryPartner, Location, Shipment

from .user import UserService


class DeliveryPartnerService(UserService):
    """Service for delivery partner operations"""
    
    def __init__(
        self,
        session: AsyncSession,
        mail_client: Optional[MailClient] = None,
    ):
        # Phase 3: BackgroundTasks removed, using Celery as primary method
        super().__init__(DeliveryPartner, session, mail_client=mail_client)

    async def add(self, delivery_partner: DeliveryPartnerCreate):
        """
        Create a new delivery partner and send verification email.
        
        Phase 3: Populates servicable_locations relationship from servicable_locations in schema.
        """
        # Extract servicable_locations from schema (now uses relationship directly)
        partner_data = delivery_partner.model_dump()
        servicable_locations = partner_data.pop("servicable_locations", [])
        
        # Create delivery partner (without servicable_locations, as it's a relationship)
        partner = await self._add_user(partner_data, router_prefix="partner")
        
        # Populate servicable_locations relationship
        if servicable_locations:
            locations = []
            for zip_code in servicable_locations:
                # Get or create Location
                location = await self.session.scalar(
                    select(Location).where(Location.zip_code == zip_code)
                )
                if not location:
                    location = Location(zip_code=zip_code)
                    await self._add(location)
                locations.append(location)
            
            # Set the relationship
            partner.servicable_locations = locations
            await self.session.commit()
            await self.session.refresh(partner, ["servicable_locations"])
        
        return partner

    async def verify_email(self, token: str) -> None:
        """Verify delivery partner email using verification token"""
        await super().verify_email(token)

    async def get_partner_by_zipcode(self, zipcode: int) -> Sequence[DeliveryPartner]:
        """
        Get delivery partners that service a given zipcode.
        
        Phase 3: Uses servicable_locations relationship only (ARRAY field removed).
        """
        return (
            await self.session.scalars(
                select(DeliveryPartner)
                .join(Location, DeliveryPartner.servicable_locations)
                .where(Location.zip_code == zipcode)
            )
        ).all()
    
    async def assign_shipment(self, shipment: Shipment):
        """Assign a delivery partner to a shipment based on zipcode and capacity"""
        eligible_partners = await self.get_partner_by_zipcode(shipment.destination)
        
        for partner in eligible_partners:
            if partner.current_handling_capacity > 0:
                partner.shipments.append(shipment)
                return partner

        # If no eligible partners found or partners have reached max handling capacity
        raise DeliveryPartnerNotAvailable("No delivery partner available")

    async def update(self, partner: DeliveryPartner):
        """Update a delivery partner"""
        return await self._update(partner)

    async def token(self, email: str, password: str) -> str:
        """Generate JWT token for delivery partner"""
        # Phase 2: require_verification=True (enforce email verification)
        return await self._generate_token(email, password, require_verification=True)


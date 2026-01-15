"""
Shipment Event Service - handles event creation and timeline management
"""
import logging
from datetime import timedelta
from random import randint
from typing import Optional
from uuid import UUID

# Phase 3: BackgroundTasks removed, using Celery as primary method
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.mail import MailClient
from app.database.models import Shipment, ShipmentEvent, ShipmentStatus
from app.database.redis import add_shipment_verification_code

from .base import BaseService

logger = logging.getLogger(__name__)

# Try to import Celery tasks (optional - fallback to BackgroundTasks if not available)
try:
    from app.celery_app import send_email_with_template_task, send_sms_task
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    logger.warning("Celery not available, falling back to BackgroundTasks")


class ShipmentEventService(BaseService):
    """Service for shipment event operations"""
    
    def __init__(
        self,
        session: AsyncSession,
        mail_client: Optional[MailClient] = None,
    ):
        super().__init__(ShipmentEvent, session)
        self.mail_client = mail_client
        # Phase 3: BackgroundTasks removed, using Celery as primary method

    async def create_event(
        self,
        shipment: Shipment,
        status: ShipmentStatus,
        location: Optional[int] = None,
        description: Optional[str] = None,
    ) -> ShipmentEvent:
        """
        Create a new shipment event
        
        Args:
            shipment: The shipment to create an event for
            status: The status for this event
            location: Optional location zipcode (uses last event location if not provided)
            description: Optional description (auto-generated if not provided)
            
        Returns:
            Created ShipmentEvent
        """
        # Get last event to inherit location if not provided
        if location is None:
            last_event = await self.get_latest_event(shipment)
            if last_event:
                location = last_event.location
            else:
                # No previous events, use shipment destination
                location = shipment.destination
        
        # Generate description if not provided
        if description is None:
            description = self._generate_description(status, location)
        
        # Create new event
        new_event = ShipmentEvent(
            shipment_id=shipment.id,
            status=status,
            location=location,
            description=description,
        )
        
        # Save event
        event = await self._add(new_event)
        
        # Send notification email (if mail client available and not in_transit)
        if self.mail_client and status != ShipmentStatus.in_transit:
            # Reload shipment with relationships for email
            await self.session.refresh(shipment, ["seller", "delivery_partner"])
            
            # Phase 3: Use Celery as primary method (BackgroundTasks removed)
            if CELERY_AVAILABLE:
                # Use Celery tasks (async call, but task runs in worker)
                await self._send_status_notification_celery(shipment, status)
            else:
                logger.warning("Celery not available - notifications will not be sent")
        
        return event

    async def get_latest_event(self, shipment: Shipment) -> Optional[ShipmentEvent]:
        """
        Get the latest event for a shipment (chronologically oldest, first in timeline)
        
        Args:
            shipment: The shipment to get events for
            
        Returns:
            Latest ShipmentEvent or None if no events exist
        """
        if not shipment.events:
            return None
        
        # Timeline is already sorted reverse chronologically (newest first)
        # So the last item is the oldest (first event)
        timeline = shipment.timeline
        if not timeline:
            return None
        
        # Return the oldest event (last in reversed timeline)
        return timeline[-1] if timeline else None

    async def get_shipment_timeline(self, shipment_id: UUID) -> list[ShipmentEvent]:
        """
        Get timeline of events for a shipment
        
        Args:
            shipment_id: UUID of the shipment
            
        Returns:
            List of events in reverse chronological order (newest first)
        """
        shipment = await self.session.get(Shipment, shipment_id)
        if not shipment:
            return []
        
        # Refresh to load events relationship
        await self.session.refresh(shipment, ["events"])
        return shipment.timeline

    def _generate_description(self, status: ShipmentStatus, location: int) -> str:
        """
        Generate automatic description for an event based on status
        
        Args:
            status: The shipment status
            location: The location zipcode
            
        Returns:
            Generated description string
        """
        match status:
            case ShipmentStatus.placed:
                return "assigned delivery partner"
            case ShipmentStatus.out_for_delivery:
                return "shipment out for delivery"
            case ShipmentStatus.delivered:
                return "successfully delivered"
            case ShipmentStatus.cancelled:
                return "cancelled by seller"
            case ShipmentStatus.in_transit:
                return f"scanned at {location}"
            case _:
                return f"status updated to {status.value}"

    async def _send_status_notification(
        self,
        shipment: Shipment,
        status: ShipmentStatus,
    ):
        """
        Send status notification email and/or SMS (background task)
        
        Args:
            shipment: The shipment with loaded relationships
            status: The new status
        """
        try:
            # Phase 2: client_contact_email is now required, so it should always be present
            client_email = shipment.client_contact_email
            client_phone = getattr(shipment, "client_contact_phone", None)
            
            if not client_email:
                logger.warning(f"Shipment {shipment.id} missing client_contact_email (required field), skipping notification")
                return
            
            subject: str
            template_name: str
            context: dict = {}
            verification_code: Optional[int] = None
            
            match status:
                case ShipmentStatus.placed:
                    subject = "Your Order is Shipped 🚛"
                    template_name = "mail_placed.html"
                    # Ensure relationships are loaded
                    if not hasattr(shipment, 'seller') or shipment.seller is None:
                        await self.session.refresh(shipment, ["seller"])
                    if not hasattr(shipment, 'delivery_partner') or shipment.delivery_partner is None:
                        await self.session.refresh(shipment, ["delivery_partner"])
                    context = {
                        "seller": shipment.seller.name if shipment.seller else "FastShip",
                        "partner": shipment.delivery_partner.name if shipment.delivery_partner else "Delivery Partner",
                    }
                case ShipmentStatus.out_for_delivery:
                    subject = "Your Order is Arriving Soon 🛵"
                    template_name = "mail_out_for_delivery.html"
                    
                    # Generate 6-digit verification code
                    verification_code = randint(100_000, 999_999)
                    await add_shipment_verification_code(shipment.id, verification_code)
                    logger.info(f"Generated verification code {verification_code} for shipment {shipment.id}")
                    
                    # Send SMS if phone available
                    if client_phone and self.mail_client:
                        sms_sent = await self.mail_client.send_sms(
                            to=client_phone,
                            body=f"Your order is arriving soon! Share the {verification_code} code with your delivery executive to receive your package."
                        )
                        if sms_sent:
                            logger.info(f"Verification code SMS sent to {client_phone} for shipment {shipment.id}")
                        else:
                            # SMS failed, include code in email
                            context["verification_code"] = verification_code
                    else:
                        # No phone, include code in email
                        context["verification_code"] = verification_code
                    
                case ShipmentStatus.delivered:
                    subject = "Your Order is Delivered ✅"
                    template_name = "mail_delivered.html"
                    context = {"seller": shipment.seller.name}
                    
                    # Generate review token for review link
                    from app.utils import generate_url_safe_token
                    from app.config import app_settings
                    
                    review_token = generate_url_safe_token(
                        {"id": str(shipment.id)},
                        salt="review",
                        expiry=timedelta(days=30),  # 30-day expiry for reviews
                    )
                    context["review_url"] = (
                        f"http://{app_settings.APP_DOMAIN}/shipment/review?token={review_token}"
                    )
                case ShipmentStatus.cancelled:
                    subject = "Your Order is Cancelled ❌"
                    template_name = "mail_cancelled.html"
                    context = {}
                case _:
                    # Don't send email for in_transit or unknown status
                    return
            
            # Send email notification
            await self.mail_client.send_email_with_template(
                recipients=[EmailStr(client_email)],
                subject=subject,
                template_name=template_name,
                context=context,
            )
            logger.info(f"Status notification sent to {client_email} for shipment {shipment.id}")
        except Exception as e:
            logger.error(f"Failed to send status notification for shipment {shipment.id}: {e}")

    async def _send_status_notification_celery(
        self,
        shipment: Shipment,
        status: ShipmentStatus,
    ):
        """
        Send status notification using Celery tasks (Phase 2).
        
        This method prepares the notification data and queues it via Celery.
        
        Args:
            shipment: The shipment with loaded relationships
            status: The new status
        """
        try:
            # Phase 2: client_contact_email is now required, so it should always be present
            client_email = shipment.client_contact_email
            client_phone = getattr(shipment, "client_contact_phone", None)
            
            if not client_email:
                logger.warning(f"Shipment {shipment.id} missing client_contact_email (required field), skipping notification")
                return
            
            subject: str
            template_name: str
            context: dict = {}
            verification_code: Optional[int] = None
            
            match status:
                case ShipmentStatus.placed:
                    subject = "Your Order is Shipped 🚛"
                    template_name = "mail_placed.html"
                    # Ensure relationships are loaded
                    if not hasattr(shipment, 'seller') or shipment.seller is None:
                        await self.session.refresh(shipment, ["seller"])
                    if not hasattr(shipment, 'delivery_partner') or shipment.delivery_partner is None:
                        await self.session.refresh(shipment, ["delivery_partner"])
                    context = {
                        "seller": shipment.seller.name if shipment.seller else "FastShip",
                        "partner": shipment.delivery_partner.name if shipment.delivery_partner else "Delivery Partner",
                    }
                case ShipmentStatus.out_for_delivery:
                    subject = "Your Order is Arriving Soon 🛵"
                    template_name = "mail_out_for_delivery.html"
                    
                    # Generate 6-digit verification code
                    verification_code = randint(100_000, 999_999)
                    await add_shipment_verification_code(shipment.id, verification_code)
                    logger.info(f"Generated verification code {verification_code} for shipment {shipment.id}")
                    
                    # Always include verification code in email as backup
                    # (SMS may fail due to rate limits or other issues)
                    context["verification_code"] = verification_code
                    
                    # Send SMS via Celery if phone available (as primary method)
                    # But email will always contain the code as fallback
                    if client_phone:
                        # Format phone number to E.164 format (required by Twilio)
                        # If phone doesn't start with +, assume it's a Spanish number and add +34
                        formatted_phone = client_phone
                        if not formatted_phone.startswith('+'):
                            # Remove leading 0 if present (Spanish format: 0XXXXXXXXX -> +34XXXXXXXXX)
                            if formatted_phone.startswith('0'):
                                formatted_phone = formatted_phone[1:]
                            formatted_phone = f"+34{formatted_phone}"
                        
                        send_sms_task.delay(
                            to=formatted_phone,
                            body=f"Your order is arriving soon! Share the {verification_code} code with your delivery executive to receive your package."
                        )
                        logger.info(f"Queued SMS to {formatted_phone} for shipment {shipment.id} (email also contains code as backup)")
                    
                case ShipmentStatus.delivered:
                    subject = "Your Order is Delivered ✅"
                    template_name = "mail_delivered.html"
                    context = {"seller": shipment.seller.name}
                    
                    # Generate review token for review link
                    from app.utils import generate_url_safe_token
                    from app.config import app_settings
                    
                    review_token = generate_url_safe_token(
                        {"id": str(shipment.id)},
                        salt="review",
                        expiry=timedelta(days=30),  # 30-day expiry for reviews
                    )
                    context["review_url"] = (
                        f"http://{app_settings.APP_DOMAIN}/shipment/review?token={review_token}"
                    )
                    
                    # Send SMS via Celery if phone available
                    if client_phone:
                        # Format phone number to E.164 format (required by Twilio)
                        # If phone doesn't start with +, assume it's a Spanish number and add +34
                        formatted_phone = client_phone
                        if not formatted_phone.startswith('+'):
                            # Remove leading 0 if present (Spanish format: 0XXXXXXXXX -> +34XXXXXXXXX)
                            if formatted_phone.startswith('0'):
                                formatted_phone = formatted_phone[1:]
                            formatted_phone = f"+34{formatted_phone}"
                        
                        send_sms_task.delay(
                            to=formatted_phone,
                            body=f"✅ Your order has been delivered! Thank you for choosing FastShip. We hope you're satisfied with your delivery."
                        )
                        logger.info(f"Queued delivery confirmation SMS to {formatted_phone} for shipment {shipment.id}")
                case ShipmentStatus.delivered:
                    subject = "Your Order is Delivered ✅"
                    template_name = "mail_delivered.html"
                    # Ensure seller relationship is loaded
                    if not hasattr(shipment, 'seller') or shipment.seller is None:
                        await self.session.refresh(shipment, ["seller"])
                    context = {"seller": shipment.seller.name if shipment.seller else "FastShip"}
                    
                    # Generate review token for review link
                    from app.utils import generate_url_safe_token
                    from app.config import app_settings
                    
                    review_token = generate_url_safe_token(
                        {"id": str(shipment.id)},
                        salt="review",
                        expiry=timedelta(days=30),  # 30-day expiry for reviews
                    )
                    context["review_url"] = (
                        f"http://{app_settings.APP_DOMAIN}/shipment/review?token={review_token}"
                    )
                    
                    # Send SMS via Celery if phone available
                    if client_phone:
                        # Format phone number to E.164 format (required by Twilio)
                        # If phone doesn't start with +, assume it's a Spanish number and add +34
                        formatted_phone = client_phone
                        if not formatted_phone.startswith('+'):
                            # Remove leading 0 if present (Spanish format: 0XXXXXXXXX -> +34XXXXXXXXX)
                            if formatted_phone.startswith('0'):
                                formatted_phone = formatted_phone[1:]
                            formatted_phone = f"+34{formatted_phone}"
                        
                        send_sms_task.delay(
                            to=formatted_phone,
                            body=f"✅ Your order has been delivered! Thank you for choosing FastShip. We hope you're satisfied with your delivery."
                        )
                        logger.info(f"Queued delivery confirmation SMS to {formatted_phone} for shipment {shipment.id}")
                case ShipmentStatus.cancelled:
                    subject = "Your Order is Cancelled ❌"
                    template_name = "mail_cancelled.html"
                    context = {}
                case _:
                    # Don't send email for in_transit or unknown status
                    return
            
            # Queue email notification via Celery
            send_email_with_template_task.delay(
                recipients=[client_email],
                subject=subject,
                context=context,
                template_name=template_name,
            )
            logger.info(f"Queued status notification email to {client_email} for shipment {shipment.id}")
        except Exception as e:
            logger.error(f"Failed to queue status notification for shipment {shipment.id}: {e}", exc_info=True)


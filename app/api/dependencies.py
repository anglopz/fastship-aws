"""
API dependencies for dependency injection
"""
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ClientNotAuthorized, InvalidToken
from app.core.mail import MailClient, get_mail_client
from app.core.security import oauth2_scheme_seller, oauth2_scheme_partner
from app.database.models import DeliveryPartner, Seller
from app.database.redis import is_jti_blacklisted
from app.database.session import get_session
from app.services.delivery_partner import DeliveryPartnerService
from app.services.event import ShipmentEventService
from app.services.seller import SellerService
from app.services.shipment import ShipmentService
from app.utils import decode_access_token


# Asynchronous database session dep annotation
SessionDep = Annotated[AsyncSession, Depends(get_session)]


# Access token data dep
async def _get_access_token(token: str) -> dict:
    """Validate and decode access token"""
    data = decode_access_token(token)

    # Validate the token
    if data is None or await is_jti_blacklisted(data["jti"]):
        raise InvalidToken("Invalid or expired access token")

    return data


# Seller access token data
async def get_seller_access_token(
    token: Annotated[str, Depends(oauth2_scheme_seller)],
) -> dict:
    """Get and validate seller access token"""
    return await _get_access_token(token)


# Delivery partner access token data
async def get_partner_access_token(
    token: Annotated[str, Depends(oauth2_scheme_partner)],
) -> dict:
    """Get and validate delivery partner access token"""
    return await _get_access_token(token)


# Logged In Seller
async def get_current_seller(
    token_data: Annotated[dict, Depends(get_seller_access_token)],
    session: SessionDep,
):
    """Get the currently authenticated seller"""
    seller = await session.get(
        Seller,
        UUID(token_data["user"]["id"]),
    )

    if seller is None:
        raise ClientNotAuthorized("Not authorized")

    return seller


# Logged In Delivery partner
async def get_current_partner(
    token_data: Annotated[dict, Depends(get_partner_access_token)],
    session: SessionDep,
):
    """Get the currently authenticated delivery partner"""
    partner = await session.get(
        DeliveryPartner,
        UUID(token_data["user"]["id"]),
    )

    if partner is None:
        raise ClientNotAuthorized("Not authorized")

    return partner


# Mail client dep
def get_mail_service() -> MailClient:
    """Get mail client instance (singleton)"""
    return get_mail_client()


# Event service dep
def get_event_service(
    session: SessionDep,
    mail_client: Annotated[MailClient, Depends(get_mail_service)],
):
    """Create event service with mail dependencies"""
    return ShipmentEventService(
        session,
        mail_client=mail_client,
    )


# Shipment service dep
def get_shipment_service(
    session: SessionDep,
    mail_client: Annotated[MailClient, Depends(get_mail_service)],
):
    """Create shipment service with delivery partner service, event service, and mail dependencies"""
    return ShipmentService(
        session,
        DeliveryPartnerService(session, mail_client=mail_client),
        ShipmentEventService(session, mail_client=mail_client),
        mail_client=mail_client,
    )


# Seller service dep
def get_seller_service(
    session: SessionDep,
    mail_client: Annotated[MailClient, Depends(get_mail_service)],
):
    """Create seller service with mail dependencies"""
    return SellerService(
        session,
        mail_client=mail_client,
    )


# Delivery partner service dep
def get_delivery_partner_service(
    session: SessionDep,
    mail_client: Annotated[MailClient, Depends(get_mail_service)],
):
    """Create delivery partner service with mail dependencies"""
    return DeliveryPartnerService(session, mail_client=mail_client)


# Seller dep annotation
SellerDep = Annotated[
    Seller,
    Depends(get_current_seller),
]

# Delivery partner dep annotation
DeliveryPartnerDep = Annotated[
    DeliveryPartner,
    Depends(get_current_partner),
]

# Shipment service dep annotation
ShipmentServiceDep = Annotated[
    ShipmentService,
    Depends(get_shipment_service),
]

# Seller service dep annotation
SellerServiceDep = Annotated[
    SellerService,
    Depends(get_seller_service),
]

# Delivery partner service dep annotation
DeliveryPartnerServiceDep = Annotated[
    DeliveryPartnerService,
    Depends(get_delivery_partner_service),
]

# Backward compatibility - keep old get_current_user for existing code
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme_seller)]) -> dict:
    """Backward compatibility alias for get_seller_access_token"""
    return await get_seller_access_token(token)

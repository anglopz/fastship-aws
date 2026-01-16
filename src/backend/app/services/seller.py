"""
Seller service - refactored to use UserService base class
"""
import logging
from typing import Optional

from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.seller import SellerCreate
from app.core.mail import MailClient
from app.database.models import Seller

from .user import UserService

logger = logging.getLogger(__name__)


class SellerService(UserService):
    """Service for seller operations"""
    
    def __init__(
        self,
        session: AsyncSession,
        mail_client: Optional[MailClient] = None,
    ):
        # Phase 3: BackgroundTasks removed, using Celery as primary method
        super().__init__(Seller, session, mail_client=mail_client)
        self.mail_client = mail_client

    async def add(self, seller_create: SellerCreate) -> Seller:
        """Create a new seller and send verification email"""
        # _add_user now handles verification email sending
        seller = await self._add_user(seller_create.model_dump(), router_prefix="seller")
        return seller

    async def verify_email(self, token: str) -> None:
        """Verify seller email using verification token"""
        await super().verify_email(token)

    async def token(self, email: str, password: str) -> str:
        """Generate JWT token for seller"""
        # Phase 2: require_verification=True (enforce email verification)
        return await self._generate_token(email, password, require_verification=True)

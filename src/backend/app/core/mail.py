"""
Mail service with SMTP connection, pooling, and retry logic
"""
import asyncio
import logging
from typing import Optional

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from pydantic import EmailStr
from twilio.rest import Client as TwilioClient

from app.config import mail_settings, twilio_settings
from app.utils import TEMPLATE_DIR

logger = logging.getLogger(__name__)


class MailClient:
    """
    Mail client with connection pooling, retry logic, and template rendering.
    
    This service is designed to be injectable into other services like
    SellerService and ShipmentService.
    """
    
    def __init__(self):
        """Initialize mail client with connection pooling"""
        self._fastmail: Optional[FastMail] = None
        self._template_env: Optional[Environment] = None
        self._twilio_client: Optional[TwilioClient] = None
        self._max_retries = 3
        self._retry_delay = 1.0  # Initial delay in seconds
        
    @property
    def fastmail(self) -> FastMail:
        """Lazy initialization of FastMail client with connection pooling"""
        if self._fastmail is None:
            # Get SMTP config based on EMAIL_MODE
            smtp_config = mail_settings.get_smtp_config()
            
            # FastMail handles connection pooling internally
            config = ConnectionConfig(
                MAIL_USERNAME=smtp_config["MAIL_USERNAME"],
                MAIL_PASSWORD=smtp_config["MAIL_PASSWORD"],
                MAIL_FROM=mail_settings.MAIL_FROM,
                MAIL_PORT=smtp_config["MAIL_PORT"],
                MAIL_SERVER=smtp_config["MAIL_SERVER"],
                MAIL_FROM_NAME=mail_settings.MAIL_FROM_NAME,
                MAIL_STARTTLS=mail_settings.MAIL_STARTTLS,
                MAIL_SSL_TLS=mail_settings.MAIL_SSL_TLS,
                USE_CREDENTIALS=mail_settings.USE_CREDENTIALS,
                VALIDATE_CERTS=mail_settings.VALIDATE_CERTS,
                TEMPLATE_FOLDER=str(TEMPLATE_DIR),
            )
            self._fastmail = FastMail(config)
        return self._fastmail
    
    async def verify_connection(self) -> dict:
        """
        Verify SMTP connection by attempting to connect and authenticate.
        
        Returns:
            Dictionary with connection status and details
        """
        try:
            smtp_config = mail_settings.get_smtp_config()
            
            # Validate required settings
            if not smtp_config["MAIL_USERNAME"] or not smtp_config["MAIL_PASSWORD"]:
                return {
                    "status": "error",
                    "message": "SMTP credentials not configured",
                    "mode": mail_settings.EMAIL_MODE,
                    "server": smtp_config.get("MAIL_SERVER", "unknown"),
                    "port": smtp_config.get("MAIL_PORT", "unknown"),
                }
            
            # Try to create a test connection
            test_config = ConnectionConfig(
                MAIL_USERNAME=smtp_config["MAIL_USERNAME"],
                MAIL_PASSWORD=smtp_config["MAIL_PASSWORD"],
                MAIL_PORT=smtp_config["MAIL_PORT"],
                MAIL_SERVER=smtp_config["MAIL_SERVER"],
                MAIL_STARTTLS=mail_settings.MAIL_STARTTLS,
                MAIL_SSL_TLS=mail_settings.MAIL_SSL_TLS,
                USE_CREDENTIALS=mail_settings.USE_CREDENTIALS,
                VALIDATE_CERTS=mail_settings.VALIDATE_CERTS,
            )
            
            # Create a temporary FastMail instance to test connection
            test_fastmail = FastMail(test_config)
            
            # Try to send a test message to verify connection
            # Use a test recipient that won't actually receive (or use Mailtrap's test inbox)
            test_message = MessageSchema(
                recipients=["test@example.com"],  # Dummy recipient for connection test
                subject="Connection Test",
                body="This is a connection test",
                subtype=MessageType.plain,
            )
            
            # Attempt to send (this will verify connection and authentication)
            # Note: In sandbox mode (Mailtrap), this will work but email won't be delivered
            # In production, we should use a real test email or skip actual sending
            try:
                await test_fastmail.send_message(test_message)
                logger.info("SMTP connection test successful")
            except Exception as send_error:
                # If sending fails but it's a delivery error (not auth/connection), consider it a success
                error_str = str(send_error).lower()
                if "authentication" in error_str or "connection" in error_str or "refused" in error_str:
                    raise  # Re-raise auth/connection errors
                # Delivery errors (like invalid recipient) mean connection worked
                logger.info(f"SMTP connection verified (delivery error expected): {send_error}")
            
            return {
                "status": "success",
                "message": "SMTP connection verified",
                "mode": mail_settings.EMAIL_MODE,
                "server": smtp_config["MAIL_SERVER"],
                "port": smtp_config["MAIL_PORT"],
                "username": smtp_config["MAIL_USERNAME"][:3] + "***" if len(smtp_config["MAIL_USERNAME"]) > 3 else "***",
            }
        except Exception as e:
            logger.error(f"SMTP connection verification failed: {e}")
            smtp_config = mail_settings.get_smtp_config()
            return {
                "status": "error",
                "message": f"SMTP connection failed: {str(e)}",
                "mode": mail_settings.EMAIL_MODE,
                "server": smtp_config.get("MAIL_SERVER", "unknown"),
                "port": smtp_config.get("MAIL_PORT", "unknown"),
            }
    
    @property
    def template_env(self) -> Environment:
        """Lazy initialization of Jinja2 template environment"""
        if self._template_env is None:
            self._template_env = Environment(
                loader=FileSystemLoader(str(TEMPLATE_DIR)),
                autoescape=True,
            )
        return self._template_env
    
    def render_template(
        self,
        template_name: str,
        context: dict,
    ) -> str:
        """
        Render an email template with the given context.
        
        This is separated from sending logic for testability and reusability.
        
        Args:
            template_name: Name of the template file (e.g., "mail_placed.html")
            context: Dictionary of variables to pass to the template
            
        Returns:
            Rendered HTML string
            
        Raises:
            TemplateNotFound: If template file doesn't exist
            Exception: If template rendering fails
        """
        try:
            template = self.template_env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound as e:
            logger.error(f"Template not found: {template_name}")
            raise
        except Exception as e:
            logger.error(f"Error rendering template {template_name}: {e}")
            raise
    
    async def send_email(
        self,
        recipients: list[EmailStr],
        subject: str,
        body: str,
        subtype: MessageType = MessageType.plain,
    ) -> bool:
        """
        Send a plain text or HTML email with retry logic.
        
        Args:
            recipients: List of recipient email addresses
            subject: Email subject
            body: Email body (plain text or HTML)
            subtype: Message type (plain or html)
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        message = MessageSchema(
            recipients=recipients,
            subject=subject,
            body=body,
            subtype=subtype,
        )
        
        return await self._send_with_retry(message)
    
    async def send_email_with_template(
        self,
        recipients: list[EmailStr],
        subject: str,
        template_name: str,
        context: dict,
    ) -> bool:
        """
        Send an email using a template with retry logic.
        
        Args:
            recipients: List of recipient email addresses
            subject: Email subject
            template_name: Name of the template file
            context: Dictionary of variables for template rendering
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            # Render template separately from sending
            html_body = self.render_template(template_name, context)
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {e}")
            return False
        
        message = MessageSchema(
            recipients=recipients,
            subject=subject,
            body=html_body,
            subtype=MessageType.html,
        )
        
        return await self._send_with_retry(message)
    
    async def _send_with_retry(
        self,
        message: MessageSchema,
    ) -> bool:
        """
        Send email with exponential backoff retry logic.
        
        Args:
            message: MessageSchema to send
            
        Returns:
            True if sent successfully, False otherwise
        """
        last_exception = None
        
        for attempt in range(self._max_retries):
            try:
                await self.fastmail.send_message(message)
                logger.info(
                    f"Email sent successfully to {message.recipients} "
                    f"(attempt {attempt + 1})"
                )
                return True
            except Exception as e:
                last_exception = e
                logger.warning(
                    f"Email send attempt {attempt + 1} failed: {e}"
                )
                
                # Don't retry on the last attempt
                if attempt < self._max_retries - 1:
                    # Exponential backoff: 1s, 2s, 4s
                    delay = self._retry_delay * (2 ** attempt)
                    logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
        
        # All retries failed
        logger.error(
            f"Failed to send email after {self._max_retries} attempts: "
            f"{last_exception}"
        )
        return False
    
    @property
    def twilio_client(self) -> Optional[TwilioClient]:
        """Lazy initialization of Twilio client for SMS"""
        if self._twilio_client is None:
            # Only initialize if Twilio credentials are provided
            if twilio_settings.TWILIO_SID and twilio_settings.TWILIO_AUTH_TOKEN:
                try:
                    self._twilio_client = TwilioClient(
                        twilio_settings.TWILIO_SID,
                        twilio_settings.TWILIO_AUTH_TOKEN,
                    )
                    logger.info("Twilio client initialized")
                except Exception as e:
                    logger.warning(f"Failed to initialize Twilio client: {e}")
                    return None
            else:
                logger.warning("Twilio credentials not configured, SMS disabled")
                return None
        return self._twilio_client

    async def send_sms(self, to: str, body: str) -> bool:
        """
        Send SMS via Twilio.
        
        Args:
            to: Phone number to send SMS to (E.164 format)
            body: SMS message body
            
        Returns:
            True if SMS was sent successfully, False otherwise
        """
        if not self.twilio_client:
            logger.warning("Twilio client not available, SMS not sent")
            return False
        
        if not twilio_settings.TWILIO_NUMBER:
            logger.warning("Twilio number not configured, SMS not sent")
            return False
        
        try:
            message = self.twilio_client.messages.create(
                from_=twilio_settings.TWILIO_NUMBER,
                to=to,
                body=body,
            )
            logger.info(f"SMS sent successfully to {to} (SID: {message.sid})")
            return True
        except Exception as e:
            logger.error(f"Failed to send SMS to {to}: {e}")
            return False

    async def close(self):
        """Close mail client connections"""
        if self._fastmail:
            # FastMail doesn't expose a close method, but connections
            # are managed internally and will be cleaned up
            self._fastmail = None
            self._template_env = None
        # Twilio client doesn't need explicit closing
        self._twilio_client = None


# Singleton instance (optional - can also be instantiated per service)
_mail_client: Optional[MailClient] = None


def get_mail_client() -> MailClient:
    """Get or create singleton mail client instance"""
    global _mail_client
    if _mail_client is None:
        _mail_client = MailClient()
    return _mail_client


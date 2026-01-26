"""
Celery task queue for background task processing.

This module provides Celery tasks for email and SMS sending,
replacing FastAPI BackgroundTasks with a distributed, persistent task queue.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from asgiref.sync import async_to_sync
from celery import Celery

from app.config import db_settings, logging_settings, mail_settings, twilio_settings
from app.utils import TEMPLATE_DIR

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    # Only needed for typing; imported lazily at runtime elsewhere.
    from fastapi_mail import MessageSchema

# Create FastMail instance for Celery tasks
# Note: Celery tasks must be synchronous, so we use async_to_sync wrapper
_fastmail_instance = None


def get_fastmail():
    """Get or create FastMail instance (singleton)"""
    # NOTE: We import FastMail lazily so the API container (which only enqueues
    # Celery tasks) doesn't pay the memory cost of mail dependencies.
    from fastapi_mail import ConnectionConfig, FastMail

    global _fastmail_instance
    # Always recreate to pick up new configuration
    # This ensures we get the latest mail settings after restart
    # Use get_smtp_config() to get correct credentials based on EMAIL_MODE
    smtp_config = mail_settings.get_smtp_config()
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
    _fastmail_instance = FastMail(config)
    logger.info(f"FastMail configured for {smtp_config['MAIL_SERVER']}:{smtp_config['MAIL_PORT']} (mode: {mail_settings.EMAIL_MODE})")
    return _fastmail_instance


# Convert async send_message to sync for Celery
def send_message_sync(message: MessageSchema, template_name: str | None = None):
    """Synchronous wrapper for FastMail send_message"""
    fastmail = get_fastmail()
    send_message = async_to_sync(fastmail.send_message)
    return send_message(message, template_name=template_name)


# Create Twilio client (if configured)
_twilio_client = None


def get_twilio_client():
    """Get or create Twilio client (singleton)"""
    # NOTE: Lazy import so API container doesn't load Twilio dependencies.
    from twilio.rest import Client as TwilioClient

    global _twilio_client
    if _twilio_client is None and twilio_settings.TWILIO_SID:
        _twilio_client = TwilioClient(
            twilio_settings.TWILIO_SID,
            twilio_settings.TWILIO_AUTH_TOKEN,
        )
    return _twilio_client


# Create Celery app
celery_app = Celery(
    "fastship_tasks",
    broker=db_settings.REDIS_URL,
    backend=db_settings.REDIS_URL,
    broker_connection_retry_on_startup=True,
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_mail_task(
    self,
    recipients: list[str],
    subject: str,
    body: str,
):
    """
    Send plain text email via Celery.
    
    Args:
        recipients: List of email addresses
        subject: Email subject
        body: Plain text email body
        
    Returns:
        str: Success message
    """
    try:
        from fastapi_mail import MessageSchema, MessageType

        send_message_sync(
            message=MessageSchema(
                recipients=recipients,
                subject=subject,
                body=body,
                subtype=MessageType.plain,
            ),
        )
        logger.info(f"Email sent successfully to {recipients}")
        return "Message sent successfully"
    except Exception as exc:
        logger.error(f"Failed to send email to {recipients}: {exc}", exc_info=True)
        # Retry on failure (up to max_retries)
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_with_template_task(
    self,
    recipients: list[str],
    subject: str,
    context: dict,
    template_name: str,
):
    """
    Send HTML email with template via Celery.
    
    Args:
        recipients: List of email addresses
        subject: Email subject
        context: Template context variables
        template_name: Name of the template file (e.g., "mail_placed.html")
        
    Returns:
        str: Success message
    """
    try:
        from fastapi_mail import MessageSchema, MessageType

        send_message_sync(
            message=MessageSchema(
                recipients=recipients,
                subject=subject,
                template_body=context,
                subtype=MessageType.html,
            ),
            template_name=template_name,
        )
        logger.info(f"Template email sent successfully to {recipients} using {template_name}")
        return "Email sent successfully"
    except Exception as exc:
        logger.error(
            f"Failed to send template email to {recipients} using {template_name}: {exc}",
            exc_info=True,
        )
        # Retry on failure (up to max_retries)
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_sms_task(
    self,
    to: str,
    body: str,
):
    """
    Send SMS via Celery using Twilio.
    
    Args:
        to: Phone number to send SMS to
        body: SMS message body
        
    Returns:
        str: Success message or error message if Twilio not configured
    """
    twilio_client = get_twilio_client()
    if not twilio_client:
        logger.warning("Twilio not configured, skipping SMS")
        return "Twilio not configured"
    
    if not twilio_settings.TWILIO_NUMBER:
        logger.warning("Twilio number not configured, skipping SMS")
        return "Twilio number not configured"
    
    try:
        message = twilio_client.messages.create(
            from_=twilio_settings.TWILIO_NUMBER,
            to=to,
            body=body,
        )
        logger.info(f"SMS sent successfully to {to}: {message.sid}")
        return f"SMS sent successfully: {message.sid}"
    except Exception as exc:
        # Check if it's a Twilio REST exception
        from twilio.base.exceptions import TwilioRestException
        
        if isinstance(exc, TwilioRestException):
            # Handle specific Twilio error codes
            status_code = getattr(exc, 'status', None)
            error_msg = getattr(exc, 'msg', str(exc))
            
            # 429 = Rate limit exceeded (don't retry - won't help until limit resets)
            if status_code == 429:
                logger.warning(
                    f"Twilio rate limit exceeded for {to}. "
                    f"Error: {error_msg}. "
                    f"SMS not sent. Daily limit may be reached."
                )
                return f"Twilio rate limit exceeded: {error_msg}"
            
            # 400 = Bad request (don't retry - invalid data)
            if status_code == 400:
                logger.error(
                    f"Twilio bad request for {to}: {error_msg}. "
                    f"Check phone number format."
                )
                return f"Twilio bad request: {error_msg}"
            
            # Other 4xx errors (client errors) - don't retry
            if status_code and 400 <= status_code < 500:
                logger.error(
                    f"Twilio client error ({status_code}) for {to}: {error_msg}",
                    exc_info=True
                )
                return f"Twilio client error ({status_code}): {error_msg}"
            
            # 5xx errors (server errors) - retry
            if status_code and status_code >= 500:
                logger.error(
                    f"Twilio server error ({status_code}) for {to}: {error_msg}",
                    exc_info=True
                )
                # Retry server errors
                if self.request.retries < self.max_retries:
                    raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
                else:
                    logger.error(f"Max retries exceeded for SMS to {to}. Giving up.")
                    return f"Failed to send SMS after {self.max_retries} retries: {error_msg}"
            
            # Unknown Twilio error - log and don't retry
            logger.error(
                f"Twilio API error for {to}: {error_msg}",
                exc_info=True
            )
            return f"Twilio error: {error_msg}"
        else:
            # Non-Twilio exceptions - log and retry
            logger.error(f"Failed to send SMS to {to}: {exc}", exc_info=True)
            # Retry on failure (up to max_retries)
            if self.request.retries < self.max_retries:
                raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
            else:
                logger.error(f"Max retries exceeded for SMS to {to}. Giving up.")
                return f"Failed to send SMS after {self.max_retries} retries: {str(exc)}"


@celery_app.task(bind=True, max_retries=2, default_retry_delay=10)
def log_request_task(
    self,
    log_message: str,
):
    """
    Log request details asynchronously via Celery.
    
    Section 27: API Middleware - Async Logging
    
    Args:
        log_message: Log message in format "{method} {url} ({status_code}) {time_taken} s"
        
    Returns:
        str: Success message
    """
    from pathlib import Path
    
    try:
        # Ensure logs directory exists
        log_dir = Path(logging_settings.LOG_DIR)
        log_dir.mkdir(exist_ok=True)
        
        # Write to log file (Section 27 style)
        log_file_path = log_dir / logging_settings.LOG_FILE
        with open(log_file_path, "a") as file:
            file.write(f"{log_message}\n")
        
        # Also log via Python logging module for better structure
        logger.info(f"[Request] {log_message}")
        
        return "Request logged successfully"
    except Exception as exc:
        logger.error(f"Failed to log request: {exc}", exc_info=True)
        # Retry on failure (up to max_retries)
        raise self.retry(exc=exc, countdown=10 * (self.request.retries + 1))


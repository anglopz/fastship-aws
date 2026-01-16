"""
Health check endpoints
"""
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.mail import get_mail_client

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "",
    summary="API health check",
    description="""
    General health check endpoint for the API.
    
    Returns the overall health status of the API including Redis connection status.
    """,
    response_description="API health status",
    responses={
        200: {
            "description": "API is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "redis": "connected",
                        "service": "FastAPI Backend"
                    }
                }
            }
        }
    },
    operation_id="health_check",
)
async def health_check():
    """General health check endpoint with Redis status"""
    from app.database.redis import get_redis
    
    redis_status = "disconnected"
    try:
        redis_client = await get_redis()
        await redis_client.ping()
        redis_status = "connected"
    except Exception:
        redis_status = "disconnected"

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "healthy", "redis": redis_status, "service": "FastAPI Backend"}
    )


@router.get(
    "/email",
    summary="Verify SMTP email connection",
    description="""
    Verify the SMTP email connection configuration.
    
    This endpoint tests the SMTP connection based on the current EMAIL_MODE setting:
    - **sandbox**: Uses Mailtrap for testing (emails are captured, not sent)
    - **production**: Uses real SMTP server (emails are actually sent)
    
    **Use Cases:**
    - Verify email configuration before deployment
    - Troubleshoot email delivery issues
    - Monitor email service health
    
    **Response:**
    - Returns connection status and configuration details (without exposing sensitive data)
    - Server and port information
    - Current EMAIL_MODE setting
    
    **Note:** This endpoint does not actually send an email, only verifies the connection configuration.
    """,
    response_description="SMTP connection verification result",
    responses={
        200: {
            "description": "SMTP connection status",
            "content": {
                "application/json": {
                    "examples": {
                        "success": {
                            "summary": "Connection successful",
                            "value": {
                                "status": "success",
                                "message": "SMTP connection verified",
                                "mode": "sandbox",
                                "server": "sandbox.smtp.mailtrap.io",
                                "port": 587,
                                "username": "020***"
                            }
                        },
                        "error": {
                            "summary": "Connection failed",
                            "value": {
                                "status": "error",
                                "message": "SMTP connection failed: Authentication failed",
                                "mode": "production",
                                "server": "smtp.gmail.com",
                                "port": 587
                            }
                        }
                    }
                }
            }
        },
        500: {
            "description": "Internal server error during verification",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "message": "Internal error during SMTP verification"
                    }
                }
            }
        }
    },
    operation_id="verify_email_connection",
)
async def verify_email_connection():
    """
    Verify SMTP email connection.
    
    Tests the SMTP connection based on EMAIL_MODE configuration.
    Returns connection status without exposing sensitive credentials.
    """
    try:
        mail_client = get_mail_client()
        result = await mail_client.verify_connection()
        
        if result["status"] == "success":
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=result
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=result
            )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": f"Internal error during SMTP verification: {str(e)}",
                "mode": "unknown"
            }
        )

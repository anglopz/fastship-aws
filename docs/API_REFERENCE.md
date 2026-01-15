# FastShip API - Complete API Reference

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://fastship-api.onrender.com`

## Authentication

The API uses OAuth2 with JWT tokens. Two separate authentication schemes are available:

- **Seller Authentication**: For seller endpoints (`/seller/*`)
- **Delivery Partner Authentication**: For delivery partner endpoints (`/partner/*`)

### Getting Started

1. Register as a seller or delivery partner
2. Verify your email address
3. Login to get an access token
4. Use the token in the Authorization header: `Bearer <token>`

## Endpoints

### Health Check

#### GET /health/email

Verify SMTP email connection configuration.

**Description:**
Tests the SMTP connection based on the current EMAIL_MODE setting:
- **sandbox**: Uses Mailtrap for testing (emails are captured, not sent)
- **production**: Uses real SMTP server (emails are actually sent)

**Query Parameters:** None

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "SMTP connection verified",
  "mode": "sandbox",
  "server": "sandbox.smtp.mailtrap.io",
  "port": 587,
  "username": "020***"
}
```

**Response (500 Error):**
```json
{
  "status": "error",
  "message": "SMTP connection failed: Authentication failed",
  "mode": "production",
  "server": "smtp.gmail.com",
  "port": 587
}
```

**Use Cases:**
- Verify email configuration before deployment
- Troubleshoot email delivery issues
- Monitor email service health

**Note:** This endpoint does not actually send an email, only verifies the connection configuration.

---

## Seller Endpoints

### Register Seller

#### POST /seller/signup

Register a new seller account.

**Request Body:**
```json
{
  "name": "Acme Shipping Co.",
  "email": "seller@example.com",
  "password": "SecurePassword123!"
}
```

**Response:** `200 OK`
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Acme Shipping Co.",
  "email": "seller@example.com"
}
```

**Error Responses:**
- `409 Conflict`: Email already exists
- `422 Validation Error`: Invalid input data

### Login Seller

#### POST /seller/token

Authenticate and get access token.

**Request Body:** (form data)
```
username=seller@example.com
password=SecurePassword123!
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid credentials or email not verified

### Verify Email

#### GET /seller/verify

Verify seller email address.

**Query Parameters:**
- `token` (required): Verification token from email

**Response:** `200 OK`
```json
{
  "detail": "Email verified successfully"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid or expired token

### Request Password Reset

#### GET /seller/forgot_password

Request password reset email.

**Query Parameters:**
- `email` (required): Seller email address

**Response:** `200 OK`
```json
{
  "detail": "Password reset email sent"
}
```

### Get Seller Profile

#### GET /seller/me

Get the current authenticated seller's profile.

**Headers:**
- `Authorization: Bearer <token>` (required)

**Response:** `200 OK`
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Acme Shipping Co.",
  "email": "seller@example.com"
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid or expired token

### Get Seller Shipments

#### GET /seller/shipments

Get all shipments created by the authenticated seller.

**Headers:**
- `Authorization: Bearer <token>` (required)

**Response:** `200 OK`
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "content": "Electronics",
    "weight": 5.5,
    "destination": 887,
    "status": "in_transit",
    "estimated_delivery": "2026-01-10T12:00:00",
    "client_contact_email": "client@example.com",
    "client_contact_phone": "+34601539533",
    "tags": ["express", "fragile"]
  }
]
```

**Error Responses:**
- `401 Unauthorized`: Invalid or expired token

### Logout Seller

#### GET /seller/logout

Logout and blacklist token.

**Headers:**
- `Authorization: Bearer <token>` (required)

**Response:** `200 OK`
```json
{
  "detail": "Logged out successfully"
}
```

---

## Delivery Partner Endpoints

### Register Delivery Partner

#### POST /partner/signup

Register a new delivery partner account.

**Request Body:**
```json
{
  "name": "FastDelivery Co.",
  "email": "partner@example.com",
  "password": "SecurePassword123!",
  "servicable_locations": [887, 8020, 28001],
  "max_handling_capacity": 50
}
```

**Response:** `200 OK`
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "FastDelivery Co.",
  "email": "partner@example.com",
  "servicable_locations": [887, 8020, 28001],
  "max_handling_capacity": 50
}
```

**Error Responses:**
- `409 Conflict`: Email already exists
- `422 Validation Error`: Invalid input data

### Login Delivery Partner

#### POST /partner/token

Authenticate and get access token.

**Request Body:** (form data)
```
username=partner@example.com
password=SecurePassword123!
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Update Delivery Partner

#### POST /partner/

Update delivery partner information.

**Headers:**
- `Authorization: Bearer <token>` (required)

**Request Body:**
```json
{
  "servicable_locations": [887, 8020, 28001, 28002],
  "max_handling_capacity": 75
}
```

**Response:** `200 OK`
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "FastDelivery Co.",
  "email": "partner@example.com",
  "servicable_locations": [887, 8020, 28001, 28002],
  "max_handling_capacity": 75
}
```

### Get Delivery Partner Profile

#### GET /partner/me

Get the current authenticated delivery partner's profile.

**Headers:**
- `Authorization: Bearer <token>` (required)

**Response:** `200 OK`
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "FastDelivery Co.",
  "email": "partner@example.com",
  "servicable_locations": [887, 8020, 28001],
  "max_handling_capacity": 50
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid or expired token

### Get Delivery Partner Shipments

#### GET /partner/shipments

Get all shipments assigned to the authenticated delivery partner.

**Headers:**
- `Authorization: Bearer <token>` (required)

**Response:** `200 OK`
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "content": "Electronics",
    "weight": 5.5,
    "destination": 887,
    "status": "in_transit",
    "estimated_delivery": "2026-01-10T12:00:00",
    "client_contact_email": "client@example.com",
    "client_contact_phone": "+34601539533",
    "tags": ["express", "fragile"]
  }
]
```

**Error Responses:**
- `401 Unauthorized`: Invalid or expired token

---

## Shipment Endpoints

### Get Shipment

#### GET /shipment/

Get shipment by ID.

**Query Parameters:**
- `id` (required): Shipment UUID

**Response:** `200 OK`
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "content": "Electronics - Laptop and accessories",
  "weight": 5.5,
  "destination": 887,
  "status": "in_transit",
  "estimated_delivery": "2026-01-10T12:00:00",
  "client_contact_email": "client@example.com",
  "client_contact_phone": "+34601539533",
  "tags": ["express", "fragile"]
}
```

**Error Responses:**
- `404 Not Found`: Shipment not found

### Create Shipment

#### POST /shipment/

Create a new shipment.

**Headers:**
- `Authorization: Bearer <token>` (required - seller token)

**Request Body:**
```json
{
  "content": "Electronics - Laptop and accessories",
  "weight": 5.5,
  "destination": 887,
  "client_contact_email": "client@example.com",
  "client_contact_phone": "+34601539533"
}
```

**Response:** `200 OK`
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "content": "Electronics - Laptop and accessories",
  "weight": 5.5,
  "destination": 887,
  "status": "placed",
  "estimated_delivery": "2026-01-10T12:00:00",
  "client_contact_email": "client@example.com",
  "client_contact_phone": "+34601539533",
  "tags": []
}
```

**Error Responses:**
- `401 Unauthorized`: Not authenticated
- `406 Not Acceptable`: No delivery partner available
- `422 Validation Error`: Invalid input data

### Update Shipment

#### PATCH /shipment/

Update shipment status and location.

**Headers:**
- `Authorization: Bearer <token>` (required - delivery partner token)

**Query Parameters:**
- `id` (required): Shipment UUID

**Request Body:**
```json
{
  "status": "out_for_delivery",
  "location": 887,
  "description": "Package is out for delivery",
  "estimated_delivery": "2026-01-10T14:00:00"
}
```

**Response:** `200 OK`
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "out_for_delivery",
  "location": 887,
  "estimated_delivery": "2026-01-10T14:00:00"
}
```

**Error Responses:**
- `400 Bad Request`: No data provided or validation error
- `401 Unauthorized`: Not authorized
- `404 Not Found`: Shipment not found

### Cancel Shipment

#### POST /shipment/cancel

Cancel a shipment.

**Headers:**
- `Authorization: Bearer <token>` (required - seller token)

**Query Parameters:**
- `id` (required): Shipment UUID

**Response:** `200 OK`
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "cancelled"
}
```

**Error Responses:**
- `401 Unauthorized`: Not authorized
- `404 Not Found`: Shipment not found

### Track Shipment

#### GET /shipment/track

Get shipment tracking page (HTML).

**Query Parameters:**
- `id` (required): Shipment UUID

**Response:** `200 OK` (HTML)
- Returns HTML page with shipment tracking information

**Error Responses:**
- `404 Not Found`: Shipment not found

---

## Data Models

### Shipment Status

Enum values:
- `placed`: Shipment created
- `in_transit`: Shipment in transit
- `out_for_delivery`: Out for delivery
- `delivered`: Delivered
- `cancelled`: Cancelled

### Tag Names

Enum values:
- `express`: Express delivery
- `standard`: Standard delivery
- `fragile`: Fragile items
- `heavy`: Heavy items
- `international`: International shipment
- `domestic`: Domestic shipment

---

## Error Responses

All error responses follow this format:

```json
{
  "error": "ErrorClassName",
  "message": "Human-readable error message",
  "status_code": 404
}
```

### Common Error Codes

- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required or failed
- `404 Not Found`: Resource not found
- `406 Not Acceptable`: Business logic constraint
- `409 Conflict`: Resource already exists
- `422 Validation Error`: Input validation failed
- `500 Internal Server Error`: Server error

---

## Rate Limiting

Some endpoints have rate limiting:
- Email verification: 5 attempts per hour
- Password reset: 5 attempts per hour

---

## Interactive Documentation

- **Swagger UI**: https://fastship-api.onrender.com/docs
- **Scalar Docs**: https://fastship-api.onrender.com/scalar
- **OpenAPI JSON**: https://fastship-api.onrender.com/openapi.json

---

**Last Updated**: January 8, 2026  
**API Version**: 1.0.0


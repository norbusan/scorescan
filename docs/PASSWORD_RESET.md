# Password Reset Feature Documentation

## Overview

The password reset feature allows users to securely reset their passwords through an email verification process. This document covers the complete implementation, configuration, and usage.

## Table of Contents

1. [Features](#features)
2. [Architecture](#architecture)
3. [Setup & Configuration](#setup--configuration)
4. [API Endpoints](#api-endpoints)
5. [Database Schema](#database-schema)
6. [User Flow](#user-flow)
7. [Security Considerations](#security-considerations)
8. [Email Configuration](#email-configuration)
9. [Troubleshooting](#troubleshooting)

---

## Features

- **Secure Token Generation**: Cryptographically secure random tokens
- **Email Verification**: Password reset links sent via email
- **Token Expiration**: Configurable expiration time (default: 24 hours)
- **One-Time Use**: Tokens can only be used once
- **Email Enumeration Protection**: Always returns success to prevent account discovery
- **Mobile-Friendly UI**: Responsive design with password visibility toggle
- **Automatic Cleanup**: Expired tokens are cleaned up during validation

## Architecture

```
┌─────────────┐
│   User      │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  1. Request Password Reset              │
│     POST /api/auth/password-reset/      │
│          request                        │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  2. Generate Token & Send Email         │
│     - Create secure token               │
│     - Store in database                 │
│     - Send email with reset link        │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  3. User Clicks Link in Email           │
│     Frontend: /reset-password?token=... │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  4. Enter New Password                  │
│     POST /api/auth/password-reset/      │
│          confirm                        │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  5. Validate Token & Update Password    │
│     - Check token validity              │
│     - Check expiration                  │
│     - Update password                   │
│     - Mark token as used                │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  6. Redirect to Login                   │
└─────────────────────────────────────────┘
```

## Setup & Configuration

### 1. Run Database Migration

```bash
cd backend
python3 migrate_add_password_reset.py
```

This creates the `password_reset_tokens` table and indexes.

### 2. Configure Environment Variables

Add the following to your `.env` file:

```bash
# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=ScoreScan
FRONTEND_URL=http://localhost:5173

# Token expiration (hours)
PASSWORD_RESET_TOKEN_EXPIRE_HOURS=24
```

### 3. Gmail Configuration (Example)

For Gmail, you need to use an **App Password**:

1. Go to your Google Account settings
2. Navigate to Security → 2-Step Verification
3. Scroll to "App passwords"
4. Generate a new app password
5. Use this password in `SMTP_PASSWORD`

**Important**: Regular Gmail passwords won't work due to security restrictions.

### 4. Restart Services

```bash
docker-compose restart backend
```

## API Endpoints

### Request Password Reset

**Endpoint**: `POST /api/auth/password-reset/request`

**Request Body**:
```json
{
  "email": "user@example.com"
}
```

**Response** (200 OK):
```json
{
  "message": "If the email exists, a password reset link has been sent",
  "success": true
}
```

**Notes**:
- Always returns success (prevents email enumeration)
- Email sent only if account exists
- Token expires in 24 hours (configurable)

---

### Confirm Password Reset

**Endpoint**: `POST /api/auth/password-reset/confirm`

**Request Body**:
```json
{
  "token": "secure-random-token-from-email",
  "new_password": "newpassword123"
}
```

**Success Response** (200 OK):
```json
{
  "message": "Password has been reset successfully",
  "success": true
}
```

**Error Responses**:

**Invalid/Expired Token** (400 Bad Request):
```json
{
  "detail": "Invalid or expired reset token"
}
```

**Token Already Used** (400 Bad Request):
```json
{
  "detail": "Reset token has already been used"
}
```

**Token Expired** (400 Bad Request):
```json
{
  "detail": "Reset token has expired"
}
```

## Database Schema

### password_reset_tokens Table

```sql
CREATE TABLE password_reset_tokens (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    token VARCHAR(64) UNIQUE NOT NULL,
    expires_at DATETIME NOT NULL,
    used VARCHAR(1) DEFAULT '0',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX idx_password_reset_tokens_token ON password_reset_tokens(token);
CREATE INDEX idx_password_reset_tokens_user_id ON password_reset_tokens(user_id);
```

### Fields

- **id**: UUID primary key
- **user_id**: Reference to user
- **token**: Secure random token (URL-safe)
- **expires_at**: Expiration timestamp
- **used**: "0" (unused) or "1" (used)
- **created_at**: Creation timestamp

### Token Generation

Tokens are generated using Python's `secrets.token_urlsafe(32)`, which creates a cryptographically secure 43-character URL-safe token.

## User Flow

### Frontend Routes

1. **Forgot Password Page**: `/forgot-password`
   - User enters email
   - Form submits to backend
   - Success message displayed

2. **Reset Password Page**: `/reset-password?token=...`
   - Extracts token from URL
   - User enters new password
   - Validates password match
   - Submits to backend
   - Redirects to login on success

### UI Features

**Forgot Password Page**:
- Email input validation
- Loading state during submission
- Success confirmation screen
- Link back to login

**Reset Password Page**:
- Password visibility toggle
- Password confirmation field
- Real-time password match validation
- Minimum 8 characters requirement
- Loading state during submission
- Success screen with auto-redirect

## Security Considerations

### 1. Email Enumeration Protection

The request endpoint **always** returns success, regardless of whether the email exists:

```python
# Always return success to prevent email enumeration
return {
    "message": "If the email exists, a password reset link has been sent",
    "success": True,
}
```

This prevents attackers from discovering which emails are registered.

### 2. Token Security

- **Cryptographically Secure**: Uses `secrets.token_urlsafe()`
- **One-Time Use**: Tokens marked as used after password reset
- **Time-Limited**: 24-hour expiration (configurable)
- **Indexed**: Fast lookup without exposing user info

### 3. Password Validation

- Minimum 8 characters (enforced in frontend and backend)
- Frontend validates password match before submission
- Backend hashes password using bcrypt

### 4. Token Expiration

Expired tokens are:
- Automatically rejected during validation
- Deleted from database when encountered
- Cannot be reused after expiration

### 5. HTTPS Requirement

**Production**: Always use HTTPS to prevent:
- Token interception
- Man-in-the-middle attacks
- Email link tampering

### 6. Rate Limiting (Recommended)

Consider adding rate limiting to prevent abuse:
- Limit requests per IP
- Limit requests per email
- Use tools like `slowapi` or nginx rate limiting

## Email Configuration

### Supported SMTP Providers

#### Gmail
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password  # Not your regular password!
```

#### Outlook/Office 365
```bash
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USERNAME=your-email@outlook.com
SMTP_PASSWORD=your-password
```

#### SendGrid
```bash
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your-sendgrid-api-key
```

#### Amazon SES
```bash
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USERNAME=your-ses-username
SMTP_PASSWORD=your-ses-password
```

### Email Template

The email includes:
- Plain text version (for email clients that don't support HTML)
- HTML version with styled button
- Reset link with token
- Expiration notice
- Security notice

Example HTML email:

![Password Reset Email](../assets/password-reset-email-preview.png)

### Email Not Configured

If SMTP credentials are not set, the system will:
- Log a warning
- Log the reset URL to console (for development)
- Return success to the user (no error shown)

**Development Mode**: Check logs for the reset URL:
```
Password reset URL (not sent): http://localhost:5173/reset-password?token=...
```

## Troubleshooting

### Issue: Emails Not Being Sent

**Symptoms**: User requests reset but no email arrives

**Checks**:

1. **Verify SMTP Configuration**:
   ```bash
   # Check backend logs
   docker-compose logs -f backend | grep "SMTP"
   ```

2. **Test SMTP Connection**:
   ```python
   import smtplib
   smtp = smtplib.SMTP('smtp.gmail.com', 587)
   smtp.starttls()
   smtp.login('your-email@gmail.com', 'your-app-password')
   print("SMTP connection successful!")
   smtp.quit()
   ```

3. **Common Issues**:
   - Using regular Gmail password instead of App Password
   - Firewall blocking port 587
   - SMTP credentials incorrect
   - "Less secure apps" disabled (Gmail legacy)

### Issue: Token Invalid or Expired

**Symptoms**: Reset link doesn't work

**Checks**:

1. **Check Token in Database**:
   ```bash
   sqlite3 backend/storage/scorescan.db
   SELECT * FROM password_reset_tokens WHERE token='...';
   ```

2. **Verify Expiration**:
   ```sql
   SELECT token, expires_at, used, 
          datetime(expires_at) > datetime('now') as is_valid
   FROM password_reset_tokens;
   ```

3. **Common Issues**:
   - Token older than 24 hours
   - Token already used
   - Token manually deleted from database
   - Server timezone mismatch

### Issue: Reset Page Shows "Invalid Link"

**Symptoms**: User redirected to login immediately

**Checks**:

1. **Token in URL**: Ensure URL has `?token=...`
2. **Frontend Route**: Verify `/reset-password` route exists
3. **Browser Console**: Check for JavaScript errors

### Issue: Password Requirements Not Clear

**Solution**: Frontend enforces:
- Minimum 8 characters
- Shows password strength (optional enhancement)
- Confirms password match

Backend validates:
- Minimum 8 characters in schema
- Maximum 100 characters

## Testing

### Manual Testing

1. **Request Reset**:
   ```bash
   curl -X POST http://localhost:8000/api/auth/password-reset/request \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com"}'
   ```

2. **Check Email** (or logs if SMTP not configured)

3. **Reset Password**:
   ```bash
   curl -X POST http://localhost:8000/api/auth/password-reset/confirm \
     -H "Content-Type: application/json" \
     -d '{
       "token":"token-from-email",
       "new_password":"newpassword123"
     }'
   ```

4. **Login with New Password**

### Database Verification

```bash
sqlite3 backend/storage/scorescan.db

-- View all reset tokens
SELECT 
  prt.id,
  u.email,
  prt.token,
  prt.expires_at,
  prt.used,
  datetime(prt.expires_at) > datetime('now') as is_valid
FROM password_reset_tokens prt
JOIN users u ON prt.user_id = u.id;

-- Clean up old tokens
DELETE FROM password_reset_tokens 
WHERE datetime(expires_at) < datetime('now');
```

## Additional Features (Future Enhancements)

### 1. Email Templates with Jinja2
- More flexible email customization
- Multiple languages support

### 2. Rate Limiting
- Prevent abuse of reset endpoint
- Per-email and per-IP limits

### 3. Token Cleanup Job
- Celery periodic task to delete expired tokens
- Reduces database bloat

### 4. Password History
- Prevent reusing recent passwords
- Store hashed password history

### 5. Two-Factor Authentication
- Additional security for password reset
- SMS or authenticator app verification

### 6. Notification on Password Change
- Send email notification after successful reset
- Security alert for unauthorized changes

## References

- **Backend Model**: `backend/app/models/password_reset.py`
- **Email Service**: `backend/app/services/email.py`
- **API Endpoints**: `backend/app/routers/auth.py`
- **Frontend Pages**: 
  - `frontend/src/pages/ForgotPassword.tsx`
  - `frontend/src/pages/ResetPassword.tsx`
- **Migration Script**: `backend/migrate_add_password_reset.py`

---

**Last Updated**: January 28, 2026  
**Version**: 1.0  
**Status**: ✅ Production Ready

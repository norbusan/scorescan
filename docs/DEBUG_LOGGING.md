# Debug Logging Guide

## Overview

ScoreScan includes comprehensive debug logging for authentication and user management operations. This can be enabled via the `DEBUG` environment variable to troubleshoot registration, login, and approval issues.

## Enabling Debug Mode

### Docker (Production/Staging)

1. Edit your `.env` file:
   ```bash
   DEBUG=true
   ```

2. Restart the services:
   ```bash
   docker-compose restart
   ```

### Local Development

1. Edit `backend/.env`:
   ```bash
   DEBUG=true
   ```

2. Restart the backend server:
   ```bash
   # In backend directory
   uvicorn app.main:app --reload
   ```

## What Gets Logged

When `DEBUG=true`, the following operations produce detailed logs:

### User Registration (`/api/auth/register`)

```
[AUTH DEBUG] /register: Attempting to register user: user@example.com
[AUTH DEBUG] Checking if email is registered: user@example.com
[AUTH DEBUG] Looking up user by email: user@example.com
[AUTH DEBUG] User not found for email: user@example.com
[AUTH DEBUG] Email user@example.com registered: False
[AUTH DEBUG] Creating new user: email=user@example.com
[AUTH DEBUG] New user defaults: is_active=True, is_approved=False, is_superuser=False
[AUTH DEBUG] User created successfully: id=xxx, email=user@example.com, is_approved=False
[AUTH DEBUG] /register: User registered successfully: user@example.com, is_approved=False, requires approval
```

### User Login (`/api/auth/login`)

#### Successful Login

```
[AUTH DEBUG] /login: Login attempt for user: user@example.com
[AUTH DEBUG] Authenticating user: user@example.com
[AUTH DEBUG] Looking up user by email: user@example.com
[AUTH DEBUG] User found: id=xxx, email=user@example.com, is_active=True, is_approved=True, is_superuser=False
[AUTH DEBUG] User found, verifying password...
[AUTH DEBUG] Password verified successfully for user: user@example.com
[AUTH DEBUG] /login: User authenticated, checking status...
[AUTH DEBUG] /login: is_active=True, is_approved=True, is_superuser=False
[AUTH DEBUG] /login: Creating tokens for user: user@example.com
[AUTH DEBUG] /login: Login successful for: user@example.com
```

#### Failed Login - Wrong Password

```
[AUTH DEBUG] /login: Login attempt for user: user@example.com
[AUTH DEBUG] Authenticating user: user@example.com
[AUTH DEBUG] Looking up user by email: user@example.com
[AUTH DEBUG] User found: id=xxx, email=user@example.com, is_active=True, is_approved=True, is_superuser=False
[AUTH DEBUG] User found, verifying password...
[AUTH DEBUG] Authentication failed: invalid password
[AUTH DEBUG] /login: Authentication failed for: user@example.com
```

#### Failed Login - User Not Found

```
[AUTH DEBUG] /login: Login attempt for user: nonexistent@example.com
[AUTH DEBUG] Authenticating user: nonexistent@example.com
[AUTH DEBUG] Looking up user by email: nonexistent@example.com
[AUTH DEBUG] User not found for email: nonexistent@example.com
[AUTH DEBUG] Authentication failed: user not found
[AUTH DEBUG] /login: Authentication failed for: nonexistent@example.com
```

#### Failed Login - Pending Approval

```
[AUTH DEBUG] /login: Login attempt for user: pending@example.com
[AUTH DEBUG] Authenticating user: pending@example.com
[AUTH DEBUG] Looking up user by email: pending@example.com
[AUTH DEBUG] User found: id=xxx, email=pending@example.com, is_active=True, is_approved=False, is_superuser=False
[AUTH DEBUG] User found, verifying password...
[AUTH DEBUG] Password verified successfully for user: pending@example.com
[AUTH DEBUG] /login: User authenticated, checking status...
[AUTH DEBUG] /login: is_active=True, is_approved=False, is_superuser=False
[AUTH DEBUG] /login: Account pending approval for: pending@example.com
```

### Token Validation (`get_current_user`)

#### Successful Validation

```
[AUTH DEBUG] get_current_user: Validating access token
[AUTH DEBUG] get_current_user: Token valid, user_id=xxx
[AUTH DEBUG] Looking up user by ID: xxx
[AUTH DEBUG] User found: id=xxx, email=user@example.com, is_active=True, is_approved=True, is_superuser=False
[AUTH DEBUG] get_current_user: Success - user=user@example.com
```

#### Invalid Token

```
[AUTH DEBUG] get_current_user: Validating access token
[AUTH DEBUG] get_current_user: Invalid or expired token
```

#### User Pending Approval

```
[AUTH DEBUG] get_current_user: Validating access token
[AUTH DEBUG] get_current_user: Token valid, user_id=xxx
[AUTH DEBUG] Looking up user by ID: xxx
[AUTH DEBUG] User found: id=xxx, email=user@example.com, is_active=True, is_approved=False, is_superuser=False
[AUTH DEBUG] get_current_user: User account pending approval
```

### Token Refresh (`/api/auth/refresh`)

```
[AUTH DEBUG] /refresh: Attempting to refresh token
[AUTH DEBUG] /refresh: Token valid for user_id=xxx, email=user@example.com
[AUTH DEBUG] Looking up user by ID: xxx
[AUTH DEBUG] User found: id=xxx, email=user@example.com, is_active=True, is_approved=True, is_superuser=False
[AUTH DEBUG] /refresh: Creating new tokens for user: user@example.com
[AUTH DEBUG] /refresh: Token refresh successful
```

## Viewing Logs

### Docker Deployment

```bash
# View all logs
docker-compose logs -f

# View only API logs
docker-compose logs -f api

# View only worker logs
docker-compose logs -f worker

# Filter for auth debug logs
docker-compose logs -f api | grep "AUTH DEBUG"

# Save logs to file
docker-compose logs api > api_logs.txt
```

### Local Development

Logs will appear in your terminal where you're running `uvicorn`.

## Common Debug Scenarios

### Scenario 1: User Can't Login After Registration

**Debug Steps:**

1. Enable debug mode
2. Check registration logs:
   ```bash
   docker-compose logs api | grep "register.*user@example.com"
   ```
3. Look for `is_approved=False` in the logs
4. Verify in admin panel or database:
   ```bash
   sqlite3 backend/storage/scorescan.db \
     "SELECT email, is_approved FROM users WHERE email='user@example.com';"
   ```
5. If `is_approved=0`, approve the user via admin panel

**Expected Debug Output:**
```
[AUTH DEBUG] /register: User registered successfully: user@example.com, is_approved=False
[AUTH DEBUG] /login: Account pending approval for: user@example.com
```

### Scenario 2: Token Validation Failures

**Debug Steps:**

1. Enable debug mode
2. Watch for token validation logs:
   ```bash
   docker-compose logs -f api | grep "get_current_user"
   ```
3. Check if token is expired or invalid
4. Look for user status issues

**Expected Debug Output for Expired Token:**
```
[AUTH DEBUG] get_current_user: Validating access token
[AUTH DEBUG] get_current_user: Invalid or expired token
```

### Scenario 3: Duplicate Email Registration

**Debug Steps:**

1. Enable debug mode
2. Attempt registration
3. Check logs:
   ```bash
   docker-compose logs api | grep "register.*user@example.com"
   ```

**Expected Debug Output:**
```
[AUTH DEBUG] /register: Attempting to register user: user@example.com
[AUTH DEBUG] Checking if email is registered: user@example.com
[AUTH DEBUG] Looking up user by email: user@example.com
[AUTH DEBUG] User found: id=xxx, email=user@example.com, ...
[AUTH DEBUG] Email user@example.com registered: True
[AUTH DEBUG] /register: Email already registered: user@example.com
```

### Scenario 4: Superuser Can't Access Admin Panel

**Debug Steps:**

1. Enable debug mode
2. Attempt to access admin endpoint
3. Check user's superuser status in logs
4. Verify in database

**Expected Debug Output:**
```
[AUTH DEBUG] get_current_user: Success - user=admin@example.com
[AUTH DEBUG] User found: id=xxx, email=admin@example.com, is_active=True, is_approved=True, is_superuser=True
```

## Performance Impact

Debug logging adds minimal overhead:
- **Disk I/O**: Additional log writes (negligible)
- **CPU**: String formatting (~0.1ms per log)
- **Memory**: Log buffer (typically <1MB)

**Recommendation**: Enable debug mode only when troubleshooting. Disable in production for optimal performance.

## Security Considerations

### What Debug Logs Include

✅ **Safe to log:**
- User IDs (UUIDs)
- Email addresses
- User status flags (is_active, is_approved, is_superuser)
- Operation timestamps

❌ **NEVER logged:**
- Passwords (plain or hashed)
- JWT token contents
- Refresh tokens
- Session secrets

### Debug Log Safety

Debug logs are safe to share with:
- Internal team members
- System administrators
- Support engineers

Do NOT share logs containing:
- Full JWT tokens
- Database credentials
- API keys

## Troubleshooting

### Debug Logs Not Appearing

**Problem**: Enabled DEBUG=true but no logs appear

**Solutions:**

1. **Verify environment variable:**
   ```bash
   docker-compose exec api python -c "from app.config import get_settings; print(get_settings().debug)"
   ```
   Should output: `True`

2. **Check log level:**
   ```bash
   # Ensure logging level is set correctly
   docker-compose logs api | head -20
   ```

3. **Restart services:**
   ```bash
   docker-compose restart api worker
   ```

4. **Check .env file location:**
   - Docker: `.env` in project root
   - Local: `backend/.env`

### Too Many Logs

**Problem**: Debug logs are overwhelming

**Solutions:**

1. **Filter for specific operations:**
   ```bash
   # Only registration
   docker-compose logs api | grep "/register"
   
   # Only login
   docker-compose logs api | grep "/login"
   
   # Only token validation
   docker-compose logs api | grep "get_current_user"
   ```

2. **Use log rotation:**
   ```yaml
   # In docker-compose.yml
   services:
     api:
       logging:
         driver: "json-file"
         options:
           max-size: "10m"
           max-file: "3"
   ```

3. **Disable when not needed:**
   ```bash
   # In .env
   DEBUG=false
   ```

## Best Practices

### When to Enable Debug Mode

✅ **Enable for:**
- Investigating login/registration issues
- Troubleshooting approval workflow
- Debugging token validation
- Testing authentication flow
- User reports of access issues

❌ **Disable for:**
- Normal production operation
- Performance testing
- High-traffic periods
- After issue is resolved

### Debug Workflow

1. **Enable debug mode**
2. **Reproduce the issue**
3. **Capture logs**
4. **Analyze log output**
5. **Fix the issue**
6. **Verify fix works**
7. **Disable debug mode**

### Log Analysis Tips

1. **Follow the request flow:**
   - Registration: `/register` → `create_user` → database
   - Login: `/login` → `authenticate_user` → `get_user_by_email` → password check
   - Token: `get_current_user` → `verify_token` → `get_user_by_id`

2. **Look for state changes:**
   - User creation: Check `is_approved=False`
   - Approval: Look for status changes
   - Login: Track authentication steps

3. **Identify failure points:**
   - "User not found" → Registration issue
   - "Invalid password" → Credential issue
   - "Pending approval" → Workflow issue
   - "Invalid token" → Token/session issue

## Examples

### Complete Registration Flow with Debug Logs

```bash
# User registers
POST /api/auth/register
  {
    "email": "newuser@example.com",
    "password": "********"
  }

# Debug logs:
[AUTH DEBUG] /register: Attempting to register user: newuser@example.com
[AUTH DEBUG] Checking if email is registered: newuser@example.com
[AUTH DEBUG] Looking up user by email: newuser@example.com
[AUTH DEBUG] User not found for email: newuser@example.com
[AUTH DEBUG] Email newuser@example.com registered: False
[AUTH DEBUG] Creating new user: email=newuser@example.com
[AUTH DEBUG] New user defaults: is_active=True, is_approved=False, is_superuser=False
[AUTH DEBUG] User created successfully: id=abc-123, email=newuser@example.com, is_approved=False
[AUTH DEBUG] /register: User registered successfully: newuser@example.com, is_approved=False, requires approval
```

### Complete Login Flow (Pending Approval)

```bash
# User attempts login
POST /api/auth/login
  {
    "username": "newuser@example.com",
    "password": "********"
  }

# Debug logs:
[AUTH DEBUG] /login: Login attempt for user: newuser@example.com
[AUTH DEBUG] Authenticating user: newuser@example.com
[AUTH DEBUG] Looking up user by email: newuser@example.com
[AUTH DEBUG] User found: id=abc-123, email=newuser@example.com, is_active=True, is_approved=False, is_superuser=False
[AUTH DEBUG] User found, verifying password...
[AUTH DEBUG] Password verified successfully for user: newuser@example.com
[AUTH DEBUG] /login: User authenticated, checking status...
[AUTH DEBUG] /login: is_active=True, is_approved=False, is_superuser=False
[AUTH DEBUG] /login: Account pending approval for: newuser@example.com

# Response: 403 Forbidden
# "Your account is pending approval by an administrator"
```

---

**Last Updated**: January 28, 2026  
**Version**: 1.0  
**Status**: ✅ Production Ready

# Change Password Feature Documentation

## Overview

The change password feature allows authenticated users to update their password from within their account settings. This document covers the implementation, usage, and security considerations.

## Table of Contents

1. [Features](#features)
2. [User Flow](#user-flow)
3. [API Endpoint](#api-endpoint)
4. [Frontend Implementation](#frontend-implementation)
5. [Security Considerations](#security-considerations)
6. [Usage Instructions](#usage-instructions)
7. [Troubleshooting](#troubleshooting)

---

## Features

- **Current Password Verification**: Users must provide their current password
- **Password Requirements**: Minimum 8 characters
- **Real-time Validation**: Password match indicator
- **Password Visibility Toggle**: Show/hide password fields
- **Success Confirmation**: Clear feedback after password change
- **Security Tips**: Built-in password security guidance
- **Account Information Display**: Shows email and account type
- **Mobile-Friendly**: Responsive design for all devices

## User Flow

```
User logs in → Navigates to Settings → Enters current password
→ Enters new password → Confirms new password → Submits
→ System validates → Password updated → Success message
```

### Step-by-Step Flow

1. **Access Settings Page**
   - User must be logged in
   - Click "Settings" in navigation menu
   - Or navigate to `/settings`

2. **View Account Information**
   - Email address displayed
   - Account type badge (Standard User / Administrator)

3. **Fill Change Password Form**
   - Enter current password
   - Enter new password (min 8 characters)
   - Confirm new password
   - Real-time validation shows password match status

4. **Submit Form**
   - System validates current password
   - System validates new password requirements
   - Password is updated in database
   - Success message displayed

5. **Next Login**
   - User logs in with new password
   - Old password no longer works

## API Endpoint

### Change Password

**Endpoint**: `POST /api/auth/change-password`

**Authentication**: Required (Bearer token)

**Request Body**:
```json
{
  "current_password": "oldpassword123",
  "new_password": "newpassword456"
}
```

**Success Response** (200 OK):
```json
{
  "message": "Password changed successfully",
  "success": true
}
```

**Error Responses**:

**Incorrect Current Password** (400 Bad Request):
```json
{
  "detail": "Current password is incorrect"
}
```

**Unauthorized** (401 Unauthorized):
```json
{
  "detail": "Could not validate credentials"
}
```

**Validation Error** (422 Unprocessable Entity):
```json
{
  "detail": [
    {
      "loc": ["body", "new_password"],
      "msg": "ensure this value has at least 8 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

### Implementation Details

**Backend Service Method**:
```python
def change_password(self, user: User, current_password: str, new_password: str) -> bool:
    """
    Change a user's password.
    
    Returns:
        True if password changed successfully, False if current password is incorrect
    """
    # Verify current password
    if not verify_password(current_password, user.hashed_password):
        return False
    
    # Update password
    user.hashed_password = get_password_hash(new_password)
    self.db.commit()
    
    return True
```

## Frontend Implementation

### Settings Page (`/settings`)

Located at: `frontend/src/pages/Settings.tsx`

**Key Components**:

1. **Account Information Section**
   - Display user email
   - Display account type badge
   - Non-editable information

2. **Change Password Form**
   - Current password field
   - New password field
   - Confirm password field
   - Password visibility toggles
   - Submit and Cancel buttons

3. **Success Message**
   - Green alert box with checkmark
   - Auto-hides after 5 seconds
   - Confirms password change

4. **Security Tips Section**
   - Best practices for password security
   - Helpful guidance for users

### Form Validation

**Frontend Validation**:
- New password must be at least 8 characters
- New password must match confirmation
- New password must be different from current password
- All fields required before submission

**Real-time Feedback**:
- Password match indicator (green checkmark / red text)
- Loading state during submission
- Disabled submit button when invalid

### UI Features

**Password Visibility Toggle**:
```tsx
<button
  type="button"
  onClick={() => setShowPassword(!showPassword)}
  className="absolute right-3 top-1/2 -translate-y-1/2"
>
  {showPassword ? <EyeOff /> : <Eye />}
</button>
```

**Success Message**:
```tsx
{changeSuccess && (
  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
    <CheckCircle className="h-5 w-5 text-green-600" />
    <p>Password changed successfully!</p>
  </div>
)}
```

## Security Considerations

### 1. Current Password Verification

**Why It Matters**: Prevents unauthorized password changes if someone gains temporary access to an active session.

**Implementation**: Backend verifies current password before allowing change:
```python
if not verify_password(current_password, user.hashed_password):
    return False  # Reject change
```

### 2. Authentication Required

**Why It Matters**: Only authenticated users can change their password.

**Implementation**: Endpoint protected by `get_current_user` dependency:
```python
@router.post("/change-password")
def change_password(
    password_data: PasswordChange,
    current_user=Depends(get_current_user),  # Auth required
    db: Session = Depends(get_db),
):
```

### 3. Password Requirements

**Why It Matters**: Enforces minimum security standards.

**Implementation**:
- Minimum 8 characters (enforced in schema and frontend)
- Maximum 100 characters (prevents abuse)
- Validated on both frontend and backend

### 4. Password Hashing

**Why It Matters**: Passwords stored securely in database.

**Implementation**: Uses bcrypt hashing via passlib:
```python
user.hashed_password = get_password_hash(new_password)
```

### 5. No Email Notification

**Current Implementation**: No email sent after password change.

**Future Enhancement**: Consider sending notification email for security:
- Alert user of password change
- Include timestamp and IP address
- Provide link to reset if unauthorized

### 6. HTTPS Required

**Production**: Always use HTTPS to prevent:
- Password interception during transmission
- Man-in-the-middle attacks
- Session hijacking

## Usage Instructions

### For Users

1. **Log in to your account**
   - Use your current credentials

2. **Navigate to Settings**
   - Click "Settings" in the top navigation bar
   - Or go to `/settings`

3. **Enter your current password**
   - This verifies it's you making the change
   - Use the eye icon to show/hide password

4. **Enter your new password**
   - Must be at least 8 characters
   - Should be different from current password
   - Use the eye icon to show/hide password

5. **Confirm your new password**
   - Re-enter the same new password
   - Watch for the green checkmark when they match

6. **Click "Change Password"**
   - Wait for confirmation message
   - If error occurs, check your current password

7. **Use new password on next login**
   - Old password will no longer work
   - Update password in any password managers

### For Administrators

**Note**: Administrators cannot change other users' passwords directly. If a user forgets their password, they should use the "Forgot Password" feature.

**Alternative**: Create a superuser password reset feature if needed (future enhancement).

## Troubleshooting

### Issue: "Current password is incorrect"

**Symptoms**: Error when submitting form

**Solutions**:
1. Verify you're entering the correct current password
2. Check for typos (use show/hide toggle)
3. Try copying and pasting if you have it saved
4. If forgotten, use "Forgot Password" feature instead

### Issue: "New password must be at least 8 characters"

**Symptoms**: Submit button disabled or validation error

**Solutions**:
1. Count characters in your new password
2. Add more characters to meet minimum
3. Consider using a passphrase (easier to remember)

### Issue: "Passwords do not match"

**Symptoms**: Red text below confirm password field

**Solutions**:
1. Check both password fields match exactly
2. Watch for extra spaces
3. Use show/hide toggle to verify
4. Re-type the confirmation

### Issue: Form clears after submission

**Symptoms**: Success, but user wants to change again

**Solutions**:
This is normal behavior for security:
- Form clears after successful change
- Prevents accidental re-submission
- Refresh the page to see form again

### Issue: Can't access Settings page

**Symptoms**: Redirected to login

**Solutions**:
1. Make sure you're logged in
2. Check if session expired
3. Log in again and try Settings

## Testing

### Manual Testing

1. **Basic Change**:
   ```
   Login → Settings → Change password → Verify success
   ```

2. **Wrong Current Password**:
   ```
   Login → Settings → Enter wrong current password → Verify error
   ```

3. **Password Mismatch**:
   ```
   Login → Settings → Different new passwords → Verify validation
   ```

4. **Too Short Password**:
   ```
   Login → Settings → 7 characters → Verify validation
   ```

5. **Same as Current**:
   ```
   Login → Settings → Same password → Verify error
   ```

6. **Login with New Password**:
   ```
   Change password → Logout → Login with new password → Success
   ```

7. **Login with Old Password**:
   ```
   Change password → Logout → Login with old password → Fail
   ```

### Automated Testing (Future)

Suggested test cases:
- Unit tests for `change_password` service method
- API endpoint tests with various inputs
- Frontend component tests
- E2E tests for full flow

## Comparison: Change Password vs. Reset Password

| Feature | Change Password | Reset Password |
|---------|----------------|----------------|
| **Authentication** | Required (logged in) | Not required |
| **Current Password** | Required | Not required |
| **Email Verification** | Not used | Required (token via email) |
| **Use Case** | User knows current password | User forgot password |
| **Access Method** | Settings page | Forgot password link |
| **Security** | Session-based | Token-based |

## Best Practices

### For Users

1. **Use Strong Passwords**
   - At least 8 characters (more is better)
   - Mix uppercase, lowercase, numbers, symbols
   - Avoid common words or patterns

2. **Unique Passwords**
   - Don't reuse passwords from other sites
   - Use a password manager

3. **Change Regularly**
   - Consider changing every 90 days
   - Change immediately if compromised

4. **Keep Secure**
   - Don't share your password
   - Don't write it down in plain text
   - Be cautious of phishing attempts

### For Developers

1. **Never Log Passwords**
   - Don't log password fields
   - Use debug mode carefully

2. **Always Hash**
   - Never store passwords in plain text
   - Use bcrypt or similar

3. **Validate Both Sides**
   - Frontend validation for UX
   - Backend validation for security

4. **Rate Limiting** (Future Enhancement)
   - Limit password change attempts
   - Prevent brute force attacks

## Future Enhancements

Potential improvements:

1. **Email Notification**
   - Send email after successful password change
   - Include timestamp and location
   - Provide emergency reset link

2. **Password Strength Meter**
   - Visual indicator of password strength
   - Real-time feedback on entropy

3. **Password History**
   - Prevent reusing recent passwords
   - Store hashed history

4. **Two-Factor Authentication**
   - Require 2FA for password changes
   - Additional security layer

5. **Password Expiration**
   - Force password change after X days
   - Configurable per account type

6. **Change Confirmation Modal**
   - "Are you sure?" dialog
   - Prevent accidental changes

7. **Activity Log**
   - Track password changes
   - Show in user settings

## References

- **Backend Endpoint**: `backend/app/routers/auth.py` (line ~518)
- **Backend Service**: `backend/app/services/auth.py` (line ~123)
- **Frontend Page**: `frontend/src/pages/Settings.tsx`
- **Schema**: `backend/app/schemas/auth.py`
- **Route**: Configured in `frontend/src/App.tsx`
- **Navigation**: Updated in `frontend/src/components/Layout/Layout.tsx`

## Related Documentation

- [Password Reset Feature](./PASSWORD_RESET.md) - For forgotten passwords
- [User Approval System](./USER_APPROVAL_SYSTEM.md) - User management
- [Deployment Guide](./DEPLOYMENT_GUIDE.md) - Production setup

---

**Last Updated**: January 28, 2026  
**Version**: 1.0  
**Status**: ✅ Production Ready

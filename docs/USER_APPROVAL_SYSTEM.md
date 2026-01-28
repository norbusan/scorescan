# User Approval System

## Overview

ScoreScan now includes a user approval system where new registrations must be approved by a superuser before they can access the application.

## Features

- **Superuser Role**: Special users with administrative privileges
- **Approval Workflow**: New registrations are pending until approved
- **Admin Panel**: Web interface for managing users
- **User Management**: Approve, reject, and manage superuser privileges

## How It Works

### User Registration

1. User registers with email and password
2. Account is created with `is_approved = False`
3. User sees message: "Account created! Please wait for administrator approval"
4. User cannot login until approved

### User Approval

1. Superuser logs in and navigates to Admin panel
2. Pending users are displayed with approval actions
3. Superuser can:
   - **Approve**: Grant access to the application
   - **Reject**: Delete the user account
   - **Make Superuser**: Grant admin privileges

### Login

1. User attempts to login
2. System checks `is_approved` status
3. If not approved: "Your account is pending approval by an administrator"
4. If approved: Login successful

## Setup Instructions

### 1. Run Database Migration

The migration adds two new fields to the `users` table:
- `is_approved` (default: False for new users)
- `is_superuser` (default: False)

```bash
cd backend
python3 migrate_add_user_approval.py
```

This will:
- Add the new columns
- Set existing users to `is_approved = True` (grandfather clause)
- Leave all users as non-superuser

### 2. Create a Superuser

```bash
cd backend
python3 create_superuser.py
```

Follow the prompts to:
- Enter email address
- Enter password (twice for confirmation)
- Creates a superuser with `is_approved = True` and `is_superuser = True`

### 3. Restart the Application

```bash
docker-compose down
docker-compose build
docker-compose up -d
```

## Using the Admin Panel

### Access

1. Login as a superuser
2. Click "Admin" in the navigation bar
3. View the user management dashboard

### Statistics Dashboard

The admin panel shows:
- **Total Users**: All registered users
- **Pending Approval**: Users waiting for approval
- **Approved**: Users with access
- **Superusers**: Number of administrators

### User Actions

#### Approve a User
1. Find the user in the pending list
2. Click the green checkmark icon
3. User can now login

#### Reject a User
1. Find the user in the pending list
2. Click the red X icon
3. Confirm deletion
4. User account is permanently deleted

#### Make Superuser
1. Find an approved user
2. Click the shield icon
3. Confirm promotion
4. User gains admin privileges

#### Revoke Superuser
1. Find a superuser (except yourself)
2. Click the shield-off icon
3. Confirm revocation
4. User loses admin privileges (but remains approved)

## API Endpoints

### Admin Endpoints (Superuser Only)

All endpoints require superuser authentication.

```
GET  /api/admin/users                    # List all users with stats
GET  /api/admin/users/pending            # List pending users
POST /api/admin/users/{id}/approve       # Approve a user
POST /api/admin/users/{id}/reject        # Reject and delete a user
POST /api/admin/users/{id}/make-superuser   # Grant superuser privileges
DELETE /api/admin/users/{id}/superuser   # Revoke superuser privileges
```

### Response Codes

- `200 OK`: Success
- `403 Forbidden`: Not a superuser or trying to modify self
- `404 Not Found`: User not found

## Database Schema Changes

### User Model

```python
class User(Base):
    id = Column(String(36), primary_key=True)
    email = Column(String(255), unique=True)
    hashed_password = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_approved = Column(Boolean, default=False)     # NEW
    is_superuser = Column(Boolean, default=False)   # NEW
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
```

## Security Features

### Protection Against

- **Self-Modification**: Superusers cannot revoke their own privileges
- **Superuser Deletion**: Cannot reject/delete superuser accounts
- **Unauthorized Access**: All admin endpoints check for superuser status
- **Pending User Access**: Unapproved users cannot login or use the API

### Authentication Flow

```
1. User Login Request
   ↓
2. Check Credentials
   ↓
3. Check is_active
   ↓
4. Check is_approved ← NEW
   ↓
5. Issue JWT Token
```

## User Experience

### For New Users

1. **Registration**: 
   - Clear message about approval requirement
   - Account created immediately
   
2. **Login Attempt**:
   - Clear error: "Your account is pending approval"
   - Cannot access dashboard
   
3. **After Approval**:
   - Can login normally
   - Full access to all features

### For Superusers

1. **Admin Panel Access**:
   - "Admin" link in navigation
   - Dashboard shows pending count
   
2. **User Management**:
   - Visual indicators (pending/approved/superuser badges)
   - One-click approve/reject
   - Confirmation dialogs for destructive actions
   
3. **Statistics**:
   - Quick overview of user base
   - Pending approvals highlighted

## Common Workflows

### Creating the First Superuser

```bash
# 1. Run migration
cd backend
python3 migrate_add_user_approval.py

# 2. Create superuser
python3 create_superuser.py
# Email: admin@example.com
# Password: ********

# 3. Restart
docker-compose restart
```

### Approving a New User

1. User registers: user@example.com
2. Superuser logs in
3. Goes to Admin panel
4. Sees user@example.com in pending list
5. Clicks approve
6. User receives email/can now login

### Promoting a User to Superuser

1. User is already approved
2. Superuser goes to Admin panel
3. Finds user in list
4. Clicks shield icon
5. Confirms promotion
6. User is now a superuser

## Frontend Components

### New Components

- `src/pages/Admin.tsx`: Admin panel page
- Admin API methods in `src/api/client.ts`
- Updated types in `src/types/index.ts`

### Updated Components

- `src/components/Layout/Layout.tsx`: Added Admin link for superusers
- `src/components/Auth/RegisterForm.tsx`: Updated success message
- `src/App.tsx`: Added /admin route

## Environment Variables

No new environment variables required. The system works with existing configuration.

## Troubleshooting

### "Access denied: Superuser privileges required"

- You are not a superuser
- Login with a superuser account
- Or promote your account using `create_superuser.py`

### "Your account is pending approval"

- Your account has not been approved yet
- Contact an administrator
- Check admin panel if you should be approved

### Cannot create superuser

- Make sure database migration has run
- Check database path in script
- Verify database file exists

### Migration already applied

- Normal message if migration was run before
- No action needed
- Database is already up to date

## Best Practices

### Security

1. **Limit Superusers**: Only trusted administrators
2. **Regular Audits**: Review user list periodically
3. **Strong Passwords**: Enforce for superuser accounts
4. **Prompt Approval**: Don't leave users waiting

### User Management

1. **Quick Response**: Approve/reject within 24 hours
2. **Clear Communication**: Tell users about approval process
3. **Verify Emails**: Check user emails before approving
4. **Document Decisions**: Keep track of rejections

### Operational

1. **Backup Database**: Before running migrations
2. **Test Workflow**: Verify approval process works
3. **Monitor Pending**: Check for pending users regularly
4. **Multiple Superusers**: Have at least 2 superusers

## Rollback

If you need to revert the changes:

```bash
# 1. Remove the new columns from database
sqlite3 backend/storage/scorescan.db
> ALTER TABLE users DROP COLUMN is_approved;
> ALTER TABLE users DROP COLUMN is_superuser;
> .exit

# 2. Revert code changes
git revert <commit-hash>

# 3. Rebuild and restart
docker-compose build
docker-compose up -d
```

## Future Enhancements

Potential improvements:

1. **Email Notifications**: Notify users when approved
2. **Bulk Actions**: Approve/reject multiple users at once
3. **User Notes**: Add comments about users
4. **Approval History**: Track who approved whom
5. **Automated Approval**: Based on email domain
6. **Role-Based Access**: More granular permissions
7. **User Suspension**: Temporary access revocation

## Support

For issues or questions:
1. Check logs: `docker-compose logs api`
2. Verify database state with migration script
3. Review this documentation
4. Check admin panel for user status

---

**Implemented**: January 28, 2026  
**Version**: 1.0  
**Status**: ✅ Production Ready

# Deployment Guide: User Approval System

## Quick Start

Follow these steps to deploy the user approval system:

### 1. Stop the Application

```bash
cd /home/norbert/Development/ScoreScan
docker-compose down
```

### 2. Run Database Migration

```bash
cd backend
python3 migrate_add_user_approval.py
```

Expected output:
```
============================================================
User Approval Migration
============================================================

1. Adding 'is_approved' column...
   ✓ Added is_approved column
   ✓ Approved X existing user(s)

2. Adding 'is_superuser' column...
   ✓ Added is_superuser column

============================================================
✅ Migration completed successfully!
============================================================
```

### 3. Create a Superuser

```bash
python3 create_superuser.py
```

Example session:
```
============================================================
Create Superuser Account
============================================================

Email address: admin@example.com
Password: ********
Password (confirm): ********

============================================================
✅ Superuser created successfully!
============================================================

Email: admin@example.com
Permissions: superuser, approved, active
```

### 4. Rebuild and Restart

```bash
cd ..
docker-compose build
docker-compose up -d
```

### 5. Verify

1. Open http://localhost:5173
2. Login with superuser credentials
3. Click "Admin" in the navigation
4. You should see the user management panel

## What Changed

### Backend Changes

**New Files:**
- `backend/app/routers/admin.py` - Admin API endpoints
- `backend/migrate_add_user_approval.py` - Database migration script
- `backend/create_superuser.py` - Superuser creation tool

**Modified Files:**
- `backend/app/models/user.py` - Added is_approved and is_superuser fields
- `backend/app/schemas/user.py` - Updated UserResponse schema
- `backend/app/routers/auth.py` - Added approval checks
- `backend/app/routers/__init__.py` - Registered admin router
- `backend/app/main.py` - Included admin router

### Frontend Changes

**New Files:**
- `frontend/src/pages/Admin.tsx` - Admin panel UI

**Modified Files:**
- `frontend/src/types/index.ts` - Added approval fields to User type
- `frontend/src/api/client.ts` - Added admin API methods
- `frontend/src/components/Layout/Layout.tsx` - Added Admin link
- `frontend/src/components/Auth/RegisterForm.tsx` - Updated success message
- `frontend/src/App.tsx` - Added /admin route

## Testing the System

### Test New User Registration

1. Logout if logged in
2. Click "Sign Up"
3. Register with a new email
4. You should see: "Account created! Please wait for administrator approval"
5. Try to login → Error: "Your account is pending approval"

### Test User Approval

1. Login as superuser
2. Go to Admin panel
3. You should see the new user in "Pending Approval"
4. Click the green checkmark to approve
5. The new user can now login

### Test Superuser Privileges

1. Login as superuser
2. Verify "Admin" link appears in navigation
3. Login as regular user
4. Verify "Admin" link does NOT appear
5. Try to access /admin directly → Redirected to dashboard

## Monitoring

### Check Application Logs

```bash
# API logs
docker-compose logs -f api

# Worker logs
docker-compose logs -f worker

# All logs
docker-compose logs -f
```

### Verify Database

```bash
# Check user table structure
sqlite3 backend/storage/scorescan.db "PRAGMA table_info(users);"

# List all users
sqlite3 backend/storage/scorescan.db "SELECT email, is_approved, is_superuser FROM users;"
```

## Common Issues

### Migration Fails

**Problem**: Migration script reports an error

**Solution**:
1. Check if database exists: `ls backend/storage/scorescan.db`
2. If not, start the app once to create it: `docker-compose up -d`
3. Then run migration: `python3 backend/migrate_add_user_approval.py`

### Cannot Create Superuser

**Problem**: Script cannot find database or modules

**Solution**:
```bash
# Make sure you're in the backend directory
cd backend

# Check Python path
export PYTHONPATH=/home/norbert/Development/ScoreScan/backend:$PYTHONPATH

# Run script
python3 create_superuser.py
```

### Admin Panel Not Accessible

**Problem**: 403 Forbidden when accessing /admin

**Solution**:
1. Check if user is superuser:
   ```bash
   sqlite3 backend/storage/scorescan.db \
     "SELECT email, is_superuser FROM users WHERE email='your@email.com';"
   ```
2. If not, make them superuser:
   ```bash
   python3 backend/create_superuser.py
   # Enter the existing email when prompted
   ```

### Existing Users Cannot Login

**Problem**: Users created before migration cannot login

**Solution**:
This shouldn't happen (migration approves existing users), but if it does:
```bash
sqlite3 backend/storage/scorescan.db \
  "UPDATE users SET is_approved = 1 WHERE created_at < datetime('now');"
```

## Production Deployment

### Additional Steps for Production

1. **Backup Database**:
   ```bash
   cp backend/storage/scorescan.db backend/storage/scorescan.db.backup
   ```

2. **Update Environment Variables**:
   - Ensure `SECRET_KEY` is set to a strong random value
   - Set appropriate `CORS_ORIGINS`

3. **SSL/TLS**:
   - Configure reverse proxy (nginx/traefik)
   - Enable HTTPS
   - Update API URL in frontend

4. **Email Notifications** (Future Enhancement):
   - Configure SMTP settings
   - Send approval confirmation emails

### Health Checks

Add to your monitoring:
```bash
# Check API health
curl http://localhost:8000/health

# Check pending users count
# (requires superuser token)
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/admin/users/pending
```

## Rollback Plan

If you need to rollback:

1. **Stop the application**:
   ```bash
   docker-compose down
   ```

2. **Restore database backup**:
   ```bash
   mv backend/storage/scorescan.db.backup backend/storage/scorescan.db
   ```

3. **Revert code changes**:
   ```bash
   git revert HEAD
   ```

4. **Rebuild and restart**:
   ```bash
   docker-compose build
   docker-compose up -d
   ```

## Support

For detailed information, see:
- [USER_APPROVAL_SYSTEM.md](USER_APPROVAL_SYSTEM.md) - Complete documentation
- [README.md](README.md) - General application documentation

## Checklist

- [ ] Application stopped
- [ ] Database migration completed
- [ ] Superuser created
- [ ] Application rebuilt and restarted
- [ ] Superuser can login
- [ ] Admin panel accessible
- [ ] New user registration tested
- [ ] User approval workflow tested
- [ ] All tests passing

---

**Deployment Date**: _________________  
**Deployed By**: _________________  
**Superuser Email**: _________________  
**Status**: _________________

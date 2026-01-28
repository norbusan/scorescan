# Password Reset - Quick Setup Guide

## Step 1: Run Database Migration

```bash
cd backend
python3 migrate_add_password_reset.py
```

Expected output:
```
======================================================================
Password Reset Tokens Table Migration
======================================================================

🔍 Found database at: /path/to/storage/scorescan.db
📝 Creating 'password_reset_tokens' table...
📝 Creating indexes...
✅ Migration completed successfully!
```

## Step 2: Configure Email Settings

Add to your `.env` file:

```bash
# Email Configuration (for password reset)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=ScoreScan
FRONTEND_URL=http://localhost:5173
```

### Gmail Setup (Recommended for Testing)

1. Go to your Google Account: https://myaccount.google.com/
2. Navigate to **Security** → **2-Step Verification** (enable if not already)
3. Scroll down to **App passwords**
4. Click **Select app** → Choose "Mail"
5. Click **Select device** → Choose "Other" → Enter "ScoreScan"
6. Click **Generate**
7. Copy the 16-character password (without spaces)
8. Use this password in `SMTP_PASSWORD`

## Step 3: Restart Backend

```bash
docker-compose restart backend
```

## Step 4: Test the Feature

1. Go to http://localhost:5173/login
2. Click "Forgot password?"
3. Enter your email
4. Check your email inbox
5. Click the reset link
6. Set new password
7. Login with new password

## Development Mode (No Email)

If you don't configure SMTP, the reset link will be logged to the console:

```bash
# Watch backend logs
docker-compose logs -f backend

# You'll see:
Password reset URL (not sent): http://localhost:5173/reset-password?token=...
```

Copy the URL and paste it into your browser.

## Troubleshooting

### Issue: "Authentication failed" when sending email

**Solution**: Make sure you're using an **App Password**, not your regular Gmail password.

### Issue: Email not received

**Checks**:
1. Check spam folder
2. Verify SMTP settings in `.env`
3. Check backend logs: `docker-compose logs -f backend`
4. Test SMTP connection manually (see full docs)

### Issue: "Invalid or expired token"

**Solutions**:
- Token expires after 24 hours - request a new one
- Each token can only be used once
- Make sure the full URL is copied (including token parameter)

## Security Notes

- Tokens expire after 24 hours (configurable via `PASSWORD_RESET_TOKEN_EXPIRE_HOURS`)
- Each token can only be used once
- Always returns success to prevent email enumeration
- Use HTTPS in production

## Need More Help?

See full documentation: [PASSWORD_RESET.md](./PASSWORD_RESET.md)

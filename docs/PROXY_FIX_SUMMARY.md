# Apache Proxy Fix Summary

## Problem

When running ScoreScan behind Apache reverse proxy, the frontend was trying to connect to `http://localhost:8000` instead of using the proxy URL, resulting in:

```
POST http://localhost:8000/api/auth/login net::ERR_CONNECTION_REFUSED
```

## Root Cause

The `VITE_API_URL` environment variable was hardcoded in `docker-compose.yml` to `http://localhost:8000`, which doesn't work when accessed through a proxy.

## Solution

Changed the configuration to use **relative URLs** by default, which automatically use the current domain (proxy URL).

## Changes Made

### 1. docker-compose.yml

**Before:**
```yaml
environment:
  - VITE_API_URL=http://localhost:8000
```

**After:**
```yaml
environment:
  # Leave empty for relative URLs (recommended for proxy setups)
  # Set to full URL for development: http://localhost:8000
  - VITE_API_URL=${VITE_API_URL:-}
```

Also made CORS_ORIGINS configurable:
```yaml
- CORS_ORIGINS=${CORS_ORIGINS:-http://localhost:5173,http://localhost:3000}
```

### 2. .env.example

**Added:**
```bash
# Frontend API URL
# Leave empty for relative URLs (recommended for Apache/nginx proxy)
# Set to http://localhost:8000 for local development without proxy
VITE_API_URL=

# CORS Origins (comma-separated list of allowed origins)
# Add your domain when running behind a proxy: https://yourdomain.com
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### 3. Documentation

**Created:**
- `APACHE_PROXY_SETUP.md` - Complete Apache proxy configuration guide

**Updated:**
- `README.md` - Added proxy setup section

## How It Works

### With Relative URLs (VITE_API_URL empty)

When `VITE_API_URL` is empty or not set:

```typescript
const API_BASE_URL = import.meta.env.VITE_API_URL || '';
// API_BASE_URL = ''

const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,  // Results in: '/api'
});
```

API calls become:
- `POST /api/auth/login` (relative to current domain)
- When accessed via `https://scorescan.preining.info`, it becomes:
- `POST https://scorescan.preining.info/api/auth/login` ✅

### With Absolute URL (Development)

When `VITE_API_URL=http://localhost:8000`:

```typescript
const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: `http://localhost:8000/api`,
});
```

API calls become:
- `POST http://localhost:8000/api/auth/login` (absolute URL)
- Works for local development ✅
- Doesn't work behind proxy ❌

## Deployment Steps

### For Existing Installations

1. **Update .env file:**
   ```bash
   cd /path/to/ScoreScan
   nano .env
   ```

2. **Set environment variables:**
   ```bash
   # Leave VITE_API_URL empty for relative URLs
   VITE_API_URL=
   
   # Add your domain to CORS
   CORS_ORIGINS=https://scorescan.preining.info,http://localhost:5173
   ```

3. **Restart containers:**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

4. **Verify:**
   - Open browser to `https://scorescan.preining.info`
   - Open DevTools Console (F12)
   - Try to login
   - Check Network tab - API calls should go to:
     - `https://scorescan.preining.info/api/auth/login` ✅
     - NOT `http://localhost:8000/api/auth/login` ❌

### For New Installations

1. **Copy environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit .env:**
   ```bash
   # Keep VITE_API_URL empty (already correct in .env.example)
   VITE_API_URL=
   
   # Add your domain
   CORS_ORIGINS=https://yourdomain.com
   
   # Set secret key
   SECRET_KEY=your-random-secret-key
   ```

3. **Start services:**
   ```bash
   docker-compose up -d
   ```

## Apache Configuration

Add to your Apache VirtualHost:

```apache
<VirtualHost *:443>
    ServerName scorescan.preining.info
    
    # SSL config...
    
    # Proxy API requests
    ProxyPass /api http://localhost:8000/api
    ProxyPassReverse /api http://localhost:8000/api
    
    # Proxy frontend
    ProxyPass / http://localhost:5173/
    ProxyPassReverse / http://localhost:5173/
</VirtualHost>
```

Enable required modules:
```bash
sudo a2enmod proxy proxy_http headers rewrite
sudo systemctl reload apache2
```

## Testing

### 1. Test Environment Variable

```bash
# Inside frontend container
docker-compose exec frontend sh
echo $VITE_API_URL
# Should output: (empty) or nothing
```

### 2. Test API Calls

```bash
# Check browser console (F12) Network tab
# API calls should show:
https://scorescan.preining.info/api/auth/login
# NOT:
http://localhost:8000/api/auth/login
```

### 3. Test CORS

```bash
# Should not see CORS errors in console
# If you do, add domain to CORS_ORIGINS and restart backend
```

## Rollback

If this breaks local development:

1. **Set VITE_API_URL for local development:**
   ```bash
   # In .env
   VITE_API_URL=http://localhost:8000
   ```

2. **Restart:**
   ```bash
   docker-compose restart frontend
   ```

## Benefits

✅ **Works with proxy** - Uses relative URLs that respect proxy domain  
✅ **Backward compatible** - Can still set absolute URL for development  
✅ **Configurable** - Environment variable instead of hardcoded  
✅ **Secure** - Respects CORS configuration  
✅ **Standard** - Follows best practices for SPA behind proxy

## Files Changed

1. `docker-compose.yml` - Made VITE_API_URL and CORS_ORIGINS configurable
2. `.env.example` - Added VITE_API_URL and CORS_ORIGINS documentation
3. `APACHE_PROXY_SETUP.md` - Complete proxy configuration guide (NEW)
4. `README.md` - Added proxy setup section
5. `PROXY_FIX_SUMMARY.md` - This file (NEW)

## Related Documentation

- [APACHE_PROXY_SETUP.md](APACHE_PROXY_SETUP.md) - Complete Apache configuration
- [README.md](README.md) - General documentation
- [.env.example](.env.example) - Environment variables

---

**Issue Fixed:** January 28, 2026  
**Tested With:** Apache 2.4, Docker Compose  
**Status:** ✅ Fixed and Documented

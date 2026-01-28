# Apache Proxy Setup Guide

This guide explains how to run ScoreScan behind an Apache reverse proxy.

## Problem

When running behind Apache proxy, the frontend tries to connect to `http://localhost:8000` which doesn't work because:
1. The API is behind the proxy, not directly accessible
2. The frontend should use relative URLs to go through the proxy

## Solution

Configure ScoreScan to use relative URLs and set up Apache as a reverse proxy.

## Configuration Steps

### 1. Configure ScoreScan Environment

Edit your `.env` file:

```bash
# Leave VITE_API_URL empty for relative URLs
VITE_API_URL=

# Add your domain to CORS origins
CORS_ORIGINS=https://scorescan.preining.info,http://localhost:5173

# Your secret key
SECRET_KEY=your-secure-secret-key-here

# Optional: Enable debug logging
DEBUG=false
```

### 2. Restart Docker Containers

```bash
docker-compose down
docker-compose up -d
```

### 3. Configure Apache Virtual Host

Create or edit your Apache virtual host configuration:

```apache
<VirtualHost *:80>
    ServerName scorescan.preining.info
    
    # Redirect to HTTPS (recommended)
    Redirect permanent / https://scorescan.preining.info/
</VirtualHost>

<VirtualHost *:443>
    ServerName scorescan.preining.info
    
    # SSL Configuration
    SSLEngine on
    SSLCertificateFile /path/to/your/certificate.crt
    SSLCertificateKeyFile /path/to/your/private.key
    SSLCertificateChainFile /path/to/your/chain.crt
    
    # Enable required modules
    # a2enmod proxy proxy_http proxy_wstunnel headers rewrite
    
    # Logging
    ErrorLog ${APACHE_LOG_DIR}/scorescan_error.log
    CustomLog ${APACHE_LOG_DIR}/scorescan_access.log combined
    
    # Proxy settings for WebSocket (if needed in future)
    ProxyPreserveHost On
    ProxyRequests Off
    
    # API Backend Proxy (port 8000)
    ProxyPass /api http://localhost:8000/api
    ProxyPassReverse /api http://localhost:8000/api
    
    # Frontend Proxy (port 5173)
    ProxyPass / http://localhost:5173/
    ProxyPassReverse / http://localhost:5173/
    
    # WebSocket support for Vite HMR (development only)
    RewriteEngine on
    RewriteCond %{HTTP:Upgrade} websocket [NC]
    RewriteCond %{HTTP:Connection} upgrade [NC]
    RewriteRule ^/?(.*) "ws://localhost:5173/$1" [P,L]
    
    # Security headers
    Header always set X-Frame-Options "SAMEORIGIN"
    Header always set X-Content-Type-Options "nosniff"
    Header always set X-XSS-Protection "1; mode=block"
    
    # CORS headers (if needed - usually handled by backend)
    # Header always set Access-Control-Allow-Origin "https://scorescan.preining.info"
</VirtualHost>
```

### 4. Enable Required Apache Modules

```bash
sudo a2enmod proxy
sudo a2enmod proxy_http
sudo a2enmod proxy_wstunnel
sudo a2enmod headers
sudo a2enmod rewrite
sudo a2enmod ssl
```

### 5. Test Apache Configuration

```bash
# Test configuration syntax
sudo apache2ctl configtest

# If OK, reload Apache
sudo systemctl reload apache2
```

## Production Build (Recommended)

For production, it's better to build the frontend as static files and serve them directly with Apache:

### 1. Build Frontend

Create a production Dockerfile for frontend:

```dockerfile
# frontend/Dockerfile.prod
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build for production
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# Production image
FROM nginx:alpine

# Copy built files
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### 2. Create nginx.conf for Frontend

```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Serve static files
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Enable gzip
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
}
```

### 3. Update docker-compose.yml for Production

Add a production frontend service:

```yaml
  frontend-prod:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
      args:
        VITE_API_URL: ""  # Empty for relative URLs
    ports:
      - "8080:80"
    depends_on:
      - backend
    networks:
      - scorescan-network
```

### 4. Update Apache Config for Production Build

```apache
<VirtualHost *:443>
    ServerName scorescan.preining.info
    
    # ... SSL config ...
    
    # Serve static frontend files directly
    DocumentRoot /path/to/scorescan/frontend/dist
    
    <Directory /path/to/scorescan/frontend/dist>
        Options -Indexes +FollowSymLinks
        AllowOverride All
        Require all granted
        
        # SPA routing - redirect all to index.html
        RewriteEngine On
        RewriteBase /
        RewriteRule ^index\.html$ - [L]
        RewriteCond %{REQUEST_FILENAME} !-f
        RewriteCond %{REQUEST_FILENAME} !-d
        RewriteRule . /index.html [L]
    </Directory>
    
    # Proxy API requests to backend
    ProxyPass /api http://localhost:8000/api
    ProxyPassReverse /api http://localhost:8000/api
</VirtualHost>
```

## Troubleshooting

### Issue: CORS Errors

**Symptom:**
```
Access to XMLHttpRequest at 'https://scorescan.preining.info/api/...' from origin 'https://scorescan.preining.info' has been blocked by CORS policy
```

**Solution:**
Add your domain to CORS_ORIGINS in .env:
```bash
CORS_ORIGINS=https://scorescan.preining.info,http://localhost:5173
```

Restart backend:
```bash
docker-compose restart backend
```

### Issue: API Calls Go to localhost:8000

**Symptom:**
Browser console shows:
```
POST http://localhost:8000/api/auth/login net::ERR_CONNECTION_REFUSED
```

**Solution:**
1. Ensure `VITE_API_URL` is empty in .env
2. Rebuild frontend:
   ```bash
   docker-compose down
   docker-compose build frontend
   docker-compose up -d
   ```

### Issue: 502 Bad Gateway

**Symptom:**
Apache returns 502 Bad Gateway error

**Solutions:**

1. **Check if backend is running:**
   ```bash
   docker-compose ps
   curl http://localhost:8000/health
   ```

2. **Check Apache can reach Docker:**
   ```bash
   # From Apache server
   curl http://localhost:8000/api/
   ```

3. **Check SELinux (if enabled):**
   ```bash
   sudo setsebool -P httpd_can_network_connect 1
   ```

4. **Check firewall:**
   ```bash
   sudo ufw allow from 127.0.0.1 to any port 8000
   ```

### Issue: WebSocket Connection Failed (Vite HMR)

**Symptom:**
Development hot-reload doesn't work

**Solution:**
This is normal for production. For development with HMR through proxy:

```apache
# Add to VirtualHost
RewriteEngine on
RewriteCond %{HTTP:Upgrade} websocket [NC]
RewriteCond %{HTTP:Connection} upgrade [NC]
RewriteRule ^/?(.*) "ws://localhost:5173/$1" [P,L]

ProxyPass /ws ws://localhost:5173/ws
ProxyPassReverse /ws ws://localhost:5173/ws
```

### Issue: Static Files Not Loading

**Symptom:**
CSS, JS, or images don't load

**Solution:**

1. **Check Vite base path:**
   In `vite.config.ts`:
   ```typescript
   export default defineConfig({
     base: '/',  // Should be '/' for root domain
     // ...
   })
   ```

2. **Clear browser cache:**
   Hard refresh with Ctrl+Shift+R

3. **Check Apache serves static files:**
   ```apache
   <Directory /path/to/frontend/dist>
       Options -Indexes +FollowSymLinks
       AllowOverride All
       Require all granted
   </Directory>
   ```

## Testing

### 1. Test API Directly

```bash
# From server
curl http://localhost:8000/health
# Expected: {"status":"healthy"}

# Through proxy
curl https://scorescan.preining.info/api/health
# Expected: 404 (health endpoint is at /health, not /api/health)

curl https://scorescan.preining.info/health
# Should proxy to backend
```

### 2. Test Frontend

```bash
# Visit in browser
https://scorescan.preining.info

# Open browser console (F12)
# Try to register/login
# Check Network tab - API calls should go to:
# https://scorescan.preining.info/api/auth/login
# NOT http://localhost:8000/api/auth/login
```

### 3. Test CORS

```bash
# From browser console
fetch('https://scorescan.preining.info/api/health', {
  method: 'GET',
  headers: { 'Content-Type': 'application/json' }
})
.then(r => r.json())
.then(console.log)
```

## Quick Reference

### Environment Variables

| Variable | Value | Purpose |
|----------|-------|---------|
| `VITE_API_URL` | Empty `""` | Use relative URLs for proxy |
| `CORS_ORIGINS` | `https://yourdomain.com` | Allow API access from domain |
| `SECRET_KEY` | Random string | JWT signing |

### URLs

| Service | Internal | Through Proxy |
|---------|----------|---------------|
| Frontend Dev | `http://localhost:5173` | `https://yourdomain.com` |
| Backend API | `http://localhost:8000` | `https://yourdomain.com/api` |
| API Docs | `http://localhost:8000/docs` | Not proxied |

### Apache Commands

```bash
# Test config
sudo apache2ctl configtest

# Reload config
sudo systemctl reload apache2

# Restart Apache
sudo systemctl restart apache2

# View logs
sudo tail -f /var/log/apache2/scorescan_error.log

# Enable site
sudo a2ensite scorescan.conf

# Disable site  
sudo a2dissite scorescan.conf
```

## Security Recommendations

1. **Use HTTPS:** Always use SSL/TLS in production
2. **Firewall:** Block direct access to ports 8000 and 5173
3. **Headers:** Enable security headers in Apache
4. **Secrets:** Use strong SECRET_KEY
5. **Updates:** Keep Apache, Docker, and dependencies updated

## Example Complete Setup

```bash
# 1. Clone repository
cd /var/www
git clone <repo> scorescan
cd scorescan

# 2. Configure environment
cp .env.example .env
nano .env
# Set VITE_API_URL=
# Set CORS_ORIGINS=https://scorescan.preining.info
# Set SECRET_KEY=<random-string>

# 3. Start services
docker-compose up -d

# 4. Configure Apache
sudo nano /etc/apache2/sites-available/scorescan.conf
# Paste configuration from above

# 5. Enable site
sudo a2ensite scorescan.conf
sudo a2enmod proxy proxy_http headers rewrite ssl
sudo apache2ctl configtest
sudo systemctl reload apache2

# 6. Test
curl https://scorescan.preining.info
```

---

**Last Updated:** January 28, 2026  
**Tested With:** Apache 2.4, Docker Compose, Ubuntu 22.04  
**Status:** ✅ Production Ready

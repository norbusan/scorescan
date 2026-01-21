# Apache Configuration for ScoreScan

This directory contains Apache virtual host configurations for the ScoreScan application.

## Files

- `scorescan.conf` - Full HTTPS configuration with SSL/TLS (production)
- `scorescan-http.conf` - HTTP-only configuration (development or behind load balancer)

## Prerequisites

Enable required Apache modules:

```bash
sudo a2enmod proxy proxy_http proxy_wstunnel rewrite ssl headers
sudo systemctl restart apache2
```

## Installation

### Development (HTTP only)

1. Copy the configuration:
   ```bash
   sudo cp scorescan-http.conf /etc/apache2/sites-available/scorescan.conf
   ```

2. Edit the configuration:
   ```bash
   sudo nano /etc/apache2/sites-available/scorescan.conf
   ```
   - Change `ServerName` to your domain or `localhost`

3. Enable the site:
   ```bash
   sudo a2ensite scorescan.conf
   sudo systemctl reload apache2
   ```

### Production (HTTPS)

1. Copy the configuration:
   ```bash
   sudo cp scorescan.conf /etc/apache2/sites-available/scorescan.conf
   ```

2. Edit the configuration:
   ```bash
   sudo nano /etc/apache2/sites-available/scorescan.conf
   ```
   - Change `ServerName` to your actual domain
   - Update SSL certificate paths
   - For static file serving, build the frontend and update `DocumentRoot`

3. Set up SSL certificates (using Let's Encrypt):
   ```bash
   sudo apt install certbot python3-certbot-apache
   sudo certbot --apache -d scorescan.example.com
   ```

4. Enable the site:
   ```bash
   sudo a2ensite scorescan.conf
   sudo systemctl reload apache2
   ```

## Building Frontend for Production

To serve static files instead of proxying to Vite:

1. Build the frontend:
   ```bash
   cd frontend
   npm run build
   ```

2. Copy to web directory:
   ```bash
   sudo mkdir -p /var/www/scorescan
   sudo cp -r frontend/dist/* /var/www/scorescan/
   sudo chown -R www-data:www-data /var/www/scorescan
   ```

3. Update the Apache config to use `DocumentRoot` instead of proxying to Vite.

## Configuration Options

### Ports

By default, the services run on:
- Backend API: `localhost:8000`
- Frontend (Vite): `localhost:5173`

Adjust `ProxyPass` directives if you change these.

### Upload Size

The `LimitRequestBody` is set to 50MB to match the backend limit. Adjust if needed:

```apache
LimitRequestBody 104857600  # 100MB
```

### Timeouts

`ProxyTimeout` is set to 300 seconds (5 minutes) to allow for long processing times:

```apache
ProxyTimeout 600  # 10 minutes
```

## Troubleshooting

### 502 Bad Gateway
- Ensure the backend is running: `docker-compose ps`
- Check backend logs: `docker-compose logs backend`

### 504 Gateway Timeout
- Increase `ProxyTimeout` in Apache config
- Check if the processing is taking too long

### WebSocket Errors (Vite HMR)
- Ensure `proxy_wstunnel` module is enabled
- Check the WebSocket rewrite rules are uncommented

### Permission Denied
- Check file permissions on DocumentRoot
- Ensure Apache can read the files: `sudo chown -R www-data:www-data /var/www/scorescan`

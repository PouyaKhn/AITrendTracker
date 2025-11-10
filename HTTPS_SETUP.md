# HTTPS Setup Guide for AI Trend Tracker

This guide will help you set up HTTPS for your Streamlit app using Nginx and Let's Encrypt.

## Prerequisites

1. A domain name pointing to your server IP (46.62.148.167)
2. SSH access to your server
3. Ports 80 and 443 open in your firewall

---

## Step 1: Install Nginx

On your server, run:

```bash
sudo apt update
sudo apt install -y nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

Verify Nginx is running:
```bash
sudo systemctl status nginx
```

---

## Step 2: Configure Firewall

Allow HTTP and HTTPS traffic:

```bash
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw status
```

---

## Step 3: Create Nginx Configuration

Create a configuration file for your domain:

```bash
sudo nano /etc/nginx/sites-available/aitrendtracker
```

Paste this configuration (replace `yourdomain.com` with your actual domain):

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Redirect all HTTP to HTTPS (will be enabled after SSL setup)
    # For now, comment this out until SSL is configured
    # return 301 https://$server_name$request_uri;

    # Proxy to Streamlit
    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

Save and exit (Ctrl+O, Enter, Ctrl+X).

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/aitrendtracker /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
sudo systemctl reload nginx
```

---

## Step 4: Install Certbot (Let's Encrypt)

```bash
sudo apt install -y certbot python3-certbot-nginx
```

---

## Step 5: Get SSL Certificate

Replace `yourdomain.com` with your actual domain:

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Certbot will:
- Ask for your email (for renewal notices)
- Ask to agree to terms
- Ask if you want to share email with EFF (optional)
- Automatically configure Nginx for HTTPS
- Set up automatic renewal

---

## Step 6: Verify HTTPS Works

1. Visit `https://yourdomain.com` in your browser
2. You should see a padlock icon (🔒) indicating HTTPS is working
3. The site should redirect HTTP to HTTPS automatically

---

## Step 7: Test Automatic Renewal

Let's Encrypt certificates expire every 90 days. Certbot sets up automatic renewal, but test it:

```bash
sudo certbot renew --dry-run
```

If this works, renewal is configured correctly.

---

## Step 8: Update Streamlit Configuration (Optional)

If you want Streamlit to know it's behind a proxy, you can update the systemd service:

```bash
sudo nano /etc/systemd/system/streamlit.service
```

Add these environment variables:

```ini
[Service]
Environment="STREAMLIT_SERVER_HEADLESS=true"
Environment="STREAMLIT_SERVER_ENABLE_CORS=false"
```

Then restart:
```bash
sudo systemctl daemon-reload
sudo systemctl restart streamlit
```

---

## Troubleshooting

### Certificate not working?
- Make sure your domain DNS is pointing to your server IP
- Wait a few minutes for DNS propagation
- Check: `dig yourdomain.com` or `nslookup yourdomain.com`

### Nginx errors?
- Check logs: `sudo tail -f /var/log/nginx/error.log`
- Test config: `sudo nginx -t`
- Check if Streamlit is running: `sudo systemctl status streamlit`

### Can't access site?
- Check firewall: `sudo ufw status`
- Check Nginx: `sudo systemctl status nginx`
- Check Streamlit: `sudo systemctl status streamlit`

### Port 8501 not accessible?
- Make sure Streamlit is running on 127.0.0.1:8501 (localhost only)
- Nginx will proxy from port 80/443 to 8501

---

## Final Nginx Configuration (After SSL)

After Certbot runs, your `/etc/nginx/sites-available/aitrendtracker` will look like this:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # SSL configuration (added by Certbot)
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

---

## Notes

- **Domain Required**: You need a domain name for HTTPS. IP addresses alone won't work with Let's Encrypt.
- **DNS Propagation**: After pointing your domain to the server, wait 5-30 minutes for DNS to propagate.
- **Certificate Renewal**: Certbot automatically renews certificates. You can verify with `sudo certbot renew --dry-run`.
- **Security**: HTTPS encrypts all traffic between users and your server, protecting login credentials and data.

---

## Quick Reference Commands

```bash
# Check Nginx status
sudo systemctl status nginx

# Check Streamlit status  
sudo systemctl status streamlit

# Test Nginx config
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx

# Check SSL certificate expiry
sudo certbot certificates

# Manually renew certificate
sudo certbot renew

# View Nginx error logs
sudo tail -f /var/log/nginx/error.log
```


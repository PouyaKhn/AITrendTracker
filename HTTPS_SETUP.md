# HTTPS Setup Guide for ai-center.dk

This guide explains how to set up HTTPS (SSL/TLS) for your domain using Let's Encrypt and Certbot.

## Prerequisites

- Domain `ai-center.dk` pointing to your server IP (A record)
- Nginx installed and configured
- Port 80 and 443 open in firewall
- Root or sudo access to the server

## Step 1: Install Certbot

```bash
sudo apt update
sudo apt install certbot python3-certbot-nginx -y
```

## Step 2: Obtain SSL Certificate

Certbot will automatically configure Nginx for HTTPS:

```bash
sudo certbot --nginx -d ai-center.dk -d www.ai-center.dk
```

This command will:
- Obtain SSL certificates for both `ai-center.dk` and `www.ai-center.dk`
- Automatically update your Nginx configuration
- Set up automatic renewal

**During the process, you'll be asked:**
- Email address (for renewal notifications)
- Agree to terms of service
- Choose whether to redirect HTTP to HTTPS (recommended: Yes)

## Step 3: Verify HTTPS is Working

After Certbot completes, test your site:

```bash
# Test Nginx configuration
sudo nginx -t

# Reload Nginx if test passes
sudo systemctl reload nginx

# Check certificate status
sudo certbot certificates
```

Visit `https://ai-center.dk/aitrendtracker/` in your browser to verify HTTPS is working.

## Step 4: Automatic Renewal

Certbot sets up automatic renewal. Certificates expire every 90 days and are automatically renewed.

**Test renewal manually:**
```bash
sudo certbot renew --dry-run
```

**Check renewal status:**
```bash
sudo systemctl status certbot.timer
```

## Step 5: Firewall Configuration

Ensure ports 80 and 443 are open:

```bash
# Check current rules
sudo ufw status

# Allow HTTP and HTTPS if not already allowed
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Reload firewall
sudo ufw reload
```

## Troubleshooting

### Certificate Not Obtained

**Error: "Failed to obtain certificate"**
- Verify domain DNS points to your server: `dig ai-center.dk`
- Ensure port 80 is accessible from internet
- Check Nginx is running: `sudo systemctl status nginx`

### Nginx Configuration Issues

**Error: "conflicting server name"**
- Remove duplicate server blocks in `/etc/nginx/sites-enabled/`
- Keep only the Certbot-modified configuration

### Certificate Renewal Fails

**Check renewal logs:**
```bash
sudo journalctl -u certbot.timer
sudo certbot renew --dry-run
```

**Manual renewal:**
```bash
sudo certbot renew
sudo systemctl reload nginx
```

## Manual Configuration (Alternative)

If you prefer to manually configure HTTPS, Certbot will create a new configuration file at:
`/etc/nginx/sites-available/ai-center.dk-le-ssl.conf`

You can then manually merge the HTTPS settings into your existing configuration.

## Security Best Practices

1. **Force HTTPS redirect**: Certbot will add this automatically
2. **Strong SSL protocols**: Certbot configures modern TLS versions
3. **Automatic renewal**: Certbot timer handles this automatically
4. **Regular updates**: Keep Certbot updated: `sudo apt update && sudo apt upgrade certbot`

## Verification

After setup, verify your SSL configuration:

```bash
# Check SSL certificate
openssl s_client -connect ai-center.dk:443 -servername ai-center.dk

# Online SSL checker
# Visit: https://www.ssllabs.com/ssltest/analyze.html?d=ai-center.dk
```

Your site should now be accessible at `https://ai-center.dk/aitrendtracker/` with a valid SSL certificate.


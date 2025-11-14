# Domain Setup Guide for ai-center.dk/AITrendTracker

This guide will help you set up your Streamlit app at `ai-center.dk/aitrendtracker`.

---

## Step 1: Update Streamlit Service for Base Path

Edit the Streamlit systemd service file:

```bash
sudo nano /etc/systemd/system/streamlit.service
```

Update the `ExecStart` line to include the base path:

```ini
[Unit]
Description=Streamlit App
After=network.target

[Service]
User=deployer
WorkingDirectory=/home/deployer/Secondment
Environment="PATH=/home/deployer/Secondment/venv/bin"
ExecStart=/home/deployer/Secondment/venv/bin/streamlit run streamlit_app.py --server.port 8501 --server.address 127.0.0.1 --server.baseUrlPath=/aitrendtracker
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Important**: 
- `--server.address 127.0.0.1` (localhost only - Nginx will proxy)
- `--server.baseUrlPath=/aitrendtracker` (the base path)

Save and reload:

```bash
sudo systemctl daemon-reload
sudo systemctl restart streamlit
sudo systemctl status streamlit
```

---

## Step 2: Install Nginx (if not already installed)

```bash
sudo apt update
sudo apt install -y nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

---

## Step 3: Configure Firewall

```bash
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw status
```

---

## Step 4: Create Nginx Configuration

Copy the configuration file to Nginx:

```bash
sudo cp /home/deployer/Secondment/nginx-ai-center.conf /etc/nginx/sites-available/ai-center.dk
```

Or create it manually:

```bash
sudo nano /etc/nginx/sites-available/ai-center.dk
```

Paste this configuration:

```nginx
server {
    listen 80;
    server_name ai-center.dk www.ai-center.dk;

    # Temporary placeholder for root (empty for now)
    location = / {
        add_header Content-Type text/plain;
        return 200 "Coming soon...\n";
    }

    # Redirect /aitrendtracker to /aitrendtracker/ (with trailing slash)
    location = /aitrendtracker {
        return 301 /aitrendtracker/;
    }

    # Proxy the Streamlit app under /aitrendtracker/
    location /aitrendtracker/ {
        proxy_pass http://127.0.0.1:8501/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;

        # Allow WebSocket connections for Streamlit
        proxy_set_header Sec-WebSocket-Extensions $http_sec_websocket_extensions;
        proxy_set_header Sec-WebSocket-Key $http_sec_websocket_key;
        proxy_set_header Sec-WebSocket-Version $http_sec_websocket_version;
    }
}
```

Save and exit (Ctrl+O, Enter, Ctrl+X).

---

## Step 5: Enable the Site

```bash
sudo ln -s /etc/nginx/sites-available/ai-center.dk /etc/nginx/sites-enabled/
```

---

## Step 6: Test Nginx Configuration

```bash
sudo nginx -t
```

You should see: `nginx: configuration file /etc/nginx/nginx.conf test is successful`

---

## Step 7: Reload Nginx

```bash
sudo systemctl reload nginx
```

---

## Step 8: Test HTTP Access

1. Visit `http://ai-center.dk/aitrendtracker` in your browser
2. You should see your Streamlit app
3. The root `http://ai-center.dk/` should show "Coming soon..."

---

## Step 9: Set Up HTTPS (Recommended)

Install Certbot:

```bash
sudo apt install -y certbot python3-certbot-nginx
```

Get SSL certificate:

```bash
sudo certbot --nginx -d ai-center.dk -d www.ai-center.dk
```

Certbot will:
- Ask for your email
- Ask to agree to terms
- Ask about sharing email (optional)
- Automatically configure HTTPS
- Set up automatic renewal

After this, your site will be available at `https://ai-center.dk/aitrendtracker`

---

## Step 10: Verify Everything Works

1. **HTTP**: `http://ai-center.dk/aitrendtracker` → should redirect to HTTPS
2. **HTTPS**: `https://ai-center.dk/aitrendtracker` → should show your Streamlit app
3. **Root**: `https://ai-center.dk/` → should show "Coming soon..."

---

## Troubleshooting

### Can't access the app?
- Check Streamlit is running: `sudo systemctl status streamlit`
- Check Nginx is running: `sudo systemctl status nginx`
- Check logs: `sudo tail -f /var/log/nginx/error.log`
- Test locally: `curl http://127.0.0.1:8501/aitrendtracker/`

### 502 Bad Gateway?
- Streamlit might not be running: `sudo systemctl restart streamlit`
- Check if port 8501 is listening: `netstat -tln | grep 8501`

### DNS not working?
- Wait 5-30 minutes for DNS propagation
- Check DNS: `dig ai-center.dk` or `nslookup ai-center.dk`
- Should return: `46.62.148.167`

### Nginx config errors?
- Test config: `sudo nginx -t`
- Check syntax in the config file
- Make sure there are no typos

---

## Quick Reference Commands

```bash
# Restart Streamlit
sudo systemctl restart streamlit

# Restart Nginx
sudo systemctl reload nginx

# Check Streamlit status
sudo systemctl status streamlit

# Check Nginx status
sudo systemctl status nginx

# View Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Test Nginx config
sudo nginx -t

# Check SSL certificate
sudo certbot certificates
```


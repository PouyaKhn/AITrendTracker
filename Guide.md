# AI Trend Tracker – Full Deployment Guide (Beginner Friendly)

This guide takes you from zero to a running server with your Streamlit dashboard on a real domain (e.g., AITrendTracker.dk). It assumes a fresh Ubuntu VPS.

If you get stuck, re-run any step safely. Commands with `sudo` may ask for your password.

---

## 0) What You'll Need

- A VPS (Ubuntu 22.04/24.04 recommended)
- A domain (e.g., AITrendTracker.dk) with access to DNS
- OpenAI API key and/or Anthropic API key

---

## 1) Connect to Your Server

On your local machine (Mac/Linux/WSL):

```bash
ssh youruser@your_server_ip
```

If you only have `root@ip`, use that first; you can add a user later.

---

## 2) Basic Server Setup

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git python3-venv python3-pip nginx ufw
```

(Optional) Basic firewall:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

---

## 3) Point Your Domain to the Server

In your registrar's DNS panel:
- A record: `AITrendTracker.dk` → your VPS IP
- (Optional) CNAME: `www` → `AITrendTracker.dk`

Check propagation:

```bash
dig +short aitrendtracker.dk
```

---

## 4) Get the App Code and Install

```bash
sudo mkdir -p /opt/ai-trend-tracker
sudo chown $USER:$USER /opt/ai-trend-tracker
cd /opt/ai-trend-tracker

# If you use Git:
# git clone https://github.com/yourname/ai-trend-tracker.git .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 5) Configure Environment Variables

Create a system env file for keys/settings:

```bash
sudo tee /etc/ai-trend-tracker.env >/dev/null <<'EOF'
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
FETCH_INTERVAL=120
MAX_ARTICLES=0
LOG_LEVEL=INFO
STORAGE_DIR=/opt/ai-trend-tracker/data
LOG_PATH=/opt/ai-trend-tracker/logs/news_scraper.log
EOF

sudo chmod 640 /etc/ai-trend-tracker.env
sudo chown root:root /etc/ai-trend-tracker.env
```

---

## 6) Create Data and Log Directories

```bash
mkdir -p /opt/ai-trend-tracker/data
mkdir -p /opt/ai-trend-tracker/logs
sudo chown -R $USER:$USER /opt/ai-trend-tracker/data /opt/ai-trend-tracker/logs
```

---

## 7) Run Streamlit as a Service (systemd)

Run Streamlit on localhost and reverse proxy with Nginx.

Create a service (replace `YOURUSER` with your actual username):

```bash
sudo tee /etc/systemd/system/ai-trend-tracker-web.service >/dev/null <<EOF
[Unit]
Description=AI Trend Tracker Streamlit Web
After=network.target

[Service]
Type=simple
User=YOURUSER
WorkingDirectory=/opt/ai-trend-tracker
EnvironmentFile=/etc/ai-trend-tracker.env
ExecStart=/opt/ai-trend-tracker/venv/bin/streamlit run streamlit_app.py --server.port 8501 --server.address 127.0.0.1
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

Enable/start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-trend-tracker-web
sudo systemctl start ai-trend-tracker-web
sudo systemctl status ai-trend-tracker-web
```

---

## 8) Nginx Reverse Proxy (Your Domain)

Create a site file:

```bash
sudo tee /etc/nginx/sites-available/ai-trend-tracker >/dev/null <<EOF
server {
    listen 80;
    server_name aitrendtracker.dk www.aitrendtracker.dk;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_read_timeout 600;
        proxy_send_timeout 600;
        proxy_connect_timeout 600;
        proxy_buffering off;
    }

    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
}
EOF
```

Enable and reload Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/ai-trend-tracker /etc/nginx/sites-enabled/ai-trend-tracker
sudo nginx -t && sudo systemctl reload nginx
```

Visit `http://AITrendTracker.dk`.

---

## 9) HTTPS (Let's Encrypt)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d aitrendtracker.dk -d www.aitrendtracker.dk
```

Choose redirect → HTTPS. Certificates auto-renew.

Visit `https://AITrendTracker.dk`.

---

## 10) Use the Dashboard

- **START**: Runs the pipeline in the background as a separate process
- **STOP**: Terminates the running pipeline
- **Refresh Stats**: Manually update statistics (auto-refreshes every 5 minutes)
- **Language Selection**: Switch between English and Danish interface

(Optional) Always-on pipeline via a second service:

```bash
sudo tee /etc/systemd/system/ai-trend-tracker-pipeline.service >/dev/null <<EOF
[Unit]
Description=AI Trend Tracker Pipeline (continuous)
After=network.target

[Service]
Type=simple
User=YOURUSER
WorkingDirectory=/opt/ai-trend-tracker
EnvironmentFile=/etc/ai-trend-tracker.env
ExecStart=/opt/ai-trend-tracker/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-trend-tracker-pipeline
sudo systemctl start ai-trend-tracker-pipeline
sudo systemctl status ai-trend-tracker-pipeline
```

**Note**: Choose one approach - either use the dashboard controls OR the continuous service, not both simultaneously.

---

## 11) Permissions

Ensure proper permissions:

```bash
sudo chown -R YOURUSER:YOURUSER /opt/ai-trend-tracker/data /opt/ai-trend-tracker/logs
```

---

## 12) Logs & Monitoring

```bash
# Streamlit service logs
journalctl -u ai-trend-tracker-web -f

# Pipeline service logs (if enabled)
journalctl -u ai-trend-tracker-pipeline -f

# Application logs
tail -f /opt/ai-trend-tracker/logs/news_scraper.log
```

Restart services:

```bash
sudo systemctl restart ai-trend-tracker-web
sudo systemctl restart ai-trend-tracker-pipeline   # if used
```

---

## 13) Updating the App

```bash
cd /opt/ai-trend-tracker
# git pull   # if using git
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart ai-trend-tracker-web
sudo systemctl restart ai-trend-tracker-pipeline   # if used
```

---

## 14) Troubleshooting

### Streamlit not responding

```bash
sudo systemctl status ai-trend-tracker-web
journalctl -u ai-trend-tracker-web -f
```

### 502 Bad Gateway

```bash
sudo nginx -t
sudo systemctl reload nginx
# Ensure Streamlit is running on 127.0.0.1:8501
sudo systemctl status ai-trend-tracker-web
```

### Port busy

Change `--server.port` in the service file and update `proxy_pass` in Nginx config.

### Missing API keys

Check `/etc/ai-trend-tracker.env` and restart services:

```bash
sudo systemctl restart ai-trend-tracker-web
sudo systemctl restart ai-trend-tracker-pipeline
```

### No new articles

GDELT may not have items in the current 2-hour window. The system fetches from the past 2 hours only (minimum GDELT timespan). Check logs for domain failures:

```bash
tail -f /opt/ai-trend-tracker/logs/news_scraper.log | grep -i "domain\|failed"
```

### Database issues

```bash
# Check database
sqlite3 /opt/ai-trend-tracker/data/processed_articles.db "SELECT COUNT(*) FROM processed_articles;"

# View recent articles
sqlite3 /opt/ai-trend-tracker/data/processed_articles.db "SELECT title, domain, processed_at FROM processed_articles ORDER BY processed_at DESC LIMIT 10;"
```

---

## 15) Security Tips (Optional)

- Keep OS updated: `sudo apt update && sudo apt upgrade -y`
- Use SSH keys instead of passwords
- Monitor disk usage: `df -h` and rotate logs if needed
- Regular backups of `/opt/ai-trend-tracker/data/processed_articles.db`
- Review firewall rules: `sudo ufw status verbose`

---

## 16) Performance Tuning

### Increase Nginx timeouts (if processing large batches)

Edit `/etc/nginx/sites-available/ai-trend-tracker` and increase timeout values if needed.

### Monitor resource usage

```bash
# CPU and memory
htop

# Disk usage
df -h
du -sh /opt/ai-trend-tracker/data/*

# Database size
ls -lh /opt/ai-trend-tracker/data/processed_articles.db
```

---

## Done

Your dashboard should now be live on your domain with HTTPS. Use the UI to run and monitor the pipeline. The system will:

- Fetch articles from GDELT every 2 hours (or as configured)
- Classify AI-related content using LLM APIs
- Store results in SQLite database
- Display analytics in the Streamlit dashboard
- Support both English and Danish interfaces

#!/bin/bash
# Script to add WebSocket map directive to nginx.conf

NGINX_CONF="/etc/nginx/nginx.conf"
BACKUP="/etc/nginx/nginx.conf.backup.$(date +%Y%m%d_%H%M%S)"

# Backup original config
sudo cp "$NGINX_CONF" "$BACKUP"
echo "Backup created: $BACKUP"

# Check if map already exists
if sudo grep -q "map \$http_upgrade \$connection_upgrade" "$NGINX_CONF"; then
    echo "WebSocket map directive already exists. Skipping."
    exit 0
fi

# Use Python to insert the map directive after "http {"
sudo python3 << 'PYTHON'
import re

nginx_conf = "/etc/nginx/nginx.conf"

# Read the file
with open(nginx_conf, 'r') as f:
    content = f.read()

# Check if already exists
if "map $http_upgrade $connection_upgrade" in content:
    print("WebSocket map directive already exists. Skipping.")
    exit(0)

# Find http { and add map directive after it
map_directive = """    # Map WebSocket upgrade header
    map $http_upgrade $connection_upgrade {
        default upgrade;
        '' close;
    }
"""

# Pattern to match "http {" at the start of a line
pattern = r'(^http \{)(\n)'
replacement = r'\1\2' + map_directive

# Replace
new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

# Write back
with open(nginx_conf, 'w') as f:
    f.write(new_content)

print("WebSocket map directive added successfully!")
PYTHON

echo "Done! Test with: sudo nginx -t"


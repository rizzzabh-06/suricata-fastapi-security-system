# Suricata + FastAPI Security System

A lightweight, self-hosted network security system that detects and mitigates real network threats.

## Architecture

```
[Suricata Sensor] → [EVE JSON] → [FastAPI Backend] → [Detection Engine] → [WebSocket Stream] → [Dashboard]
                                                    ↓
                                              [Mitigation Layer]
```

## Requirements

- Ubuntu 22.04+
- Python 3.11+
- Suricata with EVE JSON enabled
- nginx (for production deployment)

## Quick Start

### 1. Install Dependencies

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

### 3. Run Backend

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## System Integration (Production)

### Systemd Service

Create `/etc/systemd/system/secapp-backend.service`:

```ini
[Unit]
Description=SecApp Backend (FastAPI)
After=network.target

[Service]
User=secapp
Group=secapp
WorkingDirectory=/opt/secapp/backend
Environment="PATH=/opt/secapp/backend/venv/bin"
ExecStart=/opt/secapp/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now secapp-backend.service
```

### Nginx Configuration

Create `/etc/nginx/sites-available/secapp`:

```nginx
server {
    listen 80;
    server_name _;

    root /opt/secapp/frontend;
    index index.html;

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws {
        proxy_pass http://127.0.0.1:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

Enable and reload:

```bash
sudo ln -s /etc/nginx/sites-available/secapp /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### Sudoers Configuration

Add to `/etc/sudoers.d/secapp`:

```
secapp ALL=(root) NOPASSWD: /usr/local/bin/secapp-mitigate
```

Install the helper script:

```bash
sudo cp scripts/secapp-mitigate /usr/local/bin/
sudo chown root:root /usr/local/bin/secapp-mitigate
sudo chmod 750 /usr/local/bin/secapp-mitigate
```

### Suricata Setup

1. Enable EVE JSON in `/etc/suricata/suricata.yaml`:

```yaml
outputs:
  - eve-log:
      enabled: yes
      filetype: regular
      filename: eve.json
```

2. Copy local rules:

```bash
sudo cp suricata/rules/local.rules /etc/suricata/rules/
```

3. Update `/etc/suricata/suricata.yaml` to include local rules:

```yaml
rule-files:
  - local.rules
```

4. Restart Suricata:

```bash
sudo systemctl restart suricata
```

## Production Deployment

### Step 1: Create Service User

```bash
sudo adduser --disabled-login --gecos "SecurityApp" secapp
sudo mkdir -p /opt/secapp
sudo chown secapp:secapp /opt/secapp
```

### Step 2: Deploy Application

```bash
sudo -u secapp git clone <your-repo-url> /opt/secapp
cd /opt/secapp/backend
sudo -u secapp python3 -m venv venv
sudo -u secapp venv/bin/pip install -r requirements.txt
```

### Step 3: Configure Environment

```bash
sudo -u secapp cp /opt/secapp/backend/.env.example /opt/secapp/backend/.env
sudo -u secapp nano /opt/secapp/backend/.env
```

Set production values:
```
EVE_PATH=/var/log/suricata/eve.json
AUTO_MITIGATE=0
JWT_SECRET=<generate-random-secret>
JWT_EXPIRE_MIN=60
SECAPP_USER=admin
SECAPP_PASS=<strong-password>
WINDOW_SECS=60
PPS_THRESHOLD=100
```

### Step 4: Install Mitigation Helper

```bash
sudo cp /opt/secapp/scripts/secapp-mitigate /usr/local/bin/
sudo chown root:root /usr/local/bin/secapp-mitigate
sudo chmod 750 /usr/local/bin/secapp-mitigate
```

### Step 5: Configure Sudoers

Create `/etc/sudoers.d/secapp`:

```bash
sudo visudo -f /etc/sudoers.d/secapp
```

Add:
```
secapp ALL=(root) NOPASSWD: /usr/local/bin/secapp-mitigate
```

Set permissions:
```bash
sudo chmod 440 /etc/sudoers.d/secapp
```

### Step 6: Create Systemd Service

Create `/etc/systemd/system/secapp-backend.service`:

```ini
[Unit]
Description=SecApp Backend (FastAPI)
After=network.target suricata.service

[Service]
User=secapp
Group=secapp
WorkingDirectory=/opt/secapp/backend
EnvironmentFile=/opt/secapp/backend/.env
Environment="PATH=/opt/secapp/backend/venv/bin"
ExecStart=/opt/secapp/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable secapp-backend.service
sudo systemctl start secapp-backend.service
sudo systemctl status secapp-backend.service
```

### Step 7: Configure Nginx

Create `/etc/nginx/sites-available/secapp`:

```nginx
server {
    listen 80;
    server_name _;

    # Frontend
    location / {
        root /opt/secapp/frontend;
        try_files $uri $uri/ /index.html;
    }

    # API endpoints
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # WebSocket
    location /ws {
        proxy_pass http://127.0.0.1:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

Enable and reload:
```bash
sudo ln -s /etc/nginx/sites-available/secapp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Step 8: Configure Suricata

1. Enable EVE JSON in `/etc/suricata/suricata.yaml`:

```yaml
outputs:
  - eve-log:
      enabled: yes
      filetype: regular
      filename: eve.json
      types:
        - alert
        - http
        - dns
        - tls
        - flow
```

2. Copy local rules:

```bash
sudo cp /opt/secapp/suricata/rules/local.rules /etc/suricata/rules/
```

3. Update `/etc/suricata/suricata.yaml` to include local rules:

```yaml
rule-files:
  - suricata.rules
  - local.rules
```

4. Set permissions for EVE log:

```bash
sudo usermod -aG adm secapp
sudo chmod 644 /var/log/suricata/eve.json
```

5. Restart Suricata:

```bash
sudo systemctl restart suricata
sudo systemctl status suricata
```

### Step 9: Verify Installation

```bash
# Check backend service
sudo systemctl status secapp-backend

# Check logs
sudo journalctl -u secapp-backend -f

# Test API
curl http://localhost:8000/api/health

# Check Suricata is writing EVE JSON
sudo tail -f /var/log/suricata/eve.json
```

## Testing with Attack Simulation

**WARNING: Lab use only. Never run against production systems without authorization.**

```bash
cd /opt/secapp/attack
python3 http_flood.py http://target-ip 150
```

This generates 150 requests/sec to trigger PPS threshold alerts.

## Validation Checklist

- [ ] Backend service running: `systemctl status secapp-backend`
- [ ] Nginx serving frontend: `curl http://localhost/`
- [ ] `/api/health` returns `{"status": "ok"}`
- [ ] WebSocket connects at `ws://localhost/ws`
- [ ] Suricata writing to `/var/log/suricata/eve.json`
- [ ] Events appear in dashboard Live tab
- [ ] PPS threshold triggers alerts (test with attack script)
- [ ] Top talkers populated during traffic
- [ ] Login works with configured credentials
- [ ] Block IP creates iptables rule: `sudo iptables -L INPUT -n`
- [ ] Unblock removes iptables rule
- [ ] Audit log records all mitigation actions
- [ ] Auto-unblock works after TTL expires

## Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `EVE_PATH` | `/var/log/suricata/eve.json` | Path to Suricata EVE JSON log |
| `AUTO_MITIGATE` | `0` | Enable automatic mitigation (1=yes, 0=no) |
| `JWT_SECRET` | `change_me` | Secret for JWT signing |
| `JWT_EXPIRE_MIN` | `60` | JWT token expiration in minutes |
| `SECAPP_USER` | `admin` | Login username |
| `SECAPP_PASS` | `admin` | Login password |
| `WINDOW_SECS` | `60` | Sliding window duration for PPS calculation |
| `PPS_THRESHOLD` | `100` | Alert threshold for packets per second |

### Tuning Detection

**For high-traffic networks:**
```bash
WINDOW_SECS=30
PPS_THRESHOLD=500
```

**For low-traffic/sensitive networks:**
```bash
WINDOW_SECS=120
PPS_THRESHOLD=50
```

## Troubleshooting

### Backend won't start
```bash
sudo journalctl -u secapp-backend -n 50
# Check Python dependencies
sudo -u secapp /opt/secapp/backend/venv/bin/pip list
```

### No events appearing
```bash
# Check Suricata is running
sudo systemctl status suricata

# Check EVE JSON is being written
sudo tail -f /var/log/suricata/eve.json

# Check file permissions
ls -la /var/log/suricata/eve.json

# Verify secapp user can read
sudo -u secapp cat /var/log/suricata/eve.json | head
```

### Mitigation not working
```bash
# Test helper script manually
sudo /usr/local/bin/secapp-mitigate block 192.168.1.100
sudo iptables -L INPUT -n | grep 192.168.1.100
sudo /usr/local/bin/secapp-mitigate unblock 192.168.1.100

# Check sudoers
sudo -u secapp sudo -l
```

### WebSocket disconnects
```bash
# Check nginx WebSocket config
sudo nginx -T | grep -A 5 "location /ws"

# Check backend logs
sudo journalctl -u secapp-backend -f
```

## Security Notes

- JWT tokens stored in memory only (not localStorage)
- All API inputs validated via Pydantic schemas
- Mitigation operates through helper script only (no direct iptables from Python)
- AUTO_MITIGATE=0 by default (manual approval required)
- All mitigation actions audited with timestamp/actor/reason
- Backend binds to 127.0.0.1 (nginx reverse proxy only)
- Sudoers restricted to specific script path
- Helper script validates IP format before iptables operations

## Maintenance

### View logs
```bash
sudo journalctl -u secapp-backend -f
```

### Restart service
```bash
sudo systemctl restart secapp-backend
```

### Update application
```bash
cd /opt/secapp
sudo -u secapp git pull
sudo systemctl restart secapp-backend
```

### Backup configuration
```bash
sudo tar -czf secapp-backup-$(date +%Y%m%d).tar.gz /opt/secapp/backend/.env /etc/systemd/system/secapp-backend.service /etc/nginx/sites-available/secapp
```

## License

MIT License - For ethical and educational use only.

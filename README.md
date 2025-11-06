# Suricata + FastAPI Security System

A lightweight, self-hosted cybersecurity system that detects and mitigates real network threats by analyzing **Suricata EVE JSON output** in real time. It combines data structures and algorithms (DSA), modern backend logic, and a minimal web dashboard for monitoring and safe mitigation.

---

## 🚀 Overview

This project integrates **Suricata** (as the packet capture and detection sensor) with a **Python FastAPI** backend that performs additional real-time analytics using efficient **DSA techniques**. The backend streams processed events to a live dashboard via WebSockets, allowing operators to visualize anomalies, assess attack patterns, and take manual mitigation actions.

### Core Features

* **Real-Time Threat Detection** from Suricata alerts (EVE JSON format)
* **DSA-Driven Analysis Engine** using sliding windows, hash tables, and bloom filters
* **Live Web Dashboard** connected to backend via WebSockets
* **Manual & Safe Mitigation** with IP block/unblock
* **Systemd-Based Deployment** — no Docker needed

---

## 🧩 Architecture

```
[Suricata Sensor] → [EVE JSON] → [FastAPI Backend] → [Detection Engine] → [WebSocket Stream] → [Dashboard]
                                                    ↓
                                              [Mitigation Layer]
```

### Key Components

| Folder      | Purpose                                                    |
| ----------- | ---------------------------------------------------------- |
| `suricata/` | Custom Suricata rules and configurations                   |
| `backend/`  | FastAPI backend with detection engine and mitigation logic |
| `frontend/` | Live security dashboard (WebSocket-based)                  |
| `attack/`   | Controlled attack simulation scripts for testing detection |

---

## 🧠 How We Use DSA

This system applies **Data Structures and Algorithms** for performance and real-time detection efficiency:

| DSA Concept                | Usage                                                                                            |
| -------------------------- | ------------------------------------------------------------------------------------------------ |
| **Sliding Window (Deque)** | Maintains recent packets/alerts per IP to compute rolling PPS and detect short-term anomalies    |
| **Hash Tables (Dicts)**    | Tracks flow-level counters: IP → stats (pps, bytes/sec, alerts)                                  |
| **Bloom Filter**           | Quickly checks whether an IP/domain is part of known malicious lists without storing entire sets |
| **Count-Min Sketch**       | Identifies top talkers (approximate heavy hitters) in large-scale traffic efficiently            |
| **Heaps/Priority Queues**  | Ranks top offending IPs by PPS or severity for dashboard display                                 |
| **Graph Structures**       | (Planned) To map attacker–victim communication paths for lateral movement detection              |
| **Union-Find (Optional)**  | For clustering correlated alerts and grouping connected flows                                    |

These algorithms ensure **O(1)** or **O(log n)** operations even under heavy network load, enabling near real-time detection without external dependencies or databases.

---

## 🛠️ Installation & Setup

### Requirements

Ubuntu 22.04+ with `suricata`, `python3.11`, `nginx`, and `git` installed.

### Setup Steps

```bash
sudo adduser --disabled-login --gecos "SecurityApp" secapp
sudo mkdir -p /opt/secapp && sudo chown secapp:secapp /opt/secapp
sudo -u secapp git clone <your-repo-url> /opt/secapp
```

### Configure Suricata

1. Enable EVE JSON in `/etc/suricata/suricata.yaml`.
2. Copy local rules:

```bash
sudo cp suricata/rules/local.rules /etc/suricata/rules/local.rules
sudo systemctl restart suricata
```

Example rule:

```
alert http any any -> any any (msg:"LOCAL SQLi attempt"; http_uri; content:"UNION"; nocase; sid:1000001; rev:1;)
```

### Setup Backend

```bash
cd /opt/secapp/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Access dashboard: [http://localhost:8000/](http://localhost:8000/)

---

## ⚙️ System Services (No Docker)

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

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now secapp-backend.service
```

### Nginx Frontend Proxy

Serve `/frontend/index.html` and proxy API + WebSocket traffic:

```nginx
server {
    listen 80;
    server_name _;

    root /var/www/secapp;
    index index.html;

    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
    }

    location /ws/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

Reload nginx:

```bash
sudo nginx -t && sudo systemctl reload nginx
```

---

## 🔒 Mitigation & Safety

Mitigation actions use controlled privileges:

* IP block/unblock via `/usr/local/bin/secapp-mitigate` helper script
* Logged actions with timestamps, reasons, and TTLs
* Manual mode by default; auto-mitigation requires `AUTO_MITIGATE=1`

Example sudoers entry:

```
secapp ALL=(root) NOPASSWD: /usr/local/bin/secapp-mitigate
```

---

## 💻 Dashboard

* Minimal WebSocket-based interface showing live alerts
* Displays JSON events, PPS counters, and top IPs
* To be extended with charts, ATT&CK mappings, and audit views

---

## 🧪 Testing & Simulation

Simulate traffic using provided attack script:

```bash
python3 attack/http_flood.py
```

Detects high PPS spikes → triggers alert → optional mitigation.

---

## 🧾 License

Released under the MIT License — for ethical and educational use only.

---

## 👨‍💻 Author

Developed by **Rishabh Raj Singh** — cybersecurity researcher and founder focused on ethical security automation systems.

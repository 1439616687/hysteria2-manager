## README.md - 项目文档 v2.0

```markdown
# Hysteria2 Manager v2.0

<div align="center">

![Hysteria2 Manager](https://img.shields.io/badge/Hysteria2-Manager%20v2.0-00a6fb?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZD0iTTEyIDJMMiA3djEwYzAgNS41NSAzLjg0IDEwLjc0IDkgMTIgNS4xNi0xLjI2IDktNi40NSA5LTEyVjdMMTIgMnoiIGZpbGw9IiMwMGE2ZmIiLz48L3N2Zz4=)
![Version](https://img.shields.io/badge/version-2.0.0-00d68f?style=for-the-badge)
![License](https://img.shields.io/badge/license-MIT-ffaa00?style=for-the-badge)
![Platform](https://img.shields.io/badge/platform-Linux-0095ff?style=for-the-badge)

**🚀 Advanced Proxy Management System with Web Authentication**

[**English**](#) | [**简体中文**](#) | [**Installation**](#-quick-installation) | [**Documentation**](#-usage-guide) | [**API**](#-api-documentation)

</div>

---

## 📋 Table of Contents

- [Introduction](#-introduction)
- [Features](#-features)
- [System Requirements](#-system-requirements)
- [Quick Installation](#-quick-installation)
- [Usage Guide](#-usage-guide)
- [Configuration](#-configuration)
- [Command Reference](#-command-reference)
- [API Documentation](#-api-documentation)
- [Troubleshooting](#-troubleshooting)
- [FAQ](#-faq)
- [Changelog](#-changelog)
- [Contributing](#-contributing)
- [License](#-license)

## 🌟 Introduction

Hysteria2 Manager v2.0 is a comprehensive web-based management system for Hysteria2 proxy service. It provides an intuitive, secure, and feature-rich interface for managing your proxy nodes, monitoring system resources, and controlling services.

### Why Hysteria2 Manager?

- **🔐 Secure Authentication** - Protected web interface with user authentication
- **🎨 Modern UI** - Sleek, tech-style interface with dark theme
- **⚡ One-Click Deployment** - Automated installation and configuration
- **📊 Real-time Monitoring** - Live traffic and system resource statistics
- **🌍 Multi-node Support** - Easy switching between multiple proxy servers
- **🛡️ System Optimization** - Automatic kernel parameter tuning

## ✨ Features

### Core Features

- ✅ **Web Authentication System** - Secure login with session management
- ✅ **Node Management** - Add, edit, delete, and switch nodes
- ✅ **Service Control** - Start/stop/restart proxy service
- ✅ **Real-time Statistics** - Traffic, CPU, memory monitoring
- ✅ **Log Viewer** - Real-time log streaming
- ✅ **System Settings** - Comprehensive configuration options
- ✅ **URL Parsing** - Support for hy2://, hysteria2://, hysteria:// formats
- ✅ **Password Management** - Secure password change functionality

### Technical Features

- 🔧 **RESTful API** - Complete API for automation
- 🐍 **Python Backend** - Based on Flask framework
- 📦 **Single-file Frontend** - All UI code in one HTML file
- 🔄 **Auto Updates** - Check and install updates
- 📱 **Responsive Design** - Mobile-friendly interface
- 🌐 **Multi-language Support** - Chinese/English (planned)

### Security Features

- 🔒 **Encrypted Storage** - Secure credential storage
- 🚫 **Login Throttling** - Protection against brute force
- ⏱️ **Session Timeout** - Automatic logout for security
- 📝 **Audit Logging** - Track all operations

## 💻 System Requirements

### Minimum Requirements

| Component | Requirement |
|-----------|-------------|
| **OS** | Linux (Ubuntu 18.04+, Debian 9+, CentOS 7+) |
| **Architecture** | x86_64, arm64, armv7 |
| **RAM** | 512MB |
| **Storage** | 100MB available |
| **Python** | 3.6+ |
| **Network** | Internet connection |
| **Privileges** | Root access |

### Recommended Configuration

| Component | Recommendation |
|-----------|---------------|
| **OS** | Ubuntu 22.04 LTS |
| **RAM** | 1GB+ |
| **Storage** | 500MB+ |
| **CPU** | 2+ cores |
| **Network** | Stable broadband |

## 🚀 Quick Installation

### One-Command Installation

```bash
# Using wget
wget -O install.sh https://raw.githubusercontent.com/yourusername/hysteria2-manager/main/install.sh && sudo bash install.sh

# Using curl
curl -fsSL https://raw.githubusercontent.com/yourusername/hysteria2-manager/main/install.sh | sudo bash
```

### Installation Process

The installer will automatically:
1. ✅ Detect system environment
2. ✅ Install dependencies
3. ✅ Download Hysteria2 core
4. ✅ Configure system services
5. ✅ Optimize kernel parameters
6. ✅ Start web interface

### Post-Installation

After installation, you'll see:
```
══════════════════════════════════════════════════
     Hysteria2 Manager Installation Successful!
══════════════════════════════════════════════════
Access Information:
  Local: http://127.0.0.1:8080
  Remote: http://YOUR_SERVER_IP:8080

Login Credentials:
  Username: admin
  Password: admin
  ⚠️ Please change the default password immediately!
══════════════════════════════════════════════════
```

## 📖 Usage Guide

### 1. First Login

1. Open your browser and navigate to `http://YOUR_SERVER_IP:8080`
2. Login with default credentials:
   - **Username:** `admin`
   - **Password:** `admin`
3. **Important:** Change your password immediately after first login

### 2. Adding Nodes

#### Method 1: Import from URL

1. Navigate to **Node Management**
2. Click **Add Node**
3. Select **Link Import** tab
4. Paste your node URL:
   ```
   hy2://password@server.com:443/?sni=server.com
   hysteria2://password@server.com:443/?sni=server.com
   ```
5. Click **Add Node**

#### Method 2: Manual Configuration

1. Navigate to **Node Management**
2. Click **Add Node**
3. Select **Manual Config** tab
4. Fill in the details:
   - **Name:** Custom name for the node
   - **Server:** Server address (IP or domain)
   - **Port:** Server port (default: 443)
   - **Password:** Authentication password
   - **SNI:** Server Name Indication (optional)
5. Click **Add Node**

### 3. Connecting to Proxy

1. Select a node from the list
2. Click **Use** button
3. Go to **Dashboard**
4. Click **Start Service**
5. Wait for connection status to show **Connected**

### 4. Monitoring Status

The dashboard displays:
- **Service Status** - Running/Stopped
- **Current Node** - Active node name
- **Upload Speed** - Real-time upload traffic
- **Download Speed** - Real-time download traffic
- **Connection Info** - IP, location, latency
- **System Resources** - CPU, memory usage

### 5. Managing Password

1. Go to **System Settings**
2. Under **Account Settings**:
   - Enter current password
   - Enter new password
   - Confirm new password
3. Click **Change Password**

## ⚙️ Configuration

### Configuration Files

```
/opt/hysteria2-manager/
├── data/
│   ├── config.json        # System configuration
│   ├── nodes.json         # Node data
│   └── users.json         # User data
├── static/
│   └── dashboard.html     # Web interface
└── hysteria2_manager.py   # Core program

/etc/hysteria2/
└── client.yaml            # Hysteria2 client config

/var/log/hysteria2/
├── manager.log            # Manager logs
└── hysteria.log           # Hysteria2 logs
```

### System Configuration (config.json)

```json
{
  "version": "2.0.0",
  "web_port": 8080,
  "web_host": "0.0.0.0",
  "language": "zh-CN",
  "theme": "dark",
  "auth": {
    "enabled": true,
    "session_timeout": 3600
  },
  "hysteria": {
    "bin_path": "/usr/local/bin/hysteria",
    "config_path": "/etc/hysteria2/client.yaml",
    "log_level": "info"
  },
  "system": {
    "auto_start": true,
    "auto_optimize": true,
    "check_update": true,
    "log_retention_days": 7
  },
  "security": {
    "max_login_attempts": 5,
    "lockout_duration": 300,
    "require_https": false
  }
}
```

### Node URL Format

Supported formats:
```
# Basic format
hy2://password@server:port

# With parameters
hy2://password@server:port/?sni=domain.com&insecure=1

# Full format
hysteria2://password@server:port/?sni=domain.com&obfs=salamander&obfs-password=pass

# With custom name
hy2://password@server:port/#NodeName
```

### Environment Variables

Override default settings:
```bash
export HY2_MANAGER_PORT=8888          # Web port
export HY2_MANAGER_HOST=127.0.0.1     # Listen address
export HY2_MANAGER_DEBUG=true         # Debug mode
```

## 🔧 Command Reference

### CLI Tool (hy2)

After installation, use the `hy2` command for quick management:

```bash
# Service Management
hy2 status              # Show service status
hy2 start               # Start proxy service
hy2 stop                # Stop proxy service
hy2 restart             # Restart proxy service

# Information Display
hy2 test                # Test proxy connection
hy2 web                 # Show WebUI address

# Logs
hy2 logs                # View client logs
hy2 manager-logs        # View manager logs

# Updates
hy2 update              # Check for updates
```

### Service Management (systemctl)

```bash
# Manager Service
sudo systemctl status hysteria2-manager    # Check status
sudo systemctl start hysteria2-manager     # Start service
sudo systemctl stop hysteria2-manager      # Stop service
sudo systemctl restart hysteria2-manager   # Restart service
sudo systemctl enable hysteria2-manager    # Enable auto-start

# Client Service
sudo systemctl status hysteria2-client     # Check status
sudo systemctl start hysteria2-client      # Start client
sudo systemctl stop hysteria2-client       # Stop client
sudo systemctl restart hysteria2-client    # Restart client
sudo systemctl enable hysteria2-client     # Enable auto-start

# View Logs
sudo journalctl -u hysteria2-manager -f    # Manager logs
sudo journalctl -u hysteria2-client -f     # Client logs
```

### Installation Management

```bash
# Update
bash install.sh update

# Uninstall
bash install.sh uninstall

# Force Reinstall
bash install.sh force
```

## 📡 API Documentation

### Authentication Endpoints

#### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin"
}

Response:
{
  "success": true,
  "message": "Login successful",
  "data": {
    "username": "admin",
    "role": "admin",
    "session_id": "...",
    "expires_in": 3600
  }
}
```

#### Logout
```http
POST /api/auth/logout

Response:
{
  "success": true,
  "message": "Logout successful"
}
```

#### Change Password
```http
POST /api/auth/change_password
Content-Type: application/json

{
  "old_password": "current_password",
  "new_password": "new_password"
}
```

### Service Management

#### Get Status
```http
GET /api/status

Response:
{
  "success": true,
  "data": {
    "service": {
      "hysteria": "running",
      "manager": "running",
      "tun_interface": true
    },
    "connection": {
      "status": "connected",
      "ip": "x.x.x.x",
      "location": "US",
      "latency": 50,
      "dns": true,
      "http": true
    },
    "stats": {
      "traffic": {
        "up": 1024,
        "down": 2048
      }
    }
  }
}
```

#### Service Control
```http
POST /api/service/start    # Start service
POST /api/service/stop     # Stop service
POST /api/service/restart  # Restart service
```

### Node Management

#### Get Nodes
```http
GET /api/nodes

Response:
{
  "success": true,
  "data": {
    "nodes": [...],
    "current": "node_id"
  }
}
```

#### Add Node
```http
POST /api/nodes
Content-Type: application/json

# Method 1: URL Import
{
  "url": "hy2://password@server:port/?sni=domain",
  "name": "Custom Name"
}

# Method 2: Manual
{
  "name": "Node Name",
  "server": "server.com",
  "port": 443,
  "password": "password",
  "sni": "server.com"
}
```

#### Use Node
```http
POST /api/nodes/:id/use
```

#### Delete Node
```http
DELETE /api/nodes/:id
```

### System Operations

#### Get Logs
```http
GET /api/logs?lines=100&type=all
```

#### Get System Stats
```http
GET /api/system/stats
```

#### Test Connection
```http
GET /api/test
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Cannot Access WebUI

**Problem:** Unable to connect to http://SERVER_IP:8080

**Solutions:**
```bash
# Check service status
sudo systemctl status hysteria2-manager

# Check if port is listening
netstat -tuln | grep 8080

# Check firewall
sudo ufw status
sudo ufw allow 8080/tcp  # If using ufw

# For firewalld
sudo firewall-cmd --add-port=8080/tcp --permanent
sudo firewall-cmd --reload
```

#### 2. Login Failed

**Problem:** Cannot login with default credentials

**Solutions:**
```bash
# Reset to default password
sudo python3 << EOF
import json
from werkzeug.security import generate_password_hash

users_file = '/opt/hysteria2-manager/data/users.json'
with open(users_file, 'r') as f:
    users = json.load(f)

users['users'][0]['password'] = generate_password_hash('admin')
users['users'][0]['failed_attempts'] = 0
users['users'][0]['locked_until'] = None

with open(users_file, 'w') as f:
    json.dump(users, f, indent=2)

print("Password reset to: admin")
EOF

# Restart service
sudo systemctl restart hysteria2-manager
```

#### 3. Proxy Not Working

**Problem:** Connected but no internet access

**Solutions:**
```bash
# Check Hysteria2 client status
sudo systemctl status hysteria2-client

# Check TUN interface
ip link show hytun

# Check routing
ip route | grep hytun

# View detailed logs
sudo journalctl -u hysteria2-client -n 100

# Test with manual config
sudo /usr/local/bin/hysteria client -c /etc/hysteria2/client.yaml
```

#### 4. High CPU/Memory Usage

**Solutions:**
```bash
# Check process usage
htop

# Clear logs
sudo truncate -s 0 /var/log/hysteria2/*.log

# Restart services
sudo systemctl restart hysteria2-manager
sudo systemctl restart hysteria2-client

# Check for memory leaks
ps aux | grep hysteria
```

### Diagnostic Commands

```bash
# Complete system check
cat > /tmp/diagnose.sh << 'EOF'
#!/bin/bash
echo "=== System Diagnosis ==="
echo "1. Service Status:"
systemctl status hysteria2-manager --no-pager | head -10
systemctl status hysteria2-client --no-pager | head -10

echo -e "\n2. Port Status:"
netstat -tuln | grep -E ":(8080|443)"

echo -e "\n3. TUN Interface:"
ip link show hytun 2>/dev/null || echo "TUN interface not found"

echo -e "\n4. Current IP:"
curl -s https://ifconfig.io || echo "Cannot fetch IP"

echo -e "\n5. DNS Test:"
nslookup google.com 8.8.8.8 | head -5

echo -e "\n6. Resource Usage:"
free -h
df -h /

echo -e "\n7. Recent Errors:"
journalctl -p err --since "1 hour ago" | tail -20
EOF

bash /tmp/diagnose.sh
```

## ❓ FAQ

### Q1: How to change the web port?

**A:** Edit the configuration file:
```bash
# Edit config
sudo nano /opt/hysteria2-manager/data/config.json
# Change "web_port": 8080 to your desired port

# Restart service
sudo systemctl restart hysteria2-manager
```

### Q2: How to enable HTTPS?

**A:** Use a reverse proxy like Nginx:
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Q3: How to backup configuration?

**A:** Backup all configuration files:
```bash
# Create backup
tar -czf hysteria2-backup-$(date +%Y%m%d).tar.gz \
    /opt/hysteria2-manager/data/ \
    /etc/hysteria2/

# Restore backup
tar -xzf hysteria2-backup-20240120.tar.gz -C /
```

### Q4: How to migrate to another server?

**A:** Follow these steps:
```bash
# On old server - Export
tar -czf hysteria2-migrate.tar.gz \
    /opt/hysteria2-manager/ \
    /etc/hysteria2/

# On new server - Import
scp user@old-server:~/hysteria2-migrate.tar.gz .
tar -xzf hysteria2-migrate.tar.gz -C /
bash install.sh  # Run installer to set up services
```

### Q5: How to use multiple users?

**A:** Currently supports single admin user. Multi-user support is planned for future releases.

## 📝 Changelog

### v2.0.0 (2024-01-20)
- 🔐 **New:** Complete authentication system
- 🎨 **New:** Modern tech-style UI with dark theme
- 🔧 **New:** RESTful API with session management
- ✅ **Fixed:** All known v1.0 issues
- ✅ **Fixed:** URL parsing for all formats
- ✅ **Fixed:** Connection status detection
- ✅ **Fixed:** DNS test reliability
- ✅ **Fixed:** Log viewing functionality
- ✅ **Fixed:** System resource monitoring
- 📦 **Improved:** Installation process
- 📊 **Improved:** Real-time statistics
- 🛡️ **Improved:** Security features

### v1.0.0 (2024-01-15)
- 🎉 Initial release
- ✨ Basic functionality
- 🎨 Web UI interface
- 📦 One-click installation

### Roadmap

- [ ] v2.1.0 - Multi-user support
- [ ] v2.2.0 - Docker container support
- [ ] v2.3.0 - Subscription management
- [ ] v2.4.0 - Traffic statistics & limits
- [ ] v3.0.0 - Mobile app

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone repository
git clone https://github.com/yourusername/hysteria2-manager.git
cd hysteria2-manager

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run in debug mode
python hysteria2_manager.py --debug
```

### Submitting Issues

Please include:
- System information (OS, Python version)
- Error logs
- Steps to reproduce
- Expected vs actual behavior

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Hysteria2](https://github.com/apernet/hysteria) - The powerful proxy core
- [Flask](https://flask.palletsprojects.com/) - Python web framework
- [Vue.js](https://vuejs.org/) - Frontend framework
- [Chart.js](https://www.chartjs.org/) - Data visualization
- All contributors and users

## 📞 Contact

- **GitHub Issues:** [Report bugs](https://github.com/yourusername/hysteria2-manager/issues)
- **Discussions:** [Ask questions](https://github.com/yourusername/hysteria2-manager/discussions)
- **Email:** admin@example.com

---

<div align="center">

**If this project helps you, please give it a ⭐ Star!**

[![Star History](https://star-history.com/#yourusername/hysteria2-manager&Date)](https://star-history.com/#yourusername/hysteria2-manager)

[Back to Top](#hysteria2-manager-v20)

</div>
```

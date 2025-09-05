# Hysteria2 Manager v2.0

<div align="center">

![Hysteria2 Manager Logo](https://img.shields.io/badge/Hysteria2-Manager%20v2.0-blue?style=for-the-badge&logo=rocket)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.6%2B-yellow?style=for-the-badge&logo=python)
![Platform](https://img.shields.io/badge/Platform-Linux-orange?style=for-the-badge&logo=linux)
![Status](https://img.shields.io/badge/Status-Stable-success?style=for-the-badge)

**🚀 专业的 Hysteria2 代理管理系统 - 让代理管理变得简单高效**

[功能特性](#-功能特性) | [快速开始](#-快速开始) | [使用教程](#-使用教程) | [API文档](#-api文档) | [常见问题](#-常见问题)

</div>

---

## 📋 目录

- [项目介绍](#-项目介绍)
- [功能特性](#-功能特性)
- [系统要求](#-系统要求)
- [快速开始](#-快速开始)
- [使用教程](#-使用教程)
  - [登录系统](#1-登录系统)
  - [节点管理](#2-节点管理)
  - [服务控制](#3-服务控制)
  - [系统监控](#4-系统监控)
  - [日志查看](#5-日志查看)
  - [系统设置](#6-系统设置)
- [常用命令](#-常用命令)
- [配置说明](#-配置说明)
- [API文档](#-api文档)
- [故障排查](#-故障排查)
- [高级功能](#-高级功能)
- [性能优化](#-性能优化)
- [安全建议](#-安全建议)
- [更新日志](#-更新日志)
- [贡献指南](#-贡献指南)
- [许可证](#-许可证)

## 🌟 项目介绍

Hysteria2 Manager 是一个基于 Web 的 Hysteria2 代理管理系统，提供直观的图形界面来管理您的代理节点。通过现代化的技术栈和精心设计的用户界面，让复杂的代理配置变得简单易用。

### 为什么选择 Hysteria2 Manager？

- **🎯 零门槛** - 无需了解复杂的命令行操作
- **⚡ 高性能** - 基于 Hysteria2 协议，速度快、延迟低
- **🔒 安全可靠** - JWT认证、密码加密、会话管理
- **🎨 现代界面** - 科技风设计、响应式布局、深色模式
- **📊 实时监控** - 流量统计、系统资源、连接状态
- **🌍 多节点** - 轻松管理和切换多个服务器节点

### 技术栈

- **后端**: Python 3.6+, Flask, JWT
- **前端**: Vue.js 3, Axios, Chart.js
- **协议**: Hysteria2 v2.6.2+
- **系统**: Linux (Ubuntu/Debian/CentOS)

## ✨ 功能特性

### 核心功能
| 功能 | 描述 | 状态 |
|------|------|------|
| 🔐 **用户认证** | JWT Token认证系统，支持会话管理 | ✅ |
| 🌐 **节点管理** | 添加、编辑、删除、切换节点 | ✅ |
| 🚀 **服务控制** | 一键启动/停止/重启服务 | ✅ |
| 📊 **流量监控** | 实时上传/下载速度统计 | ✅ |
| 📝 **日志查看** | 分类查看系统和服务日志 | ✅ |
| 📦 **订阅导入** | 批量导入节点订阅链接 | ✅ |
| ⚙️ **系统优化** | 一键优化系统网络参数 | ✅ |
| 💾 **配置备份** | 导入/导出配置文件 | ✅ |
| 🎨 **主题切换** | 深色/浅色主题自由切换 | ✅ |
| 📱 **响应式设计** | 完美适配移动设备 | ✅ |

### 节点协议支持
- ✅ `hy2://` 格式
- ✅ `hysteria2://` 格式  
- ✅ `hysteria://` 格式
- ✅ URL编码支持
- ✅ 自定义参数支持

### 安全特性
- 🔒 密码使用 bcrypt 加密存储
- 🔑 JWT Token 认证机制
- ⏱️ 会话超时自动登出
- 🛡️ 输入验证和参数校验
- 🚫 SQL注入和XSS防护

## 💻 系统要求

### 最低配置
| 组件 | 要求 |
|------|------|
| **操作系统** | Linux (64位) |
| **CPU** | 1核心 |
| **内存** | 512MB |
| **存储** | 100MB |
| **Python** | 3.6+ |
| **网络** | 支持TUN/TAP |

### 推荐配置
| 组件 | 要求 |
|------|------|
| **操作系统** | Ubuntu 22.04 LTS |
| **CPU** | 2核心+ |
| **内存** | 1GB+ |
| **存储** | 500MB+ |
| **带宽** | 10Mbps+ |

### 支持的系统
- ✅ Ubuntu 18.04/20.04/22.04
- ✅ Debian 10/11/12
- ✅ CentOS 7/8/9
- ✅ RHEL 7/8/9
- ✅ Fedora 35+
- ✅ Arch Linux

### 支持的架构
- ✅ x86_64 (amd64)
- ✅ ARM64 (aarch64)
- ✅ ARMv7 (arm)

## 🚀 快速开始

### 一键安装

```bash
# 下载安装脚本
wget -O install.sh https://raw.githubusercontent.com/1439616687/hysteria2-manager/main/install.sh

# 赋予执行权限
chmod +x install.sh

# 执行安装
sudo bash install.sh
```

### 手动安装

```bash
# 1. 克隆仓库
git clone https://github.com/1439616687/hysteria2-manager.git
cd hysteria2-manager

# 2. 执行安装
sudo bash install.sh

# 3. 启动服务
sudo systemctl start hysteria2-manager
```

### Docker部署（开发中）

```bash
# 拉取镜像
docker pull 1439616687/hysteria2-manager:latest

# 运行容器
docker run -d \
  --name hysteria2-manager \
  --restart unless-stopped \
  --network host \
  --cap-add NET_ADMIN \
  -v /opt/hysteria2-data:/data \
  1439616687/hysteria2-manager:latest
```

### 安装验证

安装完成后，通过以下命令验证：

```bash
# 检查服务状态
systemctl status hysteria2-manager

# 检查端口监听
netstat -tuln | grep 8080

# 查看运行日志
journalctl -u hysteria2-manager -f
```

## 📖 使用教程

### 1. 登录系统

安装完成后，打开浏览器访问：

- **本地访问**: http://127.0.0.1:8080
- **远程访问**: http://服务器IP:8080

**默认账号密码**：
- 用户名：`admin`
- 密码：`admin`

> ⚠️ **重要**：首次登录后请立即修改密码！

### 2. 节点管理

#### 2.1 添加节点（方式一：链接导入）

1. 点击 **节点管理** → **添加节点**
2. 选择 **链接导入** 标签
3. 粘贴节点链接，支持格式：
   ```
   hy2://password@server.com:443/?sni=server.com
   hysteria2://password@server.com:443/?sni=server.com&insecure=0
   ```
4. 设置自定义名称（可选）
5. 点击 **添加节点**

#### 2.2 添加节点（方式二：手动配置）

1. 点击 **节点管理** → **添加节点**
2. 选择 **手动配置** 标签
3. 填写节点信息：
   - **节点名称**: 自定义名称
   - **服务器地址**: 域名或IP
   - **端口**: 默认443
   - **密码**: 认证密码
   - **SNI**: 服务器名称指示（可选）
   - **跳过证书验证**: 测试使用（不推荐）
4. 点击 **添加节点**

#### 2.3 导入订阅

1. 点击 **节点管理** → **导入订阅**
2. 输入订阅地址
3. 设置订阅名称（可选）
4. 点击 **导入**

#### 2.4 管理节点

- **使用节点**: 点击节点右侧的 ✓ 按钮
- **编辑节点**: 点击编辑图标修改节点信息
- **删除节点**: 点击垃圾桶图标删除节点

### 3. 服务控制

在 **仪表板** 页面，使用快速操作按钮：

- **启动服务**: 开始代理连接
- **停止服务**: 断开代理连接
- **重启服务**: 重新连接代理
- **测试连接**: 检测连接状态

### 4. 系统监控

#### 4.1 实时状态

仪表板显示以下实时信息：

- **服务状态**: 运行中/已停止
- **当前节点**: 正在使用的节点
- **上传速度**: 实时上传流量
- **下载速度**: 实时下载流量

#### 4.2 连接信息

- **出口IP**: 代理服务器IP
- **IP归属地**: 地理位置
- **连接延迟**: ping值
- **DNS状态**: 解析状态
- **HTTP状态**: 连接状态

#### 4.3 系统资源

实时图表显示：
- CPU使用率
- 内存使用率
- 网络流量

### 5. 日志查看

在 **日志查看** 页面：

- **Hysteria日志**: 查看代理服务日志
- **管理器日志**: 查看系统管理日志
- **刷新日志**: 获取最新日志内容

日志级别说明：
- 🔴 ERROR - 错误信息
- 🟡 WARNING - 警告信息
- 🔵 INFO - 普通信息
- ⚪ DEBUG - 调试信息

### 6. 系统设置

#### 6.1 基本设置

- **Web端口**: 管理界面端口（默认8080）
- **日志级别**: debug/info/warn/error
- **开机自启动**: 系统启动时自动运行
- **自动优化**: 自动优化系统参数

#### 6.2 系统优化

点击 **应用优化** 自动配置：
- TCP BBR加速
- 网络缓冲区优化
- 文件描述符限制
- IP转发启用

#### 6.3 配置备份

- **导出配置**: 下载当前配置文件
- **导入配置**: 恢复备份的配置

#### 6.4 修改密码

1. 点击右上角用户菜单
2. 选择 **修改密码**
3. 输入原密码和新密码
4. 点击确认

## 🔧 常用命令

### 服务管理命令

```bash
# 查看服务状态
sudo systemctl status hysteria2-manager

# 启动服务
sudo systemctl start hysteria2-manager

# 停止服务
sudo systemctl stop hysteria2-manager

# 重启服务
sudo systemctl restart hysteria2-manager

# 开机自启
sudo systemctl enable hysteria2-manager

# 取消自启
sudo systemctl disable hysteria2-manager
```

### 日志查看命令

```bash
# 查看管理器日志
sudo journalctl -u hysteria2-manager -f

# 查看最近50条日志
sudo journalctl -u hysteria2-manager -n 50

# 查看指定时间日志
sudo journalctl -u hysteria2-manager --since "2024-01-01 00:00:00"

# 查看Hysteria2客户端日志
sudo journalctl -u hysteria2-client -f

# 查看错误日志
sudo journalctl -u hysteria2-manager -p err
```

### 进程管理命令

```bash
# 查看进程
ps aux | grep hysteria

# 查看端口占用
netstat -tuln | grep 8080
lsof -i:8080

# 查看系统资源
htop
top

# 查看网络连接
ss -tuln
netstat -an
```

### 更新和卸载命令

```bash
# 更新到最新版本
sudo bash install.sh update

# 完全卸载
sudo bash install.sh uninstall

# 手动更新
cd /opt/hysteria2-manager
git pull
sudo systemctl restart hysteria2-manager
```

### 配置文件操作

```bash
# 编辑主配置
sudo nano /opt/hysteria2-manager/data/config.json

# 编辑节点配置
sudo nano /opt/hysteria2-manager/data/nodes.json

# 查看Hysteria2配置
sudo cat /etc/hysteria2/client.yaml

# 备份配置
sudo cp -r /opt/hysteria2-manager/data /opt/backup/

# 恢复配置
sudo cp -r /opt/backup/data /opt/hysteria2-manager/
```

### 网络诊断命令

```bash
# 测试节点连接
curl -x socks5://127.0.0.1:1080 https://www.google.com

# 查看路由表
ip route show

# 查看TUN接口
ip link show hytun

# DNS测试
nslookup google.com
dig google.com

# 测速
speedtest-cli

# 查看防火墙规则
sudo iptables -L
sudo ufw status
```

## ⚙️ 配置说明

### 目录结构

```
/opt/hysteria2-manager/
├── hysteria2_manager.py    # 主程序
├── venv/                    # Python虚拟环境
├── static/
│   └── webui.html          # Web界面
├── data/
│   ├── config.json         # 系统配置
│   ├── users.json          # 用户数据
│   ├── nodes.json          # 节点配置
│   └── stats.json          # 统计数据
└── logs/                    # 日志文件

/etc/hysteria2/
└── client.yaml             # Hysteria2配置

/var/log/hysteria2/
├── manager.log             # 管理器日志
└── hysteria.log           # 客户端日志
```

### 主配置文件 (config.json)

```json
{
  "version": "2.0.0",
  "web_port": 8080,              // Web界面端口
  "web_host": "0.0.0.0",          // 监听地址
  "language": "zh-CN",            // 界面语言
  "theme": "dark",                // 主题: dark/light
  "auth": {
    "enabled": true,              // 启用认证
    "session_timeout": 1800       // 会话超时(秒)
  },
  "hysteria": {
    "bin_path": "/usr/local/bin/hysteria",
    "config_path": "/etc/hysteria2/client.yaml",
    "log_level": "info"           // 日志级别
  },
  "system": {
    "auto_start": true,           // 开机自启
    "auto_optimize": true,        // 自动优化
    "check_update": true          // 检查更新
  }
}
```

### 节点配置格式 (nodes.json)

```json
{
  "nodes": [
    {
      "id": "abc123",
      "name": "香港节点",
      "server": "hk.example.com",
      "port": 443,
      "password": "your_password",
      "sni": "hk.example.com",
      "insecure": false,
      "created_at": "2024-01-01T00:00:00"
    }
  ],
  "current": "abc123",
  "subscriptions": []
}
```

### 环境变量

可通过环境变量覆盖默认配置：

```bash
# 设置Web端口
export HY2_MANAGER_PORT=8888

# 设置监听地址
export HY2_MANAGER_HOST=127.0.0.1

# 启用调试模式
export HY2_MANAGER_DEBUG=true

# 设置JWT密钥
export JWT_SECRET=your-secret-key

# 设置Flask密钥
export FLASK_SECRET=your-flask-secret
```

## 🔌 API文档

### 认证相关

#### 登录
```http
POST /api/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin"
}

Response:
{
  "success": true,
  "data": {
    "token": "JWT_TOKEN",
    "username": "admin"
  }
}
```

#### 修改密码
```http
POST /api/change_password
Authorization: Bearer JWT_TOKEN
Content-Type: application/json

{
  "old_password": "admin",
  "new_password": "new_password"
}
```

### 节点管理

#### 获取节点列表
```http
GET /api/nodes
Authorization: Bearer JWT_TOKEN

Response:
{
  "success": true,
  "data": {
    "nodes": [...],
    "current": "node_id"
  }
}
```

#### 添加节点
```http
POST /api/nodes
Authorization: Bearer JWT_TOKEN
Content-Type: application/json

{
  "url": "hy2://...",  // 或
  "name": "节点名称",
  "server": "server.com",
  "port": 443,
  "password": "password"
}
```

#### 使用节点
```http
POST /api/nodes/:id/use
Authorization: Bearer JWT_TOKEN
```

#### 删除节点
```http
DELETE /api/nodes/:id
Authorization: Bearer JWT_TOKEN
```

### 服务控制

#### 启动服务
```http
POST /api/service/start
Authorization: Bearer JWT_TOKEN
```

#### 停止服务
```http
POST /api/service/stop
Authorization: Bearer JWT_TOKEN
```

#### 重启服务
```http
POST /api/service/restart
Authorization: Bearer JWT_TOKEN
```

### 系统信息

#### 获取状态
```http
GET /api/status
Authorization: Bearer JWT_TOKEN
```

#### 获取日志
```http
GET /api/logs?lines=100
Authorization: Bearer JWT_TOKEN
```

#### 系统统计
```http
GET /api/system/stats
Authorization: Bearer JWT_TOKEN
```

## 🔨 故障排查

### 常见问题

#### 1. 无法访问Web界面

**可能原因**：
- 防火墙阻止端口
- 服务未启动
- 端口被占用

**解决方案**：
```bash
# 检查服务状态
sudo systemctl status hysteria2-manager

# 检查端口
netstat -tuln | grep 8080

# 开放防火墙端口
sudo ufw allow 8080/tcp           # Ubuntu
sudo firewall-cmd --add-port=8080/tcp --permanent  # CentOS
sudo firewall-cmd --reload

# 更换端口
sudo nano /opt/hysteria2-manager/data/config.json
# 修改 web_port 值
sudo systemctl restart hysteria2-manager
```

#### 2. 登录失败

**可能原因**：
- 密码错误
- Token过期
- 服务异常

**解决方案**：
```bash
# 重置密码
sudo python3 << EOF
import json
import bcrypt
with open('/opt/hysteria2-manager/data/users.json', 'r') as f:
    users = json.load(f)
users[0]['password'] = bcrypt.hashpw(b'admin', bcrypt.gensalt()).decode()
with open('/opt/hysteria2-manager/data/users.json', 'w') as f:
    json.dump(users, f)
EOF

# 重启服务
sudo systemctl restart hysteria2-manager
```

#### 3. 节点连接失败

**可能原因**：
- 节点配置错误
- 网络问题
- TUN设备问题

**解决方案**：
```bash
# 检查TUN设备
lsmod | grep tun
sudo modprobe tun

# 检查配置文件
sudo cat /etc/hysteria2/client.yaml

# 手动测试节点
sudo /usr/local/bin/hysteria client -c /etc/hysteria2/client.yaml

# 查看详细日志
sudo journalctl -u hysteria2-client -n 100
```

#### 4. 服务启动失败

**可能原因**：
- Python依赖缺失
- 配置文件损坏
- 权限问题

**解决方案**：
```bash
# 检查Python环境
/opt/hysteria2-manager/venv/bin/python -c "import flask; print('OK')"

# 重装依赖
cd /opt/hysteria2-manager
source venv/bin/activate
pip install -r requirements.txt
deactivate

# 检查权限
sudo chown -R root:root /opt/hysteria2-manager
sudo chmod -R 755 /opt/hysteria2-manager

# 验证配置
python3 -m json.tool < /opt/hysteria2-manager/data/config.json
```

### 错误代码说明

| 错误代码 | 说明 | 解决方法 |
|---------|------|----------|
| 401 | 未认证或Token过期 | 重新登录 |
| 403 | 权限不足 | 检查用户权限 |
| 404 | 资源不存在 | 检查请求路径 |
| 500 | 服务器错误 | 查看服务日志 |
| 502 | 网关错误 | 重启服务 |

### 日志分析

```bash
# 查找错误
sudo journalctl -u hysteria2-manager | grep ERROR

# 按时间查看
sudo journalctl -u hysteria2-manager --since today

# 导出日志
sudo journalctl -u hysteria2-manager > manager.log

# 实时监控
sudo tail -f /var/log/hysteria2/manager.log
```

## 🚀 高级功能

### 自定义TLS配置

编辑节点时可设置：
- **SNI**: 服务器名称指示
- **ALPN**: 应用层协议协商
- **指纹**: TLS指纹伪装

### 带宽限制

```yaml
bandwidth:
  up: 100 mbps    # 上传限制
  down: 100 mbps   # 下载限制
```

### 路由规则

编辑 `/etc/hysteria2/client.yaml`：

```yaml
tun:
  route:
    ipv4:
      - 0.0.0.0/0
    ipv4Exclude:
      - 192.168.0.0/16
      - 10.0.0.0/8
```

### 混淆配置

```yaml
obfs:
  type: salamander
  password: obfs_password
```

### 多用户支持（规划中）

未来版本将支持：
- 多用户账号
- 权限管理
- 流量配额
- 使用统计

## 📈 性能优化

### 系统优化建议

```bash
# 1. 启用BBR加速
echo "net.core.default_qdisc=fq" >> /etc/sysctl.conf
echo "net.ipv4.tcp_congestion_control=bbr" >> /etc/sysctl.conf
sysctl -p

# 2. 优化文件描述符
echo "* soft nofile 65535" >> /etc/security/limits.conf
echo "* hard nofile 65535" >> /etc/security/limits.conf

# 3. 优化网络缓冲区
echo "net.core.rmem_max = 134217728" >> /etc/sysctl.conf
echo "net.core.wmem_max = 134217728" >> /etc/sysctl.conf
sysctl -p
```

### 服务优化

```bash
# 使用生产服务器
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8080 hysteria2_manager:app

# 启用缓存
pip install Flask-Caching redis
```

### 监控建议

- 使用 Prometheus + Grafana 监控
- 集成 Sentry 错误追踪
- 配置日志轮转

## 🔒 安全建议

### 1. 修改默认设置

```bash
# 修改默认端口
nano /opt/hysteria2-manager/data/config.json

# 修改JWT密钥
export JWT_SECRET=$(openssl rand -base64 32)
```

### 2. 限制访问

```bash
# 只允许本地访问
"web_host": "127.0.0.1"

# 使用Nginx反代
location / {
    proxy_pass http://127.0.0.1:8080;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

### 3. 启用HTTPS

```nginx
server {
    listen 443 ssl;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:8080;
    }
}
```

### 4. 定期更新

```bash
# 检查更新
cd /opt/hysteria2-manager
git pull

# 更新依赖
pip install --upgrade -r requirements.txt
```

### 5. 备份策略

```bash
# 自动备份脚本
#!/bin/bash
backup_dir="/backup/hysteria2-manager"
mkdir -p $backup_dir
tar -czf $backup_dir/backup-$(date +%Y%m%d).tar.gz \
    /opt/hysteria2-manager/data
    
# 添加到crontab
0 3 * * * /path/to/backup.sh
```

## 📝 更新日志

### v2.0.0 (2024-01-20)
- ✨ 全新科技风UI设计
- 🔐 添加JWT认证系统
- 📊 实时系统资源监控
- 🌍 支持所有Hysteria2链接格式
- 🔧 修复所有已知问题
- ⚡ 性能大幅优化

### v1.0.0 (2024-01-01)
- 🎉 首次发布
- ✅ 基础功能实现
- 📱 响应式设计
- 🚀 一键安装脚本

### 开发计划

- [ ] Docker容器支持
- [ ] 多用户权限管理
- [ ] 流量统计和限制
- [ ] 自动故障转移
- [ ] WebSocket实时推送
- [ ] 移动端APP
- [ ] 规则路由配置
- [ ] 一键部署脚本优化

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

### 如何贡献

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/1439616687/hysteria2-manager.git
cd hysteria2-manager

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 运行开发服务器
python hysteria2_manager.py --debug
```

### 代码规范

- Python: PEP 8
- JavaScript: ESLint
- Git Commit: Conventional Commits

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

```
MIT License

Copyright (c) 2024 Hysteria2 Manager Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 🙏 鸣谢

- [Hysteria2](https://github.com/apernet/hysteria) - 强大的代理协议
- [Flask](https://flask.palletsprojects.com/) - Python Web框架
- [Vue.js](https://vuejs.org/) - 前端框架
- [Chart.js](https://www.chartjs.org/) - 图表库
- 所有贡献者和用户的支持

## 📞 联系支持

- **GitHub Issues**: [提交问题](https://github.com/1439616687/hysteria2-manager/issues)
- **Email**: support@example.com
- **Telegram**: [@hysteria2manager](https://t.me/hysteria2manager)
- **文档**: [在线文档](https://docs.example.com)

---

<div align="center">

**如果这个项目对您有帮助，请给一个 ⭐ Star！**

[![Star History Chart](https://api.star-history.com/svg?repos=1439616687/hysteria2-manager&type=Date)](https://star-history.com/#1439616687/hysteria2-manager)

Made with ❤️ by Hysteria2 Manager Team

</div>

# Hysteria2 Manager v2.0

<div align="center">

![Hysteria2 Manager](https://img.shields.io/badge/Hysteria2-Manager%20v2.0-00a6fb?style=for-the-badge)
![版本](https://img.shields.io/badge/版本-2.0.0-00d68f?style=for-the-badge)
![许可证](https://img.shields.io/badge/许可证-MIT-ffaa00?style=for-the-badge)
![平台](https://img.shields.io/badge/平台-Linux-0095ff?style=for-the-badge)

**🚀 先进的代理管理系统 - 带Web认证功能**

[**功能特性**](#核心功能) | [**快速安装**](#一键安装) | [**使用教程**](#使用教程) | [**API文档**](#api-文档) | [**常见问题**](#常见问题)

</div>

---

## 📋 目录

- [项目介绍](#项目介绍)
- [核心功能](#核心功能)
- [系统要求](#系统要求)
- [一键安装](#一键安装)
- [使用教程](#使用教程)
- [配置说明](#配置说明)
- [命令参考](#命令参考)
- [API文档](#api-文档)
- [故障排查](#故障排查)
- [常见问题](#常见问题)
- [更新日志](#更新日志)
- [开发说明](#开发说明)
- [许可证](#许可证)

## 🌟 项目介绍

Hysteria2 Manager v2.0 是一个功能完善的 Hysteria2 代理服务Web管理系统。它提供了直观、安全、功能丰富的界面来管理您的代理节点、监控系统资源和控制服务。

### 为什么选择 Hysteria2 Manager？

- **🔐 安全认证** - 带用户认证的Web界面保护
- **🎨 现代化UI** - 科技风格的深色主题界面
- **⚡ 一键部署** - 自动化安装和配置
- **📊 实时监控** - 实时流量和系统资源统计
- **🌍 多节点支持** - 轻松切换多个代理服务器
- **🛡️ 系统优化** - 自动内核参数调优

## ✨ 核心功能

### 主要功能

- ✅ **Web认证系统** - 安全登录和会话管理
- ✅ **节点管理** - 添加、编辑、删除和切换节点
- ✅ **服务控制** - 启动/停止/重启代理服务
- ✅ **实时统计** - 流量、CPU、内存监控
- ✅ **日志查看器** - 实时日志流显示
- ✅ **系统设置** - 全面的配置选项
- ✅ **URL解析** - 支持 hy2://、hysteria2://、hysteria:// 格式
- ✅ **密码管理** - 安全的密码修改功能

### 技术特性

- 🔧 **RESTful API** - 完整的API用于自动化
- 🐍 **Python后端** - 基于Flask框架
- 📦 **单文件前端** - 所有UI代码在一个HTML文件中
- 🔄 **自动更新** - 检查并安装更新
- 📱 **响应式设计** - 移动端友好界面
- 🌐 **国际化支持** - 中文/英文（计划中）

### 安全特性

- 🔒 **加密存储** - 安全的凭证存储
- 🚫 **登录限制** - 防止暴力破解
- ⏱️ **会话超时** - 自动登出保护
- 📝 **审计日志** - 跟踪所有操作

## 💻 系统要求

### 最低要求

| 组件 | 要求 |
|------|------|
| **操作系统** | Linux (Ubuntu 18.04+, Debian 9+, CentOS 7+) |
| **架构** | x86_64, arm64, armv7 |
| **内存** | 512MB |
| **存储** | 100MB 可用空间 |
| **Python** | 3.6+ |
| **网络** | 互联网连接 |
| **权限** | Root 权限 |

### 推荐配置

| 组件 | 推荐 |
|------|------|
| **操作系统** | Ubuntu 22.04 LTS |
| **内存** | 1GB+ |
| **存储** | 500MB+ |
| **CPU** | 2+ 核心 |
| **网络** | 稳定的宽带连接 |

## 🚀 一键安装

### 快速安装命令

```bash
# 使用 wget
wget -O install.sh https://raw.githubusercontent.com/yourusername/hysteria2-manager/main/install.sh && sudo bash install.sh

# 使用 curl
curl -fsSL https://raw.githubusercontent.com/yourusername/hysteria2-manager/main/install.sh | sudo bash

# 国内用户使用镜像
wget -O install.sh https://ghproxy.com/https://raw.githubusercontent.com/yourusername/hysteria2-manager/main/install.sh && sudo bash install.sh
```

### 安装过程

安装程序将自动：
1. ✅ 检测系统环境
2. ✅ 安装依赖包
3. ✅ 下载 Hysteria2 核心
4. ✅ 配置系统服务
5. ✅ 优化内核参数
6. ✅ 启动Web界面

### 安装完成后

安装成功后，您将看到：
```
══════════════════════════════════════════════════
     Hysteria2 Manager 安装成功！
══════════════════════════════════════════════════
访问信息:
  本地访问: http://127.0.0.1:8080
  远程访问: http://您的服务器IP:8080

登录信息:
  用户名: admin
  密码: admin
  ⚠️ 请立即登录并修改默认密码！
══════════════════════════════════════════════════
```

## 📖 使用教程

### 1. 首次登录

1. 打开浏览器访问 `http://您的服务器IP:8080`
2. 使用默认凭证登录：
   - **用户名：** `admin`
   - **密码：** `admin`
3. **重要：** 首次登录后立即修改密码

### 2. 添加节点

#### 方法一：URL导入

1. 进入 **节点管理**
2. 点击 **添加节点**
3. 选择 **链接导入** 标签
4. 粘贴您的节点URL：
   ```
   hy2://密码@服务器.com:443/?sni=服务器.com
   hysteria2://密码@服务器.com:443/?sni=服务器.com
   ```
5. 点击 **添加节点**

#### 方法二：手动配置

1. 进入 **节点管理**
2. 点击 **添加节点**
3. 选择 **手动配置** 标签
4. 填写详细信息：
   - **名称：** 节点自定义名称
   - **服务器：** 服务器地址（IP或域名）
   - **端口：** 服务器端口（默认443）
   - **密码：** 认证密码
   - **SNI：** 服务器名称指示（可选）
5. 点击 **添加节点**

### 3. 连接代理

1. 从列表中选择一个节点
2. 点击 **使用** 按钮
3. 进入 **仪表板**
4. 点击 **启动服务**
5. 等待连接状态显示 **已连接**

### 4. 监控状态

仪表板显示：
- **服务状态** - 运行中/已停止
- **当前节点** - 活动节点名称
- **上传速度** - 实时上传流量
- **下载速度** - 实时下载流量
- **连接信息** - IP、位置、延迟
- **系统资源** - CPU、内存使用率

### 5. 修改密码

1. 进入 **系统设置**
2. 在 **账户设置** 下：
   - 输入当前密码
   - 输入新密码
   - 确认新密码
3. 点击 **修改密码**

## ⚙️ 配置说明

### 配置文件位置

```
/opt/hysteria2-manager/
├── data/
│   ├── config.json        # 系统配置
│   ├── nodes.json         # 节点数据
│   └── users.json         # 用户数据
├── static/
│   └── dashboard.html     # Web界面
└── hysteria2_manager.py   # 核心程序

/etc/hysteria2/
└── client.yaml            # Hysteria2客户端配置

/var/log/hysteria2/
├── manager.log            # 管理器日志
└── hysteria.log           # Hysteria2日志
```

### 系统配置 (config.json)

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

### 节点URL格式

支持的格式：
```
# 基本格式
hy2://密码@服务器:端口

# 带参数
hy2://密码@服务器:端口/?sni=域名&insecure=1

# 完整格式
hysteria2://密码@服务器:端口/?sni=域名&obfs=salamander&obfs-password=混淆密码

# 带自定义名称
hy2://密码@服务器:端口/#节点名称
```

### 环境变量

可以通过环境变量覆盖默认设置：
```bash
export HY2_MANAGER_PORT=8888          # Web端口
export HY2_MANAGER_HOST=127.0.0.1     # 监听地址
export HY2_MANAGER_DEBUG=true         # 调试模式
```

## 🔧 命令参考

### CLI工具 (hy2)

安装后，使用 `hy2` 命令快速管理：

```bash
# 服务管理
hy2 status              # 显示服务状态
hy2 start               # 启动代理服务
hy2 stop                # 停止代理服务
hy2 restart             # 重启代理服务

# 信息显示
hy2 test                # 测试代理连接
hy2 web                 # 显示WebUI地址

# 日志查看
hy2 logs                # 查看客户端日志
hy2 manager-logs        # 查看管理器日志

# 更新
hy2 update              # 检查更新
```

### 服务管理 (systemctl)

```bash
# 管理器服务
sudo systemctl status hysteria2-manager    # 检查状态
sudo systemctl start hysteria2-manager     # 启动服务
sudo systemctl stop hysteria2-manager      # 停止服务
sudo systemctl restart hysteria2-manager   # 重启服务
sudo systemctl enable hysteria2-manager    # 启用自启动

# 客户端服务
sudo systemctl status hysteria2-client     # 检查状态
sudo systemctl start hysteria2-client      # 启动客户端
sudo systemctl stop hysteria2-client       # 停止客户端
sudo systemctl restart hysteria2-client    # 重启客户端
sudo systemctl enable hysteria2-client     # 启用自启动

# 查看日志
sudo journalctl -u hysteria2-manager -f    # 管理器日志
sudo journalctl -u hysteria2-client -f     # 客户端日志
```

### 安装管理

```bash
# 更新
bash install.sh update

# 卸载
bash install.sh uninstall

# 强制重新安装
bash install.sh force
```

## 📡 API 文档

### 认证端点

#### 登录
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin"
}

响应:
{
  "success": true,
  "message": "登录成功",
  "data": {
    "username": "admin",
    "role": "admin",
    "session_id": "...",
    "expires_in": 3600
  }
}
```

#### 登出
```http
POST /api/auth/logout

响应:
{
  "success": true,
  "message": "登出成功"
}
```

#### 修改密码
```http
POST /api/auth/change_password
Content-Type: application/json

{
  "old_password": "当前密码",
  "new_password": "新密码"
}
```

### 服务管理

#### 获取状态
```http
GET /api/status

响应:
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

#### 服务控制
```http
POST /api/service/start    # 启动服务
POST /api/service/stop     # 停止服务
POST /api/service/restart  # 重启服务
```

### 节点管理

#### 获取节点
```http
GET /api/nodes

响应:
{
  "success": true,
  "data": {
    "nodes": [...],
    "current": "节点ID"
  }
}
```

#### 添加节点
```http
POST /api/nodes
Content-Type: application/json

# 方法1: URL导入
{
  "url": "hy2://密码@服务器:端口/?sni=域名",
  "name": "自定义名称"
}

# 方法2: 手动配置
{
  "name": "节点名称",
  "server": "服务器.com",
  "port": 443,
  "password": "密码",
  "sni": "服务器.com"
}
```

#### 使用节点
```http
POST /api/nodes/:id/use
```

#### 删除节点
```http
DELETE /api/nodes/:id
```

### 系统操作

#### 获取日志
```http
GET /api/logs?lines=100&type=all
```

#### 获取系统统计
```http
GET /api/system/stats
```

#### 测试连接
```http
GET /api/test
```

## 🔧 故障排查

### 常见问题

#### 1. 无法访问WebUI

**问题：** 无法连接到 http://服务器IP:8080

**解决方案：**
```bash
# 检查服务状态
sudo systemctl status hysteria2-manager

# 检查端口监听
netstat -tuln | grep 8080

# 检查防火墙
sudo ufw status
sudo ufw allow 8080/tcp  # 如果使用ufw

# 对于firewalld
sudo firewall-cmd --add-port=8080/tcp --permanent
sudo firewall-cmd --reload
```

#### 2. 登录失败

**问题：** 无法使用默认凭证登录

**解决方案：**
```bash
# 重置为默认密码
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

print("密码已重置为: admin")
EOF

# 重启服务
sudo systemctl restart hysteria2-manager
```

#### 3. 代理无法工作

**问题：** 已连接但无法访问互联网

**解决方案：**
```bash
# 检查Hysteria2客户端状态
sudo systemctl status hysteria2-client

# 检查TUN接口
ip link show hytun

# 检查路由
ip route | grep hytun

# 查看详细日志
sudo journalctl -u hysteria2-client -n 100

# 手动测试配置
sudo /usr/local/bin/hysteria client -c /etc/hysteria2/client.yaml
```

#### 4. 高CPU/内存占用

**解决方案：**
```bash
# 检查进程使用
htop

# 清理日志
sudo truncate -s 0 /var/log/hysteria2/*.log

# 重启服务
sudo systemctl restart hysteria2-manager
sudo systemctl restart hysteria2-client

# 检查内存泄漏
ps aux | grep hysteria
```

### 诊断命令

```bash
# 完整系统检查
cat > /tmp/diagnose.sh << 'EOF'
#!/bin/bash
echo "=== 系统诊断 ==="
echo "1. 服务状态:"
systemctl status hysteria2-manager --no-pager | head -10
systemctl status hysteria2-client --no-pager | head -10

echo -e "\n2. 端口状态:"
netstat -tuln | grep -E ":(8080|443)"

echo -e "\n3. TUN接口:"
ip link show hytun 2>/dev/null || echo "TUN接口未找到"

echo -e "\n4. 当前IP:"
curl -s https://ifconfig.io || echo "无法获取IP"

echo -e "\n5. DNS测试:"
nslookup google.com 8.8.8.8 | head -5

echo -e "\n6. 资源使用:"
free -h
df -h /

echo -e "\n7. 最近错误:"
journalctl -p err --since "1 hour ago" | tail -20
EOF

bash /tmp/diagnose.sh
```

## ❓ 常见问题

### Q1: 如何更改Web端口？

**答：** 编辑配置文件：
```bash
# 编辑配置
sudo nano /opt/hysteria2-manager/data/config.json
# 将 "web_port": 8080 改为您需要的端口

# 重启服务
sudo systemctl restart hysteria2-manager
```

### Q2: 如何启用HTTPS？

**答：** 使用Nginx反向代理：
```nginx
server {
    listen 443 ssl;
    server_name 您的域名.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Q3: 如何备份配置？

**答：** 备份所有配置文件：
```bash
# 创建备份
tar -czf hysteria2-backup-$(date +%Y%m%d).tar.gz \
    /opt/hysteria2-manager/data/ \
    /etc/hysteria2/

# 恢复备份
tar -xzf hysteria2-backup-20240120.tar.gz -C /
```

### Q4: 如何迁移到另一台服务器？

**答：** 按以下步骤操作：
```bash
# 在旧服务器 - 导出
tar -czf hysteria2-migrate.tar.gz \
    /opt/hysteria2-manager/ \
    /etc/hysteria2/

# 在新服务器 - 导入
scp user@旧服务器:~/hysteria2-migrate.tar.gz .
tar -xzf hysteria2-migrate.tar.gz -C /
bash install.sh  # 运行安装程序设置服务
```

### Q5: 如何使用多用户？

**答：** 目前只支持单个管理员用户。多用户支持计划在未来版本中加入。

### Q6: 如何查看实时流量？

**答：** 仪表板会自动每5秒更新一次流量统计。您也可以使用命令行：
```bash
# 实时流量监控
watch -n 1 'ip -s link show hytun'
```

### Q7: 节点链接格式有哪些？

**答：** 支持以下格式：
- `hy2://` - Hysteria2标准格式
- `hysteria2://` - 完整格式
- `hysteria://` - 兼容格式

参数支持：
- `sni` - 服务器名称指示
- `insecure` - 跳过证书验证
- `obfs` - 混淆类型
- `obfs-password` - 混淆密码
- `alpn` - ALPN协议
- `up/down` - 带宽限制

### Q8: 如何优化性能？

**答：** 系统已自动优化，额外优化：
```bash
# 增加文件描述符限制
ulimit -n 65535

# 优化TCP参数
echo "net.ipv4.tcp_congestion_control = bbr" >> /etc/sysctl.conf
sysctl -p

# 使用更快的DNS
echo "nameserver 1.1.1.1" > /etc/resolv.conf
```

## 📝 更新日志

### v2.0.0 (2024-01-20)
- 🔐 **新增：** 完整的认证系统
- 🎨 **新增：** 现代科技风格UI，深色主题
- 🔧 **新增：** RESTful API带会话管理
- ✅ **修复：** 所有已知v1.0问题
- ✅ **修复：** URL解析支持所有格式
- ✅ **修复：** 连接状态检测
- ✅ **修复：** DNS测试可靠性
- ✅ **修复：** 日志查看功能
- ✅ **修复：** 系统资源监控
- 📦 **改进：** 安装流程
- 📊 **改进：** 实时统计
- 🛡️ **改进：** 安全特性

### v1.0.0 (2024-01-15)
- 🎉 初始版本发布
- ✨ 基础功能实现
- 🎨 Web UI界面
- 📦 一键安装脚本

### 开发路线图

- [ ] v2.1.0 - 多用户支持
- [ ] v2.2.0 - Docker容器支持
- [ ] v2.3.0 - 订阅管理
- [ ] v2.4.0 - 流量统计和限制
- [ ] v2.5.0 - 规则路由
- [ ] v3.0.0 - 移动端APP

## 🤝 开发说明

### 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/yourusername/hysteria2-manager.git
cd hysteria2-manager

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install flask flask-cors psutil pyyaml requests bcrypt

# 调试模式运行
export HY2_MANAGER_DEBUG=true
python hysteria2_manager.py
```

### 项目结构

```
hysteria2-manager/
├── install.sh                    # 安装脚本
├── hysteria2_manager.py          # 核心程序
├── static/
│   └── dashboard.html            # Web界面
├── data/                         # 数据目录
│   ├── config.json              # 系统配置
│   ├── nodes.json               # 节点数据
│   └── users.json               # 用户数据
├── system/                       # 系统文件
│   ├── hysteria2-manager.service # systemd服务文件
│   └── hysteria2-client.service  # 客户端服务文件
├── docs/                         # 文档
│   ├── API.md                   # API文档
│   └── DEVELOPMENT.md           # 开发文档
├── tests/                        # 测试
│   └── test_manager.py          # 单元测试
├── requirements.txt              # Python依赖
├── LICENSE                       # 许可证
└── README.md                     # 说明文档
```

### 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 提交问题

请包含以下信息：
- 系统信息（操作系统、Python版本）
- 错误日志
- 重现步骤
- 预期行为 vs 实际行为

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

- [Hysteria2](https://github.com/apernet/hysteria) - 强大的代理核心
- [Flask](https://flask.palletsprojects.com/) - Python Web框架
- [Vue.js](https://vuejs.org/) - 前端框架
- [Chart.js](https://www.chartjs.org/) - 数据可视化
- 所有贡献者和用户

## 📞 联系方式

- **GitHub Issues：** [报告问题](https://github.com/yourusername/hysteria2-manager/issues)
- **Discussions：** [提问讨论](https://github.com/yourusername/hysteria2-manager/discussions)
- **邮箱：** admin@example.com
- **Telegram：** [@hysteria2manager](https://t.me/hysteria2manager)

## 🌟 Star历史

[![Star History Chart](https://api.star-history.com/svg?repos=yourusername/hysteria2-manager&type=Date)](https://star-history.com/#yourusername/hysteria2-manager&Date)

---

<div align="center">

**如果这个项目对您有帮助，请给一个 ⭐ Star！**

[![GitHub Stars](https://img.shields.io/github/stars/yourusername/hysteria2-manager?style=social)](https://github.com/yourusername/hysteria2-manager)
[![GitHub Forks](https://img.shields.io/github/forks/yourusername/hysteria2-manager?style=social)](https://github.com/yourusername/hysteria2-manager/fork)
[![GitHub Issues](https://img.shields.io/github/issues/yourusername/hysteria2-manager)](https://github.com/yourusername/hysteria2-manager/issues)
[![GitHub License](https://img.shields.io/github/license/yourusername/hysteria2-manager)](https://github.com/yourusername/hysteria2-manager/blob/main/LICENSE)

[返回顶部](#hysteria2-manager-v20)

</div>

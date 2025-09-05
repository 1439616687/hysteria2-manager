# Hysteria2 WebUI Manager

一个功能强大且易于使用的 Hysteria2 客户端 Web 管理界面，提供一键安装、可视化配置和实时监控功能。

## 🌟 特性

- **🚀 一键安装**: 单行命令即可完成全部部署
- **🎨 友好界面**: 直观的 Web UI，无需记忆复杂命令
- **⚙️ 灵活配置**: 支持快速导入节点链接或手动配置
- **📊 实时监控**: 查看服务状态、系统资源和网络流量
- **📝 日志查看**: 实时查看和分析系统日志
- **🔒 安全访问**: 内置用户认证系统
- **📱 响应式设计**: 支持手机、平板和桌面访问

## 📋 系统要求

- Linux 系统 (Ubuntu/Debian/CentOS/Fedora)
- Python 3.6+
- Root 权限
- 1GB+ 内存
- 支持 TUN/TAP 的内核

## 🚀 快速安装

### 方法一：在线安装（推荐）

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/yourusername/hysteria2-webui-manager/main/install.sh)

方法二：离线安装

克隆仓库：

bashgit clone https://github.com/yourusername/hysteria2-webui-manager.git
cd hysteria2-webui-manager

运行安装脚本：

bashsudo bash install.sh
📖 使用说明
访问管理界面
安装完成后，使用浏览器访问：
http://您的服务器IP:8080
默认登录信息会在安装时显示，请妥善保存。
快速连接节点

在主页的"快速连接"区域粘贴节点链接
点击"一键连接"按钮
系统会自动解析并应用配置

支持的节点格式
hy2://password@server:port?sni=domain
hysteria2://password@server:port?insecure=1&sni=domain
配置管理
快速配置

直接粘贴节点链接
支持批量导入多个节点
自动解析和验证

手动配置

服务器地址和端口
认证密码
TLS/SNI 设置
证书验证选项

高级设置

TUN 接口参数
路由规则自定义
IP 段排除配置
带宽优化设置

🛠️ 管理命令
服务管理
bash# 查看服务状态
systemctl status hysteria2-webui

# 启动服务
systemctl start hysteria2-webui

# 停止服务
systemctl stop hysteria2-webui

# 重启服务
systemctl restart hysteria2-webui

# 查看日志
journalctl -u hysteria2-webui -f
Hysteria2 核心管理
bash# 查看 Hysteria2 状态
systemctl status hysteria2

# 手动测试配置
/usr/local/bin/hysteria client -c /etc/hysteria2/client.yaml --test
📁 文件位置

WebUI 程序: /opt/hysteria2-webui/
Hysteria2 配置: /etc/hysteria2/client.yaml
Hysteria2 二进制: /usr/local/bin/hysteria
WebUI 配置: /opt/hysteria2-webui/config/settings.json

🔧 故障排查
无法访问 WebUI

检查防火墙是否开放 8080 端口：

bash# UFW
sudo ufw allow 8080/tcp

# Firewalld
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --reload

检查服务是否运行：

bashsystemctl status hysteria2-webui
Hysteria2 无法连接

查看详细日志：

bashjournalctl -u hysteria2 -n 50

验证配置文件：

bashcat /etc/hysteria2/client.yaml

测试网络连接：

bashping 服务器地址
telnet 服务器地址 端口
重置管理密码
编辑配置文件：
bashnano /opt/hysteria2-webui/config/settings.json
修改 password 字段后重启服务：
bashsystemctl restart hysteria2-webui
🔄 更新
bashcd /opt/hysteria2-webui
git pull
pip install -r requirements.txt
systemctl restart hysteria2-webui
🤝 贡献
欢迎提交 Issue 和 Pull Request！
📄 许可证
MIT License
🙏 致谢

Hysteria2 - 高性能代理核心
Flask - Web 框架
所有贡献者和用户


如有问题，请提交 Issue

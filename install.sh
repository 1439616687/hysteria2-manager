#!/bin/bash
#
# Hysteria2 Manager v2.0 - Professional Installation Script
# Author: Hysteria2 Manager Team
# License: MIT
#

set -e

# ==================== 配置常量 ====================
VERSION="2.0.0"
INSTALL_DIR="/opt/hysteria2-manager"
DATA_DIR="$INSTALL_DIR/data"
STATIC_DIR="$INSTALL_DIR/static"
LOG_DIR="/var/log/hysteria2"
CONFIG_DIR="/etc/hysteria2"
HYSTERIA_BIN="/usr/local/bin/hysteria"
SYSTEMD_DIR="/etc/systemd/system"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# ==================== 工具函数 ====================

# 打印带颜色的消息
print_msg() {
    local color=$1
    local msg=$2
    echo -e "${color}${msg}${NC}"
}

# 打印标题
print_title() {
    echo ""
    echo -e "${BLUE}=================================================================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${BLUE}=================================================================================${NC}"
    echo ""
}

# 打印成功消息
print_success() {
    print_msg "$GREEN" "✓ $1"
}

# 打印错误消息
print_error() {
    print_msg "$RED" "✗ $1"
}

# 打印警告消息
print_warning() {
    print_msg "$YELLOW" "⚠ $1"
}

# 打印信息
print_info() {
    print_msg "$CYAN" "ℹ $1"
}

# 打印步骤
print_step() {
    echo -e "${PURPLE}▶ $1${NC}"
}

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 检查是否为root用户
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "此脚本必须以root权限运行"
        echo "请使用: sudo bash $0"
        exit 1
    fi
}

# 获取系统信息
get_system_info() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$ID
        OS_VERSION=$VERSION_ID
        OS_PRETTY=$PRETTY_NAME
    elif command_exists lsb_release; then
        OS=$(lsb_release -si | tr '[:upper:]' '[:lower:]')
        OS_VERSION=$(lsb_release -sr)
        OS_PRETTY=$(lsb_release -sd)
    else
        OS=$(uname -s | tr '[:upper:]' '[:lower:]')
        OS_VERSION=$(uname -r)
        OS_PRETTY="$OS $OS_VERSION"
    fi
    
    # 获取架构
    ARCH=$(uname -m)
    case $ARCH in
        x86_64)
            ARCH="amd64"
            ;;
        aarch64)
            ARCH="arm64"
            ;;
        armv7l)
            ARCH="armv7"
            ;;
        *)
            print_error "不支持的架构: $ARCH"
            exit 1
            ;;
    esac
}

# 显示Logo
show_logo() {
    clear
    echo -e "${CYAN}"
    cat << "EOF"
    ╦ ╦╦ ╦╔═╗╔╦╗╔═╗╦═╗╦╔═╗╔═╗  ╔╦╗╔═╗╔╗╔╔═╗╔═╗╔═╗╦═╗
    ╠═╣╚╦╝╚═╗ ║ ║╣ ╠╦╝║╠═╣╔═╝  ║║║╠═╣║║║╠═╣║ ╦║╣ ╠╦╝
    ╩ ╩ ╩ ╚═╝ ╩ ╚═╝╩╚═╩╩ ╩╚═╝  ╩ ╩╩ ╩╝╚╝╩ ╩╚═╝╚═╝╩╚═
                    v2.0.0
EOF
    echo -e "${NC}"
    echo -e "${WHITE}Professional Proxy Management System${NC}"
    echo ""
}

# 显示系统信息
show_system_info() {
    print_title "系统信息"
    echo -e "操作系统: ${WHITE}$OS_PRETTY${NC}"
    echo -e "系统架构: ${WHITE}$ARCH${NC}"
    echo -e "内核版本: ${WHITE}$(uname -r)${NC}"
    echo -e "主机名称: ${WHITE}$(hostname)${NC}"
    echo -e "当前时间: ${WHITE}$(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo ""
}

# ==================== 依赖安装 ====================

# 安装基础依赖
install_dependencies() {
    print_title "安装系统依赖"
    
    print_step "更新包管理器..."
    
    case $OS in
        ubuntu|debian)
            apt-get update -qq
            print_step "安装依赖包..."
            apt-get install -y -qq \
                curl \
                wget \
                tar \
                gzip \
                ca-certificates \
                python3 \
                python3-pip \
                python3-venv \
                git \
                jq \
                net-tools \
                dnsutils \
                lsof
            ;;
        centos|rhel|fedora)
            if command_exists dnf; then
                dnf update -y -q
                print_step "安装依赖包..."
                dnf install -y -q \
                    curl \
                    wget \
                    tar \
                    gzip \
                    ca-certificates \
                    python3 \
                    python3-pip \
                    git \
                    jq \
                    net-tools \
                    bind-utils \
                    lsof
            else
                yum update -y -q
                print_step "安装依赖包..."
                yum install -y -q \
                    curl \
                    wget \
                    tar \
                    gzip \
                    ca-certificates \
                    python3 \
                    python3-pip \
                    git \
                    jq \
                    net-tools \
                    bind-utils \
                    lsof
            fi
            ;;
        arch)
            pacman -Syu --noconfirm
            print_step "安装依赖包..."
            pacman -S --noconfirm \
                curl \
                wget \
                tar \
                gzip \
                ca-certificates \
                python \
                python-pip \
                git \
                jq \
                net-tools \
                bind \
                lsof
            ;;
        *)
            print_error "不支持的操作系统: $OS"
            exit 1
            ;;
    esac
    
    print_success "系统依赖安装完成"
}

# ==================== Hysteria2安装 ====================

# 下载Hysteria2
download_hysteria2() {
    print_title "下载Hysteria2核心"
    
    # 获取最新版本
    print_step "获取最新版本信息..."
    HYSTERIA_VERSION=$(curl -s https://api.github.com/repos/apernet/hysteria/releases/latest | grep tag_name | cut -d'"' -f4)
    
    if [[ -z "$HYSTERIA_VERSION" ]]; then
        print_warning "无法获取最新版本，使用默认版本"
        HYSTERIA_VERSION="v2.6.2"
    fi
    
    print_info "最新版本: $HYSTERIA_VERSION"
    
    # 构建下载URL
    DOWNLOAD_URL="https://github.com/apernet/hysteria/releases/download/${HYSTERIA_VERSION}/hysteria-linux-${ARCH}"
    
    # 如果文件已存在且版本相同，跳过下载
    if [[ -f "$HYSTERIA_BIN" ]]; then
        CURRENT_VERSION=$($HYSTERIA_BIN version 2>/dev/null | grep -oP 'Version:\s+\K[^\s]+' || echo "unknown")
        if [[ "$CURRENT_VERSION" == "${HYSTERIA_VERSION#v}" ]]; then
            print_info "Hysteria2已是最新版本，跳过下载"
            return
        fi
    fi
    
    # 下载文件
    print_step "下载Hysteria2核心..."
    if wget -q --show-progress -O /tmp/hysteria "$DOWNLOAD_URL"; then
        mv /tmp/hysteria "$HYSTERIA_BIN"
        chmod +x "$HYSTERIA_BIN"
        print_success "Hysteria2下载成功"
    else
        print_error "Hysteria2下载失败"
        exit 1
    fi
    
    # 验证安装
    if $HYSTERIA_BIN version >/dev/null 2>&1; then
        print_success "Hysteria2安装成功"
        $HYSTERIA_BIN version
    else
        print_error "Hysteria2安装验证失败"
        exit 1
    fi
}

# ==================== Python环境配置 ====================

# 设置Python环境
setup_python_env() {
    print_title "配置Python环境"
    
    # 创建虚拟环境
    print_step "创建Python虚拟环境..."
    python3 -m venv "$INSTALL_DIR/venv"
    
    # 激活虚拟环境并安装依赖
    print_step "安装Python依赖包..."
    source "$INSTALL_DIR/venv/bin/activate"
    
    # 升级pip
    pip install --upgrade pip -q
    
    # 安装依赖
    cat > /tmp/requirements.txt << EOF
Flask==3.0.0
Flask-Cors==4.0.0
PyJWT==2.8.0
bcrypt==4.1.2
psutil==5.9.8
PyYAML==6.0.1
requests==2.31.0
EOF
    
    pip install -r /tmp/requirements.txt -q
    
    deactivate
    rm -f /tmp/requirements.txt
    
    print_success "Python环境配置完成"
}

# ==================== 文件部署 ====================

# 创建目录结构
create_directories() {
    print_title "创建目录结构"
    
    directories=(
        "$INSTALL_DIR"
        "$DATA_DIR"
        "$STATIC_DIR"
        "$LOG_DIR"
        "$CONFIG_DIR"
    )
    
    for dir in "${directories[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            print_success "创建目录: $dir"
        else
            print_info "目录已存在: $dir"
        fi
    done
    
    # 设置权限
    chmod 755 "$INSTALL_DIR"
    chmod 755 "$LOG_DIR"
    chmod 755 "$CONFIG_DIR"
}

# 下载项目文件
download_project_files() {
    print_title "下载项目文件"
    
    # GitHub仓库地址
    GITHUB_REPO="https://raw.githubusercontent.com/1439616687/hysteria2-manager/main"
    
    # 下载主程序
    print_step "下载主程序..."
    if [[ -f "hysteria2_manager.py" ]]; then
        cp hysteria2_manager.py "$INSTALL_DIR/"
        print_success "使用本地主程序文件"
    else
        wget -q -O "$INSTALL_DIR/hysteria2_manager.py" "$GITHUB_REPO/hysteria2_manager.py" || {
            print_warning "无法从GitHub下载，使用内置版本"
            create_minimal_manager
        }
    fi
    
    # 下载WebUI
    print_step "下载WebUI..."
    if [[ -f "webui.html" ]]; then
        cp webui.html "$STATIC_DIR/"
        print_success "使用本地WebUI文件"
    else
        wget -q -O "$STATIC_DIR/webui.html" "$GITHUB_REPO/webui.html" || {
            print_warning "无法从GitHub下载，使用内置版本"
            create_minimal_webui
        }
    fi
    
    # 创建初始配置文件
    create_initial_configs
    
    print_success "项目文件部署完成"
}

# 创建最小化管理器（备用）
create_minimal_manager() {
    cat > "$INSTALL_DIR/hysteria2_manager.py" << 'EOF'
#!/usr/bin/env python3
# Minimal Hysteria2 Manager
import os
import sys
print("请从GitHub下载完整版本的hysteria2_manager.py")
print("https://github.com/1439616687/hysteria2-manager")
sys.exit(1)
EOF
    chmod +x "$INSTALL_DIR/hysteria2_manager.py"
}

# 创建最小化WebUI（备用）
create_minimal_webui() {
    cat > "$STATIC_DIR/webui.html" << 'EOF'
<!DOCTYPE html>
<html>
<head><title>Hysteria2 Manager</title></head>
<body>
<h1>请从GitHub下载完整版本</h1>
<p>https://github.com/1439616687/hysteria2-manager</p>
</body>
</html>
EOF
}

# 创建初始配置文件
create_initial_configs() {
    # 创建默认配置
    if [[ ! -f "$DATA_DIR/config.json" ]]; then
        cat > "$DATA_DIR/config.json" << EOF
{
  "version": "$VERSION",
  "web_port": 8080,
  "web_host": "0.0.0.0",
  "language": "zh-CN",
  "theme": "dark",
  "auth": {
    "enabled": true,
    "session_timeout": 1800
  },
  "hysteria": {
    "bin_path": "$HYSTERIA_BIN",
    "config_path": "$CONFIG_DIR/client.yaml",
    "log_level": "info"
  },
  "system": {
    "auto_start": true,
    "auto_optimize": true,
    "check_update": true
  }
}
EOF
        print_success "创建默认配置文件"
    fi
    
    # 创建用户文件
    if [[ ! -f "$DATA_DIR/users.json" ]]; then
        cat > "$DATA_DIR/users.json" << EOF
[
  {
    "username": "admin",
    "password": "admin",
    "role": "admin",
    "created_at": "$(date -Iseconds)"
  }
]
EOF
        print_success "创建默认用户文件"
    fi
    
    # 创建节点文件
    if [[ ! -f "$DATA_DIR/nodes.json" ]]; then
        cat > "$DATA_DIR/nodes.json" << EOF
{
  "nodes": [],
  "current": null,
  "subscriptions": []
}
EOF
        print_success "创建节点配置文件"
    fi
}

# ==================== 系统服务配置 ====================

# 创建systemd服务
create_systemd_services() {
    print_title "配置系统服务"
    
    # 创建管理器服务
    print_step "创建管理器服务..."
    cat > "$SYSTEMD_DIR/hysteria2-manager.service" << EOF
[Unit]
Description=Hysteria2 Manager WebUI Service
Documentation=https://github.com/1439616687/hysteria2-manager
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="PYTHONPATH=$INSTALL_DIR"
ExecStartPre=/bin/bash -c 'if [ ! -f $DATA_DIR/config.json ]; then exit 1; fi'
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/hysteria2_manager.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=hysteria2-manager
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF
    
    # 创建客户端服务
    print_step "创建客户端服务..."
    cat > "$SYSTEMD_DIR/hysteria2-client.service" << EOF
[Unit]
Description=Hysteria2 Client Service
Documentation=https://v2.hysteria.network/
After=network-online.target nss-lookup.target
Wants=network-online.target
BindsTo=hysteria2-manager.service
After=hysteria2-manager.service

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=$CONFIG_DIR
ExecStartPre=-/usr/sbin/ip link delete hytun 2>/dev/null
ExecStartPre=/bin/sleep 2
ExecStart=$HYSTERIA_BIN client -c $CONFIG_DIR/client.yaml
ExecStopPost=-/usr/sbin/ip link delete hytun 2>/dev/null
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=hysteria2-client
LimitNOFILE=1048576
CapabilityBoundingSet=CAP_NET_ADMIN CAP_NET_RAW CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_ADMIN CAP_NET_RAW CAP_NET_BIND_SERVICE

[Install]
WantedBy=multi-user.target
EOF
    
    # 重载systemd
    systemctl daemon-reload
    
    print_success "系统服务配置完成"
}

# ==================== 系统优化 ====================

# 优化系统参数
optimize_system() {
    print_title "系统优化"
    
    print_step "优化网络参数..."
    
    # 备份原始配置
    if [[ ! -f /etc/sysctl.conf.bak ]]; then
        cp /etc/sysctl.conf /etc/sysctl.conf.bak
    fi
    
    # 添加优化参数
    cat >> /etc/sysctl.conf << EOF

# Hysteria2 Manager Optimizations
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.ipv4.tcp_rmem = 4096 87380 134217728
net.ipv4.tcp_wmem = 4096 65536 134217728
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_mtu_probing = 1
net.ipv4.tcp_congestion_control = bbr
net.ipv4.ip_forward = 1
net.ipv6.conf.all.forwarding = 1
net.ipv4.tcp_fastopen = 3
EOF
    
    # 应用设置
    sysctl -p >/dev/null 2>&1
    
    print_step "优化文件描述符限制..."
    cat >> /etc/security/limits.conf << EOF

# Hysteria2 Manager Limits
* soft nofile 65535
* hard nofile 65535
root soft nofile 65535
root hard nofile 65535
EOF
    
    # 加载TUN模块
    print_step "加载TUN模块..."
    modprobe tun
    echo "tun" >> /etc/modules-load.d/modules.conf
    
    print_success "系统优化完成"
}

# ==================== 防火墙配置 ====================

# 配置防火墙
configure_firewall() {
    print_title "配置防火墙"
    
    # 获取Web端口
    WEB_PORT=$(grep -oP '"web_port":\s*\K\d+' "$DATA_DIR/config.json" 2>/dev/null || echo "8080")
    
    print_step "开放端口 $WEB_PORT..."
    
    # UFW防火墙
    if command_exists ufw; then
        ufw allow "$WEB_PORT/tcp" >/dev/null 2>&1
        print_success "UFW防火墙规则已添加"
    fi
    
    # Firewalld防火墙
    if command_exists firewall-cmd; then
        firewall-cmd --permanent --add-port="$WEB_PORT/tcp" >/dev/null 2>&1
        firewall-cmd --reload >/dev/null 2>&1
        print_success "Firewalld防火墙规则已添加"
    fi
    
    # iptables防火墙
    if command_exists iptables; then
        iptables -I INPUT -p tcp --dport "$WEB_PORT" -j ACCEPT >/dev/null 2>&1
        print_info "iptables规则已添加（重启后需要重新配置）"
    fi
}

# ==================== 启动服务 ====================

# 启动服务
start_services() {
    print_title "启动服务"
    
    print_step "启动管理器服务..."
    systemctl start hysteria2-manager
    systemctl enable hysteria2-manager >/dev/null 2>&1
    
    # 等待服务启动
    sleep 3
    
    # 检查服务状态
    if systemctl is-active hysteria2-manager >/dev/null 2>&1; then
        print_success "管理器服务启动成功"
    else
        print_error "管理器服务启动失败"
        print_info "查看日志: journalctl -u hysteria2-manager -n 50"
    fi
}

# ==================== 卸载功能 ====================

# 卸载程序
uninstall() {
    print_title "卸载 Hysteria2 Manager"
    
    print_warning "即将卸载Hysteria2 Manager"
    read -p "确定要继续吗？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "取消卸载"
        exit 0
    fi
    
    # 停止服务
    print_step "停止服务..."
    systemctl stop hysteria2-manager >/dev/null 2>&1
    systemctl stop hysteria2-client >/dev/null 2>&1
    systemctl disable hysteria2-manager >/dev/null 2>&1
    systemctl disable hysteria2-client >/dev/null 2>&1
    
    # 删除服务文件
    print_step "删除服务文件..."
    rm -f "$SYSTEMD_DIR/hysteria2-manager.service"
    rm -f "$SYSTEMD_DIR/hysteria2-client.service"
    systemctl daemon-reload
    
    # 备份配置
    print_step "备份配置..."
    if [[ -d "$DATA_DIR" ]]; then
        backup_file="/tmp/hysteria2-manager-backup-$(date +%Y%m%d-%H%M%S).tar.gz"
        tar -czf "$backup_file" -C "$INSTALL_DIR" data/ 2>/dev/null
        print_info "配置已备份到: $backup_file"
    fi
    
    # 删除文件
    print_step "删除程序文件..."
    rm -rf "$INSTALL_DIR"
    rm -rf "$LOG_DIR"
    rm -rf "$CONFIG_DIR"
    rm -f "$HYSTERIA_BIN"
    
    print_success "卸载完成"
}

# ==================== 更新功能 ====================

# 更新程序
update() {
    print_title "更新 Hysteria2 Manager"
    
    # 备份当前版本
    print_step "备份当前版本..."
    backup_dir="/tmp/hysteria2-manager-backup-$(date +%Y%m%d-%H%M%S)"
    cp -r "$INSTALL_DIR" "$backup_dir"
    print_info "备份目录: $backup_dir"
    
    # 停止服务
    print_step "停止服务..."
    systemctl stop hysteria2-manager
    
    # 更新文件
    download_hysteria2
    download_project_files
    setup_python_env
    
    # 重启服务
    print_step "重启服务..."
    systemctl start hysteria2-manager
    
    print_success "更新完成"
}

# ==================== 安装后信息 ====================

# 显示安装信息
show_installation_info() {
    WEB_PORT=$(grep -oP '"web_port":\s*\K\d+' "$DATA_DIR/config.json" 2>/dev/null || echo "8080")
    
    # 获取IP地址
    PUBLIC_IP=$(curl -s -4 ifconfig.io 2>/dev/null || echo "服务器IP")
    
    print_title "安装完成"
    
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║         Hysteria2 Manager 安装成功！                      ║${NC}"
    echo -e "${GREEN}╠════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${GREEN}║${NC} WebUI访问地址:                                            ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC}   本地: ${CYAN}http://127.0.0.1:$WEB_PORT${NC}                            ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC}   远程: ${CYAN}http://$PUBLIC_IP:$WEB_PORT${NC}                          ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC}                                                            ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC} 默认账号密码:                                             ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC}   用户名: ${YELLOW}admin${NC}                                           ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC}   密码:   ${YELLOW}admin${NC}                                           ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC}                                                            ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC} ${RED}⚠ 请立即登录并修改默认密码！${NC}                            ${GREEN}║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${WHITE}常用命令:${NC}"
    echo -e "  查看状态: ${CYAN}systemctl status hysteria2-manager${NC}"
    echo -e "  查看日志: ${CYAN}journalctl -u hysteria2-manager -f${NC}"
    echo -e "  重启服务: ${CYAN}systemctl restart hysteria2-manager${NC}"
    echo -e "  停止服务: ${CYAN}systemctl stop hysteria2-manager${NC}"
    echo ""
}

# ==================== 主函数 ====================

main() {
    # 显示Logo
    show_logo
    
    # 检查root权限
    check_root
    
    # 获取系统信息
    get_system_info
    
    # 显示系统信息
    show_system_info
    
    # 处理命令行参数
    case "${1:-}" in
        uninstall)
            uninstall
            exit 0
            ;;
        update)
            update
            exit 0
            ;;
        *)
            # 执行完整安装
            ;;
    esac
    
    # 检查是否已安装
    if [[ -d "$INSTALL_DIR" ]] && [[ -f "$INSTALL_DIR/hysteria2_manager.py" ]]; then
        print_warning "检测到已安装的Hysteria2 Manager"
        echo ""
        echo "请选择操作:"
        echo "  1) 重新安装"
        echo "  2) 更新"
        echo "  3) 卸载"
        echo "  4) 取消"
        echo ""
        read -p "请输入选项 [1-4]: " choice
        
        case $choice in
            1)
                print_info "开始重新安装..."
                ;;
            2)
                update
                exit 0
                ;;
            3)
                uninstall
                exit 0
                ;;
            *)
                print_info "操作已取消"
                exit 0
                ;;
        esac
    fi
    
    # 开始安装
    print_info "开始安装过程..."
    
    # 安装步骤
    install_dependencies
    create_directories
    download_hysteria2
    download_project_files
    setup_python_env
    create_systemd_services
    optimize_system
    configure_firewall
    start_services
    
    # 显示安装信息
    show_installation_info
    
    print_success "安装脚本执行完成！"
}

# 执行主函数
main "$@"

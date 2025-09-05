#!/bin/bash

# Hysteria2 Manager - 一键安装脚本
# 项目地址: https://github.com/yourusername/hysteria2-manager
# 版权信息: MIT License
# 版本: v1.0.0

set -e

# ================== 配置变量 ==================
GITHUB_REPO="yourusername/hysteria2-manager"
INSTALL_DIR="/opt/hysteria2-manager"
DATA_DIR="$INSTALL_DIR/data"
SYSTEM_DIR="$INSTALL_DIR/system"
STATIC_DIR="$INSTALL_DIR/static"
BIN_DIR="/usr/local/bin"
SERVICE_NAME="hysteria2-manager"
CLIENT_SERVICE="hysteria2-client"
WEB_PORT=8080
CURRENT_VERSION="v1.0.0"

# ================== 颜色定义 ==================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# ================== 工具函数 ==================
print_logo() {
    clear
    echo -e "${CYAN}"
    cat << "EOF"
    _   _           _            _       ____  
   | | | |_   _ ___| |_ ___ _ __(_) __ _|___ \ 
   | |_| | | | / __| __/ _ \ '__| |/ _` | __) |
   |  _  | |_| \__ \ ||  __/ |  | | (_| |/ __/ 
   |_| |_|\__, |___/\__\___|_|  |_|\__,_|_____|
          |___/     Manager - WebUI Edition
EOF
    echo -e "${NC}"
    echo -e "${GREEN}Hysteria2 Manager 一键安装脚本 ${CURRENT_VERSION}${NC}"
    echo -e "${CYAN}=================================${NC}"
    echo
}

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

confirm() {
    local prompt="${1:-继续操作？}"
    local default="${2:-n}"
    
    if [[ $default == "y" ]]; then
        prompt="$prompt [Y/n]: "
    else
        prompt="$prompt [y/N]: "
    fi
    
    read -r -p "$prompt" response
    response=${response,,}  # 转换为小写
    
    if [[ -z $response ]]; then
        response=$default
    fi
    
    [[ $response == "y" ]]
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本必须以root权限运行"
        echo "请使用: sudo bash $0"
        exit 1
    fi
}

detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$ID
        OS_NAME=$NAME
        VERSION=$VERSION_ID
    elif [[ -f /etc/redhat-release ]]; then
        OS="centos"
        OS_NAME="CentOS"
        VERSION=$(rpm -E %{rhel})
    else
        log_error "不支持的操作系统"
        exit 1
    fi
    
    # 检测架构
    ARCH=$(uname -m)
    case $ARCH in
        x86_64|amd64)
            ARCH_TYPE="amd64"
            ;;
        aarch64|arm64)
            ARCH_TYPE="arm64"
            ;;
        armv7l)
            ARCH_TYPE="armv7"
            ;;
        *)
            log_error "不支持的系统架构: $ARCH"
            exit 1
            ;;
    esac
    
    log_info "检测到系统: $OS_NAME $VERSION ($ARCH_TYPE)"
}

check_dependencies() {
    log_info "检查系统依赖..."
    
    local missing_deps=()
    
    # 检查Python3
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    fi
    
    # 检查pip3
    if ! command -v pip3 &> /dev/null && ! python3 -m pip --version &> /dev/null; then
        missing_deps+=("python3-pip")
    fi
    
    # 检查curl
    if ! command -v curl &> /dev/null; then
        missing_deps+=("curl")
    fi
    
    # 检查systemctl
    if ! command -v systemctl &> /dev/null; then
        log_error "系统不支持systemd"
        exit 1
    fi
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_info "需要安装以下依赖: ${missing_deps[*]}"
        install_dependencies
    else
        log_success "所有依赖已满足"
    fi
}

install_dependencies() {
    log_info "安装系统依赖..."
    
    case $OS in
        ubuntu|debian)
            apt-get update
            apt-get install -y python3 python3-pip python3-venv curl wget nano net-tools
            ;;
        centos|rhel|fedora|rocky|almalinux)
            yum install -y python3 python3-pip curl wget nano net-tools
            ;;
        arch|manjaro)
            pacman -Sy --noconfirm python python-pip curl wget nano net-tools
            ;;
        *)
            log_error "不支持的系统: $OS"
            exit 1
            ;;
    esac
    
    log_success "依赖安装完成"
}

download_hysteria2() {
    log_info "下载Hysteria2核心程序..."
    
    local download_url="https://github.com/apernet/hysteria/releases/latest/download/hysteria-linux-$ARCH_TYPE"
    
    # 如果已存在且是最新版本，跳过下载
    if [[ -f "$BIN_DIR/hysteria" ]]; then
        if $BIN_DIR/hysteria version &> /dev/null; then
            log_info "Hysteria2已安装，检查更新..."
            local current=$($BIN_DIR/hysteria version 2>&1 | grep -oP 'v[\d.]+' || echo "unknown")
            log_info "当前版本: $current"
        fi
    fi
    
    # 下载最新版本
    log_info "下载地址: $download_url"
    if curl -L -o /tmp/hysteria --progress-bar "$download_url"; then
        mv /tmp/hysteria "$BIN_DIR/hysteria"
        chmod +x "$BIN_DIR/hysteria"
        log_success "Hysteria2核心下载成功"
        
        # 验证安装
        if $BIN_DIR/hysteria version &> /dev/null; then
            local version=$($BIN_DIR/hysteria version 2>&1 | head -1)
            log_success "Hysteria2安装成功: $version"
        else
            log_error "Hysteria2安装验证失败"
            exit 1
        fi
    else
        log_error "Hysteria2下载失败"
        exit 1
    fi
}

create_directories() {
    log_info "创建目录结构..."
    
    # 创建必要的目录
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$DATA_DIR"
    mkdir -p "$SYSTEM_DIR"
    mkdir -p "$STATIC_DIR"
    mkdir -p "/var/log/hysteria2"
    
    # 设置权限
    chmod 755 "$INSTALL_DIR"
    chmod 700 "$DATA_DIR"  # 数据目录仅root可访问
    
    log_success "目录创建完成"
}

download_manager_files() {
    log_info "下载管理器文件..."
    
    # 这里可以从GitHub下载，或者使用内嵌的方式创建文件
    # 为了演示，我们使用创建文件的方式
    
    # 下载或创建主程序
    if [[ -f "hysteria2_manager.py" ]]; then
        # 如果本地存在，直接复制
        cp hysteria2_manager.py "$INSTALL_DIR/"
    else
        # 从GitHub下载
        local base_url="https://raw.githubusercontent.com/$GITHUB_REPO/main"
        curl -sL -o "$INSTALL_DIR/hysteria2_manager.py" "$base_url/hysteria2_manager.py" || {
            log_error "下载管理器主程序失败"
            exit 1
        }
    fi
    
    # 下载WebUI文件
    if [[ -f "static/dashboard.html" ]]; then
        cp static/dashboard.html "$STATIC_DIR/"
    else
        curl -sL -o "$STATIC_DIR/dashboard.html" "$base_url/static/dashboard.html" || {
            log_error "下载WebUI文件失败"
            exit 1
        }
    fi
    
    # 创建初始配置文件
    create_initial_config
    
    # 设置权限
    chmod +x "$INSTALL_DIR/hysteria2_manager.py"
    
    log_success "管理器文件部署完成"
}

create_initial_config() {
    log_info "创建初始配置..."
    
    # 创建默认配置文件
    cat > "$DATA_DIR/config.json" << EOF
{
    "version": "$CURRENT_VERSION",
    "web_port": $WEB_PORT,
    "web_host": "0.0.0.0",
    "language": "zh-CN",
    "theme": "auto",
    "auth": {
        "enabled": false,
        "username": "admin",
        "password": ""
    },
    "hysteria": {
        "bin_path": "$BIN_DIR/hysteria",
        "config_path": "/etc/hysteria2/client.yaml",
        "log_level": "info"
    },
    "system": {
        "auto_start": true,
        "auto_optimize": true,
        "check_update": true
    }
}
EOF
    
    # 创建空的节点列表
    cat > "$DATA_DIR/nodes.json" << EOF
{
    "nodes": [],
    "current": null,
    "subscriptions": []
}
EOF
    
    log_success "配置文件创建完成"
}

install_python_packages() {
    log_info "安装Python依赖包..."
    
    # 创建虚拟环境（可选，但推荐）
    if [[ ! -d "$INSTALL_DIR/venv" ]]; then
        python3 -m venv "$INSTALL_DIR/venv"
    fi
    
    # 安装依赖
    "$INSTALL_DIR/venv/bin/pip" install --upgrade pip
    "$INSTALL_DIR/venv/bin/pip" install flask flask-cors psutil pyyaml requests
    
    log_success "Python依赖安装完成"
}

create_systemd_services() {
    log_info "配置systemd服务..."
    
    # 创建管理器服务
    cat > "/etc/systemd/system/$SERVICE_NAME.service" << EOF
[Unit]
Description=Hysteria2 Manager WebUI Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/hysteria2_manager.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    
    # 创建Hysteria2客户端服务
    cat > "/etc/systemd/system/$CLIENT_SERVICE.service" << EOF
[Unit]
Description=Hysteria2 Client Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
ExecStart=$BIN_DIR/hysteria client -c /etc/hysteria2/client.yaml
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
CapabilityBoundingSet=CAP_NET_ADMIN CAP_NET_RAW CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_ADMIN CAP_NET_RAW CAP_NET_BIND_SERVICE

[Install]
WantedBy=multi-user.target
EOF
    
    # 重载systemd
    systemctl daemon-reload
    
    log_success "系统服务配置完成"
}

optimize_system() {
    log_info "优化系统参数..."
    
    # 创建sysctl配置
    cat > /etc/sysctl.d/99-hysteria2.conf << EOF
# Hysteria2 优化参数
net.ipv4.ip_forward = 1
net.ipv6.conf.all.forwarding = 1
net.ipv4.conf.default.rp_filter = 2
net.ipv4.conf.all.rp_filter = 2
net.core.default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr
net.ipv4.tcp_fastopen = 3
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
EOF
    
    # 应用配置
    sysctl -p /etc/sysctl.d/99-hysteria2.conf &> /dev/null
    
    # 配置防火墙（如果启用）
    if command -v ufw &> /dev/null && ufw status | grep -q "Status: active"; then
        log_info "配置UFW防火墙..."
        ufw allow $WEB_PORT/tcp comment 'Hysteria2 Manager WebUI'
        ufw reload
    fi
    
    if command -v firewall-cmd &> /dev/null && firewall-cmd --state &> /dev/null; then
        log_info "配置firewalld防火墙..."
        firewall-cmd --permanent --add-port=$WEB_PORT/tcp
        firewall-cmd --reload
    fi
    
    log_success "系统优化完成"
}

start_services() {
    log_info "启动服务..."
    
    # 启用并启动管理器服务
    systemctl enable "$SERVICE_NAME"
    systemctl restart "$SERVICE_NAME"
    
    # 等待服务启动
    sleep 3
    
    # 检查服务状态
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log_success "Hysteria2 Manager 服务启动成功"
    else
        log_error "Hysteria2 Manager 服务启动失败"
        echo "请查看日志: journalctl -u $SERVICE_NAME -n 50"
        exit 1
    fi
}

print_success_info() {
    echo
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}     Hysteria2 Manager 安装成功！${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo
    echo -e "${CYAN}访问地址:${NC}"
    
    # 获取服务器IP
    local ipv4=$(curl -s -4 ip.sb 2>/dev/null || echo "获取失败")
    local ipv6=$(curl -s -6 ip.sb 2>/dev/null || echo "")
    
    if [[ $ipv4 != "获取失败" ]]; then
        echo -e "  ${WHITE}http://$ipv4:$WEB_PORT${NC}"
    fi
    
    # 显示本地IP
    local local_ips=$(ip -4 addr show | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | grep -v '127.0.0.1')
    for ip in $local_ips; do
        echo -e "  ${WHITE}http://$ip:$WEB_PORT${NC} (局域网)"
    done
    
    if [[ -n $ipv6 ]]; then
        echo -e "  ${WHITE}http://[$ipv6]:$WEB_PORT${NC} (IPv6)"
    fi
    
    echo
    echo -e "${CYAN}管理命令:${NC}"
    echo -e "  ${WHITE}systemctl status $SERVICE_NAME${NC}  - 查看服务状态"
    echo -e "  ${WHITE}systemctl restart $SERVICE_NAME${NC} - 重启服务"
    echo -e "  ${WHITE}systemctl stop $SERVICE_NAME${NC}    - 停止服务"
    echo -e "  ${WHITE}journalctl -u $SERVICE_NAME -f${NC}  - 查看日志"
    echo
    echo -e "${CYAN}配置路径:${NC}"
    echo -e "  安装目录: ${WHITE}$INSTALL_DIR${NC}"
    echo -e "  配置文件: ${WHITE}$DATA_DIR/config.json${NC}"
    echo -e "  节点数据: ${WHITE}$DATA_DIR/nodes.json${NC}"
    echo
    echo -e "${YELLOW}提示:${NC}"
    echo -e "  1. 首次访问WebUI时，建议设置访问密码"
    echo -e "  2. 如需外网访问，请确保防火墙开放 $WEB_PORT 端口"
    echo -e "  3. 使用 ${WHITE}bash $0 uninstall${NC} 可以卸载"
    echo -e "${GREEN}========================================${NC}"
}

# ================== 卸载函数 ==================
uninstall() {
    print_logo
    echo -e "${RED}准备卸载 Hysteria2 Manager${NC}"
    echo
    
    if ! confirm "确定要卸载吗？所有配置将被删除" "n"; then
        echo "取消卸载"
        exit 0
    fi
    
    log_info "停止服务..."
    systemctl stop "$SERVICE_NAME" 2>/dev/null || true
    systemctl stop "$CLIENT_SERVICE" 2>/dev/null || true
    systemctl disable "$SERVICE_NAME" 2>/dev/null || true
    systemctl disable "$CLIENT_SERVICE" 2>/dev/null || true
    
    log_info "删除服务文件..."
    rm -f "/etc/systemd/system/$SERVICE_NAME.service"
    rm -f "/etc/systemd/system/$CLIENT_SERVICE.service"
    systemctl daemon-reload
    
    log_info "删除安装目录..."
    rm -rf "$INSTALL_DIR"
    
    log_info "删除Hysteria2核心..."
    rm -f "$BIN_DIR/hysteria"
    
    log_info "删除配置文件..."
    rm -rf "/etc/hysteria2"
    rm -f "/etc/sysctl.d/99-hysteria2.conf"
    
    log_success "卸载完成"
}

# ================== 更新函数 ==================
update() {
    print_logo
    echo -e "${BLUE}检查更新...${NC}"
    
    # 备份配置
    log_info "备份配置文件..."
    cp -r "$DATA_DIR" "$DATA_DIR.bak.$(date +%Y%m%d%H%M%S)"
    
    # 重新下载文件
    download_hysteria2
    download_manager_files
    
    # 重启服务
    systemctl restart "$SERVICE_NAME"
    
    log_success "更新完成"
}

# ================== 主函数 ==================
main() {
    case "${1:-}" in
        uninstall)
            uninstall
            ;;
        update)
            update
            ;;
        *)
            print_logo
            check_root
            detect_os
            
            # 检查是否已安装
            if [[ -d "$INSTALL_DIR" ]]; then
                log_warn "检测到已安装 Hysteria2 Manager"
                if confirm "是否重新安装？" "n"; then
                    uninstall
                else
                    echo "退出安装"
                    exit 0
                fi
            fi
            
            # 执行安装步骤
            check_dependencies
            download_hysteria2
            create_directories
            install_python_packages
            download_manager_files
            create_systemd_services
            optimize_system
            start_services
            print_success_info
            ;;
    esac
}

# 运行主函数
main "$@"

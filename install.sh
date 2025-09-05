#!/bin/bash

# Hysteria2 Manager v2.0 - 安装脚本
# 完全重构版本，修复所有已知问题，增加认证功能
# 项目地址: https://github.com/1439616687/hysteria2-manager

set -e

# ================== 配置变量 ==================
GITHUB_REPO="1439616687/hysteria2-manager"
INSTALL_DIR="/opt/hysteria2-manager"
DATA_DIR="$INSTALL_DIR/data"
SYSTEM_DIR="$INSTALL_DIR/system"
STATIC_DIR="$INSTALL_DIR/static"
BIN_DIR="/usr/local/bin"
SERVICE_NAME="hysteria2-manager"
CLIENT_SERVICE="hysteria2-client"
WEB_PORT=8080
CURRENT_VERSION="v2.0.0"

# ================== 颜色定义 ==================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

# ================== 工具函数 ==================
print_logo() {
    clear
    echo -e "${CYAN}"
    cat << "EOF"
    ╦ ╦┬ ┬┌─┐┌┬┐┌─┐┬─┐┬┌─┐╔═╗  ╔╦╗┌─┐┌┐┌┌─┐┌─┐┌─┐┬─┐
    ╠═╣└┬┘└─┐ │ ├┤ ├┬┘│├─┤╔═╝  ║║║├─┤│││├─┤│ ┬├┤ ├┬┘
    ╩ ╩ ┴ └─┘ ┴ └─┘┴└─┴┴ ┴╚═╝  ╩ ╩┴ ┴┘└┘┴ ┴└─┘└─┘┴└─
                    Version 2.0.0
EOF
    echo -e "${NC}"
    echo -e "${BLUE}══════════════════════════════════════════════════${NC}"
    echo -e "${WHITE}    Advanced Proxy Management System${NC}"
    echo -e "${BLUE}══════════════════════════════════════════════════${NC}"
    echo
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

spinner() {
    local pid=$1
    local delay=0.1
    local spinstr='⣾⣽⣻⢿⡿⣟⣯⣷'
    while [ "$(ps a | awk '{print $1}' | grep $pid)" ]; do
        local temp=${spinstr#?}
        printf " ${CYAN}%c${NC} " "$spinstr"
        local spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b"
    done
    printf "   \b\b\b"
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
    response=${response,,}
    
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
    
    # 必要的命令
    local required_commands="python3 curl wget systemctl"
    for cmd in $required_commands; do
        if ! command -v $cmd &> /dev/null; then
            case $cmd in
                python3) missing_deps+=("python3") ;;
                curl) missing_deps+=("curl") ;;
                wget) missing_deps+=("wget") ;;
                systemctl) 
                    log_error "系统不支持systemd"
                    exit 1
                    ;;
            esac
        fi
    done
    
    # 检查Python pip
    if ! python3 -m pip --version &> /dev/null 2>&1; then
        missing_deps+=("python3-pip")
    fi
    
    # 检查开发工具
    if ! command -v gcc &> /dev/null; then
        missing_deps+=("build-essential" "gcc")
    fi
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_info "安装缺失的依赖..."
        install_dependencies "${missing_deps[@]}"
    else
        log_success "所有依赖已满足"
    fi
}

install_dependencies() {
    case $OS in
        ubuntu|debian)
            apt-get update > /dev/null 2>&1 &
            spinner $!
            apt-get install -y python3 python3-pip python3-venv curl wget nano net-tools \
                               dnsutils iptables bc build-essential > /dev/null 2>&1 &
            spinner $!
            ;;
        centos|rhel|fedora|rocky|almalinux)
            yum install -y python3 python3-pip curl wget nano net-tools \
                          bind-utils iptables bc gcc make > /dev/null 2>&1 &
            spinner $!
            ;;
        arch|manjaro)
            pacman -Sy --noconfirm python python-pip curl wget nano net-tools \
                                  bind-tools iptables bc base-devel > /dev/null 2>&1 &
            spinner $!
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
    
    # 获取最新版本
    local latest_version=$(curl -s https://api.github.com/repos/apernet/hysteria/releases/latest | grep -Po '"tag_name": "\K.*?(?=")')
    
    if [[ -z "$latest_version" ]]; then
        log_warn "无法获取最新版本，使用默认版本"
        latest_version="v2.6.2"
    fi
    
    local download_url="https://github.com/apernet/hysteria/releases/download/${latest_version}/hysteria-linux-${ARCH_TYPE}"
    
    # 如果已存在，检查版本
    if [[ -f "$BIN_DIR/hysteria" ]]; then
        local current_version=$($BIN_DIR/hysteria version 2>&1 | grep -oP 'Version:\s*\K[v\d.]+' || echo "unknown")
        if [[ "$current_version" == "$latest_version" ]]; then
            log_success "Hysteria2已是最新版本 ($latest_version)"
            return
        fi
        log_info "更新Hysteria2: $current_version -> $latest_version"
    fi
    
    # 下载新版本
    wget -q --show-progress -O /tmp/hysteria "$download_url"
    
    if [[ ! -f /tmp/hysteria ]]; then
        log_error "下载失败"
        exit 1
    fi
    
    mv /tmp/hysteria "$BIN_DIR/hysteria"
    chmod +x "$BIN_DIR/hysteria"
    
    # 验证安装
    if $BIN_DIR/hysteria version &> /dev/null; then
        log_success "Hysteria2核心安装成功 ($latest_version)"
    else
        log_error "Hysteria2安装验证失败"
        exit 1
    fi
}

create_directories() {
    log_info "创建目录结构..."
    
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$DATA_DIR"
    mkdir -p "$SYSTEM_DIR"
    mkdir -p "$STATIC_DIR"
    mkdir -p "/var/log/hysteria2"
    mkdir -p "/etc/hysteria2"
    
    # 设置权限
    chmod 755 "$INSTALL_DIR"
    chmod 700 "$DATA_DIR"
    
    log_success "目录创建完成"
}

download_manager_files() {
    log_info "部署管理器文件..."
    
    # 这里应该从GitHub下载，但为了演示，我们将在后续步骤中创建文件
    # 实际部署时，这些文件应该已经在GitHub仓库中
    
    if [[ -f "hysteria2_manager.py" ]]; then
        cp hysteria2_manager.py "$INSTALL_DIR/"
    else
        # 从GitHub下载
        local base_url="https://raw.githubusercontent.com/$GITHUB_REPO/main"
        
        log_info "从GitHub下载核心文件..."
        curl -sL -o "$INSTALL_DIR/hysteria2_manager.py" "$base_url/hysteria2_manager.py" || {
            log_error "下载管理器主程序失败"
            exit 1
        }
    fi
    
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
    
    # 生成随机密钥
    local secret_key=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
    
    # 创建配置文件
    cat > "$DATA_DIR/config.json" << EOF
{
    "version": "$CURRENT_VERSION",
    "web_port": $WEB_PORT,
    "web_host": "0.0.0.0",
    "language": "zh-CN",
    "theme": "light",
    "secret_key": "$secret_key",
    "auth": {
        "enabled": true,
        "username": "admin",
        "password": "admin",
        "session_timeout": 3600
    },
    "hysteria": {
        "bin_path": "$BIN_DIR/hysteria",
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
EOF
    
    # 创建空的节点列表
    cat > "$DATA_DIR/nodes.json" << EOF
{
    "nodes": [],
    "current": null,
    "subscriptions": [],
    "groups": []
}
EOF
    
    # 创建用户数据文件
    cat > "$DATA_DIR/users.json" << EOF
{
    "users": [
        {
            "id": 1,
            "username": "admin",
            "password": "admin",
            "role": "admin",
            "created_at": "$(date -Iseconds)",
            "last_login": null,
            "status": "active"
        }
    ],
    "sessions": {}
}
EOF
    
    # 设置文件权限
    chmod 600 "$DATA_DIR"/*.json
    
    log_success "配置文件创建完成"
}

install_python_packages() {
    log_info "安装Python依赖包..."
    
    # 创建虚拟环境
    if [[ ! -d "$INSTALL_DIR/venv" ]]; then
        python3 -m venv "$INSTALL_DIR/venv"
    fi
    
    # 升级pip
    "$INSTALL_DIR/venv/bin/pip" install --upgrade pip > /dev/null 2>&1 &
    spinner $!
    
    # 安装依赖包
    local packages="flask flask-cors flask-login flask-session psutil pyyaml requests bcrypt"
    
    log_info "安装必要的Python包..."
    "$INSTALL_DIR/venv/bin/pip" install $packages > /dev/null 2>&1 &
    spinner $!
    
    log_success "Python依赖安装完成"
}

create_systemd_services() {
    log_info "配置systemd服务..."
    
    # 管理器服务
    cat > "/etc/systemd/system/$SERVICE_NAME.service" << EOF
[Unit]
Description=Hysteria2 Manager WebUI Service
Documentation=https://github.com/$GITHUB_REPO
After=network-online.target
Wants=network-online.target systemd-networkd-wait-online.service

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="PYTHONPATH=$INSTALL_DIR"
Environment="LANG=en_US.UTF-8"

ExecStartPre=/bin/bash -c 'test -f $DATA_DIR/config.json || exit 1'
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/hysteria2_manager.py
Restart=always
RestartSec=10
StartLimitInterval=120
StartLimitBurst=5

TimeoutStopSec=10
KillMode=mixed
KillSignal=SIGTERM

LimitNOFILE=65535
LimitNPROC=4096
NoNewPrivileges=false
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$DATA_DIR /var/log/hysteria2 /etc/hysteria2

StandardOutput=journal
StandardError=journal
SyslogIdentifier=$SERVICE_NAME

[Install]
WantedBy=multi-user.target
EOF
    
    # 客户端服务
    cat > "/etc/systemd/system/$CLIENT_SERVICE.service" << EOF
[Unit]
Description=Hysteria2 Client Service
Documentation=https://v2.hysteria.network/
After=network-online.target nss-lookup.target
Wants=network-online.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/etc/hysteria2

ExecStartPre=-/usr/sbin/ip link delete hytun 2>/dev/null
ExecStartPre=/bin/sleep 2
ExecStart=$BIN_DIR/hysteria client -c /etc/hysteria2/client.yaml
ExecStopPost=-/usr/sbin/ip link delete hytun 2>/dev/null

Restart=on-failure
RestartSec=10
StartLimitInterval=120
StartLimitBurst=5

TimeoutStartSec=30
TimeoutStopSec=10
KillMode=mixed
KillSignal=SIGTERM

LimitNOFILE=1048576
LimitNPROC=512
CapabilityBoundingSet=CAP_NET_ADMIN CAP_NET_RAW CAP_NET_BIND_SERVICE CAP_SYS_PTRACE CAP_DAC_READ_SEARCH
AmbientCapabilities=CAP_NET_ADMIN CAP_NET_RAW CAP_NET_BIND_SERVICE

NoNewPrivileges=false
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/etc/hysteria2 /var/log/hysteria2
PrivateDevices=no
DeviceAllow=/dev/net/tun rw

StandardOutput=journal
StandardError=journal
SyslogIdentifier=$CLIENT_SERVICE

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
# Hysteria2 Manager System Optimization
# Network Performance
net.ipv4.ip_forward = 1
net.ipv6.conf.all.forwarding = 1
net.ipv4.conf.default.rp_filter = 2
net.ipv4.conf.all.rp_filter = 2

# TCP Optimization
net.core.default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr
net.ipv4.tcp_fastopen = 3
net.ipv4.tcp_slow_start_after_idle = 0
net.ipv4.tcp_mtu_probing = 1

# Buffer Sizes
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.ipv4.tcp_rmem = 4096 87380 134217728
net.ipv4.tcp_wmem = 4096 65536 134217728
net.core.netdev_max_backlog = 5000

# Connection Tracking
net.netfilter.nf_conntrack_max = 65535
net.netfilter.nf_conntrack_tcp_timeout_established = 3600
EOF
    
    # 应用配置
    sysctl -p /etc/sysctl.d/99-hysteria2.conf > /dev/null 2>&1
    
    # 配置日志轮转
    cat > /etc/logrotate.d/hysteria2 << EOF
/var/log/hysteria2/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
    postrotate
        systemctl reload $CLIENT_SERVICE 2>/dev/null || true
        systemctl reload $SERVICE_NAME 2>/dev/null || true
    endscript
}
EOF
    
    # 配置防火墙（如果启用）
    if command -v ufw &> /dev/null && ufw status | grep -q "Status: active"; then
        log_info "配置UFW防火墙..."
        ufw allow $WEB_PORT/tcp comment 'Hysteria2 Manager WebUI' > /dev/null 2>&1
        ufw reload > /dev/null 2>&1
    fi
    
    if command -v firewall-cmd &> /dev/null && firewall-cmd --state &> /dev/null; then
        log_info "配置firewalld防火墙..."
        firewall-cmd --permanent --add-port=$WEB_PORT/tcp > /dev/null 2>&1
        firewall-cmd --reload > /dev/null 2>&1
    fi
    
    # 增加文件描述符限制
    if ! grep -q "* soft nofile 65535" /etc/security/limits.conf; then
        cat >> /etc/security/limits.conf << EOF
# Hysteria2 Manager Limits
* soft nofile 65535
* hard nofile 65535
root soft nofile 65535
root hard nofile 65535
EOF
    fi
    
    log_success "系统优化完成"
}

create_cli_tool() {
    log_info "创建命令行工具..."
    
    cat > "$BIN_DIR/hy2" << 'EOF'
#!/bin/bash

# Hysteria2 Manager CLI Tool v2.0

BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

case "$1" in
    status)
        echo -e "${BLUE}Hysteria2 Service Status:${NC}"
        systemctl status hysteria2-client --no-pager | head -15
        echo ""
        echo -e "${BLUE}Current IP:${NC} $(curl -s --max-time 3 http://ifconfig.io 2>/dev/null || echo "N/A")"
        echo -e "${BLUE}Location:${NC} $(curl -s --max-time 3 http://ifconfig.io/country_code 2>/dev/null || echo "N/A")"
        ;;
        
    start)
        sudo systemctl start hysteria2-client
        echo -e "${GREEN}Service started${NC}"
        ;;
        
    stop)
        sudo systemctl stop hysteria2-client
        echo -e "${RED}Service stopped${NC}"
        ;;
        
    restart)
        sudo systemctl restart hysteria2-client
        echo -e "${GREEN}Service restarted${NC}"
        ;;
        
    logs)
        sudo journalctl -u hysteria2-client -f
        ;;
        
    manager-logs)
        sudo journalctl -u hysteria2-manager -f
        ;;
        
    test)
        echo -e "${BLUE}Testing connection...${NC}"
        echo "IP: $(curl -s http://ifconfig.io)"
        echo "Location: $(curl -s http://ifconfig.io/country)"
        echo "ISP: $(curl -s http://ifconfig.io/asn)"
        ;;
        
    web)
        echo -e "${BLUE}WebUI Address:${NC} http://127.0.0.1:8080"
        echo -e "${BLUE}Default Login:${NC} admin / admin"
        ;;
        
    update)
        echo -e "${BLUE}Checking for updates...${NC}"
        bash <(curl -fsSL https://raw.githubusercontent.com/1439616687/hysteria2-manager/main/install.sh) update
        ;;
        
    *)
        echo "Hysteria2 Manager CLI v2.0"
        echo ""
        echo "Usage: hy2 {command}"
        echo ""
        echo "Commands:"
        echo "  status        - Show service status"
        echo "  start         - Start proxy service"
        echo "  stop          - Stop proxy service"
        echo "  restart       - Restart proxy service"
        echo "  logs          - Show client logs"
        echo "  manager-logs  - Show manager logs"
        echo "  test          - Test proxy connection"
        echo "  web           - Show WebUI address"
        echo "  update        - Check for updates"
        ;;
esac
EOF
    
    chmod +x "$BIN_DIR/hy2"
    
    log_success "命令行工具创建完成"
}

start_services() {
    log_info "启动服务..."
    
    # 启用服务
    systemctl enable "$SERVICE_NAME" > /dev/null 2>&1
    
    # 启动管理器服务
    systemctl restart "$SERVICE_NAME"
    
    # 等待服务启动
    sleep 3
    
    # 检查服务状态
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log_success "Hysteria2 Manager服务启动成功"
    else
        log_error "Hysteria2 Manager服务启动失败"
        echo "查看日志: journalctl -u $SERVICE_NAME -n 50"
        exit 1
    fi
}

print_success_info() {
    echo
    echo -e "${BLUE}══════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}     Hysteria2 Manager 安装成功！${NC}"
    echo -e "${BLUE}══════════════════════════════════════════════════${NC}"
    echo
    
    # 获取IP地址
    local ipv4=$(curl -s -4 ip.sb 2>/dev/null || ip -4 addr show | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | grep -v '127.0.0.1' | head -1)
    local ipv6=$(curl -s -6 ip.sb 2>/dev/null || echo "")
    
    echo -e "${CYAN}访问信息:${NC}"
    echo -e "  ${WHITE}本地访问:${NC} http://127.0.0.1:$WEB_PORT"
    if [[ -n $ipv4 ]]; then
        echo -e "  ${WHITE}远程访问:${NC} http://$ipv4:$WEB_PORT"
    fi
    if [[ -n $ipv6 ]]; then
        echo -e "  ${WHITE}IPv6访问:${NC} http://[$ipv6]:$WEB_PORT"
    fi
    echo
    
    echo -e "${CYAN}登录信息:${NC}"
    echo -e "  ${WHITE}用户名:${NC} admin"
    echo -e "  ${WHITE}密码:${NC} admin"
    echo -e "  ${YELLOW}请立即登录并修改默认密码！${NC}"
    echo
    
    echo -e "${CYAN}管理命令:${NC}"
    echo -e "  ${WHITE}hy2 status${NC}  - 查看服务状态"
    echo -e "  ${WHITE}hy2 test${NC}    - 测试代理连接"
    echo -e "  ${WHITE}hy2 logs${NC}    - 查看服务日志"
    echo -e "  ${WHITE}hy2 web${NC}     - 显示WebUI地址"
    echo
    
    echo -e "${CYAN}系统路径:${NC}"
    echo -e "  安装目录: ${WHITE}$INSTALL_DIR${NC}"
    echo -e "  配置文件: ${WHITE}$DATA_DIR/config.json${NC}"
    echo -e "  节点数据: ${WHITE}$DATA_DIR/nodes.json${NC}"
    echo
    
    echo -e "${BLUE}══════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}提示: 使用 ${WHITE}bash $0 uninstall${NC} ${GREEN}可以卸载${NC}"
    echo -e "${BLUE}══════════════════════════════════════════════════${NC}"
}

# ================== 卸载函数 ==================
uninstall() {
    print_logo
    echo -e "${RED}准备卸载 Hysteria2 Manager${NC}"
    echo
    
    if ! confirm "确定要卸载吗？所有配置和数据将被删除" "n"; then
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
    
    log_info "删除相关文件..."
    rm -f "$BIN_DIR/hysteria"
    rm -f "$BIN_DIR/hy2"
    rm -rf "/etc/hysteria2"
    rm -rf "/var/log/hysteria2"
    rm -f "/etc/sysctl.d/99-hysteria2.conf"
    rm -f "/etc/logrotate.d/hysteria2"
    
    log_success "卸载完成"
}

# ================== 更新函数 ==================
update() {
    print_logo
    echo -e "${BLUE}检查更新...${NC}"
    
    # 备份配置
    log_info "备份配置文件..."
    cp -r "$DATA_DIR" "$DATA_DIR.bak.$(date +%Y%m%d%H%M%S)"
    
    # 下载最新文件
    log_info "下载最新版本..."
    download_hysteria2
    download_manager_files
    
    # 重启服务
    log_info "重启服务..."
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
            if [[ -d "$INSTALL_DIR" ]] && [[ ! "${1:-}" == "force" ]]; then
                log_warn "检测到已安装 Hysteria2 Manager"
                echo
                echo "选项:"
                echo "  1) 重新安装"
                echo "  2) 更新"
                echo "  3) 卸载"
                echo "  4) 退出"
                echo
                read -p "请选择 [1-4]: " choice
                
                case $choice in
                    1)
                        log_info "开始重新安装..."
                        uninstall
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
                        echo "退出安装"
                        exit 0
                        ;;
                esac
            fi
            
            # 执行安装
            log_info "开始安装 Hysteria2 Manager v2.0..."
            
            check_dependencies
            download_hysteria2
            create_directories
            install_python_packages
            download_manager_files
            create_systemd_services
            optimize_system
            create_cli_tool
            start_services
            print_success_info
            ;;
    esac
}

# 捕获错误
trap 'log_error "安装过程中发生错误，请查看日志"; exit 1' ERR

# 运行主函数
main "$@"

#!/usr/bin/env bash
#
# Hysteria2 Manager 一键安装脚本
# 支持系统: Ubuntu 18+, Debian 9+, CentOS 7+, Fedora 30+, Arch Linux
# 
# 使用方法:
#   curl -fsSL https://raw.githubusercontent.com/yourusername/hysteria2-manager/main/install.sh | bash
#   或
#   wget -qO- https://raw.githubusercontent.com/yourusername/hysteria2-manager/main/install.sh | bash
#

set -e

# ======================== 颜色定义 ========================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
CLEAR='\033[0m'

# ======================== 配置变量 ========================
# 版本信息
SCRIPT_VERSION="1.0.0"
HYSTERIA_VERSION="latest"
MANAGER_VERSION="1.0.0"

# GitHub仓库地址（请修改为您的实际仓库）
GITHUB_REPO="yourusername/hysteria2-manager"
GITHUB_RAW_URL="https://raw.githubusercontent.com/${GITHUB_REPO}/main"

# 安装路径
INSTALL_DIR="/opt/hysteria2-manager"
BIN_DIR="/usr/local/bin"
SYSTEMD_DIR="/etc/systemd/system"
CONFIG_DIR="${INSTALL_DIR}/config"
DATA_DIR="${INSTALL_DIR}/data"
LOG_DIR="${DATA_DIR}/logs"

# 服务配置
SERVICE_NAME="hysteria2-manager"
HYSTERIA_SERVICE_NAME="hysteria-client"
DEFAULT_PORT="8088"
DEFAULT_HOST="0.0.0.0"

# 系统信息
OS=""
OS_VERSION=""
ARCH=""
PACKAGE_MANAGER=""
PYTHON_CMD=""
PIP_CMD=""

# ======================== 工具函数 ========================

# 打印带颜色的消息
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${CLEAR}"
}

# 打印标题
print_title() {
    echo ""
    echo -e "${PURPLE}========================================${CLEAR}"
    echo -e "${PURPLE}     $1${CLEAR}"
    echo -e "${PURPLE}========================================${CLEAR}"
    echo ""
}

# 打印成功消息
print_success() {
    print_message "${GREEN}" "✓ $1"
}

# 打印错误消息
print_error() {
    print_message "${RED}" "✗ $1"
}

# 打印警告消息
print_warning() {
    print_message "${YELLOW}" "⚠ $1"
}

# 打印信息消息
print_info() {
    print_message "${CYAN}" "ℹ $1"
}

# 错误处理
error_exit() {
    print_error "$1"
    exit 1
}

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 获取用户确认
get_confirmation() {
    local prompt="$1"
    local response
    
    while true; do
        read -p "$(echo -e ${CYAN}${prompt} [y/N]: ${CLEAR})" response
        case "$response" in
            [yY][eE][sS]|[yY]) 
                return 0
                ;;
            [nN][oO]|[nN]|"")
                return 1
                ;;
            *)
                print_warning "请输入 y 或 n"
                ;;
        esac
    done
}

# 生成随机密码
generate_password() {
    local length=${1:-16}
    if command_exists openssl; then
        openssl rand -base64 $length | tr -d "=+/" | cut -c1-$length
    else
        cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w $length | head -n 1
    fi
}

# 创建进度条
show_progress() {
    local duration=$1
    local message=$2
    local elapsed=0
    
    echo -n "$message "
    while [ $elapsed -lt $duration ]; do
        echo -n "."
        sleep 1
        elapsed=$((elapsed + 1))
    done
    echo " 完成"
}

# ======================== 系统检测函数 ========================

# 检测操作系统
detect_os() {
    print_info "检测操作系统..."
    
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$ID
        OS_VERSION=$VERSION_ID
    elif [[ -f /etc/redhat-release ]]; then
        OS="centos"
        OS_VERSION=$(rpm -E %{rhel})
    else
        error_exit "不支持的操作系统"
    fi
    
    # 转换为小写
    OS=${OS,,}
    
    # 处理衍生发行版
    case "$OS" in
        ubuntu|debian|raspbian)
            PACKAGE_MANAGER="apt-get"
            ;;
        centos|rhel|fedora|rocky|alma)
            PACKAGE_MANAGER="yum"
            if [[ "$OS_VERSION" -ge 8 ]] || [[ "$OS" == "fedora" ]]; then
                PACKAGE_MANAGER="dnf"
            fi
            ;;
        arch|manjaro)
            PACKAGE_MANAGER="pacman"
            ;;
        alpine)
            PACKAGE_MANAGER="apk"
            ;;
        *)
            error_exit "不支持的操作系统: $OS"
            ;;
    esac
    
    print_success "检测到系统: $OS $OS_VERSION"
}

# 检测系统架构
detect_architecture() {
    print_info "检测系统架构..."
    
    ARCH=$(uname -m)
    case "$ARCH" in
        x86_64|amd64)
            ARCH="amd64"
            ;;
        aarch64|arm64)
            ARCH="arm64"
            ;;
        armv7l|armv7)
            ARCH="armv7"
            ;;
        *)
            error_exit "不支持的架构: $ARCH"
            ;;
    esac
    
    print_success "系统架构: $ARCH"
}

# 检查是否为root用户
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error_exit "此脚本必须以root权限运行，请使用 sudo 或切换到root用户"
    fi
}

# 检查系统要求
check_requirements() {
    print_info "检查系统要求..."
    
    # 检查内存
    local total_mem=$(free -m | awk 'NR==2{print $2}')
    if [[ $total_mem -lt 256 ]]; then
        print_warning "系统内存较低 (${total_mem}MB)，可能影响性能"
    fi
    
    # 检查磁盘空间
    local available_space=$(df -m / | awk 'NR==2{print $4}')
    if [[ $available_space -lt 500 ]]; then
        error_exit "磁盘空间不足 (需要至少500MB，当前${available_space}MB)"
    fi
    
    # 检查网络连接
    print_info "检查网络连接..."
    if ! ping -c 1 -W 3 google.com >/dev/null 2>&1 && \
       ! ping -c 1 -W 3 8.8.8.8 >/dev/null 2>&1; then
        print_warning "网络连接可能存在问题"
    fi
    
    print_success "系统要求检查通过"
}

# ======================== 安装函数 ========================

# 更新包管理器
update_package_manager() {
    print_info "更新软件包列表..."
    
    case "$PACKAGE_MANAGER" in
        apt-get)
            apt-get update -qq
            ;;
        yum|dnf)
            $PACKAGE_MANAGER makecache -q
            ;;
        pacman)
            pacman -Sy --noconfirm >/dev/null 2>&1
            ;;
        apk)
            apk update >/dev/null 2>&1
            ;;
    esac
    
    print_success "软件包列表已更新"
}

# 安装基础依赖
install_dependencies() {
    print_info "安装系统依赖..."
    
    local packages=""
    
    # 通用依赖
    case "$PACKAGE_MANAGER" in
        apt-get)
            packages="curl wget git python3 python3-pip python3-venv ca-certificates gnupg lsb-release"
            DEBIAN_FRONTEND=noninteractive apt-get install -y $packages >/dev/null 2>&1
            ;;
        yum|dnf)
            packages="curl wget git python3 python3-pip ca-certificates"
            $PACKAGE_MANAGER install -y $packages >/dev/null 2>&1
            ;;
        pacman)
            packages="curl wget git python python-pip ca-certificates"
            pacman -S --noconfirm $packages >/dev/null 2>&1
            ;;
        apk)
            packages="curl wget git python3 py3-pip ca-certificates"
            apk add --no-cache $packages >/dev/null 2>&1
            ;;
    esac
    
    print_success "系统依赖安装完成"
}

# 安装Python依赖
install_python_dependencies() {
    print_info "安装Python依赖..."
    
    # 检测Python版本
    if command_exists python3; then
        PYTHON_CMD="python3"
    elif command_exists python; then
        PYTHON_CMD="python"
    else
        error_exit "未找到Python，请先安装Python 3.7+"
    fi
    
    # 检测pip
    if command_exists pip3; then
        PIP_CMD="pip3"
    elif command_exists pip; then
        PIP_CMD="pip"
    else
        print_warning "未找到pip，尝试安装..."
        curl -sS https://bootstrap.pypa.io/get-pip.py | $PYTHON_CMD
        PIP_CMD="pip"
    fi
    
    # 升级pip
    $PIP_CMD install --upgrade pip >/dev/null 2>&1
    
    # 安装Python包
    print_info "安装Python包..."
    $PIP_CMD install flask flask-cors pyyaml requests >/dev/null 2>&1
    
    print_success "Python依赖安装完成"
}

# 下载并安装Hysteria2
install_hysteria2() {
    print_info "安装Hysteria2核心..."
    
    local download_url="https://download.hysteria.network/app/latest/hysteria-linux-${ARCH}"
    local hysteria_bin="${BIN_DIR}/hysteria"
    
    # 备份旧版本
    if [[ -f "$hysteria_bin" ]]; then
        print_info "备份现有版本..."
        mv "$hysteria_bin" "${hysteria_bin}.bak"
    fi
    
    # 下载Hysteria2
    print_info "下载Hysteria2..."
    if ! curl -fsSL "$download_url" -o "$hysteria_bin"; then
        # 恢复备份
        [[ -f "${hysteria_bin}.bak" ]] && mv "${hysteria_bin}.bak" "$hysteria_bin"
        error_exit "下载Hysteria2失败"
    fi
    
    # 设置权限
    chmod +x "$hysteria_bin"
    
    # 验证安装
    if ! $hysteria_bin version >/dev/null 2>&1; then
        error_exit "Hysteria2安装验证失败"
    fi
    
    local version=$($hysteria_bin version 2>/dev/null | head -1)
    print_success "Hysteria2安装成功: $version"
}

# 下载管理程序文件
download_manager_files() {
    print_info "下载管理程序..."
    
    # 创建目录
    mkdir -p "$INSTALL_DIR" "$CONFIG_DIR" "$DATA_DIR" "$LOG_DIR"
    
    # 下载文件
    local files=("hysteria2_manager.py" "webui.html")
    
    for file in "${files[@]}"; do
        print_info "下载 $file..."
        
        # 首先尝试从GitHub下载
        if curl -fsSL "${GITHUB_RAW_URL}/${file}" -o "${INSTALL_DIR}/${file}" 2>/dev/null; then
            print_success "$file 下载成功"
        else
            # 如果GitHub下载失败，检查本地文件
            if [[ -f "./${file}" ]]; then
                print_info "使用本地文件 $file"
                cp "./${file}" "${INSTALL_DIR}/${file}"
            else
                error_exit "无法下载 $file"
            fi
        fi
    done
    
    # 设置权限
    chmod +x "${INSTALL_DIR}/hysteria2_manager.py"
    chmod 644 "${INSTALL_DIR}/webui.html"
    
    print_success "管理程序下载完成"
}

# 创建systemd服务
create_systemd_services() {
    print_info "创建系统服务..."
    
    # Hysteria2 Manager服务
    cat > "${SYSTEMD_DIR}/${SERVICE_NAME}.service" << EOF
[Unit]
Description=Hysteria2 Manager Web Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${INSTALL_DIR}
ExecStart=${PYTHON_CMD} ${INSTALL_DIR}/hysteria2_manager.py
Restart=always
RestartSec=10
StandardOutput=append:${LOG_DIR}/manager.log
StandardError=append:${LOG_DIR}/manager_error.log

[Install]
WantedBy=multi-user.target
EOF

    # Hysteria2客户端服务
    cat > "${SYSTEMD_DIR}/${HYSTERIA_SERVICE_NAME}.service" << EOF
[Unit]
Description=Hysteria2 Client Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
ExecStart=${BIN_DIR}/hysteria client -c ${DATA_DIR}/hysteria.yaml
ExecStartPre=/bin/sleep 2
ExecStartPre=/bin/sh -c 'ip link delete hytun 2>/dev/null || true'
ExecStopPost=/bin/sh -c 'ip link delete hytun 2>/dev/null || true'
Restart=always
RestartSec=10
LimitNOFILE=65535
CapabilityBoundingSet=CAP_NET_ADMIN CAP_NET_RAW CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_ADMIN CAP_NET_RAW CAP_NET_BIND_SERVICE
StandardOutput=append:${LOG_DIR}/hysteria.log
StandardError=append:${LOG_DIR}/hysteria_error.log

[Install]
WantedBy=multi-user.target
EOF

    # 重载systemd
    systemctl daemon-reload
    
    # 启用服务
    systemctl enable "${SERVICE_NAME}.service" >/dev/null 2>&1
    
    print_success "系统服务创建成功"
}

# 系统优化
optimize_system() {
    print_info "优化系统配置..."
    
    # 创建sysctl配置
    cat > /etc/sysctl.d/99-hysteria2.conf << EOF
# Hysteria2 优化配置
# 网络优化
net.ipv4.ip_forward = 1
net.ipv6.conf.all.forwarding = 1

# 反向路径过滤
net.ipv4.conf.default.rp_filter = 2
net.ipv4.conf.all.rp_filter = 2

# TCP优化
net.core.default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr
net.ipv4.tcp_fastopen = 3

# 连接数优化
net.core.somaxconn = 65535
net.netfilter.nf_conntrack_max = 65535

# 缓冲区优化
net.core.rmem_max = 67108864
net.core.wmem_max = 67108864
net.ipv4.tcp_rmem = 4096 87380 67108864
net.ipv4.tcp_wmem = 4096 65536 67108864

# 文件描述符
fs.file-max = 1000000
EOF

    # 应用配置
    sysctl -p /etc/sysctl.d/99-hysteria2.conf >/dev/null 2>&1
    
    # 设置ulimit
    cat >> /etc/security/limits.conf << EOF
* soft nofile 1000000
* hard nofile 1000000
* soft nproc 65535
* hard nproc 65535
EOF

    print_success "系统优化完成"
}

# 配置防火墙
configure_firewall() {
    print_info "配置防火墙..."
    
    # 检测并配置防火墙
    if command_exists firewall-cmd; then
        # firewalld
        firewall-cmd --permanent --add-port=${DEFAULT_PORT}/tcp >/dev/null 2>&1
        firewall-cmd --permanent --zone=trusted --add-interface=hytun >/dev/null 2>&1
        firewall-cmd --reload >/dev/null 2>&1
        print_success "firewalld配置完成"
    elif command_exists ufw; then
        # ufw
        ufw allow ${DEFAULT_PORT}/tcp >/dev/null 2>&1
        print_success "ufw配置完成"
    elif command_exists iptables; then
        # iptables
        iptables -I INPUT -p tcp --dport ${DEFAULT_PORT} -j ACCEPT
        iptables -I INPUT -i hytun -j ACCEPT
        iptables -I FORWARD -i hytun -j ACCEPT
        iptables -I FORWARD -o hytun -j ACCEPT
        
        # 保存规则
        if command_exists iptables-save; then
            iptables-save > /etc/iptables/rules.v4 2>/dev/null || \
            iptables-save > /etc/sysconfig/iptables 2>/dev/null
        fi
        print_success "iptables配置完成"
    else
        print_warning "未检测到防火墙，请手动开放端口 ${DEFAULT_PORT}"
    fi
}

# 启动服务
start_services() {
    print_info "启动服务..."
    
    # 启动管理面板
    systemctl start "${SERVICE_NAME}.service"
    
    # 等待服务启动
    sleep 3
    
    # 检查服务状态
    if systemctl is-active --quiet "${SERVICE_NAME}.service"; then
        print_success "Hysteria2 Manager 启动成功"
    else
        print_warning "Hysteria2 Manager 启动失败，请检查日志"
    fi
}

# 生成初始配置
generate_initial_config() {
    print_info "生成初始配置..."
    
    # 创建示例节点配置
    cat > "${DATA_DIR}/nodes.json" << EOF
[]
EOF

    # 设置文件权限
    chmod 600 "${CONFIG_DIR}"/*
    chmod 644 "${DATA_DIR}"/*
    
    print_success "初始配置生成完成"
}

# ======================== 卸载函数 ========================

uninstall() {
    print_title "卸载 Hysteria2 Manager"
    
    if ! get_confirmation "确定要卸载 Hysteria2 Manager 吗？"; then
        print_info "取消卸载"
        exit 0
    fi
    
    print_info "停止服务..."
    systemctl stop "${SERVICE_NAME}.service" 2>/dev/null || true
    systemctl stop "${HYSTERIA_SERVICE_NAME}.service" 2>/dev/null || true
    
    print_info "禁用服务..."
    systemctl disable "${SERVICE_NAME}.service" 2>/dev/null || true
    systemctl disable "${HYSTERIA_SERVICE_NAME}.service" 2>/dev/null || true
    
    print_info "删除服务文件..."
    rm -f "${SYSTEMD_DIR}/${SERVICE_NAME}.service"
    rm -f "${SYSTEMD_DIR}/${HYSTERIA_SERVICE_NAME}.service"
    systemctl daemon-reload
    
    print_info "删除程序文件..."
    rm -rf "${INSTALL_DIR}"
    rm -f "${BIN_DIR}/hysteria"
    
    print_info "删除系统配置..."
    rm -f /etc/sysctl.d/99-hysteria2.conf
    
    print_success "卸载完成"
}

# ======================== 升级函数 ========================

upgrade() {
    print_title "升级 Hysteria2 Manager"
    
    # 备份配置
    print_info "备份配置..."
    cp -r "${CONFIG_DIR}" "${CONFIG_DIR}.bak"
    cp -r "${DATA_DIR}" "${DATA_DIR}.bak"
    
    # 停止服务
    print_info "停止服务..."
    systemctl stop "${SERVICE_NAME}.service"
    
    # 下载新版本
    download_manager_files
    
    # 安装新版Hysteria2
    install_hysteria2
    
    # 重启服务
    print_info "重启服务..."
    systemctl start "${SERVICE_NAME}.service"
    
    print_success "升级完成"
}

# ======================== 显示安装信息 ========================

show_installation_info() {
    local ip_addr=$(ip -4 addr show | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | grep -v '127.0.0.1' | head -1)
    
    # 获取初始密码
    local init_password=""
    if [[ -f "${LOG_DIR}/manager.log" ]]; then
        init_password=$(grep "初始密码" "${LOG_DIR}/manager.log" | tail -1 | awk -F': ' '{print $2}')
    fi
    
    print_title "安装完成"
    
    echo -e "${GREEN}Hysteria2 Manager 安装成功！${CLEAR}"
    echo ""
    echo -e "${CYAN}访问地址:${CLEAR} http://${ip_addr}:${DEFAULT_PORT}"
    echo -e "${CYAN}本地访问:${CLEAR} http://127.0.0.1:${DEFAULT_PORT}"
    echo ""
    echo -e "${CYAN}默认用户名:${CLEAR} admin"
    
    if [[ -n "$init_password" ]]; then
        echo -e "${CYAN}初始密码:${CLEAR} ${init_password}"
    else
        echo -e "${YELLOW}请查看日志获取初始密码:${CLEAR}"
        echo "  cat ${LOG_DIR}/manager.log | grep '初始密码'"
    fi
    
    echo ""
    echo -e "${PURPLE}管理命令:${CLEAR}"
    echo "  systemctl start ${SERVICE_NAME}       # 启动管理面板"
    echo "  systemctl stop ${SERVICE_NAME}        # 停止管理面板"
    echo "  systemctl restart ${SERVICE_NAME}     # 重启管理面板"
    echo "  systemctl status ${SERVICE_NAME}      # 查看状态"
    echo "  journalctl -u ${SERVICE_NAME} -f      # 查看日志"
    echo ""
    echo -e "${PURPLE}文件位置:${CLEAR}"
    echo "  安装目录: ${INSTALL_DIR}"
    echo "  配置目录: ${CONFIG_DIR}"
    echo "  数据目录: ${DATA_DIR}"
    echo "  日志目录: ${LOG_DIR}"
    echo ""
    echo -e "${GREEN}请访问Web界面完成初始配置${CLEAR}"
    echo ""
}

# ======================== 主函数 ========================

main() {
    # 解析命令行参数
    case "${1:-}" in
        uninstall)
            uninstall
            exit 0
            ;;
        upgrade)
            upgrade
            exit 0
            ;;
    esac
    
    # 显示欢迎信息
    clear
    cat << "EOF"
    _   _           _            _      ____  
   | | | |_   _ ___| |_ ___ _ __(_) __ |___ \ 
   | |_| | | | / __| __/ _ \ '__| |/ _` |__) |
   |  _  | |_| \__ \ ||  __/ |  | | (_| |/ __/ 
   |_| |_|\__, |___/\__\___|_|  |_|\__,_|_____|
          |___/     Manager v1.0.0
   
EOF
    
    print_info "开始安装 Hysteria2 Manager..."
    echo ""
    
    # 检查root权限
    check_root
    
    # 检测系统
    detect_os
    detect_architecture
    check_requirements
    
    # 确认安装
    echo ""
    print_info "即将安装以下组件:"
    echo "  - Hysteria2 核心程序"
    echo "  - Hysteria2 Manager 管理面板"
    echo "  - 系统服务和自启动配置"
    echo ""
    
    if ! get_confirmation "是否继续安装？"; then
        print_info "安装已取消"
        exit 0
    fi
    
    # 执行安装
    print_title "开始安装"
    
    # 更新系统包
    update_package_manager
    
    # 安装依赖
    install_dependencies
    install_python_dependencies
    
    # 安装Hysteria2
    install_hysteria2
    
    # 下载管理程序
    download_manager_files
    
    # 创建服务
    create_systemd_services
    
    # 系统优化
    optimize_system
    
    # 配置防火墙
    configure_firewall
    
    # 生成配置
    generate_initial_config
    
    # 启动服务
    start_services
    
    # 显示安装信息
    show_installation_info
}

# ======================== 错误处理 ========================

# 捕获错误
trap 'error_exit "安装过程中发生错误，请查看日志"' ERR

# 捕获退出信号
trap 'print_warning "安装被中断"; exit 1' INT TERM

# ======================== 执行安装 ========================

main "$@"

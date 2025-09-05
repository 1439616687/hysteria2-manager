#!/bin/bash
#
# Hysteria2 WebUI Manager - 一键安装脚本
# 项目地址: https://github.com/yourusername/hysteria2-webui-manager
#
# 使用方法:
# bash <(curl -fsSL https://raw.githubusercontent.com/yourusername/hysteria2-webui-manager/main/install.sh)

set -e

# 定义颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 全局变量
INSTALL_DIR="/opt/hysteria2-webui"
SERVICE_NAME="hysteria2-webui"
HYSTERIA_VERSION="latest"
WEBUI_PORT="8080"

# 打印带颜色的消息
print_message() {
    echo -e "${2}${1}${NC}"
}

# 检查是否为root用户
check_root() {
    if [ "$EUID" -ne 0 ]; then 
        print_message "错误：请使用root权限运行此脚本" "$RED"
        print_message "提示：使用 'sudo bash' 或 'sudo su -' 运行" "$YELLOW"
        exit 1
    fi
}

# 检测系统信息
detect_system() {
    print_message "正在检测系统信息..." "$BLUE"
    
    # 检测操作系统
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
        print_message "操作系统: $OS $VER" "$GREEN"
    fi
    
    # 检测架构
    ARCH=$(uname -m)
    case "$ARCH" in
        x86_64|amd64)
            ARCH_TYPE="amd64"
            ;;
        aarch64|arm64)
            ARCH_TYPE="arm64"
            ;;
        *)
            print_message "不支持的系统架构: $ARCH" "$RED"
            exit 1
            ;;
    esac
    print_message "系统架构: $ARCH_TYPE" "$GREEN"
}

# 安装依赖
install_dependencies() {
    print_message "安装系统依赖..." "$BLUE"
    
    # 更新包管理器
    if command -v apt-get &> /dev/null; then
        apt-get update
        apt-get install -y python3 python3-pip python3-venv curl wget git nano
    elif command -v yum &> /dev/null; then
        yum update -y
        yum install -y python3 python3-pip curl wget git nano
    elif command -v dnf &> /dev/null; then
        dnf update -y
        dnf install -y python3 python3-pip curl wget git nano
    else
        print_message "不支持的包管理器，请手动安装依赖" "$RED"
        exit 1
    fi
}

# 下载并安装Hysteria2核心
install_hysteria2_core() {
    print_message "下载Hysteria2核心..." "$BLUE"
    
    # 创建目录
    mkdir -p /usr/local/bin
    
    # 下载Hysteria2
    DOWNLOAD_URL="https://download.hysteria.network/app/${HYSTERIA_VERSION}/hysteria-linux-${ARCH_TYPE}"
    curl -fsSL -o /usr/local/bin/hysteria "$DOWNLOAD_URL"
    chmod +x /usr/local/bin/hysteria
    
    # 验证安装
    if /usr/local/bin/hysteria version &> /dev/null; then
        print_message "✓ Hysteria2核心安装成功" "$GREEN"
        /usr/local/bin/hysteria version
    else
        print_message "Hysteria2核心安装失败" "$RED"
        exit 1
    fi
}

# 安装WebUI管理界面
install_webui() {
    print_message "安装WebUI管理界面..." "$BLUE"
    
    # 创建安装目录
    mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    
    # 如果是从GitHub安装，克隆仓库
    if [ -z "$LOCAL_INSTALL" ]; then
        git clone https://github.com/yourusername/hysteria2-webui-manager.git .
    fi
    
    # 创建Python虚拟环境
    python3 -m venv venv
    source venv/bin/activate
    
    # 安装Python依赖
    pip install --upgrade pip
    pip install flask flask-cors psutil pyyaml requests
    
    print_message "✓ WebUI安装完成" "$GREEN"
}

# 创建系统服务
create_service() {
    print_message "创建系统服务..." "$BLUE"
    
    # 创建Hysteria2服务
    cat > /etc/systemd/system/hysteria2.service <<EOF
[Unit]
Description=Hysteria2 Client Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/hysteria client -c /etc/hysteria2/client.yaml
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    # 创建WebUI服务
    cat > /etc/systemd/system/${SERVICE_NAME}.service <<EOF
[Unit]
Description=Hysteria2 WebUI Manager
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${INSTALL_DIR}
Environment="PATH=${INSTALL_DIR}/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=${INSTALL_DIR}/venv/bin/python ${INSTALL_DIR}/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # 重载systemd
    systemctl daemon-reload
    systemctl enable ${SERVICE_NAME}
}

# 配置防火墙
configure_firewall() {
    print_message "配置防火墙规则..." "$BLUE"
    
    # 检测并配置防火墙
    if command -v ufw &> /dev/null; then
        ufw allow ${WEBUI_PORT}/tcp comment 'Hysteria2 WebUI'
    elif command -v firewall-cmd &> /dev/null; then
        firewall-cmd --permanent --add-port=${WEBUI_PORT}/tcp
        firewall-cmd --reload
    fi
}

# 初始化配置
initialize_config() {
    print_message "初始化配置..." "$BLUE"
    
    # 创建配置目录
    mkdir -p /etc/hysteria2
    mkdir -p ${INSTALL_DIR}/config
    
    # 创建默认配置
    cat > ${INSTALL_DIR}/config/settings.json <<EOF
{
    "webui": {
        "port": ${WEBUI_PORT},
        "host": "0.0.0.0",
        "username": "admin",
        "password": "$(openssl rand -base64 12)"
    },
    "hysteria2": {
        "config_path": "/etc/hysteria2/client.yaml",
        "binary_path": "/usr/local/bin/hysteria",
        "log_path": "/var/log/hysteria2.log"
    }
}
EOF

    # 保存配置信息
    print_message "================================" "$GREEN"
    print_message "WebUI访问信息:" "$GREEN"
    print_message "地址: http://$(curl -s ifconfig.io 2>/dev/null || echo "YOUR_SERVER_IP"):${WEBUI_PORT}" "$YELLOW"
    print_message "用户名: admin" "$YELLOW"
    print_message "密码: $(grep -oP '"password": "\K[^"]+' ${INSTALL_DIR}/config/settings.json)" "$YELLOW"
    print_message "================================" "$GREEN"
}

# 主安装流程
main() {
    clear
    print_message "=====================================" "$BLUE"
    print_message "   Hysteria2 WebUI Manager 安装脚本  " "$BLUE"
    print_message "=====================================" "$BLUE"
    echo
    
    check_root
    detect_system
    install_dependencies
    install_hysteria2_core
    install_webui
    create_service
    configure_firewall
    initialize_config
    
    # 启动服务
    print_message "启动服务..." "$BLUE"
    systemctl start ${SERVICE_NAME}
    
    print_message "\n✓ 安装完成！" "$GREEN"
    print_message "\n管理命令:" "$YELLOW"
    print_message "  systemctl status ${SERVICE_NAME}  # 查看服务状态" "$NC"
    print_message "  systemctl restart ${SERVICE_NAME} # 重启服务" "$NC"
    print_message "  journalctl -u ${SERVICE_NAME} -f  # 查看日志" "$NC"
    echo
}

# 如果直接运行脚本，执行主函数
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi

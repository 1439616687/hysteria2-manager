#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hysteria2 Manager - 一个轻量级的Hysteria2管理工具
作者: Hysteria2 Manager Contributors
版本: 1.0.0
描述: 提供Web界面管理Hysteria2代理服务，支持节点管理、配置生成、服务控制等功能
"""

import os
import sys
import json
import yaml
import time
import subprocess
import socket
import hashlib
import secrets
import logging
import signal
import threading
import re
import base64
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from functools import wraps
from collections import deque

# Flask相关导入
from flask import Flask, request, jsonify, send_file, render_template_string
from flask_cors import CORS
import requests

# ======================== 配置常量 ========================

# 应用配置
APP_NAME = "Hysteria2 Manager"
APP_VERSION = "1.0.0"
DEFAULT_PORT = 8088
DEFAULT_HOST = "0.0.0.0"  # 监听所有接口，生产环境建议改为127.0.0.1

# 路径配置
BASE_DIR = Path(__file__).parent.absolute()
CONFIG_DIR = BASE_DIR / "config"
DATA_DIR = BASE_DIR / "data"
LOG_DIR = DATA_DIR / "logs"

# 确保必要目录存在
for dir_path in [CONFIG_DIR, DATA_DIR, LOG_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# 文件路径
SETTINGS_FILE = CONFIG_DIR / "settings.json"
NODES_FILE = DATA_DIR / "nodes.json"
HYSTERIA_CONFIG = DATA_DIR / "hysteria.yaml"
AUTH_FILE = CONFIG_DIR / "auth.json"
STATS_FILE = DATA_DIR / "stats.json"
LOG_FILE = LOG_DIR / "app.log"

# Hysteria2相关路径
HYSTERIA_BIN = Path("/usr/local/bin/hysteria")
HYSTERIA_SERVICE = "hysteria-client"
SYSTEMD_SERVICE_FILE = Path(f"/etc/systemd/system/{HYSTERIA_SERVICE}.service")

# ======================== 日志配置 ========================

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ======================== 数据模型 ========================

@dataclass
class Node:
    """节点数据模型"""
    id: str
    name: str
    server: str
    port: int
    password: str
    sni: Optional[str] = None
    insecure: bool = False
    protocol: str = "hysteria2"
    created_at: str = ""
    updated_at: str = ""
    enabled: bool = True
    remark: Optional[str] = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        if not self.id:
            self.id = hashlib.md5(f"{self.server}:{self.port}".encode()).hexdigest()[:8]

@dataclass
class SystemStatus:
    """系统状态数据模型"""
    hysteria_running: bool
    hysteria_version: str
    tun_interface: bool
    cpu_usage: float
    memory_usage: float
    network_stats: Dict[str, Any]
    uptime: int
    last_error: Optional[str] = None

# ======================== 工具函数 ========================

class Utils:
    """工具函数集合"""
    
    @staticmethod
    def run_command(cmd: List[str], check: bool = True, capture_output: bool = True) -> Tuple[int, str, str]:
        """执行系统命令"""
        try:
            result = subprocess.run(
                cmd,
                check=check,
                capture_output=capture_output,
                text=True
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            return e.returncode, e.stdout or "", e.stderr or ""
        except Exception as e:
            logger.error(f"命令执行失败: {e}")
            return -1, "", str(e)
    
    @staticmethod
    def parse_hysteria_url(url: str) -> Optional[Dict[str, Any]]:
        """解析Hysteria2节点URL"""
        try:
            # 解码URL
            decoded_url = urllib.parse.unquote(url)
            
            # 匹配Hysteria2 URL格式
            # hysteria2://password@server:port/?sni=xxx&insecure=1
            # hy2://password@server:port/?sni=xxx
            pattern = r'^(hysteria2?|hy2)://([^@]+)@([^:]+):(\d+)(/?\?(.+))?$'
            match = re.match(pattern, decoded_url)
            
            if not match:
                return None
            
            protocol = match.group(1)
            password = match.group(2)
            server = match.group(3)
            port = int(match.group(4))
            params_str = match.group(6)
            
            # 解析参数
            params = {}
            if params_str:
                params = urllib.parse.parse_qs(params_str)
            
            return {
                'protocol': 'hysteria2' if protocol in ['hysteria2', 'hy2'] else protocol,
                'server': server,
                'port': port,
                'password': password,
                'sni': params.get('sni', [server])[0],
                'insecure': params.get('insecure', ['0'])[0] == '1'
            }
        except Exception as e:
            logger.error(f"解析URL失败: {e}")
            return None
    
    @staticmethod
    def generate_hysteria_config(node: Node) -> str:
        """生成Hysteria2配置文件"""
        config = {
            'server': f"{node.server}:{node.port}",
            'auth': node.password,
            'tls': {
                'sni': node.sni or node.server,
                'insecure': node.insecure
            },
            'tun': {
                'name': 'hytun',
                'mtu': 1500,
                'timeout': '5m',
                'route': {
                    'ipv4': ['0.0.0.0/0'],
                    'ipv6': ['2000::/3'],
                    'ipv4Exclude': [
                        f"{node.server}/32",  # 排除服务器IP
                        '127.0.0.0/8',
                        '10.0.0.0/8',
                        '172.16.0.0/12',
                        '192.168.0.0/16',
                        '224.0.0.0/4',
                        '240.0.0.0/4',
                        '169.254.0.0/16'
                    ]
                }
            },
            'bandwidth': {
                'up': '100 mbps',
                'down': '100 mbps'
            }
        }
        
        return yaml.dump(config, default_flow_style=False, allow_unicode=True)
    
    @staticmethod
    def get_network_stats() -> Dict[str, Any]:
        """获取网络统计信息"""
        stats = {
            'rx_bytes': 0,
            'tx_bytes': 0,
            'rx_packets': 0,
            'tx_packets': 0,
            'interface': 'hytun'
        }
        
        try:
            # 读取网络接口统计
            cmd = ["ip", "-s", "link", "show", "hytun"]
            returncode, stdout, _ = Utils.run_command(cmd, check=False)
            
            if returncode == 0 and stdout:
                lines = stdout.split('\n')
                for i, line in enumerate(lines):
                    if 'RX:' in line and i + 1 < len(lines):
                        rx_stats = lines[i + 1].split()
                        if len(rx_stats) >= 2:
                            stats['rx_bytes'] = int(rx_stats[0])
                            stats['rx_packets'] = int(rx_stats[1])
                    elif 'TX:' in line and i + 1 < len(lines):
                        tx_stats = lines[i + 1].split()
                        if len(tx_stats) >= 2:
                            stats['tx_bytes'] = int(tx_stats[0])
                            stats['tx_packets'] = int(tx_stats[1])
        except Exception as e:
            logger.error(f"获取网络统计失败: {e}")
        
        return stats
    
    @staticmethod
    def test_connectivity() -> Dict[str, Any]:
        """测试网络连接"""
        results = {
            'dns': False,
            'http': False,
            'https': False,
            'ip': None,
            'country': None
        }
        
        try:
            # 测试DNS
            socket.gethostbyname('google.com')
            results['dns'] = True
            
            # 测试HTTP/HTTPS和获取IP
            response = requests.get('https://ifconfig.io/json', timeout=5)
            if response.status_code == 200:
                results['https'] = True
                data = response.json()
                results['ip'] = data.get('ip')
                results['country'] = data.get('country_code')
            
            # 测试HTTP
            response = requests.get('http://www.google.com/generate_204', timeout=5)
            results['http'] = response.status_code == 204
            
        except Exception as e:
            logger.error(f"连接测试失败: {e}")
        
        return results

# ======================== 核心管理类 ========================

class Hysteria2Manager:
    """Hysteria2管理核心类"""
    
    def __init__(self):
        self.nodes: List[Node] = []
        self.current_node: Optional[Node] = None
        self.load_nodes()
        self.init_system()
        
    def init_system(self):
        """初始化系统配置"""
        try:
            # 确保Hysteria2已安装
            if not HYSTERIA_BIN.exists():
                logger.warning("Hysteria2未安装，请先运行install.sh")
                
            # 加载当前配置
            if HYSTERIA_CONFIG.exists():
                with open(HYSTERIA_CONFIG, 'r') as f:
                    config = yaml.safe_load(f)
                    # 尝试识别当前使用的节点
                    server = config.get('server', '').split(':')[0]
                    for node in self.nodes:
                        if node.server == server:
                            self.current_node = node
                            break
        except Exception as e:
            logger.error(f"系统初始化失败: {e}")
    
    def load_nodes(self):
        """加载节点列表"""
        try:
            if NODES_FILE.exists():
                with open(NODES_FILE, 'r') as f:
                    nodes_data = json.load(f)
                    self.nodes = [Node(**node) for node in nodes_data]
                    logger.info(f"加载了 {len(self.nodes)} 个节点")
        except Exception as e:
            logger.error(f"加载节点失败: {e}")
            self.nodes = []
    
    def save_nodes(self):
        """保存节点列表"""
        try:
            nodes_data = [asdict(node) for node in self.nodes]
            with open(NODES_FILE, 'w') as f:
                json.dump(nodes_data, f, indent=2, ensure_ascii=False)
            logger.info("节点保存成功")
        except Exception as e:
            logger.error(f"保存节点失败: {e}")
    
    def add_node(self, node_data: Dict[str, Any]) -> Tuple[bool, str]:
        """添加节点"""
        try:
            # 如果是URL，先解析
            if 'url' in node_data:
                parsed = Utils.parse_hysteria_url(node_data['url'])
                if not parsed:
                    return False, "无效的节点URL"
                node_data.update(parsed)
                node_data['name'] = node_data.get('name') or f"{parsed['server']}:{parsed['port']}"
            
            # 创建节点对象
            node = Node(**{k: v for k, v in node_data.items() if k in Node.__annotations__})
            
            # 检查重复
            for existing in self.nodes:
                if existing.server == node.server and existing.port == node.port:
                    return False, "节点已存在"
            
            self.nodes.append(node)
            self.save_nodes()
            return True, f"节点 {node.name} 添加成功"
            
        except Exception as e:
            logger.error(f"添加节点失败: {e}")
            return False, str(e)
    
    def update_node(self, node_id: str, node_data: Dict[str, Any]) -> Tuple[bool, str]:
        """更新节点"""
        try:
            for i, node in enumerate(self.nodes):
                if node.id == node_id:
                    # 更新节点数据
                    for key, value in node_data.items():
                        if hasattr(node, key):
                            setattr(node, key, value)
                    node.updated_at = datetime.now().isoformat()
                    
                    self.save_nodes()
                    return True, "节点更新成功"
            
            return False, "节点不存在"
            
        except Exception as e:
            logger.error(f"更新节点失败: {e}")
            return False, str(e)
    
    def delete_node(self, node_id: str) -> Tuple[bool, str]:
        """删除节点"""
        try:
            for i, node in enumerate(self.nodes):
                if node.id == node_id:
                    deleted = self.nodes.pop(i)
                    self.save_nodes()
                    return True, f"节点 {deleted.name} 已删除"
            
            return False, "节点不存在"
            
        except Exception as e:
            logger.error(f"删除节点失败: {e}")
            return False, str(e)
    
    def switch_node(self, node_id: str) -> Tuple[bool, str]:
        """切换节点"""
        try:
            # 查找节点
            target_node = None
            for node in self.nodes:
                if node.id == node_id:
                    target_node = node
                    break
            
            if not target_node:
                return False, "节点不存在"
            
            # 生成配置文件
            config_content = Utils.generate_hysteria_config(target_node)
            with open(HYSTERIA_CONFIG, 'w') as f:
                f.write(config_content)
            
            # 重启服务
            success, message = self.restart_service()
            if success:
                self.current_node = target_node
                return True, f"已切换到节点: {target_node.name}"
            else:
                return False, f"切换失败: {message}"
                
        except Exception as e:
            logger.error(f"切换节点失败: {e}")
            return False, str(e)
    
    def start_service(self) -> Tuple[bool, str]:
        """启动Hysteria2服务"""
        try:
            if not HYSTERIA_CONFIG.exists():
                return False, "配置文件不存在，请先选择节点"
            
            # 使用systemctl启动服务
            returncode, stdout, stderr = Utils.run_command(
                ["systemctl", "start", HYSTERIA_SERVICE],
                check=False
            )
            
            if returncode == 0:
                logger.info("Hysteria2服务启动成功")
                return True, "服务启动成功"
            else:
                # 如果systemd服务不存在，尝试直接运行
                if "not found" in stderr or "not loaded" in stderr:
                    # 创建systemd服务
                    self.create_systemd_service()
                    # 重试启动
                    returncode, stdout, stderr = Utils.run_command(
                        ["systemctl", "start", HYSTERIA_SERVICE],
                        check=False
                    )
                    if returncode == 0:
                        return True, "服务启动成功"
                    
                return False, f"启动失败: {stderr}"
                
        except Exception as e:
            logger.error(f"启动服务失败: {e}")
            return False, str(e)
    
    def stop_service(self) -> Tuple[bool, str]:
        """停止Hysteria2服务"""
        try:
            returncode, stdout, stderr = Utils.run_command(
                ["systemctl", "stop", HYSTERIA_SERVICE],
                check=False
            )
            
            if returncode == 0:
                logger.info("Hysteria2服务已停止")
                return True, "服务已停止"
            else:
                # 尝试直接kill进程
                Utils.run_command(["pkill", "-f", "hysteria"], check=False)
                return True, "服务已停止"
                
        except Exception as e:
            logger.error(f"停止服务失败: {e}")
            return False, str(e)
    
    def restart_service(self) -> Tuple[bool, str]:
        """重启Hysteria2服务"""
        try:
            self.stop_service()
            time.sleep(1)
            return self.start_service()
        except Exception as e:
            logger.error(f"重启服务失败: {e}")
            return False, str(e)
    
    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        try:
            # 检查服务是否运行
            returncode, stdout, _ = Utils.run_command(
                ["systemctl", "is-active", HYSTERIA_SERVICE],
                check=False
            )
            is_running = returncode == 0 and "active" in stdout
            
            # 获取版本信息
            version = "未知"
            if HYSTERIA_BIN.exists():
                returncode, stdout, _ = Utils.run_command(
                    [str(HYSTERIA_BIN), "version"],
                    check=False
                )
                if returncode == 0:
                    version = stdout.strip()
            
            # 检查TUN接口
            returncode, stdout, _ = Utils.run_command(
                ["ip", "link", "show", "hytun"],
                check=False
            )
            tun_exists = returncode == 0
            
            # 获取系统资源使用情况
            cpu_usage = 0.0
            memory_usage = 0.0
            try:
                # 获取CPU使用率
                with open('/proc/stat', 'r') as f:
                    cpu_line = f.readline()
                    cpu_times = list(map(int, cpu_line.split()[1:8]))
                    idle_time = cpu_times[3]
                    total_time = sum(cpu_times)
                    cpu_usage = 100 * (1 - idle_time / total_time)
                
                # 获取内存使用率
                with open('/proc/meminfo', 'r') as f:
                    lines = f.readlines()
                    total_mem = int(lines[0].split()[1])
                    free_mem = int(lines[1].split()[1])
                    memory_usage = 100 * (1 - free_mem / total_mem)
            except:
                pass
            
            # 获取网络统计
            network_stats = Utils.get_network_stats() if tun_exists else {}
            
            # 获取运行时间
            uptime = 0
            if is_running:
                returncode, stdout, _ = Utils.run_command(
                    ["systemctl", "show", HYSTERIA_SERVICE, "-p", "ActiveEnterTimestamp"],
                    check=False
                )
                if returncode == 0 and "=" in stdout:
                    try:
                        timestamp_str = stdout.split("=")[1].strip()
                        # 这里简化处理，实际需要解析systemd的时间戳格式
                        uptime = int(time.time() - time.mktime(time.strptime(timestamp_str[:19], "%Y-%m-%d %H:%M:%S")))
                    except:
                        pass
            
            return {
                'running': is_running,
                'version': version,
                'tun_interface': tun_exists,
                'cpu_usage': round(cpu_usage, 2),
                'memory_usage': round(memory_usage, 2),
                'network_stats': network_stats,
                'uptime': uptime,
                'current_node': asdict(self.current_node) if self.current_node else None
            }
            
        except Exception as e:
            logger.error(f"获取状态失败: {e}")
            return {
                'running': False,
                'version': '未知',
                'tun_interface': False,
                'cpu_usage': 0,
                'memory_usage': 0,
                'network_stats': {},
                'uptime': 0,
                'current_node': None,
                'error': str(e)
            }
    
    def create_systemd_service(self):
        """创建systemd服务文件"""
        try:
            service_content = f"""[Unit]
Description=Hysteria2 Client Service
After=network.target

[Service]
Type=simple
User=root
ExecStart={HYSTERIA_BIN} client -c {HYSTERIA_CONFIG}
Restart=always
RestartSec=10
LimitNOFILE=65535
CapabilityBoundingSet=CAP_NET_ADMIN CAP_NET_RAW CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_ADMIN CAP_NET_RAW CAP_NET_BIND_SERVICE

[Install]
WantedBy=multi-user.target
"""
            
            with open(SYSTEMD_SERVICE_FILE, 'w') as f:
                f.write(service_content)
            
            # 重载systemd配置
            Utils.run_command(["systemctl", "daemon-reload"])
            Utils.run_command(["systemctl", "enable", HYSTERIA_SERVICE])
            
            logger.info("Systemd服务创建成功")
            
        except Exception as e:
            logger.error(f"创建systemd服务失败: {e}")
    
    def get_logs(self, lines: int = 100) -> List[str]:
        """获取服务日志"""
        try:
            returncode, stdout, _ = Utils.run_command(
                ["journalctl", "-u", HYSTERIA_SERVICE, "-n", str(lines), "--no-pager"],
                check=False
            )
            
            if returncode == 0:
                return stdout.split('\n')
            else:
                # 尝试读取本地日志文件
                if LOG_FILE.exists():
                    with open(LOG_FILE, 'r') as f:
                        all_lines = f.readlines()
                        return all_lines[-lines:]
                return []
                
        except Exception as e:
            logger.error(f"获取日志失败: {e}")
            return [f"获取日志失败: {e}"]

# ======================== 认证系统 ========================

class AuthManager:
    """认证管理器"""
    
    def __init__(self):
        self.load_or_create_auth()
    
    def load_or_create_auth(self):
        """加载或创建认证信息"""
        try:
            if AUTH_FILE.exists():
                with open(AUTH_FILE, 'r') as f:
                    self.auth_data = json.load(f)
            else:
                # 创建默认认证信息
                default_password = secrets.token_urlsafe(12)
                self.auth_data = {
                    'username': 'admin',
                    'password_hash': self.hash_password(default_password),
                    'token_secret': secrets.token_urlsafe(32),
                    'created_at': datetime.now().isoformat()
                }
                self.save_auth()
                
                # 打印初始密码
                logger.info("="*50)
                logger.info(f"初始用户名: admin")
                logger.info(f"初始密码: {default_password}")
                logger.info("请登录后立即修改密码！")
                logger.info("="*50)
                
        except Exception as e:
            logger.error(f"加载认证信息失败: {e}")
            # 创建临时认证
            self.auth_data = {
                'username': 'admin',
                'password_hash': self.hash_password('admin'),
                'token_secret': secrets.token_urlsafe(32)
            }
    
    def save_auth(self):
        """保存认证信息"""
        try:
            with open(AUTH_FILE, 'w') as f:
                json.dump(self.auth_data, f, indent=2)
            # 设置文件权限为仅所有者可读写
            os.chmod(AUTH_FILE, 0o600)
        except Exception as e:
            logger.error(f"保存认证信息失败: {e}")
    
    def hash_password(self, password: str) -> str:
        """哈希密码"""
        salt = "hysteria2_manager_salt"  # 实际应用中应该使用随机盐
        return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
    
    def verify_password(self, username: str, password: str) -> bool:
        """验证密码"""
        if username != self.auth_data.get('username'):
            return False
        password_hash = self.hash_password(password)
        return password_hash == self.auth_data.get('password_hash')
    
    def generate_token(self) -> str:
        """生成访问令牌"""
        timestamp = int(time.time())
        token_data = f"{timestamp}:{self.auth_data['token_secret']}"
        token = base64.b64encode(token_data.encode()).decode()
        return token
    
    def verify_token(self, token: str) -> bool:
        """验证令牌（简化版，实际应该使用JWT）"""
        try:
            token_data = base64.b64decode(token.encode()).decode()
            timestamp, secret = token_data.split(':')
            
            # 检查令牌是否过期（24小时）
            if int(time.time()) - int(timestamp) > 86400:
                return False
            
            return secret == self.auth_data['token_secret']
        except:
            return False
    
    def change_password(self, old_password: str, new_password: str) -> Tuple[bool, str]:
        """修改密码"""
        if not self.verify_password(self.auth_data['username'], old_password):
            return False, "原密码错误"
        
        self.auth_data['password_hash'] = self.hash_password(new_password)
        self.save_auth()
        return True, "密码修改成功"

# ======================== Flask应用 ========================

# 创建Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_urlsafe(32)
CORS(app, origins=['http://localhost:*', 'http://127.0.0.1:*', f'http://*:{DEFAULT_PORT}'])

# 创建管理器实例
manager = Hysteria2Manager()
auth_manager = AuthManager()

# ======================== 认证装饰器 ========================

def require_auth(f):
    """需要认证的装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token or not auth_manager.verify_token(token):
            return jsonify({'error': '未授权访问'}), 401
        return f(*args, **kwargs)
    return decorated_function

# ======================== API路由 ========================

@app.route('/')
def index():
    """返回WebUI页面"""
    webui_file = BASE_DIR / "webui.html"
    if webui_file.exists():
        return send_file(webui_file)
    else:
        return "<h1>WebUI文件不存在，请检查安装</h1>", 404

@app.route('/api/health')
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'version': APP_VERSION,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/auth/login', methods=['POST'])
def login():
    """登录接口"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if auth_manager.verify_password(username, password):
        token = auth_manager.generate_token()
        return jsonify({
            'success': True,
            'token': token,
            'username': username
        })
    else:
        return jsonify({
            'success': False,
            'message': '用户名或密码错误'
        }), 401

@app.route('/api/auth/change-password', methods=['POST'])
@require_auth
def change_password():
    """修改密码接口"""
    data = request.json
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    if not old_password or not new_password:
        return jsonify({'success': False, 'message': '参数不完整'}), 400
    
    success, message = auth_manager.change_password(old_password, new_password)
    return jsonify({'success': success, 'message': message})

@app.route('/api/status')
@require_auth
def get_status():
    """获取系统状态"""
    status = manager.get_service_status()
    return jsonify(status)

@app.route('/api/nodes')
@require_auth
def get_nodes():
    """获取节点列表"""
    nodes = [asdict(node) for node in manager.nodes]
    return jsonify({
        'nodes': nodes,
        'current_node_id': manager.current_node.id if manager.current_node else None
    })

@app.route('/api/nodes', methods=['POST'])
@require_auth
def add_node():
    """添加节点"""
    data = request.json
    success, message = manager.add_node(data)
    return jsonify({'success': success, 'message': message})

@app.route('/api/nodes/<node_id>', methods=['PUT'])
@require_auth
def update_node(node_id):
    """更新节点"""
    data = request.json
    success, message = manager.update_node(node_id, data)
    return jsonify({'success': success, 'message': message})

@app.route('/api/nodes/<node_id>', methods=['DELETE'])
@require_auth
def delete_node(node_id):
    """删除节点"""
    success, message = manager.delete_node(node_id)
    return jsonify({'success': success, 'message': message})

@app.route('/api/nodes/<node_id>/switch', methods=['POST'])
@require_auth
def switch_node(node_id):
    """切换节点"""
    success, message = manager.switch_node(node_id)
    return jsonify({'success': success, 'message': message})

@app.route('/api/service/start', methods=['POST'])
@require_auth
def start_service():
    """启动服务"""
    success, message = manager.start_service()
    return jsonify({'success': success, 'message': message})

@app.route('/api/service/stop', methods=['POST'])
@require_auth
def stop_service():
    """停止服务"""
    success, message = manager.stop_service()
    return jsonify({'success': success, 'message': message})

@app.route('/api/service/restart', methods=['POST'])
@require_auth
def restart_service():
    """重启服务"""
    success, message = manager.restart_service()
    return jsonify({'success': success, 'message': message})

@app.route('/api/test-connection')
@require_auth
def test_connection():
    """测试连接"""
    results = Utils.test_connectivity()
    return jsonify(results)

@app.route('/api/logs')
@require_auth
def get_logs():
    """获取日志"""
    lines = request.args.get('lines', 100, type=int)
    logs = manager.get_logs(lines)
    return jsonify({'logs': logs})

@app.route('/api/config/export')
@require_auth
def export_config():
    """导出配置"""
    if HYSTERIA_CONFIG.exists():
        return send_file(HYSTERIA_CONFIG, as_attachment=True, 
                        download_name='hysteria.yaml')
    else:
        return jsonify({'error': '配置文件不存在'}), 404

@app.route('/api/config/import', methods=['POST'])
@require_auth
def import_config():
    """导入配置"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '没有文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': '文件名为空'}), 400
        
        # 保存并验证配置文件
        content = file.read()
        config = yaml.safe_load(content)
        
        # 保存配置
        with open(HYSTERIA_CONFIG, 'wb') as f:
            f.write(content)
        
        return jsonify({'success': True, 'message': '配置导入成功'})
        
    except Exception as e:
        logger.error(f"导入配置失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/system/optimize', methods=['POST'])
@require_auth
def optimize_system():
    """优化系统设置"""
    try:
        # 执行系统优化命令
        commands = [
            ["sysctl", "-w", "net.ipv4.ip_forward=1"],
            ["sysctl", "-w", "net.ipv4.conf.all.rp_filter=2"],
            ["sysctl", "-w", "net.ipv4.conf.default.rp_filter=2"],
            ["sysctl", "-w", "net.core.default_qdisc=fq"],
            ["sysctl", "-w", "net.ipv4.tcp_congestion_control=bbr"]
        ]
        
        for cmd in commands:
            Utils.run_command(cmd, check=False)
        
        return jsonify({'success': True, 'message': '系统优化完成'})
        
    except Exception as e:
        logger.error(f"系统优化失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ======================== WebSocket支持（可选） ========================

# 如需实时日志，可以添加WebSocket支持
# 这里简化处理，使用轮询方式

@app.route('/api/realtime/stats')
@require_auth
def realtime_stats():
    """获取实时统计（简化版）"""
    stats = {
        'timestamp': datetime.now().isoformat(),
        'network': Utils.get_network_stats(),
        'status': manager.get_service_status()
    }
    return jsonify(stats)

# ======================== 主函数 ========================

def signal_handler(sig, frame):
    """处理信号"""
    logger.info("收到退出信号，正在关闭...")
    sys.exit(0)

def main():
    """主函数"""
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 打印启动信息
    logger.info("="*50)
    logger.info(f"{APP_NAME} v{APP_VERSION}")
    logger.info(f"访问地址: http://{DEFAULT_HOST}:{DEFAULT_PORT}")
    logger.info("="*50)
    
    # 检查是否以root运行（TUN需要）
    if os.geteuid() != 0:
        logger.warning("警告：程序未以root权限运行，某些功能可能受限")
    
    # 启动Flask应用
    try:
        app.run(
            host=DEFAULT_HOST,
            port=DEFAULT_PORT,
            debug=False,  # 生产环境设为False
            use_reloader=False,
            threaded=True
        )
    except Exception as e:
        logger.error(f"启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

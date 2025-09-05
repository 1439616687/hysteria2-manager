#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Hysteria2 Manager v2.0 - 核心管理程序
完整重构版本，包含认证系统和所有问题修复
"""

import os
import sys
import json
import yaml
import time
import signal
import base64
import hashlib
import logging
import subprocess
import threading
import socket
import secrets
import functools
import urllib.parse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple

# Flask相关
from flask import Flask, request, jsonify, send_from_directory, session, g
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

# 系统监控
import psutil

# ==================== 配置常量 ====================
VERSION = "2.0.0"
INSTALL_DIR = Path("/opt/hysteria2-manager")
DATA_DIR = INSTALL_DIR / "data"
STATIC_DIR = INSTALL_DIR / "static"
CONFIG_FILE = DATA_DIR / "config.json"
NODES_FILE = DATA_DIR / "nodes.json"
USERS_FILE = DATA_DIR / "users.json"
HYSTERIA_CONFIG = Path("/etc/hysteria2/client.yaml")
HYSTERIA_BIN = Path("/usr/local/bin/hysteria")
LOG_DIR = Path("/var/log/hysteria2")

# 确保目录存在
for dir_path in [HYSTERIA_CONFIG.parent, LOG_DIR, DATA_DIR, STATIC_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# ==================== 日志配置 ====================
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    handlers=[
        logging.FileHandler(LOG_DIR / "manager.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==================== Flask应用初始化 ====================
app = Flask(__name__, static_folder=str(STATIC_DIR))
CORS(app, supports_credentials=True)

# ==================== 全局变量 ====================
config_data = {}
nodes_data = {}
users_data = {}
service_status = {
    "hysteria": "stopped",
    "manager": "running",
    "tun_interface": False,
    "last_check": time.time()
}
stats_cache = {
    "traffic": {"up": 0, "down": 0, "total": 0},
    "connections": 0,
    "uptime": 0,
    "cpu_history": [],
    "memory_history": [],
    "last_update": time.time()
}
monitor_thread = None
session_cleanup_thread = None

# ==================== 配置和数据管理 ====================
def load_config():
    """加载配置文件"""
    global config_data
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        else:
            config_data = create_default_config()
            save_config()
        
        # 设置Flask密钥
        app.secret_key = config_data.get('secret_key', secrets.token_hex(32))
        logger.info(f"配置加载成功，版本: {config_data.get('version', 'unknown')}")
    except Exception as e:
        logger.error(f"加载配置失败: {e}")
        config_data = create_default_config()

def create_default_config():
    """创建默认配置"""
    return {
        "version": VERSION,
        "web_port": 8080,
        "web_host": "0.0.0.0",
        "language": "zh-CN",
        "theme": "light",
        "secret_key": secrets.token_hex(32),
        "auth": {
            "enabled": True,
            "username": "admin",
            "password": generate_password_hash("admin"),
            "session_timeout": 3600
        },
        "hysteria": {
            "bin_path": str(HYSTERIA_BIN),
            "config_path": str(HYSTERIA_CONFIG),
            "log_level": "info"
        },
        "system": {
            "auto_start": True,
            "auto_optimize": True,
            "check_update": True,
            "log_retention_days": 7
        },
        "security": {
            "max_login_attempts": 5,
            "lockout_duration": 300,
            "require_https": False
        }
    }

def save_config():
    """保存配置文件"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"保存配置失败: {e}")
        return False

def load_nodes():
    """加载节点数据"""
    global nodes_data
    try:
        if NODES_FILE.exists():
            with open(NODES_FILE, 'r', encoding='utf-8') as f:
                nodes_data = json.load(f)
        else:
            nodes_data = {
                "nodes": [],
                "current": None,
                "subscriptions": [],
                "groups": []
            }
            save_nodes()
    except Exception as e:
        logger.error(f"加载节点失败: {e}")
        nodes_data = {"nodes": [], "current": None, "subscriptions": [], "groups": []}

def save_nodes():
    """保存节点数据"""
    try:
        with open(NODES_FILE, 'w', encoding='utf-8') as f:
            json.dump(nodes_data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"保存节点失败: {e}")
        return False

def load_users():
    """加载用户数据"""
    global users_data
    try:
        if USERS_FILE.exists():
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                users_data = json.load(f)
        else:
            users_data = {
                "users": [
                    {
                        "id": 1,
                        "username": "admin",
                        "password": generate_password_hash("admin"),
                        "role": "admin",
                        "created_at": datetime.now().isoformat(),
                        "last_login": None,
                        "status": "active",
                        "failed_attempts": 0,
                        "locked_until": None
                    }
                ],
                "sessions": {}
            }
            save_users()
    except Exception as e:
        logger.error(f"加载用户数据失败: {e}")
        users_data = {"users": [], "sessions": {}}

def save_users():
    """保存用户数据"""
    try:
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users_data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"保存用户数据失败: {e}")
        return False

# ==================== 认证装饰器 ====================
def login_required(f):
    """需要登录的装饰器"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        # 检查是否启用认证
        if not config_data.get('auth', {}).get('enabled', True):
            return f(*args, **kwargs)
        
        # 检查会话
        if 'user_id' not in session:
            return jsonify({"success": False, "message": "未登录", "code": 401}), 401
        
        # 检查会话是否过期
        session_id = session.get('session_id')
        if session_id and session_id in users_data.get('sessions', {}):
            session_info = users_data['sessions'][session_id]
            if datetime.now().timestamp() > session_info.get('expires_at', 0):
                # 会话过期
                del users_data['sessions'][session_id]
                session.clear()
                save_users()
                return jsonify({"success": False, "message": "会话已过期", "code": 401}), 401
            
            # 更新最后活动时间
            session_info['last_activity'] = datetime.now().isoformat()
            save_users()
        
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """需要管理员权限的装饰器"""
    @functools.wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        user = next((u for u in users_data.get('users', []) if u['id'] == user_id), None)
        
        if not user or user.get('role') != 'admin':
            return jsonify({"success": False, "message": "需要管理员权限", "code": 403}), 403
        
        return f(*args, **kwargs)
    return decorated_function

# ==================== 工具函数 ====================
def run_command(cmd: List[str], timeout: int = 10) -> Tuple[int, str, str]:
    """执行系统命令"""
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "命令执行超时"
    except Exception as e:
        return -2, "", str(e)

def get_server_ip(server: str) -> str:
    """解析服务器域名为IP地址"""
    try:
        # 检查是否已经是IP地址
        socket.inet_aton(server)
        return server
    except socket.error:
        # 是域名，需要解析
        try:
            ip = socket.gethostbyname(server)
            logger.info(f"解析域名 {server} -> {ip}")
            return ip
        except socket.gaierror as e:
            logger.warning(f"无法解析域名 {server}: {e}")
            # 返回常见公共DNS作为后备
            return server

def parse_hysteria2_url(url: str) -> Optional[Dict[str, Any]]:
    """
    解析Hysteria2节点链接
    支持格式:
    - hy2://password@server:port/?参数#名称
    - hysteria2://password@server:port/?参数#名称
    - hysteria://password@server:port/?参数#名称
    """
    try:
        # 完整URL解码
        url = urllib.parse.unquote(url.strip())
        
        # 分离fragment（节点名称）
        custom_name = None
        if '#' in url:
            url, fragment = url.split('#', 1)
            custom_name = fragment
        
        # 解析协议
        protocol = None
        if url.startswith("hy2://"):
            url_content = url[6:]
            protocol = "hy2"
        elif url.startswith("hysteria2://"):
            url_content = url[12:]
            protocol = "hysteria2"
        elif url.startswith("hysteria://"):
            url_content = url[11:]
            protocol = "hysteria"
        else:
            logger.error(f"不支持的协议: {url}")
            return None
        
        # 分离参数部分
        params = {}
        if '?' in url_content:
            main_part, params_str = url_content.split('?', 1)
            # 处理参数，支持/和&作为分隔符
            params_str = params_str.replace('/', '&')
            params = dict(urllib.parse.parse_qsl(params_str))
        else:
            main_part = url_content
        
        # 解析主体部分 password@server:port
        if '@' not in main_part:
            logger.error(f"URL格式错误，缺少@符号: {url}")
            return None
        
        auth_part, server_part = main_part.rsplit('@', 1)
        
        # 解析服务器和端口
        if ':' in server_part:
            server, port = server_part.rsplit(':', 1)
            try:
                port = int(port)
            except ValueError:
                logger.error(f"端口格式错误: {port}")
                return None
        else:
            server = server_part
            port = 443
        
        # 处理insecure参数
        insecure = False
        if 'insecure' in params:
            insecure_val = params.get('insecure', '0')
            insecure = str(insecure_val) in ['1', 'true', 'True']
        
        # 构建节点信息
        node = {
            "name": custom_name or params.get("name", f"{server}:{port}"),
            "server": server,
            "port": port,
            "password": auth_part,
            "protocol": protocol,
            "sni": params.get("sni", server),
            "insecure": insecure,
            "obfs": params.get("obfs"),
            "obfs_password": params.get("obfs-password") or params.get("obfs_password"),
            "alpn": params.get("alpn"),
            "bandwidth_up": params.get("up"),
            "bandwidth_down": params.get("down"),
            "mtu": int(params.get("mtu", 1500))
        }
        
        # 清理None值
        node = {k: v for k, v in node.items() if v is not None}
        
        logger.info(f"成功解析节点: {node['name']} ({node['server']}:{node['port']})")
        return node
        
    except Exception as e:
        logger.error(f"解析节点URL失败: {e}, URL: {url}")
        import traceback
        traceback.print_exc()
        return None

def generate_hysteria_config(node: Dict[str, Any]) -> str:
    """生成Hysteria2配置文件内容"""
    
    # 解析服务器IP（用于路由排除）
    server_ip = get_server_ip(node["server"])
    
    config = {
        "server": f"{node['server']}:{node['port']}",
        "auth": node["password"],
        "tls": {
            "sni": node.get("sni", node["server"]),
            "insecure": node.get("insecure", False)
        }
    }
    
    # ALPN配置
    if node.get("alpn"):
        config["tls"]["alpn"] = node["alpn"].split(",")
    
    # 混淆配置
    if node.get("obfs"):
        config["obfs"] = {
            "type": node["obfs"]
        }
        if node.get("obfs_password"):
            config["obfs"]["password"] = node["obfs_password"]
    
    # TUN模式配置
    config["tun"] = {
        "name": "hytun",
        "mtu": int(node.get("mtu", 1500)),
        "timeout": "5m",
        "route": {
            "ipv4": ["0.0.0.0/0"],
            "ipv6": ["2000::/3"],
            "ipv4Exclude": [
                f"{server_ip}/32",  # 使用解析后的IP地址
                "127.0.0.0/8",
                "10.0.0.0/8",
                "172.16.0.0/12",
                "192.168.0.0/16",
                "224.0.0.0/4",
                "240.0.0.0/4",
                "169.254.0.0/16"
            ]
        }
    }
    
    # 带宽配置
    if node.get("bandwidth_up") or node.get("bandwidth_down"):
        config["bandwidth"] = {}
        if node.get("bandwidth_up"):
            config["bandwidth"]["up"] = node["bandwidth_up"]
        if node.get("bandwidth_down"):
            config["bandwidth"]["down"] = node["bandwidth_down"]
    
    # 日志配置
    config["log"] = {
        "level": config_data.get("hysteria", {}).get("log_level", "info"),
        "file": str(LOG_DIR / "hysteria.log")
    }
    
    return yaml.dump(config, default_flow_style=False, allow_unicode=True, sort_keys=False)

def check_hysteria_status() -> bool:
    """检查Hysteria2服务状态"""
    try:
        # 检查服务状态
        ret, stdout, _ = run_command(["systemctl", "is-active", "hysteria2-client"])
        is_active = stdout.strip() == "active"
        service_status["hysteria"] = "running" if is_active else "stopped"
        
        # 检查TUN接口
        ret, stdout, _ = run_command(["ip", "link", "show", "hytun"])
        service_status["tun_interface"] = ret == 0
        
        service_status["last_check"] = time.time()
        
        return is_active
    except Exception as e:
        logger.error(f"检查服务状态失败: {e}")
        return False

def test_connection() -> Dict[str, Any]:
    """测试连接状态"""
    result = {
        "status": "unknown",
        "latency": -1,
        "ip": "N/A",
        "location": "N/A",
        "dns": False,
        "http": False
    }
    
    try:
        # 检查服务是否运行
        if service_status.get("hysteria") != "running":
            result["status"] = "disconnected"
            return result
        
        # 测试DNS - 使用多种方法
        dns_methods = [
            ["nslookup", "google.com", "8.8.8.8"],
            ["getent", "hosts", "google.com"],
            ["host", "google.com", "8.8.8.8"]
        ]
        
        for method in dns_methods:
            try:
                ret, _, _ = run_command(method, timeout=3)
                if ret == 0:
                    result["dns"] = True
                    break
            except:
                continue
        
        # 测试HTTP连接和获取IP信息
        try:
            import requests
            # 使用多个IP检测服务
            ip_services = [
                "https://api.ipify.org?format=json",
                "https://ifconfig.io/ip",
                "https://ipapi.co/ip/"
            ]
            
            for service in ip_services:
                try:
                    response = requests.get(service, timeout=5)
                    if response.status_code == 200:
                        result["http"] = True
                        if "json" in service:
                            result["ip"] = response.json().get("ip", "N/A")
                        else:
                            result["ip"] = response.text.strip()
                        break
                except:
                    continue
            
            # 获取位置信息
            if result["ip"] != "N/A":
                try:
                    loc_response = requests.get(f"https://ipapi.co/{result['ip']}/country/", timeout=5)
                    if loc_response.status_code == 200:
                        result["location"] = loc_response.text.strip()
                except:
                    pass
        except ImportError:
            # requests模块不可用，使用curl
            ret, stdout, _ = run_command(["curl", "-s", "-m", "5", "https://ifconfig.io/ip"])
            if ret == 0 and stdout.strip():
                result["http"] = True
                result["ip"] = stdout.strip()
                
                ret, stdout, _ = run_command(["curl", "-s", "-m", "5", "https://ifconfig.io/country_code"])
                if ret == 0:
                    result["location"] = stdout.strip()
        
        # 如果都失败但能访问网站，也认为DNS正常
        if not result["dns"] and result["http"]:
            result["dns"] = True
        
        # 测试延迟
        ret, stdout, _ = run_command(["ping", "-c", "1", "-W", "2", "8.8.8.8"])
        if ret == 0:
            import re
            match = re.search(r'time=(\d+\.?\d*)', stdout)
            if match:
                result["latency"] = float(match.group(1))
        
        # 判断整体状态
        tun_exists = service_status.get("tun_interface", False)
        
        if tun_exists and result["http"]:
            result["status"] = "connected"
        elif service_status["hysteria"] == "running":
            result["status"] = "connecting"
        else:
            result["status"] = "disconnected"
        
    except Exception as e:
        logger.error(f"连接测试失败: {e}")
    
    return result

def get_system_stats() -> Dict[str, Any]:
    """获取系统统计信息"""
    try:
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # 内存使用
        mem = psutil.virtual_memory()
        
        # 磁盘使用
        disk = psutil.disk_usage('/')
        
        # 网络流量
        net_io = psutil.net_io_counters()
        
        # 获取hysteria进程信息
        hysteria_stats = {"cpu": 0, "memory": 0, "pid": None}
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                if proc.info['name'] == 'hysteria':
                    hysteria_stats['pid'] = proc.info['pid']
                    hysteria_stats['cpu'] = proc.info.get('cpu_percent', 0) or 0
                    hysteria_stats['memory'] = proc.info.get('memory_percent', 0) or 0
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # 计算运行时间
        uptime = 0
        if hysteria_stats['pid']:
            try:
                create_time = psutil.Process(hysteria_stats['pid']).create_time()
                uptime = int(time.time() - create_time)
            except:
                pass
        
        return {
            "cpu": {
                "total": cpu_percent,
                "cores": psutil.cpu_count(),
                "hysteria": hysteria_stats['cpu']
            },
            "memory": {
                "total": mem.percent,
                "used": mem.used // (1024 * 1024),  # MB
                "available": mem.available // (1024 * 1024),  # MB
                "total_gb": mem.total // (1024 * 1024 * 1024),  # GB
                "hysteria": hysteria_stats['memory']
            },
            "disk": {
                "total": disk.total // (1024 * 1024 * 1024),  # GB
                "used": disk.used // (1024 * 1024 * 1024),  # GB
                "free": disk.free // (1024 * 1024 * 1024),  # GB
                "percent": disk.percent
            },
            "network": {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv,
                "errors_in": net_io.errin,
                "errors_out": net_io.errout
            },
            "uptime": uptime,
            "hysteria_running": hysteria_stats['pid'] is not None,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"获取系统统计失败: {e}")
        return {
            "cpu": {"total": 0, "cores": 1, "hysteria": 0},
            "memory": {"total": 0, "used": 0, "available": 0, "total_gb": 0, "hysteria": 0},
            "disk": {"total": 0, "used": 0, "free": 0, "percent": 0},
            "network": {"bytes_sent": 0, "bytes_recv": 0, "packets_sent": 0, "packets_recv": 0},
            "uptime": 0,
            "hysteria_running": False,
            "timestamp": time.time()
        }

# ==================== Hysteria2服务控制 ====================
def start_hysteria() -> Tuple[bool, str]:
    """启动Hysteria2服务"""
    try:
        if not HYSTERIA_CONFIG.exists():
            return False, "配置文件不存在，请先选择节点"
        
        ret, stdout, stderr = run_command(["systemctl", "start", "hysteria2-client"])
        if ret != 0:
            return False, f"启动失败: {stderr}"
        
        time.sleep(2)
        
        if check_hysteria_status():
            return True, "服务启动成功"
        else:
            return False, "服务启动失败，请查看日志"
    except Exception as e:
        return False, str(e)

def stop_hysteria() -> Tuple[bool, str]:
    """停止Hysteria2服务"""
    try:
        ret, stdout, stderr = run_command(["systemctl", "stop", "hysteria2-client"])
        if ret != 0:
            return False, f"停止失败: {stderr}"
        
        # 清理TUN接口
        run_command(["ip", "link", "delete", "hytun"], timeout=5)
        
        service_status["hysteria"] = "stopped"
        service_status["tun_interface"] = False
        
        return True, "服务已停止"
    except Exception as e:
        return False, str(e)

def restart_hysteria() -> Tuple[bool, str]:
    """重启Hysteria2服务"""
    stop_hysteria()
    time.sleep(1)
    return start_hysteria()

# ==================== 监控线程 ====================
def monitor_worker():
    """后台监控线程"""
    global stats_cache
    last_bytes_sent = 0
    last_bytes_recv = 0
    
    while True:
        try:
            # 更新服务状态
            check_hysteria_status()
            
            # 获取网络流量
            net_io = psutil.net_io_counters()
            
            # 计算流量增量
            if last_bytes_sent > 0:
                stats_cache["traffic"]["up"] = net_io.bytes_sent - last_bytes_sent
                stats_cache["traffic"]["down"] = net_io.bytes_recv - last_bytes_recv
                stats_cache["traffic"]["total"] = net_io.bytes_sent + net_io.bytes_recv
            
            last_bytes_sent = net_io.bytes_sent
            last_bytes_recv = net_io.bytes_recv
            
            # 更新CPU和内存历史
            cpu_percent = psutil.cpu_percent()
            mem_percent = psutil.virtual_memory().percent
            
            stats_cache["cpu_history"].append({"time": time.time(), "value": cpu_percent})
            stats_cache["memory_history"].append({"time": time.time(), "value": mem_percent})
            
            # 保留最近100个数据点
            if len(stats_cache["cpu_history"]) > 100:
                stats_cache["cpu_history"] = stats_cache["cpu_history"][-100:]
            if len(stats_cache["memory_history"]) > 100:
                stats_cache["memory_history"] = stats_cache["memory_history"][-100:]
            
            # 更新连接数
            connections = len([c for c in psutil.net_connections() if c.status == 'ESTABLISHED'])
            stats_cache["connections"] = connections
            
            stats_cache["last_update"] = time.time()
            
            time.sleep(5)
        except Exception as e:
            logger.error(f"监控线程错误: {e}")
            time.sleep(10)

def session_cleanup_worker():
    """会话清理线程"""
    while True:
        try:
            now = datetime.now().timestamp()
            expired_sessions = []
            
            for session_id, session_info in users_data.get('sessions', {}).items():
                if now > session_info.get('expires_at', 0):
                    expired_sessions.append(session_id)
            
            if expired_sessions:
                for session_id in expired_sessions:
                    del users_data['sessions'][session_id]
                save_users()
                logger.info(f"清理了 {len(expired_sessions)} 个过期会话")
            
            time.sleep(300)  # 每5分钟清理一次
        except Exception as e:
            logger.error(f"会话清理线程错误: {e}")
            time.sleep(60)

# ==================== Flask路由 - 认证相关 ====================
@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """用户登录"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({"success": False, "message": "用户名和密码不能为空"})
        
        # 查找用户
        user = None
        for u in users_data.get('users', []):
            if u['username'] == username:
                user = u
                break
        
        if not user:
            return jsonify({"success": False, "message": "用户名或密码错误"})
        
        # 检查账号状态
        if user.get('status') != 'active':
            return jsonify({"success": False, "message": "账号已被禁用"})
        
        # 检查账号锁定
        if user.get('locked_until'):
            locked_until = datetime.fromisoformat(user['locked_until'])
            if datetime.now() < locked_until:
                return jsonify({"success": False, "message": f"账号已锁定，请稍后再试"})
            else:
                # 解锁
                user['locked_until'] = None
                user['failed_attempts'] = 0
        
        # 验证密码
        if not check_password_hash(user['password'], password):
            # 记录失败次数
            user['failed_attempts'] = user.get('failed_attempts', 0) + 1
            
            max_attempts = config_data.get('security', {}).get('max_login_attempts', 5)
            if user['failed_attempts'] >= max_attempts:
                # 锁定账号
                lockout_duration = config_data.get('security', {}).get('lockout_duration', 300)
                user['locked_until'] = (datetime.now() + timedelta(seconds=lockout_duration)).isoformat()
                save_users()
                return jsonify({"success": False, "message": f"登录失败次数过多，账号已锁定{lockout_duration}秒"})
            
            save_users()
            return jsonify({"success": False, "message": "用户名或密码错误"})
        
        # 登录成功
        user['failed_attempts'] = 0
        user['last_login'] = datetime.now().isoformat()
        
        # 创建会话
        session_id = secrets.token_hex(32)
        session_timeout = config_data.get('auth', {}).get('session_timeout', 3600)
        
        users_data['sessions'][session_id] = {
            'user_id': user['id'],
            'username': username,
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(seconds=session_timeout)).timestamp(),
            'ip': request.remote_addr,
            'user_agent': request.headers.get('User-Agent'),
            'last_activity': datetime.now().isoformat()
        }
        
        save_users()
        
        # 设置会话
        session['user_id'] = user['id']
        session['username'] = username
        session['session_id'] = session_id
        session.permanent = True
        app.permanent_session_lifetime = timedelta(seconds=session_timeout)
        
        logger.info(f"用户 {username} 登录成功，IP: {request.remote_addr}")
        
        return jsonify({
            "success": True,
            "message": "登录成功",
            "data": {
                "username": username,
                "role": user.get('role', 'user'),
                "session_id": session_id,
                "expires_in": session_timeout
            }
        })
        
    except Exception as e:
        logger.error(f"登录失败: {e}")
        return jsonify({"success": False, "message": "登录失败"})

@app.route('/api/auth/logout', methods=['POST'])
@login_required
def api_logout():
    """用户登出"""
    try:
        session_id = session.get('session_id')
        if session_id and session_id in users_data.get('sessions', {}):
            del users_data['sessions'][session_id]
            save_users()
        
        username = session.get('username', 'unknown')
        session.clear()
        
        logger.info(f"用户 {username} 登出")
        
        return jsonify({"success": True, "message": "登出成功"})
    except Exception as e:
        logger.error(f"登出失败: {e}")
        return jsonify({"success": False, "message": "登出失败"})

@app.route('/api/auth/status')
def api_auth_status():
    """获取认证状态"""
    if 'user_id' in session:
        return jsonify({
            "success": True,
            "authenticated": True,
            "data": {
                "username": session.get('username'),
                "user_id": session.get('user_id')
            }
        })
    else:
        return jsonify({
            "success": True,
            "authenticated": False
        })

@app.route('/api/auth/change_password', methods=['POST'])
@login_required
def api_change_password():
    """修改密码"""
    try:
        data = request.get_json()
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        
        if not old_password or not new_password:
            return jsonify({"success": False, "message": "密码不能为空"})
        
        if len(new_password) < 6:
            return jsonify({"success": False, "message": "新密码至少6个字符"})
        
        user_id = session.get('user_id')
        user = next((u for u in users_data.get('users', []) if u['id'] == user_id), None)
        
        if not user:
            return jsonify({"success": False, "message": "用户不存在"})
        
        # 验证旧密码
        if not check_password_hash(user['password'], old_password):
            return jsonify({"success": False, "message": "原密码错误"})
        
        # 更新密码
        user['password'] = generate_password_hash(new_password)
        user['password_changed_at'] = datetime.now().isoformat()
        save_users()
        
        logger.info(f"用户 {user['username']} 修改了密码")
        
        return jsonify({"success": True, "message": "密码修改成功"})
        
    except Exception as e:
        logger.error(f"修改密码失败: {e}")
        return jsonify({"success": False, "message": "修改密码失败"})

# ==================== Flask路由 - 主要功能 ====================
@app.route('/')
def index():
    """主页"""
    return send_from_directory(STATIC_DIR, 'dashboard.html')

@app.route('/api/status')
@login_required
def api_status():
    """获取服务状态"""
    return jsonify({
        "success": True,
        "data": {
            "service": service_status,
            "connection": test_connection() if service_status["hysteria"] == "running" else {
                "status": "disconnected",
                "ip": "N/A",
                "location": "N/A",
                "latency": -1,
                "dns": False,
                "http": False
            },
            "stats": stats_cache,
            "current_node": nodes_data.get("current"),
            "version": VERSION
        }
    })

@app.route('/api/nodes', methods=['GET'])
@login_required
def api_get_nodes():
    """获取节点列表"""
    return jsonify({
        "success": True,
        "data": nodes_data
    })

@app.route('/api/nodes', methods=['POST'])
@login_required
def api_add_node():
    """添加节点"""
    try:
        data = request.get_json()
        
        if "url" in data:
            # 通过URL添加
            node = parse_hysteria2_url(data["url"])
            if not node:
                return jsonify({"success": False, "message": "无效的节点链接"})
            
            # 使用自定义名称（如果提供）
            if data.get("name"):
                node["name"] = data["name"]
        else:
            # 手动添加
            required = ["name", "server", "port", "password"]
            if not all(k in data for k in required):
                return jsonify({"success": False, "message": "缺少必要参数"})
            node = data
        
        # 生成唯一ID
        node["id"] = hashlib.md5(f"{node['server']}:{node['port']}:{time.time()}".encode()).hexdigest()[:8]
        node["created_at"] = datetime.now().isoformat()
        node["last_used"] = None
        node["group"] = data.get("group", "default")
        
        # 添加到节点列表
        nodes_data["nodes"].append(node)
        save_nodes()
        
        logger.info(f"添加节点: {node['name']} ({node['server']}:{node['port']})")
        
        return jsonify({"success": True, "message": "节点添加成功", "data": node})
    except Exception as e:
        logger.error(f"添加节点失败: {e}")
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/nodes/<node_id>', methods=['DELETE'])
@login_required
def api_delete_node(node_id):
    """删除节点"""
    try:
        node_name = None
        for node in nodes_data["nodes"]:
            if node.get("id") == node_id:
                node_name = node.get("name", "未知")
                break
        
        nodes_data["nodes"] = [n for n in nodes_data["nodes"] if n.get("id") != node_id]
        
        # 如果删除的是当前节点
        if nodes_data.get("current") == node_id:
            nodes_data["current"] = None
            stop_hysteria()
        
        save_nodes()
        
        logger.info(f"删除节点: {node_name}")
        
        return jsonify({"success": True, "message": "节点已删除"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/nodes/<node_id>/use', methods=['POST'])
@login_required
def api_use_node(node_id):
    """使用指定节点"""
    try:
        # 查找节点
        node = None
        for n in nodes_data["nodes"]:
            if n.get("id") == node_id:
                node = n
                break
        
        if not node:
            return jsonify({"success": False, "message": "节点不存在"})
        
        # 生成配置文件
        config_content = generate_hysteria_config(node)
        with open(HYSTERIA_CONFIG, 'w') as f:
            f.write(config_content)
        
        # 更新当前节点
        nodes_data["current"] = node_id
        node["last_used"] = datetime.now().isoformat()
        save_nodes()
        
        # 重启服务
        success, message = restart_hysteria()
        
        logger.info(f"切换到节点: {node['name']} ({node['server']}:{node['port']})")
        
        return jsonify({
            "success": success,
            "message": message,
            "data": {"current_node": node}
        })
    except Exception as e:
        logger.error(f"使用节点失败: {e}")
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/service/<action>', methods=['POST'])
@login_required
def api_service_control(action):
    """服务控制"""
    try:
        if action == "start":
            success, message = start_hysteria()
        elif action == "stop":
            success, message = stop_hysteria()
        elif action == "restart":
            success, message = restart_hysteria()
        else:
            return jsonify({"success": False, "message": "无效的操作"})
        
        logger.info(f"服务控制: {action} - {message}")
        
        return jsonify({"success": success, "message": message})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/test')
@login_required
def api_test_connection():
    """测试连接"""
    return jsonify({
        "success": True,
        "data": test_connection()
    })

@app.route('/api/logs')
@login_required
def api_get_logs():
    """获取日志"""
    try:
        lines = int(request.args.get('lines', 100))
        log_type = request.args.get('type', 'all')
        
        logs = {
            "hysteria": [],
            "manager": []
        }
        
        if log_type in ['hysteria', 'all']:
            # Hysteria客户端日志
            ret, stdout, _ = run_command(["journalctl", "-u", "hysteria2-client", "-n", str(lines), "--no-pager"])
            if ret == 0 and stdout:
                logs["hysteria"] = [line for line in stdout.split('\n') if line.strip()]
            
            # 备用：读取日志文件
            if not logs["hysteria"]:
                hysteria_log = LOG_DIR / "hysteria.log"
                if hysteria_log.exists():
                    try:
                        with open(hysteria_log, 'r', encoding='utf-8', errors='ignore') as f:
                            all_lines = f.readlines()
                            logs["hysteria"] = [line.strip() for line in all_lines[-lines:] if line.strip()]
                    except:
                        pass
        
        if log_type in ['manager', 'all']:
            # 管理器日志
            ret, stdout, _ = run_command(["journalctl", "-u", "hysteria2-manager", "-n", str(lines), "--no-pager"])
            if ret == 0 and stdout:
                logs["manager"] = [line for line in stdout.split('\n') if line.strip()]
            
            # 备用：读取日志文件
            if not logs["manager"]:
                manager_log = LOG_DIR / "manager.log"
                if manager_log.exists():
                    try:
                        with open(manager_log, 'r', encoding='utf-8', errors='ignore') as f:
                            all_lines = f.readlines()
                            logs["manager"] = [line.strip() for line in all_lines[-lines:] if line.strip()]
                    except:
                        pass
        
        return jsonify({"success": True, "data": logs})
    except Exception as e:
        logger.error(f"获取日志失败: {e}")
        return jsonify({"success": False, "message": str(e), "data": {"hysteria": [], "manager": []}})

@app.route('/api/system/stats')
@login_required
def api_system_stats():
    """获取系统统计"""
    try:
        stats = get_system_stats()
        return jsonify({
            "success": True,
            "data": stats
        })
    except Exception as e:
        logger.error(f"获取系统统计失败: {e}")
        return jsonify({
            "success": True,
            "data": get_system_stats()  # 返回默认值
        })

@app.route('/api/config', methods=['GET'])
@login_required
def api_get_config():
    """获取配置"""
    # 过滤敏感信息
    safe_config = config_data.copy()
    if 'secret_key' in safe_config:
        del safe_config['secret_key']
    if 'auth' in safe_config and 'password' in safe_config['auth']:
        safe_config['auth']['password'] = '******'
    
    return jsonify({
        "success": True,
        "data": safe_config
    })

@app.route('/api/config', methods=['POST'])
@admin_required
def api_update_config():
    """更新配置"""
    try:
        data = request.get_json()
        
        # 不允许直接修改某些敏感字段
        protected_fields = ['secret_key', 'version']
        for field in protected_fields:
            if field in data:
                del data[field]
        
        # 更新配置
        for key, value in data.items():
            if key in config_data:
                config_data[key] = value
        
        save_config()
        
        logger.info(f"配置已更新")
        
        return jsonify({"success": True, "message": "配置已更新"})
    except Exception as e:
        logger.error(f"更新配置失败: {e}")
        return jsonify({"success": False, "message": str(e)})

# ==================== 信号处理 ====================
def signal_handler(sig, frame):
    """优雅关闭"""
    logger.info("收到停止信号，正在关闭...")
    sys.exit(0)

# ==================== 主函数 ====================
def main():
    """主函数"""
    # 加载数据
    load_config()
    load_nodes()
    load_users()
    
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 启动监控线程
    global monitor_thread, session_cleanup_thread
    monitor_thread = threading.Thread(target=monitor_worker, daemon=True)
    monitor_thread.start()
    
    session_cleanup_thread = threading.Thread(target=session_cleanup_worker, daemon=True)
    session_cleanup_thread.start()
    
    # 检查服务状态
    check_hysteria_status()
    
    # 启动Flask应用
    host = config_data.get("web_host", "0.0.0.0")
    port = config_data.get("web_port", 8080)
    
    logger.info(f"Hysteria2 Manager v{VERSION} 启动中...")
    logger.info(f"WebUI地址: http://{host}:{port}")
    logger.info(f"认证状态: {'启用' if config_data.get('auth', {}).get('enabled', True) else '禁用'}")
    
    app.run(
        host=host,
        port=port,
        debug=False,
        use_reloader=False
    )

if __name__ == '__main__':
    main()

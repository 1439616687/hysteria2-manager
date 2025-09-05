#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hysteria2 Manager v2.0 - Professional Proxy Management System
Author: Hysteria2 Manager Team
License: MIT
"""

import os
import sys
import json
import time
import yaml
import uuid
import shutil
import socket
import hashlib
import logging
import sqlite3
import argparse
import subprocess
import threading
import urllib.parse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from functools import wraps
from contextlib import contextmanager

# Flask及扩展
from flask import Flask, request, jsonify, send_file, Response, g
from flask_cors import CORS
import jwt
import bcrypt
import psutil
import requests

# ==================== 配置常量 ====================
VERSION = "2.0.0"
BASE_DIR = Path("/opt/hysteria2-manager")
DATA_DIR = BASE_DIR / "data"
LOG_DIR = Path("/var/log/hysteria2")
STATIC_DIR = BASE_DIR / "static"
HYSTERIA_BIN = Path("/usr/local/bin/hysteria")
HYSTERIA_CONFIG = Path("/etc/hysteria2/client.yaml")
CONFIG_FILE = DATA_DIR / "config.json"
USERS_FILE = DATA_DIR / "users.json"
NODES_FILE = DATA_DIR / "nodes.json"
STATS_FILE = DATA_DIR / "stats.json"
SESSIONS_FILE = DATA_DIR / "sessions.json"

# JWT配置
JWT_SECRET_KEY = os.environ.get('JWT_SECRET', 'hysteria2-manager-secret-key-change-me')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

# 默认配置
DEFAULT_CONFIG = {
    "version": VERSION,
    "web_port": 8080,
    "web_host": "0.0.0.0",
    "language": "zh-CN",
    "theme": "dark",
    "auth": {
        "enabled": True,
        "session_timeout": 1800  # 30分钟
    },
    "hysteria": {
        "bin_path": str(HYSTERIA_BIN),
        "config_path": str(HYSTERIA_CONFIG),
        "log_level": "info"
    },
    "system": {
        "auto_start": True,
        "auto_optimize": True,
        "check_update": True
    }
}

DEFAULT_USER = {
    "username": "admin",
    "password": "admin",  # 将被加密
    "role": "admin",
    "created_at": datetime.now().isoformat()
}

# ==================== 日志配置 ====================
class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)

def setup_logging():
    """配置日志系统"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # 控制台处理器（彩色）
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(ColoredFormatter(log_format))
    
    # 文件处理器
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(LOG_DIR / "manager.log")
    file_handler.setFormatter(logging.Formatter(log_format))
    
    # 配置根日志器
    logging.basicConfig(
        level=logging.INFO,
        handlers=[console_handler, file_handler]
    )
    
    return logging.getLogger(__name__)

logger = setup_logging()

# ==================== 工具函数 ====================
def run_command(cmd: List[str], timeout: int = 30) -> Tuple[int, str, str]:
    """执行系统命令"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        logger.error(f"命令超时: {' '.join(cmd)}")
        return -1, "", "Command timeout"
    except Exception as e:
        logger.error(f"命令执行失败: {e}")
        return -1, "", str(e)

def ensure_dirs():
    """确保必要目录存在"""
    for dir_path in [BASE_DIR, DATA_DIR, LOG_DIR, STATIC_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)
    logger.info("目录结构已就绪")

def load_json_file(filepath: Path, default: Any = None) -> Any:
    """加载JSON文件"""
    try:
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"加载JSON文件失败 {filepath}: {e}")
    return default if default is not None else {}

def save_json_file(filepath: Path, data: Any) -> bool:
    """保存JSON文件"""
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"保存JSON文件失败 {filepath}: {e}")
        return False

def get_server_ip(domain: str) -> str:
    """解析域名为IP地址"""
    try:
        # 检查是否已是IP地址
        socket.inet_aton(domain)
        return domain
    except socket.error:
        # 解析域名
        try:
            ip = socket.gethostbyname(domain)
            logger.info(f"域名解析: {domain} -> {ip}")
            return ip
        except socket.gaierror:
            logger.warning(f"域名解析失败: {domain}")
            return domain

# ==================== 认证系统 ====================
class AuthManager:
    """认证管理器"""
    
    def __init__(self):
        self.users = {}
        self.sessions = {}
        self.load_users()
    
    def load_users(self):
        """加载用户数据"""
        users_data = load_json_file(USERS_FILE, [DEFAULT_USER])
        
        # 如果是默认用户，加密密码
        for user in users_data:
            if user['username'] == 'admin' and user['password'] == 'admin':
                user['password'] = self.hash_password('admin')
                save_json_file(USERS_FILE, users_data)
        
        self.users = {u['username']: u for u in users_data}
        logger.info(f"加载了 {len(self.users)} 个用户")
    
    def hash_password(self, password: str) -> str:
        """密码哈希"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """验证密码"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except:
            # 兼容旧的明文密码
            return password == hashed
    
    def create_token(self, username: str) -> str:
        """创建JWT令牌"""
        payload = {
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """验证JWT令牌"""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token已过期")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Token无效: {e}")
            return None
    
    def login(self, username: str, password: str) -> Optional[str]:
        """用户登录"""
        user = self.users.get(username)
        if not user:
            return None
        
        if self.verify_password(password, user['password']):
            token = self.create_token(username)
            session_id = str(uuid.uuid4())
            self.sessions[session_id] = {
                'username': username,
                'token': token,
                'login_time': datetime.now().isoformat(),
                'last_activity': datetime.now().isoformat()
            }
            save_json_file(SESSIONS_FILE, self.sessions)
            logger.info(f"用户登录成功: {username}")
            return token
        return None
    
    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """修改密码"""
        user = self.users.get(username)
        if not user:
            return False
        
        if not self.verify_password(old_password, user['password']):
            return False
        
        user['password'] = self.hash_password(new_password)
        users_list = list(self.users.values())
        save_json_file(USERS_FILE, users_list)
        logger.info(f"用户密码已更新: {username}")
        return True
    
    def change_username(self, old_username: str, password: str, new_username: str) -> bool:
        """修改用户名"""
        # 验证原用户
        user = self.users.get(old_username)
        if not user:
            return False
        
        # 验证密码
        if not self.verify_password(password, user['password']):
            return False
        
        # 检查新用户名是否已存在
        if new_username in self.users:
            return False
        
        # 更新用户名
        user['username'] = new_username
        
        # 重新构建用户字典
        del self.users[old_username]
        self.users[new_username] = user
        
        # 保存到文件
        users_list = list(self.users.values())
        save_json_file(USERS_FILE, users_list)
        
        logger.info(f"用户名已更新: {old_username} -> {new_username}")
        return True

# ==================== Hysteria2管理器 ====================
class Hysteria2Manager:
    """Hysteria2核心管理器"""
    
    def __init__(self):
        self.config = load_json_file(CONFIG_FILE, DEFAULT_CONFIG)
        self.nodes = load_json_file(NODES_FILE, {"nodes": [], "current": None})
        self.stats = load_json_file(STATS_FILE, {})
        self.service_status = {"hysteria": "stopped", "manager": "running"}
        
    def parse_hysteria2_url(self, url: str) -> Optional[Dict[str, Any]]:
        """解析Hysteria2节点链接（支持所有格式）"""
        try:
            # URL完整解码
            url = urllib.parse.unquote(url.strip())
            
            # 提取节点名称（#后的部分）
            custom_name = None
            if '#' in url:
                url, fragment = url.split('#', 1)
                custom_name = fragment
            
            # 识别协议类型
            protocol = None
            if url.startswith("hy2://"):
                url_content = url[6:]
                protocol = "hysteria2"
            elif url.startswith("hysteria2://"):
                url_content = url[12:]
                protocol = "hysteria2"
            elif url.startswith("hysteria://"):
                url_content = url[11:]
                protocol = "hysteria2"
            else:
                logger.error(f"不支持的协议: {url}")
                return None
            
            # 分离查询参数
            params = {}
            if '?' in url_content:
                main_part, params_str = url_content.split('?', 1)
                # 处理参数（支持/和&作为分隔符）
                params_str = params_str.replace('/', '&')
                params = dict(urllib.parse.parse_qsl(params_str))
            else:
                main_part = url_content
            
            # 解析认证和服务器信息
            if '@' not in main_part:
                logger.error(f"URL格式错误: {url}")
                return None
            
            auth_part, server_part = main_part.rsplit('@', 1)
            
            # 解析服务器地址和端口
            if ':' in server_part:
                server, port = server_part.rsplit(':', 1)
                try:
                    port = int(port)
                except ValueError:
                    port = 443
            else:
                server = server_part
                port = 443
            
            # 处理insecure参数
            insecure = str(params.get('insecure', '0')) in ['1', 'true', 'True']
            
            # 构建节点配置
            node = {
                "id": str(uuid.uuid4())[:8],
                "name": custom_name or f"{server}:{port}",
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
                "mtu": int(params.get("mtu", 1500)),
                "created_at": datetime.now().isoformat()
            }
            
            # 清理None值
            node = {k: v for k, v in node.items() if v is not None}
            
            logger.info(f"成功解析节点: {node['name']}")
            return node
            
        except Exception as e:
            logger.error(f"解析URL失败: {e}")
            return None
    
    def generate_hysteria_config(self, node: Dict[str, Any]) -> str:
        """生成Hysteria2配置文件"""
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
            config["obfs"] = {"type": node["obfs"]}
            if node.get("obfs_password"):
                config["obfs"]["password"] = node["obfs_password"]
        
        # TUN配置
        config["tun"] = {
            "name": "hytun",
            "mtu": node.get("mtu", 1500),
            "timeout": "5m",
            "route": {
                "ipv4": ["0.0.0.0/0"],
                "ipv6": ["2000::/3"],
                "ipv4Exclude": [
                    f"{server_ip}/32",  # 使用解析后的IP
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
        
        # 带宽限制
        if node.get("bandwidth_up") or node.get("bandwidth_down"):
            config["bandwidth"] = {}
            if node.get("bandwidth_up"):
                config["bandwidth"]["up"] = node["bandwidth_up"]
            if node.get("bandwidth_down"):
                config["bandwidth"]["down"] = node["bandwidth_down"]
        
        # 日志配置
        config["log"] = {
            "level": self.config.get("hysteria", {}).get("log_level", "info"),
            "file": str(LOG_DIR / "hysteria.log")
        }
        
        return yaml.dump(config, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    def add_node(self, node_data: Dict) -> Tuple[bool, str, Optional[str]]:
        """添加节点"""
        try:
            # 如果是URL格式，先解析
            if node_data.get("url"):
                node = self.parse_hysteria2_url(node_data["url"])
                if not node:
                    return False, "无效的节点链接", None
                # 如果提供了自定义名称，使用它
                if node_data.get("name"):
                    node["name"] = node_data["name"]
            else:
                # 手动配置的节点
                node = {
                    "id": str(uuid.uuid4())[:8],
                    "name": node_data.get("name", f"{node_data['server']}:{node_data['port']}"),
                    "server": node_data["server"],
                    "port": node_data["port"],
                    "password": node_data["password"],
                    "sni": node_data.get("sni", node_data["server"]),
                    "insecure": node_data.get("insecure", False),
                    "created_at": datetime.now().isoformat()
                }
            
            # 检查重复
            for existing in self.nodes["nodes"]:
                if (existing["server"] == node["server"] and 
                    existing["port"] == node["port"]):
                    return False, "节点已存在", None
            
            # 添加节点
            self.nodes["nodes"].append(node)
            save_json_file(NODES_FILE, self.nodes)
            
            logger.info(f"添加节点: {node['name']}")
            return True, "节点添加成功", node["id"]
            
        except Exception as e:
            logger.error(f"添加节点失败: {e}")
            return False, str(e), None
    
    def delete_node(self, node_id: str) -> Tuple[bool, str]:
        """删除节点"""
        try:
            # 查找节点
            node_index = None
            for i, node in enumerate(self.nodes["nodes"]):
                if node["id"] == node_id:
                    node_index = i
                    break
            
            if node_index is None:
                return False, "节点不存在"
            
            # 如果是当前节点，清除选择
            if self.nodes["current"] == node_id:
                self.nodes["current"] = None
            
            # 删除节点
            deleted = self.nodes["nodes"].pop(node_index)
            save_json_file(NODES_FILE, self.nodes)
            
            logger.info(f"删除节点: {deleted['name']}")
            return True, "节点已删除"
            
        except Exception as e:
            logger.error(f"删除节点失败: {e}")
            return False, str(e)
    
    def use_node(self, node_id: str) -> Tuple[bool, str]:
        """使用指定节点"""
        try:
            # 查找节点
            target_node = None
            for node in self.nodes["nodes"]:
                if node["id"] == node_id:
                    target_node = node
                    break
            
            if not target_node:
                return False, "节点不存在"
            
            # 生成配置文件
            config_content = self.generate_hysteria_config(target_node)
            
            # 备份旧配置
            if HYSTERIA_CONFIG.exists():
                shutil.copy(HYSTERIA_CONFIG, HYSTERIA_CONFIG.with_suffix('.yaml.bak'))
            
            # 写入新配置
            HYSTERIA_CONFIG.parent.mkdir(parents=True, exist_ok=True)
            with open(HYSTERIA_CONFIG, 'w', encoding='utf-8') as f:
                f.write(config_content)
            
            # 更新当前节点
            self.nodes["current"] = node_id
            save_json_file(NODES_FILE, self.nodes)
            
            # 重启服务
            if self.service_status["hysteria"] == "running":
                self.restart_service()
            
            logger.info(f"切换到节点: {target_node['name']}")
            return True, f"已切换到节点: {target_node['name']}"
            
        except Exception as e:
            logger.error(f"切换节点失败: {e}")
            return False, str(e)
    
    def start_service(self) -> Tuple[bool, str]:
        """启动Hysteria2服务"""
        try:
            if not self.nodes["current"]:
                return False, "请先选择一个节点"
            
            ret, _, stderr = run_command(["systemctl", "start", "hysteria2-client"])
            if ret == 0:
                self.service_status["hysteria"] = "running"
                logger.info("Hysteria2服务已启动")
                return True, "服务启动成功"
            else:
                logger.error(f"启动失败: {stderr}")
                return False, f"启动失败: {stderr}"
                
        except Exception as e:
            logger.error(f"启动服务失败: {e}")
            return False, str(e)
    
    def stop_service(self) -> Tuple[bool, str]:
        """停止Hysteria2服务"""
        try:
            ret, _, _ = run_command(["systemctl", "stop", "hysteria2-client"])
            if ret == 0:
                self.service_status["hysteria"] = "stopped"
                logger.info("Hysteria2服务已停止")
                return True, "服务已停止"
            else:
                return False, "停止失败"
                
        except Exception as e:
            logger.error(f"停止服务失败: {e}")
            return False, str(e)
    
    def restart_service(self) -> Tuple[bool, str]:
        """重启Hysteria2服务"""
        self.stop_service()
        time.sleep(2)
        return self.start_service()
    
    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        # 检查Hysteria2服务
        ret, stdout, _ = run_command(["systemctl", "is-active", "hysteria2-client"])
        self.service_status["hysteria"] = "running" if ret == 0 and "active" in stdout else "stopped"
        
        # 检查TUN接口
        ret, _, _ = run_command(["ip", "link", "show", "hytun"])
        tun_exists = ret == 0
        
        return {
            "hysteria": self.service_status["hysteria"],
            "manager": "running",
            "tun_interface": tun_exists
        }
    
    def test_connection(self) -> Dict[str, Any]:
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
            # 检查服务状态
            if self.service_status["hysteria"] != "running":
                result["status"] = "disconnected"
                return result
            
            # 测试DNS解析（多种方法）
            dns_tests = [
                ["nslookup", "google.com", "8.8.8.8"],
                ["getent", "hosts", "google.com"],
            ]
            for test in dns_tests:
                ret, _, _ = run_command(test, timeout=3)
                if ret == 0:
                    result["dns"] = True
                    break
            
            # 测试HTTP连接并获取IP
            try:
                response = requests.get("https://api.ipify.org?format=json", timeout=5)
                if response.status_code == 200:
                    result["http"] = True
                    result["ip"] = response.json().get("ip", "N/A")
                    
                    # 获取IP位置
                    loc_resp = requests.get(f"https://ipapi.co/{result['ip']}/country/", timeout=3)
                    if loc_resp.status_code == 200:
                        result["location"] = loc_resp.text.strip()
            except:
                # 备用方法
                ret, stdout, _ = run_command(["curl", "-s", "-m", "5", "https://ifconfig.io/ip"])
                if ret == 0 and stdout.strip():
                    result["http"] = True
                    result["ip"] = stdout.strip()
                    
                    ret, stdout, _ = run_command(["curl", "-s", "-m", "3", "https://ifconfig.io/country_code"])
                    if ret == 0:
                        result["location"] = stdout.strip()
            
            # 如果HTTP正常但DNS显示失败，修正为正常
            if result["http"] and not result["dns"]:
                result["dns"] = True
            
            # 测试延迟
            ret, stdout, _ = run_command(["ping", "-c", "1", "-W", "2", "8.8.8.8"])
            if ret == 0:
                import re
                match = re.search(r'time=(\d+\.?\d*)', stdout)
                if match:
                    result["latency"] = float(match.group(1))
            
            # 判断连接状态
            tun_exists = run_command(["ip", "link", "show", "hytun"])[0] == 0
            
            if tun_exists and result["http"]:
                result["status"] = "connected"
            elif self.service_status["hysteria"] == "running":
                result["status"] = "connecting"
            else:
                result["status"] = "disconnected"
                
        except Exception as e:
            logger.error(f"连接测试失败: {e}")
        
        return result
    
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息 - 修复版本"""
        try:
            # CPU使用率 - 使用interval参数获取准确值
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存信息
            mem = psutil.virtual_memory()
            
            # 磁盘信息
            disk = psutil.disk_usage('/')
            
            # 网络流量
            net_io = psutil.net_io_counters()
            
            # Hysteria进程信息
            hysteria_info = {"cpu": 0, "memory": 0, "pid": None}
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
                try:
                    if 'hysteria' in proc.info['name'].lower():
                        hysteria_info["pid"] = proc.info['pid']
                        hysteria_info["cpu"] = proc.cpu_percent(interval=0.1)
                        hysteria_info["memory"] = proc.memory_info().rss / 1024 / 1024  # MB
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            # 返回格式化的数据，确保前端能正确访问
            return {
                "cpu": {
                    "total": round(cpu_percent, 1),  # 确保是浮点数
                    "hysteria": round(hysteria_info["cpu"], 1)
                },
                "memory": {
                    "total": round(mem.percent, 1),  # 确保是浮点数
                    "used": mem.used // (1024 * 1024),  # MB
                    "available": mem.available // (1024 * 1024),  # MB
                    "hysteria": round(hysteria_info["memory"], 1)
                },
                "disk": {
                    "total": disk.total // (1024 * 1024 * 1024),  # GB
                    "used": disk.used // (1024 * 1024 * 1024),  # GB
                    "percent": round(disk.percent, 1)
                },
                "network": {
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv,
                    "packets_sent": net_io.packets_sent,
                    "packets_recv": net_io.packets_recv
                },
                "uptime": int(time.time() - psutil.boot_time()),
                "hysteria_running": hysteria_info["pid"] is not None
            }
            
        except Exception as e:
            logger.error(f"获取系统统计失败: {e}")
            # 返回默认值，确保前端不会崩溃
            return {
                "cpu": {"total": 0, "hysteria": 0},
                "memory": {"total": 0, "used": 0, "available": 0, "hysteria": 0},
                "disk": {"total": 0, "used": 0, "percent": 0},
                "network": {"bytes_sent": 0, "bytes_recv": 0, "packets_sent": 0, "packets_recv": 0},
                "uptime": 0,
                "hysteria_running": False
            }

# ==================== Flask应用 ====================
app = Flask(__name__)
CORS(app, origins="*", allow_headers="*", methods="*")  # 开发环境配置
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET', 'hysteria2-flask-secret-key')

# 全局对象
auth_manager = AuthManager()
hysteria_manager = Hysteria2Manager()

# ==================== 认证装饰器 ====================
def require_auth(f):
    """需要认证的装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 获取token
        token = None
        auth_header = request.headers.get('Authorization')
        if auth_header:
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except:
                token = auth_header
        
        if not token:
            return jsonify({"success": False, "message": "未提供认证令牌"}), 401
        
        # 验证token
        payload = auth_manager.verify_token(token)
        if not payload:
            return jsonify({"success": False, "message": "认证令牌无效或已过期"}), 401
        
        # 将用户信息添加到g对象
        g.user = payload
        return f(*args, **kwargs)
    
    return decorated_function

# ==================== API路由 ====================

@app.route('/')
def index():
    """主页 - 返回WebUI"""
    webui_file = STATIC_DIR / "webui.html"
    if webui_file.exists():
        return send_file(str(webui_file))
    else:
        return jsonify({"success": False, "message": "WebUI文件未找到"}), 404

@app.route('/api/login', methods=['POST'])
def api_login():
    """用户登录"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"success": False, "message": "用户名和密码不能为空"}), 400
    
    token = auth_manager.login(username, password)
    if token:
        return jsonify({
            "success": True,
            "message": "登录成功",
            "data": {
                "token": token,
                "username": username
            }
        })
    else:
        return jsonify({"success": False, "message": "用户名或密码错误"}), 401

@app.route('/api/logout', methods=['POST'])
@require_auth
def api_logout():
    """用户登出"""
    return jsonify({"success": True, "message": "登出成功"})

@app.route('/api/change_password', methods=['POST'])
@require_auth
def api_change_password():
    """修改密码"""
    data = request.get_json()
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    if not old_password or not new_password:
        return jsonify({"success": False, "message": "密码不能为空"}), 400
    
    if len(new_password) < 6:
        return jsonify({"success": False, "message": "新密码长度至少6位"}), 400
    
    username = g.user['username']
    if auth_manager.change_password(username, old_password, new_password):
        return jsonify({"success": True, "message": "密码修改成功"})
    else:
        return jsonify({"success": False, "message": "原密码错误"}), 400

@app.route('/api/change_username', methods=['POST'])
@require_auth
def api_change_username():
    """修改用户名 - 新增功能"""
    data = request.get_json()
    password = data.get('password')
    new_username = data.get('new_username')
    
    if not password or not new_username:
        return jsonify({"success": False, "message": "密码和新用户名不能为空"}), 400
    
    if len(new_username) < 3:
        return jsonify({"success": False, "message": "用户名长度至少3位"}), 400
    
    if len(new_username) > 20:
        return jsonify({"success": False, "message": "用户名长度不能超过20位"}), 400
    
    # 验证用户名格式（只允许字母数字和下划线）
    import re
    if not re.match(r'^[a-zA-Z0-9_]+$', new_username):
        return jsonify({"success": False, "message": "用户名只能包含字母、数字和下划线"}), 400
    
    current_username = g.user['username']
    if auth_manager.change_username(current_username, password, new_username):
        return jsonify({"success": True, "message": "用户名修改成功"})
    else:
        return jsonify({"success": False, "message": "密码错误或新用户名已存在"}), 400

@app.route('/api/status')
@require_auth
def api_status():
    """获取系统状态"""
    try:
        service_status = hysteria_manager.get_service_status()
        connection_status = hysteria_manager.test_connection()
        
        # 获取流量统计
        stats = {
            "traffic": {"up": 0, "down": 0, "total": 0},
            "connections": 0,
            "uptime": 0
        }
        
        # 尝试从系统获取流量信息
        try:
            net_io = psutil.net_io_counters()
            stats["traffic"]["up"] = net_io.bytes_sent
            stats["traffic"]["down"] = net_io.bytes_recv
            stats["traffic"]["total"] = net_io.bytes_sent + net_io.bytes_recv
        except:
            pass
        
        return jsonify({
            "success": True,
            "data": {
                "service": service_status,
                "connection": connection_status,
                "stats": stats,
                "current_node": hysteria_manager.nodes.get("current")
            }
        })
    except Exception as e:
        logger.error(f"获取状态失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/nodes')
@require_auth
def api_get_nodes():
    """获取节点列表"""
    return jsonify({
        "success": True,
        "data": {
            "nodes": hysteria_manager.nodes.get("nodes", []),
            "current": hysteria_manager.nodes.get("current")
        }
    })

@app.route('/api/nodes', methods=['POST'])
@require_auth
def api_add_node():
    """添加节点"""
    data = request.get_json()
    success, message, node_id = hysteria_manager.add_node(data)
    
    if success:
        return jsonify({
            "success": True,
            "message": message,
            "data": {"id": node_id}
        })
    else:
        return jsonify({"success": False, "message": message}), 400

@app.route('/api/nodes/<node_id>', methods=['PUT'])
@require_auth
def api_update_node(node_id):
    """更新节点"""
    data = request.get_json()
    
    # 查找并更新节点
    for node in hysteria_manager.nodes["nodes"]:
        if node["id"] == node_id:
            node.update(data)
            save_json_file(NODES_FILE, hysteria_manager.nodes)
            return jsonify({"success": True, "message": "节点已更新"})
    
    return jsonify({"success": False, "message": "节点不存在"}), 404

@app.route('/api/nodes/<node_id>', methods=['DELETE'])
@require_auth
def api_delete_node(node_id):
    """删除节点"""
    success, message = hysteria_manager.delete_node(node_id)
    if success:
        return jsonify({"success": True, "message": message})
    else:
        return jsonify({"success": False, "message": message}), 404

@app.route('/api/nodes/<node_id>/use', methods=['POST'])
@require_auth
def api_use_node(node_id):
    """使用指定节点"""
    success, message = hysteria_manager.use_node(node_id)
    if success:
        return jsonify({"success": True, "message": message})
    else:
        return jsonify({"success": False, "message": message}), 400

@app.route('/api/service/start', methods=['POST'])
@require_auth
def api_start_service():
    """启动服务"""
    success, message = hysteria_manager.start_service()
    if success:
        return jsonify({"success": True, "message": message})
    else:
        return jsonify({"success": False, "message": message}), 400

@app.route('/api/service/stop', methods=['POST'])
@require_auth
def api_stop_service():
    """停止服务"""
    success, message = hysteria_manager.stop_service()
    return jsonify({"success": success, "message": message})

@app.route('/api/service/restart', methods=['POST'])
@require_auth
def api_restart_service():
    """重启服务"""
    success, message = hysteria_manager.restart_service()
    if success:
        return jsonify({"success": True, "message": message})
    else:
        return jsonify({"success": False, "message": message}), 400

@app.route('/api/test')
@require_auth
def api_test_connection():
    """测试连接"""
    result = hysteria_manager.test_connection()
    return jsonify({"success": True, "data": result})

@app.route('/api/logs')
@require_auth
def api_get_logs():
    """获取日志"""
    try:
        lines = int(request.args.get('lines', 100))
        
        logs = {
            "hysteria": [],
            "manager": []
        }
        
        # 使用journalctl读取日志
        ret, stdout, _ = run_command(["journalctl", "-u", "hysteria2-client", "-n", str(lines), "--no-pager"])
        if ret == 0 and stdout:
            logs["hysteria"] = [line for line in stdout.split('\n') if line.strip()]
        
        # 备用：读取日志文件
        if not logs["hysteria"]:
            hysteria_log = LOG_DIR / "hysteria.log"
            if hysteria_log.exists():
                with open(hysteria_log, 'r', encoding='utf-8', errors='ignore') as f:
                    all_lines = f.readlines()
                    logs["hysteria"] = [line.strip() for line in all_lines[-lines:]]
        
        # 管理器日志
        ret, stdout, _ = run_command(["journalctl", "-u", "hysteria2-manager", "-n", str(lines), "--no-pager"])
        if ret == 0 and stdout:
            logs["manager"] = [line for line in stdout.split('\n') if line.strip()]
        
        return jsonify({"success": True, "data": logs})
        
    except Exception as e:
        logger.error(f"获取日志失败: {e}")
        return jsonify({"success": False, "message": str(e), "data": {"hysteria": [], "manager": []}}), 500

@app.route('/api/system/stats')
@require_auth
def api_system_stats():
    """获取系统统计"""
    stats = hysteria_manager.get_system_stats()
    return jsonify({"success": True, "data": stats})

@app.route('/api/system/optimize', methods=['POST'])
@require_auth
def api_optimize_system():
    """系统优化"""
    try:
        # 执行系统优化命令
        commands = [
            ["sysctl", "-w", "net.core.rmem_max=134217728"],
            ["sysctl", "-w", "net.core.wmem_max=134217728"],
            ["sysctl", "-w", "net.ipv4.tcp_rmem=4096 87380 134217728"],
            ["sysctl", "-w", "net.ipv4.tcp_wmem=4096 65536 134217728"],
            ["sysctl", "-w", "net.ipv4.tcp_congestion_control=bbr"],
            ["sysctl", "-w", "net.ipv4.ip_forward=1"]
        ]
        
        for cmd in commands:
            run_command(cmd)
        
        logger.info("系统优化完成")
        return jsonify({"success": True, "message": "系统优化成功"})
        
    except Exception as e:
        logger.error(f"系统优化失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/config')
@require_auth
def api_get_config():
    """获取配置"""
    return jsonify({"success": True, "data": hysteria_manager.config})

@app.route('/api/config', methods=['POST'])
@require_auth
def api_update_config():
    """更新配置"""
    data = request.get_json()
    hysteria_manager.config.update(data)
    save_json_file(CONFIG_FILE, hysteria_manager.config)
    return jsonify({"success": True, "message": "配置已更新"})

@app.route('/api/subscription', methods=['POST'])
@require_auth
def api_import_subscription():
    """导入订阅"""
    data = request.get_json()
    url = data.get('url')
    name = data.get('name', '未命名订阅')
    
    if not url:
        return jsonify({"success": False, "message": "订阅地址不能为空"}), 400
    
    try:
        # 获取订阅内容
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        content = response.text
        
        # 解析订阅（假设每行一个节点链接）
        nodes_added = 0
        for line in content.split('\n'):
            line = line.strip()
            if line and (line.startswith('hy2://') or line.startswith('hysteria')):
                success, _, _ = hysteria_manager.add_node({"url": line})
                if success:
                    nodes_added += 1
        
        if nodes_added > 0:
            return jsonify({
                "success": True,
                "message": f"成功导入 {nodes_added} 个节点"
            })
        else:
            return jsonify({"success": False, "message": "未找到有效节点"}), 400
            
    except Exception as e:
        logger.error(f"导入订阅失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/export/config')
@require_auth
def api_export_config():
    """导出配置"""
    config_data = {
        "version": VERSION,
        "config": hysteria_manager.config,
        "nodes": hysteria_manager.nodes,
        "exported_at": datetime.now().isoformat()
    }
    
    return jsonify({
        "success": True,
        "data": json.dumps(config_data, indent=2, ensure_ascii=False)
    })

@app.route('/api/import/config', methods=['POST'])
@require_auth
def api_import_config():
    """导入配置"""
    try:
        data = request.get_json()
        config_str = data.get('data')
        
        if not config_str:
            return jsonify({"success": False, "message": "配置数据为空"}), 400
        
        # 解析配置
        import_data = json.loads(config_str)
        
        # 导入配置
        if 'config' in import_data:
            hysteria_manager.config = import_data['config']
            save_json_file(CONFIG_FILE, hysteria_manager.config)
        
        # 导入节点
        if 'nodes' in import_data:
            hysteria_manager.nodes = import_data['nodes']
            save_json_file(NODES_FILE, hysteria_manager.nodes)
        
        logger.info("配置导入成功")
        return jsonify({"success": True, "message": "配置导入成功"})
        
    except Exception as e:
        logger.error(f"配置导入失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/version')
def api_version():
    """获取版本信息"""
    return jsonify({
        "success": True,
        "data": {
            "version": VERSION,
            "hysteria_version": "2.6.2",
            "update_available": False
        }
    })

# ==================== 错误处理 ====================
@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "message": "接口不存在"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"success": False, "message": "服务器内部错误"}), 500

# ==================== 主程序 ====================
def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(description='Hysteria2 Manager v2.0')
    parser.add_argument('--port', type=int, default=8080, help='Web服务端口')
    parser.add_argument('--host', default='0.0.0.0', help='监听地址')
    parser.add_argument('--debug', action='store_true', help='调试模式')
    parser.add_argument('--no-auth', action='store_true', help='禁用认证（不推荐）')
    args = parser.parse_args()
    
    # 确保目录结构
    ensure_dirs()
    
    # 加载配置
    config = load_json_file(CONFIG_FILE, DEFAULT_CONFIG)
    
    # 处理命令行参数
    if args.no_auth:
        logger.warning("认证已禁用 - 生产环境不推荐")
        config['auth']['enabled'] = False
        save_json_file(CONFIG_FILE, config)
    
    # 启动信息
    logger.info(f"""
    ╔══════════════════════════════════════╗
    ║   Hysteria2 Manager v{VERSION}          ║
    ║   Starting Web Server...             ║
    ╚══════════════════════════════════════╝
    """)
    
    logger.info(f"Web服务地址: http://{args.host}:{args.port}")
    logger.info(f"认证状态: {'启用' if config['auth']['enabled'] else '禁用'}")
    logger.info("默认账号: admin / admin (首次登录后请修改)")
    
    # 启动Flask应用
    try:
        app.run(
            host=args.host,
            port=args.port,
            debug=args.debug,
            use_reloader=False
        )
    except KeyboardInterrupt:
        logger.info("\n正在关闭...")
    except Exception as e:
        logger.error(f"启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

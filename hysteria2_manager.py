#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Hysteria2 Manager - 核心管理程序
提供WebUI服务器、API接口、节点管理、系统控制等所有功能
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
import urllib.parse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple

import psutil
from flask import Flask, request, jsonify, send_from_directory, render_template_string
from flask_cors import CORS

# ==================== 配置常量 ====================
VERSION = "1.0.0"
INSTALL_DIR = Path("/opt/hysteria2-manager")
DATA_DIR = INSTALL_DIR / "data"
STATIC_DIR = INSTALL_DIR / "static"
CONFIG_FILE = DATA_DIR / "config.json"
NODES_FILE = DATA_DIR / "nodes.json"
HYSTERIA_CONFIG = Path("/etc/hysteria2/client.yaml")
HYSTERIA_BIN = Path("/usr/local/bin/hysteria")
LOG_DIR = Path("/var/log/hysteria2")

# 确保目录存在
HYSTERIA_CONFIG.parent.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ==================== 日志配置 ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "manager.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==================== Flask应用初始化 ====================
app = Flask(__name__, static_folder=str(STATIC_DIR))
CORS(app)

# ==================== 全局变量 ====================
config_data = {}
nodes_data = {}
stats_cache = {
    "traffic": {"up": 0, "down": 0, "total": 0},
    "connections": 0,
    "uptime": 0,
    "last_update": time.time()
}
monitor_thread = None
service_status = {
    "hysteria": "stopped",
    "manager": "running",
    "tun_interface": False
}

# ==================== 工具函数 ====================
def load_config():
    """加载配置文件"""
    global config_data
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        else:
            # 创建默认配置
            config_data = {
                "version": VERSION,
                "web_port": 8080,
                "web_host": "0.0.0.0",
                "language": "zh-CN",
                "theme": "auto",
                "auth": {
                    "enabled": False,
                    "username": "admin",
                    "password": ""
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
            save_config()
    except Exception as e:
        logger.error(f"加载配置失败: {e}")
        config_data = {}

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
                "subscriptions": []
            }
            save_nodes()
    except Exception as e:
        logger.error(f"加载节点失败: {e}")
        nodes_data = {"nodes": [], "current": None, "subscriptions": []}

def save_nodes():
    """保存节点数据"""
    try:
        with open(NODES_FILE, 'w', encoding='utf-8') as f:
            json.dump(nodes_data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"保存节点失败: {e}")
        return False

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

def parse_hysteria2_url(url: str) -> Optional[Dict[str, Any]]:
    """
    解析Hysteria2节点链接
    支持格式:
    - hy2://password@server:port/?参数
    - hysteria2://password@server:port/?参数
    """
    try:
        # URL解码
        url = urllib.parse.unquote(url)
        
        # 解析协议
        if url.startswith("hy2://"):
            url = url[6:]
            protocol = "hy2"
        elif url.startswith("hysteria2://"):
            url = url[12:]
            protocol = "hysteria2"
        else:
            return None
        
        # 分离参数部分
        if '?' in url:
            main_part, params_str = url.split('?', 1)
            params = dict(urllib.parse.parse_qsl(params_str))
        else:
            main_part = url
            params = {}
        
        # 解析主体部分 password@server:port
        if '@' not in main_part:
            return None
            
        auth_part, server_part = main_part.rsplit('@', 1)
        
        # 解析服务器和端口
        if ':' in server_part:
            server, port = server_part.rsplit(':', 1)
            port = int(port)
        else:
            server = server_part
            port = 443
        
        # 构建节点信息
        node = {
            "name": params.get("name", f"{server}:{port}"),
            "server": server,
            "port": port,
            "password": auth_part,
            "protocol": protocol,
            "sni": params.get("sni", server),
            "insecure": params.get("insecure", "0") == "1",
            "obfs": params.get("obfs"),
            "obfs_password": params.get("obfs-password"),
            "alpn": params.get("alpn"),
            "bandwidth_up": params.get("up"),
            "bandwidth_down": params.get("down"),
            "mtu": params.get("mtu", 1500)
        }
        
        # 清理None值
        node = {k: v for k, v in node.items() if v is not None}
        
        return node
    except Exception as e:
        logger.error(f"解析节点URL失败: {e}")
        return None

def generate_hysteria_config(node: Dict[str, Any]) -> str:
    """生成Hysteria2配置文件内容"""
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
                f"{node['server']}/32",  # 排除服务器IP
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
        ret, stdout, _ = run_command(["systemctl", "is-active", "hysteria2-client"])
        service_status["hysteria"] = "running" if stdout.strip() == "active" else "stopped"
        
        # 检查TUN接口
        ret, stdout, _ = run_command(["ip", "link", "show", "hytun"])
        service_status["tun_interface"] = ret == 0
        
        return service_status["hysteria"] == "running"
    except Exception as e:
        logger.error(f"检查服务状态失败: {e}")
        return False

def start_hysteria() -> Tuple[bool, str]:
    """启动Hysteria2服务"""
    try:
        # 确保配置文件存在
        if not HYSTERIA_CONFIG.exists():
            return False, "配置文件不存在，请先选择节点"
        
        # 启动服务
        ret, stdout, stderr = run_command(["systemctl", "start", "hysteria2-client"])
        if ret != 0:
            return False, f"启动失败: {stderr}"
        
        # 等待服务启动
        time.sleep(2)
        
        # 检查状态
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
        # 测试DNS
        ret, stdout, _ = run_command(["nslookup", "google.com"], timeout=5)
        result["dns"] = ret == 0
        
        # 测试HTTP连接和获取IP信息
        ret, stdout, _ = run_command(["curl", "-s", "-m", "5", "https://ifconfig.io/ip"])
        if ret == 0 and stdout.strip():
            result["http"] = True
            result["ip"] = stdout.strip()
            
            # 获取位置信息
            ret, stdout, _ = run_command(["curl", "-s", "-m", "5", "https://ifconfig.io/country_code"])
            if ret == 0:
                result["location"] = stdout.strip()
        
        # 测试延迟
        ret, stdout, _ = run_command(["ping", "-c", "1", "-W", "2", "8.8.8.8"])
        if ret == 0:
            # 从ping输出中提取延迟
            import re
            match = re.search(r'time=(\d+\.?\d*)', stdout)
            if match:
                result["latency"] = float(match.group(1))
        
        # 判断整体状态
        if result["dns"] and result["http"]:
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
        hysteria_pid = None
        hysteria_stats = {"cpu": 0, "memory": 0}
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            if proc.info['name'] == 'hysteria':
                hysteria_pid = proc.info['pid']
                hysteria_stats['cpu'] = proc.info.get('cpu_percent', 0)
                hysteria_stats['memory'] = proc.info.get('memory_percent', 0)
                break
        
        # 计算运行时间
        uptime = 0
        if hysteria_pid:
            try:
                create_time = psutil.Process(hysteria_pid).create_time()
                uptime = int(time.time() - create_time)
            except:
                pass
        
        return {
            "cpu": {
                "total": cpu_percent,
                "hysteria": hysteria_stats['cpu']
            },
            "memory": {
                "total": mem.percent,
                "used": mem.used // (1024 * 1024),  # MB
                "available": mem.available // (1024 * 1024),  # MB
                "hysteria": hysteria_stats['memory']
            },
            "disk": {
                "total": disk.total // (1024 * 1024 * 1024),  # GB
                "used": disk.used // (1024 * 1024 * 1024),  # GB
                "percent": disk.percent
            },
            "network": {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv
            },
            "uptime": uptime,
            "hysteria_running": hysteria_pid is not None
        }
    except Exception as e:
        logger.error(f"获取系统统计失败: {e}")
        return {}

def apply_system_optimization() -> Tuple[bool, str]:
    """应用系统优化"""
    try:
        optimizations = [
            # IP转发
            ["sysctl", "-w", "net.ipv4.ip_forward=1"],
            ["sysctl", "-w", "net.ipv6.conf.all.forwarding=1"],
            
            # 反向路径过滤
            ["sysctl", "-w", "net.ipv4.conf.default.rp_filter=2"],
            ["sysctl", "-w", "net.ipv4.conf.all.rp_filter=2"],
            
            # TCP优化
            ["sysctl", "-w", "net.core.default_qdisc=fq"],
            ["sysctl", "-w", "net.ipv4.tcp_congestion_control=bbr"],
            ["sysctl", "-w", "net.ipv4.tcp_fastopen=3"],
            
            # 缓冲区优化
            ["sysctl", "-w", "net.core.rmem_max=16777216"],
            ["sysctl", "-w", "net.core.wmem_max=16777216"],
        ]
        
        failed = []
        for cmd in optimizations:
            ret, _, stderr = run_command(cmd)
            if ret != 0:
                failed.append(f"{' '.join(cmd)}: {stderr}")
        
        if failed:
            return False, f"部分优化失败: {'; '.join(failed)}"
        else:
            return True, "系统优化已应用"
    except Exception as e:
        return False, str(e)

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
                stats_cache["traffic"]["total"] += stats_cache["traffic"]["up"] + stats_cache["traffic"]["down"]
            
            last_bytes_sent = net_io.bytes_sent
            last_bytes_recv = net_io.bytes_recv
            
            # 更新连接数（简化实现）
            connections = len([c for c in psutil.net_connections() if c.status == 'ESTABLISHED'])
            stats_cache["connections"] = connections
            
            # 更新时间戳
            stats_cache["last_update"] = time.time()
            
            time.sleep(5)  # 每5秒更新一次
        except Exception as e:
            logger.error(f"监控线程错误: {e}")
            time.sleep(10)

# ==================== Flask路由 ====================

@app.route('/')
def index():
    """主页 - 返回WebUI"""
    return send_from_directory(STATIC_DIR, 'dashboard.html')

@app.route('/api/status')
def api_status():
    """获取服务状态"""
    return jsonify({
        "success": True,
        "data": {
            "service": service_status,
            "connection": test_connection() if service_status["hysteria"] == "running" else {},
            "stats": stats_cache,
            "current_node": nodes_data.get("current"),
            "version": VERSION
        }
    })

@app.route('/api/nodes', methods=['GET'])
def api_get_nodes():
    """获取节点列表"""
    return jsonify({
        "success": True,
        "data": nodes_data
    })

@app.route('/api/nodes', methods=['POST'])
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
        
        # 添加到节点列表
        nodes_data["nodes"].append(node)
        save_nodes()
        
        return jsonify({"success": True, "message": "节点添加成功", "data": node})
    except Exception as e:
        logger.error(f"添加节点失败: {e}")
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/nodes/<node_id>', methods=['DELETE'])
def api_delete_node(node_id):
    """删除节点"""
    try:
        nodes_data["nodes"] = [n for n in nodes_data["nodes"] if n.get("id") != node_id]
        
        # 如果删除的是当前节点
        if nodes_data.get("current") == node_id:
            nodes_data["current"] = None
            stop_hysteria()
        
        save_nodes()
        return jsonify({"success": True, "message": "节点已删除"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/nodes/<node_id>', methods=['PUT'])
def api_update_node(node_id):
    """更新节点"""
    try:
        data = request.get_json()
        
        for node in nodes_data["nodes"]:
            if node.get("id") == node_id:
                node.update(data)
                save_nodes()
                
                # 如果是当前节点，重新生成配置
                if nodes_data.get("current") == node_id:
                    config_content = generate_hysteria_config(node)
                    with open(HYSTERIA_CONFIG, 'w') as f:
                        f.write(config_content)
                    
                    if service_status["hysteria"] == "running":
                        restart_hysteria()
                
                return jsonify({"success": True, "message": "节点更新成功"})
        
        return jsonify({"success": False, "message": "节点不存在"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/nodes/<node_id>/use', methods=['POST'])
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
        save_nodes()
        
        # 重启服务
        success, message = restart_hysteria()
        
        return jsonify({
            "success": success,
            "message": message,
            "data": {"current_node": node}
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/service/<action>', methods=['POST'])
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
        
        return jsonify({"success": success, "message": message})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/test')
def api_test_connection():
    """测试连接"""
    return jsonify({
        "success": True,
        "data": test_connection()
    })

@app.route('/api/logs')
def api_get_logs():
    """获取日志"""
    try:
        lines = int(request.args.get('lines', 100))
        
        logs = {
            "hysteria": [],
            "manager": []
        }
        
        # 读取Hysteria日志
        hysteria_log = LOG_DIR / "hysteria.log"
        if hysteria_log.exists():
            ret, stdout, _ = run_command(["tail", f"-n{lines}", str(hysteria_log)])
            if ret == 0:
                logs["hysteria"] = stdout.split('\n')
        
        # 读取管理器日志
        manager_log = LOG_DIR / "manager.log"
        if manager_log.exists():
            ret, stdout, _ = run_command(["tail", f"-n{lines}", str(manager_log)])
            if ret == 0:
                logs["manager"] = stdout.split('\n')
        
        return jsonify({"success": True, "data": logs})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/system/stats')
def api_system_stats():
    """获取系统统计"""
    return jsonify({
        "success": True,
        "data": get_system_stats()
    })

@app.route('/api/system/optimize', methods=['POST'])
def api_system_optimize():
    """应用系统优化"""
    success, message = apply_system_optimization()
    return jsonify({"success": success, "message": message})

@app.route('/api/config', methods=['GET'])
def api_get_config():
    """获取配置"""
    return jsonify({
        "success": True,
        "data": config_data
    })

@app.route('/api/config', methods=['POST'])
def api_update_config():
    """更新配置"""
    try:
        data = request.get_json()
        config_data.update(data)
        save_config()
        return jsonify({"success": True, "message": "配置已更新"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/subscription', methods=['POST'])
def api_add_subscription():
    """添加订阅"""
    try:
        data = request.get_json()
        url = data.get("url")
        
        if not url:
            return jsonify({"success": False, "message": "订阅地址不能为空"})
        
        # 下载订阅内容
        import requests
        response = requests.get(url, timeout=10)
        content = response.text
        
        # 解析节点
        added = 0
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith(('hy2://', 'hysteria2://')):
                node = parse_hysteria2_url(line)
                if node:
                    node["id"] = hashlib.md5(f"{node['server']}:{node['port']}:{time.time()}".encode()).hexdigest()[:8]
                    node["created_at"] = datetime.now().isoformat()
                    node["source"] = "subscription"
                    nodes_data["nodes"].append(node)
                    added += 1
        
        # 保存订阅信息
        nodes_data["subscriptions"].append({
            "url": url,
            "name": data.get("name", "未命名订阅"),
            "updated_at": datetime.now().isoformat(),
            "nodes_count": added
        })
        
        save_nodes()
        
        return jsonify({
            "success": True,
            "message": f"成功导入 {added} 个节点"
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/export/config')
def api_export_config():
    """导出配置"""
    try:
        export_data = {
            "version": VERSION,
            "exported_at": datetime.now().isoformat(),
            "config": config_data,
            "nodes": nodes_data
        }
        
        return jsonify({
            "success": True,
            "data": base64.b64encode(json.dumps(export_data).encode()).decode()
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/import/config', methods=['POST'])
def api_import_config():
    """导入配置"""
    try:
        data = request.get_json()
        encoded = data.get("data")
        
        if not encoded:
            return jsonify({"success": False, "message": "无效的导入数据"})
        
        # 解码
        import_data = json.loads(base64.b64decode(encoded))
        
        # 合并配置
        if "config" in import_data:
            config_data.update(import_data["config"])
            save_config()
        
        # 合并节点
        if "nodes" in import_data:
            existing_servers = {(n["server"], n["port"]) for n in nodes_data["nodes"]}
            
            for node in import_data["nodes"].get("nodes", []):
                if (node["server"], node["port"]) not in existing_servers:
                    nodes_data["nodes"].append(node)
            
            save_nodes()
        
        return jsonify({"success": True, "message": "配置导入成功"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/check_update')
def api_check_update():
    """检查更新"""
    try:
        import requests
        
        # 检查GitHub最新版本
        response = requests.get(
            f"https://api.github.com/repos/{config_data.get('github_repo', '1439616687/hysteria2-manager')}/releases/latest",
            timeout=10
        )
        
        if response.status_code == 200:
            latest = response.json()
            latest_version = latest.get("tag_name", "").lstrip("v")
            
            return jsonify({
                "success": True,
                "data": {
                    "current_version": VERSION,
                    "latest_version": latest_version,
                    "update_available": latest_version > VERSION,
                    "release_notes": latest.get("body", ""),
                    "download_url": latest.get("html_url", "")
                }
            })
        else:
            return jsonify({"success": False, "message": "无法获取更新信息"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

# ==================== 信号处理 ====================
def signal_handler(sig, frame):
    """优雅关闭"""
    logger.info("收到停止信号，正在关闭...")
    sys.exit(0)

# ==================== 主函数 ====================
def main():
    """主函数"""
    # 加载配置
    load_config()
    load_nodes()
    
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 启动监控线程
    global monitor_thread
    monitor_thread = threading.Thread(target=monitor_worker, daemon=True)
    monitor_thread.start()
    
    # 检查服务状态
    check_hysteria_status()
    
    # 启动Flask应用
    host = config_data.get("web_host", "0.0.0.0")
    port = config_data.get("web_port", 8080)
    
    logger.info(f"Hysteria2 Manager v{VERSION} 启动中...")
    logger.info(f"WebUI地址: http://{host}:{port}")
    
    app.run(
        host=host,
        port=port,
        debug=False,
        use_reloader=False
    )

if __name__ == '__main__':
    main()

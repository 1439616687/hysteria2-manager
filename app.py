#!/usr/bin/env python3
"""
Hysteria2 WebUI Manager - 主应用程序
提供Web界面来管理Hysteria2客户端配置
"""

import os
import json
import yaml
import subprocess
import psutil
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash
import secrets

# 初始化Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)
CORS(app)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 配置文件路径
CONFIG_DIR = os.path.join(os.path.dirname(__file__), 'config')
SETTINGS_FILE = os.path.join(CONFIG_DIR, 'settings.json')
HYSTERIA_CONFIG = '/etc/hysteria2/client.yaml'

# 加载应用配置
def load_settings():
    """加载应用设置"""
    try:
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载配置失败: {e}")
        return {
            "webui": {
                "port": 8080,
                "host": "0.0.0.0",
                "username": "admin",
                "password": "admin123"
            }
        }

# 保存应用配置
def save_settings(settings):
    """保存应用设置"""
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=4)
        return True
    except Exception as e:
        logger.error(f"保存配置失败: {e}")
        return False

# 登录验证装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# 路由：登录页面
@app.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        settings = load_settings()
        
        if (username == settings['webui']['username'] and 
            password == settings['webui']['password']):
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='用户名或密码错误')
    
    return render_template('login.html')

# 路由：登出
@app.route('/logout')
def logout():
    """用户登出"""
    session.clear()
    return redirect(url_for('login'))

# 路由：主页面
@app.route('/')
@login_required
def index():
    """主页面 - 显示状态仪表板"""
    return render_template('index.html')

# 路由：配置页面
@app.route('/config')
@login_required
def config():
    """配置页面"""
    return render_template('config.html')

# 路由：日志页面
@app.route('/logs')
@login_required
def logs():
    """日志页面"""
    return render_template('logs.html')

# API：获取系统状态
@app.route('/api/status')
@login_required
def api_status():
    """获取Hysteria2服务状态和系统信息"""
    try:
        # 检查Hysteria2服务状态
        result = subprocess.run(
            ['systemctl', 'is-active', 'hysteria2'],
            capture_output=True, text=True
        )
        hysteria_status = result.stdout.strip() == 'active'
        
        # 获取系统信息
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        network = psutil.net_io_counters()
        
        # 检查TUN接口
        tun_status = 'hytun' in psutil.net_if_addrs()
        
        # 获取出口IP（如果服务运行中）
        exit_ip = 'N/A'
        if hysteria_status:
            try:
                result = subprocess.run(
                    ['curl', '-s', '-m', '3', 'https://ifconfig.io'],
                    capture_output=True, text=True
                )
                exit_ip = result.stdout.strip() or 'N/A'
            except:
                pass
        
        return jsonify({
            'success': True,
            'data': {
                'hysteria': {
                    'status': hysteria_status,
                    'tun_interface': tun_status,
                    'exit_ip': exit_ip
                },
                'system': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_used': memory.used // (1024**2),  # MB
                    'memory_total': memory.total // (1024**2),  # MB
                    'network_sent': network.bytes_sent // (1024**2),  # MB
                    'network_recv': network.bytes_recv // (1024**2),  # MB
                    'uptime': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            }
        })
    except Exception as e:
        logger.error(f"获取状态失败: {e}")
        return jsonify({'success': False, 'error': str(e)})

# API：获取配置
@app.route('/api/config', methods=['GET'])
@login_required
def api_get_config():
    """获取当前Hysteria2配置"""
    try:
        if os.path.exists(HYSTERIA_CONFIG):
            with open(HYSTERIA_CONFIG, 'r') as f:
                config = yaml.safe_load(f)
        else:
            # 返回默认配置模板
            config = {
                'server': '',
                'auth': '',
                'tls': {
                    'sni': '',
                    'insecure': False
                },
                'tun': {
                    'name': 'hytun',
                    'mtu': 1500,
                    'route': {
                        'ipv4': ['0.0.0.0/0'],
                        'ipv6': ['2000::/3'],
                        'ipv4Exclude': [
                            '127.0.0.0/8',
                            '10.0.0.0/8',
                            '172.16.0.0/12',
                            '192.168.0.0/16'
                        ]
                    }
                }
            }
        
        return jsonify({'success': True, 'config': config})
    except Exception as e:
        logger.error(f"获取配置失败: {e}")
        return jsonify({'success': False, 'error': str(e)})

# API：保存配置
@app.route('/api/config', methods=['POST'])
@login_required
def api_save_config():
    """保存Hysteria2配置"""
    try:
        data = request.json
        
        # 解析节点URL或使用手动配置
        if data.get('node_url'):
            config = parse_node_url(data['node_url'])
        else:
            config = data.get('config', {})
        
        # 确保配置目录存在
        os.makedirs('/etc/hysteria2', exist_ok=True)
        
        # 保存配置
        with open(HYSTERIA_CONFIG, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        return jsonify({'success': True, 'message': '配置已保存'})
    except Exception as e:
        logger.error(f"保存配置失败: {e}")
        return jsonify({'success': False, 'error': str(e)})

# API：控制服务
@app.route('/api/service/<action>')
@login_required
def api_service_control(action):
    """控制Hysteria2服务"""
    try:
        if action not in ['start', 'stop', 'restart']:
            return jsonify({'success': False, 'error': '无效的操作'})
        
        result = subprocess.run(
            ['systemctl', action, 'hysteria2'],
            capture_output=True, text=True
        )
        
        if result.returncode == 0:
            return jsonify({'success': True, 'message': f'服务已{action}'})
        else:
            return jsonify({'success': False, 'error': result.stderr})
    except Exception as e:
        logger.error(f"服务控制失败: {e}")
        return jsonify({'success': False, 'error': str(e)})

# API：获取日志
@app.route('/api/logs')
@login_required
def api_get_logs():
    """获取Hysteria2日志"""
    try:
        result = subprocess.run(
            ['journalctl', '-u', 'hysteria2', '-n', '100', '--no-pager'],
            capture_output=True, text=True
        )
        
        logs = result.stdout.split('\n')
        return jsonify({'success': True, 'logs': logs})
    except Exception as e:
        logger.error(f"获取日志失败: {e}")
        return jsonify({'success': False, 'error': str(e)})

# 工具函数：解析节点URL
def parse_node_url(url):
    """解析Hysteria2节点URL"""
    import re
    from urllib.parse import unquote, urlparse, parse_qs
    
    # 解码URL
    url = unquote(url)
    
    # 解析URL组件
    pattern = r'(hy2|hysteria2)://([^@]+)@([^:]+):([^/?]+)(\?.*)?$'
    match = re.match(pattern, url)
    
    if not match:
        raise ValueError("无效的节点URL格式")
    
    protocol, password, server, port, params_str = match.groups()
    
    # 解析查询参数
    params = {}
    if params_str:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
    
    # 构建配置
    config = {
        'server': f'{server}:{port}',
        'auth': password,
        'tls': {
            'sni': params.get('sni', [server])[0],
            'insecure': params.get('insecure', ['0'])[0] == '1'
        },
        'tun': {
            'name': 'hytun',
            'mtu': 1500,
            'route': {
                'ipv4': ['0.0.0.0/0'],
                'ipv6': ['2000::/3'],
                'ipv4Exclude': [
                    f'{server}/32',  # 排除服务器IP
                    '127.0.0.0/8',
                    '10.0.0.0/8',
                    '172.16.0.0/12',
                    '192.168.0.0/16'
                ]
            }
        }
    }
    
    return config

# 主程序入口
if __name__ == '__main__':
    settings = load_settings()
    app.run(
        host=settings['webui']['host'],
        port=settings['webui']['port'],
        debug=False
    )

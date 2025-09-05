# Hysteria2 Manager

<div align="center">

![Hysteria2 Manager](https://img.shields.io/badge/Hysteria2-Manager-blue?style=for-the-badge&logo=rocket)
![Version](https://img.shields.io/badge/version-1.0.0-green?style=for-the-badge)
![License](https://img.shields.io/badge/license-MIT-yellow?style=for-the-badge)
![Platform](https://img.shields.io/badge/platform-Linux-orange?style=for-the-badge&logo=linux)

**🚀 一个功能强大且易用的 Hysteria2 代理管理器**

[English](#) | **简体中文** | [安装教程](#快速开始) | [使用文档](#使用指南) | [问题反馈](https://github.com/yourusername/hysteria2-manager/issues)

</div>

---

## 📋 目录

- [简介](#-简介)
- [功能特性](#-功能特性)
- [系统要求](#-系统要求)
- [快速开始](#-快速开始)
- [使用指南](#-使用指南)
- [配置说明](#-配置说明)
- [API文档](#-api文档)
- [故障排查](#-故障排查)
- [更新日志](#-更新日志)
- [贡献指南](#-贡献指南)
- [鸣谢](#-鸣谢)
- [许可证](#-许可证)

## 🌟 简介

Hysteria2 Manager 是一个基于 Web 的 Hysteria2 代理管理工具，提供了直观的图形界面来管理您的代理节点。它让复杂的命令行操作变得简单，即使是新手也能轻松上手。

### 为什么选择 Hysteria2 Manager？

- **🎯 零基础门槛** - 无需了解复杂的配置文件格式
- **⚡ 一键部署** - 单个命令完成所有安装配置
- **🎨 现代化界面** - 响应式设计，支持深色模式
- **🔒 安全可靠** - 本地运行，数据加密存储
- **📊 实时监控** - 流量统计、系统资源监控
- **🌍 多节点管理** - 轻松切换不同服务器

## ✨ 功能特性

### 核心功能
- ✅ **Web UI 控制面板** - 美观易用的网页界面
- ✅ **节点管理** - 添加、编辑、删除、切换节点
- ✅ **一键连接** - 快速启动/停止/重启服务
- ✅ **订阅支持** - 批量导入节点订阅
- ✅ **连接测试** - 实时测试代理连接状态
- ✅ **日志查看** - 分类查看系统和服务日志
- ✅ **系统优化** - 自动优化内核参数
- ✅ **配置备份** - 导入/导出配置文件

### 界面特性
- 🎨 **深色模式** - 自动适应系统主题
- 📱 **响应式设计** - 完美支持移动设备
- 🌐 **多语言支持** - 中文/英文界面（规划中）
- 📊 **可视化图表** - 流量和资源使用图表
- 🔔 **实时通知** - 连接状态变化提醒

### 技术特点
- 🐍 **Python 后端** - 基于 Flask 框架
- 🎯 **单文件前端** - 所有界面代码集成在一个 HTML 文件
- 📦 **轻量化设计** - 最小依赖，资源占用低
- 🔄 **RESTful API** - 完整的 API 接口
- 🐳 **容器支持** - Docker 部署支持（规划中）

## 💻 系统要求

### 最低要求
- **操作系统**: Linux (Ubuntu 18.04+, Debian 9+, CentOS 7+)
- **架构**: x86_64, arm64, armv7
- **内存**: 512MB RAM
- **存储**: 100MB 可用空间
- **Python**: 3.6+
- **权限**: root 权限（用于 TUN 设备）

### 推荐配置
- **操作系统**: Ubuntu 22.04 LTS
- **内存**: 1GB RAM
- **存储**: 500MB 可用空间
- **网络**: 稳定的互联网连接

## 🚀 快速开始

### 一键安装

```bash
# 使用 wget
wget -O install.sh https://raw.githubusercontent.com/1439616687/hysteria2-manager/main/install.sh && sudo bash install.sh

# 或使用 curl
curl -fsSL https://raw.githubusercontent.com/1439616687/hysteria2-manager/main/install.sh | sudo bash

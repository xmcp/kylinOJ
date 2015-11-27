# kylinOJ
Ultra-Safe Online Judge System Based on VirtualBox

## This repo is still under construction.

## 部署指南
- 安装 Virtualbox 5.0.10
- 创建一个 linux 虚拟机并安装系统
- 在虚拟机里安装 g++ 和 VBoxGuestAdditions
- 创建一个名为 `judge` 的普通用户
- 关闭虚拟机，在设置中**关闭虚拟机的网络连接**（连 Host-Only 网络都不要留）
- 按情况调整虚拟机的设置
- 打开虚拟机，当完全开机后创建一个快照
- 在设置文件（`const.py`）里填入虚拟机的相关设置，包括虚拟机的名称、快照名称、root 密码和 judge 密码

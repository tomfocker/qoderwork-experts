# 服务器台账

## 活跃设备

| 设备名 | 角色 | 公网IP | Tailscale IP | LAN IP | 用户 | SSH端口 | 操作系统 | 密钥状态 | 主要服务 |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| 阿里云VPS | 反向代理/穿透 | 39.107.245.108 | 100.64.0.11 | - | root | 22 | Linux(Debian) | ✅ 已配置 | 宝塔面板, nginx反代, Docker(10容器), tailscale, derper, frps, wxchat |
| Ubuntu VM | Docker主宿主机 | - | 100.64.0.1 | 10.10.158.160 | zym588 | 22 | Ubuntu Server(LVM) | ✅ 已配置 | 44个Docker容器(已加docker组), 1Panel, alist, portainer, karakeep |
| 极空间NAS | 存储/媒体 | - | 100.64.0.6 | 192.168.31.221 | 17733717568 | 22222 | Linux(Q4 6.8.1) | ✅ 已配置 | moviepilot-v2(偶尔挂), 出口节点 |
| Mac mini | 个人桌面 | - | 100.64.0.8 | 192.168.31.95 | andy | 22 | macOS 15.6.1 | ❌ 待配置(离线) | 个人桌面 |
| GL-MT2500 | 路由器 | - | 100.64.0.31 | - | root | 22 | OpenWrt(ARMv8) | ✅ 已配置(dropbear) | 路由/NAT/Tailscale |
| WSL2 Ubuntu | 本地AI | - | - | localhost | zym | 22 | Ubuntu(WSL2) | ❌ 未配置 | Ollama, VoxCPM |
| 本机Windows | 工作机 | - | 100.64.0.3 | 10.10.158.165 | Admin | - | Windows 10/11 | - | 密钥源(admin@h3c), 已清三个后门 |

## SSH 密钥信息

- 密钥类型: ed25519
- 公钥位置: C:\Users\Admin\.ssh\id_ed25519.pub
- 注释: admin@h3c
- 生成时间: 2026-07-01

## 待维护设备

| 设备名 | Tailscale IP | 用户 | SSH端口 | 状态 | 备注 |
|:---|:---|:---|:---|:---|:---|
| fatcow Linux | 100.64.0.4 | zym588 | 2222 | 内核被篡改，需重装 | 不可原地修复, 离线11天 |

## 离线设备

| 设备名 | Tailscale IP | 最后在线 | 备注 |
|:---|:---|:---|:---|
| Mac mini | 100.64.0.8 | 22小时前 | SSH密钥待配置 |
| notebook | 100.64.0.2 | 33分钟前 | - |
| my-pc | 100.64.0.5 | 1天前 | - |
| fatcow-test | 100.64.0.9 | 94天前 | - |
| xuniji | 100.64.0.10 | 56天前 | - |
| phone | 100.64.0.7 | 83天前 | - |

## 关键服务

| 服务 | URL/地址 | 备注 |
|:---|:---|:---|
| Alist 网盘 | https://share.zym588.space | 本地目录正常, 123网盘待API恢复 |
| 123云盘 | 123pan.com | API当前404 |
| restic备份 | D:\虚拟机共享存储\Ubuntu_Backups\repo | 本机VMware共享目录, 最新快照deccbb77(2026-06-16) |

## 网络环境

- Tailscale Tailnet: tomfocker091@
- 所有活跃设备通过 Tailscale 组网互联
- 极空间NAS 提供 Tailscale 出口节点

## 特殊注意事项

- **Ubuntu VM Docker**: 用户 zym588 已加入 docker 组，当前会话可用 `sg docker -c 'docker ...'`，重新登录后直接 `docker ...`
- **阿里云VPS Docker**: root 用户直接运行，Docker 26.1.3，10个容器（6运行/4停止），含 tailscale/derper/wxchat/frps/nginx-proxy-manager
- **极空间NAS**: 用户无家目录(/home/17733717568 不存在)，通过 sudo 创建了 .ssh 目录
- **GL-MT2500**: 使用 dropbear，authorized_keys 在 /etc/dropbear/authorized_keys
- **VPS 磁盘**: 40G 用了 30G (81%)，偏高需关注
- **Ubuntu VM 磁盘**: 72G 用了 57G (83%)，偏高需关注

## 变更记录

- 2026-07-01: Ubuntu VM zym588 已加入 docker 组，免 sudo 运行 docker
- 2026-07-01: 确认 VPS 有 Docker(10容器)，修正之前误判
- 2026-07-01: 生成密钥对(admin@h3c)，推送到 VPS/Ubuntu VM/NAS/GL-MT2500
- 2026-07-01: 首次全设备检测，4台在线设备密钥登录成功
- 2026-07-01: Mac mini 离线22小时，密钥待上线后推送
- 2026-07-01: 初始台账创建，录入全部设备信息
- 2026-07-01: 本机Windows 已清除三个后门(python3-libstud/escsvc/tempadmin)

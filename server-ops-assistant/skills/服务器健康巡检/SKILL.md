---
name: 服务器健康巡检
version: 1.0.0
description: Batch health check for personal servers via SSH — CPU, memory, disk, network, Docker, Tailscale status, with email notification via Agently Mail
description_zh: 通过SSH批量检查服务器CPU、内存、磁盘、网络、Docker、Tailscale状态，结果可推送到QQ邮箱
user-invocable: true
argument-hint: 指定设备名（如"VPS"）或输入"全部"巡检所有活跃设备
---

# 服务器健康巡检

通过 SSH 连接到各服务器，执行健康检查命令，汇总结果并可选邮件推送。

## 前置条件

- 读取 [服务器台账](references/server-inventory.md) 获取设备连接信息
- Windows 本机已安装 OpenSSH（`where ssh` 验证）
- 如需邮件推送：Agently Mail CLI 已安装并授权

## 巡检流程

### 1. 确定巡检目标

根据用户输入确定要巡检的设备：
- "全部" → 巡检所有活跃设备（跳过 fatcow 和离线设备）
- 指定设备名 → 只巡检该设备
- 未指定 → 默认巡检全部活跃设备

活跃 Linux 设备清单：阿里云VPS、Ubuntu VM、极空间NAS、Mac mini、GL-MT2500、WSL2

### 2. SSH 连接

对每台目标设备执行 SSH 连接：

```bash
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 -p <SSH端口> <用户>@<IP> "<命令>"
```

连接参数说明：
- `StrictHostKeyChecking=no`：Tailscale 环境下 IP 可能变化，避免 host key 检查阻塞
- `ConnectTimeout=10`：10 秒超时，不在线的设备快速跳过
- 优先使用 Tailscale IP 连接，Tailscale 不可用时用 LAN IP
- 阿里云 VPS 用公网 IP `39.107.245.108`

如果 SSH 需要密码且当前环境不支持交互式输入，提示用户设置 SSH 密钥认证。

### 3. 执行健康检查命令

在每台 Linux 服务器上依次执行（合并为一条命令减少连接次数）：

```bash
echo "=== SYSTEM ===" && uname -a && uptime && echo "=== CPU ===" && top -bn1 | head -5 && echo "=== MEMORY ===" && free -h && echo "=== DISK ===" && df -h | grep -v tmpfs | grep -v devtmpfs && echo "=== NETWORK ===" && ip -br addr 2>/dev/null || ifconfig 2>/dev/null && echo "=== DOCKER ===" && docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' 2>/dev/null && echo "=== TAILSCALE ===" && tailscale status 2>/dev/null && echo "=== LOAD ===" && cat /proc/loadavg 2>/dev/null
```

对 macOS（Mac mini）调整命令：

```bash
echo "=== SYSTEM ===" && uname -a && uptime && echo "=== CPU ===" && sysctl -n hw.ncpu && echo "=== MEMORY ===" && vm_stat && echo "=== DISK ===" && df -h | grep -v devfs && echo "=== NETWORK ===" && ifconfig | grep "inet " && echo "=== TAILSCALE ===" && tailscale status 2>/dev/null
```

对 OpenWrt（GL-MT2500）调整命令：

```bash
echo "=== SYSTEM ===" && uname -a && uptime && echo "=== MEMORY ===" && free && echo "=== NETWORK ===" && ip addr && echo "=== TAILSCALE ===" && tailscale status 2>/dev/null && echo "=== TEMPERATURE ===" && cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null
```

### 4. 结果分析与告警阈值

对每台设备的结果进行分析，标注异常项：

- **CPU**：1分钟负载 > CPU核心数 × 2 → 警告
- **内存**：使用率 > 85% → 警告，> 95% → 严重
- **磁盘**：任意挂载点使用率 > 85% → 警告，> 95% → 严重
- **Docker**：存在非 running/healthy 状态的容器 → 列出
- **Tailscale**：不在线 → 严重

### 5. 生成报告

输出格式（手机友好，开头摘要，少用分割线）：

```
📊 服务器巡检报告 | YYYY-MM-DD HH:MM

X台在线，Y个紧急，Z个警告，整体还行不用慌。

🚨 紧急
• [设备名] 具体问题描述

⚠️ 警告
• [设备名] 具体问题描述

---

☁️ 阿里云VPS (100.64.0.11) — 运行X天
CPU X核 负载X.XX ✅ | 内存 X/XG ✅ | 磁盘 X% ⚠️
Docker X容器: X跑X停 (具体说明)

🖥️ Ubuntu VM (100.64.0.1) — 运行X天
CPU X核 负载X.XX ✅ | 内存 X/XG ✅ | Swap X% ⚠️
磁盘 X% ⚠️ | VMware共享 X%
Docker X容器全部在线 ✅
Tailscale X台设备可见 ✅

💾 极空间NAS (100.64.0.6) — 运行X天
CPU/内存/存储 状态汇总
Docker状态

📡 GL-MT2500路由器 (100.64.0.31) — 运行X天
负载/内存/温度 状态
DHCP X台设备在线

---

💡 建议
1. 最紧急的操作建议
2. 次优先的操作建议
...
```

格式要求：
- 开头第一行必须是"X台在线，Y个紧急，Z个警告"的一句话摘要
- 紧急和警告部分放在设备详情之前
- 每台设备用 emoji 标识（☁️VPS 🖥️VM 💾NAS 📡路由器）
- 指标用 ✅⚠️🚨 标注状态，一目了然
- 分割线只用 `---`，不用 `═══` 等重分隔符
- 语气轻松自然，像朋友汇报一样

### 6. 邮件推送

如果用户要求推送报告，使用 Agently Mail CLI：

```bash
agently-cli message +send --to "1448960082@qq.com" --subject "服务器巡检报告 $(date +%Y-%m-%d)" --body "<报告内容>"
```

Agently Mail 需要两步确认：先执行 +send 获取 confirmation_token，再带 --confirmation-token 参数重发。

## 错误处理

- SSH 连接失败 → 标记"不可达"，继续下一台，不中断
- 命令执行超时 → 标记"超时"，记录错误信息
- 全部设备不可达 → 检查本机网络/Tailscale 状态
- NAS 的 SSH 端口是 22222，注意不要和标准 22 混淆

## 特殊注意事项

- 极空间 NAS 的 moviepilot-v2 容器偶尔挂掉，巡检时重点关注该容器状态
- Ubuntu VM 有 44 个容器，输出较多时做分组摘要
- 阿里云 VPS 是唯一有公网 IP 的设备，检查时额外关注外部连通性

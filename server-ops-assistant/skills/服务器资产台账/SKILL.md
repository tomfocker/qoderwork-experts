---
name: 服务器资产台账
version: 1.0.0
description: Server asset inventory management — maintain device list, connection parameters, status tracking, and change history
description_zh: 维护服务器设备清单和连接参数，追踪各设备状态变更和运维历史
user-invocable: true
argument-hint: 指定操作（如"更新台账"、"查看设备状态"、"添加设备"、"变更记录"）
---

# 服务器资产台账

维护服务器设备清单，追踪各设备的状态变更。

## 功能

1. **查看台账**：显示当前所有设备信息
2. **更新台账**：通过 SSH 检测设备在线状态并更新
3. **添加/修改设备**：新增设备或更新现有设备信息
4. **查看变更记录**：显示设备历史变更

## 台账文件

台账数据存储在 [references/server-inventory.md](references/server-inventory.md)。

读取台账时直接展示表格内容，按以下分组展示：
- **活跃设备**：正常运行的设备，显示连接参数和服务信息
- **待维护设备**：需要维修但暂未处理的设备
- **离线设备**：当前不在线的设备

## 操作流程

### 查看台账

直接读取并展示台账文件内容。按用户需求过滤：
- "所有设备" → 展示全部
- "活跃设备" → 只展示活跃设备表
- "某个设备" → 只展示该设备行

### 更新台账（状态刷新）

通过 SSH 逐一检测各活跃设备的在线状态和基本信息：

```bash
# 检测 Tailscale 连通性
tailscale status 2>/dev/null

# 对每台设备 SSH 检测基本信息
ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no -p <端口> <用户>@<IP> "uname -a && uptime && date && free -h 2>/dev/null && df -h / 2>/dev/null && docker ps -q 2>/dev/null | wc -l"
```

更新台账文件中对应设备的信息（如有变化）。

### 添加/修改设备

当用户提供新设备信息或要求修改现有设备时：
1. 读取当前台账
2. 按用户提供的信息更新对应条目
3. 在"变更记录"部分添加一条记录，格式：`- YYYY-MM-DD: <变更描述>`
4. 写回台账文件

### 查看变更记录

展示台账文件中"变更记录"部分的所有条目，按时间倒序排列。

## 变更记录规则

每次设备信息变化时，在台账的"变更记录"部分追加一条：

```
- YYYY-MM-DD: <设备名> — <变更描述>
```

变更类型包括：
- 设备上线/下线
- IP 地址变化
- Docker 容器数量变化
- 服务新增/移除
- 安全事件（后门发现/清理）
- 系统升级/重装

## 输出格式

```
📋 服务器资产台账
更新时间: YYYY-MM-DD

═══ 活跃设备 (X台) ═══
• 阿里云VPS — 反向代理/穿透 — ✅ 在线 — Docker: 3容器
• Ubuntu VM — Docker主宿主机 — ✅ 在线 — Docker: 44容器
• 极空间NAS — 存储/媒体 — ✅ 在线
...

═══ 待维护 (X台) ═══
• fatcow Linux — ⚠️ 内核被篡改，需重装

═══ 离线 (X台) ═══
• notebook, phone, fatcow-test, xuniji, openclaw

═══ 最近变更 ═══
- 2026-07-01: 本机Windows 清除三个后门
- 2026-06-30: 初始台账创建
```

## 邮件通知

如果检测到重要变更（设备上下线、IP变化等），通过 Agently Mail 通知：

```bash
agently-cli message +send --to "1448960082@qq.com" --subject "设备状态变更" --body "<变更详情>"
```

## 安全注意

- 台账中不存储明文密码，只记录连接参数（IP、端口、用户名）
- 密码信息仅存在于用户的私人记忆/对话中，不写入台账文件
- 台账文件作为插件参考材料，不会被外部分享

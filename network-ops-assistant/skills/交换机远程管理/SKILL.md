---
name: 交换机远程管理
version: 1.0.0
description: Remotely manage Huawei VRP switches via Telnet — execute display commands, check port status, VLAN config, and more.
description_zh: 通过 Telnet 远程管理华为 VRP 交换机，执行查看命令、检查端口状态、VLAN 配置等。
user-invocable: true
argument-hint: 提供交换机IP和密码，或描述你想执行的运维操作
---

# 交换机远程管理

通过 Telnet 远程连接华为 S 系列交换机（VRP 系统），执行运维命令并分析结果。

## 前置条件

- 用户需提供：交换机 IP、Telnet 端口（默认 23）、登录密码
- 当前机器能通过 TCP 连通目标交换机（用 `Test-NetConnection` 验证）
- 如果用户之前提供过连接信息，直接复用，不要反复追问

## 执行流程

### 1. 连通性测试

先用 PowerShell 测试端口是否可达：

```powershell
powershell -NoProfile -Command "Test-NetConnection -ComputerName {IP} -Port {端口} -WarningAction SilentlyContinue | Select-Object ComputerName, RemotePort, TcpTestSucceeded"
```

如果 `TcpTestSucceeded` 为 `False`，告知用户网络不通，建议检查路由、ACL 或交换机管理口状态。

### 2. Telnet 会话脚本

**核心原则**：用 PowerShell 的 `System.Net.Sockets.TcpClient` 模拟 Telnet 会话，不依赖系统 telnet.exe。

将以下脚本写入 `.ps1` 文件后执行（变量不能直接在 cmd.exe 里传，`$` 会被吞掉）：

```powershell
$tcp = New-Object System.Net.Sockets.TcpClient
$tcp.Connect('{IP}', {端口})
$stream = $tcp.GetStream()
$stream.ReadTimeout = 8000

# 读取 Banner
$buffer = New-Object byte[] 4096
$stream.Read($buffer, 0, $buffer.Length) | Out-Null

# 发送密码
$passBytes = [System.Text.Encoding]::ASCII.GetBytes("{密码}`r`n")
$stream.Write($passBytes, 0, $passBytes.Length)
Start-Sleep -Seconds 2

# 读取登录响应
$buffer2 = New-Object byte[] 8192
$stream.Read($buffer2, 0, $buffer2.Length) | Out-Null
```

### 3. 关闭分页（关键步骤）

登录后第一件事必须关闭分页，否则输出会被 `---- More ----` 截断：

```
screen-length 0 temporary
```

### 4. 执行命令的辅助函数

```powershell
function Send-Command {
    param([string]$Command, [int]$WaitMs = 2000)
    $cmdBytes = [System.Text.Encoding]::ASCII.GetBytes("$Command`r`n")
    $stream.Write($cmdBytes, 0, $cmdBytes.Length)
    Start-Sleep -Milliseconds $WaitMs
    $allData = ""
    $readBuf = New-Object byte[] 32768
    $stream.ReadTimeout = 3000
    while ($true) {
        try {
            $n = $stream.Read($readBuf, 0, $readBuf.Length)
            if ($n -gt 0) {
                $allData += [System.Text.Encoding]::Default.GetString($readBuf, 0, $n)
                if ($allData -match "---- More ----") {
                    $spaceBytes = [System.Text.Encoding]::ASCII.GetBytes(" ")
                    $stream.Write($spaceBytes, 0, $spaceBytes.Length)
                    $allData = $allData -replace "---- More ----", ""
                    Start-Sleep -Milliseconds 500
                } else { break }
            } else { break }
        } catch { break }
    }
    return $allData
}
```

遇到 `---- More ----` 时自动发送空格翻页，确保拿到完整输出。

### 5. 结束会话

命令执行完毕后发送 `quit` 并关闭 TCP 连接。

## 常用华为 VRP 命令速查

详细的命令参考见 [华为VRP命令速查](references/huawei-vrp-commands.md)。

最常用的几个：

- `display version` — 设备型号、系统版本、运行时间
- `display interface brief` — 所有端口状态一览
- `display vlan` — VLAN 划分和端口归属
- `display ip interface brief` — 三层接口 IP 信息
- `display mac-address` — MAC 地址表
- `display arp` — ARP 表
- `display current-configuration` — 当前完整配置（输出很长，慎用）
- `display cpu-usage` — CPU 利用率
- `display memory` — 内存使用情况
- `display logbuffer` — 系统日志缓冲区

## 结果分析要点

拿到交换机输出后，主动分析以下方面：

- **端口异常**：有 inErrors/outErrors 的端口，流量利用率偏高的端口
- **down 口排查**：区分 administratively down（人工关闭）和物理 down
- **VLAN 一致性**：检查端口 VLAN 归属是否合理，有无孤立端口
- **系统资源**：CPU/内存是否接近告警阈值
- **运行时间**：uptime 异常短说明最近重启过，需关注原因

## 安全注意

- 脚本文件中会包含明文密码，执行完毕后必须立即删除临时脚本
- Telnet 是明文协议，建议用户有条件时切换到 SSH（Stelnet）
- 不要在输出中回显密码

## 端口状态监控与邮件告警

支持对指定端口设置定时监控，状态变化时通过 Agently Mail 自动发邮件通知。

### 监控脚本

监控脚本位于插件目录下：`port-monitor.ps1`

核心流程：
1. Telnet 连接交换机，执行 `display interface brief`
2. 解析目标端口的 PHY/Protocol 状态（接口名用完整格式如 `GigabitEthernet0/0/19`，输出中不能用缩写 `GE0/0/19`）
3. 与 `port19_state.txt` 中记录的上次状态对比
4. 状态变化时通过 `agently-cli message +send` 发送告警邮件（需处理两步确认：先拿 confirmation_token，再用 `--confirmation-token` 确认发送）

### Agently Mail 前置配置

```bash
npm install -g @tencent-qqmail/agently-cli
agently-cli auth login   # 微信扫码授权
agently-cli +me           # 确认邮箱地址
```

### 设置定时监控

用 QoderWork 定时任务（cron）定期执行监控脚本，例如每 30 分钟巡检一次：

```
运行 PowerShell 脚本：
powershell -NoProfile -ExecutionPolicy Bypass -File "插件目录\port-monitor.ps1"
```

脚本参数可通过 param 块自定义：SwitchIP、SwitchPort、Password、MonitorInterface、NotifyTo、StateFile。

### 解析注意事项

- 华为交换机 `display interface brief` 输出中接口名是完整格式 `GigabitEthernet0/0/19`
- 不支持 `display interface GigabitEthernet0/0/19 brief`（Too many parameters 错误）
- 正则匹配需用完整接口名，如 `"GigabitEthernet0/0/19\s+(up|down|\*down)\s+(up|down)"`

## If Connectors Available

If **文档平台** is connected:
- 将巡检结果自动发布为运维文档

If **任务工具** is connected:
- 发现异常时自动创建维修工单

If no connectors available:
- 结果直接输出到对话中（默认行为）

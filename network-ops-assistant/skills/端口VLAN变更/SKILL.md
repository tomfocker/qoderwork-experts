---
name: 端口VLAN变更
version: 1.0.0
description: Move a switch port to a different VLAN (commonly VLAN 444 for internet isolation).
description_zh: 将交换机端口划分到指定VLAN，常用场景：划入VLAN 444断网隔离。
user-invocable: true
argument-hint: 例如：把21口划到VLAN 444
---

# 端口VLAN变更

将华为交换机指定端口从当前 VLAN 切换到目标 VLAN。最常用场景：将端口划入 VLAN 444（保留的隔离VLAN，不能上网），用于临时断网或设备隔离。

## 已知环境

- 交换机：172.16.20.217（YouJiaoLou-F2-1-3），华为 S5700S-52P-LI-AC
- Telnet 密码：用户已配置（从记忆或插件脚本中复用，不要反复追问）
- VLAN 444：隔离VLAN，仅 Trunk 口通过，无网络出口，用于断网隔离
- VLAN 1210/1220/1320：正常上网的业务VLAN

## 执行流程

### 1. 确认变更内容

用户只需提供：端口号 + 目标 VLAN。如未指定 VLAN，默认使用 444（隔离）。

变更前先查看端口当前配置，确认当前 VLAN 和描述信息，让用户确认后再执行。

### 2. Telnet 登录交换机

使用 `交换机远程管理` 技能中的 Telnet 连接方法（TcpClient 模拟，screen-length 0 temporary 关分页）。

### 3. 执行配置命令

```
system-view
interface GigabitEthernet0/0/{端口号}
port link-type access
port default vlan {目标VLAN}
quit
return
save
```

**关键细节**：
- 接口名必须用完整格式 `GigabitEthernet0/0/21`，不能用缩写 `GE0/0/21`
- `save` 必须在用户视图 `<xxx>` 下执行，不能在系统视图 `[xxx]` 下
- `save` 会弹出 `Are you sure to continue?[Y/N]` 确认，需发送 `y` 回应
- 端口已经是 access 模式时，`port link-type access` 不会有额外提示

### 4. 验证

执行 `display current-configuration interface GigabitEthernet0/0/{端口号}` 确认 `port default vlan` 已变更为目标值。

### 5. 恢复端口

如果需要恢复上网，将端口划回原来的业务 VLAN（通常是 1210/1220/1320 之一）。变更前记录的原始 VLAN 要告知用户，方便恢复。

## 常见场景

| 场景 | 命令 |
|------|------|
| 断网隔离 | 划入 VLAN 444 |
| 恢复上网 | 划回原 VLAN（如 1210） |
| 调整到指定网段 | 划入对应业务 VLAN |

## If Connectors Available

If **通知渠道** is connected:
- VLAN 变更操作完成后自动发送通知给相关人员

If no connectors available:
- 结果直接输出到对话中

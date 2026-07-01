---
name: 网络故障诊断
version: 1.0.0
description: Diagnose campus network faults — physical layer, DHCP conflicts, MAC tracing, port comparison, DHCP Snooping, security audit.
description_zh: 校园网故障诊断：物理层排查、私接DHCP排查、MAC定位、端口对比、DHCP Snooping、安全审计，含根因速查表和真实案例。
user-invocable: true
argument-hint: 描述故障现象，例如：107房间不能上网 / 设备拿到了192.168的IP
---

# 网络故障诊断

远程连接华为交换机，根据用户描述的故障现象自动执行诊断命令，分析根因并给出修复建议。

## 前置条件

- 交换机连接信息：IP、端口（默认23）、密码（从记忆或插件复用，不反复追问）
- 故障定位信息：端口号 / 房间名 / 设备MAC / IP地址（根据场景需要）

使用 `交换机远程管理` 技能的 Telnet 连接方法建立会话。

## 路由规则

根据用户描述匹配场景，自动进入对应诊断流程：

| 用户描述关键词 | 进入场景 |
|---------------|---------|
| 不能上网、断网、网速慢、时断时续 | [场景A：物理层排查](#场景a房间不能上网物理层排查) |
| 拿到错误IP、192.168而非10.x、DHCP问题 | [场景B：DHCP冲突排查](#场景b设备获取到错误ipdhcp-冲突排查) |
| 找设备、定位端口、MAC/IP查位置 | [场景C：IP/MAC定位](#场景c通过-ipmac-定位设备物理位置) |
| 对比、正常口vs故障口 | [场景D：对比诊断](#场景d故障端口-vs-正常端口对比诊断) |
| DHCP Snooping、封堵私接 | [场景E：安全配置](#场景e安全配置dhcp-snooping--端口隔离) |
| 安全审计、查登录、查用户 | [场景F：安全审计](#场景f交换机安全审计) |

无法匹配时，先执行 `display interface brief` 做全局扫描，再引导用户描述具体现象。

---

## 场景A：房间不能上网（物理层排查）

触发条件：用户反馈某房间断网、网速慢、时断时续。

### 步骤

1. **查看端口详情**：`display interface GigabitEthernet 0/0/{端口号}`

   关注以下字段：
   - **current state**：UP 还是 DOWN
   - **Speed**：100M 还是 1000M（100M = 网线可能只有4芯通）
   - **CRC / Total Error**：>0 则物理层有问题
   - **Last 300 seconds input/output rate**：流量是否为零

2. **查端口日志**：`display logbuffer | include 0/0/{端口号}`

   检查是否有频繁 UP/DOWN 记录。

3. 如果用户提供正常工作的对照端口，转入 [场景D](#场景d故障端口-vs-正常端口对比诊断)。

### 根因判断

| 症状 | 诊断 | 处理 |
|------|------|------|
| 频繁 UP/DOWN + 100M | 网线物理损伤（4芯通） | 更换网线或重新打水晶头 |
| 频繁 UP/DOWN + 1000M + CRC>0 | 网线接触不良 | 重新插拔或更换 |
| 端口 DOWN 且无历史 UP 记录 | 对端关机或线缆断开 | 检查房间设备 |
| 端口 UP 但流量为 0 | 设备未获取 IP 或未开机 | 检查设备网络配置 |

### 真实案例

- **GE0/0/5（106房间）**：100M 速率 + 频繁 UP/DOWN → 网线损伤，换线解决
- **GE0/0/21（107希沃）**：1000M 但 CRC=99 + 频繁 UP/DOWN → 线缆接触不良，重新插拔解决
- **GE0/0/13（101希沃）**：1000M + CRC=0 + 流量正常 → 物理层完好，问题在 DHCP（转入场景B）

---

## 场景B：设备获取到错误IP（DHCP 冲突排查）

触发条件：用户反馈设备拿到 192.168.x.x 而非预期的 10.x.x.x。

### 诊断逻辑

设备获取的 IP 网段与校园网规划不一致（如 192.168.10.x 而非 10.10.x.x），说明 VLAN 内存在**私接 DHCP 服务器**（通常来自家用路由器 LAN 口反插）。

### 排查步骤

1. 确认故障设备所在 VLAN：
   ```
   display port vlan GigabitEthernet 0/0/{端口号}
   ```

2. 查看该 VLAN 所有 MAC 地址，排查非学校设备：
   ```
   display mac-address vlan {VID}
   ```

3. 通过排除法缩小范围：逐个 shutdown 可疑端口，观察故障设备是否恢复正常。

4. 若无法物理定位，直接启用 DHCP Snooping 封堵（转 [场景E](#场景e安全配置dhcp-snooping--端口隔离)）。

### 关键认知

DHCP Discover 是广播帧，私接路由器的 DHCP 应答会泛洪到整个 VLAN，影响同 VLAN 下**所有房间**——不是只影响私接设备所在的房间。

### 真实案例

VLAN 1210 内某设备 DHCP 分发 192.168.10.x → 101 希沃拿到 192.168.10.4 → 无法上网。排除 106 房间和 19 房间后，最终通过 DHCP Snooping 全局封堵。

---

## 场景C：通过 IP/MAC 定位设备物理位置

触发条件：用户知道设备 IP 或 MAC 后缀，需要找到它在哪个端口。

### 步骤

1. 若用户只知 IP，先让用户在能正常上网的电脑上 `arp -a` 查对应的 MAC。

2. 在交换机上按 MAC 查找：
   ```
   display mac-address | include {MAC后4位}
   ```
   或按 VLAN 缩小范围：
   ```
   display mac-address vlan {VID}
   ```

3. 找到 `Learned-From` 字段即为物理端口。

### 注意

纯二层交换机无法通过 `display arp` 查到接入设备的 IP（只有交换机自己有 IP 的 VLAN 才有 ARP 表），必须通过 MAC 表定位。

### 真实案例

用户提供 MAC 后缀 55F7 → `display mac-address vlan 1210` → 找到 `7424-ca1e-55f7` on GE0/0/13（101希沃）。

---

## 场景D：故障端口 vs 正常端口对比诊断

触发条件：用户提供一个能正常上网的对照端口。

### 操作

对两个端口依次执行：
```
display interface GigabitEthernet 0/0/{端口号}
display port vlan GigabitEthernet 0/0/{端口号}
display mac-address GigabitEthernet 0/0/{端口号}
display stp interface GigabitEthernet 0/0/{端口号}
```

### 对比关键指标

| 指标 | 故障暗示 |
|------|----------|
| Speed 不同 | 线缆问题（故障口降速） |
| CRC 差异大 | 物理层劣化 |
| 出流量极低 vs 正常 | DHCP 失败或设备配置错误 |
| MAC 数量 | 下挂设备是否正常 |
| STP 状态 | Forwarding vs 其他 |
| 历史峰值流量 | 端口是否曾被正常使用 |

---

## 场景E：安全配置（DHCP Snooping / 端口隔离）

### 启用 DHCP Snooping（防私接 DHCP）

```
system-view
dhcp enable
dhcp snooping enable
vlan {VID}
 dhcp snooping enable
 quit
interface GigabitEthernet 0/0/{上行口}
 dhcp snooping trusted
 quit
```

对所有上行口（Trunk口，通常是 GE0/0/46-48）重复配置 trusted。

### 临时端口隔离（切 VLAN）

使用 `端口VLAN变更` 技能，将故障端口划入 VLAN 444 隔离。

底层原理：将端口 PVID 从业务 VLAN 切换到无网关的隔离 VLAN，物理链路保持 UP 但三层不通。

---

## 场景F：交换机安全审计

### 检查项

```
display ssh server status          # SSH 是否开启
display local-user                 # 本地用户列表（注意未知账户如 huawei）
display acl all                    # VTY 访问控制
display users                      # 当前在线用户
display logbuffer | include LOGIN  # 登录审计
```

### 注意

Telnet 明文传输密码，若 SSH 可用应立即建议切换。

---

## 根因速查表

| 症状 | 根因 | 处理 |
|------|------|------|
| UP/DOWN 抖动 + 100M | 网线 4 芯通 | 换线 |
| UP/DOWN 抖动 + CRC>0 | 线缆接触不良 | 重新插拔或换线 |
| 获取 192.168.x.x | 私接 DHCP | DHCP Snooping 封堵 |
| 端口 UP 但流量约0 | 设备未获取 IP | 检查 DHCP / 设备配置 |
| DOWN 无抖动历史 | 对端关机或断线 | 查房间 |
| CRC 高 + 碎片多 | 电磁干扰或线缆老化 | 换线 |
| MAC 漂移 | 下游环路 | 查房间交换机接线 |

---

## 注意事项

- **VRP 版本差异**：`display cpu-usage`、`display logbuffer | include` 等命令可能在部分版本报错，需换写法
- **二层交换机无 ARP**：`display arp interface` 返回空是正常的
- **改配置先备份**：`display this` 确认当前配置
- **改完要保存**：`save` + `y`，否则重启丢失

## If Connectors Available

If **通知渠道** is connected:
- 故障诊断结果自动发送通知

If **文档平台** is connected:
- 将诊断报告归档为运维文档

If no connectors available:
- 结果直接输出到对话中

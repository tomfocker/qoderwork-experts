# 华为/H3C VRP 常用诊断命令参考

## 系统信息
| 命令 | 用途 |
|------|------|
| `display version` | 设备型号、VRP版本、运行时间、内存/Flash |
| `display device` | 板卡/子卡状态 |
| `display cpu-usage` | CPU 使用率（部分版本不支持） |
| `display memory-usage` | 内存使用率 |
| `display temperature` | 设备温度 |

## 接口诊断
| 命令 | 用途 |
|------|------|
| `display interface brief` | 所有接口简要状态 |
| `display interface GigabitEthernet X/X/X` | 接口详情：速率/双工/流量/错误/光功率 |
| `display interface X/X/X | include error\|CRC\|drop\|discard` | 筛选错误统计 |
| `display ip interface brief` | 三层接口 IP 地址和状态 |

## VLAN 与链路类型
| 命令 | 用途 |
|------|------|
| `display vlan` | 所有 VLAN 概要 |
| `display vlan <VID>` | 指定 VLAN 详情（端口成员、Tag/Untag） |
| `display port vlan GigabitEthernet X/X/X` | 端口 VLAN 归属 |
| `display current-configuration interface X/X/X` | 端口完整配置（也可能用 system-view + display this） |

## MAC 地址
| 命令 | 用途 |
|------|------|
| `display mac-address` | 整个 MAC 表 |
| `display mac-address vlan <VID>` | 按 VLAN 查询 MAC |
| `display mac-address GigabitEthernet X/X/X` | 按端口查询 MAC |
| `display mac-address flapping record` | MAC 漂移记录（环路检测） |
| `display mac-address sticky` | 粘滞 MAC |

## ARP
| 命令 | 用途 |
|------|------|
| `display arp` | 完整 ARP 表 |
| `display arp interface X/X/X` | 按接口查询（仅三层口有效） |
| `display arp all` | ARP 表全部条目 |

## STP / 生成树
| 命令 | 用途 |
|------|------|
| `display stp` | STP 全局状态（根桥、模式） |
| `display stp brief` | STP 端口摘要 |
| `display stp interface X/X/X` | 指定端口 STP 状态 |
| `display stp topology-change` | 拓扑变更统计 |

## 日志
| 命令 | 用途 |
|------|------|
| `display logbuffer` | 日志缓冲区（默认 512 条） |
| `display logbuffer \| include <keyword>` | 过滤日志（可能不支持管道） |
| `display trapbuffer` | 告警缓冲区 |

## DHCP
| 命令 | 用途 |
|------|------|
| `display dhcp snooping` | DHCP 监听状态 |
| `display dhcp relay` | DHCP 中继配置 |
| `display dhcp server` | DHCP 服务器状态 |

## 安全策略
| 命令 | 用途 |
|------|------|
| `display acl all` | ACL 列表 |
| `display traffic-policy applied-record` | 流策略应用记录 |
| `display storm-control` | 风暴控制状态 |
| `display port-security` | 端口安全 |

## 路由
| 命令 | 用途 |
|------|------|
| `display ip routing-table` | 路由表 |

## 配置
| 命令 | 用途 |
|------|------|
| `display current-configuration` | 当前运行配置（可能很大） |
| `display current-configuration \| include <keyword>` | 过滤配置 |
| `display saved-configuration` | 已保存的配置 |

## 常用操作（需谨慎）
| 命令 | 用途 | 风险 |
|------|------|------|
| `system-view` → `interface X/X/X` → `shutdown` | 关闭端口 | 业务中断 |
| `system-view` → `interface X/X/X` → `undo shutdown` | 开启端口 | — |
| `system-view` → `interface X/X/X` → `display this` | 查看接口配置 | — |
| `ping <IP>` | 连通性测试 | — |
| `tracert <IP>` | 路由追踪 | — |

## VRP 常见注意事项
1. **管道符 `| include`** — 部分老版本不支持，会报 `Error: Unrecognized command`
2. **分页 `---- More ----`** — 长输出会暂停，需要发送空格继续或设置 `screen-length 0 temporary` 禁用分页
3. **命令补全** — Tab 键可补全命令
4. **`?` 帮助** — 输入 `?` 可查看可用命令
5. **Vlanif vs Vlan-interface** — VRP 5.x 使用 `interface Vlanif <ID>`，部分版本用 `interface Vlan-interface <ID>`

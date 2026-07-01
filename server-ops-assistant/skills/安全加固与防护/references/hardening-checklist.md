# 安全加固清单

基于用户实际入侵事件总结的安全基线，逐项检查并记录合规状态。

## SSH 加固

| 检查项 | 期望值 | 说明 |
|:---|:---|:---|
| PermitRootLogin | no 或 prohibit-password | 禁止 root 密码登录 |
| PasswordAuthentication | no | 仅允许密钥认证 |
| PubkeyAuthentication | yes | 启用公钥认证 |
| PermitEmptyPasswords | no | 禁止空密码 |
| X11Forwarding | no | 除非需要 GUI |
| MaxAuthTries | ≤ 5 | 限制认证尝试次数 |
| LoginGraceTime | ≤ 60 | 登录超时时间(秒) |
| ClientAliveInterval | 300 | 空闲超时(秒) |
| ClientAliveCountMax | 2 | 最大空闲计数 |
| 非标准 SSH 端口 | 可选 | 降低被扫概率 |
| sshd_config.d/ 检查 | 无异常覆盖文件 | 防止配置被隐藏修改 |

## 防火墙

| 检查项 | 期望值 | 说明 |
|:---|:---|:---|
| 防火墙已启用 | 是 | ufw/iptables/firewalld |
| 默认策略 | DROP/REJECT | 默认拒绝入站 |
| 仅开放必要端口 | 是 | 最小化暴露面 |
| 公网设备(VPS)额外检查 | 是 | 限制来源 IP、geo-blocking |
| frps 端口范围 | 已限制 | 不暴露不必要的穿透端口 |

## 账户安全

| 检查项 | 期望值 | 说明 |
|:---|:---|:---|
| 无异常 UID 0 账户 | 是 | 仅 root 为 UID 0 |
| 无 tempadmin 类临时账户 | 是 | 参照历史入侵 |
| sudo 权限最小化 | 是 | 仅必要用户有 sudo |
| 密码复杂度 | ≥12位 | 混合字符 |
| 过期账户清理 | 已清理 | 无废弃账户 |

## 入侵检测

| 检查项 | 期望值 | 说明 |
|:---|:---|:---|
| fail2ban 已安装 | 是 | 自动封禁暴力破解 |
| 无异常 crontab | 是 | 后门常见藏身处 |
| 无可疑 systemd 服务 | 是 | 参照 escsvc 后门 |
| /tmp 无可执行文件 | 是 | 后门常见位置 |
| 无异常 SUID 文件 | 是 | 权限提升风险 |
| /etc/ld.so.preload 为空 | 是 | rootkit 常用手法 |
| 无异常内核模块 | 是 | 参照 fatcow 内核篡改 |
| 无异常外连 | 是 | 反向 shell/C2 通信 |

## Docker 安全

| 检查项 | 期望值 | 说明 |
|:---|:---|:---|
| Docker socket 不暴露 | 是 | 不绑定 0.0.0.0:2375 |
| 容器不以 root 运行 | 尽量 | 降低逃逸风险 |
| 镜像来源可信 | 是 | 避免未经验证的镜像 |
| 敏感数据用 secrets/env | 是 | 不硬编码在镜像中 |

## 备份安全

| 检查项 | 期望值 | 说明 |
|:---|:---|:---|
| 备份定期执行 | 是 | restic 快照正常更新 |
| 备份可恢复性验证 | 每月至少1次 | 备份不等于可恢复 |
| SSH 密钥有备份 | 是 | 防止丢失访问权限 |

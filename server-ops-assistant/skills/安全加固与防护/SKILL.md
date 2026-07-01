---
name: 安全加固与防护
version: 1.0.0
description: Security hardening audit via SSH — SSH config, firewall rules, suspicious processes, port scanning, fail2ban status, based on real intrusion experience
description_zh: 通过SSH执行安全加固审计，包括SSH配置、防火墙规则、可疑进程、端口扫描、fail2ban状态，基于真实入侵事件经验
user-invocable: true
argument-hint: 指定设备名或"全部"执行安全审计
---

# 安全加固与防护

对服务器执行安全审计和加固检查，基于用户过去遭受入侵的经验（后门程序、内核篡改、未授权账户）。

## 前置条件

- 读取 [服务器台账](references/server-inventory.md) 获取设备连接信息
- 参考 [安全加固清单](references/hardening-checklist.md) 作为检查标准

## 安全背景

用户环境曾遭受以下类型的入侵（已清理）：
- **python3-libstud**：伪装为 Python 库的后门程序
- **escsvc**：伪装为系统服务的后门
- **tempadmin**：临时管理员账户，用于持久化访问
- **fatcow Linux 内核被篡改**：无法原地修复，需重装系统

这些经验应贯穿在所有安全检查中——特别关注伪装成正常进程/服务的后门。

## 审计流程

### 1. SSH 配置审计

```bash
# 检查 SSH 配置
cat /etc/ssh/sshd_config | grep -iE "PermitRootLogin|PasswordAuthentication|PubkeyAuthentication|Port |AllowUsers|AllowGroups|PermitEmptyPasswords|X11Forwarding|MaxAuthTries|LoginGraceTime"

# 检查 authorized_keys（是否有未授权的公钥）
for user in root $(awk -F: '$3 >= 1000 {print $1}' /etc/passwd); do
  echo "--- $user ---"
  cat /home/$user/.ssh/authorized_keys 2>/dev/null || cat /root/.ssh/authorized_keys 2>/dev/null || echo "(none)"
done

# 检查 SSH 端口是否已修改（非默认22）
grep -i "^Port" /etc/ssh/sshd_config
```

重点关注：
- `PermitRootLogin` 是否设为 `yes`（公网设备应为 `no` 或 `prohibit-password`）
- `PasswordAuthentication` 是否为 `yes`（建议密钥认证）
- 是否有未识别的 authorized_keys 条目
- 是否有隐藏的非标准 SSH 配置（`/etc/ssh/sshd_config.d/` 目录）

### 2. 防火墙规则检查

```bash
# iptables
iptables -L -n --line-numbers
iptables -L -n -t nat

# ufw（Ubuntu 常用）
ufw status verbose 2>/dev/null

# firewalld
firewall-cmd --list-all 2>/dev/null

# 检查开放端口
ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null
```

重点关注：
- 是否有不该开放的端口暴露到公网
- 阿里云 VPS（公网IP: 39.107.245.108）的暴露面是否最小化
- frps 穿透端口范围是否合理，是否限制了来源 IP
- 是否有反向 shell 或异常出站连接

### 3. 可疑进程和连接检查

```bash
# 检查高权限进程
ps auxf | head -50

# 检查网络连接（关注外连）
ss -tnp 2>/dev/null || netstat -tnp 2>/dev/null

# 检查异常 crontab（后门常见藏身之处）
for user in root $(awk -F: '$3 >= 1000 {print $1}' /etc/passwd); do
  echo "=== crontab: $user ==="
  crontab -u $user -l 2>/dev/null || echo "(none)"
done

# 检查系统级定时任务
ls -la /etc/cron.d/ /etc/cron.daily/ /etc/cron.hourly/ 2>/dev/null
cat /etc/crontab

# 检查 systemd 服务（后门常伪装为服务）
systemctl list-units --type=service --state=running
# 重点检查非标准路径的服务
systemctl list-units --type=service --state=running | while read line; do
  unit=$(echo "$line" | awk '{print $1}')
  path=$(systemctl show "$unit" -p ExecStart 2>/dev/null | grep -oP '(?<=path=)[^ ]+')
  if [ -n "$path" ] && ! echo "$path" | grep -qE "^/(usr|opt|snap)/"; then
    echo "⚠️ 非标准路径服务: $unit -> $path"
  fi
done

# 检查 /tmp /var/tmp /dev/shm 中的可执行文件（后门常见位置）
find /tmp /var/tmp /dev/shm -type f -executable 2>/dev/null

# 检查异常 SUID/SGID 文件
find / -perm -4000 -type f 2>/dev/null | sort

# 检查 /etc/ld.so.preload（rootkit 常用手法）
cat /etc/ld.so.preload 2>/dev/null

# 检查内核模块（排查内核级后门，参照 fatcow 经验）
lsmod | head -30
```

### 4. fail2ban 检查

```bash
# 检查是否安装
which fail2ban-client 2>/dev/null && fail2ban-client status

# 检查封禁统计
fail2ban-client status sshd 2>/dev/null

# 如果未安装，建议安装
# apt install fail2ban -y && systemctl enable fail2ban
```

### 5. 用户账户审计

```bash
# 检查所有用户
cat /etc/passwd | awk -F: '$3 >= 1000 || $1 == "root" {print $1, $3, $7}'

# 检查 sudo 权限
getent group sudo 2>/dev/null || getent group wheel 2>/dev/null
cat /etc/sudoers.d/* 2>/dev/null

# 检查最近登录
last -20

# 检查失败登录
lastb -20 2>/dev/null

# 检查是否有隐藏用户（UID 0 的非 root 账户）
awk -F: '$3 == 0 {print $1}' /etc/passwd
```

重点关注：
- 是否存在 `tempadmin` 类账户（参照历史入侵）
- UID 0 的非 root 账户
- 有 sudo 权限的异常用户
- shell 为 `/bin/bash` 或 `/bin/sh` 的服务账户

### 6. 文件完整性基础检查

```bash
# 最近 7 天修改的系统文件
find /etc /usr/bin /usr/sbin -mtime -7 -type f 2>/dev/null | head -30

# 检查已知后门路径（参照历史入侵）
ls -la /usr/lib/python3*/dist-packages/libstud* 2>/dev/null
ls -la /usr/lib/escsvc* /usr/bin/escsvc* 2>/dev/null
getent passwd tempadmin 2>/dev/null

# 检查 /etc/hosts 是否被篡改
cat /etc/hosts
```

### 7. OpenWrt 专项检查（GL-MT2500 路由器）

```bash
# 检查已安装的额外包
opkg list-installed | grep -v "^base"

# 检查启动脚本
ls -la /etc/rc.local /etc/init.d/

# 检查防火墙配置
iptables -L -n
uci show firewall

# 检查已连接的 WiFi 设备
cat /tmp/dhcp.leases
```

## 输出格式

```
🔒 安全审计报告 — <设备名>
时间: YYYY-MM-DD HH:MM

═══ SSH 配置 ═══
✅ PermitRootLogin: no
⚠️ PasswordAuthentication: yes → 建议关闭
✅ PubkeyAuthentication: yes

═══ 防火墙 ═══
⚠️ 端口 8080 暴露到公网 → 确认是否必要
✅ 已封禁 IP: 127 个

═══ 可疑项 ═══
🚨 发现异常 cron 任务: */5 * * * * curl http://xxx → 立即检查
✅ /tmp 无可执行文件
✅ 无异常 SUID 文件

═══ 账户安全 ═══
✅ 无异常 UID 0 账户
✅ 无 tempadmin 类账户

📋 总结: X 项正常 / Y 项警告 / Z 项严重
```

## 告警规则

- 🚨 **高风险**（立即告警）：发现活跃后门、未授权 root 访问、内核模块异常、可疑外连
- ⚠️ **中风险**（报告列出）：密码认证未关闭、fail2ban 未安装、非标准端口暴露
- ℹ️ **低风险**（建议改进）：SSH 版本较旧、缺少日志轮转

高风险发现立即通过 Agently Mail 发送告警：

```bash
agently-cli message +send --to "1448960082@qq.com" --subject "🚨 安全告警: <设备名>" --body "<告警详情>"
```

## 安全规则

1. 不自动修改任何配置，只做检查和建议
2. 修改操作须逐项确认，说明影响范围
3. fatcow Linux 标记为不可信，仅记录当前状态
4. 阿里云 VPS 作为唯一公网设备，安全标准最高
5. 发现入侵迹象时，先保护现场（记录进程、网络连接），再建议处置方案

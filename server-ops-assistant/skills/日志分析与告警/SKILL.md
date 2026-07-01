---
name: 日志分析与告警
version: 1.0.0
description: System and Docker log analysis via SSH — detect brute force, abnormal logins, container crash loops, with email alerting
description_zh: 通过SSH分析系统日志和Docker日志，识别暴力破解、异常登录、容器反复重启等模式，通过邮件推送告警
user-invocable: true
argument-hint: 指定分析类型（如"安全检查"、"容器日志"、"最近24小时"）或设备名
---

# 日志分析与告警

收集并分析服务器日志，识别安全事件和异常模式。

## 前置条件

- 读取 [服务器台账](references/server-inventory.md) 获取设备连接信息

## 日志来源

### 系统日志
```bash
# 检查可用日志工具
which journalctl 2>/dev/null && echo "journalctl available"
which logwatch 2>/dev/null && echo "logwatch available"
ls /var/log/auth.log 2>/dev/null || ls /var/log/secure 2>/dev/null || echo "check syslog"
```

### 分析命令

```bash
# SSH 暴力破解检测
journalctl -u sshd --since "24 hours ago" 2>/dev/null | grep -i "failed\|invalid\|refused" | tail -50

# 认证日志（Debian/Ubuntu）
grep -i "failed\|invalid" /var/log/auth.log 2>/dev/null | tail -50

# 认证日志（RHEL/CentOS）
grep -i "failed\|invalid" /var/log/secure 2>/dev/null | tail -50

# 最近登录记录
last -20

# 失败登录记录
lastb -20 2>/dev/null

# 系统错误日志（最近24小时）
journalctl --since "24 hours ago" -p err --no-pager 2>/dev/null | tail -50

# 内核日志（OOM、硬件错误等）
dmesg --time-format iso | tail -30

# Docker 日志
docker ps -a --format '{{.Names}}' | while read c; do
  restarts=$(docker inspect "$c" --format '{{.RestartCount}}' 2>/dev/null)
  if [ "$restarts" -gt 3 ] 2>/dev/null; then
    echo "⚠️ $c: $restarts 次重启"
    docker logs --tail 20 "$c" 2>&1
  fi
done
```

## 异常检测模式

### 暴力破解检测
- SSH 登录失败次数 > 10次/小时 → 告警
- 同一 IP 短时间内多次失败（5分钟内 > 5次） → 高危告警
- 从非常规 IP 段登录 → 告警

分析命令：
```bash
# 统计各IP的失败次数
grep -i "failed" /var/log/auth.log 2>/dev/null | awk '{print $(NF-3)}' | sort | uniq -c | sort -rn | head -10

# 统计最近1小时的失败
grep -i "failed" /var/log/auth.log 2>/dev/null | awk -v d="$(date -d '1 hour ago' '+%b %d %H')" '$0 ~ d' | wc -l
```

### 异常登录检测
```bash
# 非工作时间登录（22:00-06:00）
last -F | awk '{print $5}' | grep -E "^(22|23|0[0-5]):"

# 来自新 IP 的登录
last -i | awk '{print $3}' | sort -u

# 检查当前登录会话
who
w

# 检查 sudo 使用记录
grep -i "sudo" /var/log/auth.log 2>/dev/null | tail -20
```

### 容器异常检测
```bash
# 重启循环检测
docker ps -a --format '{{.Names}}: Restarts={{.Status}}' | grep -i "restart"

# OOM killed 检测
dmesg | grep -i "oom\|killed process" | tail -10

# 容器错误日志关键词扫描
docker ps --format '{{.Names}}' | while read c; do
  errors=$(docker logs "$c" 2>&1 | grep -icE "error|fatal|panic|exception|traceback" | tail -100)
  if [ "$errors" -gt 10 ] 2>/dev/null; then
    echo "⚠️ $c: 最近100行日志有 $errors 条错误"
  fi
done
```

### 后门和入侵迹象

基于历史入侵经验（python3-libstud、escsvc、tempadmin），重点检查：

```bash
# 检查已知后门路径
ls -la /usr/lib/python3*/dist-packages/libstud* 2>/dev/null
ls -la /usr/lib/escsvc* /usr/bin/escsvc* 2>/dev/null
getent passwd tempadmin 2>/dev/null

# 检查可疑的定时任务
crontab -l 2>/dev/null
for f in /etc/cron.d/*; do echo "=== $f ==="; cat "$f" 2>/dev/null; done

# 检查异常网络连接（外连到非常规端口）
ss -tnp | grep -vE ":22 |:443 |:80 |:53 " | grep ESTAB

# 检查最近安装的可疑包
dpkg --log 2>/dev/null | tail -20
```

## 告警级别

| 级别 | 含义 | 典型场景 | 处理方式 |
|:---|:---|:---|:---|
| P0 | 立即处理 | 发现活跃后门、rootkit迹象、SSH爆破成功 | 立即告警+建议隔离 |
| P1 | 尽快处理 | 暴力破解高频、容器OOM反复、未知SUID | 告警+排查建议 |
| P2 | 关注 | 少量登录失败、容器偶尔重启、磁盘警告 | 汇总报告 |
| P3 | 信息 | 正常维护日志、定期任务执行 | 仅记录 |

## 邮件通知

汇总告警事件后通过 Agently Mail 推送：

```bash
agently-cli message +send --to "1448960082@qq.com" --subject "服务器日志告警 [P0:x P1:x]" --body "<告警详情>"
```

邮件内容格式：
```
告警时间: YYYY-MM-DD HH:MM
设备: <设备名>
事件:
- [P0] 发现可疑进程: /tmp/.hidden/payload
- [P1] SSH 暴力破解: 来自 1.2.3.4，过去1小时 523 次失败
- [P1] moviepilot-v2 容器重启 12 次

建议操作:
1. 检查 /tmp/.hidden/ 目录内容
2. 封禁 1.2.3.4
3. 查看 moviepilot 日志定位重启原因
```

## 分析策略

- 默认分析最近 24 小时日志
- 用户可指定时间范围（如"最近7天"、"上周五"）
- 用户可指定分析类型（安全/容器/系统/全部）
- 大日志文件做采样分析，不全量输出，给出统计摘要即可
- 重点关注 P0 和 P1 事件，P2/P3 做汇总

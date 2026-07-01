---
name: 备份与恢复
version: 1.0.0
description: Backup management via SSH — restic snapshots, container config export, backup verification, disaster recovery
description_zh: 通过SSH管理备份，包括restic快照操作、容器配置导出、备份完整性验证、灾备恢复
user-invocable: true
argument-hint: 指定操作（如"查看快照"、"执行备份"、"验证备份"、"导出容器配置"）
---

# 备份与恢复

管理服务器备份，包括 restic 快照、容器配置、关键数据。

## 前置条件

- 读取 [服务器台账](references/server-inventory.md) 获取设备和备份路径信息

## 备份架构

| 备份对象 | 备份工具 | 存储位置 | 当前状态 |
|:---|:---|:---|:---|
| Ubuntu VM 系统 | restic | D:\虚拟机共享存储\Ubuntu_Backups\repo | 最新快照 deccbb77 (2026-06-16) |
| Docker 容器配置 | docker 命令导出 | 待定义 | 待建立 |
| 容器数据卷 | restic / 手动 | 待定义 | 待建立 |

**restic 密码**：已在用户侧管理（执行时需用户提供或通过环境变量）

## restic 快照管理

```bash
# 列出所有快照
restic -r "D:\虚拟机共享存储\Ubuntu_Backups\repo" snapshots

# 查看最新快照详情
restic -r "D:\虚拟机共享存储\Ubuntu_Backups\repo" snapshots --latest 1

# 查看快照内容
restic -r "D:\虚拟机共享存储\Ubuntu_Backups\repo" ls latest --long

# 验证备份完整性
restic -r "D:\虚拟机共享存储\Ubuntu_Backups\repo" check

# 完整数据验证（耗时较长）
restic -r "D:\虚拟机共享存储\Ubuntu_Backups\repo" check --read-data

# 查看备份统计
restic -r "D:\虚拟机共享存储\Ubuntu_Backups\repo" stats
```

注意：restic 需要密码访问仓库。如果环境变量 `RESTIC_PASSWORD` 未设置，执行时会提示输入。

## 执行备份

```bash
# 增量备份指定路径
restic -r "<repo路径>" backup <路径> --tag auto

# 备份并排除大文件/临时文件
restic -r "<repo路径>" backup <路径> --exclude="*.tmp" --exclude=".cache" --exclude="node_modules" --tag auto

# 查看备份进度
restic -r "<repo路径>" backup <路径> --verbose --tag auto
```

## 清理过期快照

```bash
# 保留策略：7日备 + 4周备 + 12月备
restic -r "<repo路径>" forget --keep-daily 7 --keep-weekly 4 --keep-monthly 12 --prune

# 预览会清理哪些（不实际删除）
restic -r "<repo路径>" forget --keep-daily 7 --keep-weekly 4 --keep-monthly 12 --dry-run
```

**执行 forget+prune 前必须**：先做 `--dry-run` 预览，确认无误后再实际执行。

## 恢复操作

```bash
# 从最新快照恢复到指定目录
restic -r "<repo路径>" restore latest --target <恢复路径>

# 从指定快照恢复
restic -r "<repo路径>" restore <快照ID> --target <恢复路径>

# 恢复单个文件
restic -r "<repo路径>" restore latest --target <恢复路径> --include <文件路径>

# 查看可恢复的文件列表
restic -r "<repo路径>" ls latest
```

**恢复操作前确认**：目标路径有足够空间，且不会覆盖当前重要数据。

## Docker 容器配置导出

```bash
# 导出所有容器配置（JSON）
mkdir -p /tmp/container-backup
docker ps -a --format '{{.Names}}' | while read c; do
  docker inspect "$c" > "/tmp/container-backup/${c}.json"
done

# 导出 compose 文件
find / -name "docker-compose.yml" -o -name "docker-compose.yaml" -o -name "compose.yml" -o -name "compose.yaml" 2>/dev/null | while read f; do
  dir="/tmp/container-backup/compose/$(dirname "$f" | tr '/' '_')"
  mkdir -p "$dir"
  cp "$f" "$dir/"
done

# 导出环境变量文件
find / -name ".env" -path "*/docker*" -o -name ".env" -path "*/compose*" 2>/dev/null | while read f; do
  dir="/tmp/container-backup/env/$(dirname "$f" | tr '/' '_')"
  mkdir -p "$dir"
  cp "$f" "$dir/"
done

# 打包备份
tar czf /tmp/container-backup-$(date +%Y%m%d).tar.gz -C /tmp container-backup
```

## 数据库备份

```bash
# MySQL/MariaDB
docker exec <容器名> mysqldump -u root -p<密码> --all-databases > mysql-backup-$(date +%Y%m%d).sql

# PostgreSQL
docker exec <容器名> pg_dumpall -U <用户> > pg-backup-$(date +%Y%m%d).sql

# SQLite（直接复制文件）
docker cp <容器名>:/data/db.sqlite3 ./sqlite-backup-$(date +%Y%m%d).db
```

## 邮件通知

```bash
# 备份成功
agently-cli message +send --to "1448960082@qq.com" --subject "备份完成: <设备名>" --body "快照ID: xxx, 大小: xxx, 耗时: xxx"

# 备份失败
agently-cli message +send --to "1448960082@qq.com" --subject "备份失败: <设备名>" --body "错误: xxx"
```

## 安全规则

1. 备份验证建议每月至少一次 `restic check`
2. restic 密码不在命令中明文传递，使用环境变量或交互式输入
3. 容器配置备份保存到本地工作目录，不放远程
4. `forget --prune` 前必须 dry-run 确认
5. 恢复操作前检查目标磁盘空间

## 备份健康报告

```
💾 备份状态报告
时间: YYYY-MM-DD

═══ restic 快照 ═══
最新快照: deccbb77 (2026-06-16)
快照总数: 42
仓库大小: 15.3 GB
✅ 完整性检查通过

═══ 容器配置 ═══
已导出: 44/44 容器
compose 文件: 12 个
最近导出: 2026-07-01

⚠️ 注意: 最近一次快照距今 15 天，建议执行新备份
```

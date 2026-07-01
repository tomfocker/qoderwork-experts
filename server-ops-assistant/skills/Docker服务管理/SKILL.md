---
name: Docker服务管理
version: 1.0.0
description: Remote Docker container management via SSH — status check, start/stop/restart, image cleanup, compose operations, with focus on unstable containers
description_zh: 通过SSH远程管理Docker容器，支持状态检查、启停操作、镜像清理、compose部署，重点监控易挂容器
user-invocable: true
argument-hint: 指定操作（如"检查容器状态"、"重启moviepilot"、"清理镜像"）
---

# Docker 服务管理

通过 SSH 连接到运行 Docker 的服务器，执行容器管理操作。

## 前置条件

- 读取 [服务器台账](references/server-inventory.md) 获取设备连接信息
- 目标设备：Ubuntu VM（主力 Docker 宿主机，44个容器）、阿里云 VPS（10个容器）、极空间 NAS

## 运行环境说明

| 设备 | 管理方式 | 容器数量 | 特殊说明 |
|:---|:---|:---|:---|
| Ubuntu VM | 1Panel 面板 + 命令行 | 44 | 用户已在 docker 组，新会话直接 `docker`，当前会话用 `sg docker -c 'docker ...'`，alist/portainer/karakeep 等 |
| 阿里云 VPS | 宝塔面板 + 命令行 | 10 | root 用户直接运行 docker，含 tailscale/derper/wxchat/frps/nginx-proxy-manager |
| 极空间 NAS | 极空间自带 UI + SSH | 少量 | moviepilot-v2 偶尔挂 |

**注意**：Ubuntu VM 当前会话如遇到 docker 权限问题，用 `sg docker -c 'docker ...'` 包裹命令即可。

## 操作流程

### 容器状态检查

```bash
# 连接目标设备后执行
docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}\t{{.Ports}}'

# 只看运行中的
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}'

# 只看停止的/异常的
docker ps -a --filter "status=exited" --filter "status=dead" --format 'table {{.Names}}\t{{.Status}}'

# 检查重启次数多的容器（不稳定信号）
docker ps -a --format '{{.Names}}: {{.Status}}' | grep -i "restart"

# 资源占用 TOP 10
docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}' | head -11
```

### 容器操作

```bash
# 查看容器日志（最近100行）
docker logs --tail 100 <容器名>

# 查看容器详细信息
docker inspect <容器名> --format '{{.State.Status}} {{.State.StartedAt}} Restarts:{{.RestartCount}}'

# 启动容器
docker start <容器名>

# 停止容器（先尝试优雅停止）
docker stop -t 30 <容器名>

# 重启容器
docker restart <容器名>

# 强制停止（仅当 stop 超时后使用）
docker kill <容器名>
```

### 镜像清理

```bash
# 查看镜像占用
docker images --format 'table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedSince}}'

# 清理悬空镜像
docker image prune -f

# 清理所有未使用镜像（需确认）
docker image prune -a -f

# 清理未使用的 volume（需确认，数据不可恢复）
docker volume prune -f

# 全面清理（镜像+容器+网络+缓存）
docker system prune -f

# 查看 Docker 磁盘占用
docker system df
```

### Docker Compose 操作

```bash
# 查看 compose 项目
docker compose ls

# 启动服务
docker compose -f <compose文件路径> up -d

# 停止服务
docker compose -f <compose文件路径> down

# 查看日志
docker compose -f <compose文件路径> logs --tail 100

# 更新镜像并重建
docker compose -f <compose文件路径> pull && docker compose -f <compose文件路径> up -d

# 查找 compose 文件位置
find / -name "docker-compose.yml" -o -name "docker-compose.yaml" -o -name "compose.yml" -o -name "compose.yaml" 2>/dev/null
```

## 重点监控容器

### moviepilot-v2（极空间 NAS）
- **已知问题**：容器偶尔挂掉
- 检查方式：`docker ps -a --filter "name=moviepilot" --format '{{.Names}}: {{.Status}}'`
- 如果状态为 Exited：先查日志 `docker logs --tail 50 moviepilot-v2`，确认无数据损坏后重启
- 重启后验证：等待 30 秒，再次检查状态

### alist（Ubuntu VM）
- 服务地址：https://share.zym588.space
- 检查后可以用 `curl -sI https://share.zym588.space` 验证 HTTP 可达性

### portainer（Ubuntu VM）
- Docker 管理面板，停止会影响容器可视化管理

## 邮件通知

操作完成后如需通知，使用 Agently Mail CLI：

```bash
agently-cli message +send --to "1448960082@qq.com" --subject "Docker操作报告" --body "<操作结果>"
```

Agently Mail 需要两步确认：先执行 +send 获取 confirmation_token，再带 --confirmation-token 参数重发。

## 安全规则

1. **不得批量重启所有容器**，除非用户明确要求
2. **包含数据的容器**（数据库、alist、moviepilot）操作前须确认
3. `docker system prune -a` 和 `docker volume prune` 执行前必须警告用户可能丢失的数据
4. 停止容器优先用 `docker stop`（优雅），仅超时后才用 `docker kill`
5. compose 操作前先确认 compose 文件路径正确

## 排障决策树

容器异常时的处理顺序：
1. 查日志 `docker logs --tail 200 <容器>` → 定位错误
2. 检查资源 `docker stats --no-stream` → 是否 OOM 或 CPU 满载
3. 检查宿主机资源 `free -h && df -h` → 内存/磁盘不足？
4. 如果日志无异常 → 尝试重启
5. 重启后仍异常 → 检查 compose 配置和环境变量是否完整
6. 持续异常 → 记录日志并通知用户

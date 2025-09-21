# 项目管理系统 DSM 部署指南

## 概述

本文档描述如何在群晖 NAS (DSM 7.x) 上部署项目管理系统。系统基于 Flask 框架，使用 PostgreSQL 数据库，通过 Docker 容器化部署。

## 系统要求

### 硬件要求
- 群晖 NAS (DSM 7.0+)
- 至少 4GB 内存
- 至少 10GB 可用存储空间

### 软件要求
- DSM 7.0 或更高版本
- Docker 套件包
- SSH 访问权限

## 部署架构

```
[Internet] 
    ↓
[Nginx Reverse Proxy] :80, :443
    ↓
[Flask Application] :5000
    ↓
[PostgreSQL Database] :5432
```

## 快速部署

### 1. 准备环境

1. 在 DSM 套件中心安装 Docker
2. 启用 SSH 服务
3. 以 root 用户登录到 DSM

### 2. 上传项目文件

将项目文件上传到群晖 NAS 的任意目录，例如：
```bash
scp -r project_mgmt-bak/ admin@your-dsm-ip:/volume1/temp/
```

### 3. 执行部署脚本

```bash
ssh root@your-dsm-ip
cd /volume1/temp/project_mgmt-bak/
chmod +x deploy-dsm.sh
./deploy-dsm.sh
```

### 4. 访问应用

部署完成后，通过以下地址访问：
- HTTP: http://your-dsm-ip
- HTTPS: https://your-dsm-ip

## 手动部署步骤

如果自动部署脚本失败，可以按照以下步骤手动部署：

### 1. 创建目录结构

```bash
mkdir -p /volume1/docker/project-mgmt/{app,nginx/ssl,logs,data/{postgres,redis}}
```

### 2. 复制项目文件

```bash
cp -r * /volume1/docker/project-mgmt/app/
```

### 3. 生成 SSL 证书

```bash
cd /volume1/docker/project-mgmt/nginx/ssl
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes \
    -subj "/C=CN/ST=State/L=City/O=Organization/CN=project-mgmt.local"
```

### 4. 创建环境配置

```bash
cat > /volume1/docker/project-mgmt/.env << EOF
FLASK_ENV=production
CONFIG_TYPE=docker
SECRET_KEY=$(openssl rand -hex 32)
POSTGRES_DB=project_mgmt_db
POSTGRES_USER=project_mgmt
POSTGRES_PASSWORD=$(openssl rand -base64 32)
DATABASE_URL=postgresql://project_mgmt:$(openssl rand -base64 32)@db:5432/project_mgmt_db
ADMIN_PASSWORD=$(openssl rand -base64 16)
DEV_PASSWORD=$(openssl rand -base64 16)
LOG_LEVEL=INFO
TZ=Asia/Shanghai
EOF
```

### 5. 启动服务

```bash
cd /volume1/docker/project-mgmt
docker-compose up -d --build
```

## 配置说明

### 环境变量

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| FLASK_ENV | Flask 运行环境 | production |
| CONFIG_TYPE | 配置类型 | docker |
| SECRET_KEY | Flask 密钥 | 随机生成 |
| DATABASE_URL | 数据库连接字符串 | 自动配置 |
| ADMIN_PASSWORD | 管理员密码 | 随机生成 |
| DEV_PASSWORD | 开发者密码 | 随机生成 |
| LOG_LEVEL | 日志级别 | INFO |

### 端口配置

| 服务 | 端口 | 描述 |
|------|------|------|
| Nginx | 80/443 | HTTP/HTTPS 访问 |
| Flask | 5000 | Web 应用 |
| PostgreSQL | 5432 | 数据库 |
| Redis | 6379 | 缓存 |

### 数据持久化

- 数据库数据: `/volume1/docker/project-mgmt/data/postgres`
- Redis 数据: `/volume1/docker/project-mgmt/data/redis`
- 应用日志: `/volume1/docker/project-mgmt/logs`
- 应用实例: `/volume1/docker/project-mgmt/instance`

## 管理操作

### 服务管理

```bash
# 启动服务
systemctl start project-mgmt

# 停止服务
systemctl stop project-mgmt

# 重启服务
systemctl restart project-mgmt

# 查看状态
systemctl status project-mgmt
```

### Docker 管理

```bash
cd /volume1/docker/project-mgmt

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 重启特定服务
docker-compose restart web

# 更新服务
docker-compose pull
docker-compose up -d --build
```

### 数据库管理

```bash
# 连接数据库
docker exec -it project-mgmt_db_1 psql -U project_mgmt -d project_mgmt_db

# 备份数据库
docker exec project-mgmt_db_1 pg_dump -U project_mgmt project_mgmt_db > backup.sql

# 恢复数据库
docker exec -i project-mgmt_db_1 psql -U project_mgmt project_mgmt_db < backup.sql
```

## 备份与恢复

### 自动备份

系统已配置自动备份脚本：
```bash
/usr/local/bin/backup-project-mgmt.sh
```

可以添加到 crontab 中实现定时备份：
```bash
# 每天凌晨2点执行备份
0 2 * * * /usr/local/bin/backup-project-mgmt.sh
```

### 手动备份

```bash
# 备份应用数据
tar -czf /volume1/docker/backups/project-mgmt/manual_backup_$(date +%Y%m%d_%H%M%S).tar.gz \
    /volume1/docker/project-mgmt/data \
    /volume1/docker/project-mgmt/logs

# 备份数据库
docker exec project-mgmt_db_1 pg_dump -U project_mgmt project_mgmt_db > \
    /volume1/docker/backups/project-mgmt/db_manual_$(date +%Y%m%d_%H%M%S).sql
```

### 恢复操作

```bash
# 停止服务
docker-compose down

# 恢复数据
tar -xzf backup_file.tar.gz -C /

# 启动服务
docker-compose up -d
```

## 安全配置

### SSL/TLS

默认生成自签名证书，生产环境建议使用有效证书：

1. 获取有效的 SSL 证书
2. 替换 `/volume1/docker/project-mgmt/nginx/ssl/` 目录下的证书文件
3. 重启 nginx 服务

### 防火墙

建议配置防火墙规则，只允许必要的端口访问：
- 80 (HTTP)
- 443 (HTTPS)
- 22 (SSH，管理用)

### 密码安全

- 定期更改管理员密码
- 使用强密码策略
- 启用双因素认证（如需要）

## 监控与日志

### 日志位置

- 应用日志: `/volume1/docker/project-mgmt/logs/project_mgmt.log`
- Nginx 日志: Docker 容器内的 `/var/log/nginx/`
- 数据库日志: Docker 容器内的 PostgreSQL 日志

### 监控检查

```bash
# 检查服务健康状态
curl -f http://localhost:5000/health

# 查看容器状态
docker-compose ps

# 查看资源使用
docker stats
```

## 故障排除

### 常见问题

1. **容器启动失败**
   - 检查端口是否被占用
   - 查看 Docker 日志
   - 确认配置文件格式正确

2. **数据库连接失败**
   - 检查数据库容器是否正常运行
   - 验证数据库连接字符串
   - 查看数据库日志

3. **SSL 证书问题**
   - 检查证书文件权限
   - 验证证书有效性
   - 查看 Nginx 错误日志

### 日志调试

```bash
# 查看所有服务日志
docker-compose logs

# 查看特定服务日志
docker-compose logs web
docker-compose logs db
docker-compose logs nginx

# 实时查看日志
docker-compose logs -f
```

## 升级更新

### 应用更新

1. 备份当前数据
2. 下载新版本代码
3. 更新 Docker 镜像
4. 重启服务

```bash
# 备份
/usr/local/bin/backup-project-mgmt.sh

# 更新代码
cd /volume1/docker/project-mgmt
cp -r /path/to/new/code/* app/

# 重建镜像
docker-compose build --no-cache
docker-compose up -d
```

### 数据库迁移

如果需要数据库结构更新：

```bash
# 进入应用容器
docker exec -it project-mgmt_web_1 /bin/bash

# 运行迁移脚本
python migrate_database.py
```

## 支持联系

如遇到问题，请联系技术支持或查看：
- 项目文档
- 错误日志
- 社区论坛

---

**注意**: 本部署指南针对群晖 DSM 7.x 系统，其他系统可能需要调整配置。
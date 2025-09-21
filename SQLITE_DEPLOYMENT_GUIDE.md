# 项目管理系统 SQLite 版本部署指南

## 概述

本版本使用 SQLite 本地数据库，简化了部署复杂度，适合中小型团队和数据量不大的场景。

## 系统架构

```
[Internet] 
    ↓
[Nginx Reverse Proxy] :80, :443
    ↓
[Flask Application] :5000
    ↓
[SQLite Database] (本地文件)
```

## 主要变更

相比 PostgreSQL 版本，SQLite 版本有以下简化：

### 移除的组件
- ❌ PostgreSQL 数据库容器
- ❌ Redis 缓存容器  
- ❌ 数据库初始化脚本
- ❌ PostgreSQL 相关依赖

### 保留的组件
- ✅ Flask Web 应用
- ✅ Nginx 反向代理
- ✅ SSL/TLS 支持
- ✅ 日志收集
- ✅ 健康检查
- ✅ 自动备份

## 数据存储

### SQLite 数据库位置
- **容器内路径**: `/app/instance/projects.db`
- **宿主机映射**: `/volume1/docker/project-mgmt/instance/projects.db`

### 数据持久化
- 数据库文件: `/volume1/docker/project-mgmt/instance/`
- 应用日志: `/volume1/docker/project-mgmt/logs/`

## 快速部署

### 1. 上传项目文件
```bash
scp -r project_mgmt-bak/ admin@your-dsm-ip:/volume1/temp/
```

### 2. 执行部署脚本
```bash
ssh root@your-dsm-ip
cd /volume1/temp/project_mgmt-bak/
chmod +x deploy-dsm.sh
./deploy-dsm.sh
```

### 3. 访问应用
- HTTP: http://your-dsm-ip
- HTTPS: https://your-dsm-ip

## 容器服务

### 运行的容器
1. **web** - Flask 应用容器
2. **nginx** - 反向代理容器

### 端口映射
- 80 → nginx (HTTP)
- 443 → nginx (HTTPS)  
- 5000 → web (Flask应用)

## 配置文件

### 环境变量 (.env)
```bash
FLASK_ENV=production
CONFIG_TYPE=docker
SECRET_KEY=随机生成
DATABASE_URL=sqlite:///app/instance/projects.db
ADMIN_PASSWORD=随机生成
DEV_PASSWORD=随机生成
LOG_LEVEL=INFO
TZ=Asia/Shanghai
```

### SQLite 配置
- 数据库文件自动创建
- 表结构自动初始化
- 无需额外配置

## 管理操作

### 服务管理
```bash
# 查看服务状态
docker-compose ps

# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看日志
docker-compose logs -f
```

### 数据库管理

#### 查看数据库
```bash
# 进入容器
docker exec -it project-mgmt_web_1 /bin/bash

# 使用 SQLite 命令行
sqlite3 /app/instance/projects.db

# 查看表结构
.schema

# 查看数据
SELECT * FROM projects;

# 退出
.quit
```

#### 备份数据库
```bash
# 手动备份
docker exec project-mgmt_web_1 cp /app/instance/projects.db /app/logs/backup_$(date +%Y%m%d_%H%M%S).db

# 自动备份脚本
/usr/local/bin/backup-project-mgmt.sh
```

#### 恢复数据库
```bash
# 停止服务
docker-compose down

# 恢复数据库文件
cp backup.db /volume1/docker/project-mgmt/instance/projects.db

# 启动服务
docker-compose up -d
```

## 性能特点

### SQLite 优势
- ✅ 部署简单，无需额外数据库服务
- ✅ 资源消耗低
- ✅ 事务支持完整
- ✅ 数据完整性好
- ✅ 备份恢复简单

### SQLite 限制
- ❌ 不支持并发写入
- ❌ 不适合大数据量
- ❌ 不支持网络访问
- ❌ 不支持用户权限管理

### 适用场景
- 中小型团队 (< 50人)
- 项目数量 < 1000个
- 并发用户 < 20人
- 数据量 < 100MB

## 性能优化

### SQLite 优化
```sql
-- 开启 WAL 模式
PRAGMA journal_mode=WAL;

-- 优化缓存大小
PRAGMA cache_size=-64000;

-- 开启外键约束
PRAGMA foreign_keys=ON;
```

### 应用优化
- 使用连接池
- 批量操作
- 索引优化
- 查询优化

## 监控建议

### 基础监控
- 磁盘空间使用
- 数据库文件大小
- 应用响应时间
- 错误日志监控

### 性能监控
```bash
# 查看数据库大小
ls -lh /volume1/docker/project-mgmt/instance/projects.db

# 查看容器资源使用
docker stats project-mgmt_web_1

# 查看磁盘使用
df -h /volume1/docker/project-mgmt/
```

## 升级迁移

### 从开发环境迁移
1. 停止开发环境应用
2. 复制 SQLite 数据库文件
3. 部署生产环境
4. 复制数据库到生产环境

### 升级到 PostgreSQL
如果数据量增长需要升级到 PostgreSQL：

1. 导出 SQLite 数据
```bash
sqlite3 projects.db .dump > export.sql
```

2. 转换为 PostgreSQL 格式
3. 导入到 PostgreSQL
4. 更新配置文件
5. 重新部署

## 故障排除

### 常见问题

1. **数据库锁定**
   - 原因：并发写入冲突
   - 解决：重启应用，减少并发

2. **数据库损坏**
   - 原因：异常关闭
   - 解决：从备份恢复

3. **磁盘空间不足**
   - 原因：日志或数据库过大
   - 解决：清理日志，优化数据

### 日志查看
```bash
# 应用日志
docker-compose logs web

# 系统日志
tail -f /volume1/docker/project-mgmt/logs/project_mgmt.log

# Nginx 日志
docker-compose logs nginx
```

## 安全建议

### 数据库安全
- 定期备份数据库
- 限制文件系统权限
- 监控异常访问
- 数据加密存储

### 应用安全
- 定期更新密码
- 使用 HTTPS
- 限制管理员权限
- 启用审计日志

---

**注意**: SQLite 版本适合中小型应用，如需支持大并发或大数据量，请考虑升级到 PostgreSQL 版本。
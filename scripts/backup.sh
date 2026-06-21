#!/bin/sh

# =====================================================
# 项目管理系统 - 数据备份脚本
# 用于定时备份SQLite数据库和重要文件
# =====================================================

# 配置变量
DATA_DIR=${DATA_DIR:-/data}
BACKUP_DIR=${BACKUP_DIR:-/backups}
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="project_mgmt_backup_${TIMESTAMP}.tar.gz"
DB_FILE="${DATA_DIR}/projects.db"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# 创建备份目录
mkdir -p "${BACKUP_DIR}"

# 检查数据库文件是否存在
if [ ! -f "${DB_FILE}" ]; then
    log "ERROR: 数据库文件不存在: ${DB_FILE}"
    exit 1
fi

log "开始备份数据..."

# 创建临时目录
TEMP_DIR="/tmp/backup_${TIMESTAMP}"
mkdir -p "${TEMP_DIR}"

# 复制数据库文件（使用SQLite备份命令以确保一致性）
log "备份数据库..."
if command -v sqlite3 >/dev/null 2>&1; then
    sqlite3 "${DB_FILE}" ".backup ${TEMP_DIR}/projects.db"
else
    # 如果没有sqlite3命令，直接复制文件
    cp "${DB_FILE}" "${TEMP_DIR}/projects.db"
fi

# 复制上传文件（如果存在）
if [ -d "${DATA_DIR}/../uploads" ]; then
    log "备份上传文件..."
    cp -r "${DATA_DIR}/../uploads" "${TEMP_DIR}/"
fi

# 创建备份信息文件
cat > "${TEMP_DIR}/backup_info.txt" << EOF
备份时间: $(date)
数据库文件: projects.db
备份类型: 自动备份
版本: 1.0.0
EOF

# 创建压缩备份文件
log "创建压缩文件..."
cd "${TEMP_DIR}"
tar -czf "${BACKUP_DIR}/${BACKUP_FILE}" .

# 清理临时目录
rm -rf "${TEMP_DIR}"

# 检查备份文件
if [ -f "${BACKUP_DIR}/${BACKUP_FILE}" ]; then
    BACKUP_SIZE=$(du -h "${BACKUP_DIR}/${BACKUP_FILE}" | cut -f1)
    log "备份完成: ${BACKUP_FILE} (大小: ${BACKUP_SIZE})"
else
    log "ERROR: 备份失败"
    exit 1
fi

# 清理旧备份文件
log "清理 ${RETENTION_DAYS} 天前的备份文件..."
find "${BACKUP_DIR}" -name "project_mgmt_backup_*.tar.gz" -type f -mtime +${RETENTION_DAYS} -delete

# 显示当前备份文件列表
log "当前备份文件列表:"
ls -lh "${BACKUP_DIR}"/project_mgmt_backup_*.tar.gz 2>/dev/null || log "无备份文件"

log "备份任务完成"
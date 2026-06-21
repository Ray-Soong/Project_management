#!/bin/bash

# =====================================================
# 项目管理系统 - 数据恢复脚本
# 用于从备份文件恢复数据
# =====================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 配置变量
DATA_DIR=${DATA_DIR:-"/volume1/docker/project_mgmt/data"}
BACKUP_DIR=${BACKUP_DIR:-"/volume1/docker/project_mgmt/backups"}
UPLOADS_DIR=${UPLOADS_DIR:-"/volume1/docker/project_mgmt/uploads"}

# 显示使用说明
show_usage() {
    echo "使用方法: $0 [备份文件名]"
    echo
    echo "参数:"
    echo "  备份文件名    要恢复的备份文件名(可选)"
    echo
    echo "示例:"
    echo "  $0                                    # 选择最新备份"
    echo "  $0 project_mgmt_backup_20231211_120000.tar.gz  # 恢复指定备份"
    echo
    echo "环境变量:"
    echo "  DATA_DIR      数据目录 (默认: ${DATA_DIR})"
    echo "  BACKUP_DIR    备份目录 (默认: ${BACKUP_DIR})"
    echo "  UPLOADS_DIR   上传目录 (默认: ${UPLOADS_DIR})"
}

# 列出可用备份
list_backups() {
    log_info "可用备份文件:"
    if ls "${BACKUP_DIR}"/project_mgmt_backup_*.tar.gz >/dev/null 2>&1; then
        ls -lht "${BACKUP_DIR}"/project_mgmt_backup_*.tar.gz | head -10
    else
        log_error "没有找到备份文件"
        exit 1
    fi
}

# 选择备份文件
select_backup() {
    if [ -n "$1" ]; then
        BACKUP_FILE="${BACKUP_DIR}/$1"
        if [ ! -f "${BACKUP_FILE}" ]; then
            log_error "备份文件不存在: ${BACKUP_FILE}"
            exit 1
        fi
    else
        # 选择最新的备份文件
        BACKUP_FILE=$(ls -t "${BACKUP_DIR}"/project_mgmt_backup_*.tar.gz 2>/dev/null | head -1)
        if [ -z "${BACKUP_FILE}" ]; then
            log_error "没有找到备份文件"
            exit 1
        fi
        log_info "选择最新备份: $(basename "${BACKUP_FILE}")"
    fi
}

# 检查Docker服务状态
check_docker_services() {
    log_info "检查Docker服务状态..."
    
    if docker-compose -f docker-compose.nas.yml ps | grep -q "Up"; then
        log_warning "检测到运行中的服务，需要停止服务进行恢复"
        read -p "是否停止服务并继续恢复? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "停止Docker服务..."
            docker-compose -f docker-compose.nas.yml down
            log_success "服务已停止"
        else
            log_info "恢复已取消"
            exit 0
        fi
    fi
}

# 备份当前数据
backup_current_data() {
    log_info "备份当前数据..."
    
    CURRENT_BACKUP_DIR="/tmp/current_backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "${CURRENT_BACKUP_DIR}"
    
    if [ -f "${DATA_DIR}/projects.db" ]; then
        cp "${DATA_DIR}/projects.db" "${CURRENT_BACKUP_DIR}/"
        log_info "当前数据库已备份到: ${CURRENT_BACKUP_DIR}/projects.db"
    fi
    
    if [ -d "${UPLOADS_DIR}" ]; then
        cp -r "${UPLOADS_DIR}" "${CURRENT_BACKUP_DIR}/"
        log_info "当前上传文件已备份到: ${CURRENT_BACKUP_DIR}/uploads"
    fi
    
    echo "${CURRENT_BACKUP_DIR}" > /tmp/current_backup_path
    log_info "当前数据备份路径已保存"
}

# 恢复数据
restore_data() {
    log_info "开始恢复数据..."
    
    # 创建临时解压目录
    TEMP_DIR="/tmp/restore_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "${TEMP_DIR}"
    
    # 解压备份文件
    log_info "解压备份文件..."
    tar -xzf "${BACKUP_FILE}" -C "${TEMP_DIR}"
    
    # 显示备份信息
    if [ -f "${TEMP_DIR}/backup_info.txt" ]; then
        log_info "备份信息:"
        cat "${TEMP_DIR}/backup_info.txt"
        echo
    fi
    
    # 确认恢复
    read -p "确认恢复此备份? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "恢复已取消"
        rm -rf "${TEMP_DIR}"
        exit 0
    fi
    
    # 创建目录
    mkdir -p "${DATA_DIR}"
    mkdir -p "${UPLOADS_DIR}"
    
    # 恢复数据库
    if [ -f "${TEMP_DIR}/projects.db" ]; then
        log_info "恢复数据库..."
        cp "${TEMP_DIR}/projects.db" "${DATA_DIR}/"
        log_success "数据库恢复完成"
    else
        log_warning "备份中没有找到数据库文件"
    fi
    
    # 恢复上传文件
    if [ -d "${TEMP_DIR}/uploads" ]; then
        log_info "恢复上传文件..."
        rm -rf "${UPLOADS_DIR}"/*
        cp -r "${TEMP_DIR}/uploads"/* "${UPLOADS_DIR}/"
        log_success "上传文件恢复完成"
    else
        log_info "备份中没有上传文件"
    fi
    
    # 设置权限
    chown -R root:root "${DATA_DIR}"
    chown -R root:root "${UPLOADS_DIR}"
    chmod -R 755 "${DATA_DIR}"
    chmod -R 755 "${UPLOADS_DIR}"
    
    # 清理临时目录
    rm -rf "${TEMP_DIR}"
    
    log_success "数据恢复完成"
}

# 启动服务
start_services() {
    read -p "是否立即启动服务? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "启动服务..."
        docker-compose -f docker-compose.nas.yml up -d
        
        # 等待服务启动
        sleep 10
        
        # 健康检查
        if curl -f http://localhost:8080/health &> /dev/null; then
            log_success "服务启动成功"
        else
            log_warning "服务可能没有正确启动，请检查日志"
        fi
    fi
}

# 显示恢复完成信息
show_completion_info() {
    echo
    log_success "========================================"
    log_success "数据恢复完成!"
    log_success "========================================"
    echo
    log_info "恢复的备份: $(basename "${BACKUP_FILE}")"
    log_info "数据目录: ${DATA_DIR}"
    log_info "上传目录: ${UPLOADS_DIR}"
    echo
    
    if [ -f /tmp/current_backup_path ]; then
        CURRENT_BACKUP=$(cat /tmp/current_backup_path)
        log_info "原数据备份位置: ${CURRENT_BACKUP}"
        log_info "如需回滚，请手动恢复原数据"
        rm -f /tmp/current_backup_path
    fi
    
    echo
    log_info "服务管理命令:"
    log_info "  启动服务: docker-compose -f docker-compose.nas.yml up -d"
    log_info "  查看状态: docker-compose -f docker-compose.nas.yml ps"
    log_info "  查看日志: docker-compose -f docker-compose.nas.yml logs -f"
}

# 主函数
main() {
    echo "========================================"
    echo "项目管理系统 - 数据恢复脚本"
    echo "========================================"
    echo
    
    # 检查参数
    if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
        show_usage
        exit 0
    fi
    
    # 检查备份目录
    if [ ! -d "${BACKUP_DIR}" ]; then
        log_error "备份目录不存在: ${BACKUP_DIR}"
        exit 1
    fi
    
    list_backups
    echo
    select_backup "$1"
    check_docker_services
    backup_current_data
    restore_data
    start_services
    show_completion_info
    
    log_success "恢复完成!"
}

# 错误处理
trap 'log_error "恢复过程中发生错误"; exit 1' ERR

# 执行主函数
main "$@"
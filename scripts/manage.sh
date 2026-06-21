#!/bin/bash

# =====================================================
# 项目管理系统 - 维护和管理脚本
# 提供日常维护、监控和故障排除功能
# =====================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
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

log_debug() {
    echo -e "${CYAN}[DEBUG]${NC} $1"
}

# 配置变量
COMPOSE_FILE="docker-compose.nas.yml"
DATA_DIR="/volume1/docker/project_mgmt"

# 显示菜单
show_menu() {
    echo "========================================"
    echo "项目管理系统 - 维护管理脚本"
    echo "========================================"
    echo
    echo "1.  查看服务状态"
    echo "2.  启动所有服务"
    echo "3.  停止所有服务"
    echo "4.  重启所有服务"
    echo "5.  查看服务日志"
    echo "6.  清理日志文件"
    echo "7.  数据库维护"
    echo "8.  备份数据"
    echo "9.  恢复数据"
    echo "10. 更新系统"
    echo "11. 系统健康检查"
    echo "12. 清理Docker资源"
    echo "13. 查看系统资源"
    echo "14. 配置管理"
    echo "15. 故障诊断"
    echo "0.  退出"
    echo
}

# 查看服务状态
check_status() {
    log_info "查看服务状态..."
    echo
    docker-compose -f "${COMPOSE_FILE}" ps
    echo
    
    # 检查端口占用
    log_info "端口占用情况:"
    netstat -tlnp | grep -E ":(80|443|5000|9090|3000)" || log_info "没有相关端口被占用"
    echo
}

# 启动服务
start_services() {
    log_info "启动服务..."
    docker-compose -f "${COMPOSE_FILE}" up -d
    
    log_info "等待服务启动..."
    sleep 10
    
    # 健康检查
    if curl -f http://localhost:8080/health &> /dev/null; then
        log_success "服务启动成功"
    else
        log_warning "服务可能没有正确启动，请查看日志"
    fi
}

# 停止服务
stop_services() {
    log_info "停止服务..."
    docker-compose -f "${COMPOSE_FILE}" down
    log_success "服务已停止"
}

# 重启服务
restart_services() {
    log_info "重启服务..."
    docker-compose -f "${COMPOSE_FILE}" restart
    
    log_info "等待服务重启..."
    sleep 10
    
    # 健康检查
    if curl -f http://localhost:8080/health &> /dev/null; then
        log_success "服务重启成功"
    else
        log_warning "服务可能没有正确重启，请查看日志"
    fi
}

# 查看日志
view_logs() {
    echo "选择要查看的服务日志:"
    echo "1. 所有服务"
    echo "2. Web应用"
    echo "3. Nginx"
    echo "4. Redis"
    echo "5. 备份服务"
    read -p "请选择 (1-5): " choice
    
    case $choice in
        1) docker-compose -f "${COMPOSE_FILE}" logs -f ;;
        2) docker-compose -f "${COMPOSE_FILE}" logs -f web ;;
        3) docker-compose -f "${COMPOSE_FILE}" logs -f nginx ;;
        4) docker-compose -f "${COMPOSE_FILE}" logs -f redis ;;
        5) docker-compose -f "${COMPOSE_FILE}" logs -f backup ;;
        *) log_error "无效选择" ;;
    esac
}

# 清理日志
clean_logs() {
    log_info "清理日志文件..."
    
    # 清理应用日志
    if [ -d "${DATA_DIR}/logs" ]; then
        find "${DATA_DIR}/logs" -name "*.log" -mtime +7 -delete
        log_info "已清理7天前的应用日志"
    fi
    
    # 清理Docker日志
    docker system prune --volumes -f
    log_info "已清理Docker日志和无用资源"
    
    log_success "日志清理完成"
}

# 数据库维护
database_maintenance() {
    log_info "数据库维护..."
    
    DB_FILE="${DATA_DIR}/data/projects.db"
    if [ ! -f "${DB_FILE}" ]; then
        log_error "数据库文件不存在: ${DB_FILE}"
        return 1
    fi
    
    # 备份数据库
    BACKUP_DB="${DB_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    cp "${DB_FILE}" "${BACKUP_DB}"
    log_info "数据库已备份: ${BACKUP_DB}"
    
    # 数据库完整性检查
    if command -v sqlite3 >/dev/null 2>&1; then
        log_info "执行数据库完整性检查..."
        if sqlite3 "${DB_FILE}" "PRAGMA integrity_check;" | grep -q "ok"; then
            log_success "数据库完整性检查通过"
        else
            log_error "数据库完整性检查失败"
            return 1
        fi
        
        # 数据库优化
        log_info "优化数据库..."
        sqlite3 "${DB_FILE}" "VACUUM;"
        sqlite3 "${DB_FILE}" "ANALYZE;"
        log_success "数据库优化完成"
    else
        log_warning "sqlite3命令不可用，跳过数据库检查"
    fi
}

# 备份数据
backup_data() {
    log_info "执行数据备份..."
    
    if docker-compose -f "${COMPOSE_FILE}" ps backup | grep -q "Up"; then
        docker-compose -f "${COMPOSE_FILE}" exec backup /usr/local/bin/backup.sh
    else
        log_info "启动备份容器..."
        docker-compose -f "${COMPOSE_FILE}" up -d backup
        sleep 5
        docker-compose -f "${COMPOSE_FILE}" exec backup /usr/local/bin/backup.sh
    fi
    
    log_success "备份完成"
}

# 恢复数据
restore_data() {
    log_warning "数据恢复将停止所有服务并覆盖当前数据"
    read -p "是否继续? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ./scripts/restore.sh
    else
        log_info "恢复已取消"
    fi
}

# 更新系统
update_system() {
    log_info "更新系统..."
    
    # 拉取最新镜像
    log_info "拉取最新镜像..."
    docker-compose -f "${COMPOSE_FILE}" pull
    
    # 重新构建
    log_info "重新构建应用..."
    docker-compose -f "${COMPOSE_FILE}" build --no-cache web
    
    # 重启服务
    log_info "重启服务..."
    docker-compose -f "${COMPOSE_FILE}" up -d
    
    log_success "系统更新完成"
}

# 系统健康检查
health_check() {
    log_info "执行系统健康检查..."
    echo
    
    # 检查服务状态
    log_info "1. 检查服务状态..."
    if docker-compose -f "${COMPOSE_FILE}" ps | grep -q "Up"; then
        log_success "服务运行正常"
    else
        log_error "部分服务未运行"
    fi
    
    # 检查Web服务
    log_info "2. 检查Web服务..."
    if curl -f http://localhost:8080/health &> /dev/null; then
        log_success "Web服务响应正常"
    else
        log_error "Web服务无响应"
    fi
    
    # 检查磁盘空间
    log_info "3. 检查磁盘空间..."
    DISK_USAGE=$(df "${DATA_DIR}" | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "${DISK_USAGE}" -lt 80 ]; then
        log_success "磁盘空间充足 (使用率: ${DISK_USAGE}%)"
    elif [ "${DISK_USAGE}" -lt 90 ]; then
        log_warning "磁盘空间紧张 (使用率: ${DISK_USAGE}%)"
    else
        log_error "磁盘空间不足 (使用率: ${DISK_USAGE}%)"
    fi
    
    # 检查内存使用
    log_info "4. 检查内存使用..."
    MEMORY_USAGE=$(free | grep Mem | awk '{printf("%.0f", $3/$2 * 100.0)}')
    if [ "${MEMORY_USAGE}" -lt 80 ]; then
        log_success "内存使用正常 (使用率: ${MEMORY_USAGE}%)"
    else
        log_warning "内存使用较高 (使用率: ${MEMORY_USAGE}%)"
    fi
    
    # 检查数据库
    log_info "5. 检查数据库..."
    DB_FILE="${DATA_DIR}/data/projects.db"
    if [ -f "${DB_FILE}" ]; then
        DB_SIZE=$(du -h "${DB_FILE}" | cut -f1)
        log_success "数据库文件正常 (大小: ${DB_SIZE})"
    else
        log_error "数据库文件不存在"
    fi
    
    echo
    log_info "健康检查完成"
}

# 清理Docker资源
clean_docker() {
    log_info "清理Docker资源..."
    
    # 清理无用镜像
    docker image prune -f
    
    # 清理无用容器
    docker container prune -f
    
    # 清理无用网络
    docker network prune -f
    
    # 清理无用卷
    docker volume prune -f
    
    log_success "Docker资源清理完成"
}

# 查看系统资源
view_resources() {
    log_info "系统资源使用情况:"
    echo
    
    # CPU使用率
    log_info "CPU使用率:"
    top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//'
    
    # 内存使用
    log_info "内存使用:"
    free -h
    
    # 磁盘使用
    log_info "磁盘使用:"
    df -h "${DATA_DIR}"
    
    # Docker资源
    log_info "Docker资源:"
    docker system df
    
    echo
}

# 配置管理
config_management() {
    echo "配置管理选项:"
    echo "1. 查看当前配置"
    echo "2. 编辑环境配置"
    echo "3. 重新生成配置"
    echo "4. 验证配置"
    read -p "请选择 (1-4): " choice
    
    case $choice in
        1)
            log_info "当前配置:"
            cat .env.nas 2>/dev/null || log_error "配置文件不存在"
            ;;
        2)
            nano .env.nas
            ;;
        3)
            log_info "重新生成配置..."
            ./scripts/deploy-nas.sh
            ;;
        4)
            log_info "验证配置..."
            docker-compose -f "${COMPOSE_FILE}" config
            ;;
        *)
            log_error "无效选择"
            ;;
    esac
}

# 故障诊断
troubleshoot() {
    log_info "故障诊断工具..."
    echo
    
    # 检查常见问题
    log_info "1. 检查端口冲突..."
    netstat -tlnp | grep -E ":(80|443|5000|9090|3000)"
    
    log_info "2. 检查Docker服务..."
    systemctl status docker
    
    log_info "3. 检查容器日志错误..."
    docker-compose -f "${COMPOSE_FILE}" logs --tail=50 | grep -i error
    
    log_info "4. 检查磁盘空间..."
    df -h
    
    log_info "5. 检查权限..."
    ls -la "${DATA_DIR}"
    
    echo
    log_info "如需更多帮助，请查看日志文件或联系技术支持"
}

# 主函数
main() {
    while true; do
        show_menu
        read -p "请选择操作 (0-15): " choice
        echo
        
        case $choice in
            1) check_status ;;
            2) start_services ;;
            3) stop_services ;;
            4) restart_services ;;
            5) view_logs ;;
            6) clean_logs ;;
            7) database_maintenance ;;
            8) backup_data ;;
            9) restore_data ;;
            10) update_system ;;
            11) health_check ;;
            12) clean_docker ;;
            13) view_resources ;;
            14) config_management ;;
            15) troubleshoot ;;
            0) 
                log_info "退出管理脚本"
                exit 0
                ;;
            *)
                log_error "无效选择，请重新输入"
                ;;
        esac
        
        echo
        read -p "按Enter键继续..." -r
        clear
    done
}

# 检查必要文件
if [ ! -f "${COMPOSE_FILE}" ]; then
    log_error "Docker Compose文件不存在: ${COMPOSE_FILE}"
    exit 1
fi

# 执行主函数
main
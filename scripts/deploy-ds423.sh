#!/bin/bash

# =====================================================
# 项目管理系统 - DS423+ 修复版部署脚本
# 针对2GB内存的群晖NAS优化版本
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

# 简化的硬件检查
check_hardware() {
    log_info "检查DS423+硬件配置..."
    
    # 检查内存
    TOTAL_MEM=$(free -m | awk '/^Mem:/{print $2}')
    log_info "检测到内存: ${TOTAL_MEM}MB"
    
    # 检查磁盘空间
    AVAILABLE_SPACE=$(df /volume1 | awk 'NR==2 {print $4}')
    SPACE_GB=$((AVAILABLE_SPACE / 1024 / 1024))
    if [ "$SPACE_GB" -lt 5 ]; then
        log_error "磁盘空间不足！可用: ${SPACE_GB}GB，建议至少5GB"
        exit 1
    fi
    
    log_success "硬件检查通过: ${TOTAL_MEM}MB内存, ${SPACE_GB}GB可用空间"
}

# 创建配置文件
create_config() {
    log_info "创建DS423+专用配置..."
    
    # 创建环境配置文件
    cat > .env << 'EOF'
# DS423+ 专用配置
SECRET_KEY=ds423-secret-key
HTTP_PORT=8088
HTTPS_PORT=8448
ADMIN_PASSWORD=admin123
ENABLE_REDIS=false
DB_HOST=db
DB_NAME=project_mgmt
DB_USER=postgres
DB_PASSWORD=postgres123
FLASK_ENV=production
WORKERS=1
TIMEOUT=180
MAX_REQUESTS=300
MEMORY_LIMIT=256m
EOF

    # 设置环境变量
    export HTTP_PORT=8088
    export HTTPS_PORT=8448
    export ADMIN_PASSWORD=admin123
    export ENABLE_REDIS=false
    
    log_success "配置文件创建完成"
    log_info "  HTTP端口: 8088"
    log_info "  管理员密码: admin123"
    log_info "  Redis缓存: 禁用（节省内存）"
}

# 部署服务
deploy_services() {
    log_info "部署DS423+优化服务..."
    
    # 停止现有服务
    docker-compose -f docker-compose.nas.yml down 2>/dev/null || true
    
    # 清理Docker资源
    docker system prune -f 2>/dev/null || true
    
    # 启动服务
    if [ -f "docker-compose.nas.yml" ]; then
        log_info "启动NAS优化服务..."
        docker-compose -f docker-compose.nas.yml up -d
    elif [ -f "docker-compose.yml" ]; then
        log_info "启动默认服务..."
        docker-compose up -d
    else
        log_error "未找到Docker配置文件！"
        log_info "请确保项目文件已正确上传"
        exit 1
    fi
    
    log_success "服务启动完成"
}

# 健康检查
health_check() {
    log_info "执行健康检查..."
    
    # 等待服务启动
    log_info "等待服务启动 (30秒)..."
    sleep 30
    
    # 检查容器状态
    log_info "检查容器状态:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | head -10
    
    # 检查Web服务
    log_info "检查Web服务..."
    for i in {1..6}; do
        if curl -f http://localhost:8088/health &>/dev/null; then
            log_success "Web服务健康检查通过"
            break
        elif [ $i -eq 6 ]; then
            log_warning "Web服务检查超时，但容器可能仍在启动"
            log_info "请稍后手动访问: http://your-nas-ip:8088"
        else
            log_info "等待Web服务响应... ($i/6)"
            sleep 10
        fi
    done
}

# 显示结果
show_result() {
    echo
    log_success "================================"
    log_success "DS423+ 部署完成!"
    log_success "================================"
    echo
    log_info "🎯 访问信息:"
    log_info "  网页地址: http://your-nas-ip:8088"
    log_info "  健康检查: http://your-nas-ip:8088/health"
    echo
    log_info "🔑 默认账户:"
    log_info "  管理员: admin / admin123"
    log_info "  开发者: developer / dev123"
    echo
    log_info "⚡ DS423+优化:"
    log_info "  内存优化: 1个Worker进程"
    log_info "  端口设置: 8088 (避免DSM冲突)"
    log_info "  Redis缓存: 禁用 (节省内存)"
    echo
    log_info "🛠️  管理命令:"
    log_info "  查看状态: docker ps"
    log_info "  查看日志: docker-compose logs -f"
    log_info "  重启服务: docker-compose restart"
    log_info "  停止服务: docker-compose down"
    echo
    log_warning "💡 注意事项:"
    log_warning "  1. 请将 'your-nas-ip' 替换为实际NAS IP地址"
    log_warning "  2. 首次启动可能需要几分钟初始化"
    log_warning "  3. DS423+内存有限，避免同时运行过多服务"
    echo
}

# 主函数
main() {
    echo "========================================"
    echo "DS423+ 项目管理系统部署脚本"
    echo "针对2GB内存优化 - 修复版"
    echo "========================================"
    echo
    
    check_hardware
    create_config
    deploy_services
    health_check
    show_result
    
    log_success "🎉 DS423+ 部署完成!"
}

# 错误处理
trap 'log_error "部署失败，请检查错误信息"; exit 1' ERR

# 执行主函数
main "$@"
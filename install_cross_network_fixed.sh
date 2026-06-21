#!/bin/bash

# =====================================================
# 项目管理系统 - DS423+ 路径修复版部署脚本
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

# 修复路径问题
fix_path_issues() {
    log_info "修复路径和配置问题..."
    
    # 检查当前路径
    CURRENT_DIR=$(pwd)
    log_info "当前目录: $CURRENT_DIR"
    
    # 如果在错误的路径，尝试找到正确的路径
    if [[ "$CURRENT_DIR" == *"project_mamt"* ]]; then
        log_warning "检测到路径拼写错误，尝试修复..."
        # 查找正确的项目目录
        CORRECT_PATH=$(find /volume1/docker -name "project_mgmt*" -type d 2>/dev/null | head -1)
        if [ -n "$CORRECT_PATH" ]; then
            log_info "找到正确路径: $CORRECT_PATH"
            cd "$CORRECT_PATH"
        fi
    fi
    
    # 确保我们在正确的项目目录
    if [ ! -f "app.py" ] && [ ! -f "wsgi.py" ]; then
        log_error "未找到项目主文件，请确认项目目录正确"
        # 列出当前目录内容以便调试
        log_info "当前目录内容:"
        ls -la
        exit 1
    fi
    
    log_success "路径检查完成"
}

# 修复Docker构建问题
fix_docker_build() {
    log_info "修复Docker构建问题..."
    
    # 备份原始requirements.txt
    if [ -f "requirements.txt" ]; then
        cp requirements.txt requirements.txt.backup
        log_info "已备份原始requirements.txt"
    fi
    
    # 创建修复版的requirements.txt
    cat > requirements.txt << 'EOF'
# Core Flask packages - DS423+ 兼容版本
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-Login==0.6.3
Flask-WTF==1.1.1
Flask-Migrate==4.0.5

# Database - 修复版本冲突
SQLAlchemy==2.0.21
Alembic==1.12.0

# Web forms
WTForms==3.0.1

# Security
Werkzeug==2.3.7
itsdangerous==2.1.2
bcrypt==4.0.1

# Utilities
Jinja2==3.1.2
MarkupSafe==2.1.3
click==8.1.7
python-dotenv==1.0.0

# Production server
gunicorn==21.2.0

# Optional dependencies
redis==4.6.0
EOF
    
    # 修复Dockerfile
    if [ -f "Dockerfile" ]; then
        cp Dockerfile Dockerfile.backup
        log_info "已备份原始Dockerfile"
    fi
    
    # 创建修复版Dockerfile
    cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 升级pip
RUN python -m pip install --upgrade pip

# 复制并安装Python依赖
COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要目录
RUN mkdir -p instance logs static/uploads

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--timeout", "180", "app:app"]
EOF
    
    log_success "Docker构建文件修复完成"
}

# 清理并重新构建
rebuild_docker() {
    log_info "清理并重新构建Docker镜像..."
    
    # 停止并删除现有容器
    docker-compose -f docker-compose.nas.yml down 2>/dev/null || true
    
    # 删除现有镜像
    docker rmi project_mgmt-bak_web 2>/dev/null || true
    docker rmi project_mgmt-bak-web 2>/dev/null || true
    
    # 清理Docker缓存
    docker system prune -f
    docker builder prune -f
    
    log_success "Docker清理完成"
}

# 部署服务
deploy_services() {
    log_info "重新部署服务..."
    
    # 创建配置文件
    cat > .env << 'EOF'
SECRET_KEY=ds423-secret-key
HTTP_PORT=8088
HTTPS_PORT=8448
ADMIN_PASSWORD=admin123
ENABLE_REDIS=false
WORKERS=1
TIMEOUT=180
EOF
    
    # 启动服务
    if [ -f "docker-compose.nas.yml" ]; then
        log_info "启动NAS服务..."
        docker-compose -f docker-compose.nas.yml up -d --build
    else
        log_error "未找到docker-compose.nas.yml文件"
        exit 1
    fi
    
    log_success "服务部署完成"
}

# 验证部署
verify_deployment() {
    log_info "验证部署..."
    
    # 等待服务启动
    sleep 60
    
    # 检查容器状态
    log_info "容器状态:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    # 检查Web服务
    for i in {1..10}; do
        if curl -f http://localhost:8088/health &>/dev/null; then
            log_success "Web服务验证通过"
            break
        elif [ $i -eq 10 ]; then
            log_warning "Web服务验证超时，请手动检查"
            docker logs project_mgmt_web --tail 50
        else
            log_info "等待Web服务... ($i/10)"
            sleep 15
        fi
    done
}

# 主函数
main() {
    echo "========================================"
    echo "DS423+ 路径和构建问题修复脚本"
    echo "========================================"
    
    fix_path_issues
    fix_docker_build
    rebuild_docker
    deploy_services
    verify_deployment
    
    echo
    log_success "修复部署完成!"
    log_info "访问地址: http://your-nas-ip:8088"
    log_info "默认账户: admin / admin123"
}

# 执行
main "$@"
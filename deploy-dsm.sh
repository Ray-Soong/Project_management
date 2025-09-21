#!/bin/bash

# DSM服务器部署脚本
# 适用于群晖NAS DSM 7.x系统

set -e

# 配置变量
PROJECT_NAME="project-mgmt"
DEPLOY_DIR="/volume1/docker/project-mgmt"
BACKUP_DIR="/volume1/docker/backups/project-mgmt"
NGINX_SSL_DIR="/volume1/docker/project-mgmt/nginx/ssl"
LOG_FILE="/volume1/docker/project-mgmt/deploy.log"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_info() {
    log "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    log "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    log "${RED}[ERROR]${NC} $1"
}

# 检查是否为root用户
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要root权限运行"
        log_info "请使用: sudo $0"
        exit 1
    fi
}

# 检查Docker是否安装
check_docker() {
    log_info "检查Docker安装状态..."
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先在DSM套件中心安装Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装，请安装Docker Compose"
        exit 1
    fi
    
    log_info "Docker检查通过"
}

# 创建目录结构
create_directories() {
    log_info "创建部署目录结构..."
    
    mkdir -p "$DEPLOY_DIR"
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$NGINX_SSL_DIR"
    mkdir -p "/volume1/docker/project-mgmt/logs"
    mkdir -p "/volume1/docker/project-mgmt/instance"
    
    log_info "目录结构创建完成"
}

# 生成SSL证书
generate_ssl_cert() {
    log_info "生成自签名SSL证书..."
    
    if [[ ! -f "$NGINX_SSL_DIR/cert.pem" || ! -f "$NGINX_SSL_DIR/key.pem" ]]; then
        openssl req -x509 -newkey rsa:4096 -keyout "$NGINX_SSL_DIR/key.pem" \
            -out "$NGINX_SSL_DIR/cert.pem" -days 365 -nodes \
            -subj "/C=CN/ST=State/L=City/O=Organization/CN=project-mgmt.local"
        
        chmod 600 "$NGINX_SSL_DIR/key.pem"
        chmod 644 "$NGINX_SSL_DIR/cert.pem"
        
        log_info "SSL证书生成完成"
    else
        log_info "SSL证书已存在，跳过生成"
    fi
}

# 创建环境配置文件
create_env_file() {
    log_info "创建环境配置文件..."
    
    cat > "$DEPLOY_DIR/.env" << EOF
# 应用配置
FLASK_ENV=production
CONFIG_TYPE=docker
SECRET_KEY=$(openssl rand -hex 32)

# 数据库配置 (SQLite)
DATABASE_URL=sqlite:///app/instance/projects.db

# 管理员账户
ADMIN_PASSWORD=$(openssl rand -base64 16)
DEV_PASSWORD=$(openssl rand -base64 16)

# 日志配置
LOG_LEVEL=INFO

# 时区配置
TZ=Asia/Shanghai
EOF
    
    chmod 600 "$DEPLOY_DIR/.env"
    log_info "环境配置文件创建完成"
}

# 复制项目文件
copy_project_files() {
    log_info "复制项目文件到部署目录..."
    
    # 假设项目文件在当前目录
    cp -r . "$DEPLOY_DIR/app"
    
    # 删除开发环境文件
    rm -f "$DEPLOY_DIR/app/instance/projects.db"
    rm -rf "$DEPLOY_DIR/app/project_mgmt_env"
    rm -rf "$DEPLOY_DIR/app/__pycache__"
    
    log_info "项目文件复制完成"
}

# 修改docker-compose.yml以适配DSM
create_dsm_compose() {
    log_info "创建适配DSM的docker-compose.yml..."
    
    cat > "$DEPLOY_DIR/docker-compose.yml" << 'EOF'
version: '3.8'

services:
  web:
    build: ./app
    environment:
      - FLASK_ENV=production
      - CONFIG_TYPE=docker
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
      - ADMIN_PASSWORD=${ADMIN_PASSWORD}
      - DEV_PASSWORD=${DEV_PASSWORD}
      - LOG_LEVEL=${LOG_LEVEL}
      - TZ=${TZ}
    ports:
      - "5000:5000"
    volumes:
      - /volume1/docker/project-mgmt/logs:/app/logs
      - /volume1/docker/project-mgmt/instance:/app/instance
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - project-mgmt-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - ./app/static:/var/www/static
    depends_on:
      - web
    restart: unless-stopped
    networks:
      - project-mgmt-network

networks:
  project-mgmt-network:
    driver: bridge
EOF
    
    log_info "DSM docker-compose.yml创建完成"
}

# 部署应用
deploy_application() {
    log_info "开始部署应用..."
    
    cd "$DEPLOY_DIR"
    
    # 停止现有容器
    docker-compose down --remove-orphans
    
    # 构建并启动服务
    docker-compose up -d --build
    
    log_info "等待服务启动..."
    sleep 30
    
    # 检查服务状态
    if docker-compose ps | grep -q "Up"; then
        log_info "应用部署成功！"
        docker-compose ps
    else
        log_error "应用部署失败，请检查日志"
        docker-compose logs
        exit 1
    fi
}

# 创建备份脚本
create_backup_script() {
    log_info "创建备份脚本..."
    
    cat > "/usr/local/bin/backup-project-mgmt.sh" << 'EOF'
#!/bin/bash

BACKUP_DIR="/volume1/docker/backups/project-mgmt"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$DATE.tar.gz"

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 备份SQLite数据库和应用数据
tar -czf "$BACKUP_FILE" /volume1/docker/project-mgmt/instance /volume1/docker/project-mgmt/logs

# 清理7天前的备份
find "$BACKUP_DIR" -name "backup_*.tar.gz" -mtime +7 -delete

echo "备份完成: $BACKUP_FILE"
EOF
    
    chmod +x "/usr/local/bin/backup-project-mgmt.sh"
    log_info "备份脚本创建完成"
}

# 创建systemd服务
create_systemd_service() {
    log_info "创建systemd服务..."
    
    cat > "/etc/systemd/system/project-mgmt.service" << EOF
[Unit]
Description=项目管理系统
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$DEPLOY_DIR
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable project-mgmt.service
    
    log_info "systemd服务创建完成"
}

# 显示部署信息
show_deployment_info() {
    log_info "部署信息:"
    echo "=================================="
    echo "应用URL: https://your-dsm-ip"
    echo "管理员账户: admin"
    echo "管理员密码: 请查看 $DEPLOY_DIR/.env 文件中的 ADMIN_PASSWORD"
    echo ""
    echo "开发者账户: developer"
    echo "开发者密码: 请查看 $DEPLOY_DIR/.env 文件中的 DEV_PASSWORD"
    echo ""
    echo "部署目录: $DEPLOY_DIR"
    echo "日志目录: /volume1/docker/project-mgmt/logs"
    echo "备份目录: $BACKUP_DIR"
    echo ""
    echo "管理命令:"
    echo "  启动服务: systemctl start project-mgmt"
    echo "  停止服务: systemctl stop project-mgmt"
    echo "  查看状态: systemctl status project-mgmt"
    echo "  查看日志: docker-compose -f $DEPLOY_DIR/docker-compose.yml logs"
    echo "  备份数据: /usr/local/bin/backup-project-mgmt.sh"
    echo "=================================="
}

# 主函数
main() {
    log_info "开始DSM项目管理系统部署..."
    
    check_root
    check_docker
    create_directories
    generate_ssl_cert
    create_env_file
    copy_project_files
    create_dsm_compose
    deploy_application
    create_backup_script
    create_systemd_service
    show_deployment_info
    
    log_info "部署完成！"
}

# 执行主函数
main "$@"
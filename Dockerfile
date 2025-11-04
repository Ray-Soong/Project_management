FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# 升级pip到最新版本
RUN pip install --upgrade pip

# 复制requirements文件
COPY requirements.txt .

# 创建SQLite优化版的requirements.txt
RUN cat > requirements_sqlite.txt << 'EOF'
# Core Flask packages
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-Login==0.6.3
Flask-WTF==1.1.1
Flask-Migrate==4.0.5

# Database - SQLite优化
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

# 日期时间处理
python-dateutil==2.8.2
EOF

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements_sqlite.txt

# 复制应用代码
COPY . .

# 创建必要的目录和SQLite数据库目录
RUN mkdir -p instance logs static/uploads data

# 设置权限
RUN chmod +x *.py

# 初始化SQLite数据库
RUN touch /app/data/project_mgmt.db && chmod 666 /app/data/project_mgmt.db

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--timeout", "180", "app:app"]
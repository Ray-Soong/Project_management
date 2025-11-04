#!/usr/bin/env python3
"""
WSGI入口文件，用于生产环境部署
"""
import os
import sys

# 设置环境变量
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('CONFIG_TYPE', 'docker')

# 尝试使用生产环境app
try:
    from app_prod import create_app
    app = create_app()
except ImportError:
    # 回退到开发环境app
    from app import app

# 添加健康检查端点（如果不存在）
@app.route('/health')
def health_check():
    try:
        from models import db
        db.session.execute('SELECT 1')
        return {'status': 'healthy', 'database': 'connected'}, 200
    except Exception as e:
        app.logger.error(f'健康检查失败: {e}')
        return {'status': 'unhealthy', 'error': str(e)}, 500

if __name__ == "__main__":
    # 开发模式运行
    app.run(host='0.0.0.0', port=8088, debug=False)
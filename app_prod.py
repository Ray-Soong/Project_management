#!/usr/bin/env python3
"""
生产环境应用入口文件
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from config_prod import config

def create_app(config_name=None):
    """应用工厂函数"""
    if config_name is None:
        config_name = os.environ.get('CONFIG_TYPE', 'production')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # 配置日志
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler(
            'logs/project_mgmt.log', 
            maxBytes=10240000, 
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('项目管理系统启动')
    
    # 导入并注册蓝图
    from models import db, Project, User, WorkLog, ProjectAssignment, StagePayment
    from forms import ProjectForm, LoginForm, UserForm, WorkLogForm, ProjectStatusForm
    
    # 初始化数据库
    db.init_app(app)
    
    # 注册Flask-Login
    from flask_login import LoginManager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "login"
    login_manager.login_message = "请先登录"
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # 健康检查端点
    @app.route('/health')
    def health_check():
        try:
            # 检查SQLite数据库连接
            db.session.execute('SELECT 1')
            return {'status': 'healthy', 'database': 'connected'}, 200
        except Exception as e:
            app.logger.error(f'健康检查失败: {e}')
            return {'status': 'unhealthy', 'error': str(e)}, 500
    
    # 创建数据库表和初始数据
    with app.app_context():
        try:
            db.create_all()
            
            # 创建初始用户
            if not User.query.filter_by(username='admin').first():
                admin = User(username='admin', role='admin')
                admin.set_password(os.environ.get('ADMIN_PASSWORD', 'admin123'))
                db.session.add(admin)
            
            if not User.query.filter_by(username='developer').first():
                developer = User(username='developer', role='developer')
                developer.set_password(os.environ.get('DEV_PASSWORD', 'dev123'))
                db.session.add(developer)
            
            db.session.commit()
            app.logger.info('数据库初始化完成')
            
        except Exception as e:
            app.logger.error(f'数据库初始化失败: {e}')
    
    return app

# 创建应用实例
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
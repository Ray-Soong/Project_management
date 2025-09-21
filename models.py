from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from decimal import Decimal

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'developer'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_developer(self):
        return self.role == 'developer'

class Project(db.Model):
    __tablename__ = "projects"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), nullable=False)
    manager = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=True)
    planned_end_date = db.Column(db.Date, nullable=True)
    estimated_completion_date = db.Column(db.Date, nullable=True)  # 预计完成时间
    estimated_hours = db.Column(db.Float, nullable=True)  # 预计开发工时
    contract_amount = db.Column(db.Numeric(14, 2), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='立项')  # 项目状态
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 项目状态选项
    STATUS_CHOICES = [
        ('立项', '立项'),
        ('开发', '开发'),
        ('结项', '结项'),
        ('跟进收款', '跟进收款'),
        ('维护', '维护')
    ]

    def get_total_logged_hours(self):
        """获取项目已记录的总工时"""
        return sum(log.hours for log in self.work_logs)
    
    def get_progress_percentage(self):
        """获取项目进度百分比"""
        if not self.estimated_hours:
            return 0
        logged_hours = self.get_total_logged_hours()
        return min(100, (logged_hours / self.estimated_hours) * 100)
    
    def get_assigned_developers(self):
        """获取分配给项目的开发者列表"""
        return [assignment.user for assignment in self.assignments]
    
    def get_status_color(self):
        """根据状态返回对应的颜色"""
        status_colors = {
            '立项': '#6c757d',      # 灰色
            '开发': '#007bff',      # 蓝色
            '结项': '#28a745',      # 绿色
            '跟进收款': '#ffc107',  # 黄色
            '维护': '#17a2b8'       # 青色
        }
        return status_colors.get(self.status, '#6c757d')
    
    def get_total_development_cost(self):
        """计算项目总开发费用（工时 * 工时费用）"""
        total_cost = 0
        for log in self.work_logs:
            # 通过项目分配找到该开发者在此项目的工时费用
            assignment = ProjectAssignment.query.filter_by(
                project_id=self.id, 
                user_id=log.user_id
            ).first()
            if assignment and assignment.hourly_rate:
                # 类型转换：将 Decimal 转换为 float 进行计算
                hourly_rate = float(assignment.hourly_rate)
                total_cost += log.hours * hourly_rate
        return total_cost
    
    def get_developer_costs(self):
        """获取每个开发者的费用明细"""
        developer_costs = {}
        for log in self.work_logs:
            assignment = ProjectAssignment.query.filter_by(
                project_id=self.id, 
                user_id=log.user_id
            ).first()
            dev_name = log.user.username
            if dev_name not in developer_costs:
                developer_costs[dev_name] = {
                    'hours': 0,
                    'rate': float(assignment.hourly_rate) if assignment and assignment.hourly_rate else 0,
                    'cost': 0
                }
            
            developer_costs[dev_name]['hours'] += log.hours
            if assignment and assignment.hourly_rate:
                hourly_rate = float(assignment.hourly_rate)
                developer_costs[dev_name]['cost'] += log.hours * hourly_rate
        
        return developer_costs

# 项目开发者分配关联表
class ProjectAssignment(db.Model):
    __tablename__ = "project_assignments"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    hourly_rate = db.Column(db.Numeric(10, 2), nullable=True)  # 工时费用，只有管理员可见
    assigned_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    project = db.relationship('Project', backref=db.backref('assignments', lazy=True, cascade='all, delete-orphan'))
    user = db.relationship('User', backref=db.backref('project_assignments', lazy=True))

class WorkLog(db.Model):
    __tablename__ = "work_logs"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    hours = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    user = db.relationship('User', backref=db.backref('work_logs', lazy=True))
    project = db.relationship('Project', backref=db.backref('work_logs', lazy=True))

    def get_cost(self):
        """获取该工时记录的费用"""
        assignment = ProjectAssignment.query.filter_by(
            project_id=self.project_id, 
            user_id=self.user_id
        ).first()
        if assignment and assignment.hourly_rate:
            return self.hours * assignment.hourly_rate
        return 0

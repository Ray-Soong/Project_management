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
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'finance', 'developer', 'project_manager'
    created_at = db.Column(db.DateTime, default=datetime.now)
    default_hourly_rate = db.Column(db.Numeric(10, 2), nullable=True)  # 默认工时费用
    
    # 角色常量
    ROLE_ADMIN = 'admin'
    ROLE_FINANCE = 'finance'
    ROLE_DEVELOPER = 'developer'
    ROLE_PROJECT_MANAGER = 'project_manager'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """是否为管理员"""
        return self.role == self.ROLE_ADMIN
    
    def is_finance(self):
        """是否为财务"""
        return self.role == self.ROLE_FINANCE
    
    def is_developer(self):
        """是否为开发工程师"""
        return self.role == self.ROLE_DEVELOPER
    
    def is_project_manager(self):
        """是否为项目经理"""
        return self.role == self.ROLE_PROJECT_MANAGER
    
    def has_full_access(self):
        """是否拥有完全访问权限（管理员和财务）"""
        return self.role in [self.ROLE_ADMIN, self.ROLE_FINANCE]
    
    def can_view_project(self, project_id):
        """检查是否可以查看指定项目"""
        if self.has_full_access():
            return True
        if self.is_project_manager():
            # 项目经理只能查看关联的项目
            assignment = ProjectManagerAssignment.query.filter_by(
                user_id=self.id,
                project_id=project_id
            ).first()
            return assignment is not None
        if self.is_developer():
            # 开发工程师只能查看被分配的项目
            assignment = ProjectAssignment.query.filter_by(
                user_id=self.id,
                project_id=project_id
            ).first()
            return assignment is not None
        return False
    
    def get_accessible_project_ids(self):
        """获取用户可访问的项目ID列表"""
        if self.has_full_access():
            # 管理员和财务可以访问所有项目
            return [p.id for p in Project.query.all()]
        elif self.is_project_manager():
            # 项目经理只能访问关联的项目
            assignments = ProjectManagerAssignment.query.filter_by(user_id=self.id).all()
            return [a.project_id for a in assignments]
        elif self.is_developer():
            # 开发工程师只能访问被分配的项目
            assignments = ProjectAssignment.query.filter_by(user_id=self.id).all()
            return [a.project_id for a in assignments]
        return []

class Project(db.Model):
    __tablename__ = "projects"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_number = db.Column(db.String(20), unique=True, nullable=True)  # 项目编号
    name = db.Column(db.String(200), nullable=False)
    manager = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=True)
    planned_end_date = db.Column(db.Date, nullable=True)
    contract_signing_date = db.Column(db.Date, nullable=True)  # 合同签订日期
    estimated_hours = db.Column(db.Float, nullable=True)  # 预计开发工时
    contract_amount = db.Column(db.Numeric(14, 2), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='启动中')  # 项目状态
    payment_method = db.Column(db.String(50), nullable=True)  # 付款方式
    acceptance_date = db.Column(db.Date, nullable=True)  # 验收日期
    settlement_date = db.Column(db.Date, nullable=True)  # 结算日期
    invoice_stage = db.Column(db.String(20), nullable=True, default='未开')  # 当前发票开具阶段
    invoice_date = db.Column(db.Date, nullable=True)  # 开票日期
    invoice_amount = db.Column(db.Numeric(14, 2), nullable=True)  # 发票金额(含税)
    invoice_file = db.Column(db.String(500), nullable=True)  # 发票文件路径
    invoice_notes = db.Column(db.Text, nullable=True)  # 开票备注
    contract_amount_with_tax = db.Column(db.Numeric(14, 2), nullable=True)  # 合同金额含税
    contract_amount_without_tax = db.Column(db.Numeric(14, 2), nullable=True)  # 合同金额
    payment_received = db.Column(db.Numeric(14, 2), nullable=True)  # 回款金额(含税)
    remaining_amount = db.Column(db.Numeric(14, 2), nullable=True)  # 剩余金额
    project_type = db.Column(db.String(50), nullable=True)  # 项目类型
    customer_name = db.Column(db.String(200), nullable=True)  # 客户名称
    final_customer = db.Column(db.String(200), nullable=True)  # 最终客户
    po_number = db.Column(db.String(100), nullable=True)  # PO号
    contract_file = db.Column(db.String(500), nullable=True)  # 合同文件路径
    created_at = db.Column(db.DateTime, default=datetime.now)
    outsourcing_cost = db.Column(db.Numeric(10, 2), default=0)  # 外包费用(含税)
    outsourcing_cost_without_tax = db.Column(db.Numeric(10, 2), default=0)  # 外包费用(不含税)
    supplier_name = db.Column(db.String(200), nullable=True)  # 供应商名称
    supplier_invoice_issued = db.Column(db.Boolean, default=False)  # 供应商发票是否开具
    supplier_pending_amount = db.Column(db.Numeric(10, 2), default=0)  # 供应商待付金额(不含税)
    outsourcing_cost_notes = db.Column(db.Text)  # 外包费用备注
    indirect_cost = db.Column(db.Numeric(10, 2), default=0)  # 间接成本
    indirect_cost_notes = db.Column(db.Text)  # 间接成本备注
    stage_payment_notes = db.Column(db.Text)  # 阶段付款备注
    payment_amount_notes = db.Column(db.Text)  # 回款金额备注
    invoice_amount_issued = db.Column(db.Numeric(14, 2), default=0)  # 已开发票金额
    current_invoice_amount = db.Column(db.Numeric(14, 2), default=0)  # 当前发票金额
    accounts_receivable = db.Column(db.Numeric(14, 2), default=0)  # 应收账款
    area = db.Column(db.Numeric(10, 2), nullable=True)  # 面积
    unit_price = db.Column(db.Numeric(10, 2), nullable=True)  # 单价
    
    # 关系
    values = db.relationship('ProjectCustomFieldValue', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    invoice_files = db.relationship('InvoiceFile', backref='project', lazy=True, cascade='all, delete-orphan')

    # 项目状态选项
    STATUS_CHOICES = [
        ('启动中', '启动中'),
        ('进行中', '进行中'),
        ('暂停', '暂停'),
        ('验收中', '验收中'),
        ('验收待回款', '验收待回款'),
        ('结算', '结算')
    ]
    
    # 付款方式选项
    PAYMENT_METHOD_CHOICES = [
        ('验收后全款', '验收后全款'),
        ('分阶段付款（3/5/2）', '分阶段付款（3/5/2）'),
        ('分阶段付款（3/6/1）', '分阶段付款（3/6/1）'),
        ('分阶段付款（3/4/3）', '分阶段付款（3/4/3）'),
        ('分阶段付款（5/5）', '分阶段付款（5/5）'),
        ('分阶段付款（3/7）', '分阶段付款（3/7）'),
        ('分阶段付款（4/6）', '分阶段付款（4/6）'),
        ('按小时付款', '按小时付款')
    ]
    
    # 项目类型选项
    PROJECT_TYPE_CHOICES = [
        ('物流仿真', '物流仿真'),
        ('机器人仿真', '机器人仿真'),
        ('工艺规划', '工艺规划'),
        ('物流规划', '物流规划'),
        ('动画', '动画'),
        ('激光扫描', '激光扫描'),
        ('数字孪生', '数字孪生'),
        ('虚拟调试', '虚拟调试')
    ]
    
    # 当前发票开具阶段选项
    INVOICE_STAGE_CHOICES = [
        ('未开', '未开'),
        ('预付款', '预付款'),
        ('第二阶段', '第二阶段'),
        ('第三阶段', '第三阶段'),
        ('第四阶段', '第四阶段'),
        ('尾款', '尾款')
    ]

    def get_total_logged_hours(self):
        """获取项目已记录的总工时"""
        return sum(log.hours for log in self.work_logs)
    
    @staticmethod
    def generate_project_number():
        """生成项目编号，格式为YYYYMMDD##"""
        from datetime import datetime
        today = datetime.now()
        date_prefix = today.strftime('%Y%m%d')
        
        # 查找今天创建的最后一个项目编号
        last_project = Project.query.filter(
            Project.project_number.like(f'{date_prefix}%')
        ).order_by(Project.project_number.desc()).first()
        
        if last_project and last_project.project_number:
            # 提取最后两位数字并加1
            last_number = int(last_project.project_number[-2:])
            new_number = last_number + 1
        else:
            # 今天第一个项目
            new_number = 1
        
        # 格式化为两位数
        return f"{date_prefix}{new_number:02d}"
    
    def get_progress_percentage(self):
        """获取项目进度百分比"""
        if not self.estimated_hours:
            return 0
        logged_hours = self.get_total_logged_hours()
        return min(100, (logged_hours / self.estimated_hours) * 100)
    
    def get_assigned_developers(self):
        """获取分配给项目的开发者列表"""
        return [assignment.user for assignment in self.assignments]
    
    def calculate_remaining_amount(self):
        """计算剩余金额"""
        if self.contract_amount_with_tax and self.payment_received:
            return float(self.contract_amount_with_tax) - float(self.payment_received)
        elif self.contract_amount_with_tax:
            return float(self.contract_amount_with_tax)
        return 0
    
    def get_status_color(self):
        """根据状态返回对应的背景色（淡色）"""
        status_colors = {
            '启动中': '#e9ecef',     # 淡灰色
            '进行中': '#cfe2ff',     # 淡蓝色
            '暂停': '#fff3cd',       # 淡黄色
            '验收中': '#ffe5d0',     # 淡橙色
            '验收待回款': '#d1e7dd', # 淡绿色
            '已结算': '#d2f4ea'       # 淡青绿色
        }
        return status_colors.get(self.status, '#e9ecef')
    
    def get_status_text_color(self):
        """根据状态返回对应的字体颜色（深色）"""
        text_colors = {
            '启动中': '#495057',     # 深灰色
            '进行中': '#084298',     # 深蓝色
            '暂停': '#997404',       # 深黄色
            '验收中': '#cc5200',     # 深橙色
            '验收待回款': '#0a5828', # 深绿色
            '已结算': '#087f5b'       # 深青绿色
        }
        return text_colors.get(self.status, '#495057')
    
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
    
    def get_total_cost(self):
        """获取项目总费用（开发费用 + 已批准的报销费用 + 外包费用(不含税) + 间接成本)"""
        # 开发费用
        dev_cost = self.get_total_development_cost()
        
        # 报销费用（只计算已批准的）
        expense_cost = 0
        project_expenses = Expense.query.filter_by(project_id=self.id, status='已批准').all()
        expense_cost = sum(float(e.total_amount) for e in project_expenses)
        
        # 外包费用(不含税)
        outsourcing = float(self.outsourcing_cost_without_tax) if self.outsourcing_cost_without_tax else 0
        
        # 间接成本
        indirect = float(self.indirect_cost) if self.indirect_cost else 0

        return dev_cost + expense_cost + outsourcing + indirect
    
    def get_gross_profit(self):
        """获取项目毛利（回款金额/1.06 - 总成本，将含税回款转为不含税）"""
        payment_received = float(self.payment_received) if self.payment_received else 0
        total_cost = self.get_total_cost()
        # 回款金额/1.06 得到不含税金额，然后减去总成本
        return payment_received / 1.06 - total_cost

# 项目开发者分配关联表
class ProjectAssignment(db.Model):
    __tablename__ = "project_assignments"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    hourly_rate = db.Column(db.Numeric(10, 2), nullable=True)  # 工时费用，只有管理员可见
    assigned_date = db.Column(db.DateTime, default=datetime.now)
    
    # 关系
    project = db.relationship('Project', backref=db.backref('assignments', lazy=True, cascade='all, delete-orphan'))
    user = db.relationship('User', backref=db.backref('project_assignments', lazy=True))

class ProjectManagerAssignment(db.Model):
    """项目经理关联表"""
    __tablename__ = "project_manager_assignments"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assigned_date = db.Column(db.DateTime, default=datetime.now)
    
    # 关系
    project = db.relationship('Project', backref=db.backref('manager_assignments', lazy=True, cascade='all, delete-orphan'))
    user = db.relationship('User', backref=db.backref('managed_projects', lazy=True))

class WorkLog(db.Model):
    __tablename__ = "work_logs"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    hours = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
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

# 阶段付款表
class StagePayment(db.Model):
    __tablename__ = "stage_payments"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    stage_name = db.Column(db.String(100), nullable=False)  # 阶段名称
    payment_amount = db.Column(db.Numeric(14, 2), nullable=False)  # 付款金额
    payment_date = db.Column(db.Date, nullable=True)  # 入款日期
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关系
    project = db.relationship('Project', backref=db.backref('stage_payments', lazy=True, cascade='all, delete-orphan'))

# 报销单表
class Expense(db.Model):
    __tablename__ = "expenses"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)  # 可关联项目，也可以是售前费用
    title = db.Column(db.String(200), nullable=False)  # 报销标题
    expense_type = db.Column(db.String(50), nullable=False)  # 费用类型：项目费用、售前费用
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)  # 总金额
    status = db.Column(db.String(20), nullable=False, default='新建')  # 状态：新建、处理中、通过
    submit_date = db.Column(db.DateTime, default=datetime.now)  # 提交日期
    approve_date = db.Column(db.DateTime, nullable=True)  # 审批日期
    approver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # 审批人
    approve_comment = db.Column(db.Text, nullable=True)  # 审批意见
    description = db.Column(db.Text, nullable=True)  # 报销说明
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 费用类型选项
    EXPENSE_TYPE_CHOICES = [
        ('项目费用', '项目费用'),
        ('售前费用', '售前费用'),
        ('其他费用', '其他费用')
    ]
    
    # 状态选项
    STATUS_CHOICES = [
        ('新建', '新建'),
        ('处理中', '处理中'),
        ('等待退款', '等待退款'),
        ('退款完成', '退款完成'),
        ('已完成', '已完成')
    ]
    
    # 关系
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('expenses', lazy=True))
    project = db.relationship('Project', backref=db.backref('expenses', lazy=True))
    approver = db.relationship('User', foreign_keys=[approver_id], backref=db.backref('approved_expenses', lazy=True))
    
    def get_status_color(self):
        """根据状态返回对应的颜色"""
        status_colors = {
            '新建': '#6c757d',       # 灰色
            '处理中': '#17a2b8',     # 青色
            '等待退款': '#fd7e14',   # 橙色
            '退款完成': '#28a745',   # 绿色
            '已完成': '#28a745'      # 绿色
        }
        return status_colors.get(self.status, '#6c757d')

# 报销明细表
class ExpenseItem(db.Model):
    __tablename__ = "expense_items"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    expense_id = db.Column(db.Integer, db.ForeignKey('expenses.id'), nullable=False)
    item_name = db.Column(db.String(200), nullable=False)  # 费用明细名称
    category = db.Column(db.String(50), nullable=False)  # 费用类别
    amount = db.Column(db.Numeric(10, 2), nullable=False)  # 费用金额
    receipt_image = db.Column(db.Text, nullable=True)  # 发票/凭证照片路径（支持多文件，用;分隔）
    receipt_original_name = db.Column(db.Text, nullable=True)  # 原始文件名（支持多文件，用;分隔）
    description = db.Column(db.Text, nullable=True)  # 费用说明
    expense_date = db.Column(db.Date, nullable=False)  # 费用发生日期
    start_date = db.Column(db.Date, nullable=True)  # 费用起始日期
    end_date = db.Column(db.Date, nullable=True)  # 费用结束日期
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 费用类别选项
    CATEGORY_CHOICES = [
        ('业务招待费', '业务招待费'),
        ('办公用品', '办公用品'),
        ('差旅费', '差旅费'),
        ('通讯费', '通讯费'),
        ('外包费（对私）', '外包费（对私）'),
        ('外包费（对公不含税）', '外包费（对公不含税）'),
        ('福利费', '福利费'),
        ('电脑网络打印机硬件费', '电脑网络打印机硬件费'),
        ('培训费', '培训费'),
        ('商务费', '商务费'),
        ('团建费', '团建费'),
        ('财务和审计', '财务和审计'),
        ('其他费用', '其他费用')
    ]
    
    # 关系
    expense = db.relationship('Expense', backref=db.backref('items', lazy=True, cascade='all, delete-orphan'))

# 任务分配表
class Task(db.Model):
    __tablename__ = "tasks"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False)  # 任务标题
    description = db.Column(db.Text, nullable=True)  # 任务描述
    task_type = db.Column(db.String(50), nullable=False)  # 任务类型：expense_process（报销处理）等
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 审批人
    assigned_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 谁分配的
    expense_id = db.Column(db.Integer, db.ForeignKey('expenses.id'), nullable=True)  # 关联的报销ID
    status = db.Column(db.String(20), nullable=False, default='处理中')  # 处理中、已完成
    priority = db.Column(db.String(20), nullable=False, default='普通')  # 紧急、高、普通、低
    created_at = db.Column(db.DateTime, default=datetime.now)
    due_date = db.Column(db.DateTime, nullable=True)  # 截止日期
    completed_at = db.Column(db.DateTime, nullable=True)  # 完成时间
    
    # 任务状态选项
    STATUS_CHOICES = [
        ('处理中', '处理中'),
        ('等待退款', '等待退款'),
        ('退款完成', '退款完成'),
        ('已完成', '已完成')
    ]
    
    # 优先级选项
    PRIORITY_CHOICES = [
        ('紧急', '紧急'),
        ('高', '高'),
        ('普通', '普通'),
        ('低', '低')
    ]
    
    # 关系
    assigned_user = db.relationship('User', foreign_keys=[assigned_to], backref=db.backref('assigned_tasks', lazy=True))
    assigner = db.relationship('User', foreign_keys=[assigned_by], backref=db.backref('created_tasks', lazy=True))
    expense = db.relationship('Expense', backref=db.backref('tasks', lazy=True, cascade='all, delete-orphan'))
    
    def get_status_color(self):
        """根据状态返回对应的颜色"""
        status_colors = {
            '处理中': '#007bff',     # 蓝色
            '等待退款': '#fd7e14',   # 橙色
            '退款完成': '#28a745',   # 绿色
            '已完成': '#28a745'      # 绿色
        }
        return status_colors.get(self.status, '#6c757d')
    
    def get_priority_color(self):
        """根据优先级返回对应的颜色"""
        priority_colors = {
            '紧急': '#dc3545',       # 红色
            '高': '#fd7e14',         # 橙色
            '普通': '#28a745',       # 绿色
            '低': '#6c757d'          # 灰色
        }
        return priority_colors.get(self.priority, '#6c757d')
    
    def validate_expense_process_task(self):
        """验证expense_process类型的任务必须关联expense_id"""
        if self.task_type == 'expense_process' and not self.expense_id:
            raise ValueError(f"报销处理任务（expense_process）必须关联一个报销单。任务标题：{self.title}")
    
    def __repr__(self):
        return f"<Task {self.id}: {self.title} ({self.status})>"

# 项目费用记录表
class ProjectExpenseRecord(db.Model):
    __tablename__ = "project_expense_records"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    expense_id = db.Column(db.Integer, db.ForeignKey('expenses.id'), nullable=True)  # 改为可为空
    category = db.Column(db.String(50), nullable=False)  # 费用类别
    amount = db.Column(db.Numeric(10, 2), nullable=False)  # 费用金额
    description = db.Column(db.Text, nullable=True)  # 费用说明
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 记录人
    recorded_at = db.Column(db.DateTime, default=datetime.now)  # 记录时间
    
    # 关系
    project = db.relationship('Project', backref=db.backref('expense_records', lazy=True))
    expense = db.relationship('Expense', backref=db.backref('project_records', lazy=True))
    recorder = db.relationship('User', backref=db.backref('recorded_expenses', lazy=True))

# 自定义字段表
class CustomField(db.Model):
    __tablename__ = 'custom_fields'
    
    id = db.Column(db.Integer, primary_key=True)
    field_name = db.Column(db.String(100), nullable=False)
    field_label = db.Column(db.String(100), nullable=False)
    field_type = db.Column(db.String(50), nullable=False)  # text, number, date, select, checkbox
    options = db.Column(db.Text)  # JSON格式存储选项（用于select类型）
    is_required = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关联到项目的自定义字段值
    values = db.relationship('ProjectCustomFieldValue', backref='custom_field', lazy='dynamic', cascade='all, delete-orphan')

class ProjectCustomFieldValue(db.Model):
    __tablename__ = 'project_custom_field_values'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    custom_field_id = db.Column(db.Integer, db.ForeignKey('custom_fields.id'), nullable=False)
    value = db.Column(db.Text)  # 存储字段值
    
    # 确保每个项目的每个自定义字段只有一个值
    __table_args__ = (db.UniqueConstraint('project_id', 'custom_field_id', name='_project_field_uc'),)

class OperationLog(db.Model):
    """操作日志模型"""
    __tablename__ = 'operation_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    operation_type = db.Column(db.String(50), nullable=False)  # 操作类型：登录、创建、编辑、删除、审批等
    operation_module = db.Column(db.String(50), nullable=False)  # 操作模块：项目、工时、报销、任务等
    operation_detail = db.Column(db.Text)  # 操作详情
    target_type = db.Column(db.String(50))  # 目标对象类型：project、worklog、expense等
    target_id = db.Column(db.Integer)  # 目标对象ID
    ip_address = db.Column(db.String(50))  # IP地址
    user_agent = db.Column(db.String(500))  # 浏览器信息
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    
    # 关联
    user = db.relationship('User', backref=db.backref('logs', lazy=True), foreign_keys=[user_id])
    
    def __repr__(self):
        return f'<OperationLog {self.user.username} - {self.operation_type} - {self.operation_module}>'
    
    def get_operation_icon(self):
        """获取操作类型对应的图标"""
        icons = {
            '登录': 'fa-sign-in-alt',
            '登出': 'fa-sign-out-alt',
            '创建': 'fa-plus-circle',
            '编辑': 'fa-edit',
            '删除': 'fa-trash-alt',
            '审批': 'fa-check-circle',
            '拒绝': 'fa-times-circle',
            '分配': 'fa-user-plus',
            '更新状态': 'fa-sync-alt',
            '上传': 'fa-upload',
            '下载': 'fa-download',
            '查看': 'fa-eye'
        }
        return icons.get(self.operation_type, 'fa-circle')


class InvoiceFile(db.Model):
    """发票文件模型 - 支持多个发票文件"""
    __tablename__ = 'invoice_files'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)  # 文件路径
    file_name = db.Column(db.String(300), nullable=False)  # 原始文件名
    file_type = db.Column(db.String(20), nullable=False)  # 文件类型: pdf, zip
    file_size = db.Column(db.Integer, nullable=True)  # 文件大小（字节）
    upload_date = db.Column(db.DateTime, default=datetime.now)  # 上传日期
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # 上传人
    description = db.Column(db.Text, nullable=True)  # 文件描述
    is_deleted = db.Column(db.Boolean, default=False)  # 软删除标记
    
    # 关系
    uploader = db.relationship('User', backref=db.backref('uploaded_invoice_files', lazy=True), foreign_keys=[uploaded_by])
    
    def __repr__(self):
        return f'<InvoiceFile {self.file_name}>'
    
    def get_file_icon(self):
        """根据文件类型获取对应的图标"""
        icons = {
            'pdf': 'fa-file-pdf',
            'zip': 'fa-file-archive'
        }
        return icons.get(self.file_type, 'fa-file')
    
    def get_operation_color(self):
        """获取操作类型对应的颜色"""
        colors = {
            '登录': '#28a745',
            '登出': '#6c757d',
            '创建': '#007bff',
            '编辑': '#ffc107',
            '删除': '#dc3545',
            '审批': '#28a745',
            '拒绝': '#dc3545',
            '分配': '#17a2b8',
            '更新状态': '#6f42c1',
            '上传': '#20c997',
            '下载': '#fd7e14',
            '查看': '#6c757d'
        }
        return colors.get(self.operation_type, '#6c757d')
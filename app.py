from flask import Flask, jsonify, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime
import logging
import os

# 设置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["SECRET_KEY"] = "yoursecret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///projects.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# 文件上传配置
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# 确保上传目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

from models import db, Project, User, WorkLog, ProjectAssignment, Expense, ExpenseItem, Task, ProjectExpenseRecord
from forms import ProjectForm, LoginForm, UserForm, WorkLogForm, ProjectStatusForm, ExpenseForm, ExpenseApprovalForm, TaskForm, TaskUpdateForm

# 登录管理器
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "请先登录"

db.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 创建初始数据
def create_initial_data():
    # 创建管理员账户
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
    
    # 创建开发者账户
    if not User.query.filter_by(username='developer').first():
        developer = User(username='developer', role='developer')
        developer.set_password('dev123')
        db.session.add(developer)
    
    db.session.commit()

with app.app_context():
    # 注意：在生产环境中，应该使用数据库迁移而不是 drop_all()
    # 如果数据库不存在，创建它；如果存在，保留数据
    try:
        # 尝试查询用户表来检查数据库是否存在
        User.query.first()
        print("数据库已存在，保留现有数据")
    except:
        # 如果查询失败，说明数据库不存在或表结构不对，重新创建
        print("创建新的数据库...")
        db.drop_all()
        db.create_all()
        create_initial_data()
        print("数据库初始化完成")

@app.route("/")
@login_required
def index():
    if current_user.is_admin():
        projects = Project.query.all()
        
        # 计算统计数据
        total_contract_amount = sum(
            float(p.contract_amount_with_tax) if p.contract_amount_with_tax else 0 
            for p in projects
        )
        
        total_dev_cost = sum(
            p.get_total_development_cost() for p in projects
        )
        
        active_projects_count = len([p for p in projects if p.status in ['启动中', '进行中']])
        
        stats = {
            'total_projects': len(projects),
            'active_projects': active_projects_count,
            'total_contract_amount': total_contract_amount,
            'total_dev_cost': total_dev_cost
        }
        
        return render_template("project_list.html", projects=projects, stats=stats)
    elif current_user.is_developer():
        return redirect(url_for('worklog_list'))
    else:
        flash("权限不足")
        return redirect(url_for('login'))

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        flash("用户名或密码错误")
    return render_template("login.html", form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/projects/create", methods=["GET", "POST"])
@login_required
def create_project():
    if not current_user.is_admin():
        flash("只有项目经理可以创建项目")
        return redirect(url_for("index"))
    
    form = ProjectForm()
    # 获取所有开发者用于选择
    developers = User.query.filter_by(role='developer').all()
    form.assigned_developers.choices = [(dev.id, dev.username) for dev in developers]
    
    if form.validate_on_submit():
        project = Project(
            name=form.name.data,
            manager=form.manager.data,
            customer_name=form.customer_name.data,
            project_type=form.project_type.data,
            start_date=form.start_date.data,
            planned_end_date=form.planned_end_date.data,
            acceptance_date=form.acceptance_date.data,
            contract_signing_date=form.contract_signing_date.data,
            settlement_date=form.settlement_date.data,
            invoice_date=form.invoice_date.data,
            estimated_hours=form.estimated_hours.data,
            contract_amount_with_tax=form.contract_amount_with_tax.data,
            contract_amount_without_tax=form.contract_amount_without_tax.data,
            payment_method=form.payment_method.data,
            payment_received=form.payment_received.data,
            invoice_issued=form.invoice_issued.data,
            status=form.status.data,
        )
        # 计算剩余金额
        if project.contract_amount_with_tax and project.payment_received:
            project.remaining_amount = project.contract_amount_with_tax - project.payment_received
        elif project.contract_amount_with_tax:
            project.remaining_amount = project.contract_amount_with_tax
        
        db.session.add(project)
        db.session.flush()  # 获取项目ID
        
        # 分配开发者
        for dev_id in form.assigned_developers.data:
            assignment = ProjectAssignment(project_id=project.id, user_id=dev_id)
            db.session.add(assignment)
        
        db.session.commit()
        flash("项目创建成功，请为开发者设置工时费用")
        return redirect(url_for("project_detail", project_id=project.id))
    return render_template("project_create.html", form=form)

@app.route("/projects/<int:project_id>")
@login_required
def project_detail(project_id):
    """项目详情页面"""
    if not current_user.is_admin():
        flash("只有项目经理可以查看项目详情")
        return redirect(url_for("index"))
    
    project = Project.query.get_or_404(project_id)
    developer_costs = project.get_developer_costs()
    total_cost = project.get_total_development_cost()
    
    return render_template("project_detail.html", 
                         project=project, 
                         developer_costs=developer_costs,
                         total_cost=total_cost)

@app.route("/projects/<int:project_id>/edit", methods=["GET", "POST"])
@login_required
def edit_project(project_id):
    if not current_user.is_admin():
        flash("只有项目经理可以编辑项目")
        return redirect(url_for("index"))
    
    project = Project.query.get_or_404(project_id)
    form = ProjectForm(obj=project)
    
    # 获取所有开发者用于选择
    developers = User.query.filter_by(role='developer').all()
    form.assigned_developers.choices = [(dev.id, dev.username) for dev in developers]
    
    # 设置已分配的开发者
    if request.method == 'GET':
        form.assigned_developers.data = [assignment.user_id for assignment in project.assignments]
    
    if form.validate_on_submit():
        project.name = form.name.data
        project.manager = form.manager.data
        project.customer_name = form.customer_name.data
        project.project_type = form.project_type.data
        project.start_date = form.start_date.data
        project.planned_end_date = form.planned_end_date.data
        project.acceptance_date = form.acceptance_date.data
        project.contract_signing_date = form.contract_signing_date.data
        project.settlement_date = form.settlement_date.data
        project.invoice_date = form.invoice_date.data
        project.estimated_hours = form.estimated_hours.data
        project.contract_amount_with_tax = form.contract_amount_with_tax.data
        project.contract_amount_without_tax = form.contract_amount_without_tax.data
        project.payment_method = form.payment_method.data
        project.payment_received = form.payment_received.data
        project.invoice_issued = form.invoice_issued.data
        project.status = form.status.data
        
        # 重新计算剩余金额
        if project.contract_amount_with_tax and project.payment_received:
            project.remaining_amount = project.contract_amount_with_tax - project.payment_received
        elif project.contract_amount_with_tax:
            project.remaining_amount = project.contract_amount_with_tax
        else:
            project.remaining_amount = 0

        # 获取当前分配的开发者
        current_assignments = {a.user_id: a for a in project.assignments}
        new_dev_ids = set(form.assigned_developers.data)
        current_dev_ids = set(current_assignments.keys())
        
        # 删除不再分配的开发者
        to_remove = current_dev_ids - new_dev_ids
        for dev_id in to_remove:
            db.session.delete(current_assignments[dev_id])
        
        # 添加新分配的开发者
        to_add = new_dev_ids - current_dev_ids
        for dev_id in to_add:
            assignment = ProjectAssignment(project_id=project.id, user_id=dev_id)
            db.session.add(assignment)
        
        db.session.commit()
        flash("项目更新成功")
        return redirect(url_for("project_detail", project_id=project.id))
    return render_template("project_edit.html", form=form, project=project)

@app.route("/projects/<int:project_id>/assignment/<int:assignment_id>/rate", methods=["POST"])
@login_required
def update_hourly_rate(project_id, assignment_id):
    """更新开发者工时费用"""
    if not current_user.is_admin():
        return jsonify({"error": "权限不足"}), 403
    
    assignment = ProjectAssignment.query.get_or_404(assignment_id)
    if assignment.project_id != project_id:
        return jsonify({"error": "数据不匹配"}), 400
    
    hourly_rate = request.json.get('hourly_rate')
    if hourly_rate is not None:
        try:
            assignment.hourly_rate = float(hourly_rate) if hourly_rate != '' else None
            db.session.commit()
            return jsonify({"success": True, "message": "工时费用更新成功"})
        except ValueError:
            return jsonify({"error": "无效的费用格式"}), 400
    
    return jsonify({"error": "缺少费用数据"}), 400

@app.route("/projects/<int:project_id>/status", methods=["GET", "POST"])
@login_required
def update_project_status(project_id):
    """快速更新项目状态"""
    if not current_user.is_admin():
        flash("只有项目经理可以更新项目状态")
        return redirect(url_for("index"))
    
    project = Project.query.get_or_404(project_id)
    form = ProjectStatusForm()
    
    # 设置当前状态
    if request.method == 'GET':
        form.status.data = project.status
    
    if form.validate_on_submit():
        old_status = project.status
        project.status = form.status.data
        db.session.commit()
        flash(f"项目状态已从 '{old_status}' 更新为 '{project.status}'")
        return redirect(url_for("project_detail", project_id=project.id))
    
    return render_template("project_status_update.html", form=form, project=project)

@app.route("/users/create", methods=["GET", "POST"])
@login_required
def create_user():
    if not current_user.is_admin():
        flash("只有项目经理可以创建用户")
        return redirect(url_for("index"))

    form = UserForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash("用户名已存在")
            return render_template("user_create.html", form=form)
        
        new_user = User(username=form.username.data, role=form.role.data)
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()
        flash("用户创建成功")
        return redirect(url_for("index"))
    return render_template("user_create.html", form=form)

@app.route("/worklogs")
@login_required
def worklog_list():
    if current_user.is_admin():
        worklogs = WorkLog.query.all()
    elif current_user.is_developer():
        worklogs = WorkLog.query.filter_by(user_id=current_user.id).all()
    else:
        flash("权限不足")
        return redirect(url_for("index"))
    
    return render_template("worklog_list.html", worklogs=worklogs)

@app.route("/worklogs/create", methods=["GET", "POST"])
@login_required
def create_worklog():
    if not current_user.is_developer():
        flash("只有开发工程师可以记录工时")
        return redirect(url_for("index"))

    form = WorkLogForm()
    # 只显示分配给当前开发者的项目
    assigned_projects = db.session.query(Project).join(ProjectAssignment).filter(
        ProjectAssignment.user_id == current_user.id
    ).all()
    
    if not assigned_projects:
        flash("您还没有被分配到任何项目，请联系项目经理")
        return redirect(url_for("worklog_list"))
    
    form.project_id.choices = [(p.id, p.name) for p in assigned_projects]
    
    if form.validate_on_submit():
        worklog = WorkLog(
            user_id=current_user.id,
            project_id=form.project_id.data,
            date=form.date.data,
            hours=form.hours.data,
            description=form.description.data
        )
        db.session.add(worklog)
        db.session.commit()
        flash("工时记录成功")
        return redirect(url_for("worklog_list"))
    
    return render_template("worklog_create.html", form=form)

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 报销相关路由
@app.route("/expenses")
@login_required
def expense_list():
    """报销列表"""
    if current_user.is_admin():
        # 管理员可以看到所有报销
        expenses = Expense.query.order_by(Expense.submit_date.desc()).all()
    else:
        # 普通用户只能看到自己的报销
        expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.submit_date.desc()).all()
    
    return render_template("expense_list.html", expenses=expenses)

@app.route("/expense/create", methods=["GET", "POST"])
@login_required
def expense_create():
    """创建报销"""
    form = ExpenseForm()
    
    # 设置项目选择列表
    if current_user.is_admin():
        projects = Project.query.all()
    else:
        # 获取用户被分配的项目
        assigned_projects = Project.query.join(ProjectAssignment).filter(
            ProjectAssignment.user_id == current_user.id
        ).all()
        projects = assigned_projects
    
    form.project_id.choices = [('', '请选择项目（售前费用可不选）')] + [(p.id, p.name) for p in projects]
    
    # 如果从项目页面跳转过来，预选择项目
    if request.method == 'GET' and request.args.get('project_id'):
        try:
            preselected_project_id = int(request.args.get('project_id'))
            # 验证用户是否有权限选择这个项目
            if current_user.is_admin() or any(p.id == preselected_project_id for p in projects):
                form.project_id.data = preselected_project_id
        except (ValueError, TypeError):
            pass  # 忽略无效的project_id
    
    if form.validate_on_submit():
        # 处理文件上传
        receipt_filename = None
        if form.receipt_image.data:
            file = form.receipt_image.data
            if file and allowed_file(file.filename):
                import uuid
                import os
                from werkzeug.utils import secure_filename
                
                # 生成唯一文件名
                file_ext = os.path.splitext(secure_filename(file.filename))[1]
                receipt_filename = f"{uuid.uuid4().hex}{file_ext}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], receipt_filename)
                file.save(file_path)
        
        # 创建报销单
        expense = Expense(
            user_id=current_user.id,
            project_id=form.project_id.data if form.project_id.data else None,
            title=form.title.data,
            expense_type=form.expense_type.data,
            total_amount=form.amount.data,
            description=form.description.data
        )
        db.session.add(expense)
        db.session.flush()  # 获取expense.id
        
        # 创建费用明细
        expense_item = ExpenseItem(
            expense_id=expense.id,
            item_name=form.item_name.data,
            category=form.category.data,
            amount=form.amount.data,
            expense_date=form.expense_date.data,
            description=form.item_description.data,
            receipt_image=receipt_filename
        )
        db.session.add(expense_item)
        
        db.session.commit()
        flash("报销申请提交成功，等待审批")
        return redirect(url_for("expense_list"))
    
    return render_template("expense_create.html", form=form)

@app.route("/expense/<int:expense_id>")
@login_required
def expense_detail(expense_id):
    """报销详情"""
    expense = Expense.query.get_or_404(expense_id)
    
    # 权限检查：用户只能查看自己的报销，管理员可以查看所有
    if not current_user.is_admin() and expense.user_id != current_user.id:
        flash("您没有权限查看此报销")
        return redirect(url_for("expense_list"))
    
    return render_template("expense_detail.html", expense=expense)

@app.route("/expense/<int:expense_id>/approve", methods=["GET", "POST"])
@login_required
def expense_approve(expense_id):
    """审批报销"""
    if not current_user.is_admin():
        flash("您没有权限审批报销")
        return redirect(url_for("expense_list"))
    
    expense = Expense.query.get_or_404(expense_id)
    
    if expense.status != '待审批':
        flash("该报销已经审批过了")
        return redirect(url_for("expense_detail", expense_id=expense_id))
    
    form = ExpenseApprovalForm()
    
    # 设置同事选择列表（除了当前用户）
    all_users = User.query.filter(User.id != current_user.id).all()
    form.assign_to.choices = [('', '不分配给其他人')] + [(u.id, f"{u.username} ({u.role})") for u in all_users]
    
    if form.validate_on_submit():
        expense.status = form.status.data
        expense.approve_comment = form.approve_comment.data
        expense.approver_id = current_user.id
        expense.approve_date = datetime.utcnow()
        
        # 如果审批通过
        if form.status.data == '已批准':
            # 1. 自动将费用记录到对应项目中
            if expense.project_id:
                for item in expense.items:
                    project_record = ProjectExpenseRecord(
                        project_id=expense.project_id,
                        expense_id=expense.id,
                        category=item.category,
                        amount=item.amount,
                        description=f"报销项目：{expense.title} - {item.item_name}",
                        recorded_by=current_user.id
                    )
                    db.session.add(project_record)
            
            # 2. 如果选择了分配给同事，创建任务
            if form.assign_to.data:
                assigned_user = User.query.get(form.assign_to.data)
                task = Task(
                    title=f"处理报销：{expense.title}",
                    description=f"报销金额：¥{expense.total_amount}\n报销说明：{expense.description or '无'}\n审批意见：{form.approve_comment.data or '无特殊说明'}",
                    task_type='expense_process',
                    assigned_to=form.assign_to.data,
                    assigned_by=current_user.id,
                    expense_id=expense.id,
                    priority='普通'
                )
                db.session.add(task)
                flash(f"报销已批准，并已分配给 {assigned_user.username} 处理")
            else:
                flash("报销已批准")
        else:
            flash("报销已拒绝")
        
        db.session.commit()
        return redirect(url_for("expense_detail", expense_id=expense_id))
    
    return render_template("expense_approve.html", form=form, expense=expense)

@app.route("/expense/<int:expense_id>/edit", methods=["GET", "POST"])
@login_required
def expense_edit(expense_id):
    """编辑报销（只有待审批状态可以编辑）"""
    expense = Expense.query.get_or_404(expense_id)
    
    # 权限检查
    if expense.user_id != current_user.id:
        flash("您只能编辑自己的报销")
        return redirect(url_for("expense_list"))
    
    if expense.status != '待审批':
        flash("只有待审批的报销可以编辑")
        return redirect(url_for("expense_detail", expense_id=expense_id))
    
    form = ExpenseForm(obj=expense)
    
    # 设置项目选择列表
    if current_user.is_admin():
        projects = Project.query.all()
    else:
        assigned_projects = Project.query.join(ProjectAssignment).filter(
            ProjectAssignment.user_id == current_user.id
        ).all()
        projects = assigned_projects
    
    form.project_id.choices = [('', '请选择项目（售前费用可不选）')] + [(p.id, p.name) for p in projects]
    
    # 设置表单的默认值
    if not form.is_submitted():
        form.project_id.data = expense.project_id if expense.project_id else ''
    
    # 填充表单数据
    if expense.items:
        first_item = expense.items[0]
        if not form.is_submitted():
            form.item_name.data = first_item.item_name
            form.category.data = first_item.category
            form.amount.data = first_item.amount
            form.expense_date.data = first_item.expense_date
            form.item_description.data = first_item.description
    
    if form.validate_on_submit():
        # 更新报销单
        expense.title = form.title.data
        expense.expense_type = form.expense_type.data
        expense.project_id = form.project_id.data if form.project_id.data else None
        expense.total_amount = form.amount.data
        expense.description = form.description.data
        
        # 更新费用明细（简化处理，只更新第一条）
        if expense.items:
            first_item = expense.items[0]
            first_item.item_name = form.item_name.data
            first_item.category = form.category.data
            first_item.amount = form.amount.data
            first_item.expense_date = form.expense_date.data
            first_item.description = form.item_description.data
        
        db.session.commit()
        flash("报销修改成功")
        return redirect(url_for("expense_detail", expense_id=expense_id))
    
    return render_template("expense_edit.html", form=form, expense=expense)

@app.route("/expense/<int:expense_id>/delete", methods=["POST"])
@login_required
def expense_delete(expense_id):
    """删除报销（只有待审批状态可以删除）"""
    expense = Expense.query.get_or_404(expense_id)
    
    # 权限检查
    if expense.user_id != current_user.id and not current_user.is_admin():
        flash("您没有权限删除此报销")
        return redirect(url_for("expense_list"))
    
    if expense.status != '待审批':
        flash("只有待审批的报销可以删除")
        return redirect(url_for("expense_detail", expense_id=expense_id))
    
    db.session.delete(expense)
    db.session.commit()
    flash("报销已删除")
    return redirect(url_for("expense_list"))

# 任务管理路由
@app.route("/tasks")
@login_required
def task_list():
    """任务列表"""
    if current_user.is_admin():
        # 管理员可以看到所有任务
        tasks = Task.query.order_by(Task.created_at.desc()).all()
    else:
        # 普通用户只能看到分配给自己的任务
        tasks = Task.query.filter_by(assigned_to=current_user.id).order_by(Task.created_at.desc()).all()
    
    return render_template("task_list.html", tasks=tasks)

@app.route("/task/<int:task_id>")
@login_required
def task_detail(task_id):
    """任务详情"""
    task = Task.query.get_or_404(task_id)
    
    # 权限检查：用户只能查看分配给自己的任务，管理员可以查看所有
    if not current_user.is_admin() and task.assigned_to != current_user.id:
        flash("您没有权限查看此任务")
        return redirect(url_for("task_list"))
    
    return render_template("task_detail.html", task=task)

@app.route("/task/<int:task_id>/update", methods=["GET", "POST"])
@login_required
def task_update(task_id):
    """更新任务状态"""
    task = Task.query.get_or_404(task_id)
    
    # 权限检查：只有任务分配者可以更新状态
    if task.assigned_to != current_user.id and not current_user.is_admin():
        flash("您没有权限更新此任务")
        return redirect(url_for("task_list"))
    
    form = TaskUpdateForm()
    
    if form.validate_on_submit():
        task.status = form.status.data
        if form.status.data == '已完成':
            task.completed_at = datetime.utcnow()
        
        # 如果是报销处理任务且状态改为已完成，可以添加额外的处理逻辑
        if task.task_type == 'expense_process' and form.status.data == '已完成':
            # 可以在这里添加费用处理完成后的逻辑
            pass
        
        db.session.commit()
        flash("任务状态已更新")
        return redirect(url_for("task_detail", task_id=task_id))
    
    # 设置当前状态作为默认值
    form.status.data = task.status
    
    return render_template("task_update.html", form=form, task=task)

@app.route("/expenses/project-records")
@login_required
def project_expense_records():
    """项目费用记录"""
    if not current_user.is_admin():
        flash("您没有权限查看项目费用记录")
        return redirect(url_for("index"))
    
    records = ProjectExpenseRecord.query.join(Project).order_by(ProjectExpenseRecord.recorded_at.desc()).all()
    return render_template("project_expense_records.html", records=records)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5005, debug=True)

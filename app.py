from flask import Flask, jsonify, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime
import logging

# 设置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["SECRET_KEY"] = "yoursecret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///projects.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

from models import db, Project, User, WorkLog, ProjectAssignment
from forms import ProjectForm, LoginForm, UserForm, WorkLogForm, ProjectStatusForm

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
        return render_template("project_list.html", projects=projects)
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


if __name__ == "__main__":
    app.run(debug=True)

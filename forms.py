from flask_wtf import FlaskForm
from wtforms import StringField, DateField, DecimalField, SubmitField, PasswordField, SelectField, TextAreaField, FloatField, SelectMultipleField, BooleanField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from wtforms.widgets import CheckboxInput, ListWidget
from models import Project
from datetime import datetime

class MultiCheckboxField(SelectMultipleField):
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()

class ProjectForm(FlaskForm):
    name = StringField("项目名称", validators=[DataRequired()])
    manager = StringField("项目经理", validators=[DataRequired()])
    customer_name = StringField("客户名称", validators=[Optional()])
    project_type = SelectField("项目类型", choices=[
        ('', '请选择项目类型'),
        ('物流仿真', '物流仿真'),
        ('机器人仿真', '机器人仿真'),
        ('工艺规划', '工艺规划'),
        ('物流规划', '物流规划'),
        ('动画', '动画'),
        ('激光扫描', '激光扫描'),
        ('数字孪生', '数字孪生')
    ], validators=[Optional()])
    start_date = DateField("开始时间", format="%Y-%m-%d", validators=[Optional()])
    planned_end_date = DateField("预计结束时间", format="%Y-%m-%d", validators=[Optional()])
    contract_signing_date = DateField("合同签订日期", format="%Y-%m-%d", validators=[Optional()])
    estimated_hours = FloatField("预计开发工时(小时)", validators=[Optional()])
    contract_amount_with_tax = DecimalField("合同金额含税", validators=[Optional()])
    contract_amount_without_tax = DecimalField("合同金额不含税", validators=[Optional()])
    payment_method = SelectField("付款方式", choices=[
        ('', '请选择付款方式'),
        ('验收后全款', '验收后全款'),
        ('分阶段', '分阶段'),
        ('预付初版', '预付初版'),
        ('预付终版', '预付终版'),
        ('待填写', '待填写')
    ], validators=[Optional()])
    acceptance_date = DateField("验收日期", format="%Y-%m-%d", validators=[Optional()])
    settlement_date = DateField("结算日期", format="%Y-%m-%d", validators=[Optional()])
    invoice_date = DateField("发票日期", format="%Y-%m-%d", validators=[Optional()])
    payment_received = DecimalField("回款金额", validators=[Optional()])
    invoice_issued = BooleanField("发票是否开具")
    status = SelectField("项目状态", choices=[
        ('启动中', '启动中'),
        ('进行中', '进行中'),
        ('暂停', '暂停'),
        ('验收中', '验收中'),
        ('验收待回款', '验收待回款'),
        ('结算', '结算'),
        ('关闭', '关闭')
    ], validators=[DataRequired()])
    assigned_developers = MultiCheckboxField("责任工程师", coerce=int)
    submit = SubmitField("提交")

class ProjectStatusForm(FlaskForm):
    """专门用于更新项目状态的表单"""
    status = SelectField("项目状态", choices=[
        ('启动中', '启动中'),
        ('进行中', '进行中'),
        ('暂停', '暂停'),
        ('验收中', '验收中'),
        ('验收待回款', '验收待回款'),
        ('结算', '结算'),
        ('关闭', '关闭')
    ], validators=[DataRequired()])
    submit = SubmitField("更新状态")
    
class LoginForm(FlaskForm):
    username = StringField("用户名", validators=[DataRequired(), Length(min=3, max=20)])
    password = PasswordField("密码", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("登录")

class UserForm(FlaskForm):
    username = StringField("用户名", validators=[DataRequired(), Length(min=3, max=20)])
    password = PasswordField("密码", validators=[DataRequired(), Length(min=6)])
    role = SelectField("角色", choices=[('admin', '项目经理'), ('developer', '开发工程师')], validators=[DataRequired()])
    submit = SubmitField("创建用户")

class WorkLogForm(FlaskForm):
    project_id = SelectField("项目", coerce=int, validators=[DataRequired()])
    date = DateField("工作日期", validators=[DataRequired()], format="%Y-%m-%d")
    hours = FloatField("工作时长(小时)", validators=[DataRequired()])
    description = TextAreaField("工作描述")
    submit = SubmitField("提交")

class DeveloperAssignmentForm(FlaskForm):
    """开发者分配表单，包含工时费用"""
    developer_id = SelectField('开发者', coerce=int, validators=[DataRequired()])
    hourly_rate = DecimalField('工时费用（元/小时）', validators=[Optional(), NumberRange(min=0)], places=2)
    submit = SubmitField("保存")

class StagePaymentForm(FlaskForm):
    """阶段付款表单"""
    stage_name = StringField("阶段名称", validators=[DataRequired()])
    payment_amount = DecimalField("付款金额", validators=[DataRequired(), NumberRange(min=0)], places=2)
    payment_date = DateField("入款日期", format="%Y-%m-%d", validators=[Optional()])
    submit = SubmitField("保存")
from flask_wtf import FlaskForm
from wtforms import StringField, DateField, DecimalField, SubmitField, PasswordField, SelectField, TextAreaField, FloatField, SelectMultipleField
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
    start_date = DateField("开始时间", format="%Y-%m-%d", validators=[Optional()])
    planned_end_date = DateField("预计结束时间", format="%Y-%m-%d", validators=[Optional()])
    estimated_completion_date = DateField("预计完成时间", format="%Y-%m-%d", validators=[Optional()])
    estimated_hours = FloatField("预计开发工时(小时)", validators=[Optional()])
    contract_amount = DecimalField("合同金额", validators=[Optional()])
    status = SelectField("项目状态", choices=[
        ('立项', '立项'),
        ('开发', '开发'),
        ('结项', '结项'),
        ('跟进收款', '跟进收款'),
        ('维护', '维护')
    ], validators=[DataRequired()])
    assigned_developers = MultiCheckboxField("责任工程师", coerce=int)
    submit = SubmitField("提交")

class ProjectStatusForm(FlaskForm):
    """专门用于更新项目状态的表单"""
    status = SelectField("项目状态", choices=[
        ('立项', '立项'),
        ('开发', '开发'),
        ('结项', '结项'),
        ('跟进收款', '跟进收款'),
        ('维护', '维护')
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
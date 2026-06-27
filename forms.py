from flask_wtf import FlaskForm
from wtforms import StringField, DateField, DecimalField, SubmitField, PasswordField, SelectField, TextAreaField, FloatField, SelectMultipleField, BooleanField, FieldList, FormField, FileField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from wtforms.widgets import CheckboxInput, ListWidget
from models import Project
from datetime import datetime

class MultiCheckboxField(SelectMultipleField):
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()

class ProjectForm(FlaskForm):
    name = StringField("项目名称", validators=[DataRequired()])
    manager = StringField("项目经理", validators=[Optional()])  # 保留但可选，为了兼容旧数据
    customer_name = StringField("客户名称", validators=[Optional()])
    final_customer = StringField("最终客户", validators=[Optional()])
    project_type = SelectField("项目类型", choices=[
        ('', '请选择项目类型'),
        ('物流仿真', '物流仿真'),
        ('机器人仿真', '机器人仿真'),
        ('工艺规划', '工艺规划'),
        ('物流规划', '物流规划'),
        ('动画', '动画'),
        ('激光扫描', '激光扫描'),
        ('数字孪生', '数字孪生'),
        ('虚拟调试', '虚拟调试')
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
        ('分阶段付款（3/5/2）', '分阶段付款（3/5/2）'),
        ('分阶段付款（3/6/1）', '分阶段付款（3/6/1）'),
        ('分阶段付款（3/4/3）', '分阶段付款（3/4/3）'),
        ('分阶段付款（5/5）', '分阶段付款（5/5）'),
        ('分阶段付款（3/7）', '分阶段付款（3/7）'),
        ('分阶段付款（4/6）', '分阶段付款（4/6）'),
        ('多阶段', '多阶段'),
        ('按小时付款', '按小时付款')
    ], validators=[Optional()])
    acceptance_date = DateField("验收日期", format="%Y-%m-%d", validators=[Optional()])
    settlement_date = DateField("结算日期", format="%Y-%m-%d", validators=[Optional()])
    invoice_date = DateField("开票日期", format="%Y-%m-%d", validators=[Optional()])
    invoice_amount = DecimalField("发票金额(含税)", validators=[Optional()])
    invoice_file = FileField("发票文件", validators=[Optional()])
    invoice_notes = TextAreaField("开票备注", validators=[Optional()])
    payment_received = DecimalField("回款金额(含税)", validators=[Optional()])
    invoice_stage = SelectField("当前发票开具阶段", choices=[
        ('', '请选择当前发票开具阶段'),
        ('未开', '未开'),
        ('预付款', '预付款'),
        ('第二阶段', '第二阶段'),
        ('第三阶段', '第三阶段'),
        ('第四阶段', '第四阶段'),
        ('尾款', '尾款')
    ], validators=[Optional()])
    status = SelectField("项目状态", choices=[
        ('启动中', '启动中'),
        ('进行中', '进行中'),
        ('暂停', '暂停'),
        ('验收中', '验收中'),
        ('验收待回款', '验收待回款'),
        ('已结算', '已结算')
    ], validators=[DataRequired()])
    
    outsourcing_cost = FloatField("外包费用(含税)", default=0)
    outsourcing_cost_without_tax = FloatField("外包费用(不含税)", default=0)
    supplier_name = StringField("供应商名称", validators=[Optional()])
    supplier_invoice_issued = BooleanField("供应商发票是否开具")
    supplier_pending_amount = FloatField("供应商待付金额(不含税)", default=0)
    outsourcing_cost_notes = TextAreaField("外包费用备注")
    indirect_cost = FloatField("间接成本", default=0)
    indirect_cost_notes = TextAreaField("间接成本备注")
    stage_payment_notes = TextAreaField("阶段付款备注")
    payment_amount_notes = TextAreaField("回款金额备注")
    invoice_amount_issued = DecimalField("已开发票金额", validators=[Optional()])
    current_invoice_amount = DecimalField("当前发票金额", validators=[Optional()])
    accounts_receivable = DecimalField("应收账款", validators=[Optional()])
    area = DecimalField("面积", validators=[Optional()])
    unit_price = DecimalField("单价", validators=[Optional()])
    po_number = StringField("PO号", validators=[Optional()])
    contract_file = FileField("合同文件", validators=[Optional()])

    assigned_developers = MultiCheckboxField("责任工程师", coerce=int)
    assigned_managers = MultiCheckboxField("项目经理", coerce=int)
    submit = SubmitField("提交")

class ProjectStatusForm(FlaskForm):
    """专门用于更新项目状态的表单"""
    status = SelectField("项目状态", choices=[
        ('启动中', '启动中'),
        ('进行中', '进行中'),
        ('暂停', '暂停'),
        ('验收中', '验收中'),
        ('验收待回款', '验收待回款'),
        ('结算', '结算')
    ], validators=[DataRequired()])
    submit = SubmitField("更新状态")
    
class LoginForm(FlaskForm):
    username = StringField("用户名", validators=[DataRequired(), Length(min=3, max=20)])
    password = PasswordField("密码", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("登录")

class UserForm(FlaskForm):
    username = StringField("用户名", validators=[DataRequired(), Length(min=3, max=20)])
    password = PasswordField("密码", validators=[DataRequired(), Length(min=6)])
    role = SelectField("角色", choices=[
        ('admin', '管理员'),
        ('finance', '财务'),
        ('developer', '开发工程师'),
        ('project_manager', '项目经理')
    ], validators=[DataRequired()])
    default_hourly_rate = DecimalField("默认工时费用（元/小时）", validators=[Optional(), NumberRange(min=0)], places=2)
    submit = SubmitField("创建用户")

class UserEditForm(FlaskForm):
    """编辑用户信息表单"""
    username = StringField("用户名", validators=[DataRequired(), Length(min=3, max=20)])
    password = PasswordField("新密码（留空则不修改）", validators=[Optional(), Length(min=6)])
    confirm_password = PasswordField("确认新密码", validators=[Optional(), Length(min=6)])
    default_hourly_rate = DecimalField("默认工时费用（元/小时）", validators=[Optional(), NumberRange(min=0)], places=2)
    submit = SubmitField("保存修改")

class ChangePasswordForm(FlaskForm):
    """修改密码表单"""
    old_password = PasswordField("当前密码", validators=[DataRequired(), Length(min=6)])
    new_password = PasswordField("新密码", validators=[DataRequired(), Length(min=6, message="密码至少需要6个字符")])
    confirm_password = PasswordField("确认新密码", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("修改密码")

class WorkLogForm(FlaskForm):
    project_id = SelectField("项目", coerce=int, validators=[DataRequired()])
    date = DateField("工作日期", validators=[DataRequired()], format="%Y-%m-%d")
    hours = FloatField("工作时长(小时)", validators=[DataRequired(), NumberRange(min=0.5, message="工作时长最小为0.5小时")])
    description = TextAreaField("工作描述")
    submit = SubmitField("提交")
    
    def validate_hours(self, field):
        """验证工时是否为0.5的倍数"""
        if field.data and (field.data * 2) % 1 != 0:
            raise ValidationError('工作时长必须是0.5小时的倍数（如：0.5, 1.0, 1.5, 2.0等）')

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

class ExpenseItemForm(FlaskForm):
    """费用明细表单"""
    item_name = StringField("费用名称", validators=[DataRequired()])
    category = SelectField("费用类别", choices=[
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
    ], validators=[DataRequired()])
    amount = DecimalField("金额", validators=[DataRequired(), NumberRange(min=0)], places=2)
    expense_date = DateField("费用发生日期", validators=[DataRequired()], format="%Y-%m-%d")
    description = TextAreaField("费用说明")

class ExpenseForm(FlaskForm):
    """报销表单"""
    title = StringField("报销标题", validators=[DataRequired()])
    expense_type = SelectField("费用类型", choices=[
        ('项目费用', '项目费用'),
        ('售前费用', '售前费用'),
        ('其他费用', '其他费用')
    ], validators=[DataRequired()])
    project_id = SelectField("关联项目", coerce=lambda x: int(x) if x and x != '' else None, validators=[DataRequired(message='请选择一个项目')])
    approver_id = SelectField("审批人", coerce=lambda x: int(x) if x and x != '' else None, validators=[Optional()])
    description = TextAreaField("报销说明")
    
    # 费用明细
    expense_date = DateField("费用日期", validators=[DataRequired()], format="%Y-%m-%d")
    start_date = DateField("费用起始日期", validators=[Optional()], format="%Y-%m-%d")
    end_date = DateField("费用结束日期", validators=[Optional()], format="%Y-%m-%d")
    category = SelectField("费用类别", choices=[
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
    ], validators=[DataRequired()])
    amount = DecimalField("金额", validators=[DataRequired(), NumberRange(min=0)], places=2)
    item_note = TextAreaField("备注")
    receipt_image = FileField("上传明细表/发票/凭证")
    
    submit = SubmitField("提交报销")

class ExpenseApprovalForm(FlaskForm):
    """报销审批表单"""
    approval_action = SelectField("审批操作", choices=[
        ('approve', '同意'),
        ('waiting_refund', '等待退款'),
        ('refund_complete', '退款完成'),
        ('reject', '拒绝')
    ], validators=[DataRequired()])
    assign_to = SelectField("下一个处理人", coerce=lambda x: int(x) if x and x != '' else None, validators=[Optional()])
    approve_comment = TextAreaField("审批意见")
    submit = SubmitField("提交审批")

class TaskForm(FlaskForm):
    """任务表单"""
    title = StringField("任务标题", validators=[DataRequired()])
    description = TextAreaField("任务描述")
    assigned_to = SelectField("审批人", coerce=int, validators=[DataRequired()])
    priority = SelectField("优先级", choices=[
        ('紧急', '紧急'),
        ('高', '高'),
        ('普通', '普通'),
        ('低', '低')
    ], default='普通', validators=[DataRequired()])
    due_date = DateField("截止日期", format="%Y-%m-%d", validators=[Optional()])
    submit = SubmitField("创建任务")

class TaskUpdateForm(FlaskForm):
    """任务更新表单"""
    approval_action = SelectField("处理操作", choices=[
        ('agree', '同意'),
        ('waiting_refund', '等待退款'),
        ('refund_complete', '退款完成'),
        ('complete', '已完成'),
        ('reject', '拒绝')
    ], validators=[DataRequired()])
    assign_to = SelectField("下一个处理人", coerce=lambda x: int(x) if x and x != '' else None, validators=[Optional()])
    task_comment = TextAreaField("处理备注")
    submit = SubmitField("更新任务")

class CustomFieldForm(FlaskForm):
    field_name = StringField('字段名称', validators=[DataRequired(), Length(min=1, max=100)])
    field_label = StringField('字段标签', validators=[DataRequired(), Length(min=1, max=100)])
    field_type = SelectField('字段类型', choices=[
        ('text', '文本'),
        ('number', '数字'),
        ('date', '日期'),
        ('select', '下拉选择'),
        ('checkbox', '复选框')
    ], validators=[DataRequired()])
    options = TextAreaField('选项（每行一个，仅用于下拉选择）')
    is_required = BooleanField('必填字段')
    submit = SubmitField('保存字段')
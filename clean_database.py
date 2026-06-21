"""
数据库清理脚本
清理具体的项目和人员数据，保留管理员admin和developer开发者作为测试用户
保留相关表结构
"""
from app import app, db
from models import (
    User, Project, ProjectAssignment, ProjectManagerAssignment,
    WorkLog, Task, Expense, OperationLog, CustomField, 
    ProjectCustomFieldValue, StagePayment, ProjectExpenseRecord, ExpenseItem
)

def clean_database():
    """清理数据库"""
    with app.app_context():
        print("=" * 60)
        print("开始清理数据库...")
        print("=" * 60)
        
        # 1. 删除所有项目相关数据
        print("\n1. 删除项目相关数据...")
        
        # 删除工作日志
        worklog_count = WorkLog.query.delete()
        print(f"   - 删除工作日志: {worklog_count} 条")
        
        # 删除任务
        task_count = Task.query.delete()
        print(f"   - 删除任务: {task_count} 条")
        
        # 删除报销记录
        expense_count = Expense.query.delete()
        print(f"   - 删除报销记录: {expense_count} 条")
        
        # 删除报销明细项
        expense_item_count = ExpenseItem.query.delete()
        print(f"   - 删除报销明细项: {expense_item_count} 条")
        
        # 删除阶段付款记录
        try:
            stage_payment_count = StagePayment.query.delete()
            print(f"   - 删除阶段付款记录: {stage_payment_count} 条")
        except Exception as e:
            stage_payment_count = 0
            print(f"   - 删除阶段付款记录: 跳过 (表结构不匹配或不存在)")
        
        # 删除项目费用记录
        try:
            project_expense_count = ProjectExpenseRecord.query.delete()
            print(f"   - 删除项目费用记录: {project_expense_count} 条")
        except Exception as e:
            project_expense_count = 0
            print(f"   - 删除项目费用记录: 跳过 (表结构不匹配或不存在)")
        
        # 删除项目自定义字段值
        custom_value_count = ProjectCustomFieldValue.query.delete()
        print(f"   - 删除项目自定义字段值: {custom_value_count} 条")
        
        # 删除项目分配关系
        assignment_count = ProjectAssignment.query.delete()
        print(f"   - 删除项目-开发者分配关系: {assignment_count} 条")
        
        # 删除项目经理分配关系
        manager_assignment_count = ProjectManagerAssignment.query.delete()
        print(f"   - 删除项目-项目经理分配关系: {manager_assignment_count} 条")
        
        # 删除所有项目
        project_count = Project.query.delete()
        print(f"   - 删除项目: {project_count} 条")
        
        # 2. 先清理操作日志（避免外键约束问题）
        print("\n2. 清理操作日志...")
        log_count = OperationLog.query.delete()
        print(f"   - 删除操作日志: {log_count} 条")
        
        # 提交删除操作日志的更改
        db.session.commit()
        print("   ✓ 操作日志已清理")
        
        # 3. 清理用户数据，只保留admin和developer
        print("\n3. 清理用户数据...")
        
        # 获取要保留的用户
        admin_user = User.query.filter_by(username='admin').first()
        developer_user = User.query.filter_by(username='developer').first()
        
        keep_user_ids = []
        if admin_user:
            keep_user_ids.append(admin_user.id)
            print(f"   ✓ 保留用户: admin (ID: {admin_user.id}, 角色: {admin_user.role})")
        else:
            print("   ⚠ 警告: 未找到admin用户")
            
        if developer_user:
            keep_user_ids.append(developer_user.id)
            print(f"   ✓ 保留用户: developer (ID: {developer_user.id}, 角色: {developer_user.role})")
        else:
            print("   ⚠ 警告: 未找到developer用户")
        
        # 删除其他用户
        other_users = User.query.filter(~User.id.in_(keep_user_ids)).all()
        deleted_user_count = 0
        for user in other_users:
            print(f"   - 删除用户: {user.username} (ID: {user.id}, 角色: {user.role})")
            db.session.delete(user)
            deleted_user_count += 1
        
        print(f"   总共删除用户: {deleted_user_count} 个")
        
        # 4. 保留自定义字段定义（不删除CustomField表）
        print("\n4. 保留自定义字段定义...")
        custom_field_count = CustomField.query.count()
        print(f"   ✓ 保留自定义字段: {custom_field_count} 个")
        
        # 提交更改
        try:
            db.session.commit()
            print("\n" + "=" * 60)
            print("✓ 数据库清理完成！")
            print("=" * 60)
            print("\n保留的数据：")
            print("  - 用户: admin, developer")
            print(f"  - 自定义字段定义: {custom_field_count} 个")
            print("  - 所有数据表结构")
            print("\n清理的数据：")
            print(f"  - 项目: {project_count} 个")
            print(f"  - 工作日志: {worklog_count} 条")
            print(f"  - 任务: {task_count} 条")
            print(f"  - 报销记录: {expense_count} 条")
            print(f"  - 报销明细项: {expense_item_count} 条")
            print(f"  - 阶段付款记录: {stage_payment_count} 条")
            print(f"  - 项目费用记录: {project_expense_count} 条")
            print(f"  - 用户: {deleted_user_count} 个")
            print(f"  - 操作日志: {log_count} 条")
            print("=" * 60)
        except Exception as e:
            db.session.rollback()
            print("\n" + "=" * 60)
            print(f"✗ 错误: 数据库清理失败!")
            print(f"错误信息: {str(e)}")
            print("=" * 60)
            return False
        
        return True

def create_test_users_if_needed():
    """如果admin或developer用户不存在，则创建它们"""
    with app.app_context():
        print("\n检查并创建测试用户...")
        
        # 检查admin用户
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            print("✓ 创建admin用户 (密码: admin123)")
        else:
            print("✓ admin用户已存在")
        
        # 检查developer用户
        developer = User.query.filter_by(username='developer').first()
        if not developer:
            developer = User(username='developer', role='developer')
            developer.set_password('dev123')
            db.session.add(developer)
            print("✓ 创建developer用户 (密码: dev123)")
        else:
            print("✓ developer用户已存在")
        
        try:
            db.session.commit()
            print("测试用户准备完成！\n")
        except Exception as e:
            db.session.rollback()
            print(f"创建测试用户失败: {str(e)}\n")

def show_database_status():
    """显示当前数据库状态"""
    with app.app_context():
        print("\n" + "=" * 60)
        print("当前数据库状态:")
        print("=" * 60)
        print(f"用户总数: {User.query.count()}")
        print(f"项目总数: {Project.query.count()}")
        print(f"工作日志: {WorkLog.query.count()}")
        print(f"任务: {Task.query.count()}")
        print(f"报销记录: {Expense.query.count()}")
        print(f"报销明细项: {ExpenseItem.query.count()}")
        try:
            print(f"阶段付款记录: {StagePayment.query.count()}")
        except:
            print(f"阶段付款记录: N/A (表结构不匹配)")
        try:
            print(f"项目费用记录: {ProjectExpenseRecord.query.count()}")
        except:
            print(f"项目费用记录: N/A (表结构不匹配)")
        print(f"自定义字段: {CustomField.query.count()}")
        print(f"操作日志: {OperationLog.query.count()}")
        print("=" * 60)
        
        # 显示用户列表
        users = User.query.all()
        if users:
            print("\n现有用户列表:")
            for user in users:
                print(f"  - {user.username} (角色: {user.role})")

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("数据库清理工具")
    print("=" * 60)
    
    # 显示清理前状态
    show_database_status()
    
    # 确认清理
    print("\n" + "!" * 60)
    print("警告: 此操作将删除除admin和developer外的所有数据!")
    print("!" * 60)
    confirm = input("\n确认清理数据库? (输入 'YES' 确认): ")
    
    if confirm == 'YES':
        # 先确保测试用户存在
        create_test_users_if_needed()
        
        # 执行清理
        if clean_database():
            # 显示清理后状态
            show_database_status()
            print("\n数据库已清理完成，可以开始使用测试账户进行测试。")
            print("\n测试账户:")
            print("  管理员 - 用户名: admin, 密码: admin123")
            print("  开发者 - 用户名: developer, 密码: dev123")
    else:
        print("\n已取消清理操作。")

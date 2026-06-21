"""
数据库清理脚本 - 仅保留admin用户
清理所有项目和非admin用户数据，保留管理员admin及其默认密码
保留相关表结构
"""
import sys
import os

# 添加父目录到路径，以便导入app和models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import (
    User, Project, ProjectAssignment, ProjectManagerAssignment,
    WorkLog, Task, Expense, OperationLog, CustomField, 
    ProjectCustomFieldValue, StagePayment, ProjectExpenseRecord, ExpenseItem
)

def clean_database_admin_only():
    """清理数据库，仅保留admin用户"""
    with app.app_context():
        print("=" * 60)
        print("开始清理数据库（仅保留admin用户）...")
        print("=" * 60)
        
        # 1. 删除所有项目相关数据
        print("\n1. 删除项目相关数据...")
        
        # 删除工作日志
        worklog_count = WorkLog.query.delete()
        print(f"   - 删除工作日志: {worklog_count} 条")
        
        # 删除任务
        task_count = Task.query.delete()
        print(f"   - 删除任务: {task_count} 条")
        
        # 删除报销明细项（必须先删除，有外键约束）
        expense_item_count = ExpenseItem.query.delete()
        print(f"   - 删除报销明细项: {expense_item_count} 条")
        
        # 删除报销记录
        expense_count = Expense.query.delete()
        print(f"   - 删除报销记录: {expense_count} 条")
        
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
        
        # 3. 清理用户数据，只保留admin
        print("\n3. 清理用户数据...")
        
        # 获取admin用户
        admin_user = User.query.filter_by(username='admin').first()
        
        if admin_user:
            print(f"   ✓ 保留用户: admin (ID: {admin_user.id}, 角色: {admin_user.role})")
            # 确保admin用户使用默认密码
            admin_user.set_password('admin123')
            print(f"   ✓ 已重置admin密码为: admin123")
            db.session.add(admin_user)
        else:
            print("   ⚠ 警告: 未找到admin用户，将创建一个新的admin用户")
            admin_user = User(username='admin', role='admin')
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            print(f"   ✓ 已创建admin用户，密码: admin123")
        
        # 删除除admin外的所有其他用户
        other_users = User.query.filter(User.username != 'admin').all()
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
            print("  - 用户: admin")
            print("  - admin密码: admin123")
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

def show_database_status():
    """显示当前数据库状态"""
    with app.app_context():
        print("\n" + "=" * 60)
        print("当前数据库状态:")
        print("=" * 60)
        users = User.query.all()
        print(f"用户总数: {len(users)}")
        if users:
            for user in users:
                print(f"  - {user.username} (角色: {user.role})")
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

if __name__ == '__main__':
    import sys
    
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + "  数据库清理脚本 - 仅保留admin用户".center(58) + "║")
    print("╚" + "═" * 58 + "╝")
    
    # 显示清理前的状态
    print("\n清理前的数据库状态：")
    show_database_status()
    
    # 提示用户确认
    print("\n⚠️  注意：此操作将删除以下数据：")
    print("   - 所有项目和项目相关数据")
    print("   - 所有用户（除admin外）")
    print("   - 所有工作日志、任务、报销记录")
    print("   - 所有操作日志")
    print("\n✓ 保留:")
    print("   - admin用户（密码重置为: admin123）")
    print("   - 数据库表结构")
    print("   - 自定义字段定义")
    
    confirm = input("\n确认执行清理？(yes/no): ")
    
    if confirm.lower() in ['yes', 'y', '是']:
        # 执行清理
        success = clean_database_admin_only()
        
        if success:
            # 显示清理后的状态
            print("\n清理后的数据库状态：")
            show_database_status()
            print("\n✓ 数据库清理成功！")
            sys.exit(0)
        else:
            print("\n✗ 数据库清理失败！")
            sys.exit(1)
    else:
        print("\n已取消操作")
        sys.exit(0)

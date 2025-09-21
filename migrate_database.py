#!/usr/bin/env python3
"""
数据库迁移脚本 - 为项目添加新字段
运行此脚本来更新现有数据库，而不丢失数据
"""

import sqlite3
from datetime import datetime

def migrate_database():
    """执行数据库迁移"""
    
    # 连接到数据库
    conn = sqlite3.connect('instance/projects.db')
    cursor = conn.cursor()
    
    print("开始数据库迁移...")
    
    try:
        # 1. 检查是否已经存在新字段
        cursor.execute("PRAGMA table_info(projects)")
        columns = [column[1] for column in cursor.fetchall()]
        
        new_columns = [
            ('payment_method', 'VARCHAR(50)'),
            ('acceptance_date', 'DATE'),
            ('invoice_issued', 'BOOLEAN DEFAULT 0'),
            ('contract_amount_with_tax', 'DECIMAL(14, 2)'),
            ('contract_amount_without_tax', 'DECIMAL(14, 2)'),
            ('payment_received', 'DECIMAL(14, 2)'),
            ('remaining_amount', 'DECIMAL(14, 2)'),
            ('project_type', 'VARCHAR(50)'),
            ('customer_name', 'VARCHAR(200)')
        ]
        
        # 2. 添加缺失的列
        for column_name, column_type in new_columns:
            if column_name not in columns:
                print(f"添加字段: {column_name}")
                cursor.execute(f"ALTER TABLE projects ADD COLUMN {column_name} {column_type}")
        
        # 3. 更新状态字段的值从旧的枚举到新的枚举
        print("更新项目状态...")
        status_mapping = {
            '立项': '启动中',
            '开发': '进行中',
            '结项': '验收中',
            '跟进收款': '验收待回款',
            '维护': '关闭'
        }
        
        for old_status, new_status in status_mapping.items():
            cursor.execute("UPDATE projects SET status = ? WHERE status = ?", (new_status, old_status))
            updated_rows = cursor.rowcount
            if updated_rows > 0:
                print(f"更新了 {updated_rows} 个项目的状态从 '{old_status}' 到 '{new_status}'")
        
        # 4. 迁移旧的 contract_amount 到新的 contract_amount_with_tax
        print("迁移合同金额字段...")
        cursor.execute("""
            UPDATE projects 
            SET contract_amount_with_tax = contract_amount 
            WHERE contract_amount IS NOT NULL 
            AND contract_amount_with_tax IS NULL
        """)
        migrated_amounts = cursor.rowcount
        if migrated_amounts > 0:
            print(f"迁移了 {migrated_amounts} 个项目的合同金额")
        
        # 5. 计算剩余金额
        print("计算剩余金额...")
        cursor.execute("""
            UPDATE projects 
            SET remaining_amount = COALESCE(contract_amount_with_tax, 0) - COALESCE(payment_received, 0)
        """)
        
        # 6. 设置默认的发票状态
        cursor.execute("UPDATE projects SET invoice_issued = 0 WHERE invoice_issued IS NULL")
        
        # 提交更改
        conn.commit()
        print("数据库迁移成功完成！")
        
        # 显示迁移后的统计信息
        cursor.execute("SELECT COUNT(*) FROM projects")
        total_projects = cursor.fetchone()[0]
        
        cursor.execute("SELECT status, COUNT(*) FROM projects GROUP BY status")
        status_counts = cursor.fetchall()
        
        print(f"\n迁移完成统计:")
        print(f"总项目数: {total_projects}")
        print("项目状态分布:")
        for status, count in status_counts:
            print(f"  {status}: {count}")
        
    except Exception as e:
        print(f"迁移过程中出错: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def backup_database():
    """备份当前数据库"""
    import shutil
    from pathlib import Path
    
    db_path = Path('instance/projects.db')
    if db_path.exists():
        backup_path = Path(f'instance/projects_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
        shutil.copy2(db_path, backup_path)
        print(f"数据库已备份到: {backup_path}")
        return backup_path
    else:
        print("没有找到现有数据库文件")
        return None

if __name__ == "__main__":
    print("项目管理系统数据库迁移工具")
    print("=" * 40)
    
    # 询问是否要备份
    response = input("是否要先备份现有数据库？(y/n): ").lower()
    if response in ['y', 'yes']:
        backup_database()
    
    # 执行迁移
    response = input("确认执行数据库迁移？(y/n): ").lower()
    if response in ['y', 'yes']:
        migrate_database()
    else:
        print("迁移已取消")
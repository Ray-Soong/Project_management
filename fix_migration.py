#!/usr/bin/env python3
import sqlite3
import os

# 确保实例目录存在
if not os.path.exists('instance'):
    os.makedirs('instance')

# 连接到数据库
db_path = 'instance/projects.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("开始数据库迁移...")

try:
    # 检查并添加缺少的列
    missing_columns = [
        ('contract_signing_date', 'DATE'),
        ('settlement_date', 'DATE'), 
        ('invoice_date', 'DATE')
    ]
    
    # 获取现有列
    cursor.execute('PRAGMA table_info(projects)')
    existing_columns = [col[1] for col in cursor.fetchall()]
    
    for column_name, column_type in missing_columns:
        if column_name not in existing_columns:
            print(f"添加列: {column_name}")
            cursor.execute(f'ALTER TABLE projects ADD COLUMN {column_name} {column_type}')
        else:
            print(f"列已存在: {column_name}")
    
    # 创建 stage_payments 表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stage_payments'")
    if not cursor.fetchone():
        print("创建 stage_payments 表...")
        cursor.execute('''
            CREATE TABLE stage_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                amount DECIMAL(14, 2) NOT NULL,
                payment_date DATE,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
            )
        ''')
        print("stage_payments 表创建成功")
    else:
        print("stage_payments 表已存在")
    
    # 提交更改
    conn.commit()
    print("数据库迁移完成!")
    
except Exception as e:
    print(f"迁移过程中发生错误: {e}")
    conn.rollback()
    
finally:
    conn.close()
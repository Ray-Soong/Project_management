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

print("当前 projects 表的列结构:")
cursor.execute('PRAGMA table_info(projects)')
columns = cursor.fetchall()
for col in columns:
    print(f"  {col[1]} - {col[2]} {'(NOT NULL)' if col[3] else ''} {'(PRIMARY KEY)' if col[5] else ''}")

print("\n检查是否缺少的列:")
required_columns = [
    'contract_signing_date',
    'settlement_date', 
    'invoice_date'
]

existing_columns = [col[1] for col in columns]
missing_columns = [col for col in required_columns if col not in existing_columns]

if missing_columns:
    print(f"缺少列: {missing_columns}")
else:
    print("所有必需的列都存在")

# 检查 stage_payments 表是否存在
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stage_payments'")
stage_payments_exists = cursor.fetchone()
print(f"\nstage_payments 表存在: {bool(stage_payments_exists)}")

conn.close()
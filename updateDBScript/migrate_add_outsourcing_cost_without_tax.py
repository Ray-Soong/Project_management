"""
Add missing outsourcing_cost_without_tax column to projects table
"""
import sqlite3
import os

# Use absolute path
db_path = os.path.join(os.path.dirname(__file__), 'instance', 'project_mgmt.db')

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

print(f"Connecting to database at: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # 检查列是否已存在
    cursor.execute("PRAGMA table_info(projects)")
    columns = {col[1] for col in cursor.fetchall()}
    
    if 'outsourcing_cost_without_tax' not in columns:
        print("Adding outsourcing_cost_without_tax column...")
        cursor.execute("""
            ALTER TABLE projects
            ADD COLUMN outsourcing_cost_without_tax NUMERIC(10, 2) DEFAULT 0
        """)
        conn.commit()
        print("✓ Column added successfully")
    else:
        print("✓ Column already exists")
    
    # 验证列已被添加
    cursor.execute("PRAGMA table_info(projects)")
    columns = {col[1] for col in cursor.fetchall()}
    
    if 'outsourcing_cost_without_tax' in columns:
        print("✓ Verification successful: outsourcing_cost_without_tax column exists")
    else:
        print("✗ Verification failed: column not found")
        
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()
finally:
    conn.close()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证invoice_files表结构
"""

import sqlite3
import os

DB_FILE = "instance/projects.db"

def verify_table_structure():
    """验证表结构"""
    print("=" * 70)
    print("Invoice Files 表结构验证".center(70))
    print("=" * 70)
    print()
    
    if not os.path.exists(DB_FILE):
        print(f"✗ 数据库文件不存在: {DB_FILE}")
        return False
    
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # 获取invoice_files表的列信息
        cursor.execute("PRAGMA table_info(invoice_files)")
        columns = cursor.fetchall()
        
        print("Invoice Files 表列结构:")
        print("-" * 70)
        for col in columns:
            col_id, col_name, col_type, not_null, default, pk = col
            nullable = "NOT NULL" if not_null else "NULL"
            default_str = f"DEFAULT {default}" if default else ""
            pk_str = "PRIMARY KEY" if pk else ""
            print(f"  {col_name:20} {col_type:15} {nullable:10} {default_str} {pk_str}")
        
        print()
        print(f"总列数: {len(columns)}")
        print()
        
        # 检查必要的列
        required_columns = ['id', 'project_id', 'file_path', 'file_name', 'file_type', 
                          'file_size', 'upload_date', 'uploaded_by', 'description', 'is_deleted']
        column_names = [col[1] for col in columns]
        
        missing = [col for col in required_columns if col not in column_names]
        
        if not missing:
            print("✓ 所有必要的列都已存在")
        else:
            print(f"✗ 缺失列: {', '.join(missing)}")
        
        # 检查数据
        cursor.execute("SELECT COUNT(*) FROM invoice_files")
        record_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM invoice_files WHERE file_name IS NULL OR file_name = ''")
        null_count = cursor.fetchone()[0]
        
        print()
        print(f"数据统计:")
        print(f"  总记录数: {record_count}")
        print(f"  file_name为空: {null_count}")
        
        conn.close()
        
        print()
        print("=" * 70)
        print("✓ 验证完成".center(70))
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"✗ 验证失败: {e}")
        return False

if __name__ == "__main__":
    verify_table_structure()

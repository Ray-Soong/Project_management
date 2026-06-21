#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向invoice_files表添加缺失的file_name列
版本: v1.0.0
日期: 2026-06-13

功能：
1. 检查invoice_files表是否存在file_name列
2. 如果不存在，添加file_name列
3. 备份数据库
4. 验证添加结果
"""

import sqlite3
import os
import sys
import shutil
from datetime import datetime

# 添加上级目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_FILE = "instance/projects.db"
BACKUP_DIR = "instance/backups"

def print_header():
    """打印脚本头部信息"""
    print("=" * 70)
    print("Invoice Files 表迁移脚本".center(70))
    print("=" * 70)
    print()

def backup_database():
    """备份数据库"""
    print("[1/4] 备份数据库...")
    
    try:
        if not os.path.exists(DB_FILE):
            print(f"  ✗ 数据库文件不存在: {DB_FILE}")
            return False
        
        # 创建备份目录
        os.makedirs(BACKUP_DIR, exist_ok=True)
        
        # 生成备份文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(BACKUP_DIR, f"projects_backup_{timestamp}.db")
        
        # 备份数据库
        shutil.copy2(DB_FILE, backup_file)
        file_size = os.path.getsize(backup_file) / 1024  # KB
        
        print(f"  ✓ 备份成功")
        print(f"  ✓ 备份文件: {backup_file}")
        print(f"  ✓ 备份大小: {file_size:.2f} KB")
        print()
        return True
        
    except Exception as e:
        print(f"  ✗ 备份失败: {e}")
        print()
        return False

def check_column_exists():
    """检查file_name列是否存在"""
    print("[2/4] 检查invoice_files表结构...")
    
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # 获取invoice_files表的列信息
        cursor.execute("PRAGMA table_info(invoice_files)")
        columns = cursor.fetchall()
        conn.close()
        
        column_names = [col[1] for col in columns]
        
        print(f"  ✓ 找到 {len(column_names)} 列")
        print(f"  列: {', '.join(column_names)}")
        print()
        
        return 'file_name' in column_names
        
    except Exception as e:
        print(f"  ✗ 检查失败: {e}")
        print()
        return False

def add_missing_columns():
    """添加所有缺失的列"""
    print("[3/4] 添加缺失的列...")
    
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # 检查现有列
        cursor.execute("PRAGMA table_info(invoice_files)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        # 定义需要添加的列
        missing_columns = []
        
        # 检查每一列是否存在
        columns_to_add = {
            'file_name': "VARCHAR(300)",
            'file_type': "VARCHAR(20)",
            'uploaded_by': "INTEGER",
            'description': "TEXT",
            'is_deleted': "BOOLEAN DEFAULT 0"
        }
        
        for col_name, col_type in columns_to_add.items():
            if col_name not in column_names:
                missing_columns.append((col_name, col_type))
        
        if not missing_columns:
            print("  ✓ 所有必要的列都已存在")
            conn.close()
            print()
            return True
        
        # 添加缺失的列
        for col_name, col_type in missing_columns:
            print(f"  正在添加 {col_name} 列...")
            try:
                cursor.execute(f"ALTER TABLE invoice_files ADD COLUMN {col_name} {col_type}")
                conn.commit()
                print(f"  ✓ {col_name} 列添加成功")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print(f"  ✓ {col_name} 列已存在")
                else:
                    raise
        
        conn.close()
        print()
        return True
        
    except Exception as e:
        print(f"  ✗ 添加列失败: {e}")
        print()
        return False

def update_file_name_from_path():
    """从file_path或original_name更新file_name（如果为空）"""
    print("[4/4] 更新file_name数据...")
    
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # 获取file_name为空的记录数
        cursor.execute("SELECT COUNT(*) FROM invoice_files WHERE file_name IS NULL OR file_name = ''")
        empty_count = cursor.fetchone()[0]
        
        if empty_count > 0:
            print(f"  发现 {empty_count} 条记录file_name为空，正在更新...")
            
            # 首先尝试从original_name获取
            cursor.execute("""
                UPDATE invoice_files 
                SET file_name = original_name
                WHERE (file_name IS NULL OR file_name = '') 
                  AND original_name IS NOT NULL
            """)
            
            # 再从file_path中提取文件名
            cursor.execute("""
                UPDATE invoice_files 
                SET file_name = 
                    CASE 
                        WHEN file_path LIKE '%/%' THEN 
                            SUBSTR(file_path, INSTR(file_path, '/') + 1)
                        WHEN file_path LIKE '%\\%' THEN
                            SUBSTR(file_path, INSTR(file_path, '\\') + 1)
                        ELSE 
                            file_path
                    END
                WHERE file_name IS NULL OR file_name = ''
            """)
            
            conn.commit()
            cursor.execute("SELECT COUNT(*) FROM invoice_files WHERE file_name IS NULL OR file_name = ''")
            remaining = cursor.fetchone()[0]
            
            print(f"  ✓ 更新完成，剩余空值: {remaining}")
        else:
            print(f"  ✓ 所有file_name都已有值")
        
        conn.close()
        print()
        return True
        
    except Exception as e:
        print(f"  ✗ 更新数据失败: {e}")
        print()
        return False

def main():
    """主函数"""
    print_header()
    
    if not os.path.exists(DB_FILE):
        print(f"✗ 数据库文件不存在: {DB_FILE}")
        return False
    
    # 1. 备份数据库
    if not backup_database():
        return False
    
    # 2. 检查列是否存在
    if check_column_exists():
        print("✓ 必要的列已存在，继续检查其他列...")
    
    # 3. 添加缺失的列
    if not add_missing_columns():
        return False
    
    # 4. 更新file_name数据
    if not update_file_name_from_path():
        return False
    
    print("=" * 70)
    print("✓ 所有操作完成成功！".center(70))
    print("=" * 70)
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

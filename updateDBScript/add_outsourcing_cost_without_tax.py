#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向projects表添加外包费用(不含税)列
版本: v1.0.0
日期: 2026-06-13

功能：
1. 检查projects表是否存在outsourcing_cost_without_tax列
2. 如果不存在，添加外包费用(不含税)列
3. 备份数据库
4. 验证添加结果
"""

import sqlite3
import os
import sys
import shutil
from datetime import datetime

DB_FILE = "instance/projects.db"
BACKUP_DIR = "instance/backups"

def print_header():
    """打印脚本头部信息"""
    print("=" * 70)
    print("添加外包费用(不含税)列".center(70))
    print("=" * 70)
    print()

def backup_database():
    """备份数据库"""
    print("[1/3] 备份数据库...")
    
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

def add_column():
    """添加outsourcing_cost_without_tax列"""
    print("[2/3] 检查并添加外包费用(不含税)列...")
    
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # 检查列是否已存在
        cursor.execute("PRAGMA table_info(projects)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'outsourcing_cost_without_tax' in column_names:
            print("  ✓ outsourcing_cost_without_tax列已存在")
            conn.close()
            print()
            return True
        
        # 添加列
        print("  正在添加outsourcing_cost_without_tax列...")
        cursor.execute("""
            ALTER TABLE projects 
            ADD COLUMN outsourcing_cost_without_tax NUMERIC(10, 2) DEFAULT 0
        """)
        
        conn.commit()
        print("  ✓ outsourcing_cost_without_tax列添加成功")
        conn.close()
        print()
        return True
        
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("  ✓ outsourcing_cost_without_tax列已存在")
            print()
            return True
        else:
            print(f"  ✗ 添加列失败: {e}")
            print()
            return False
    except Exception as e:
        print(f"  ✗ 添加列失败: {e}")
        print()
        return False

def verify_column():
    """验证列是否成功添加"""
    print("[3/3] 验证列结构...")
    
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # 检查列信息
        cursor.execute("PRAGMA table_info(projects)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'outsourcing_cost_without_tax' in column_names:
            print("  ✓ outsourcing_cost_without_tax列已成功添加")
            print(f"  ✓ 目前projects表共有{len(columns)}列")
        else:
            print("  ✗ outsourcing_cost_without_tax列未找到")
            conn.close()
            return False
        
        conn.close()
        print()
        return True
        
    except Exception as e:
        print(f"  ✗ 验证失败: {e}")
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
    
    # 2. 添加列
    if not add_column():
        return False
    
    # 3. 验证
    if not verify_column():
        return False
    
    print("=" * 70)
    print("✓ 所有操作完成成功！".center(70))
    print("=" * 70)
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

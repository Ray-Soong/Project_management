#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库快速诊断工具
版本: v1.0.0
日期: 2026-06-09

功能：快速检查数据库的当前状态，无需修改任何内容

使用方法：
    python diagnostic_check.py
"""

import sqlite3
import os
import sys
from datetime import datetime
from pathlib import Path

DB_FILE = "instance/projects.db"

class DatabaseDiagnostics:
    """数据库诊断工具"""
    
    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """连接数据库"""
        try:
            self.conn = sqlite3.connect(self.db_file)
            self.cursor = self.conn.cursor()
            return True
        except Exception as e:
            print(f"✗ 连接失败: {e}")
            return False
    
    def close(self):
        """关闭连接"""
        if self.conn:
            self.conn.close()
    
    def check_file(self):
        """检查数据库文件"""
        print("\n【数据库文件】")
        print("-" * 50)
        
        if not os.path.exists(self.db_file):
            print(f"✗ 文件不存在: {self.db_file}")
            return False
        
        file_size = os.path.getsize(self.db_file)
        file_size_mb = file_size / 1024 / 1024
        
        print(f"✓ 文件存在: {self.db_file}")
        print(f"  大小: {file_size_mb:.2f} MB ({file_size:,} 字节)")
        
        file_stat = os.stat(self.db_file)
        mod_time = datetime.fromtimestamp(file_stat.st_mtime)
        print(f"  最后修改: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True
    
    def check_version(self):
        """检查SQLite版本"""
        print("\n【SQLite版本】")
        print("-" * 50)
        
        try:
            version = sqlite3.version
            lib_version = sqlite3.sqlite_version
            print(f"✓ Python SQLite: {version}")
            print(f"✓ SQLite库版本: {lib_version}")
            return True
        except Exception as e:
            print(f"✗ 检查失败: {e}")
            return False
    
    def check_tables(self):
        """检查表"""
        print("\n【数据库表】")
        print("-" * 50)
        
        try:
            self.cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = [row[0] for row in self.cursor.fetchall()]
            
            if not tables:
                print("✗ 未发现任何表")
                return False
            
            print(f"✓ 发现 {len(tables)} 个表:")
            
            for table_name in tables:
                self.cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = self.cursor.fetchone()[0]
                print(f"  - {table_name}: {count:,} 条记录")
            
            return True
            
        except Exception as e:
            print(f"✗ 检查失败: {e}")
            return False
    
    def check_projects_table(self):
        """详细检查projects表"""
        print("\n【Projects表详情】")
        print("-" * 50)
        
        try:
            # 检查表是否存在
            self.cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='projects'"
            )
            if not self.cursor.fetchone():
                print("✗ Projects表不存在")
                return False
            
            # 获取列信息
            self.cursor.execute("PRAGMA table_info(projects)")
            columns = self.cursor.fetchall()
            
            print(f"✓ 列数: {len(columns)}")
            print("  列表:")
            
            for col_id, col_name, col_type, notnull, dflt_value, pk in columns:
                nullable = "NOT NULL" if notnull else "NULL"
                print(f"    - {col_name}: {col_type} ({nullable})")
            
            # 获取记录数
            self.cursor.execute("SELECT COUNT(*) FROM projects")
            count = self.cursor.fetchone()[0]
            print(f"\n✓ 记录数: {count}")
            
            if count > 0:
                # 获取一些统计信息
                self.cursor.execute("""
                    SELECT 
                        COUNT(DISTINCT status) as status_count,
                        COUNT(DISTINCT manager) as manager_count
                    FROM projects
                """)
                status_count, manager_count = self.cursor.fetchone()
                print(f"  项目状态类型: {status_count}")
                print(f"  项目经理数: {manager_count}")
                
                # 按状态统计
                self.cursor.execute("""
                    SELECT status, COUNT(*) as count
                    FROM projects
                    GROUP BY status
                    ORDER BY count DESC
                """)
                print("\n  按状态统计:")
                for status, count in self.cursor.fetchall():
                    print(f"    - {status}: {count}")
            
            return True
            
        except Exception as e:
            print(f"✗ 检查失败: {e}")
            return False
    
    def check_users_table(self):
        """检查Users表"""
        print("\n【Users表详情】")
        print("-" * 50)
        
        try:
            # 检查表是否存在
            self.cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
            )
            if not self.cursor.fetchone():
                print("✗ Users表不存在")
                return False
            
            # 获取列信息
            self.cursor.execute("PRAGMA table_info(users)")
            columns = self.cursor.fetchall()
            
            print(f"✓ 列数: {len(columns)}")
            
            # 获取记录数
            self.cursor.execute("SELECT COUNT(*) FROM users")
            count = self.cursor.fetchone()[0]
            print(f"✓ 记录数: {count}")
            
            if count > 0:
                # 按角色统计
                self.cursor.execute("""
                    SELECT role, COUNT(*) as count
                    FROM users
                    GROUP BY role
                    ORDER BY count DESC
                """)
                print("\n  按角色统计:")
                for role, count in self.cursor.fetchall():
                    print(f"    - {role}: {count}")
            
            return True
            
        except Exception as e:
            print(f"✗ 检查失败: {e}")
            return False
    
    def check_critical_tables(self):
        """检查关键表的状态"""
        print("\n【关键表检查】")
        print("-" * 50)
        
        critical_tables = {
            'projects': 'Projects',
            'users': 'Users',
            'expenses': 'Expenses',
            'expense_items': 'Expense Items',
            'work_logs': 'Work Logs',
            'tasks': 'Tasks',
            'project_assignments': 'Project Assignments',
        }
        
        self.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        existing_tables = {row[0] for row in self.cursor.fetchall()}
        
        status = []
        for table_name, display_name in critical_tables.items():
            if table_name in existing_tables:
                self.cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = self.cursor.fetchone()[0]
                status.append(f"✓ {display_name}: {count:,} 条")
            else:
                status.append(f"✗ {display_name}: 不存在")
        
        for line in status:
            print(f"  {line}")
        
        return True
    
    def check_data_relationships(self):
        """检查数据关系"""
        print("\n【数据关系检查】")
        print("-" * 50)
        
        try:
            # 检查work_logs中的孤立数据
            self.cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='work_logs'"
            )
            if self.cursor.fetchone():
                self.cursor.execute("""
                    SELECT COUNT(*) FROM work_logs 
                    WHERE project_id NOT IN (SELECT id FROM projects)
                """)
                orphan_count = self.cursor.fetchone()[0]
                if orphan_count > 0:
                    print(f"⚠️  孤立的work_logs: {orphan_count} 条")
                else:
                    print(f"✓ work_logs: 无孤立数据")
            
            # 检查expenses中的孤立数据
            self.cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='expenses'"
            )
            if self.cursor.fetchone():
                self.cursor.execute("""
                    SELECT COUNT(*) FROM expenses 
                    WHERE project_id NOT IN (SELECT id FROM projects)
                """)
                orphan_count = self.cursor.fetchone()[0]
                if orphan_count > 0:
                    print(f"⚠️  孤立的expenses: {orphan_count} 条")
                else:
                    print(f"✓ expenses: 无孤立数据")
            
            return True
            
        except Exception as e:
            print(f"⚠️  检查失败: {e}")
            return True
    
    def check_foreign_keys(self):
        """检查外键约束"""
        print("\n【外键约束】")
        print("-" * 50)
        
        try:
            # SQLite中检查外键
            self.cursor.execute("PRAGMA foreign_keys")
            fk_enabled = self.cursor.fetchone()[0]
            
            if fk_enabled:
                print("✓ 外键约束已启用")
            else:
                print("⚠️  外键约束已禁用（SQLite默认）")
                print("  这是正常的，应用程序在代码层面管理关系")
            
            return True
            
        except Exception as e:
            print(f"⚠️  检查失败: {e}")
            return True
    
    def generate_summary(self):
        """生成诊断摘要"""
        print("\n【诊断摘要】")
        print("-" * 50)
        
        try:
            # 收集统计信息
            self.cursor.execute(
                "SELECT COUNT(name) FROM sqlite_master WHERE type='table'"
            )
            table_count = self.cursor.fetchone()[0]
            
            self.cursor.execute(
                "SELECT SUM(COUNT(*)) FROM sqlite_master WHERE type='table'"
            )
            
            # 计算总记录数
            self.cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = [row[0] for row in self.cursor.fetchall()]
            total_records = 0
            
            for table in tables:
                self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
                total_records += self.cursor.fetchone()[0]
            
            print(f"✓ 表数: {table_count}")
            print(f"✓ 总记录数: {total_records:,}")
            
            return True
            
        except Exception as e:
            print(f"⚠️  摘要生成失败: {e}")
            return True
    
    def run(self):
        """运行完整诊断"""
        print("\n" + "=" * 50)
        print("数据库快速诊断工具".center(50))
        print("版本 v1.0.0".center(50))
        print("=" * 50)
        
        # 检查文件
        if not self.check_file():
            return False
        
        # 连接数据库
        if not self.connect():
            return False
        
        try:
            # 检查SQLite版本
            self.check_version()
            
            # 检查表
            self.check_tables()
            
            # 检查关键表
            self.check_critical_tables()
            
            # 检查Projects表详情
            self.check_projects_table()
            
            # 检查Users表
            self.check_users_table()
            
            # 检查数据关系
            self.check_data_relationships()
            
            # 检查外键
            self.check_foreign_keys()
            
            # 生成摘要
            self.generate_summary()
            
            # 建议
            print("\n【建议】")
            print("-" * 50)
            print("✓ 如果上面没有红色 ✗，数据库状态良好")
            print("✗ 如果有红色 ✗，运行升级工具:")
            print("  python updateDBScript/comprehensive_db_upgrade.py")
            print("⚠️  如果有黄色 ⚠️，可能需要清理数据")
            
            print("\n" + "=" * 50)
            print("诊断完成".center(50))
            print("=" * 50 + "\n")
            
            return True
            
        finally:
            self.close()

def main():
    """主函数"""
    try:
        diagnostics = DatabaseDiagnostics(DB_FILE)
        success = diagnostics.run()
        return success
    except Exception as e:
        print(f"\n✗ 诊断失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n✗ 用户中断诊断")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ 未预期的错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

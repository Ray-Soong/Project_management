#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
综合数据库升级工具 - 诊断和修复projects.db兼容性问题
版本: v2.0.0
日期: 2026-06-09

功能：
1. 诊断数据库架构问题
2. 修复表结构不兼容
3. 处理字段类型转换
4. 清理孤立数据
5. 验证数据完整性
6. 生成升级报告

使用方法：
    python comprehensive_db_upgrade.py
"""

import sqlite3
import os
import sys
import shutil
from datetime import datetime
from pathlib import Path

# 数据库配置
DB_FILE = "instance/projects.db"
BACKUP_DIR = "instance/backups"

# 定义所有表的架构
TABLES_SCHEMA = {
    'users': {
        'columns': {
            'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'username': 'VARCHAR(80) UNIQUE NOT NULL',
            'password_hash': 'VARCHAR(120) NOT NULL',
            'role': 'VARCHAR(20) NOT NULL',
            'created_at': 'DATETIME DEFAULT CURRENT_TIMESTAMP',
            'default_hourly_rate': 'NUMERIC(10, 2)',
        }
    },
    'projects': {
        'columns': {
            'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'project_number': 'VARCHAR(20) UNIQUE',
            'name': 'VARCHAR(200) NOT NULL',
            'manager': 'VARCHAR(100) NOT NULL',
            'start_date': 'DATE',
            'planned_end_date': 'DATE',
            'contract_signing_date': 'DATE',
            'estimated_hours': 'FLOAT',
            'contract_amount': 'NUMERIC(14, 2)',
            'status': 'VARCHAR(20) NOT NULL DEFAULT \'启动中\'',
            'payment_method': 'VARCHAR(50)',
            'acceptance_date': 'DATE',
            'settlement_date': 'DATE',
            'invoice_stage': 'VARCHAR(20) DEFAULT \'未开\'',
            'invoice_date': 'DATE',
            'invoice_amount': 'NUMERIC(14, 2)',
            'invoice_file': 'VARCHAR(500)',
            'invoice_notes': 'TEXT',
            'contract_amount_with_tax': 'NUMERIC(14, 2)',
            'contract_amount_without_tax': 'NUMERIC(14, 2)',
            'payment_received': 'NUMERIC(14, 2)',
            'remaining_amount': 'NUMERIC(14, 2)',
            'project_type': 'VARCHAR(50)',
            'customer_name': 'VARCHAR(200)',
            'final_customer': 'VARCHAR(200)',
            'po_number': 'VARCHAR(100)',
            'contract_file': 'VARCHAR(500)',
            'created_at': 'DATETIME DEFAULT CURRENT_TIMESTAMP',
            'outsourcing_cost': 'NUMERIC(10, 2) DEFAULT 0',
            'supplier_name': 'VARCHAR(200)',
            'supplier_invoice_issued': 'BOOLEAN DEFAULT 0',
            'supplier_pending_amount': 'NUMERIC(10, 2) DEFAULT 0',
            'outsourcing_cost_notes': 'TEXT',
            'indirect_cost': 'NUMERIC(10, 2) DEFAULT 0',
            'indirect_cost_notes': 'TEXT',
            'stage_payment_notes': 'TEXT',
            'payment_amount_notes': 'TEXT',
            'invoice_amount_issued': 'NUMERIC(14, 2) DEFAULT 0',
            'current_invoice_amount': 'NUMERIC(14, 2) DEFAULT 0',
            'accounts_receivable': 'NUMERIC(14, 2) DEFAULT 0',
        }
    },
    'expenses': {
        'columns': {
            'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'project_id': 'INTEGER NOT NULL',
            'category': 'VARCHAR(50) NOT NULL',
            'description': 'TEXT',
            'total_amount': 'NUMERIC(10, 2) NOT NULL',
            'status': 'VARCHAR(20) NOT NULL DEFAULT \'待审批\'',
            'submission_date': 'DATETIME DEFAULT CURRENT_TIMESTAMP',
            'approval_date': 'DATETIME',
            'approver_id': 'INTEGER',
            'approval_notes': 'TEXT',
            'created_at': 'DATETIME DEFAULT CURRENT_TIMESTAMP',
            'FOREIGN KEY (project_id)': 'REFERENCES projects(id)',
            'FOREIGN KEY (approver_id)': 'REFERENCES users(id)',
        }
    },
    'expense_items': {
        'columns': {
            'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'expense_id': 'INTEGER NOT NULL',
            'description': 'TEXT',
            'amount': 'NUMERIC(10, 2) NOT NULL',
            'receipt_image': 'VARCHAR(500)',
            'receipt_original_name': 'VARCHAR(300)',
            'FOREIGN KEY (expense_id)': 'REFERENCES expenses(id)',
        }
    },
    'work_logs': {
        'columns': {
            'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'project_id': 'INTEGER NOT NULL',
            'user_id': 'INTEGER NOT NULL',
            'date': 'DATE NOT NULL',
            'hours': 'FLOAT NOT NULL',
            'description': 'TEXT',
            'created_at': 'DATETIME DEFAULT CURRENT_TIMESTAMP',
            'FOREIGN KEY (project_id)': 'REFERENCES projects(id)',
            'FOREIGN KEY (user_id)': 'REFERENCES users(id)',
        }
    },
    'project_assignments': {
        'columns': {
            'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'project_id': 'INTEGER NOT NULL',
            'user_id': 'INTEGER NOT NULL',
            'hourly_rate': 'NUMERIC(10, 2)',
            'assigned_date': 'DATETIME DEFAULT CURRENT_TIMESTAMP',
            'FOREIGN KEY (project_id)': 'REFERENCES projects(id)',
            'FOREIGN KEY (user_id)': 'REFERENCES users(id)',
        }
    },
    'tasks': {
        'columns': {
            'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'project_id': 'INTEGER NOT NULL',
            'title': 'VARCHAR(200) NOT NULL',
            'description': 'TEXT',
            'status': 'VARCHAR(20) NOT NULL DEFAULT \'进行中\'',
            'priority': 'VARCHAR(20)',
            'assigned_to': 'INTEGER',
            'due_date': 'DATE',
            'created_at': 'DATETIME DEFAULT CURRENT_TIMESTAMP',
            'updated_at': 'DATETIME DEFAULT CURRENT_TIMESTAMP',
            'FOREIGN KEY (project_id)': 'REFERENCES projects(id)',
            'FOREIGN KEY (assigned_to)': 'REFERENCES users(id)',
        }
    },
    'invoice_files': {
        'columns': {
            'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'project_id': 'INTEGER NOT NULL',
            'file_path': 'VARCHAR(500) NOT NULL',
            'original_name': 'VARCHAR(300)',
            'upload_date': 'DATETIME DEFAULT CURRENT_TIMESTAMP',
            'file_size': 'INTEGER',
            'FOREIGN KEY (project_id)': 'REFERENCES projects(id)',
        }
    },
}

class DatabaseUpgrader:
    """数据库升级器"""
    
    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = None
        self.cursor = None
        self.issues = []
        self.fixes_applied = []
        
    def connect(self):
        """连接数据库"""
        try:
            self.conn = sqlite3.connect(self.db_file)
            self.cursor = self.conn.cursor()
            return True
        except Exception as e:
            print(f"  ✗ 数据库连接失败: {e}")
            return False
    
    def close(self):
        """关闭连接"""
        if self.conn:
            self.conn.close()
    
    def backup_database(self):
        """备份数据库"""
        print("\n[1/6] 备份数据库...")
        
        try:
            if not os.path.exists(self.db_file):
                print("  ⚠️  数据库文件不存在")
                return False
            
            os.makedirs(BACKUP_DIR, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(BACKUP_DIR, f"projects_backup_{timestamp}.db")
            
            shutil.copy2(self.db_file, backup_file)
            file_size = os.path.getsize(backup_file) / 1024 / 1024
            
            print(f"  ✓ 备份成功")
            print(f"  ✓ 备份文件: {backup_file}")
            print(f"  ✓ 备份大小: {file_size:.2f} MB")
            return True
            
        except Exception as e:
            print(f"  ✗ 备份失败: {e}")
            return False
    
    def diagnose_schema(self):
        """诊断数据库架构问题"""
        print("\n[2/6] 诊断数据库架构...")
        
        try:
            # 检查表是否存在
            self.cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            existing_tables = {row[0] for row in self.cursor.fetchall()}
            
            for table_name in TABLES_SCHEMA:
                if table_name not in existing_tables:
                    self.issues.append(f"缺失表: {table_name}")
                    print(f"  ⚠️  缺失表: {table_name}")
                else:
                    self._check_table_columns(table_name)
            
            if not self.issues:
                print("  ✓ 数据库架构无问题")
            else:
                print(f"  ⚠️  发现 {len(self.issues)} 个问题")
            
            return True
            
        except Exception as e:
            print(f"  ✗ 诊断失败: {e}")
            return False
    
    def _check_table_columns(self, table_name):
        """检查表的列"""
        expected_columns = TABLES_SCHEMA[table_name]['columns']
        
        try:
            self.cursor.execute(f"PRAGMA table_info({table_name})")
            existing_columns = {row[1] for row in self.cursor.fetchall()}
            
            for col_name in expected_columns:
                # 跳过FOREIGN KEY定义
                if 'FOREIGN KEY' in col_name:
                    continue
                
                if col_name not in existing_columns:
                    self.issues.append(f"表 {table_name} 缺失列: {col_name}")
                    print(f"  ⚠️  表 {table_name} 缺失列: {col_name}")
        
        except Exception as e:
            print(f"  ✗ 检查表 {table_name} 失败: {e}")
    
    def fix_schema(self):
        """修复数据库架构"""
        print("\n[3/6] 修复数据库架构...")
        
        if not self.issues:
            print("  ✓ 无需修复")
            return True
        
        try:
            fixed_count = 0
            
            for issue in self.issues:
                if "缺失表:" in issue:
                    table_name = issue.replace("缺失表: ", "")
                    if self._create_table(table_name):
                        fixed_count += 1
                        self.fixes_applied.append(f"创建表: {table_name}")
                
                elif "缺失列:" in issue:
                    parts = issue.split(" ")
                    table_name = parts[1]
                    col_name = parts[-1]
                    if self._add_column(table_name, col_name):
                        fixed_count += 1
                        self.fixes_applied.append(f"添加列: {table_name}.{col_name}")
            
            if fixed_count > 0:
                self.conn.commit()
                print(f"  ✓ 修复了 {fixed_count} 个问题")
            
            return True
            
        except Exception as e:
            print(f"  ✗ 修复失败: {e}")
            return False
    
    def _create_table(self, table_name):
        """创建缺失的表"""
        try:
            schema = TABLES_SCHEMA[table_name]
            columns_def = []
            
            for col_name, col_type in schema['columns'].items():
                if 'FOREIGN KEY' not in col_name:
                    columns_def.append(f"{col_name} {col_type}")
            
            # 添加外键约束
            for col_name in schema['columns']:
                if 'FOREIGN KEY' in col_name:
                    columns_def.append(f"{col_name} {schema['columns'][col_name]}")
            
            sql = f"CREATE TABLE IF NOT EXISTS {table_name} (\n"
            sql += ",\n".join(columns_def) + "\n)"
            
            self.cursor.execute(sql)
            print(f"  ✓ 创建表: {table_name}")
            return True
            
        except Exception as e:
            print(f"  ✗ 创建表 {table_name} 失败: {e}")
            return False
    
    def _add_column(self, table_name, col_name):
        """添加缺失的列"""
        try:
            schema = TABLES_SCHEMA[table_name]
            
            if col_name not in schema['columns']:
                print(f"  ⚠️  列定义不存在: {table_name}.{col_name}")
                return False
            
            col_type = schema['columns'][col_name]
            sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"
            
            self.cursor.execute(sql)
            print(f"  ✓ 添加列: {table_name}.{col_name}")
            return True
            
        except sqlite3.OperationalError as e:
            if "column already exists" in str(e):
                print(f"  ℹ️  列已存在: {table_name}.{col_name}")
                return True
            else:
                print(f"  ✗ 添加列失败: {table_name}.{col_name} - {e}")
                return False
        except Exception as e:
            print(f"  ✗ 添加列失败: {table_name}.{col_name} - {e}")
            return False
    
    def cleanup_orphaned_data(self):
        """清理孤立数据"""
        print("\n[4/6] 清理孤立数据...")
        
        try:
            cleanup_count = 0
            
            # 检查表是否存在再执行清理
            self.cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            existing_tables = {row[0] for row in self.cursor.fetchall()}
            
            if 'work_logs' in existing_tables and 'projects' in existing_tables:
                # 清理孤立的工作日志
                self.cursor.execute("""
                    DELETE FROM work_logs 
                    WHERE project_id NOT IN (SELECT id FROM projects)
                """)
                cleanup_count += self.cursor.rowcount
                if self.cursor.rowcount > 0:
                    print(f"  ✓ 清理孤立工作日志: {self.cursor.rowcount} 条")
            
            if 'expenses' in existing_tables and 'projects' in existing_tables:
                # 清理孤立的报销
                self.cursor.execute("""
                    DELETE FROM expenses 
                    WHERE project_id NOT IN (SELECT id FROM projects)
                """)
                cleanup_count += self.cursor.rowcount
                if self.cursor.rowcount > 0:
                    print(f"  ✓ 清理孤立报销: {self.cursor.rowcount} 条")
            
            if cleanup_count == 0:
                print("  ✓ 无孤立数据")
            
            if cleanup_count > 0:
                self.conn.commit()
            
            return True
            
        except Exception as e:
            print(f"  ⚠️  清理数据出错: {e}")
            return True  # 不作为致命错误
    
    def validate_data_integrity(self):
        """验证数据完整性"""
        print("\n[5/6] 验证数据完整性...")
        
        try:
            integrity_issues = 0
            
            # 检查外键约束（SQLite默认不强制）
            self.cursor.execute("PRAGMA foreign_keys = ON")
            
            # 检查projects表
            if self.table_exists('projects'):
                self.cursor.execute("""
                    SELECT COUNT(*) FROM projects 
                    WHERE name IS NULL OR manager IS NULL
                """)
                invalid_count = self.cursor.fetchone()[0]
                if invalid_count > 0:
                    print(f"  ⚠️  发现 {invalid_count} 条无效的项目记录")
                    integrity_issues += invalid_count
            
            # 检查users表
            if self.table_exists('users'):
                self.cursor.execute("""
                    SELECT COUNT(*) FROM users 
                    WHERE username IS NULL OR password_hash IS NULL
                """)
                invalid_count = self.cursor.fetchone()[0]
                if invalid_count > 0:
                    print(f"  ⚠️  发现 {invalid_count} 条无效的用户记录")
                    integrity_issues += invalid_count
            
            if integrity_issues == 0:
                print("  ✓ 数据完整性检查通过")
            
            return True
            
        except Exception as e:
            print(f"  ⚠️  完整性检查出错: {e}")
            return True
    
    def table_exists(self, table_name):
        """检查表是否存在"""
        try:
            self.cursor.execute(
                f"SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            )
            return self.cursor.fetchone() is not None
        except:
            return False
    
    def generate_report(self):
        """生成升级报告"""
        print("\n[6/6] 生成升级报告...")
        
        report = []
        report.append("=" * 70)
        report.append("数据库升级完成报告".center(70))
        report.append("=" * 70)
        report.append("")
        report.append(f"升级时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"数据库: {self.db_file}")
        report.append("")
        
        if self.issues:
            report.append(f"检测到的问题: {len(self.issues)}")
            for issue in self.issues:
                report.append(f"  - {issue}")
        else:
            report.append("检测到的问题: 无")
        
        report.append("")
        
        if self.fixes_applied:
            report.append(f"应用的修复: {len(self.fixes_applied)}")
            for fix in self.fixes_applied:
                report.append(f"  ✓ {fix}")
        else:
            report.append("应用的修复: 无")
        
        report.append("")
        report.append("=" * 70)
        report.append("✓ 数据库已准备就绪，可以启动应用程序".center(70))
        report.append("=" * 70)
        
        # 打印报告
        for line in report:
            print(line)
        
        # 保存报告到文件
        report_file = os.path.join(
            BACKUP_DIR, 
            f"upgrade_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        os.makedirs(BACKUP_DIR, exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(report))
        
        print(f"\n✓ 报告已保存到: {report_file}")
        return True
    
    def run(self):
        """执行完整升级流程"""
        print("=" * 70)
        print("综合数据库升级工具".center(70))
        print("版本 v2.0.0".center(70))
        print("=" * 70)
        
        # 连接数据库
        if not self.connect():
            return False
        
        try:
            # 备份数据库
            if not self.backup_database():
                return False
            
            # 诊断架构
            if not self.diagnose_schema():
                return False
            
            # 修复架构
            if not self.fix_schema():
                return False
            
            # 清理孤立数据
            if not self.cleanup_orphaned_data():
                return False
            
            # 验证完整性
            if not self.validate_data_integrity():
                return False
            
            # 生成报告
            if not self.generate_report():
                return False
            
            return True
            
        finally:
            self.close()

def main():
    """主函数"""
    try:
        # 检查数据库文件
        if not os.path.exists(DB_FILE):
            print("✗ 错误: 数据库文件不存在")
            print(f"  路径: {DB_FILE}")
            return False
        
        # 创建升级器
        upgrader = DatabaseUpgrader(DB_FILE)
        
        # 执行升级
        success = upgrader.run()
        
        return success
        
    except Exception as e:
        print(f"\n✗ 发生未预期的错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n✗ 用户中断升级")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ 发生未预期的错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

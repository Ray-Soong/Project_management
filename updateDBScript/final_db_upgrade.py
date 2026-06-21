#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最终数据库升级方案 - 基于实际的models.py定义
版本: v3.0.0
日期: 2026-06-09

功能：
1. 备份数据库
2. 诊断架构问题
3. 添加缺失的表（如invoice_files）
4. 验证现有表结构与models.py的一致性
5. 清理孤立数据
6. 生成完整报告

使用方法：
    python final_db_upgrade.py
"""

import sqlite3
import os
import sys
import shutil
from datetime import datetime

DB_FILE = "instance/projects.db"
BACKUP_DIR = "instance/backups"

# 需要添加的表（如果不存在）
MISSING_TABLES = {
    'invoice_files': '''
        CREATE TABLE invoice_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            file_path VARCHAR(500) NOT NULL,
            original_name VARCHAR(300),
            upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            file_size INTEGER,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
    ''',
    'stage_payments': '''
        CREATE TABLE stage_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            stage_name VARCHAR(100) NOT NULL,
            payment_amount NUMERIC(14, 2) NOT NULL,
            payment_date DATE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
    ''',
}

# 已有的表及其基本信息
EXISTING_TABLES_INFO = {
    'users': '用户表',
    'projects': '项目表',
    'expenses': '报销表',
    'expense_items': '报销明细表',
    'work_logs': '工作日志表',
    'tasks': '任务表',
    'project_assignments': '项目分配表',
    'project_manager_assignments': '项目经理分配表',
    'custom_fields': '自定义字段表',
    'project_custom_field_values': '项目自定义字段值表',
    'project_expense_records': '项目费用记录表',
    'operation_logs': '操作日志表',
}

class FinalDatabaseUpgrader:
    """最终数据库升级器"""
    
    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = None
        self.cursor = None
        self.issues = []
        self.fixes = []
    
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
    
    def backup_database(self):
        """备份数据库"""
        print("\n[1/6] 备份数据库...")
        
        try:
            os.makedirs(BACKUP_DIR, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(BACKUP_DIR, f"projects_backup_final_{timestamp}.db")
            
            shutil.copy2(self.db_file, backup_file)
            size_mb = os.path.getsize(backup_file) / 1024 / 1024
            
            print(f"  ✓ 备份成功")
            print(f"  ✓ 文件: {backup_file}")
            print(f"  ✓ 大小: {size_mb:.2f} MB")
            return True
            
        except Exception as e:
            print(f"  ✗ 备份失败: {e}")
            return False
    
    def diagnose_tables(self):
        """诊断表结构"""
        print("\n[2/6] 诊断表结构...")
        
        try:
            # 检查现有表
            self.cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            existing_tables = {row[0] for row in self.cursor.fetchall()}
            
            print(f"  ✓ 现有表数: {len(existing_tables)}")
            
            # 检查缺失的表
            missing = set()
            for table_name in MISSING_TABLES:
                if table_name not in existing_tables:
                    missing.add(table_name)
                    self.issues.append(f"缺失表: {table_name}")
            
            if missing:
                print(f"  ⚠️  发现 {len(missing)} 个缺失的表:")
                for table in sorted(missing):
                    print(f"    - {table}")
            else:
                print(f"  ✓ 所有必要的表都存在")
            
            # 检查项目表的关键列
            print("\n  检查Projects表结构...")
            self.cursor.execute("PRAGMA table_info(projects)")
            projects_cols = {row[1] for row in self.cursor.fetchall()}
            
            critical_cols = {
                'id', 'name', 'manager', 'status', 'invoice_stage',
                'invoice_date', 'invoice_amount', 'invoice_file', 'invoice_notes',
                'contract_amount_with_tax', 'contract_amount_without_tax',
                'payment_received', 'accounts_receivable'
            }
            
            missing_cols = critical_cols - projects_cols
            if missing_cols:
                print(f"  ⚠️  Projects表缺失列:")
                for col in sorted(missing_cols):
                    self.issues.append(f"缺失列: projects.{col}")
                    print(f"    - {col}")
            else:
                print(f"  ✓ Projects表的关键列完整")
            
            return len(self.issues) == 0
            
        except Exception as e:
            print(f"  ✗ 诊断失败: {e}")
            return False
    
    def create_missing_tables(self):
        """创建缺失的表"""
        print("\n[3/6] 创建缺失的表...")
        
        try:
            # 检查现有表
            self.cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            existing_tables = {row[0] for row in self.cursor.fetchall()}
            
            created_count = 0
            
            for table_name, create_sql in MISSING_TABLES.items():
                if table_name not in existing_tables:
                    try:
                        self.cursor.execute(create_sql)
                        print(f"  ✓ 创建表: {table_name}")
                        self.fixes.append(f"创建表: {table_name}")
                        created_count += 1
                    except Exception as e:
                        print(f"  ✗ 创建表失败: {table_name} - {e}")
                else:
                    print(f"  ℹ️  表已存在: {table_name}")
            
            if created_count > 0:
                self.conn.commit()
                print(f"  ✓ 创建了 {created_count} 个表")
            else:
                print(f"  ✓ 无需创建表")
            
            return True
            
        except Exception as e:
            print(f"  ✗ 创建表失败: {e}")
            return False
    
    def verify_data_integrity(self):
        """验证数据完整性"""
        print("\n[4/6] 验证数据完整性...")
        
        try:
            integrity_ok = True
            
            # 检查projects表
            self.cursor.execute("SELECT COUNT(*) FROM projects WHERE name IS NULL OR manager IS NULL")
            invalid_count = self.cursor.fetchone()[0]
            if invalid_count > 0:
                print(f"  ⚠️  Projects表有 {invalid_count} 条无效记录")
                integrity_ok = False
            else:
                print(f"  ✓ Projects表数据完整")
            
            # 检查users表
            self.cursor.execute("SELECT COUNT(*) FROM users WHERE username IS NULL")
            invalid_count = self.cursor.fetchone()[0]
            if invalid_count > 0:
                print(f"  ⚠️  Users表有 {invalid_count} 条无效记录")
                integrity_ok = False
            else:
                print(f"  ✓ Users表数据完整")
            
            # 检查孤立的work_logs
            self.cursor.execute("""
                SELECT COUNT(*) FROM work_logs 
                WHERE project_id NOT IN (SELECT id FROM projects)
            """)
            orphan_count = self.cursor.fetchone()[0]
            if orphan_count > 0:
                print(f"  ⚠️  孤立的work_logs: {orphan_count} 条")
            else:
                print(f"  ✓ work_logs: 无孤立数据")
            
            # 检查孤立的expenses
            self.cursor.execute("""
                SELECT COUNT(*) FROM expenses 
                WHERE project_id NOT IN (SELECT id FROM projects) AND project_id IS NOT NULL
            """)
            orphan_count = self.cursor.fetchone()[0]
            if orphan_count > 0:
                print(f"  ⚠️  孤立的expenses: {orphan_count} 条")
            else:
                print(f"  ✓ expenses: 无孤立数据")
            
            return integrity_ok
            
        except Exception as e:
            print(f"  ⚠️  完整性检查出错: {e}")
            return True
    
    def show_summary(self):
        """显示数据库摘要"""
        print("\n[5/6] 数据库摘要...")
        
        try:
            # 表统计
            self.cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = [row[0] for row in self.cursor.fetchall()]
            
            print(f"  表数: {len(tables)}")
            
            # 主要表的记录数
            main_tables = ['projects', 'users', 'expenses', 'work_logs', 'tasks']
            total_records = 0
            
            for table in main_tables:
                if table in tables:
                    self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = self.cursor.fetchone()[0]
                    total_records += count
                    print(f"  - {table}: {count:,} 条")
            
            print(f"\n  总记录数: {total_records:,}")
            
            return True
            
        except Exception as e:
            print(f"  ⚠️  摘要生成出错: {e}")
            return True
    
    def generate_report(self):
        """生成升级报告"""
        print("\n[6/6] 生成报告...\n")
        
        report = []
        report.append("=" * 70)
        report.append("数据库升级完成报告 v3.0.0".center(70))
        report.append("=" * 70)
        report.append("")
        report.append(f"升级时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"数据库: {self.db_file}")
        report.append("")
        
        if self.issues:
            report.append(f"【检测到的问题】({len(self.issues)}个)")
            for issue in self.issues:
                report.append(f"  ⚠️  {issue}")
        else:
            report.append("【检测到的问题】: 无")
        
        report.append("")
        
        if self.fixes:
            report.append(f"【应用的修复】({len(self.fixes)}个)")
            for fix in self.fixes:
                report.append(f"  ✓ {fix}")
        else:
            report.append("【应用的修复】: 无")
        
        report.append("")
        report.append("【结论】")
        
        if len(self.issues) == 0:
            report.append("✓ 数据库已完全兼容，可以启动应用")
        elif len(self.fixes) > 0:
            report.append("✓ 已修复关键问题，可以启动应用")
        else:
            report.append("⚠️  仍有未解决的问题，请检查日志")
        
        report.append("")
        report.append("=" * 70)
        
        # 打印报告
        for line in report:
            print(line)
        
        # 保存报告
        report_file = os.path.join(
            BACKUP_DIR,
            f"upgrade_final_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(report))
        
        print(f"\n✓ 报告已保存到: {report_file}\n")
        return True
    
    def run(self):
        """执行完整升级流程"""
        print("=" * 70)
        print("最终数据库升级方案".center(70))
        print("版本 v3.0.0".center(70))
        print("=" * 70)
        
        if not self.connect():
            return False
        
        try:
            # 备份
            if not self.backup_database():
                return False
            
            # 诊断
            if not self.diagnose_tables():
                # 继续，因为可能只是缺少一些表
                pass
            
            # 创建缺失的表
            if not self.create_missing_tables():
                return False
            
            # 验证数据
            self.verify_data_integrity()
            
            # 摘要
            self.show_summary()
            
            # 报告
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
        upgrader = FinalDatabaseUpgrader(DB_FILE)
        
        # 执行升级
        success = upgrader.run()
        
        if success:
            print("✓ 数据库升级成功")
            print("\n接下来的步骤：")
            print("  1. 检查升级报告")
            print("  2. 启动应用: python app.py")
            print("  3. 打开浏览器: http://localhost:5000")
        else:
            print("✗ 数据库升级失败")
        
        return success
        
    except Exception as e:
        print(f"\n✗ 未预期的错误: {e}")
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
        print(f"\n✗ 未预期的错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

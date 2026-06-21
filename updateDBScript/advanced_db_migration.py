#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
高级数据库迁移工具 - 处理复杂的字段添加
版本: v1.0.0
日期: 2026-06-09

功能：
使用表迁移策略添加NOT NULL列和非常数默认值列
- 创建临时表
- 复制数据
- 添加新列
- 验证数据
- 删除旧表
- 重命名新表

使用方法：
    python advanced_db_migration.py
"""

import sqlite3
import os
import sys
import shutil
from datetime import datetime

DB_FILE = "instance/projects.db"
BACKUP_DIR = "instance/backups"

# 需要迁移的表和列
MIGRATIONS = {
    'expenses': [
        ('category', 'VARCHAR(50) NOT NULL DEFAULT \'其他\''),
        ('submission_date', 'DATETIME DEFAULT CURRENT_TIMESTAMP'),
    ],
    'tasks': [
        ('project_id', 'INTEGER NOT NULL'),
        ('updated_at', 'DATETIME DEFAULT CURRENT_TIMESTAMP'),
    ],
}

class AdvancedMigrator:
    """高级数据库迁移器"""
    
    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = None
        self.cursor = None
        self.migrations_applied = []
    
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
        print("[1/4] 备份数据库...")
        
        try:
            os.makedirs(BACKUP_DIR, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(BACKUP_DIR, f"projects_backup_migration_{timestamp}.db")
            
            shutil.copy2(self.db_file, backup_file)
            file_size = os.path.getsize(backup_file) / 1024 / 1024
            
            print(f"  ✓ 备份成功: {backup_file}")
            print(f"  ✓ 大小: {file_size:.2f} MB\n")
            return True
            
        except Exception as e:
            print(f"  ✗ 备份失败: {e}\n")
            return False
    
    def table_exists(self, table_name):
        """检查表是否存在"""
        try:
            self.cursor.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            )
            return self.cursor.fetchone() is not None
        except:
            return False
    
    def column_exists(self, table_name, column_name):
        """检查列是否存在"""
        try:
            self.cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in self.cursor.fetchall()]
            return column_name in columns
        except:
            return False
    
    def get_table_schema(self, table_name):
        """获取表的创建SQL"""
        try:
            self.cursor.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            )
            result = self.cursor.fetchone()
            return result[0] if result else None
        except:
            return None
    
    def migrate_table(self, table_name, new_columns):
        """使用迁移策略添加列到表"""
        
        print(f"  迁移表 {table_name}...")
        
        try:
            # 检查表是否存在
            if not self.table_exists(table_name):
                print(f"    ✗ 表不存在: {table_name}")
                return False
            
            # 获取现有列信息
            self.cursor.execute(f"PRAGMA table_info({table_name})")
            existing_columns = self.cursor.fetchall()
            
            # 检查新列是否已存在
            existing_col_names = {col[1] for col in existing_columns}
            cols_to_add = []
            
            for col_name, col_type in new_columns:
                if col_name not in existing_col_names:
                    cols_to_add.append((col_name, col_type))
            
            if not cols_to_add:
                print(f"    ℹ️  列已存在: {table_name}")
                return True
            
            # 构建新表的列定义
            column_defs = []
            for col in existing_columns:
                col_id, col_name, col_type, notnull, dflt_value, pk = col
                pk_str = "PRIMARY KEY AUTOINCREMENT" if pk else ""
                not_null_str = "NOT NULL" if notnull else ""
                dflt_str = f"DEFAULT {dflt_value}" if dflt_value else ""
                
                col_def = f"{col_name} {col_type} {pk_str} {not_null_str} {dflt_str}".strip()
                column_defs.append(col_def)
            
            # 添加新列定义
            for col_name, col_type in cols_to_add:
                column_defs.append(f"{col_name} {col_type}")
            
            # 创建临时表
            temp_table = f"{table_name}_temp"
            create_temp_sql = f"CREATE TABLE {temp_table} (\n"
            create_temp_sql += ",\n".join(column_defs) + "\n)"
            
            self.cursor.execute(create_temp_sql)
            print(f"    ✓ 创建临时表: {temp_table}")
            
            # 复制现有数据（只复制现有列）
            existing_col_names_str = ", ".join([f"`{col[1]}`" for col in existing_columns])
            copy_sql = f"INSERT INTO {temp_table} ({existing_col_names_str}) SELECT {existing_col_names_str} FROM {table_name}"
            
            self.cursor.execute(copy_sql)
            print(f"    ✓ 复制数据: {self.cursor.rowcount} 条记录")
            
            # 删除原表
            self.cursor.execute(f"DROP TABLE {table_name}")
            print(f"    ✓ 删除原表: {table_name}")
            
            # 重命名临时表
            self.cursor.execute(f"ALTER TABLE {temp_table} RENAME TO {table_name}")
            print(f"    ✓ 重命名表: {temp_table} → {table_name}")
            
            # 记录迁移信息
            for col_name, col_type in cols_to_add:
                self.migrations_applied.append(f"迁移 {table_name}.{col_name}")
            
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"    ✗ 迁移失败: {e}")
            self.conn.rollback()
            return False
    
    def perform_migrations(self):
        """执行所有迁移"""
        print("[2/4] 执行表迁移...\n")
        
        try:
            migration_count = 0
            
            for table_name, new_columns in MIGRATIONS.items():
                if self.migrate_table(table_name, new_columns):
                    migration_count += 1
            
            print(f"\n  ✓ 完成 {migration_count} 个表迁移\n")
            return True
            
        except Exception as e:
            print(f"  ✗ 迁移失败: {e}\n")
            return False
    
    def verify_migrations(self):
        """验证迁移结果"""
        print("[3/4] 验证迁移结果...\n")
        
        try:
            all_verified = True
            
            for table_name, new_columns in MIGRATIONS.items():
                if not self.table_exists(table_name):
                    print(f"  ✗ 表不存在: {table_name}")
                    all_verified = False
                    continue
                
                self.cursor.execute(f"PRAGMA table_info({table_name})")
                existing_cols = {col[1] for col in self.cursor.fetchall()}
                
                for col_name, col_type in new_columns:
                    if col_name in existing_cols:
                        print(f"  ✓ {table_name}.{col_name} 已添加")
                    else:
                        print(f"  ✗ {table_name}.{col_name} 未添加")
                        all_verified = False
            
            print()
            return all_verified
            
        except Exception as e:
            print(f"  ✗ 验证失败: {e}\n")
            return False
    
    def generate_report(self):
        """生成迁移报告"""
        print("[4/4] 生成报告...\n")
        
        report = []
        report.append("=" * 70)
        report.append("数据库高级迁移完成报告".center(70))
        report.append("=" * 70)
        report.append("")
        report.append(f"迁移时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"数据库: {self.db_file}")
        report.append("")
        
        if self.migrations_applied:
            report.append(f"应用的迁移: {len(self.migrations_applied)}")
            for migration in self.migrations_applied:
                report.append(f"  ✓ {migration}")
        else:
            report.append("应用的迁移: 无")
        
        report.append("")
        report.append("=" * 70)
        report.append("✓ 迁移完成".center(70))
        report.append("=" * 70)
        
        # 打印报告
        for line in report:
            print(line)
        
        # 保存报告
        report_file = os.path.join(
            BACKUP_DIR,
            f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(report))
        
        print(f"\n✓ 报告已保存到: {report_file}\n")
        return True
    
    def run(self):
        """执行完整迁移流程"""
        print("=" * 70)
        print("高级数据库迁移工具".center(70))
        print("版本 v1.0.0".center(70))
        print("=" * 70)
        print()
        
        if not self.connect():
            return False
        
        try:
            # 备份
            if not self.backup_database():
                return False
            
            # 执行迁移
            if not self.perform_migrations():
                return False
            
            # 验证
            if not self.verify_migrations():
                print("⚠️  部分迁移未成功")
                return False
            
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
            return False
        
        # 创建迁移器
        migrator = AdvancedMigrator(DB_FILE)
        
        # 执行迁移
        success = migrator.run()
        
        if success:
            print("✓ 迁移成功完成")
            print("  现在可以启动应用程序")
        else:
            print("✗ 迁移失败")
            print("  请检查备份文件并尝试恢复")
        
        return success
        
    except Exception as e:
        print(f"✗ 发生未预期的错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n✗ 用户中断迁移")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ 未预期的错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

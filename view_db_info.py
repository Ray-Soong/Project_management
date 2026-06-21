#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
查看SQLite数据库详细信息
"""
import sqlite3
import os

db_path = 'instance/projects.db'

if not os.path.exists(db_path):
    print(f"错误：数据库文件 {db_path} 不存在！")
    exit(1)

print(f"=" * 80)
print(f"SQLite数据库详细信息")
print(f"数据库文件: {db_path}")
print(f"文件大小: {os.path.getsize(db_path) / 1024:.2f} KB")
print(f"=" * 80)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 获取所有表
tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
print(f"\n📊 数据库包含 {len(tables)} 个表:")
for table in tables:
    print(f"  - {table[0]}")

# 显示每个表的详细信息
for table in tables:
    table_name = table[0]
    print(f"\n{'=' * 80}")
    print(f"📋 表名: {table_name}")
    print(f"{'=' * 80}")
    
    # 获取表结构
    columns = cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
    print(f"\n列信息 (共 {len(columns)} 列):")
    print(f"{'ID':<5} {'列名':<30} {'类型':<15} {'非空':<8} {'默认值':<15} {'主键':<6}")
    print("-" * 85)
    for col in columns:
        col_id, col_name, col_type, not_null, default_val, is_pk = col
        print(f"{col_id:<5} {col_name:<30} {col_type:<15} {'是' if not_null else '否':<8} {str(default_val) if default_val else 'NULL':<15} {'是' if is_pk else '否':<6}")
    
    # 获取记录数
    count = cursor.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    print(f"\n📈 记录数: {count} 条")
    
    # 获取索引信息
    indexes = cursor.execute(f"PRAGMA index_list({table_name})").fetchall()
    if indexes:
        print(f"\n🔍 索引 (共 {len(indexes)} 个):")
        for idx in indexes:
            idx_name = idx[1]
            is_unique = "唯一索引" if idx[2] else "普通索引"
            print(f"  - {idx_name} ({is_unique})")
    
    # 获取外键信息
    foreign_keys = cursor.execute(f"PRAGMA foreign_key_list({table_name})").fetchall()
    if foreign_keys:
        print(f"\n🔗 外键约束 (共 {len(foreign_keys)} 个):")
        for fk in foreign_keys:
            print(f"  - {fk[3]} -> {fk[2]}.{fk[4]}")
    
    # 显示示例数据（前3条）
    if count > 0:
        print(f"\n📄 示例数据 (前3条):")
        try:
            sample_data = cursor.execute(f"SELECT * FROM {table_name} LIMIT 3").fetchall()
            col_names = [col[1] for col in columns]
            
            # 计算每列的最大宽度
            max_widths = [len(name) for name in col_names]
            for row in sample_data:
                for i, val in enumerate(row):
                    max_widths[i] = max(max_widths[i], len(str(val)) if val is not None else 4)
            
            # 限制最大宽度
            max_widths = [min(w, 30) for w in max_widths]
            
            # 打印表头
            header = " | ".join([name[:max_widths[i]].ljust(max_widths[i]) for i, name in enumerate(col_names)])
            print("  " + header)
            print("  " + "-" * len(header))
            
            # 打印数据
            for row in sample_data:
                row_str = " | ".join([str(val)[:max_widths[i]].ljust(max_widths[i]) if val is not None else "NULL".ljust(max_widths[i]) for i, val in enumerate(row)])
                print("  " + row_str)
        except Exception as e:
            print(f"  无法显示示例数据: {e}")

# 显示数据库统计信息
print(f"\n{'=' * 80}")
print(f"📊 数据库统计")
print(f"{'=' * 80}")
for table in tables:
    table_name = table[0]
    count = cursor.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    print(f"  {table_name:<30} : {count:>6} 条记录")

conn.close()

print(f"\n{'=' * 80}")
print("✅ 数据库信息查看完成")
print(f"{'=' * 80}")

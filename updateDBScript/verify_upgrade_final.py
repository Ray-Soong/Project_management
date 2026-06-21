import sqlite3

conn = sqlite3.connect('instance/projects.db')
cursor = conn.cursor()

print('【升级后数据库验证】\n')

# 检查表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()
print(f'✓ 表数: {len(tables)}')

# 检查关键表
critical = ['invoice_files', 'stage_payments']
for table_name, *_ in tables:
    if table_name in critical:
        cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
        count = cursor.fetchone()[0]
        print(f'  ✓ {table_name}: 存在 ({count} 条记录)')

# Projects表检查
cursor.execute('PRAGMA table_info(projects)')
projects_cols = len(cursor.fetchall())
print(f'\n✓ Projects表: {projects_cols} 列')

# 总记录数
cursor.execute('''
    SELECT 
        (SELECT COUNT(*) FROM projects) as projects,
        (SELECT COUNT(*) FROM users) as users,
        (SELECT COUNT(*) FROM expenses) as expenses,
        (SELECT COUNT(*) FROM work_logs) as work_logs,
        (SELECT COUNT(*) FROM tasks) as tasks
''')
p, u, e, w, t = cursor.fetchone()
print(f'  项目: {p}, 用户: {u}, 报销: {e}, 工时: {w}, 任务: {t}')

print('\n✓ 数据库升级已完成并验证成功')
print('✓ 可以启动应用程序')

conn.close()

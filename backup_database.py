"""
数据库备份脚本
在清理前备份数据库
"""
import shutil
from datetime import datetime
import os

def backup_database():
    """备份数据库文件"""
    db_path = 'instance/projects.db'
    
    if not os.path.exists(db_path):
        print(f"错误: 数据库文件不存在 ({db_path})")
        return False
    
    # 创建备份目录
    backup_dir = 'instance/backups'
    os.makedirs(backup_dir, exist_ok=True)
    
    # 生成备份文件名（带时间戳）
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f'{backup_dir}/projects_backup_{timestamp}.db'
    
    try:
        # 复制数据库文件
        shutil.copy2(db_path, backup_path)
        file_size = os.path.getsize(backup_path) / 1024  # KB
        print("=" * 60)
        print("✓ 数据库备份成功!")
        print("=" * 60)
        print(f"备份文件: {backup_path}")
        print(f"文件大小: {file_size:.2f} KB")
        print(f"备份时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        return True
    except Exception as e:
        print(f"✗ 备份失败: {str(e)}")
        return False

if __name__ == '__main__':
    print("\n数据库备份工具\n")
    backup_database()
    print("\n提示: 备份完成后，可以运行 clean_database.py 进行数据清理")

from app import app, db
from sqlalchemy import text
from models import OperationLog

def migrate():
    with app.app_context():
        try:
            print("🔄 开始创建操作日志表...")
            
            # 创建操作日志表
            db.create_all()
            
            print("✅ 操作日志表创建成功！")
            
        except Exception as e:
            print(f"❌ 迁移失败: {e}")
            raise

if __name__ == '__main__':
    migrate()
"""
Add missing outsourcing_cost_without_tax column using Flask app context
"""
from app import app, db
from sqlalchemy import text

with app.app_context():
    try:
        # 使用原始SQL语句添加列
        db.session.execute(text("""
            ALTER TABLE projects
            ADD COLUMN outsourcing_cost_without_tax NUMERIC(10, 2) DEFAULT 0
        """))
        db.session.commit()
        print("✓ Column outsourcing_cost_without_tax added successfully")
    except Exception as e:
        if "duplicate column" in str(e) or "already exists" in str(e):
            print("✓ Column already exists")
        else:
            print(f"Error: {e}")
            db.session.rollback()

#!/usr/bin/env python3
"""
WSGI入口文件，用于生产环境部署
"""
import os
from app import app

# 设置环境变量
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('CONFIG_TYPE', 'docker')

if __name__ == "__main__":
    app.run()
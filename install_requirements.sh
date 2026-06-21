#!/bin/sh

# 项目管理系统 - 依赖安装脚本
# 适用于群晖 NAS 启动脚本

echo "开始安装 Python 依赖..."

# 获取脚本所在目录
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
cd "$SCRIPT_DIR"

# 检查 requirements.txt 是否存在
if [ ! -f "requirements.txt" ]; then
    echo "错误: 未找到 requirements.txt 文件"
    exit 1
fi

# 检查 Python 是否可用
if ! command -v python3 >/dev/null 2>&1; then
    echo "错误: 未找到 python3 命令"
    exit 1
fi

# 显示 Python 版本
echo "使用 Python 版本:"
python3 --version

# 升级 pip
echo "升级 pip..."
python3 -m pip install --upgrade pip || {
    echo "警告: pip 升级失败，继续安装..."
}

# 安装依赖
echo "安装依赖包..."
python3 -m pip install --no-cache-dir -r requirements.txt

# 检查安装结果
if [ $? -eq 0 ]; then
    echo "✓ 依赖安装成功!"
    echo "已安装的包:"
    python3 -m pip list | grep -E "Flask|SQLAlchemy|WTForms|Werkzeug|openpyxl"
else
    echo "✗ 依赖安装失败!"
    exit 1
fi

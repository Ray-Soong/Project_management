# SQLite 部署测试脚本

echo "=== 项目管理系统 SQLite 版本部署测试 ==="

# 检查必要文件
echo "检查必要的部署文件..."
files=("Dockerfile" "docker-compose.yml" "wsgi.py" "config_prod.py" "requirements.txt")

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file 存在"
    else
        echo "❌ $file 缺失"
    fi
done

# 检查配置
echo -e "\n检查配置..."
if grep -q "sqlite" docker-compose.yml; then
    echo "✅ docker-compose.yml 已配置 SQLite"
else
    echo "❌ docker-compose.yml 未配置 SQLite"
fi

if grep -q "sqlite" config_prod.py; then
    echo "✅ config_prod.py 已配置 SQLite"
else
    echo "❌ config_prod.py 未配置 SQLite"
fi

# 检查依赖
echo -e "\n检查依赖..."
if ! grep -q "psycopg2" requirements.txt; then
    echo "✅ 已移除 PostgreSQL 依赖"
else
    echo "❌ 仍包含 PostgreSQL 依赖"
fi

echo -e "\n=== 测试完成 ==="
echo "提示："
echo "1. 确保已安装 Docker 和 Docker Compose"
echo "2. 运行: docker-compose up -d --build"
echo "3. 访问: http://localhost 或 https://localhost"
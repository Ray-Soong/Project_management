# 数据库升级完整指南 (v2.0.0)

## 📋 目录
1. [快速开始](#快速开始)
2. [兼容性问题说明](#兼容性问题说明)
3. [详细步骤](#详细步骤)
4. [故障排除](#故障排除)
5. [验证清单](#验证清单)

## 快速开始

### 最快的方式（推荐）

```bash
# 1. 进入项目目录
cd d:\fay-works\十致科技\0904项目管理系统\project_mgmt-bak

# 2. 激活虚拟环境（如果需要）
.\venv\Scripts\Activate.ps1

# 3. 运行综合升级工具
python updateDBScript/comprehensive_db_upgrade.py

# 4. 根据输出检查是否成功
# 如果看到 "✓ 数据库已准备就绪" 表示升级成功

# 5. 启动应用
python app.py
```

### 分步升级（高级用户）

如果需要逐步控制升级过程：

```bash
# 步骤1: 同步数据库架构
python updateDBScript/sync_database_schema.py

# 步骤2: 验证升级
python updateDBScript/verify_upgrade.py

# 步骤3: 启动应用
python app.py
```

## 兼容性问题说明

### 常见问题

| 问题 | 原因 | 症状 | 解决方案 |
|------|------|------|---------|
| 缺失表 | 数据库版本过旧 | 应用无法启动，提示表不存在 | 运行升级工具自动创建 |
| 缺失列 | 字段定义更新但未同步 | 保存数据时出错 | 自动添加缺失列 |
| 孤立数据 | 外键约束不一致 | 数据异常或丢失 | 自动清理孤立记录 |
| 类型不匹配 | SQLite类型转换 | 数据显示异常 | 自动转换数据类型 |

### 为什么需要升级？

1. **模型更新** - models.py 增加了新字段
2. **新功能** - 发票、报销、供应商等功能需要新字段
3. **数据关系** - 需要修复外键约束
4. **兼容性** - 确保新旧代码能正常工作

## 详细步骤

### 准备工作

```bash
# 1. 停止应用程序
# 确保没有进程正在使用数据库

# 2. 检查Python环境（可选）
python --version  # 需要 3.7 以上

# 3. 创建备份（如果需要额外备份）
cp instance/projects.db instance/projects.db.manual_backup
```

### 执行升级

```bash
# 进入项目目录
cd d:\fay-works\十致科技\0904项目管理系统\project_mgmt-bak

# 运行升级脚本
python updateDBScript/comprehensive_db_upgrade.py
```

### 升级流程说明

脚本将按以下顺序执行：

1. **[1/6] 备份数据库**
   - 自动在 `instance/backups/` 目录创建备份
   - 备份文件名: `projects_backup_YYYYMMDD_HHMMSS.db`
   
2. **[2/6] 诊断数据库架构**
   - 检查所有必要的表是否存在
   - 检查每个表的所有列是否完整
   - 列出发现的问题
   
3. **[3/6] 修复数据库架构**
   - 创建缺失的表
   - 添加缺失的列
   - 自动提交更改
   
4. **[4/6] 清理孤立数据**
   - 删除指向不存在项目的工作日志
   - 删除指向不存在项目的报销
   - 保证数据关系一致
   
5. **[5/6] 验证数据完整性**
   - 检查必填字段
   - 验证外键约束
   - 报告任何数据异常
   
6. **[6/6] 生成升级报告**
   - 保存详细的升级报告
   - 显示升级摘要

### 升级完成后

```bash
# 验证升级是否成功
python updateDBScript/verify_upgrade.py

# 如果验证通过，启动应用
python app.py

# 在浏览器中打开应用
# http://localhost:5000
```

## 故障排除

### 问题1: 数据库文件不存在

**症状**: `✗ 错误: 数据库文件不存在`

**解决方案**:
```bash
# 确保在项目根目录运行脚本
pwd  # 检查当前目录

# 如果 instance/projects.db 不存在，运行初始化：
python
```python
from app import app, db
with app.app_context():
    db.create_all()
exit()
```
```

### 问题2: 权限拒绝

**症状**: `✗ 备份失败: Permission denied`

**解决方案**:
```bash
# 以管理员身份运行PowerShell
# 右键点击 PowerShell 选择 "以管理员身份运行"

# 或检查文件权限
icacls instance/projects.db

# 如果需要，修改权限：
icacls instance/projects.db /grant:r $env:USERNAME:F
```

### 问题3: 升级后应用无法启动

**症状**: 应用启动但报表或功能出错

**解决方案**:
```bash
# 1. 查看应用日志
python app.py  # 查看控制台输出

# 2. 回滚到备份（如果升级失败）
cp instance/backups/projects_backup_YYYYMMDD_HHMMSS.db instance/projects.db

# 3. 运行验证脚本
python updateDBScript/verify_upgrade.py

# 4. 如果仍有问题，检查特定表
python
```python
from app import app, db
from models import Project, User, Expense
with app.app_context():
    # 检查表是否存在
    print(f"Projects: {Project.query.count()}")
    print(f"Users: {User.query.count()}")
    print(f"Expenses: {Expense.query.count()}")
exit()
```
```

### 问题4: 升级过程中超时

**症状**: 脚本运行很久没有反应

**解决方案**:
```bash
# 1. 检查数据库大小
ls -lh instance/projects.db

# 2. 如果数据库很大（>100MB），可能需要更长时间
# 继续等待...

# 3. 如果确实超时，可以中断（Ctrl+C）并：
# - 检查备份是否已创建
# - 验证数据库是否被修改
python updateDBScript/verify_upgrade.py
```

## 验证清单

升级完成后，按以下清单验证：

### 数据库检查
- [ ] 备份文件已创建在 `instance/backups/`
- [ ] 升级报告已生成
- [ ] 数据库大小合理（增加不超过 50%）
- [ ] 可以成功连接数据库

### 应用启动
- [ ] 应用可以启动 (python app.py)
- [ ] 没有数据库相关的错误信息
- [ ] 可以打开首页 (http://localhost:5000)
- [ ] 登录功能正常

### 功能测试
- [ ] 可以查看项目列表
- [ ] 可以创建新项目
- [ ] 可以添加工作日志
- [ ] 可以提交报销
- [ ] 可以上传文件和附件
- [ ] 可以查看发票和收据

### 数据完整性
- [ ] 历史数据仍然存在
- [ ] 用户账户可以登录
- [ ] 项目与任务关联正确
- [ ] 报销与项目关联正确

## 自动回滚

如果升级出现问题，可以自动回滚：

```bash
# 查看备份列表
ls instance/backups/

# 回滚到最新备份
cp instance/backups/projects_backup_LATEST.db instance/projects.db

# 或使用rollback脚本（如果可用）
python updateDBScript/rollback_database.py
```

## 联系支持

如果遇到问题：

1. 查看升级报告: `instance/backups/upgrade_report_*.txt`
2. 检查应用日志: 终端输出信息
3. 确保备份文件安全
4. 联系技术支持提供以下信息：
   - 升级报告内容
   - 应用日志截图
   - 问题描述和复现步骤

---

**最后更新**: 2026-06-09  
**版本**: v2.0.0  
**维护者**: 项目管理系统开发团队

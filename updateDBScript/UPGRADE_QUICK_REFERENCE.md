# 数据库升级快速参考

## ⚡ 一键升级（推荐）

```bash
# 1. 进入项目目录
cd d:\fay-works\十致科技\0904项目管理系统\project_mgmt-bak

# 2. 运行升级（自动处理一切）
python updateDBScript/final_db_upgrade.py

# 3. 验证结果
python verify_upgrade_final.py

# 4. 启动应用
python app.py
```

---

## 📋 可用工具

### 🔍 诊断工具
```bash
python updateDBScript/diagnostic_check.py
# 用途: 检查数据库状态（只读，不修改任何内容）
# 显示: 表数、记录数、数据关系、完整性检查
```

### 🔧 升级工具
```bash
python updateDBScript/final_db_upgrade.py
# 用途: 完整的升级和修复（推荐使用）
# 功能: 备份、诊断、修复、验证、报告
```

### ⚙️ 高级工具
```bash
python updateDBScript/comprehensive_db_upgrade.py
# 用途: 综合升级（处理所有类型的问题）

python updateDBScript/advanced_db_migration.py
# 用途: 高级迁移（处理复杂的NOT NULL列）
```

---

## 🎯 常见场景

### 场景1: 只想检查数据库状态
```bash
python updateDBScript/diagnostic_check.py
```
✅ 不会修改任何数据  
✅ 快速显示当前状态

### 场景2: 数据库可能有问题，需要修复
```bash
python updateDBScript/final_db_upgrade.py
```
✅ 自动备份  
✅ 诊断问题  
✅ 自动修复  
✅ 生成报告

### 场景3: 升级失败，需要恢复
```bash
# 1. 查看可用备份
dir instance\backups\*.db

# 2. 恢复到某个备份
copy instance\backups\projects_backup_final_YYYYMMDD_HHMMSS.db instance\projects.db

# 3. 重新尝试升级
python updateDBScript/final_db_upgrade.py
```

### 场景4: 需要详细的诊断信息
```bash
python updateDBScript/diagnostic_check.py
# 查看详细的表结构、列定义、数据统计
```

---

## 📊 升级前后对比

### 升级前
```
问题:
  ⚠️  缺失 invoice_files 表
  ⚠️  缺失 stage_payments 表（实际存在）

状态:
  ❌ 不完整
```

### 升级后 ✅
```
修复:
  ✅ invoice_files 表已创建
  ✅ stage_payments 表确认存在
  ✅ 所有数据完整

状态:
  ✅ 完全就绪
```

---

## 🔄 升级流程图

```
诊断问题
    ↓
备份数据库
    ↓
修复架构
    ↓
清理孤立数据
    ↓
验证完整性
    ↓
生成报告
    ↓
✅ 完成
```

---

## 💾 备份管理

### 查看备份
```bash
dir instance\backups\
# 或
ls -la instance/backups/
```

### 恢复备份
```bash
# 方法1: 复制文件
copy instance\backups\projects_backup_final_YYYYMMDD_HHMMSS.db instance\projects.db

# 方法2: Python脚本
python
>>> import shutil
>>> shutil.copy('instance/backups/projects_backup_final_YYYYMMDD_HHMMSS.db', 'instance/projects.db')
```

### 删除旧备份
```bash
# 只保留最近的备份
del instance\backups\projects_backup_20260609_201116.db
```

---

## ✅ 验证清单

升级完成后，验证以下内容：

- [ ] 运行诊断工具，确认无问题
- [ ] 检查备份文件是否存在
- [ ] 启动应用程序
- [ ] 打开浏览器访问应用
- [ ] 测试主要功能（登录、查看项目、添加数据）
- [ ] 检查应用日志中无错误

---

## 🆘 快速故障排除

| 问题 | 症状 | 解决方案 |
|------|------|---------|
| **连接失败** | "无法打开数据库" | 检查 instance/projects.db 是否存在 |
| **权限拒绝** | "Permission denied" | 以管理员身份运行终端 |
| **升级失败** | 脚本报错 | 运行诊断工具，查看错误信息 |
| **应用崩溃** | "数据库错误" | 恢复备份，查看应用日志 |
| **性能变慢** | 查询缓慢 | 检查数据库大小，考虑优化 |

---

## 📖 详细文档

- **完整指南**: [DATABASE_UPGRADE_COMPLETION.md](DATABASE_UPGRADE_COMPLETION.md)
- **详细步骤**: [DB_UPGRADE_GUIDE_v2.md](updateDBScript/DB_UPGRADE_GUIDE_v2.md)
- **工具说明**: [TOOLS_README.md](updateDBScript/TOOLS_README.md)

---

## 🎓 学习资源

### 了解数据库结构
```bash
# 查看所有表
python -c "import sqlite3; conn = sqlite3.connect('instance/projects.db'); cursor = conn.cursor(); cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\"'); print('\n'.join(str(t[0]) for t in cursor.fetchall()))"
```

### 检查特定表
```bash
python -c "import sqlite3; conn = sqlite3.connect('instance/projects.db'); cursor = conn.cursor(); cursor.execute('PRAGMA table_info(projects)'); print('\n'.join(str(c) for c in cursor.fetchall()))"
```

### 查看记录数
```bash
python -c "import sqlite3; conn = sqlite3.connect('instance/projects.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM projects'); print(f'项目总数: {cursor.fetchone()[0]}')"
```

---

## ⏱️ 预期耗时

| 操作 | 耗时 |
|------|------|
| 诊断检查 | 几秒钟 |
| 完整升级 | < 1 分钟 |
| 数据验证 | 几秒钟 |
| 备份恢复 | < 10 秒 |

---

## 📞 需要帮助？

1. **运行诊断**: `python updateDBScript/diagnostic_check.py`
2. **查看报告**: `instance/backups/upgrade_*.txt`
3. **检查日志**: 应用启动时的控制台输出
4. **恢复备份**: `copy instance\backups\*.db instance\projects.db`

---

## 🎉 升级成功后

```bash
# 启动应用
python app.py

# 在浏览器中打开
# http://localhost:5000

# 登录并使用应用
# 所有功能应该正常工作
```

---

**最后更新**: 2026-06-09  
**版本**: v3.0.0  
**状态**: ✅ 完成

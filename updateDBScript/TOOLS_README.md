# 项目管理系统 - 数据库升级工具套件 v2.0.0

## 📌 概述

本目录包含用于诊断和升级 `projects.db` 数据库的完整工具套件。这些工具可以：
- 📊 诊断数据库兼容性问题
- 🔧 自动修复架构不兼容
- 🗑️ 清理孤立数据
- ✅ 验证数据完整性
- 📝 生成详细报告

---

## 🚀 快速开始

### 最简单的方式 - 一键升级

```bash
# 进入项目目录
cd d:\fay-works\十致科技\0904项目管理系统\project_mgmt-bak

# 运行升级工具（自动处理所有问题）
python updateDBScript/comprehensive_db_upgrade.py
```

这将自动：
1. 备份当前数据库
2. 诊断所有问题
3. 修复兼容性问题
4. 清理孤立数据
5. 验证数据完整性
6. 生成升级报告

### 验证结果

```bash
# 查看诊断信息（不修改任何数据）
python updateDBScript/diagnostic_check.py

# 如果升级成功，启动应用
python app.py
```

---

## 🛠️ 可用工具列表

### 1. **comprehensive_db_upgrade.py** - 综合升级工具 ⭐ 推荐

**用途**: 完整的数据库升级和修复

**功能**:
- ✓ 自动备份数据库
- ✓ 诊断架构问题（缺失表、缺失列）
- ✓ 自动修复问题
- ✓ 清理孤立数据
- ✓ 验证数据完整性
- ✓ 生成升级报告

**使用方法**:
```bash
python updateDBScript/comprehensive_db_upgrade.py
```

**输出示例**:
```
======================================================================
                    综合数据库升级工具
                    版本 v2.0.0
======================================================================

[1/6] 备份数据库...
  ✓ 备份成功
  ✓ 备份文件: instance/backups/projects_backup_20260609_120000.db
  ✓ 备份大小: 2.50 MB

[2/6] 诊断数据库架构...
  ✓ 发现现有列数: 35
  ✓ 期望列数: 38
  ⚠️  发现缺失的列: 3
    - accounts_receivable
    - current_invoice_amount
    - invoice_amount_issued

[3/6] 修复数据库架构...
  ✓ 添加列: accounts_receivable
  ✓ 添加列: current_invoice_amount
  ✓ 添加列: invoice_amount_issued
  ✓ 修复了 3 个问题

[4/6] 清理孤立数据...
  ✓ 无孤立数据

[5/6] 验证数据完整性...
  ✓ 数据完整性检查通过

[6/6] 生成升级报告...
  ✓ 报告已保存到: instance/backups/upgrade_report_20260609_120000.txt

======================================================================
                ✓ 数据库已准备就绪，可以启动应用程序
======================================================================
```

---

### 2. **diagnostic_check.py** - 诊断工具

**用途**: 快速检查数据库状态（只读，不修改任何内容）

**功能**:
- ✓ 检查数据库文件状态
- ✓ 显示所有表和记录数
- ✓ 详细检查Projects表
- ✓ 检查Users表
- ✓ 检查数据关系
- ✓ 识别孤立数据
- ✓ 检查外键约束

**使用方法**:
```bash
python updateDBScript/diagnostic_check.py
```

**输出示例**:
```
==================================================
            数据库快速诊断工具
            版本 v1.0.0
==================================================

【数据库文件】
--------------------------------------------------
✓ 文件存在: instance/projects.db
  大小: 2.50 MB (2,621,440 字节)
  最后修改: 2026-06-09 12:00:00

【数据库表】
--------------------------------------------------
✓ 发现 8 个表:
  - expenses: 45 条记录
  - expense_items: 120 条记录
  - invoices: 10 条记录
  - projects: 25 条记录
  - project_assignments: 35 条记录
  - tasks: 80 条记录
  - users: 8 条记录
  - work_logs: 150 条记录

【Projects表详情】
--------------------------------------------------
✓ 列数: 38
✓ 记录数: 25
  项目状态类型: 4
  项目经理数: 3
  
  按状态统计:
    - 进行中: 12
    - 已结算: 8
    - 验收中: 3
    - 启动中: 2

【诊断摘要】
--------------------------------------------------
✓ 表数: 8
✓ 总记录数: 473

【建议】
--------------------------------------------------
✓ 如果上面没有红色 ✗，数据库状态良好
✗ 如果有红色 ✗，运行升级工具:
  python updateDBScript/comprehensive_db_upgrade.py
⚠️  如果有黄色 ⚠️，可能需要清理数据
```

---

### 3. **sync_database_schema.py** - 架构同步工具

**用途**: 针对Project表进行架构同步（旧版本）

**功能**:
- ✓ 同步Projects表字段
- ✓ 添加缺失的列
- ✓ 设置默认值
- ✓ 验证更新结果

**使用方法**:
```bash
python updateDBScript/sync_database_schema.py
```

**何时使用**: 如果only需要同步Projects表字段

---

### 4. **upgrade_database.py** - 文件管理升级

**用途**: 报销系统文件管理升级（v1.1.0）

**功能**:
- ✓ 添加 receipt_original_name 字段
- ✓ 修复旧文件扩展名
- ✓ 支持压缩包格式

**使用方法**:
```bash
python updateDBScript/upgrade_database.py
```

---

### 5. **verify_upgrade.py** - 验证工具

**用途**: 验证升级是否成功

**功能**:
- ✓ 检查升级结果
- ✓ 验证数据完整性
- ✓ 生成验证报告

**使用方法**:
```bash
python updateDBScript/verify_upgrade.py
```

---

## 📋 完整升级流程

### 推荐方案（一键升级）

```bash
# 1. 进入项目目录
cd d:\fay-works\十致科技\0904项目管理系统\project_mgmt-bak

# 2. 激活虚拟环境（如果使用）
.\venv\Scripts\Activate.ps1

# 3. 运行综合升级工具
python updateDBScript/comprehensive_db_upgrade.py

# 4. 验证结果（可选）
python updateDBScript/diagnostic_check.py

# 5. 启动应用
python app.py

# 6. 在浏览器打开
# http://localhost:5000
```

### 分步方案（高级用户）

```bash
# 步骤1: 诊断问题
python updateDBScript/diagnostic_check.py

# 步骤2: 根据问题选择升级工具
# 如果要全面升级：
python updateDBScript/comprehensive_db_upgrade.py

# 或针对特定功能升级：
python updateDBScript/sync_database_schema.py
python updateDBScript/upgrade_database.py

# 步骤3: 验证升级
python updateDBScript/verify_upgrade.py

# 步骤4: 启动应用
python app.py
```

---

## 🔍 数据库兼容性问题说明

### 常见问题及解决方案

| 问题 | 症状 | 解决方案 |
|------|------|---------|
| **缺失表** | 应用无法启动 | comprehensive_db_upgrade.py |
| **缺失列** | 保存时出错 | comprehensive_db_upgrade.py |
| **孤立数据** | 数据异常 | comprehensive_db_upgrade.py |
| **外键不一致** | 关联数据错误 | comprehensive_db_upgrade.py |
| **类型不匹配** | 数据显示异常 | comprehensive_db_upgrade.py |

### 升级前的数据库结构问题

旧版本的数据库可能存在：

1. **缺失新功能的表**:
   - `invoice_files` - 发票文件表
   - 其他新增功能表

2. **缺失字段**:
   - `project.accounts_receivable` - 应收账款
   - `project.current_invoice_amount` - 当前发票金额
   - `project.invoice_amount_issued` - 已开发票金额
   - `expense_items.receipt_original_name` - 收据原始文件名
   - 其他新功能字段

3. **数据关系问题**:
   - 孤立的工作日志（指向已删除的项目）
   - 孤立的报销（指向已删除的项目）
   - 外键约束不一致

---

## ⚠️ 安全性说明

### 备份管理

所有升级工具都会自动备份数据库：

```bash
# 查看备份文件
ls -la instance/backups/

# 备份文件名格式
projects_backup_YYYYMMDD_HHMMSS.db

# 恢复备份
cp instance/backups/projects_backup_YYYYMMDD_HHMMSS.db instance/projects.db
```

### 权限要求

- ✓ 对 `instance/projects.db` 的读写权限
- ✓ 对 `instance/backups/` 目录的写权限
- ✓ 足够的磁盘空间（至少是数据库大小的 3 倍）

### 错误恢复

如果升级失败：

```bash
# 1. 查看升级报告
cat instance/backups/upgrade_report_*.txt

# 2. 回滚到备份
cp instance/backups/projects_backup_LATEST.db instance/projects.db

# 3. 联系支持或重新运行升级
```

---

## 📊 升级对数据的影响

| 操作 | 数据库 | 数据 | 文件 |
|------|--------|------|------|
| 诊断检查 | 无修改 | 无修改 | 无修改 |
| 综合升级 | 修改表结构 | 保留所有现有数据 | 无修改 |
| 清理孤立 | 无修改 | 删除孤立记录 | 无修改 |
| 备份恢复 | 完全恢复 | 完全恢复 | 无修改 |

---

## 🆘 故障排除

### 问题1: 文件权限问题

```bash
# 检查权限
icacls instance/projects.db

# 修复权限（Windows）
icacls instance/projects.db /grant:r %USERNAME%:F

# 或以管理员身份运行PowerShell
```

### 问题2: 数据库被锁定

```bash
# 确保应用程序已关闭
# 检查是否有其他进程在使用数据库

# 如果仍被锁定，重启计算机或使用管理员权限
```

### 问题3: 磁盘空间不足

```bash
# 检查磁盘空间
dir C:\

# 如果空间不足：
# 1. 删除旧备份（instance/backups/ 中的旧文件）
# 2. 清理垃圾文件
# 3. 重新运行升级
```

### 问题4: 升级后应用无法启动

```bash
# 1. 查看应用日志
python app.py  # 查看错误信息

# 2. 验证升级
python updateDBScript/diagnostic_check.py

# 3. 回滚
cp instance/backups/projects_backup_LATEST.db instance/projects.db

# 4. 重新升级
python updateDBScript/comprehensive_db_upgrade.py
```

---

## 📚 相关文档

- [完整升级指南](DB_UPGRADE_GUIDE_v2.md) - 详细步骤和故障排除
- [数据库升级指南](DATABASE_UPGRADE_GUIDE.md) - v1.1.0 版本信息
- [报销系统更新](报销系统更新说明_20260118.md) - 报销功能变更
- [用户权限系统](用户权限系统说明.md) - 权限管理说明

---

## 📞 支持

如需帮助：

1. 查看升级报告: `instance/backups/upgrade_report_*.txt`
2. 运行诊断: `python updateDBScript/diagnostic_check.py`
3. 检查日志: 应用启动时的控制台输出
4. 联系技术支持并提供上述信息

---

## 📝 版本历史

| 版本 | 日期 | 工具 | 功能 |
|------|------|------|------|
| v2.0.0 | 2026-06-09 | comprehensive_db_upgrade.py | 综合升级和诊断 |
| v1.0.0 | 2026-05-26 | diagnostic_check.py | 快速诊断 |
| v1.1.0 | 2026-02-07 | upgrade_database.py | 文件管理升级 |
| v1.0.0 | 2026-01-18 | sync_database_schema.py | 架构同步 |

---

**最后更新**: 2026-06-09  
**维护者**: 项目管理系统开发团队

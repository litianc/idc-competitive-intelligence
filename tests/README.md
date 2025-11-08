# 测试文件说明

## 目录结构

```
tests/
├── test_category_classifier.py      # 分类器单元测试
├── test_database.py                 # 数据库单元测试
├── test_idcquan_scraper.py          # IDC圈采集器测试
├── test_llm_analyzer.py             # LLM分析器测试
├── test_new_8_sources.py            # 新8个数据源测试
├── test_scheduler.py                # 调度器测试
├── test_all_email_fixes.py          # 邮件修复完整测试 ⭐
├── test_both_fixes.py               # 双修复综合测试
├── test_email_mime_structure.py     # MIME结构测试
├── test_email_recipient_fix.py      # 收件人格式测试
├── test_email_with_pdf.py           # PDF附件测试
├── test_pdf_emoji.py                # PDF emoji测试
├── test_pdf_generation.py           # PDF生成测试
├── test_weekly_summary.py           # 周报摘要测试
└── test_scheduler_command.sh        # 定时任务命令测试
```

---

## 运行测试

### ⚠️ 重要：从项目根目录运行

所有测试脚本需要从项目根目录运行，而不是在 tests/ 目录内运行。

### 正确的运行方式

```bash
# 在项目根目录运行
cd /root/competitive-intelligence-web

# 运行单个测试
python3 tests/test_all_email_fixes.py

# 运行周报摘要测试
python3 tests/test_weekly_summary.py

# 运行PDF生成测试
python3 tests/test_pdf_generation.py

# 运行Shell脚本测试
bash tests/test_scheduler_command.sh
```

### ❌ 错误的运行方式

```bash
# 不要在 tests/ 目录内运行
cd tests
python3 test_all_email_fixes.py  # ❌ 会报错：ModuleNotFoundError
```

---

## 测试分类

### 1. 核心功能完整测试 ⭐

**最重要的测试，验证所有修复：**
```bash
python3 tests/test_all_email_fixes.py
```

**期望输出：**
```
✓ 通过  苹果邮件MIME结构
✓ 通过  收件人地址格式
✓ 通过  PDF emoji显示
✓ 通过  完整邮件结构
通过率: 4/4
🎉 所有测试通过！
```

### 2. 邮件功能测试

```bash
# MIME结构测试（苹果邮件兼容性）
python3 tests/test_email_mime_structure.py

# 收件人格式测试
python3 tests/test_email_recipient_fix.py

# 邮件附件测试
python3 tests/test_email_with_pdf.py
```

### 3. PDF功能测试

```bash
# PDF生成测试
python3 tests/test_pdf_generation.py

# PDF emoji显示测试
python3 tests/test_pdf_emoji.py
```

### 4. LLM摘要测试

```bash
# 周报摘要生成测试
python3 tests/test_weekly_summary.py
```

### 5. 定时任务测试

```bash
# 模拟定时任务执行
bash tests/test_scheduler_command.sh
```

### 6. 单元测试

```bash
# 数据库测试
python3 tests/test_database.py

# 分类器测试
python3 tests/test_category_classifier.py

# LLM分析器测试
python3 tests/test_llm_analyzer.py
```

---

## 测试覆盖的功能

### ✅ 已修复的问题

1. **苹果邮件只显示附件不显示正文**
   - 测试：`test_email_mime_structure.py`
   - 修复：MIME类型动态选择（mixed/alternative）

2. **邮件收件人显示@domain.invalid**
   - 测试：`test_email_recipient_fix.py`
   - 修复：移除Header()包装

3. **PDF中emoji不显示**
   - 测试：`test_pdf_emoji.py`
   - 修复：安装emoji字体 + CSS字体回退

### ✅ 新增的功能

1. **LLM智能摘要**
   - 测试：`test_weekly_summary.py`
   - 功能：整体总结 + 板块点评

2. **PDF生成**
   - 测试：`test_pdf_generation.py`
   - 功能：HTML转PDF + 中文支持

3. **PDF邮件附件**
   - 测试：`test_email_with_pdf.py`
   - 功能：自动附加PDF到邮件

---

## 快速验证

### 验证所有修复是否生效

```bash
# 运行完整测试套件
python3 tests/test_all_email_fixes.py

# 如果看到这个输出，说明一切正常：
# 🎉 所有测试通过！
```

### 验证定时任务兼容性

```bash
# 模拟定时任务会执行的命令
bash tests/test_scheduler_command.sh
```

---

## 故障排查

### 问题1: ModuleNotFoundError: No module named 'src'

**原因：** 在 tests/ 目录内运行测试

**解决：** 返回项目根目录运行
```bash
cd /root/competitive-intelligence-web
python3 tests/test_all_email_fixes.py
```

### 问题2: 测试失败

**排查步骤：**
```bash
# 1. 查看详细文档
cat docs/troubleshooting.md

# 2. 检查环境配置
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('LLM_API_KEY:', 'configured' if os.getenv('LLM_API_KEY') else 'not set')
print('SMTP_USER:', os.getenv('SMTP_USER') or 'not set')
"

# 3. 验证字体安装
fc-list :lang=zh | wc -l  # 应该 > 0
fc-list | grep emoji       # 应该有 Noto Color Emoji
```

---

## 相关文档

- [故障排查指南](../docs/troubleshooting.md)
- [所有修复总结](../docs/ALL_FIXES_SUMMARY.md)
- [快速参考](../docs/QUICK_FIX_REFERENCE.md)
- [定时任务状态](../docs/SCHEDULER_STATUS.md)

---

**最后更新：** 2025-11-08

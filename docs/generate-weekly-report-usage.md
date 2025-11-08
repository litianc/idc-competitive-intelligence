# generate_weekly_report.py 使用说明

## 功能概述

`generate_weekly_report.py` 是主要的周报生成和发送脚本，集成了以下功能：
- ✅ 生成 Markdown 格式周报
- ✅ 自动生成 HTML 邮件格式
- ✅ 自动生成 PDF 附件
- ✅ LLM 智能摘要（整体总结 + 板块点评）
- ✅ 发送带 PDF 附件的邮件
- ✅ 多样化的命令行选项

## 快速开始

### 基础用法

```bash
# 1. 生成周报（Markdown + HTML + PDF）
python3 generate_weekly_report.py

# 2. 生成并发送邮件（带PDF附件）
python3 generate_weekly_report.py --send-email

# 3. 仅发送邮件，不保存本地文件
python3 generate_weekly_report.py --email-only
```

### 生成的文件

默认情况下，脚本会在 `reports/` 目录生成以下文件：

```
reports/
├── weekly_report.md                    # Markdown格式周报
├── weekly_report.html                  # HTML格式（用于邮件正文）
└── IDC周报_第45周_2025-11-08.pdf       # PDF格式（邮件附件）
```

## 命令行选项

### 统计天数

```bash
# 统计最近7天（默认）
python3 generate_weekly_report.py

# 统计最近14天
python3 generate_weekly_report.py --days 14

# 统计最近30天
python3 generate_weekly_report.py --days 30
```

### 数据库路径

```bash
# 使用默认数据库
python3 generate_weekly_report.py

# 指定数据库路径
python3 generate_weekly_report.py --db /path/to/intelligence.db
```

### 输出文件路径

```bash
# 使用默认路径（reports/weekly_report.md）
python3 generate_weekly_report.py

# 自定义输出路径
python3 generate_weekly_report.py --output reports/custom_report.md
```

### 邮件发送

```bash
# 生成周报并发送邮件
python3 generate_weekly_report.py --send-email

# 仅发送邮件，不保存本地文件（适合自动化任务）
python3 generate_weekly_report.py --email-only
```

### PDF 生成控制

```bash
# 生成周报时不生成PDF（节省时间）
python3 generate_weekly_report.py --no-pdf

# 发送邮件时不附加PDF
python3 generate_weekly_report.py --send-email --no-pdf
```

### LLM 摘要控制

```bash
# 不使用LLM生成摘要（使用统计型摘要）
python3 generate_weekly_report.py --no-llm

# 组合使用：无LLM、无PDF、快速生成
python3 generate_weekly_report.py --no-llm --no-pdf
```

## 完整参数列表

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--days N` | 统计最近N天的数据 | 7 |
| `--db PATH` | 数据库文件路径 | data/intelligence.db |
| `--output PATH` | 输出文件路径 | reports/weekly_report.md |
| `--send-email` | 生成后发送邮件 | False |
| `--email-only` | 仅发送邮件，不保存文件 | False |
| `--no-pdf` | 不生成PDF文件 | False |
| `--no-llm` | 不使用LLM生成摘要 | False |

## 使用场景

### 场景1：本地生成周报（用于审阅）

```bash
python3 generate_weekly_report.py
```

**生成内容：**
- ✅ Markdown 周报（用于编辑）
- ✅ HTML 周报（预览邮件效果）
- ✅ PDF 周报（离线分享）

**用途：**
- 审阅周报内容
- 编辑 Markdown 后重新生成
- 下载 PDF 用于会议

### 场景2：定时自动发送周报

```bash
# 在 crontab 中设置
0 17 * * 5 cd /path/to/project && python3 generate_weekly_report.py --email-only
```

**说明：**
- 每周五 17:00 自动执行
- 直接发送邮件，不保存本地文件
- 自动生成 PDF 附件

### 场景3：手动审核后发送

```bash
# 步骤1: 生成周报
python3 generate_weekly_report.py

# 步骤2: 审核编辑 reports/weekly_report.md

# 步骤3: 重新生成并发送
python3 generate_weekly_report.py --send-email
```

### 场景4：快速生成（测试用）

```bash
# 不生成PDF和LLM摘要，快速生成
python3 generate_weekly_report.py --no-pdf --no-llm
```

**适用场景：**
- 测试数据采集结果
- 快速查看文章统计
- 调试周报格式

## 输出示例

### 终端输出

```
================================================================================
IDC行业竞争情报系统 - 周报生成
================================================================================

✓ 数据库连接成功: data/intelligence.db
✓ 数据库中共有 115 篇文章

文章来源分布:
  中国IDC圈: 45 篇
  36氪: 30 篇
  量子位: 20 篇
  云头条: 15 篇
  工业和信息化部: 5 篇

================================================================================
开始生成周报（统计最近 7 天）...
================================================================================

✓ LLM摘要生成成功
✓ 周报已生成!
✓ Markdown: reports/weekly_report.md
✓ HTML:     reports/weekly_report.html
✓ PDF:      reports/IDC周报_第45周_2025-11-08.pdf (780.4 KB)

================================================================================
周报预览（前30行）:
================================================================================
# IDC行业周报 | 2025年第45周

**报告日期**: 2025年11月08日
...

================================================================================
开始发送邮件...
================================================================================

✓ 邮件发送成功！
✓ 收件人: recipient@example.com
✓ 已附加PDF文件

================================================================================
周报生成完成！
================================================================================
```

## 环境配置

### 必需配置

在 `.env` 文件中配置以下选项：

```bash
# 数据库
DATABASE_PATH=data/intelligence.db

# LLM API（用于智能摘要）
LLM_API_KEY=your_api_key_here
LLM_API_BASE=https://api.your-provider.com
LLM_MODEL=gpt-4-turbo-preview

# 邮件配置
SMTP_HOST=smtp.163.com
SMTP_PORT=465
SMTP_USER=your_email@163.com
SMTP_PASS=your_auth_code
EMAIL_RECIPIENTS=recipient1@example.com,recipient2@example.com

# 功能开关
WEEKLY_SUMMARY_ENABLED=true     # LLM摘要
PDF_ENABLED=true                # PDF生成
```

### 可选配置

```bash
# LLM摘要
WEEKLY_INSIGHT_LABEL_RANDOM=true

# PDF设置
PDF_PAGE_SIZE=A4
PDF_MARGIN=20mm
PDF_PRINT_BACKGROUND=true
PDF_DISPLAY_HEADER_FOOTER=true
```

## 错误处理

### 数据库不存在

```
✗ 数据库文件不存在: data/intelligence.db
  请先运行数据采集: python3 run_collection.py
```

**解决方案：** 先运行数据采集脚本

### LLM API 失败

```
⚠️  LLM摘要生成失败: API调用超时，使用默认摘要
```

**说明：** 自动降级为统计型摘要，不影响周报生成

### PDF 生成失败

```
⚠️  PDF生成失败（但不影响其他文件）
```

**说明：** Markdown 和 HTML 正常生成，仅 PDF 失败

### 邮件发送失败

```
✗ 邮件发送失败！请检查邮箱配置。
```

**检查项：**
1. SMTP 配置是否正确
2. 邮箱授权码是否有效
3. 网络连接是否正常

## 集成到定时任务

### Linux/Mac (crontab)

```bash
# 编辑 crontab
crontab -e

# 添加定时任务（每周五 17:00）
0 17 * * 5 cd /path/to/competitive-intelligence-web && /usr/bin/python3 generate_weekly_report.py --email-only >> logs/weekly_report.log 2>&1
```

### Windows (任务计划程序)

1. 打开"任务计划程序"
2. 创建基本任务
3. 触发器：每周五 17:00
4. 操作：启动程序
   - 程序：`python.exe`
   - 参数：`generate_weekly_report.py --email-only`
   - 起始位置：项目目录

## 常见问题

### Q: 如何只生成PDF不发送邮件？

A: 默认行为就是生成文件：
```bash
python3 generate_weekly_report.py
```

### Q: 如何测试邮件发送不实际发送？

A: 使用测试脚本：
```bash
python3 test_email_with_pdf.py
```

### Q: 生成的PDF太大怎么办？

A: 检查以下几点：
- 统计天数是否过多（建议 ≤ 14 天）
- 是否有大量高评分文章
- 考虑使用 `--days 7` 限制范围

### Q: 能否自定义收件人？

A: 两种方式：

1. 修改 `.env`：
```bash
EMAIL_RECIPIENTS=user1@example.com,user2@example.com
```

2. 代码中调用（不推荐）

### Q: 周报内容有误如何修改？

A: 工作流程：
```bash
# 1. 生成周报
python3 generate_weekly_report.py

# 2. 编辑 Markdown
vim reports/weekly_report.md

# 3. 重新生成 HTML 和 PDF
# （需要手动运行）
```

## 相关脚本

- `test_weekly_summary.py` - 测试 LLM 摘要功能
- `test_pdf_generation.py` - 测试 PDF 生成功能
- `test_email_with_pdf.py` - 测试邮件附件功能
- `run_collection.py` - 数据采集脚本

## 更多信息

- [LLM 摘要功能文档](./weekly-summary-feature.md)
- [PDF 生成功能文档](./pdf-generation-feature.md)
- [项目总体说明](../README.md)

---

最后更新：2025-11-08

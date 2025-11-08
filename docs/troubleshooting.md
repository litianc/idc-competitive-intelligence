# 常见问题排查指南

## 快速诊断

遇到问题？先运行完整测试套件：

```bash
# 测试所有邮件相关功能
python3 test_all_email_fixes.py

# 应该显示: 🎉 所有测试通过！
```

如果测试未通过，查看下方对应问题的解决方案。

---

## 已解决的问题

### 1. ✅ PDF 中文显示乱码

**问题描述：** 生成的 PDF 文件中中文显示为方块或乱码

**错误信息：** 无明显错误，但 PDF 中中文不可读

**解决方案：**
```bash
# 安装中文字体
sudo apt-get install -y fonts-noto-cjk fonts-wqy-zenhei fonts-wqy-microhei

# 验证安装
fc-list :lang=zh
```

**详细说明：** 见 [pdf-chinese-font-fix.md](./pdf-chinese-font-fix.md)

**修复位置：** `src/reporting/pdf_generator.py`

---

### 2. ✅ 周报摘要生成失败: argument of type 'NoneType' is not iterable

**问题描述：** 生成周报时报错 "argument of type 'NoneType' is not iterable"

**错误信息：**
```
✗ 周报摘要生成失败: argument of type 'NoneType' is not iterable
```

**根本原因：** 数据库中某些文章的 `category` 字段为 `None`，在字符串比较时出错

**解决方案：** 在所有使用 `in category_key` 的地方添加 `None` 检查

**修复代码：**
```python
# 修复前（错误）
if '政策' in category_key:

# 修复后（正确）
if cat_key and '政策' in str(cat_key):
```

**修复位置：**
- `src/reporting/report_summarizer.py` 第 186 行
- `src/reporting/report_summarizer.py` 第 378-385 行

**验证方法：**
```bash
python3 test_weekly_summary.py
# 应该显示: ✓ 所有测试通过
```

---

### 3. ✅ 邮件收件人显示异常后缀 @domain.invalid

**问题描述：** 邮件收件人显示为 `li.xiaoyu@vnet.com@domain.invalid`

**错误现象：** 收件人邮箱地址后面多了 `@domain.invalid` 后缀

**根本原因：** 在邮件头中使用了 `Header()` 包装邮件地址，导致邮件客户端解析异常

**解决方案：** 收件人和抄送地址不要使用 `Header()` 包装，直接使用字符串

**修复代码：**
```python
# 修复前（错误）
message['To'] = Header(', '.join(recipients), 'utf-8')
message['Cc'] = Header(', '.join(cc), 'utf-8')

# 修复后（正确）
message['To'] = ', '.join(recipients)
message['Cc'] = ', '.join(cc)
```

**修复位置：** `src/notification/email_sender.py` 第 79-85 行

**验证方法：**
```bash
python3 test_email_recipient_fix.py
# 应该显示: ✓ 测试完成
```

---

### 4. ✅ PDF 中 Emoji 图标不显示

**问题描述：** 生成的 PDF 文件中 emoji 图标显示为空白或方块

**错误现象：** HTML邮件中emoji正常显示，但PDF中不显示

**根本原因：** 系统未安装emoji字体，Chromium无法渲染emoji字符

**解决方案：**
```bash
# 安装emoji字体
sudo apt-get install -y fonts-noto-color-emoji

# 验证安装
fc-list | grep -i emoji
# 应该显示: /usr/share/fonts/truetype/noto/NotoColorEmoji.ttf: Noto Color Emoji:style=Regular
```

**修复代码：**
```python
# 在PDF生成器中添加emoji字体到font-family
font-family: 'Noto Sans CJK SC', ..., sans-serif, 'Noto Color Emoji', 'Apple Color Emoji', 'Segoe UI Emoji' !important;
```

**修复位置：** `src/reporting/pdf_generator.py` 第 70-73 行

**验证方法：**
```bash
python3 test_pdf_emoji.py
# 应该生成包含emoji的测试PDF: reports/emoji_test.pdf
```

---

### 5. ✅ 苹果邮件只显示附件不显示正文

**问题描述：** 在某些邮件软件能看到正文，但苹果邮件（Mail.app）只显示附件，看不到正文

**错误现象：**
- Windows/Outlook：正文和附件都显示正常 ✓
- 苹果邮件：只能看到附件，正文消失 ✗

**根本原因：** 使用了错误的MIME类型 `multipart/alternative`，当邮件包含附件时应该使用 `multipart/mixed`

**MIME类型说明：**
- `multipart/alternative`：表示同一内容的不同格式（如纯文本和HTML二选一），邮件客户端只显示其中一个
- `multipart/mixed`：表示独立的多个部分（正文+附件），邮件客户端会同时显示所有部分

**解决方案：** 根据是否有附件动态选择MIME类型

**修复代码：**
```python
# 修复前（错误）
message = MIMEMultipart('alternative')  # 总是使用 alternative

# 修复后（正确）
message = MIMEMultipart('mixed' if attachments else 'alternative')
```

**修复位置：** `src/notification/email_sender.py` 第 78 行

**验证方法：**
```bash
python3 test_email_mime_structure.py
# 应该显示: ✓ 所有测试通过
```

---

## 常见问题

### 邮件相关

#### Q1: 邮件发送失败 - 配置不完整

**错误信息：**
```
ValueError: 邮件配置不完整，请检查环境变量: SMTP_HOST, SMTP_USER, SMTP_PASS
```

**解决方案：**
```bash
# 1. 检查 .env 文件
cat .env | grep SMTP

# 2. 确保配置了以下项
SMTP_HOST=smtp.163.com
SMTP_PORT=465
SMTP_USER=your_email@163.com
SMTP_PASS=your_auth_code
EMAIL_RECIPIENTS=recipient@example.com

# 3. 重新加载环境变量
source .env
```

#### Q2: SMTP 认证失败

**错误信息：**
```
✗ SMTP认证失败: (535, b'Error: authentication failed')
```

**可能原因：**
1. 使用了登录密码而非授权码
2. 授权码不正确
3. 邮箱未开启 SMTP 服务

**解决方案：**
```bash
# 163邮箱：
# 1. 登录网页版邮箱
# 2. 设置 → POP3/SMTP/IMAP → 开启 SMTP 服务
# 3. 获取授权码（不是登录密码！）
# 4. 将授权码填入 SMTP_PASS
```

#### Q3: 邮件附件过大被拒收

**错误信息：**
```
⚠️  PDF文件较大（2.5 MB），可能影响邮件发送
```

**解决方案：**
```bash
# 方法1: 减少统计天数
python3 generate_weekly_report.py --days 3

# 方法2: 不发送PDF附件
python3 generate_weekly_report.py --send-email --no-pdf

# 方法3: 压缩PDF（需要额外工具）
# 或者优化PDF生成配置
```

---

### PDF 相关

#### Q4: PDF 生成失败 - Playwright 未安装

**错误信息：**
```
✗ PDF生成失败: No module named 'playwright'
```

**解决方案：**
```bash
# 安装 Playwright
pip install playwright

# 安装浏览器
playwright install chromium

# 验证
python3 -c "from playwright.sync_api import sync_playwright; print('OK')"
```

#### Q5: PDF 生成失败 - 浏览器不可用

**错误信息：**
```
✗ PDF生成失败: Executable doesn't exist at /root/.cache/ms-playwright/chromium-xxx
```

**解决方案：**
```bash
# 重新安装 Chromium 浏览器
playwright install chromium

# 如果还不行，安装依赖
playwright install-deps chromium
```

#### Q6: PDF 文件过大

**问题：** PDF 文件超过 2MB

**可能原因：**
1. 嵌入了在线字体
2. 文章数量过多
3. 图片或样式过多

**解决方案：**
```bash
# 1. 确保使用系统字体（代码已优化）
# 2. 减少统计天数
python3 generate_weekly_report.py --days 5

# 3. 检查生成的PDF
ls -lh reports/*.pdf
```

---

### LLM 摘要相关

#### Q7: LLM 摘要生成失败 - API 未配置

**错误信息：**
```
⚠️  未配置LLM API密钥，摘要生成功能将不可用
```

**解决方案：**
```bash
# 在 .env 中添加
LLM_API_KEY=your_api_key_here
LLM_API_BASE=https://api.your-provider.com
LLM_MODEL=gpt-4-turbo-preview

# 或者禁用 LLM 摘要
python3 generate_weekly_report.py --no-llm
```

#### Q8: LLM API 调用超时

**错误信息：**
```
✗ 周报摘要生成失败: LLM API调用超时（30秒）
```

**解决方案：**
1. 检查网络连接
2. 验证 API 端点是否可访问
3. 增加超时时间（修改 `src/reporting/report_summarizer.py` 中的 `self.timeout`）
4. 使用降级方案：`--no-llm`

#### Q9: LLM 返回格式错误

**错误信息：**
```
⚠️  JSON解析失败: Expecting value: line 1 column 1
```

**解决方案：**
- 自动使用降级方案，不影响周报生成
- 检查 LLM 配置是否正确
- 查看日志了解 LLM 返回的原始内容

---

### 数据库相关

#### Q10: 数据库文件不存在

**错误信息：**
```
✗ 数据库文件不存在: data/intelligence.db
  请先运行数据采集: python3 run_collection.py
```

**解决方案：**
```bash
# 运行数据采集
python3 run_collection.py

# 或指定其他数据库
python3 generate_weekly_report.py --db /path/to/db
```

#### Q11: 数据库中没有文章

**症状：** 生成的周报显示 "本周暂无符合条件的文章数据"

**解决方案：**
```bash
# 检查数据库内容
python3 -c "
from src.storage.database import Database
db = Database('data/intelligence.db')
articles = db.get_all_articles()
print(f'总文章数: {len(articles)}')
"

# 如果文章数为 0，运行采集
python3 run_collection.py
```

---

## 调试技巧

### 1. 查看详细错误日志

```bash
# 运行脚本时显示详细错误
python3 generate_weekly_report.py 2>&1 | tee debug.log

# 查看日志
cat debug.log
```

### 2. 逐步测试各个功能

```bash
# 测试 LLM 摘要
python3 test_weekly_summary.py

# 测试 PDF 生成
python3 test_pdf_generation.py

# 测试邮件附件
python3 test_email_with_pdf.py
```

### 3. 检查环境配置

```bash
# 查看环境变量
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

print('LLM_API_KEY:', 'configured' if os.getenv('LLM_API_KEY') else 'not set')
print('SMTP_USER:', os.getenv('SMTP_USER') or 'not set')
print('PDF_ENABLED:', os.getenv('PDF_ENABLED', 'true'))
print('WEEKLY_SUMMARY_ENABLED:', os.getenv('WEEKLY_SUMMARY_ENABLED', 'true'))
"
```

### 4. 使用简化模式测试

```bash
# 最简单的测试（禁用所有可选功能）
python3 generate_weekly_report.py --no-pdf --no-llm

# 如果成功，逐步启用功能
python3 generate_weekly_report.py --no-pdf  # 启用 LLM
python3 generate_weekly_report.py           # 启用 PDF
```

---

## 性能优化

### 减少生成时间

```bash
# 1. 禁用 PDF（节省 3-5 秒）
python3 generate_weekly_report.py --no-pdf

# 2. 禁用 LLM（节省 2-4 秒）
python3 generate_weekly_report.py --no-llm

# 3. 减少统计天数
python3 generate_weekly_report.py --days 3

# 4. 组合使用（最快）
python3 generate_weekly_report.py --no-pdf --no-llm --days 3
```

### 减少文件大小

```bash
# PDF 文件大小优化
# 1. 确保使用系统字体（已默认）
# 2. 减少统计天数
# 3. 使用环境变量控制

PDF_PAGE_SIZE=A4
PDF_MARGIN=15mm  # 减小边距
```

---

## 获取帮助

### 查看帮助信息

```bash
# 主脚本帮助
python3 generate_weekly_report.py --help

# 查看文档
ls docs/
cat docs/generate-weekly-report-usage.md
```

### 运行测试套件

```bash
# 运行所有测试
python3 test_weekly_summary.py
python3 test_pdf_generation.py
python3 test_email_with_pdf.py

# 应该显示: ✓ 所有测试通过
```

### 检查版本和依赖

```bash
# 检查 Python 版本
python3 --version

# 检查依赖
pip list | grep -E "playwright|beautifulsoup4|requests|dotenv"

# 检查字体
fc-list :lang=zh | wc -l
```

---

**最后更新：** 2025-11-08
**维护状态：** ✅ 活跃维护

# 周报 PDF 生成功能使用说明

## 功能概述

周报系统现已支持自动生成 PDF 格式的周报，并可作为邮件附件发送。PDF 内容与 HTML 邮件完全一致，包括：
- 整体总结和板块点评
- 渐变色背景和图标
- 中文字体和 emoji
- 完整的文章列表和统计信息

## 技术方案

- **PDF 生成引擎**: Playwright (Chromium)
- **页面规格**: A4, 边距 20mm
- **文件大小**: 约 700-800KB（取决于内容量）
- **视觉一致性**: 与 HTML 邮件 100% 一致

## 快速开始

### 1. 安装依赖

Playwright 已在 `requirements.txt` 中，首次使用需安装浏览器：

```bash
# 如果还没安装 playwright
pip install playwright

# 安装 Chromium 浏览器
playwright install chromium
```

### 2. 配置环境变量

在 `.env` 文件中添加：

```bash
# PDF 生成配置
PDF_ENABLED=true                    # 是否启用PDF生成
PDF_OUTPUT_DIR=reports              # PDF输出目录
PDF_PAGE_SIZE=A4                    # 页面大小
PDF_MARGIN=20mm                     # 页边距
PDF_PRINT_BACKGROUND=true           # 打印背景色
PDF_DISPLAY_HEADER_FOOTER=true     # 显示页眉页脚
```

### 3. 生成周报（包含 PDF）

```python
from src.reporting.report_generator import WeeklyReportGenerator

# 创建生成器
generator = WeeklyReportGenerator(
    db_path="data/intelligence.db"
)

# 生成周报（自动包含 Markdown, HTML, PDF）
result = generator.generate_and_save(
    output_path="reports/weekly_report.md",
    days=7,
    generate_html=True,
    generate_pdf=True  # 启用PDF生成
)

# 返回结果
print(result['markdown'])  # reports/weekly_report.md
print(result['html'])      # reports/weekly_report.html
print(result['pdf'])       # reports/IDC周报_第45周_2025-11-08.pdf
```

### 4. 发送带 PDF 附件的邮件

#### 方式一：使用已生成的 PDF

```python
from src.notification.email_sender import EmailSender

# 先生成周报和PDF
generator = WeeklyReportGenerator()
result = generator.generate_and_save('reports/weekly.md', generate_pdf=True)

# 读取周报
with open(result['markdown'], 'r') as f:
    report_content = f.read()

# 发送邮件，附加已生成的PDF
sender = EmailSender.from_env()
sender.send_weekly_report(
    report_content=report_content,
    pdf_attachment=result['pdf']  # 使用已生成的PDF
)
```

#### 方式二：自动生成 PDF 附件

```python
from src.notification.email_sender import EmailSender

# 读取Markdown周报
with open('reports/weekly_report.md', 'r') as f:
    report_content = f.read()

# 发送邮件时自动生成PDF
sender = EmailSender.from_env()
sender.send_weekly_report(
    report_content=report_content,
    auto_generate_pdf=True  # 自动生成PDF附件
)
```

## 独立使用 PDF 生成器

### 基础用法

```python
from src.reporting.pdf_generator import PDFGenerator

# 创建生成器
generator = PDFGenerator(
    page_size="A4",
    margin="20mm",
    print_background=True
)

# HTML 转 PDF
html_content = "<h1>测试</h1><p>内容</p>"
generator.html_to_pdf(
    html_content=html_content,
    output_path="output.pdf"
)

# 或从HTML文件
generator.html_file_to_pdf(
    html_file_path="report.html",
    output_path="output.pdf"
)
```

### 便捷函数

```python
from src.reporting.pdf_generator import generate_weekly_report_pdf

# 生成周报PDF（自动命名）
pdf_path = generate_weekly_report_pdf(
    html_content=html_content,
    output_dir="reports"
)
# 返回: reports/IDC周报_第45周_2025-11-08.pdf
```

## 配置选项详解

### PDF 生成器选项

```python
PDFGenerator(
    page_size="A4",           # 页面大小: A4, Letter, Legal 等
    margin="20mm",            # 统一边距，或使用字典指定各边
    print_background=True,    # 打印背景色和图片（保留渐变）
    display_header_footer=True  # 显示页码
)
```

### 自定义选项

```python
generator.html_to_pdf(
    html_content=html,
    output_path="output.pdf",
    options={
        'margin': {
            'top': '30mm',
            'right': '20mm',
            'bottom': '30mm',
            'left': '20mm'
        },
        'footer_template': '<div>自定义页脚</div>'
    }
)
```

## 文件命名规则

自动生成的 PDF 文件名格式：
```
IDC周报_第{周数}周_{日期}.pdf
```

示例：
- `IDC周报_第45周_2025-11-08.pdf`

## 错误处理和降级

### Playwright 未安装

```bash
✗ PDF生成失败: Playwright未安装

解决方案:
  pip install playwright
  playwright install chromium
```

### 浏览器未安装

```bash
✗ PDF生成失败: 浏览器不可用

解决方案:
  playwright install chromium
```

### PDF 生成失败（自动降级）

- 周报生成流程中，PDF 失败不影响 Markdown 和 HTML 生成
- 邮件发送时，PDF 失败会记录警告，但邮件仍会发送（不带附件）

```python
# 日志示例
⚠️  PDF生成失败: xxx，但周报生成流程继续
✓ Markdown周报已保存: reports/weekly.md
✓ HTML周报已保存: reports/weekly.html
```

## 性能和限制

### 文件大小

- 典型周报 PDF: 700-800KB
- 建议限制: < 10MB（邮件服务器限制）
- 超过 10MB 时会记录警告

### 生成时间

- 单个 PDF: 3-5 秒
- 包括浏览器启动、渲染和保存

### 并发限制

- Playwright 使用浏览器引擎，避免高并发
- 建议单线程顺序生成

## 测试和验证

### 运行测试脚本

```bash
# 测试PDF生成功能
python3 test_pdf_generation.py

# 测试邮件附件功能
python3 test_email_with_pdf.py
```

### 测试输出

```
✓ 基础PDF生成
✓ 周报PDF生成
✓ 从Markdown生成PDF

生成的文件:
  - reports/test_basic.pdf (24KB)
  - reports/IDC周报_第45周_2025-11-08.pdf (780KB)
```

### 手动验证 PDF 质量

打开生成的 PDF 文件，检查：
- ✅ 中文字符显示正常
- ✅ Emoji 图标显示正常
- ✅ 渐变色背景保留
- ✅ 页码正确显示
- ✅ 布局与 HTML 一致

## 常见问题

### Q: 为什么 PDF 这么大？

A: PDF 包含完整的样式和内容，嵌入字体。如果过大：
- 检查是否包含大量文章
- 考虑压缩图片（如果有）
- 确认是否有重复内容

### Q: 能否修改页眉页脚？

A: 可以，通过环境变量或代码配置：

```bash
# .env
PDF_FOOTER_TEMPLATE=<div>自定义页脚</div>
```

或在代码中：

```python
generator.html_to_pdf(
    html,
    "output.pdf",
    options={'footer_template': '<div>自定义</div>'}
)
```

### Q: 如何禁用 PDF 生成？

A: 三种方式：

1. 环境变量：
```bash
PDF_ENABLED=false
```

2. 代码参数：
```python
generator.generate_and_save('report.md', generate_pdf=False)
```

3. 邮件发送时：
```python
sender.send_weekly_report(content, auto_generate_pdf=False)
```

### Q: PDF 和 HTML 有差异怎么办？

A: Playwright 使用真实浏览器渲染，应该 100% 一致。如有差异：
1. 检查 CSS 是否使用了不支持的特性
2. 确认 `print_background=True`
3. 查看浏览器控制台日志

### Q: 能否自定义 PDF 样式？

A: 可以在 HTML 中添加 `@media print` CSS：

```css
@media print {
  .no-print { display: none; }
  .page-break { page-break-after: always; }
}
```

## 集成到调度器

在自动化周报生成流程中集成 PDF：

```python
# start_scheduler.py 或定时任务中

from src.reporting.report_generator import WeeklyReportGenerator
from src.notification.email_sender import EmailSender

def generate_and_send_weekly_report():
    # 生成周报（含PDF）
    generator = WeeklyReportGenerator()
    result = generator.generate_and_save(
        "reports/weekly.md",
        generate_pdf=True
    )

    # 读取周报
    with open(result['markdown'], 'r') as f:
        content = f.read()

    # 发送邮件（附加PDF）
    sender = EmailSender.from_env()
    sender.send_weekly_report(
        report_content=content,
        pdf_attachment=result['pdf']
    )
```

## 最佳实践

1. **生成流程**
   - 先生成 Markdown 和 HTML
   - 最后生成 PDF（失败不影响其他格式）

2. **邮件发送**
   - 推荐使用已生成的 PDF（方式一）
   - 避免每次发送都重新生成

3. **文件管理**
   - PDF 文件按日期归档
   - 定期清理旧文件（如保留 30 天）

4. **错误处理**
   - 始终检查返回值
   - PDF 失败时记录日志但不中断流程

## 文件结构

```
src/
├── reporting/
│   ├── report_generator.py      # 周报生成器（已集成PDF）
│   ├── report_summarizer.py     # LLM摘要生成器
│   └── pdf_generator.py         # PDF生成器（独立模块）
└── notification/
    ├── email_sender.py          # 邮件发送器（支持PDF附件）
    └── email_template_v2.py     # HTML模板生成器

tests/
├── test_pdf_generation.py       # PDF生成测试
└── test_email_with_pdf.py       # 邮件附件测试

reports/
├── weekly_report.md
├── weekly_report.html
└── IDC周报_第45周_2025-11-08.pdf
```

---

最后更新：2025-11-08

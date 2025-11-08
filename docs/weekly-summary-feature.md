# 周报 LLM 增强功能使用说明

## 功能概述

周报系统现已集成 LLM 智能摘要功能，为每份周报自动生成：

1. **整体总结**（100-200字）：位于周报开头，概括本周重点动态
2. **板块点评**（30-50字）：为每个板块（政策、投资、技术、市场）生成一句话洞察

## 主要特性

### 1. 整体总结
- 位置：报告头部之后，内容章节之前
- 格式：📌 本周概览
- 内容：概括政策、投资、技术、市场等核心动态，突出关键数据

### 2. 板块点评
- 位置：每个板块标题下方，文章列表上方
- 多样化标题：每次生成随机选择不同的点评标签
  - 政策法规：政策导向、监管动态、政策红利、顶层设计等
  - 投资动态：投资热点、资本动向、市场机遇、项目观察等
  - 技术进展：技术趋势、创新亮点、技术突破、研发洞察等
  - 市场动态：市场观察、竞争格局、需求洞察、商业机会等
- 图标匹配：不同标题搭配相应图标（💡📋🔥⚡等）

## 配置说明

### 环境变量配置

在 `.env` 文件中添加以下配置：

```bash
# LLM API配置（必需）
LLM_API_KEY=your_api_key_here
LLM_API_BASE=https://api.your-llm-provider.com
LLM_MODEL=gpt-4-turbo-preview

# 周报摘要功能开关
WEEKLY_SUMMARY_ENABLED=true          # 是否启用LLM摘要（默认true）
WEEKLY_INSIGHT_LABEL_RANDOM=true     # 是否随机板块点评标题（默认true）
```

### 支持的 LLM 提供商

- OpenAI（使用 `OPENAI_API_KEY` 和 `OPENAI_MODEL`）
- Anthropic Claude（使用 `ANTHROPIC_API_KEY` 和 `ANTHROPIC_MODEL`）
- 任何 OpenAI 兼容 API（使用 `LLM_API_KEY`、`LLM_API_BASE`、`LLM_MODEL`）

## 使用方法

### 1. 生成测试周报

```bash
python3 test_weekly_summary.py
```

这将生成：
- `reports/weekly_report_test.md` - Markdown格式周报
- `reports/weekly_report_test.html` - HTML邮件格式

### 2. 生成正式周报

```bash
python3 generate_weekly_report.py
```

### 3. 在代码中使用

```python
from src.reporting.report_generator import WeeklyReportGenerator

# 创建周报生成器（启用LLM摘要）
generator = WeeklyReportGenerator(
    db_path="data/intelligence.db",
    enable_llm_summary=True  # 可选，默认从环境变量读取
)

# 生成周报
report = generator.generate_report(days=7)
```

### 4. 禁用 LLM 摘要

如果不希望使用 LLM 摘要（例如在测试环境或 API 配额限制时）：

**方法一：环境变量**
```bash
WEEKLY_SUMMARY_ENABLED=false
```

**方法二：代码参数**
```python
generator = WeeklyReportGenerator(enable_llm_summary=False)
```

## 降级方案

当 LLM API 不可用时，系统会自动降级为统计型摘要：

- **整体总结**：显示文章数量统计
- **板块点评**：显示该板块文章数量

示例：
```
本周概览：本周共收录115篇IDC行业相关文章，其中高优先级0篇，中优先级22篇...

政策法规
📡 政策信号：本周政策领域收录10篇文章，涉及行业规范与政策导向
```

## Markdown 格式示例

```markdown
# IDC行业周报 | 2025年第45周

**报告日期**: 2025年11月08日
...

---

## 📌 本周概览

本周IDC行业呈现三大亮点：一是政策层面，国家发布《算力基础设施发展规划》...

---

## 一、政策法规

**🏛️ 顶层设计**：国家级算力政策密集出台，地方配套措施加速落地

### 1. 国家发改委发布《全国算力基础设施发展规划》
...

## 二、投资动态

**💰 资本动向**：百亿级项目频现，AI算力中心成投资热点

### 1. 某集团120亿元建设华东AI算力中心
...
```

## HTML 邮件样式

- **整体总结**：蓝紫色渐变背景，白色文字，突出显示
- **板块点评**：浅色背景，左侧彩色边框，斜体文字

## 技术细节

### 文件结构

- `src/reporting/report_summarizer.py` - LLM 摘要生成器
- `src/reporting/report_generator.py` - 周报生成器（已集成摘要功能）
- `src/notification/email_template_v2.py` - HTML 邮件模板（已支持摘要显示）

### Prompt 设计

系统会将本周文章数据发送给 LLM，要求：
1. 分析各板块重点文章（优先高评分文章）
2. 提炼核心趋势和关键数据
3. 生成结构化 JSON 输出（包含整体总结和各板块点评）

### API 调用优化

- 一次 API 调用完成所有摘要（整体总结 + 所有板块点评）
- 设置超时时间（30秒）
- 错误自动降级，不影响周报生成

## 常见问题

**Q: 如何测试 LLM 摘要功能？**
A: 运行 `python3 test_weekly_summary.py`，查看生成的 Markdown 和 HTML 文件。

**Q: 板块点评标题能自定义吗？**
A: 可以，编辑 `src/reporting/report_summarizer.py` 中的 `SECTION_INSIGHT_LABELS` 字典。

**Q: 降级方案会影响周报发送吗？**
A: 不会，降级方案确保即使 LLM 不可用，周报仍能正常生成和发送。

**Q: 如何查看 LLM 调用日志？**
A: 查看应用日志，搜索 "LLM摘要" 或 "周报摘要" 相关信息。

## 后续优化建议

1. **缓存优化**：对相同文章集合缓存摘要结果
2. **多语言支持**：支持生成英文版周报摘要
3. **个性化配置**：允许用户自定义摘要风格和长度
4. **A/B测试**：对比不同 prompt 策略的摘要质量

---

最后更新：2025-11-08

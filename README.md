# IDC行业竞争情报自动化系统

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-13%2F13%20passing-brightgreen.svg)](tests/)

自动化监控中国IDC（数据中心）行业的市场动态、技术进展、投资活动和政策变化，并生成专业的周报。

## 🎯 项目简介

本系统通过自动化采集、智能分析和报告生成，帮助IDC行业从业者高效获取行业情报，包括：

- 📰 **多源数据采集**：自动从4+个专业媒体抓取行业资讯
- 🤖 **AI智能摘要**：使用GLM-4.5-Air大模型生成专业摘要
- 📊 **智能评分分类**：4维度评分系统和自动分类
- 📑 **周报自动生成**：一键生成符合商业规范的Markdown周报
- 💾 **结构化存储**：SQLite数据库持久化存储

## ✨ 核心功能

### 1. 数据采集系统

- ✅ 支持多个媒体源并行采集
- ✅ 智能CSS选择器配置，无需为每个网站写代码
- ✅ Playwright动态网页渲染支持
- ✅ URL去重机制（MD5哈希）
- ✅ 发布日期vs采集时间分离

**当前支持的媒体源**：
- 中国IDC圈（Tier 1）
- 36氪（Tier 2）
- InfoQ（Tier 2）
- 量子位（Tier 2）

### 2. 智能分析系统

#### 4维度评分模型（总分100分）

| 维度 | 权重 | 说明 |
|------|------|------|
| 业务相关性 | 40分 | 关键词匹配（IDC、数据中心、云计算、AI等） |
| 时效性 | 25分 | 时间衰减公式：25 × (1 - days/7) |
| 影响范围 | 20分 | 融资金额、项目规模、技术突破 |
| 来源可信度 | 15分 | 媒体等级（Tier 1/2/3） |

#### 优先级分类

- **高优先级**：≥70分 - 核心业务相关且时效性强
- **中优先级**：40-69分 - 一般业务相关
- **低优先级**：<40分 - 弱相关或过时信息

#### 内容分类

- 投资动态（融资、并购、IPO）
- 技术进展（GPU、芯片、液冷、PUE）
- 政策法规（标准、监管、规划）
- 市场动态（报告、趋势、竞争）

### 3. LLM智能摘要

- ✅ 使用GLM-4.5-Air生成80-150字专业摘要
- ✅ 自动提取核心信息和业务价值
- ✅ 使用行业专业术语
- ✅ 100%摘要覆盖率

### 4. 周报生成器

- ✅ Markdown格式，符合中文商业文档规范
- ✅ 按分类自动组织高优先级文章
- ✅ 包含统计信息和数据分析
- ✅ TDD开发，13/13测试通过
- ✅ 88%测试覆盖率

## 🛠️ 技术栈

- **语言**：Python 3.10+
- **网页采集**：Playwright, BeautifulSoup4, Requests
- **数据库**：SQLite
- **LLM**：GLM-4.5-Air (OpenAI兼容API)
- **测试**：pytest, pytest-cov
- **其他**：python-dotenv

## 📦 安装

### 1. 克隆项目

```bash
git clone https://github.com/yourusername/competitive-intelligence-web.git
cd competitive-intelligence-web
```

### 2. 安装依赖

```bash
pip install -r requirements.txt

# 或使用清华镜像加速
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple/ \
    playwright requests beautifulsoup4 lxml python-dotenv pytest pytest-cov
```

### 3. 安装Playwright浏览器

```bash
playwright install chromium
```

### 4. 配置环境变量

创建 `.env` 文件：

```bash
cp .env.example .env
```

编辑 `.env` 配置LLM API：

```env
# LLM API配置
LLM_API_KEY=your_api_key_here
LLM_API_BASE=http://your-api-endpoint
LLM_MODEL=GLM-4.5-Air
LLM_PROVIDER=custom

# 数据库配置
DATABASE_PATH=data/intelligence.db

# 报告配置
REPORT_OUTPUT_DIR=reports
```

## 🚀 快速开始

### 采集数据

```bash
# 运行数据采集测试脚本
python tmp/test_multi_source_collection.py
```

这会从4个媒体源采集数据并存储到 `tmp/multi_source_intelligence.db`

### 生成LLM摘要

```python
from src.processing.llm_summarizer import LLMSummarizer
from src.storage.database import Database
from dotenv import load_dotenv
import os

load_dotenv()

# 初始化
db = Database("tmp/multi_source_intelligence.db")
summarizer = LLMSummarizer(
    api_key=os.getenv("LLM_API_KEY"),
    api_base=os.getenv("LLM_API_BASE"),
    model=os.getenv("LLM_MODEL"),
)

# 为缺少摘要的文章生成
articles = [a for a in db.get_all_articles()
            if not a.get("summary") or len(a["summary"]) < 30]

for article in articles:
    summary = summarizer.generate_summary(
        title=article["title"],
        content=article.get("content", "")
    )
    if summary:
        db.update_article_summary(article["id"], summary)
```

### 生成周报

```python
from src.reporting.report_generator import WeeklyReportGenerator

# 创建生成器
generator = WeeklyReportGenerator(
    db_path="tmp/multi_source_intelligence.db"
)

# 生成并保存周报
generator.generate_and_save("reports/weekly_report.md", days=7)
```

或使用命令行：

```bash
python -c "
from src.reporting.report_generator import WeeklyReportGenerator
gen = WeeklyReportGenerator(db_path='tmp/multi_source_intelligence.db')
gen.generate_and_save('reports/weekly_report.md')
print('✅ 周报已生成')
"
```

## 📊 示例输出

### 采集统计

```
================================================================================
📊 采集统计
================================================================================

✅ 中国IDC圈:
   抓取: 5 | 存储: 5 | 重复: 0

✅ 36氪:
   抓取: 5 | 存储: 5 | 重复: 0

总计: 抓取 20 | 存储 20 | 重复 0
```

### 周报示例

查看完整示例：[tmp/IDC_Weekly_Report_2025_W45.md](tmp/IDC_Weekly_Report_2025_W45.md)

```markdown
# IDC行业周报 | 2025年第45周

## 一、投资动态

### 1. 投资26.2亿元，孝感大数据产业园一期项目开工

**【投资】** 中国IDC圈 | 2025-11-03 | 评分: 46

孝感大数据产业园一期项目投资26.2亿元正式开工，将建设高标准数据中心基础设施...

[查看详情](https://news.idcquan.com/scqb/205764.shtml)

## 二、技术进展
...
```

## 📂 项目结构

```
competitive-intelligence-web/
├── src/                          # 源代码
│   ├── scrapers/                 # 数据采集模块
│   │   ├── generic_scraper.py    # 通用爬虫（配置驱动）
│   │   └── idcquan_scraper.py    # IDC圈专用爬虫
│   ├── storage/                  # 数据存储模块
│   │   └── database.py           # SQLite数据库封装
│   ├── processing/               # 数据处理模块
│   │   └── llm_summarizer.py     # LLM摘要生成器
│   ├── scoring/                  # 评分模块（待实现）
│   ├── classification/           # 分类模块（待实现）
│   ├── reporting/                # 报告生成模块
│   │   └── report_generator.py   # 周报生成器
│   └── scheduler/                # 调度模块（待实现）
│
├── tests/                        # 测试文件
│   ├── test_report_generator.py  # 周报生成器测试（13个测试）
│   ├── test_database.py          # 数据库测试（待实现）
│   └── test_priority_scorer.py   # 评分系统测试（待实现）
│
├── config/                       # 配置文件
│   └── media-sources.json        # 媒体源配置
│
├── data/                         # 数据目录
│   └── intelligence.db           # 生产数据库
│
├── tmp/                          # 临时文件/测试
│   ├── multi_source_intelligence.db      # 测试数据库（20篇文章）
│   ├── IDC_Weekly_Report_2025_W45.md     # 生成的周报示例
│   ├── test_multi_source_collection.py   # 采集测试脚本
│   ├── LLM_SUMMARY_REPORT.md             # LLM集成报告
│   └── SQLITE_COMMANDS.md                # SQLite命令备忘单
│
├── reports/                      # 生成的报告输出目录
├── docs/                         # 项目文档
├── .env                          # 环境变量配置（需自行创建）
├── .env.example                  # 环境变量示例
├── pyproject.toml                # 项目配置
└── README.md                     # 本文件
```

## 🗄️ 数据库Schema

### articles表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| title | TEXT | 文章标题 |
| url | TEXT | 文章链接（唯一） |
| url_hash | TEXT | URL的MD5哈希（去重） |
| source | TEXT | 来源媒体 |
| source_tier | INTEGER | 媒体等级（1/2/3） |
| publish_date | DATE | 文章实际发布日期 |
| collected_at | TIMESTAMP | 系统采集时间 |
| content | TEXT | 文章正文 |
| summary | TEXT | 文章摘要 |
| category | TEXT | 分类（投资/技术/政策/市场） |
| priority | TEXT | 优先级（高/中/低） |
| score | INTEGER | 总分（0-100） |
| score_relevance | INTEGER | 业务相关性得分（0-40） |
| score_timeliness | INTEGER | 时效性得分（0-25） |
| score_impact | INTEGER | 影响范围得分（0-20） |
| score_credibility | INTEGER | 来源可信度得分（0-15） |
| link_valid | BOOLEAN | 链接是否有效 |
| summary_generated | BOOLEAN | 是否已生成摘要 |
| processed | BOOLEAN | 是否已完成处理 |

### 常用查询

```bash
# 查看Top 10文章
sqlite3 tmp/multi_source_intelligence.db \
  "SELECT title, score, priority FROM articles ORDER BY score DESC LIMIT 10;"

# 按分类统计
sqlite3 tmp/multi_source_intelligence.db \
  "SELECT category, COUNT(*) FROM articles GROUP BY category;"

# 查看高优先级文章
sqlite3 tmp/multi_source_intelligence.db \
  "SELECT title, score FROM articles WHERE priority='高';"
```

完整SQLite命令参考：[tmp/SQLITE_COMMANDS.md](tmp/SQLITE_COMMANDS.md)

## 🧪 运行测试

### 运行所有测试

```bash
pytest
```

### 运行特定测试

```bash
# 周报生成器测试
pytest tests/test_report_generator.py -v

# 带覆盖率报告
pytest --cov=src --cov-report=html
```

### 当前测试状态

- ✅ **周报生成器**：13/13 测试通过，88% 覆盖率
- ⏳ **数据库层**：待编写
- ⏳ **评分系统**：待编写
- ⏳ **爬虫系统**：待编写

## 📝 配置媒体源

编辑 `config/media-sources.json` 添加新的媒体源：

```json
{
  "name": "新媒体名称",
  "url": "https://example.com",
  "tier": 2,
  "active": true,
  "category": "科技资讯",
  "description": "媒体描述",
  "scraper_config": {
    "scraper_type": "generic",
    "list_url": "https://example.com/news/",
    "encoding": "utf-8",
    "article_container": "div.article-item",
    "title_selector": "h2 a",
    "link_selector": "h2 a",
    "date_selector": "span.date",
    "summary_selector": "div.summary"
  }
}
```

参考文档：[docs/ADD_NEW_MEDIA.md](docs/ADD_NEW_MEDIA.md)

## 🔧 开发指南

### TDD开发模式

本项目采用测试驱动开发（TDD）模式，遵循 RED-GREEN-REFACTOR 循环：

1. **RED**：先写失败的测试
2. **GREEN**：编写最小代码让测试通过
3. **REFACTOR**：重构代码，保持测试通过

示例：周报生成器的开发完全遵循TDD，先编写13个测试用例，再实现功能。

### 代码规范

- Python 3.10+ 类型提示
- 函数和类添加docstring
- 使用Black格式化（line-length=100）
- 遵循PEP 8规范

### 提交规范

```bash
# 功能开发
git commit -m "feat: 添加周报生成器"

# Bug修复
git commit -m "fix: 修复日期解析问题"

# 测试
git commit -m "test: 添加数据库层测试"

# 文档
git commit -m "docs: 更新README"
```

## 🗺️ 功能路线图

### ✅ 已完成（v0.1）

- [x] 多源数据采集系统
- [x] SQLite数据存储
- [x] 4维度评分系统
- [x] 智能内容分类
- [x] LLM智能摘要（GLM-4.5-Air）
- [x] Markdown周报生成
- [x] TDD测试框架

### 🚧 进行中（v0.2）

- [ ] 定时调度系统（APScheduler）
  - 每日早8点自动采集
  - 每周五下午5点生成周报
- [ ] 完善测试覆盖（目标≥80%）
  - 数据库层测试
  - 爬虫系统测试
  - 评分系统测试

### 📅 计划中（v0.3+）

- [ ] 扩展媒体源（目标22个）
- [ ] Web管理界面（FastAPI + React）
- [ ] 邮件自动发送
- [ ] 数据可视化仪表板
- [ ] RSS订阅支持
- [ ] 多用户支持

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request！

### 贡献指南

1. Fork本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 📧 联系方式

- 项目问题：[GitHub Issues](https://github.com/yourusername/competitive-intelligence-web/issues)
- 邮件：your.email@example.com

## 🙏 致谢

- 感谢所有贡献者
- 感谢开源社区的支持
- 使用的开源项目：Playwright, BeautifulSoup4, SQLite, pytest

---

**⭐ 如果这个项目对你有帮助，请给一个Star！**

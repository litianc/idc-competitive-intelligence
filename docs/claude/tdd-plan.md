# TDD测试计划文档

## 测试驱动开发原则

本项目采用**测试驱动开发（TDD）**模式，遵循**RED-GREEN-REFACTOR**循环：

1. **RED**：先写失败的测试
2. **GREEN**：编写最小代码让测试通过
3. **REFACTOR**：重构代码，保持测试通过

## 测试策略

### 测试金字塔

```
        /\
       /  \  E2E测试（少量）
      /    \
     /------\  集成测试（适量）
    /        \
   /----------\  单元测试（大量）
  /__________  \
```

- **单元测试**（70%）：测试单个函数/类的逻辑
- **集成测试**（25%）：测试模块间交互
- **端到端测试**（5%）：测试完整流程

### 测试覆盖率目标

- **总体覆盖率**：≥80%
- **核心模块覆盖率**：≥90%
  - 数据库层
  - 评分引擎
  - 分类器
  - 报告生成器

## 模块测试计划

### 1. 数据库层（src/storage/database.py）

**测试文件**：`tests/test_database.py`

**测试用例**：

- [ ] **test_create_tables**：测试表创建
- [ ] **test_insert_article**：测试文章插入
- [ ] **test_insert_duplicate_article**：测试重复文章去重（基于URL）
- [ ] **test_insert_with_url_hash**：测试URL哈希生成和唯一性
- [ ] **test_get_article_by_id**：测试按ID查询文章
- [ ] **test_get_articles_by_date_range**：测试按日期范围查询
- [ ] **test_update_article_summary**：测试更新摘要
- [ ] **test_update_article_scores**：测试更新评分
- [ ] **test_get_articles_for_weekly_report**：测试获取周报数据
- [ ] **test_mark_link_valid**：测试标记链接有效性
- [ ] **test_publish_date_vs_collected_at**：测试发布日期和采集时间分别存储

**关键测试**：
```python
def test_publish_date_vs_collected_at():
    """测试发布日期和采集时间是分开存储的"""
    db = Database(":memory:")

    # 文章发布日期是3天前
    publish_date = date.today() - timedelta(days=3)

    article_id = db.insert_article(
        title="测试文章",
        url="https://example.com/test",
        source="测试媒体",
        publish_date=publish_date,
        content="测试内容"
    )

    article = db.get_article_by_id(article_id)

    # 发布日期应该是3天前
    assert article["publish_date"] == publish_date
    # 采集时间应该是今天（自动设置）
    assert article["collected_at"].date() == date.today()
```

### 2. 爬虫系统（src/scrapers/）

**测试文件**：`tests/test_scraper.py`

**测试用例**：

- [ ] **test_fetch_page**：测试页面抓取
- [ ] **test_parse_article_list**：测试文章列表解析
- [ ] **test_extract_publish_date**：测试发布日期提取
- [ ] **test_extract_publish_date_formats**：测试多种日期格式解析
- [ ] **test_validate_link**：测试链接有效性验证
- [ ] **test_generate_url_hash**：测试URL哈希生成
- [ ] **test_scrape_with_user_agent_rotation**：测试User-Agent轮换
- [ ] **test_scrape_with_delay**：测试请求延迟
- [ ] **test_handle_scrape_error**：测试错误处理

**关键测试**：
```python
def test_extract_publish_date():
    """测试从不同格式的HTML中提取发布日期"""
    scraper = BaseScraper(source_config)

    # 格式1：YYYY-MM-DD
    html1 = '<span class="date">2025-01-03</span>'
    date1 = scraper.extract_publish_date(html1)
    assert date1 == date(2025, 1, 3)

    # 格式2：YYYY年MM月DD日
    html2 = '<div class="publish-time">2025年01月03日</div>'
    date2 = scraper.extract_publish_date(html2)
    assert date2 == date(2025, 1, 3)

    # 格式3：相对时间
    html3 = '<span>3天前</span>'
    date3 = scraper.extract_publish_date(html3)
    assert date3 == date.today() - timedelta(days=3)
```

### 3. LLM摘要生成器（src/processing/llm_summarizer.py）

**测试文件**：`tests/test_summarizer.py`

**测试用例**：

- [ ] **test_generate_summary**：测试摘要生成
- [ ] **test_summary_length**：测试摘要长度（80-150字）
- [ ] **test_summary_chinese_output**：测试中文输出
- [ ] **test_api_error_handling**：测试API错误处理
- [ ] **test_retry_mechanism**：测试重试机制
- [ ] **test_cache_mechanism**：测试缓存机制（相同内容不重复调用）
- [ ] **test_openai_provider**：测试OpenAI提供商
- [ ] **test_anthropic_provider**：测试Anthropic提供商

**关键测试**：
```python
def test_summary_length():
    """测试LLM生成的摘要长度符合要求"""
    summarizer = LLMSummarizer(provider="openai")

    article_content = """
    某公司宣布完成10亿元C轮融资...
    [长文章内容]
    """

    summary = summarizer.generate_summary(
        title="某公司完成10亿元融资",
        content=article_content
    )

    # 摘要长度应在80-150字之间
    assert 80 <= len(summary) <= 150
    # 摘要应该是中文
    assert any('\u4e00' <= char <= '\u9fff' for char in summary)
```

### 4. 优先级评分引擎（src/scoring/priority_scorer.py）

**测试文件**：`tests/test_priority_scorer.py`

**测试用例**：

- [ ] **test_calculate_relevance_score**：测试业务相关性评分
- [ ] **test_calculate_timeliness_score**：测试时效性评分（衰减公式）
- [ ] **test_calculate_impact_score**：测试影响范围评分
- [ ] **test_calculate_credibility_score**：测试来源可信度评分
- [ ] **test_calculate_total_score**：测试总分计算
- [ ] **test_map_priority_level**：测试优先级映射（高/中/低）
- [ ] **test_score_ranges**：测试评分边界条件
- [ ] **test_timeliness_decay**：测试时效性衰减

**关键测试**：
```python
def test_calculate_timeliness_score():
    """测试时效性评分的衰减公式"""
    scorer = PriorityScorer()

    # 当天发布：25分
    today = date.today()
    score_today = scorer.calculate_timeliness_score(today)
    assert score_today == 25

    # 3天前：约14分
    three_days_ago = today - timedelta(days=3)
    score_3days = scorer.calculate_timeliness_score(three_days_ago)
    assert 13 <= score_3days <= 15

    # 7天前：0分
    seven_days_ago = today - timedelta(days=7)
    score_7days = scorer.calculate_timeliness_score(seven_days_ago)
    assert score_7days == 0

    # 超过7天：0分
    ten_days_ago = today - timedelta(days=10)
    score_10days = scorer.calculate_timeliness_score(ten_days_ago)
    assert score_10days == 0

def test_map_priority_level():
    """测试总分到优先级的映射"""
    scorer = PriorityScorer()

    assert scorer.map_priority_level(85) == "高"
    assert scorer.map_priority_level(70) == "高"
    assert scorer.map_priority_level(65) == "中"
    assert scorer.map_priority_level(40) == "中"
    assert scorer.map_priority_level(35) == "低"
    assert scorer.map_priority_level(0) == "低"
```

### 5. 内容分类器（src/classification/content_classifier.py）

**测试文件**：`tests/test_classifier.py`

**测试用例**：

- [ ] **test_classify_investment**：测试投资类文章分类
- [ ] **test_classify_technology**：测试技术类文章分类
- [ ] **test_classify_policy**：测试政策类文章分类
- [ ] **test_classify_market**：测试市场类文章分类
- [ ] **test_classify_multiple_categories**：测试多分类
- [ ] **test_classify_no_match**：测试无匹配分类
- [ ] **test_keyword_matching**：测试关键词匹配逻辑

**关键测试**：
```python
def test_classify_multiple_categories():
    """测试一篇文章属于多个分类"""
    classifier = ContentClassifier()

    title = "某公司获10亿融资用于AI芯片研发"
    content = "该公司宣布完成C轮融资，资金将用于新一代GPU芯片的研发..."

    categories = classifier.classify(title, content)

    # 应该同时被分类为投资和技术
    assert "投资" in categories
    assert "技术" in categories

def test_classify_no_match():
    """测试无关内容的分类"""
    classifier = ContentClassifier()

    title = "某公司举办年会"
    content = "公司举办年度员工大会..."

    categories = classifier.classify(title, content)

    # 应该返回空列表或["其他"]
    assert len(categories) == 0 or categories == ["其他"]
```

### 6. 周报生成器（src/reporting/report_generator.py）

**测试文件**：`tests/test_report_generator.py`

**测试用例**：

- [ ] **test_load_data_from_database**：测试从数据库加载数据
- [ ] **test_filter_by_date_range**：测试按日期范围筛选
- [ ] **test_group_by_priority**：测试按优先级分组
- [ ] **test_group_by_category**：测试按分类分组
- [ ] **test_generate_markdown_report**：测试生成Markdown报告
- [ ] **test_report_format_compliance**：测试报告格式合规性
- [ ] **test_chinese_business_format**：测试中文商业格式
- [ ] **test_empty_module_handling**：测试空模块处理
- [ ] **test_file_naming**：测试文件命名规范

**关键测试**：
```python
def test_generate_markdown_report():
    """测试生成符合规范的Markdown周报"""
    generator = ReportGenerator(db_path=":memory:")

    # 准备测试数据
    generator.db.insert_article(...)

    report_content = generator.generate_weekly_report()

    # 验证格式
    assert "# IDC行业周报" in report_content
    assert "## 一、投资动态" in report_content
    assert "## 二、技术进展" in report_content
    assert "【投资】" in report_content
    assert " | " in report_content  # 元数据分隔符
    assert "[详情]" in report_content

def test_chinese_business_format():
    """测试中文商业格式规范"""
    generator = ReportGenerator(db_path=":memory:")
    report_content = generator.generate_weekly_report()

    # 检查中文编号
    assert "一、" in report_content
    assert "二、" in report_content

    # 检查全角括号
    assert "【" in report_content and "】" in report_content
    # 不应该出现半角括号
    assert "[投资]" not in report_content

    # 检查日期格式
    import re
    dates = re.findall(r'\d{4}-\d{2}-\d{2}', report_content)
    assert len(dates) > 0  # 至少有日期
```

## 测试执行计划

### 阶段1：数据库层（先写测试，再实现）

1. 编写`tests/test_database.py`所有测试用例（全部失败）
2. 实现`src/storage/database.py`让测试通过
3. 重构代码
4. 确认所有测试通过

### 阶段2：爬虫系统（先写测试，再实现）

1. 编写`tests/test_scraper.py`所有测试用例
2. 实现`src/scrapers/base_scraper.py`
3. 实现`src/scrapers/selenium_scraper.py`
4. 确认所有测试通过

### 阶段3：LLM摘要（先写测试，再实现）

1. 编写`tests/test_summarizer.py`所有测试用例
2. 实现`src/processing/llm_summarizer.py`
3. 使用mock避免实际API调用
4. 确认所有测试通过

### 阶段4：评分和分类（先写测试，再实现）

1. 编写`tests/test_priority_scorer.py`和`tests/test_classifier.py`
2. 实现评分引擎和分类器
3. 确认所有测试通过

### 阶段5：报告生成（先写测试，再实现）

1. 编写`tests/test_report_generator.py`
2. 实现报告生成器
3. 确认所有测试通过

### 阶段6：集成测试

1. 编写端到端测试
2. 测试完整流程
3. 确认所有测试通过

## 测试工具和框架

### pytest配置

使用pytest作为测试框架，配置在`pyproject.toml`：

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --cov=src --cov-report=html --cov-report=term-missing"
```

### Mock和Fixture

使用pytest-mock进行模拟：

```python
# 模拟LLM API调用
def test_generate_summary(mocker):
    mock_openai = mocker.patch('openai.ChatCompletion.create')
    mock_openai.return_value = {
        'choices': [{'message': {'content': '这是一个测试摘要' * 10}}]
    }

    summarizer = LLMSummarizer()
    summary = summarizer.generate_summary("标题", "内容")

    assert len(summary) >= 80
    mock_openai.assert_called_once()
```

### 测试数据库

使用内存数据库进行测试：

```python
@pytest.fixture
def test_db():
    """创建测试用的内存数据库"""
    db = Database(":memory:")
    yield db
    db.close()
```

## 运行测试

### 运行所有测试

```bash
pytest
```

### 运行特定模块测试

```bash
pytest tests/test_database.py
pytest tests/test_scraper.py -v
```

### 查看覆盖率

```bash
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

### 持续集成

测试应在每次代码提交前运行：

```bash
# 在提交前运行
pytest --cov=src --cov-report=term-missing
# 只有所有测试通过且覆盖率≥80%才能提交
```

## 成功标准

- [ ] 所有单元测试通过
- [ ] 所有集成测试通过
- [ ] 代码覆盖率≥80%
- [ ] 核心模块覆盖率≥90%
- [ ] 没有跳过的测试（除非有充分理由）
- [ ] 测试运行时间<60秒

## TDD最佳实践

1. **先写测试，再写代码**：永远不要跳过这一步
2. **测试要独立**：每个测试可以单独运行
3. **测试要快速**：使用内存数据库和mock
4. **测试要清晰**：测试名称说明测试内容
5. **一次只改一个测试**：保持专注
6. **重构时保持测试通过**：绿色状态下重构
7. **测试边界条件**：空值、零值、负值、极大值
8. **测试错误处理**：异常、超时、API失败

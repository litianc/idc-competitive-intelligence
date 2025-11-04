# 数据库Schema设计文档

## 数据库选型

**数据库类型**：SQLite3
**文件路径**：`data/intelligence.db`

**选择理由**：
- 轻量级，无需独立服务器
- 适合单机部署
- 支持完整的SQL功能
- Python标准库内置支持

## 表结构设计

### 1. articles 表

存储采集的文章信息。

```sql
CREATE TABLE IF NOT EXISTS articles (
    -- 主键
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- 基本信息
    title TEXT NOT NULL,                  -- 文章标题
    url TEXT UNIQUE NOT NULL,             -- 原文链接（唯一）
    url_hash TEXT UNIQUE NOT NULL,        -- URL的MD5哈希（用于去重）
    source TEXT NOT NULL,                 -- 来源媒体名称
    source_tier INTEGER DEFAULT 2,        -- 媒体等级（1=Tier1, 2=Tier2, 3=Tier3）

    -- 时间信息
    publish_date DATE NOT NULL,           -- 文章实际发布日期（重要！）
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 采集时间

    -- 内容
    content TEXT,                         -- 文章正文内容
    summary TEXT,                         -- LLM生成的摘要（80-150字）

    -- 分类和评分
    category TEXT,                        -- 主要分类（投资/技术/政策/市场）
    categories TEXT,                      -- 所有分类（JSON数组字符串）
    priority TEXT,                        -- 优先级（高/中/低）
    score INTEGER DEFAULT 0,              -- 总评分（0-100）

    -- 评分明细
    score_relevance INTEGER DEFAULT 0,    -- 业务相关性得分（0-40）
    score_timeliness INTEGER DEFAULT 0,   -- 时效性得分（0-25）
    score_impact INTEGER DEFAULT 0,       -- 影响范围得分（0-20）
    score_credibility INTEGER DEFAULT 0,  -- 来源可信度得分（0-15）

    -- 质量标记
    link_valid BOOLEAN DEFAULT 1,         -- 链接是否有效
    summary_generated BOOLEAN DEFAULT 0,  -- 是否已生成摘要
    processed BOOLEAN DEFAULT 0,          -- 是否已处理（评分+分类）

    -- 元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_publish_date ON articles(publish_date DESC);
CREATE INDEX IF NOT EXISTS idx_priority ON articles(priority);
CREATE INDEX IF NOT EXISTS idx_category ON articles(category);
CREATE INDEX IF NOT EXISTS idx_collected_at ON articles(collected_at DESC);
CREATE INDEX IF NOT EXISTS idx_source ON articles(source);
CREATE INDEX IF NOT EXISTS idx_link_valid ON articles(link_valid);
```

### 2. media_sources 表

存储媒体源配置信息（可选，也可使用JSON文件）。

```sql
CREATE TABLE IF NOT EXISTS media_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,            -- 媒体名称
    url TEXT NOT NULL,                    -- 网站URL
    tier INTEGER DEFAULT 2,               -- 媒体等级（1-3）
    active BOOLEAN DEFAULT 1,             -- 是否启用

    -- 爬虫配置
    scraper_type TEXT DEFAULT 'basic',    -- 爬虫类型（basic/selenium）
    list_url TEXT,                        -- 文章列表页URL
    article_selector TEXT,                -- 文章元素选择器
    title_selector TEXT,                  -- 标题选择器
    date_selector TEXT,                   -- 日期选择器
    date_format TEXT,                     -- 日期格式
    content_selector TEXT,                -- 内容选择器

    -- 统计
    total_articles INTEGER DEFAULT 0,     -- 累计采集文章数
    last_scraped_at TIMESTAMP,            -- 最后采集时间

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3. scrape_logs 表

记录采集日志。

```sql
CREATE TABLE IF NOT EXISTS scrape_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL,            -- 媒体源名称
    started_at TIMESTAMP NOT NULL,        -- 开始时间
    completed_at TIMESTAMP,               -- 完成时间
    status TEXT NOT NULL,                 -- 状态（success/failed/partial）
    articles_found INTEGER DEFAULT 0,     -- 发现的文章数
    articles_new INTEGER DEFAULT 0,       -- 新增的文章数
    articles_duplicate INTEGER DEFAULT 0, -- 重复的文章数
    error_message TEXT,                   -- 错误信息
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_scrape_logs_source ON scrape_logs(source_name);
CREATE INDEX IF NOT EXISTS idx_scrape_logs_started ON scrape_logs(started_at DESC);
```

### 4. reports 表

记录生成的报告。

```sql
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,                  -- 报告标题
    report_type TEXT NOT NULL,            -- 报告类型（weekly/daily/custom）
    file_path TEXT NOT NULL,              -- 报告文件路径
    start_date DATE NOT NULL,             -- 报告起始日期
    end_date DATE NOT NULL,               -- 报告结束日期
    article_count INTEGER DEFAULT 0,      -- 包含的文章数
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_reports_type ON reports(report_type);
CREATE INDEX IF NOT EXISTS idx_reports_generated ON reports(generated_at DESC);
```

## 字段说明

### publish_date vs collected_at

**关键区别**：
- `publish_date`：文章在媒体网站上的实际发布日期
  - 从网页中解析提取
  - 用于计算时效性得分
  - 用于周报筛选（过去7天）

- `collected_at`：系统采集文章的时间戳
  - 自动记录采集时间
  - 用于追踪数据更新
  - 不用于业务逻辑

### url_hash 去重机制

使用MD5哈希实现URL去重：
```python
import hashlib

def generate_url_hash(url: str) -> str:
    return hashlib.md5(url.encode('utf-8')).hexdigest()
```

**优势**：
- 比较哈希值比比较长URL字符串更快
- 固定长度（32字符）
- 支持唯一索引

### categories 多标签存储

使用JSON数组字符串存储多个分类：
```json
["投资", "技术"]
```

**为什么不建立关联表**：
- 数据规模不大
- 查询简单
- 减少JOIN复杂度
- SQLite JSON函数支持查询

## 数据库操作规范

### 1. 插入文章

```python
INSERT INTO articles (
    title, url, url_hash, source, source_tier,
    publish_date, content, link_valid
) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(url) DO NOTHING;
```

### 2. 更新摘要

```python
UPDATE articles
SET summary = ?,
    summary_generated = 1,
    updated_at = CURRENT_TIMESTAMP
WHERE id = ?;
```

### 3. 更新评分和分类

```python
UPDATE articles
SET category = ?,
    categories = ?,
    priority = ?,
    score = ?,
    score_relevance = ?,
    score_timeliness = ?,
    score_impact = ?,
    score_credibility = ?,
    processed = 1,
    updated_at = CURRENT_TIMESTAMP
WHERE id = ?;
```

### 4. 查询周报数据

```python
SELECT * FROM articles
WHERE publish_date >= date('now', '-7 days')
  AND link_valid = 1
  AND summary_generated = 1
  AND processed = 1
ORDER BY score DESC, publish_date DESC;
```

### 5. 链接有效性批量检查

```python
UPDATE articles
SET link_valid = ?,
    updated_at = CURRENT_TIMESTAMP
WHERE id = ?;
```

## 数据迁移

### 初始化数据库

```python
def init_database(db_path: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 执行所有CREATE TABLE语句
    # 执行所有CREATE INDEX语句

    conn.commit()
    conn.close()
```

### 备份策略

定期备份数据库文件：
```bash
# 每周备份
cp data/intelligence.db data/backups/intelligence_$(date +%Y%m%d).db
```

## 性能优化

1. **索引优化**
   - 在高频查询字段上建立索引
   - publish_date、priority、category

2. **批量操作**
   - 使用executemany()批量插入
   - 使用事务减少I/O

3. **定期维护**
   - VACUUM清理碎片
   - ANALYZE更新统计信息

## 数据完整性约束

- `url` 必须唯一（UNIQUE约束）
- `url_hash` 必须唯一（UNIQUE约束）
- `title`、`url`、`source`、`publish_date` 不能为空（NOT NULL约束）
- `source_tier` 只能是1、2或3（应用层验证）
- `priority` 只能是"高"、"中"或"低"（应用层验证）
- `score` 范围0-100（应用层验证）

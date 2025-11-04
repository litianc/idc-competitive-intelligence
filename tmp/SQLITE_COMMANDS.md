# SQLite 数据库查询命令备忘单

数据库路径: `tmp/multi_source_intelligence.db`

## 🔧 基础命令

```bash
# 进入交互模式
sqlite3 tmp/multi_source_intelligence.db

# 查看所有表
sqlite3 tmp/multi_source_intelligence.db ".tables"

# 查看表结构
sqlite3 tmp/multi_source_intelligence.db ".schema articles"

# 退出交互模式（在交互模式内使用）
.quit
```

## 📊 统计查询

### 总体统计
```bash
# 查询总文章数
sqlite3 tmp/multi_source_intelligence.db "SELECT COUNT(*) as total FROM articles;"

# 查询评分统计
sqlite3 -header -column tmp/multi_source_intelligence.db \
  "SELECT MIN(score) as min, MAX(score) as max, AVG(score) as avg FROM articles;"
```

### 按维度统计
```bash
# 按优先级统计
sqlite3 -header -column tmp/multi_source_intelligence.db \
  "SELECT priority, COUNT(*) as count FROM articles GROUP BY priority;"

# 按分类统计
sqlite3 -header -column tmp/multi_source_intelligence.db \
  "SELECT category, COUNT(*) as count FROM articles GROUP BY category ORDER BY count DESC;"

# 按来源统计
sqlite3 -header -column tmp/multi_source_intelligence.db \
  "SELECT source, COUNT(*) as count FROM articles GROUP BY source;"

# 按日期统计
sqlite3 -header -column tmp/multi_source_intelligence.db \
  "SELECT publish_date, COUNT(*) as count FROM articles GROUP BY publish_date ORDER BY publish_date DESC;"
```

## 🔍 查询文章

### Top N 文章
```bash
# Top 5 文章（按评分）
sqlite3 -header -column tmp/multi_source_intelligence.db \
  "SELECT title, score, priority, source FROM articles ORDER BY score DESC LIMIT 5;"

# Top 10 文章（只显示标题和分数）
sqlite3 tmp/multi_source_intelligence.db \
  "SELECT score, title FROM articles ORDER BY score DESC LIMIT 10;"
```

### 按条件筛选
```bash
# 查询高优先级文章
sqlite3 -header -column tmp/multi_source_intelligence.db \
  "SELECT title, score, source FROM articles WHERE priority='高';"

# 查询中优先级文章
sqlite3 -header -column tmp/multi_source_intelligence.db \
  "SELECT title, score FROM articles WHERE priority='中' ORDER BY score DESC LIMIT 10;"

# 查询特定分类
sqlite3 -header -column tmp/multi_source_intelligence.db \
  "SELECT title, score, source FROM articles WHERE category='投资' ORDER BY score DESC;"

# 查询特定来源
sqlite3 -header -column tmp/multi_source_intelligence.db \
  "SELECT title, score, publish_date FROM articles WHERE source='中国IDC圈';"

# 查询分数范围
sqlite3 -header -column tmp/multi_source_intelligence.db \
  "SELECT title, score, priority FROM articles WHERE score >= 50 ORDER BY score DESC;"

# 查询今天的文章
sqlite3 -header -column tmp/multi_source_intelligence.db \
  "SELECT title, score FROM articles WHERE publish_date = date('now');"

# 查询最近3天的文章
sqlite3 -header -column tmp/multi_source_intelligence.db \
  "SELECT title, publish_date, score FROM articles WHERE publish_date >= date('now', '-3 days') ORDER BY publish_date DESC;"
```

### 查看完整文章详情
```bash
# 使用 -line 格式查看单篇文章
sqlite3 -line tmp/multi_source_intelligence.db \
  "SELECT * FROM articles WHERE id=1;"

# 查看指定字段（美化格式）
sqlite3 -line tmp/multi_source_intelligence.db \
  "SELECT title, url, source, publish_date, score, priority, category, summary FROM articles ORDER BY score DESC LIMIT 1;"
```

## 📈 评分分析

### 查看评分维度
```bash
# 查看4维度评分
sqlite3 -header -column tmp/multi_source_intelligence.db \
  "SELECT title, score, score_relevance as 相关性, score_timeliness as 时效性, score_impact as 影响, score_credibility as 可信度 FROM articles ORDER BY score DESC LIMIT 5;"

# 查看相关性最高的文章
sqlite3 -header -column tmp/multi_source_intelligence.db \
  "SELECT title, score_relevance, score FROM articles ORDER BY score_relevance DESC LIMIT 5;"

# 查看影响力最大的文章
sqlite3 -header -column tmp/multi_source_intelligence.db \
  "SELECT title, score_impact, score FROM articles WHERE score_impact > 0 ORDER BY score_impact DESC;"
```

## 🔎 搜索功能

### 关键词搜索
```bash
# 搜索标题包含关键词的文章
sqlite3 -header -column tmp/multi_source_intelligence.db \
  "SELECT title, score, source FROM articles WHERE title LIKE '%数据中心%';"

# 搜索标题或摘要包含关键词
sqlite3 -header -column tmp/multi_source_intelligence.db \
  "SELECT title, score FROM articles WHERE title LIKE '%AI%' OR summary LIKE '%AI%';"

# 多关键词搜索（AND）
sqlite3 -header -column tmp/multi_source_intelligence.db \
  "SELECT title, score FROM articles WHERE title LIKE '%云计算%' AND title LIKE '%AI%';"

# 多关键词搜索（OR）
sqlite3 -header -column tmp/multi_source_intelligence.db \
  "SELECT title, score FROM articles WHERE title LIKE '%数据中心%' OR title LIKE '%IDC%' OR title LIKE '%算力%';"
```

## 📤 导出数据

### 导出为CSV
```bash
# 导出所有文章
sqlite3 -header -csv tmp/multi_source_intelligence.db \
  "SELECT * FROM articles;" > articles_export.csv

# 导出高分文章
sqlite3 -header -csv tmp/multi_source_intelligence.db \
  "SELECT title, url, score, priority, category, source, publish_date FROM articles WHERE score >= 45 ORDER BY score DESC;" > high_score_articles.csv

# 导出特定分类
sqlite3 -header -csv tmp/multi_source_intelligence.db \
  "SELECT title, url, score, source FROM articles WHERE category='投资' ORDER BY score DESC;" > investment_articles.csv
```

### 导出为HTML
```bash
# 生成HTML表格
sqlite3 -header -html tmp/multi_source_intelligence.db \
  "SELECT title, score, priority, source FROM articles ORDER BY score DESC LIMIT 10;" > top_articles.html
```

## 🎨 输出格式

SQLite支持多种输出格式：

```bash
# column格式（列对齐，适合查看）
sqlite3 -header -column tmp/multi_source_intelligence.db "SELECT ..."

# line格式（每个字段一行，适合查看详情）
sqlite3 -line tmp/multi_source_intelligence.db "SELECT ..."

# csv格式（适合导出）
sqlite3 -header -csv tmp/multi_source_intelligence.db "SELECT ..."

# html格式（生成HTML表格）
sqlite3 -header -html tmp/multi_source_intelligence.db "SELECT ..."

# list格式（默认，用|分隔）
sqlite3 tmp/multi_source_intelligence.db "SELECT ..."
```

## 💡 高级查询

### 复杂条件组合
```bash
# 查询最近3天、分数>40的技术类文章
sqlite3 -header -column tmp/multi_source_intelligence.db \
  "SELECT title, score, publish_date FROM articles
   WHERE category='技术'
   AND score > 40
   AND publish_date >= date('now', '-3 days')
   ORDER BY score DESC;"

# 查询Tier 1来源的所有文章
sqlite3 -header -column tmp/multi_source_intelligence.db \
  "SELECT title, score, source FROM articles
   WHERE source_tier = 1
   ORDER BY score DESC;"
```

### 聚合分析
```bash
# 每个来源的平均分
sqlite3 -header -column tmp/multi_source_intelligence.db \
  "SELECT source, COUNT(*) as count, AVG(score) as avg_score
   FROM articles
   GROUP BY source
   ORDER BY avg_score DESC;"

# 每个分类的平均分
sqlite3 -header -column tmp/multi_source_intelligence.db \
  "SELECT category, COUNT(*) as count, AVG(score) as avg_score, MAX(score) as max_score
   FROM articles
   GROUP BY category
   ORDER BY avg_score DESC;"
```

## 🔧 交互模式命令

进入交互模式后可以使用的命令：

```sql
.tables              -- 列出所有表
.schema articles     -- 查看表结构
.headers on          -- 显示列名
.mode column         -- 列对齐显示
.mode line           -- 每行显示一个字段
.width 20 10 15      -- 设置列宽
.output file.txt     -- 输出到文件
.output stdout       -- 恢复输出到屏幕
.quit                -- 退出
```

## 📝 示例：完整查询流程

```bash
# 1. 查看总体概况
sqlite3 -header -column tmp/multi_source_intelligence.db \
  "SELECT COUNT(*) as total,
          COUNT(CASE WHEN priority='高' THEN 1 END) as high,
          COUNT(CASE WHEN priority='中' THEN 1 END) as medium,
          COUNT(CASE WHEN priority='低' THEN 1 END) as low
   FROM articles;"

# 2. 查看Top 5
sqlite3 -header -column tmp/multi_source_intelligence.db \
  "SELECT title, score, priority, category, source
   FROM articles
   ORDER BY score DESC
   LIMIT 5;"

# 3. 查看某篇文章的详情
sqlite3 -line tmp/multi_source_intelligence.db \
  "SELECT * FROM articles WHERE id=1;"
```

## ⚠️ 注意事项

1. **字段名区分大小写**: SQLite的字段名区分大小写
2. **中文支持**: 如果遇到中文显示问题，可以尝试设置编码
3. **性能**: 大数据量查询建议添加索引或使用LIMIT限制结果数
4. **备份**: 查询前建议备份数据库文件

## 🎯 快速参考

```bash
# 最常用的3个命令
sqlite3 -header -column tmp/multi_source_intelligence.db "SELECT * FROM articles ORDER BY score DESC LIMIT 10;"  # Top 10
sqlite3 -header -column tmp/multi_source_intelligence.db "SELECT category, COUNT(*) FROM articles GROUP BY category;"  # 分类统计
sqlite3 -line tmp/multi_source_intelligence.db "SELECT * FROM articles WHERE id=1;"  # 查看详情
```

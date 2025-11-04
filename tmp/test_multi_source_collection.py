"""
Multi-source integrated collection test
Tests all 4 active media sources
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.scrapers.generic_scraper import ScraperFactory
from src.storage.database import Database
from datetime import datetime, date
import json
import re


class SimpleScorer:
    """Article scoring system (4-dimension model)"""

    def score_article(self, title, content, publish_date, source_tier):
        """Score article using 4 dimensions"""
        # 1. Business Relevance (40 points max)
        keywords = ["IDC", "数据中心", "云计算", "AI", "算力", "GPU", "芯片", "智算", "服务器", "大模型"]
        text = title + " " + content
        keyword_count = sum(1 for kw in keywords if kw in text)
        relevance = min(40, keyword_count * 8)

        # 2. Timeliness (25 points max)
        if isinstance(publish_date, date):
            days_ago = (date.today() - publish_date).days
            timeliness = max(0, int(25 * (1 - days_ago / 7)))
        else:
            timeliness = 0

        # 3. Impact Scope (20 points max)
        impact = 0
        funding_patterns = [r"(\d+)亿.*?融资", r"融资.*?(\d+)亿", r"投资.*?(\d+)亿"]
        for pattern in funding_patterns:
            match = re.search(pattern, text)
            if match:
                amount = float(match.group(1))
                if amount >= 10:
                    impact = 20
                elif amount >= 5:
                    impact = 15
                elif amount >= 1:
                    impact = 10
                break

        if not impact:
            high_impact_keywords = ["标准", "规范", "政策", "突破", "PUE", "发布", "上市"]
            if any(kw in text for kw in high_impact_keywords):
                impact = 15

        # 4. Source Credibility (15 points max)
        credibility_map = {1: 15, 2: 8, 3: 3}
        credibility = credibility_map.get(source_tier, 3)

        total_score = relevance + timeliness + impact + credibility

        # Map to priority
        if total_score >= 70:
            priority = "高"
        elif total_score >= 40:
            priority = "中"
        else:
            priority = "低"

        return {
            "total_score": total_score,
            "priority": priority,
            "dimension_scores": {
                "relevance": relevance,
                "timeliness": timeliness,
                "impact": impact,
                "credibility": credibility,
            },
        }


class SimpleClassifier:
    """Article classification system"""

    def classify(self, title, content):
        """Classify article"""
        text = title + " " + content

        categories = {
            "投资": ["融资", "投资", "并购", "收购", "资本", "亿元", "IPO", "上市"],
            "技术": ["GPU", "芯片", "液冷", "技术", "突破", "创新", "PUE", "智算", "算力", "AI", "大模型"],
            "政策": ["政策", "法规", "标准", "规范", "发改委", "工信部", "国务院"],
            "市场": ["市场", "份额", "增长", "报告", "规模", "趋势", "预测"],
        }

        for category, keywords in categories.items():
            if any(kw in text for kw in keywords):
                return category

        return "市场"


def main():
    print("\n" + "=" * 80)
    print("多媒体源集成测试 - 4个活跃源")
    print("=" * 80)

    # Load config
    config_path = "config/media-sources.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # Get active sources
    active_sources = [s for s in config.get("sources", []) if s.get("active", False)]
    print(f"\n📊 发现 {len(active_sources)} 个活跃媒体源")
    for source in active_sources:
        print(f"   • {source.get('name')} (Tier {source.get('tier')})")

    # Initialize components
    scorer = SimpleScorer()
    classifier = SimpleClassifier()
    db = Database(db_path="tmp/multi_source_intelligence.db")

    # Collect from all sources
    all_articles = []
    source_stats = {}

    for source_config in active_sources:
        source_name = source_config.get("name")
        source_tier = source_config.get("tier", 2)
        
        print(f"\n{'='*80}")
        print(f"📥 抓取: {source_name}")
        print('='*80)

        try:
            scraper = ScraperFactory.create_scraper(source_config)
            articles = scraper.fetch_articles(limit=5)
            
            print(f"   ✅ 成功抓取 {len(articles)} 篇文章")
            
            source_stats[source_name] = {
                "fetched": len(articles),
                "stored": 0,
                "duplicates": 0
            }
            
            # Process articles
            for article in articles:
                # Score
                score_result = scorer.score_article(
                    title=article["title"],
                    content=article.get("summary", ""),
                    publish_date=article.get("publish_date"),
                    source_tier=source_tier,
                )

                # Classify
                category = classifier.classify(
                    title=article["title"],
                    content=article.get("summary", "")
                )

                # Store
                article_id = db.insert_article(
                    title=article["title"],
                    url=article["url"],
                    source=article["source"],
                    publish_date=article.get("publish_date"),
                    summary=article.get("summary", ""),
                    content="",
                    score=score_result["total_score"],
                    priority=score_result["priority"],
                    category=category,
                    score_relevance=score_result["dimension_scores"]["relevance"],
                    score_timeliness=score_result["dimension_scores"]["timeliness"],
                    score_impact=score_result["dimension_scores"]["impact"],
                    score_credibility=score_result["dimension_scores"]["credibility"],
                    link_valid=True,
                )

                if article_id is None:
                    source_stats[source_name]["duplicates"] += 1
                else:
                    source_stats[source_name]["stored"] += 1
                    print(f"      [{score_result['priority']}] {article['title'][:50]}...")
                    print(f"         分数: {score_result['total_score']} | 分类: {category}")

        except Exception as e:
            print(f"   ❌ 抓取失败: {e}")
            source_stats[source_name] = {"fetched": 0, "stored": 0, "duplicates": 0, "error": str(e)}

    # Show summary
    print(f"\n{'='*80}")
    print("📊 采集统计")
    print('='*80)
    
    total_fetched = 0
    total_stored = 0
    total_duplicates = 0
    
    for source_name, stats in source_stats.items():
        fetched = stats.get("fetched", 0)
        stored = stats.get("stored", 0)
        duplicates = stats.get("duplicates", 0)
        
        total_fetched += fetched
        total_stored += stored
        total_duplicates += duplicates
        
        status = "✅" if fetched > 0 else "❌"
        print(f"\n{status} {source_name}:")
        print(f"   抓取: {fetched} | 存储: {stored} | 重复: {duplicates}")
        if "error" in stats:
            print(f"   错误: {stats['error'][:60]}...")

    print(f"\n{'='*80}")
    print(f"总计: 抓取 {total_fetched} | 存储 {total_stored} | 重复 {total_duplicates}")

    # Database statistics
    print(f"\n{'='*80}")
    print("📊 数据库统计")
    print('='*80)

    all_db_articles = db.get_all_articles()
    print(f"\n总文章数: {len(all_db_articles)}")

    # Priority distribution
    priority_counts = {}
    for article in all_db_articles:
        priority = article.get("priority", "未分类")
        priority_counts[priority] = priority_counts.get(priority, 0) + 1

    print(f"\n优先级分布:")
    for priority in ["高", "中", "低"]:
        count = priority_counts.get(priority, 0)
        print(f"   {priority}: {count}")

    # Category distribution
    category_counts = {}
    for article in all_db_articles:
        category = article.get("category", "未分类")
        category_counts[category] = category_counts.get(category, 0) + 1

    print(f"\n分类分布:")
    for category, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        print(f"   {category}: {count}")

    # Source distribution
    source_counts = {}
    for article in all_db_articles:
        source = article.get("source", "未知")
        source_counts[source] = source_counts.get(source, 0) + 1

    print(f"\n来源分布:")
    for source, count in sorted(source_counts.items(), key=lambda x: -x[1]):
        print(f"   {source}: {count}")

    # Show high-priority articles
    print(f"\n{'='*80}")
    print("🌟 高优先级文章")
    print('='*80)

    high_priority = db.get_articles_by_priority("高")
    if high_priority:
        for i, article in enumerate(high_priority[:10], 1):
            print(f"\n{i}. [{article['score']}分] {article['title']}")
            print(f"   来源: {article['source']} | 分类: {article['category']} | 日期: {article['publish_date']}")
    else:
        print("   暂无高优先级文章")

    # Show medium-priority samples
    print(f"\n{'='*80}")
    print("📰 中优先级文章示例")
    print('='*80)

    medium_priority = db.get_articles_by_priority("中")
    if medium_priority:
        for i, article in enumerate(medium_priority[:5], 1):
            print(f"\n{i}. [{article['score']}分] {article['title'][:60]}...")
            print(f"   来源: {article['source']} | 分类: {article['category']}")

    print(f"\n{'='*80}")
    print("✅ 测试完成!")
    print(f"📁 数据库: tmp/multi_source_intelligence.db")
    print('='*80 + "\n")


if __name__ == "__main__":
    main()

"""
Integrated article collection script

Combines:
1. IdcquanScraper - fetch real articles
2. Scoring system - calculate priority scores
3. Classification - categorize articles
4. Database - store articles
"""

import sys
sys.path.insert(0, '/Users/xyli/Documents/Code/claude-life/competitive-intelligence-web')

from src.scrapers.idcquan_scraper import IdcquanScraper
from src.storage.database import Database
from datetime import datetime, date
import re


class SimpleScorer:
    """Article scoring system (4-dimension model)"""

    def score_article(self, title, content, publish_date, source_tier):
        """
        Score article using 4 dimensions:
        1. Business relevance (40 points)
        2. Timeliness (25 points)
        3. Impact scope (20 points)
        4. Source credibility (15 points)
        """
        # 1. Business Relevance (40 points max)
        keywords = ["IDC", "数据中心", "云计算", "AI算力", "GPU", "芯片", "智算"]
        text = title + " " + content
        keyword_count = sum(1 for kw in keywords if kw in text)
        relevance = min(40, keyword_count * 10)

        # 2. Timeliness (25 points max, decays over 7 days)
        if isinstance(publish_date, date):
            days_ago = (date.today() - publish_date).days
            timeliness = max(0, int(25 * (1 - days_ago / 7)))
        else:
            timeliness = 0

        # 3. Impact Scope (20 points max)
        impact = 0
        # Check funding amount
        funding_patterns = [
            r"(\d+)亿.*?融资",
            r"融资.*?(\d+)亿",
            r"投资.*?(\d+)亿",
            r"(\d+)亿.*?投资",
        ]
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

        # Check for industry standards or major breakthroughs
        if not impact:
            high_impact_keywords = ["标准", "规范", "政策", "突破", "PUE"]
            if any(kw in text for kw in high_impact_keywords):
                impact = 18

        # 4. Source Credibility (15 points max)
        credibility_map = {1: 15, 2: 8, 3: 3}
        credibility = credibility_map.get(source_tier, 3)

        # Calculate total score
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
        """
        Classify article into one of 4 categories:
        - 投资 (Investment)
        - 技术 (Technology)
        - 政策 (Policy)
        - 市场 (Market)
        """
        text = title + " " + content

        categories = {
            "投资": ["融资", "投资", "并购", "收购", "资本", "亿元", "IPO", "上市"],
            "技术": ["GPU", "芯片", "液冷", "技术", "突破", "创新", "PUE", "智算", "算力"],
            "政策": ["政策", "法规", "标准", "规范", "发改委", "工信部", "国务院"],
            "市场": ["市场", "份额", "增长", "报告", "规模", "趋势", "预测"],
        }

        # Find first matching category
        for category, keywords in categories.items():
            if any(kw in text for kw in keywords):
                return category

        return "市场"  # Default category


def main():
    """Run integrated collection"""
    print("=" * 70)
    print("Integrated Article Collection Pipeline")
    print("=" * 70)

    # Initialize components
    scraper = IdcquanScraper()
    scorer = SimpleScorer()
    classifier = SimpleClassifier()
    db = Database(db_path="tmp/integrated_intelligence.db")

    # Step 1: Fetch articles
    print("\n📥 Step 1: Fetching articles from idcquan.com...")
    articles = scraper.fetch_articles(limit=10)
    print(f"   ✓ Fetched {len(articles)} articles")

    # Step 2: Process and store articles
    print("\n⚙️  Step 2: Processing and storing articles...")

    stored_count = 0
    duplicate_count = 0

    for article in articles:
        # Score article
        score_result = scorer.score_article(
            title=article["title"],
            content=article.get("summary", ""),
            publish_date=article["publish_date"],
            source_tier=1,  # idcquan is Tier 1
        )

        # Classify article
        category = classifier.classify(
            title=article["title"], content=article.get("summary", "")
        )

        # Store in database
        article_id = db.insert_article(
            title=article["title"],
            url=article["url"],
            source=article["source"],
            publish_date=article["publish_date"],
            summary=article.get("summary", ""),
            content="",  # Will be filled later with full article content
            score=score_result["total_score"],
            priority=score_result["priority"],
            category=category,
            score_relevance=score_result["dimension_scores"]["relevance"],
            score_timeliness=score_result["dimension_scores"]["timeliness"],
            score_impact=score_result["dimension_scores"]["impact"],
            score_credibility=score_result["dimension_scores"]["credibility"],
            link_valid=True,  # Assume valid for now
        )

        if article_id is None:
            duplicate_count += 1
        else:
            stored_count += 1
            print(
                f"   ✓ [{article_id}] {article['title'][:40]}... "
                f"(Score: {score_result['total_score']}, "
                f"Priority: {score_result['priority']}, "
                f"Category: {category})"
            )

    print(f"\n   📊 Stored: {stored_count} | Duplicates: {duplicate_count}")

    # Step 3: Show statistics
    print("\n📊 Step 3: Database Statistics")
    print("=" * 70)

    all_articles = db.get_all_articles()
    print(f"\n   Total articles: {len(all_articles)}")

    # Priority distribution
    priority_counts = {}
    for article in all_articles:
        priority = article.get("priority", "未分类")
        priority_counts[priority] = priority_counts.get(priority, 0) + 1

    print(f"\n   Priority distribution:")
    for priority, count in priority_counts.items():
        print(f"      {priority}: {count}")

    # Category distribution
    category_counts = {}
    for article in all_articles:
        category = article.get("category", "未分类")
        category_counts[category] = category_counts.get(category, 0) + 1

    print(f"\n   Category distribution:")
    for category, count in category_counts.items():
        print(f"      {category}: {count}")

    # Step 4: Show high-priority articles
    print("\n🌟 Step 4: High-Priority Articles")
    print("=" * 70)

    high_priority = db.get_articles_by_priority("高")
    if high_priority:
        for article in high_priority[:5]:
            print(f"\n   [{article['score']}分] {article['title']}")
            print(f"      Category: {article['category']}")
            print(f"      Date: {article['publish_date']}")
            print(f"      URL: {article['url'][:60]}...")
    else:
        print("   No high-priority articles found")

    print("\n" + "=" * 70)
    print("✅ Pipeline Complete!")
    print(f"📁 Database: tmp/integrated_intelligence.db")
    print("=" * 70)


if __name__ == "__main__":
    main()

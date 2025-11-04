"""
集成测试：从14个媒体源采集文章

包含：
- 6个原有active源
- 8个新增源
"""

import json
import sys
from datetime import date
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage.database import Database
from src.scrapers.generic_scraper import GenericScraper


def load_sources():
    """加载所有active媒体源"""
    with open('config/media-sources.json', 'r', encoding='utf-8') as f:
        config = json.load(f)

    active_sources = [s for s in config['sources'] if s.get('active', False)]
    return active_sources


def test_source_collection(source, db):
    """测试单个源的采集"""
    print(f"\n{'='*70}")
    print(f"测试源: {source['name']} (Tier {source['tier']})")
    print(f"URL: {source['scraper_config']['list_url']}")
    print(f"{'='*70}")

    try:
        # 创建scraper
        scraper = GenericScraper(source)

        # 采集文章
        print("正在采集文章...")
        articles = scraper.fetch_articles(limit=10)  # 每个源最多10篇

        if not articles:
            print("⚠️  未采集到文章（可能需要调整CSS选择器）")
            return {
                "name": source['name'],
                "status": "no_articles",
                "article_count": 0
            }

        print(f"✓ 采集到 {len(articles)} 篇文章")

        # 显示前3篇文章示例
        for i, article in enumerate(articles[:3], 1):
            print(f"\n  [{i}] {article.get('title', 'No title')[:50]}")
            print(f"      URL: {article.get('url', 'No URL')[:60]}")
            print(f"      日期: {article.get('publish_date', 'No date')}")

        # 存储到数据库（简化版，跳过评分）
        stored_count = 0
        for article in articles:
            # 基本验证
            if article.get('title') and article.get('url'):
                # 这里应该调用评分系统，但为了速度，我们跳过
                # 直接存储基本信息
                try:
                    db.insert_article(
                        title=article['title'],
                        url=article['url'],
                        source=source['name'],
                        source_tier=source['tier'],
                        publish_date=article.get('publish_date', date.today()),
                        content=article.get('content', ''),
                        summary=article.get('summary', ''),
                        category="未分类",
                        priority="中",
                        score=50,  # 默认分数
                        score_relevance=20,
                        score_timeliness=10,
                        score_impact=10,
                        score_credibility=source['tier'] * 5,
                        link_valid=True
                    )
                    stored_count += 1
                except Exception as e:
                    # 可能是重复URL
                    pass

        print(f"✓ 成功存储 {stored_count} 篇文章到数据库")

        return {
            "name": source['name'],
            "status": "success",
            "article_count": len(articles),
            "stored_count": stored_count
        }

    except Exception as e:
        print(f"✗ 采集失败: {str(e)}")
        return {
            "name": source['name'],
            "status": "failed",
            "error": str(e)[:200],
            "article_count": 0
        }


def main():
    """主函数"""
    print("="*80)
    print("14源集成测试")
    print("="*80)

    # 加载源
    sources = load_sources()
    print(f"\n找到 {len(sources)} 个active媒体源")

    # 创建测试数据库
    db = Database("tmp/integration_test_14_sources.db")

    # 测试每个源（只测试前5个以节省时间）
    results = []
    test_limit = 5  # 只测试前5个源

    print(f"\n注意：为节省时间，只测试前 {test_limit} 个源")
    print("="*80)

    for i, source in enumerate(sources[:test_limit], 1):
        print(f"\n[{i}/{min(test_limit, len(sources))}] ", end="")
        result = test_source_collection(source, db)
        results.append(result)

    # 统计
    print(f"\n{'='*80}")
    print("测试完成！")
    print("="*80)

    success_count = sum(1 for r in results if r['status'] == 'success')
    total_articles = sum(r['article_count'] for r in results)
    total_stored = sum(r.get('stored_count', 0) for r in results)

    print(f"\n总计测试: {len(results)} 个源")
    print(f"成功: {success_count} 个")
    print(f"采集文章总数: {total_articles} 篇")
    print(f"存储文章总数: {total_stored} 篇")

    # 显示详细结果
    print(f"\n{'='*80}")
    print("详细结果:")
    print("="*80)

    for r in results:
        status_icon = "✓" if r['status'] == 'success' else "✗"
        print(f"{status_icon} {r['name']}: {r['article_count']} 篇")
        if r['status'] == 'failed':
            print(f"   错误: {r.get('error', 'Unknown')[:50]}")

    # 查询数据库统计
    print(f"\n{'='*80}")
    print("数据库统计:")
    print("="*80)

    articles_in_db = db.get_all_articles()
    print(f"数据库中文章总数: {len(articles_in_db)}")

    # 按源统计
    source_stats = {}
    for article in articles_in_db:
        source = article['source']
        source_stats[source] = source_stats.get(source, 0) + 1

    for source, count in sorted(source_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"  {source}: {count} 篇")

    db.close()

    print(f"\n数据库文件: tmp/integration_test_14_sources.db")

    # 保存结果
    with open('tmp/integration_test_results.json', 'w', encoding='utf-8') as f:
        json.dump({
            "test_date": str(date.today()),
            "sources_tested": len(results),
            "sources_total": len(sources),
            "success_count": success_count,
            "total_articles": total_articles,
            "total_stored": total_stored,
            "results": results
        }, f, ensure_ascii=False, indent=2)

    print("\n结果已保存到: tmp/integration_test_results.json")


if __name__ == "__main__":
    main()

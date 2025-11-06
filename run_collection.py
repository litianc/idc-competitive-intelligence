#!/usr/bin/env python3
"""
IDC行业竞争情报系统 - 生产环境采集脚本

使用方法:
    python3 run_collection.py                # 采集所有active源
    python3 run_collection.py --sources 3    # 只采集前3个源
    python3 run_collection.py --limit 20     # 每个源限制20篇
"""

import json
import sys
import argparse
from datetime import date, datetime
from pathlib import Path

from src.storage.database import Database
from src.scrapers.generic_scraper import GenericScraper
from src.processing.llm_analyzer import LLMArticleAnalyzer  # 新：整合分析器
from src.scoring.priority_scorer import PriorityScorer
from src.classification.category_classifier import CategoryClassifier


def load_active_sources(config_path='config/media-sources.json'):
    """加载所有active媒体源"""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    active_sources = [s for s in config['sources'] if s.get('active', False)]
    return active_sources


def collect_from_source(source, db, llm_analyzer=None, scorer=None, classifier=None, limit=20):
    """从单个源采集文章"""
    print(f"\n{'='*70}")
    print(f"采集源: {source['name']} (Tier {source['tier']})")
    print(f"URL: {source['scraper_config']['list_url']}")
    print(f"{'='*70}")

    # 负面关键词（快速过滤明显不相关的内容）
    NEGATIVE_KEYWORDS = ['白酒', '房地产', '汽车销售', '娱乐', '影视',
                         '游戏', '餐饮', '零售', '服装', '美妆', '食品']

    stats = {
        'source': source['name'],
        'tier': source['tier'],
        'status': 'pending',
        'fetched': 0,
        'quick_filtered': 0,  # 快速过滤数量
        'llm_rejected': 0,    # LLM拒绝数量（相关性<8）
        'stored': 0,
        'duplicates': 0,
        'errors': 0,
        'avg_llm_score': 0,   # 平均LLM评分
        'avg_relevance': 0    # 平均相关性评分
    }

    try:
        # 创建scraper
        scraper = GenericScraper(source)

        # 采集文章
        print(f"正在采集文章（限制{limit}篇）...")
        articles = scraper.fetch_articles(limit=limit)

        if not articles:
            print("⚠️  未采集到文章")
            stats['status'] = 'no_articles'
            return stats

        stats['fetched'] = len(articles)
        print(f"✓ 采集到 {len(articles)} 篇文章")

        # 显示前3篇
        for i, article in enumerate(articles[:3], 1):
            print(f"  [{i}] {article.get('title', 'No title')[:50]}")

        # 处理和存储文章
        llm_scores = []
        relevance_scores = []

        for article in articles:
            if not article.get('title') or not article.get('url'):
                stats['errors'] += 1
                continue

            try:
                # 步骤1：快速预过滤（负面关键词）
                title_lower = article['title'].lower()
                if any(keyword in title_lower for keyword in NEGATIVE_KEYWORDS):
                    stats['quick_filtered'] += 1
                    print(f"    ⊗ 快速过滤: {article['title'][:40]}...")
                    continue

                # 步骤2：LLM智能分析（整合：相关性+重要性+分类+摘要）
                llm_result = None
                if llm_analyzer:
                    try:
                        llm_result = llm_analyzer.analyze_article(
                            title=article['title'],
                            content=article.get('summary', article.get('content', article['title']))
                        )

                        # 步骤3：相关性阈值过滤（<8分拒绝）
                        if llm_result['relevance_score'] < 8:
                            stats['llm_rejected'] += 1
                            print(f"    ✗ LLM拒绝 [{llm_result['relevance_score']}/20]: {article['title'][:40]}...")
                            continue

                        llm_scores.append(llm_result['total_score'])
                        relevance_scores.append(llm_result['relevance_score'])

                        # 使用LLM生成的摘要和分类
                        summary = llm_result['summary']
                        category = llm_result['category']

                        print(f"    ✓ LLM分析 [相关:{llm_result['relevance_score']}/20 重要:{llm_result['importance_score']}/20]: {article['title'][:30]}...")

                    except Exception as e:
                        print(f"    ⚠️  LLM分析失败: {e}")
                        llm_result = None

                # LLM降级处理
                if not llm_result:
                    summary = article.get('summary', '')
                    category = "其他"
                    llm_result = {
                        'relevance_score': 10,
                        'importance_score': 10,
                        'category_score': 5,
                        'total_score': 20,
                        'category': category,
                        'reason': 'LLM不可用，使用默认值'
                    }

                # 步骤4：调用传统评分系统（整合LLM评分）
                if scorer:
                    score_result = scorer.calculate_total_score(
                        title=article['title'],
                        content=article.get('content', ''),
                        publish_date=article.get('publish_date', date.today()),
                        source_tier=source['tier'],
                        llm_total_score=llm_result['total_score']  # 传递LLM评分
                    )
                    score = score_result['total_score']
                    priority = score_result['priority']
                    score_relevance = score_result['relevance_score']
                    score_timeliness = score_result['timeliness_score']
                    score_impact = score_result['impact_score']
                    score_credibility = score_result['credibility_score']
                else:
                    # 降级：使用LLM评分
                    score = llm_result['total_score']
                    priority = "高" if score >= 35 else ("中" if score >= 20 else "低")
                    score_relevance = 0
                    score_timeliness = 0
                    score_impact = 0
                    score_credibility = 0

                # 步骤5：存储到数据库（包含LLM评分）
                db.insert_article(
                    title=article['title'],
                    url=article['url'],
                    source=source['name'],
                    source_tier=source['tier'],
                    publish_date=article.get('publish_date', date.today()),
                    content=article.get('content', ''),
                    summary=summary,
                    category=category,
                    priority=priority,
                    score=score,
                    score_relevance=score_relevance,
                    score_timeliness=score_timeliness,
                    score_impact=score_impact,
                    score_credibility=score_credibility,
                    llm_relevance_score=llm_result['relevance_score'],
                    llm_importance_score=llm_result['importance_score'],
                    llm_category_score=llm_result['category_score'],
                    llm_total_score=llm_result['total_score'],
                    llm_category_suggestion=llm_result['category'],
                    llm_reason=llm_result.get('reason', ''),
                    link_valid=True
                )
                stats['stored'] += 1

            except Exception as e:
                if "UNIQUE constraint failed" in str(e):
                    stats['duplicates'] += 1
                else:
                    stats['errors'] += 1
                    print(f"    ✗ 存储失败: {e}")

        # 计算平均分
        if llm_scores:
            stats['avg_llm_score'] = sum(llm_scores) / len(llm_scores)
            stats['avg_relevance'] = sum(relevance_scores) / len(relevance_scores)

        print(f"✓ 成功存储 {stats['stored']} 篇")
        if stats['quick_filtered'] > 0:
            print(f"  (快速过滤 {stats['quick_filtered']} 篇)")
        if stats['llm_rejected'] > 0:
            print(f"  (LLM拒绝 {stats['llm_rejected']} 篇)")
        if stats['duplicates'] > 0:
            print(f"  (跳过 {stats['duplicates']} 篇重复)")
        if stats['errors'] > 0:
            print(f"  (失败 {stats['errors']} 篇)")
        if stats['avg_llm_score'] > 0:
            print(f"  平均LLM评分: {stats['avg_llm_score']:.1f}/50  平均相关性: {stats['avg_relevance']:.1f}/20")

        stats['status'] = 'success'

    except Exception as e:
        print(f"✗ 采集失败: {str(e)}")
        stats['status'] = 'failed'
        stats['error'] = str(e)[:200]

    return stats


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='IDC行业竞争情报采集')
    parser.add_argument('--sources', type=int, default=None,
                       help='限制采集源数量（测试用）')
    parser.add_argument('--limit', type=int, default=20,
                       help='每个源采集文章数量限制')
    parser.add_argument('--db', type=str, default='data/intelligence.db',
                       help='数据库文件路径')
    parser.add_argument('--no-llm', action='store_true',
                       help='禁用LLM摘要生成')

    args = parser.parse_args()

    print("="*80)
    print("IDC行业竞争情报系统 - 数据采集")
    print("="*80)
    print(f"\n开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 加载媒体源
    sources = load_active_sources()
    print(f"✓ 找到 {len(sources)} 个active媒体源")

    if args.sources:
        sources = sources[:args.sources]
        print(f"  (限制为前 {args.sources} 个源)")

    # 初始化数据库
    db = Database(args.db)
    print(f"✓ 数据库已连接: {args.db}")

    # 初始化LLM智能分析器（整合相关性判断+评分+分类+摘要）
    llm_analyzer = None
    if not args.no_llm:
        try:
            import os
            from dotenv import load_dotenv

            # 加载.env文件
            load_dotenv()

            api_key = os.getenv('LLM_API_KEY')
            api_base = os.getenv('LLM_API_BASE')
            model = os.getenv('LLM_MODEL', 'GLM-4.5-Air')

            if not api_key or not api_base:
                raise ValueError("缺少LLM配置：LLM_API_KEY 或 LLM_API_BASE")

            llm_analyzer = LLMArticleAnalyzer(api_key, api_base, model)
            print(f"✓ LLM智能分析已启用（{model}）")
            print(f"  功能：相关性判断 + 重要性评分 + 分类建议 + 摘要生成")
        except Exception as e:
            print(f"⚠️  LLM分析器初始化失败: {e}")
            print(f"  将使用传统评分系统")

    # 初始化评分和分类系统
    scorer = PriorityScorer()
    classifier = CategoryClassifier()
    print(f"✓ 评分和分类系统已启用")

    # 开始采集
    print(f"\n{'='*80}")
    print(f"开始采集（共 {len(sources)} 个源，每源限制 {args.limit} 篇）")
    print("="*80)

    all_stats = []

    for i, source in enumerate(sources, 1):
        print(f"\n[{i}/{len(sources)}] ", end="")
        stats = collect_from_source(source, db, llm_analyzer, scorer, classifier, args.limit)
        all_stats.append(stats)

    # 汇总统计
    print(f"\n{'='*80}")
    print("采集完成！")
    print("="*80)

    total_fetched = sum(s['fetched'] for s in all_stats)
    total_quick_filtered = sum(s.get('quick_filtered', 0) for s in all_stats)
    total_llm_rejected = sum(s.get('llm_rejected', 0) for s in all_stats)
    total_stored = sum(s['stored'] for s in all_stats)
    total_duplicates = sum(s['duplicates'] for s in all_stats)
    success_count = sum(1 for s in all_stats if s['status'] == 'success')

    # 计算平均LLM评分
    llm_scores = [s.get('avg_llm_score', 0) for s in all_stats if s.get('avg_llm_score', 0) > 0]
    relevance_scores = [s.get('avg_relevance', 0) for s in all_stats if s.get('avg_relevance', 0) > 0]
    avg_llm = sum(llm_scores) / len(llm_scores) if llm_scores else 0
    avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0

    print(f"\n总计:")
    print(f"  测试源数: {len(all_stats)}")
    print(f"  成功源数: {success_count}")
    print(f"  采集文章: {total_fetched} 篇")
    print(f"  快速过滤: {total_quick_filtered} 篇（负面关键词）")
    print(f"  LLM拒绝: {total_llm_rejected} 篇（相关性<8分）")
    print(f"  成功存储: {total_stored} 篇")
    print(f"  重复跳过: {total_duplicates} 篇")
    if avg_llm > 0:
        print(f"  平均LLM评分: {avg_llm:.1f}/50")
        print(f"  平均相关性: {avg_relevance:.1f}/20")

    # 按源统计
    print(f"\n按源统计:")
    for stats in all_stats:
        status_icon = "✓" if stats['status'] == 'success' else "✗"
        print(f"  {status_icon} {stats['source']}: {stats['stored']}篇")

    # 数据库统计
    all_articles = db.get_all_articles()
    print(f"\n数据库总计:")
    print(f"  总文章数: {len(all_articles)} 篇")

    # 按源统计
    source_counts = {}
    for article in all_articles:
        source = article['source']
        source_counts[source] = source_counts.get(source, 0) + 1

    print(f"\n  分源统计:")
    for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"    {source}: {count} 篇")

    db.close()

    print(f"\n结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)


if __name__ == "__main__":
    main()

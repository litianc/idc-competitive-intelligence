"""
使用样本数据演示系统功能

展示数据处理、评分、分类的完整流程
"""

import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.storage.database import Database
import re


class SimpleScorer:
    """简化版评分器"""

    def __init__(self):
        self.keywords = {
            "core": ["IDC", "数据中心", "云计算", "云服务", "AI算力", "GPU", "算力中心"],
            "secondary": ["服务器", "机柜", "机房", "液冷", "制冷", "边缘计算", "CDN"],
        }

    def score_article(self, title, content, publish_date, source_tier):
        """评分文章"""
        # 1. 业务相关性（40分）
        text = (title + " " + content).lower()
        relevance = 0
        for keyword in self.keywords["core"]:
            if keyword.lower() in text:
                relevance += 10
        for keyword in self.keywords["secondary"]:
            if keyword.lower() in text:
                relevance += 5
        relevance = min(relevance, 40)

        # 2. 时效性（25分）
        days_ago = (date.today() - publish_date).days
        if days_ago >= 7:
            timeliness = 0
        else:
            timeliness = int(25 * (1 - days_ago / 7))

        # 3. 影响范围（20分）
        impact = 0
        # 检查融资金额
        if re.search(r"(\d+)亿", text):
            amount_match = re.search(r"(\d+)亿", text)
            if amount_match:
                amount = int(amount_match.group(1))
                if amount >= 10:
                    impact = 20
                elif amount >= 5:
                    impact = 15
                elif amount >= 1:
                    impact = 10
                else:
                    impact = 5
        # 检查其他影响指标
        elif "标准" in text or "规范" in text:
            impact = 20
        elif "突破" in text:
            impact = 18
        elif "战略" in text or "合作" in text:
            impact = 15
        elif "发布" in text or "推出" in text:
            impact = 10

        # 4. 来源可信度（15分）
        credibility = {1: 15, 2: 8, 3: 3}.get(source_tier, 8)

        total = relevance + timeliness + impact + credibility

        # 优先级映射
        if total >= 70:
            priority = "高"
        elif total >= 40:
            priority = "中"
        else:
            priority = "低"

        return {
            "total_score": total,
            "relevance_score": relevance,
            "timeliness_score": timeliness,
            "impact_score": impact,
            "credibility_score": credibility,
            "priority": priority,
        }


class SimpleClassifier:
    """简化版分类器"""

    def __init__(self):
        self.categories = {
            "投资": ["融资", "投资", "并购", "收购", "IPO", "上市", "估值"],
            "技术": ["GPU", "芯片", "液冷", "技术", "发布", "突破", "性能", "算力"],
            "政策": ["政策", "法规", "标准", "规范", "规划", "监管", "工信部"],
            "市场": ["市场", "份额", "增长", "报告", "趋势", "需求"],
        }

    def classify(self, title, content):
        """分类文章"""
        text = (title + " " + content).lower()

        for category, keywords in self.categories.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    return category

        return "其他"


def create_sample_data():
    """创建样本数据"""
    today = date.today()

    samples = [
        {
            "title": "某云计算公司完成15亿元C轮融资，加码AI算力数据中心建设",
            "url": "https://www.idcquan.com/article/001.html",
            "source": "中国IDC圈",
            "source_tier": 1,
            "publish_date": today,
            "content": """
                某知名云计算公司今日宣布完成15亿元人民币C轮融资，本轮融资由多家知名投资机构领投。
                该公司表示，此次融资将主要用于扩建AI算力数据中心，计划在北京、上海、深圳三地新建
                超大型数据中心，总规模达到5万个机柜，重点部署GPU算力集群，为AI大模型训练和推理
                提供基础设施支持。此次融资创下2025年IDC行业单笔融资纪录。
            """,
        },
        {
            "title": "新型浸没式液冷技术突破PUE 1.1极限，能效提升60%",
            "url": "https://www.dcworld.cn/article/002.html",
            "source": "数据中心世界",
            "source_tier": 1,
            "publish_date": today - timedelta(days=1),
            "content": """
                某科技公司研发的新一代浸没式液冷系统在实际部署中实现PUE 1.08，打破行业纪录。
                该技术采用全新环保冷却液，相比传统风冷降低能耗60%，单机柜功率密度可达100kW。
                目前已在多个超算中心试点应用，预计第二季度投入商业化，将大幅降低数据中心运营成本。
            """,
        },
        {
            "title": "工信部发布数据中心能效新标准，2027年全面实施",
            "url": "https://www.cww.net.cn/article/003.html",
            "source": "通信世界网",
            "source_tier": 2,
            "publish_date": today - timedelta(days=2),
            "content": """
                工信部正式发布《数据中心能效限定值及能效等级》强制性国家标准，要求新建大型
                数据中心PUE不超过1.3，2027年起全面实施。标准明确了分级评价体系，推动行业
                绿色低碳转型，预计将影响全国在建的100余个数据中心项目。
            """,
        },
        {
            "title": "2024年中国IDC市场规模突破3000亿元，同比增长28%",
            "url": "https://www.idcquan.com/article/004.html",
            "source": "中国IDC圈",
            "source_tier": 1,
            "publish_date": today - timedelta(days=2),
            "content": """
                权威研究机构发布年度报告，2024年中国IDC市场规模达3200亿元，同比增长28%。
                AI算力需求爆发是主要驱动因素，智算中心投资占比首超50%。预测2025年市场将
                保持25%高增长，总规模有望达到4000亿元。
            """,
        },
        {
            "title": "某云服务商并购区域数据中心运营商，交易金额8亿元",
            "url": "https://www.idcquan.com/article/005.html",
            "source": "中国IDC圈",
            "source_tier": 1,
            "publish_date": today - timedelta(days=3),
            "content": """
                国内领先云服务商宣布以8亿元收购华东地区数据中心运营商，获得5000个机柜资源。
                此举将增强其区域覆盖能力，完善混合云战略布局。交易预计Q2完成，被收购方
                现有客户将平稳过渡。
            """,
        },
        {
            "title": "国产AI芯片性能达国际先进水平，算力提升50%",
            "url": "https://www.cww.net.cn/article/006.html",
            "source": "通信世界网",
            "source_tier": 2,
            "publish_date": today - timedelta(days=4),
            "content": """
                国内芯片厂商发布第三代AI训练芯片，FP16算力达800 TFLOPS，能效比提升50%。
                该芯片已通过多个大模型训练验证，性能对标国际主流产品。将于Q2量产，
                为国产算力基础设施提供核心支撑。
            """,
        },
        {
            "title": "某地区启动数据中心集群规划，2030年建成20万机柜",
            "url": "https://www.cww.net.cn/article/007.html",
            "source": "通信世界网",
            "source_tier": 2,
            "publish_date": today - timedelta(days=5),
            "content": """
                西部某省发布数据中心产业发展规划，计划2030年建成20万机柜规模。
                将重点发展绿色数据中心和智算中心，吸引更多互联网企业入驻。
            """,
        },
        {
            "title": "数据中心运维标准化论坛成功召开",
            "url": "https://www.dcworld.cn/article/008.html",
            "source": "数据中心世界",
            "source_tier": 1,
            "publish_date": today - timedelta(days=6),
            "content": """
                行业协会组织运维标准化论坛，100余家企业参与讨论最佳实践。
                论坛围绕智能运维、故障预测、能耗优化等议题展开交流。
            """,
        },
        {
            "title": "某公司推出边缘计算解决方案，支持5G网络",
            "url": "https://www.dcworld.cn/article/009.html",
            "source": "数据中心世界",
            "source_tier": 1,
            "publish_date": today - timedelta(days=7),
            "content": """
                某公司发布新一代边缘计算解决方案，专为5G网络优化设计。
                该方案可降低延迟30%，提升网络边缘处理能力。
            """,
        },
        {
            "title": "数据中心行业人才培养计划启动",
            "url": "https://www.cww.net.cn/article/010.html",
            "source": "通信世界网",
            "source_tier": 2,
            "publish_date": today - timedelta(days=8),
            "content": """
                行业协会联合多家企业启动人才培养计划，未来三年培养5000名
                数据中心专业人才，涵盖运维、管理、技术等多个方向。
            """,
        },
    ]

    return samples


def main():
    """主函数"""
    print("=" * 70)
    print("中国IDC行业竞争情报系统 - 数据处理演示")
    print("=" * 70)

    # 初始化
    scorer = SimpleScorer()
    classifier = SimpleClassifier()
    db = Database("tmp/demo_intelligence.db")

    # 加载样本数据
    samples = create_sample_data()
    print(f"\n加载了 {len(samples)} 篇样本文章\n")

    # 处理每篇文章
    print("开始处理文章...")
    print("-" * 70)

    for idx, article in enumerate(samples, 1):
        # 评分
        scores = scorer.score_article(
            article["title"],
            article["content"],
            article["publish_date"],
            article["source_tier"],
        )

        # 分类
        category = classifier.classify(article["title"], article["content"])

        # 保存到数据库
        article_id = db.insert_article(
            title=article["title"],
            url=article["url"],
            source=article["source"],
            source_tier=article["source_tier"],
            publish_date=article["publish_date"],
            content=article["content"],
            category=category,
            priority=scores["priority"],
            score=scores["total_score"],
        )

        if article_id:
            # 更新评分详情
            db.update_article_scores(
                article_id=article_id,
                category=category,
                priority=scores["priority"],
                score=scores["total_score"],
                score_relevance=scores["relevance_score"],
                score_timeliness=scores["timeliness_score"],
                score_impact=scores["impact_score"],
                score_credibility=scores["credibility_score"],
            )

            print(f"✓ [{idx:2d}] [{scores['priority']}] [{category:4s}] "
                  f"{scores['total_score']:3d}分 - {article['title'][:45]}...")

    print("-" * 70)
    print(f"✅ 成功处理 {len(samples)} 篇文章\n")

    # 统计分析
    print("=" * 70)
    print("数据分析结果")
    print("=" * 70)

    all_articles = db.get_all_articles()

    # 按优先级分组
    by_priority = {"高": [], "中": [], "低": []}
    for art in all_articles:
        priority = art.get("priority", "低")
        if priority in by_priority:
            by_priority[priority].append(art)

    # 按分类统计
    by_category = {}
    for art in all_articles:
        cat = art.get("category", "其他")
        by_category[cat] = by_category.get(cat, 0) + 1

    print(f"\n📊 总文章数: {len(all_articles)}")

    print(f"\n📈 优先级分布:")
    print(f"   ⭐️ 高优先级: {len(by_priority['高'])} 篇 ({len(by_priority['高'])*100//len(all_articles)}%)")
    print(f"   🔸 中优先级: {len(by_priority['中'])} 篇 ({len(by_priority['中'])*100//len(all_articles)}%)")
    print(f"   ⚪️ 低优先级: {len(by_priority['低'])} 篇 ({len(by_priority['低'])*100//len(all_articles)}%)")

    print(f"\n🏷️  分类分布:")
    for cat, count in sorted(by_category.items(), key=lambda x: -x[1]):
        print(f"   {cat}: {count} 篇 ({count*100//len(all_articles)}%)")

    # 详细展示高优先级文章
    if by_priority["高"]:
        print(f"\n{'=' * 70}")
        print("⭐️ 高优先级文章详情")
        print("=" * 70)
        for art in by_priority["高"]:
            print(f"\n【{art['category']}】{art['title']}")
            print(f"  📅 日期: {art['publish_date']} | 📰 来源: {art['source']}")
            print(f"  🎯 总分: {art['score']}分 | 优先级: {art['priority']}")
            print(f"  📊 评分详情:")
            print(f"     - 业务相关性: {art['score_relevance']}/40分")
            print(f"     - 时效性: {art['score_timeliness']}/25分")
            print(f"     - 影响范围: {art['score_impact']}/20分")
            print(f"     - 来源可信度: {art['score_credibility']}/15分")
            print(f"  🔗 链接: {art['url']}")

    # 展示中优先级示例
    if by_priority["中"]:
        print(f"\n{'=' * 70}")
        print("🔸 中优先级文章示例（前3篇）")
        print("=" * 70)
        for art in by_priority["中"][:3]:
            print(f"\n【{art['category']}】{art['title']}")
            print(f"  🎯 评分: {art['score']}分 | 📰 {art['source']} | 📅 {art['publish_date']}")

    # 周报数据预览
    print(f"\n{'=' * 70}")
    print("📅 过去7天数据（周报范围）")
    print("=" * 70)

    weekly_articles = db.get_articles_for_weekly_report(days=7)
    print(f"\n过去7天共 {len(weekly_articles)} 篇文章")
    print(f"  - 高优先级: {len([a for a in weekly_articles if a.get('priority') == '高'])} 篇")
    print(f"  - 中优先级: {len([a for a in weekly_articles if a.get('priority') == '中'])} 篇")
    print(f"  - 低优先级: {len([a for a in weekly_articles if a.get('priority') == '低'])} 篇")

    print(f"\n{'=' * 70}")
    print(f"💾 数据已保存到: tmp/demo_intelligence.db")
    print(f"   可使用 sqlite3 命令行工具查看详细数据")
    print("=" * 70)

    db.close()


if __name__ == "__main__":
    main()

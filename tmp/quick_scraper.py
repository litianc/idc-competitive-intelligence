"""
快速爬虫演示脚本

用于快速验证数据抓取效果，不需要完整的测试框架
抓取中国IDC圈的最新文章并展示
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, date, timedelta
import time
import random
import re
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.storage.database import Database


class QuickScraper:
    """快速爬虫类"""

    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        ]

    def get_headers(self):
        """获取随机User-Agent"""
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

    def scrape_idcquan(self, max_articles=10):
        """
        抓取中国IDC圈的文章

        Args:
            max_articles: 最多抓取的文章数

        Returns:
            文章列表
        """
        print(f"\n开始抓取中国IDC圈...")
        articles = []

        try:
            # 抓取列表页
            url = "https://www.idcquan.com/Special/idc/"
            print(f"访问: {url}")

            response = requests.get(url, headers=self.get_headers(), timeout=10)
            response.encoding = "utf-8"

            if response.status_code != 200:
                print(f"❌ 请求失败: {response.status_code}")
                return articles

            soup = BeautifulSoup(response.text, "html.parser")

            # 查找文章列表（需要根据实际页面结构调整）
            article_items = soup.find_all("div", class_="news-list-item")

            if not article_items:
                # 尝试其他选择器
                article_items = soup.find_all("li", class_="item")

            if not article_items:
                # 再尝试通用选择器
                article_items = soup.find_all("a", href=re.compile(r"/\d+\.html"))

            print(f"找到 {len(article_items)} 个潜在文章")

            for idx, item in enumerate(article_items[:max_articles]):
                try:
                    # 尝试提取标题和链接
                    if item.name == "a":
                        title_elem = item
                        link = item.get("href", "")
                    else:
                        title_elem = item.find("a")
                        link = title_elem.get("href", "") if title_elem else ""

                    if not title_elem or not link:
                        continue

                    title = title_elem.get_text(strip=True)

                    # 补全URL
                    if link.startswith("/"):
                        link = "https://www.idcquan.com" + link
                    elif not link.startswith("http"):
                        link = "https://www.idcquan.com/" + link

                    # 尝试提取日期
                    date_elem = item.find("span", class_="time")
                    if not date_elem:
                        date_elem = item.find(string=re.compile(r"\d{4}-\d{2}-\d{2}"))

                    publish_date = self.parse_date(
                        date_elem.get_text(strip=True) if date_elem else ""
                    )

                    # 简单的内容预览（标题本身）
                    article = {
                        "title": title,
                        "url": link,
                        "source": "中国IDC圈",
                        "source_tier": 1,
                        "publish_date": publish_date,
                        "content": title,  # 临时使用标题作为内容
                    }

                    articles.append(article)
                    print(f"  ✓ [{idx + 1}] {title[:50]}...")

                    # 礼貌延迟
                    time.sleep(random.uniform(0.5, 1.5))

                except Exception as e:
                    print(f"  ✗ 解析文章失败: {e}")
                    continue

        except Exception as e:
            print(f"❌ 抓取失败: {e}")

        print(f"✅ 成功抓取 {len(articles)} 篇文章\n")
        return articles

    def parse_date(self, date_str):
        """
        解析日期字符串

        Args:
            date_str: 日期字符串

        Returns:
            date对象
        """
        if not date_str:
            return date.today()

        date_str = date_str.strip()

        # 匹配 YYYY-MM-DD
        match = re.search(r"(\d{4})-(\d{2})-(\d{2})", date_str)
        if match:
            return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))

        # 匹配 YYYY年MM月DD日
        match = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", date_str)
        if match:
            return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))

        # 匹配相对时间
        if "今天" in date_str or "刚刚" in date_str:
            return date.today()

        match = re.search(r"(\d+)天前", date_str)
        if match:
            days = int(match.group(1))
            return date.today() - timedelta(days=days)

        match = re.search(r"(\d+)小时前", date_str)
        if match:
            return date.today()

        # 默认返回今天
        return date.today()


class SimpleScorer:
    """简化版评分器"""

    def __init__(self):
        self.keywords = {
            "core": ["IDC", "数据中心", "云计算", "云服务", "AI算力", "GPU", "算力"],
            "secondary": ["服务器", "机柜", "机房", "液冷", "边缘计算"],
        }

    def score_article(self, title, content, publish_date, source_tier):
        """
        评分文章

        Returns:
            dict with scores and priority
        """
        # 1. 业务相关性（简化版）
        text = (title + " " + content).lower()
        relevance = 0
        for keyword in self.keywords["core"]:
            if keyword.lower() in text:
                relevance += 10
        for keyword in self.keywords["secondary"]:
            if keyword.lower() in text:
                relevance += 5
        relevance = min(relevance, 40)

        # 2. 时效性
        days_ago = (date.today() - publish_date).days
        if days_ago >= 7:
            timeliness = 0
        else:
            timeliness = int(25 * (1 - days_ago / 7))

        # 3. 影响范围（简化版）
        impact = 0
        if re.search(r"(\d+)亿", text):
            impact = 15
        elif "融资" in text or "并购" in text:
            impact = 10

        # 4. 来源可信度
        credibility = {1: 15, 2: 8, 3: 3}.get(source_tier, 8)

        total = relevance + timeliness + impact + credibility

        # 优先级
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
            "投资": ["融资", "投资", "并购", "收购", "IPO", "上市"],
            "技术": ["GPU", "芯片", "液冷", "技术", "发布", "突破"],
            "政策": ["政策", "法规", "标准", "规划", "监管"],
            "市场": ["市场", "份额", "增长", "报告", "趋势"],
        }

    def classify(self, title, content):
        """
        分类文章

        Returns:
            分类名称
        """
        text = (title + " " + content).lower()

        for category, keywords in self.categories.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    return category

        return "其他"


def main():
    """主函数"""
    print("=" * 60)
    print("中国IDC行业竞争情报系统 - 快速数据抓取演示")
    print("=" * 60)

    # 初始化
    scraper = QuickScraper()
    scorer = SimpleScorer()
    classifier = SimpleClassifier()
    db = Database("tmp/test_scraping.db")

    # 抓取数据
    articles = scraper.scrape_idcquan(max_articles=10)

    if not articles:
        print("⚠️  未抓取到文章，可能需要调整选择器或网络问题")
        return

    # 处理和保存
    print("处理并保存文章...")
    saved_count = 0

    for article in articles:
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
            saved_count += 1

    print(f"✅ 成功保存 {saved_count} 篇文章\n")

    # 展示结果
    print("=" * 60)
    print("抓取结果汇总")
    print("=" * 60)

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

    print(f"\n总文章数: {len(all_articles)}")
    print(f"\n优先级分布:")
    print(f"  高: {len(by_priority['高'])} 篇")
    print(f"  中: {len(by_priority['中'])} 篇")
    print(f"  低: {len(by_priority['低'])} 篇")

    print(f"\n分类分布:")
    for cat, count in sorted(by_category.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count} 篇")

    # 展示高优先级文章
    if by_priority["高"]:
        print(f"\n{'=' * 60}")
        print("高优先级文章详情")
        print("=" * 60)
        for art in by_priority["高"]:
            print(f"\n【{art['category']}】{art['title']}")
            print(f"  来源: {art['source']} | 日期: {art['publish_date']}")
            print(f"  评分: {art['score']}分 (相关性:{art['score_relevance']} "
                  f"时效性:{art['score_timeliness']} "
                  f"影响:{art['score_impact']} "
                  f"可信度:{art['score_credibility']})")
            print(f"  链接: {art['url']}")

    # 展示中优先级示例
    if by_priority["中"]:
        print(f"\n{'=' * 60}")
        print("中优先级文章示例（前3篇）")
        print("=" * 60)
        for art in by_priority["中"][:3]:
            print(f"\n【{art['category']}】{art['title']}")
            print(f"  评分: {art['score']}分 | {art['source']} | {art['publish_date']}")

    print(f"\n{'=' * 60}")
    print(f"数据已保存到: tmp/test_scraping.db")
    print("=" * 60)

    db.close()


if __name__ == "__main__":
    main()

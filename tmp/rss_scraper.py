"""
RSS订阅爬虫

优先使用RSS方式抓取新闻，更稳定可靠
"""

import requests
import xml.etree.ElementTree as ET
from datetime import datetime, date
import sys
import os
import time
import random
from html import unescape

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.storage.database import Database


class RSSFeedScraper:
    """RSS订阅爬虫"""

    def __init__(self):
        self.user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

    def get_headers(self):
        """获取请求头"""
        return {
            "User-Agent": self.user_agent,
            "Accept": "application/rss+xml, application/xml, text/xml",
        }

    def fetch_rss(self, url, max_items=20):
        """
        抓取RSS feed

        Args:
            url: RSS订阅地址
            max_items: 最多获取的条目数

        Returns:
            文章列表
        """
        print(f"\n正在获取RSS: {url}")

        try:
            response = requests.get(url, headers=self.get_headers(), timeout=10)
            response.encoding = "utf-8"

            if response.status_code != 200:
                print(f"❌ 请求失败: {response.status_code}")
                return []

            # 解析XML
            root = ET.fromstring(response.content)

            # 判断RSS格式（RSS 2.0 或 Atom）
            if root.tag == "rss":
                return self._parse_rss2(root, max_items)
            elif "feed" in root.tag.lower():
                return self._parse_atom(root, max_items)
            else:
                print(f"❌ 未知的RSS格式: {root.tag}")
                return []

        except Exception as e:
            print(f"❌ 抓取RSS失败: {e}")
            return []

    def _parse_rss2(self, root, max_items):
        """解析RSS 2.0格式"""
        articles = []

        channel = root.find("channel")
        if not channel:
            return articles

        items = channel.findall("item")[:max_items]

        for item in items:
            try:
                title_elem = item.find("title")
                link_elem = item.find("link")
                pubdate_elem = item.find("pubDate")
                description_elem = item.find("description")

                if not title_elem or not link_elem:
                    continue

                title = unescape(title_elem.text or "")
                link = link_elem.text or ""
                description = unescape(description_elem.text or "") if description_elem else ""

                # 解析日期
                publish_date = self._parse_date(pubdate_elem.text if pubdate_elem else "")

                article = {
                    "title": title.strip(),
                    "url": link.strip(),
                    "content": description.strip(),
                    "publish_date": publish_date,
                }

                articles.append(article)

            except Exception as e:
                print(f"  ✗ 解析条目失败: {e}")
                continue

        return articles

    def _parse_atom(self, root, max_items):
        """解析Atom格式"""
        articles = []

        # Atom命名空间
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        entries = root.findall("atom:entry", ns)[:max_items]

        for entry in entries:
            try:
                title_elem = entry.find("atom:title", ns)
                link_elem = entry.find("atom:link", ns)
                published_elem = entry.find("atom:published", ns)
                summary_elem = entry.find("atom:summary", ns)

                if not title_elem or not link_elem:
                    continue

                title = unescape(title_elem.text or "")
                link = link_elem.get("href", "")
                summary = unescape(summary_elem.text or "") if summary_elem else ""

                publish_date = self._parse_date(published_elem.text if published_elem else "")

                article = {
                    "title": title.strip(),
                    "url": link.strip(),
                    "content": summary.strip(),
                    "publish_date": publish_date,
                }

                articles.append(article)

            except Exception as e:
                print(f"  ✗ 解析条目失败: {e}")
                continue

        return articles

    def _parse_date(self, date_str):
        """
        解析日期字符串

        支持多种格式：
        - RFC 822: Mon, 03 Nov 2025 14:30:00 +0800
        - ISO 8601: 2025-11-03T14:30:00+08:00
        """
        if not date_str:
            return date.today()

        try:
            # 尝试RFC 822格式（RSS 2.0）
            dt = datetime.strptime(date_str[:25], "%a, %d %b %Y %H:%M:%S")
            return dt.date()
        except:
            pass

        try:
            # 尝试ISO 8601格式（Atom）
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.date()
        except:
            pass

        # 默认返回今天
        return date.today()


# 常见的RSS feed地址（需要实际验证）
RSS_FEEDS = {
    "中国IDC圈": "https://www.idcquan.com/rss.xml",
    "数据中心世界": "https://www.dcworld.cn/rss.xml",
    "通信世界网": "https://www.cww.net.cn/rss.xml",
}


def main():
    """主函数"""
    print("=" * 70)
    print("RSS订阅爬虫演示")
    print("=" * 70)

    scraper = RSSFeedScraper()

    # 尝试抓取各个RSS源
    all_articles = []

    for source, rss_url in RSS_FEEDS.items():
        print(f"\n尝试抓取: {source}")
        articles = scraper.fetch_rss(rss_url, max_items=10)

        if articles:
            print(f"✅ 成功获取 {len(articles)} 篇文章")
            for article in articles:
                article["source"] = source
                article["source_tier"] = 1 if source == "中国IDC圈" else 1 if source == "数据中心世界" else 2
                all_articles.append(article)
        else:
            print(f"⚠️  {source} RSS可能不可用，跳过")

        # 礼貌延迟
        time.sleep(random.uniform(1, 2))

    if not all_articles:
        print("\n⚠️  未能通过RSS获取到文章")
        print("\n💡 建议：")
        print("1. 检查网站是否提供RSS订阅")
        print("2. 查找RSS feed的实际URL")
        print("3. 考虑使用网站提供的API")
        print("4. 如果都不可用，再考虑网页爬虫")
        return

    print(f"\n{'=' * 70}")
    print(f"总共获取 {len(all_articles)} 篇文章")
    print("=" * 70)

    # 展示部分文章
    print("\n文章示例:")
    for idx, article in enumerate(all_articles[:5], 1):
        print(f"\n[{idx}] {article['title']}")
        print(f"    来源: {article['source']} | 日期: {article['publish_date']}")
        print(f"    链接: {article['url']}")


if __name__ == "__main__":
    main()

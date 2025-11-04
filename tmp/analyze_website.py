"""
网站结构分析工具

帮助分析目标网站的HTML结构，找出文章列表的选择器
"""

import requests
from bs4 import BeautifulSoup
import sys


def analyze_website(url):
    """分析网站结构"""
    print(f"\n{'=' * 70}")
    print(f"分析网站: {url}")
    print("=" * 70)

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = "utf-8"

        if response.status_code != 200:
            print(f"❌ 请求失败: {response.status_code}")
            return

        print(f"✅ 页面加载成功\n")

        soup = BeautifulSoup(response.text, "html.parser")

        # 分析可能的文章列表容器
        print("📋 可能的文章列表容器:\n")

        # 查找常见的列表容器
        common_selectors = [
            ("ul.news-list", "新闻列表(ul)"),
            ("div.news-list", "新闻列表(div)"),
            ("ul.article-list", "文章列表(ul)"),
            ("div.article-list", "文章列表(div)"),
            ("div.list", "通用列表"),
            ("ul.list", "通用列表(ul)"),
        ]

        found_containers = []

        for selector, description in common_selectors:
            elements = soup.select(selector)
            if elements:
                found_containers.append((selector, len(elements), description))
                print(f"  ✓ {selector:30s} - 找到 {len(elements)} 个 ({description})")

        # 查找包含多个链接的div/ul
        print("\n📦 包含多个链接的容器:\n")

        divs_with_links = []
        for div in soup.find_all(["div", "ul", "ol"]):
            links = div.find_all("a", recursive=False)
            if len(links) >= 3:  # 至少3个链接
                classes = " ".join(div.get("class", []))
                div_id = div.get("id", "")
                selector = f"{div.name}"
                if div_id:
                    selector += f"#{div_id}"
                if classes:
                    selector += f".{classes.split()[0]}"

                divs_with_links.append((selector, len(links)))

        # 按链接数量排序
        divs_with_links.sort(key=lambda x: -x[1])

        for selector, link_count in divs_with_links[:10]:
            print(f"  • {selector:40s} - {link_count} 个链接")

        # 分析所有链接
        print(f"\n🔗 页面链接分析:\n")

        all_links = soup.find_all("a", href=True)
        print(f"  总链接数: {len(all_links)}")

        # 分析链接模式
        internal_links = []
        for link in all_links:
            href = link.get("href", "")
            text = link.get_text(strip=True)

            # 可能是文章链接
            if text and len(text) > 10 and (".html" in href or "/article/" in href or "/news/" in href):
                internal_links.append({
                    "text": text[:60],
                    "href": href,
                    "parent": link.parent.name if link.parent else ""
                })

        if internal_links:
            print(f"\n  可能的文章链接 (前10个):\n")
            for i, link in enumerate(internal_links[:10], 1):
                print(f"    [{i}] {link['text']}")
                print(f"        URL: {link['href']}")
                print(f"        父元素: <{link['parent']}>")
                print()

        # 分析时间元素
        print("⏰ 可能的时间元素:\n")

        time_patterns = [
            "span.time",
            "span.date",
            "div.date",
            "time",
            ".publish-time",
            ".update-time"
        ]

        for pattern in time_patterns:
            elements = soup.select(pattern)
            if elements:
                example = elements[0].get_text(strip=True)
                print(f"  ✓ {pattern:25s} - 找到 {len(elements)} 个, 示例: {example}")

        print(f"\n{'=' * 70}")
        print("💡 建议的配置:")
        print("=" * 70)

        if found_containers:
            selector, count, desc = found_containers[0]
            print(f"\n文章列表容器: {selector}")

        if internal_links:
            print(f"文章链接数量: {len(internal_links)}")
            print(f"\n需要在浏览器中检查:")
            print(f"1. 文章列表的具体CSS类名")
            print(f"2. 每篇文章的容器元素")
            print(f"3. 标题、日期、链接的选择器")

    except Exception as e:
        print(f"❌ 分析失败: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python analyze_website.py <URL>")
        print("\n示例:")
        print("  python analyze_website.py https://www.idcquan.com/news/")
        print("  python analyze_website.py https://www.dcworld.cn/")
        sys.exit(1)

    url = sys.argv[1]
    analyze_website(url)

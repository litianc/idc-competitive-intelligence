"""
详细分析6个主流科技媒体的结构
"""

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
import re


SOURCES = [
    {"name": "IT之家", "url": "https://www.ithome.com", "list_url": "https://www.ithome.com/"},
    {"name": "驱动之家", "url": "https://www.mydrivers.com", "list_url": "https://www.mydrivers.com/"},
    {"name": "新浪科技", "url": "https://tech.sina.com.cn", "list_url": "https://tech.sina.com.cn/"},
    {"name": "腾讯科技", "url": "https://tech.qq.com", "list_url": "https://tech.qq.com/"},
    {"name": "网易科技", "url": "https://tech.163.com", "list_url": "https://tech.163.com/"},
    {"name": "搜狐科技", "url": "https://it.sohu.com", "list_url": "https://it.sohu.com/"},
]


def analyze_source(source, playwright):
    """详细分析单个源"""
    print(f"\n{'='*70}")
    print(f"分析: {source['name']}")
    print(f"{'='*70}")

    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(source['list_url'], wait_until='domcontentloaded', timeout=15000)
    page.wait_for_timeout(3000)

    html = page.content()
    soup = BeautifulSoup(html, 'lxml')

    result = {
        "name": source['name'],
        "url": source['url'],
        "list_url": source['list_url'],
        "recommended_config": {}
    }

    # 查找文章链接和标题
    article_analysis = analyze_articles(soup, source['name'])
    result["article_analysis"] = article_analysis

    # 推荐配置
    if article_analysis['title_candidates']:
        best = article_analysis['title_candidates'][0]
        result["recommended_config"] = {
            "scraper_type": "generic",
            "list_url": source['list_url'],
            "encoding": "utf-8",
            "article_container": best.get('container', 'div'),
            "title_selector": best['selector'],
            "link_selector": best['selector'],
            "date_selector": best.get('date_selector', 'span.time'),
        }

        print(f"\n推荐配置:")
        print(f"  article_container: {best.get('container', 'div')}")
        print(f"  title_selector: {best['selector']}")
        print(f"  示例: {best['sample_text'][:50]}")

    browser.close()
    return result


def analyze_articles(soup, source_name):
    """分析文章结构"""
    candidates = []

    # 查找所有带href的链接，文本长度>15
    links = soup.find_all('a', href=True)

    for link in links[:30]:
        text = link.get_text(strip=True)
        href = link.get('href', '')

        if len(text) < 15 or len(text) > 100:
            continue

        if any(x in href for x in ['javascript:', '#']):
            continue

        # 构建选择器
        selector = "a"
        if link.get('class'):
            classes = link.get('class')
            if classes:
                selector = f"a.{classes[0]}"

        # 查找父容器
        parent = link.parent
        container = parent.name if parent else 'div'
        if parent and parent.get('class'):
            container = f"{parent.name}.{parent.get('class')[0]}"

        candidates.append({
            "selector": selector,
            "container": container,
            "sample_text": text,
            "sample_href": href[:80],
            "date_selector": "span.time"  # 默认
        })

    # 去重
    seen = set()
    unique = []
    for c in candidates:
        key = c['selector']
        if key not in seen:
            seen.add(key)
            unique.append(c)

    return {
        "title_candidates": unique[:5]
    }


def main():
    with sync_playwright() as p:
        results = []
        for source in SOURCES:
            try:
                result = analyze_source(source, p)
                results.append(result)
            except Exception as e:
                print(f"✗ 分析失败: {e}")
                results.append({
                    "name": source['name'],
                    "status": "failed",
                    "error": str(e)
                })

    # 保存
    with open('tmp/6_mainstream_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*70}")
    print("分析完成!")
    print("="*70)


if __name__ == "__main__":
    main()

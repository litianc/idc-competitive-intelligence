"""
快速测试几个额外的科技媒体源
"""

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json


# 额外测试的媒体源
ADDITIONAL_SOURCES = [
    {
        "name": "IT之家",
        "url": "https://www.ithome.com",
        "list_url": "https://www.ithome.com/",
        "tier": 2,
    },
    {
        "name": "驱动之家",
        "url": "https://www.mydrivers.com",
        "list_url": "https://www.mydrivers.com/",
        "tier": 2,
    },
    {
        "name": "新浪科技",
        "url": "https://tech.sina.com.cn",
        "list_url": "https://tech.sina.com.cn/",
        "tier": 2,
    },
    {
        "name": "腾讯科技",
        "url": "https://tech.qq.com",
        "list_url": "https://tech.qq.com/",
        "tier": 2,
    },
    {
        "name": "网易科技",
        "url": "https://tech.163.com",
        "list_url": "https://tech.163.com/",
        "tier": 2,
    },
    {
        "name": "搜狐科技",
        "url": "https://it.sohu.com",
        "list_url": "https://it.sohu.com/",
        "tier": 2,
    },
]


def quick_test(source):
    """快速测试网站是否可访问并有内容"""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            print(f"\n测试: {source['name']} - {source['list_url']}")
            page.goto(source['list_url'], wait_until='domcontentloaded', timeout=10000)
            page.wait_for_timeout(2000)

            html = page.content()
            soup = BeautifulSoup(html, 'lxml')

            # 快速检查：是否有文章链接
            links = soup.find_all('a', href=True)
            article_links = [l for l in links if l.get_text(strip=True) and len(l.get_text(strip=True)) > 15]

            print(f"  ✓ HTML长度: {len(html):,}")
            print(f"  ✓ 找到 {len(article_links)} 个可能的文章链接")

            # 检查常见的文章容器
            containers = []
            for pattern in ['article', 'news', 'item', 'list', 'post']:
                elems = soup.find_all(attrs={'class': lambda x: x and pattern in str(x).lower()})
                containers.extend(elems)

            print(f"  ✓ 找到 {len(set(containers))} 个可能的容器")

            browser.close()

            return {
                "name": source['name'],
                "status": "success",
                "html_length": len(html),
                "article_links_count": len(article_links),
                "containers_count": len(set(containers)),
                "usable": len(html) > 10000 and len(article_links) > 10
            }

    except Exception as e:
        print(f"  ✗ 失败: {str(e)[:100]}")
        return {
            "name": source['name'],
            "status": "failed",
            "error": str(e)[:200],
            "usable": False
        }


def main():
    print("="*70)
    print("快速测试额外媒体源")
    print("="*70)

    results = []
    for source in ADDITIONAL_SOURCES:
        result = quick_test(source)
        results.append(result)

    # 保存结果
    with open('tmp/additional_sources_test.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 统计
    usable = [r for r in results if r.get('usable')]

    print(f"\n{'='*70}")
    print(f"测试完成: {len(results)} 个网站")
    print(f"可用: {len(usable)} 个")
    print("="*70)

    if usable:
        print("\n可用的网站:")
        for r in usable:
            print(f"  ✓ {r['name']}")


if __name__ == "__main__":
    main()

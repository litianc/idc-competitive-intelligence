"""
批量分析8个新媒体源的网站结构

使用Playwright访问网站，分析HTML结构，提取CSS选择器
"""

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
import time
from typing import Dict, List
import re


# 8个待分析的媒体源
SOURCES_TO_ANALYZE = [
    {
        "name": "钛媒体",
        "url": "https://www.tmtpost.com",
        "list_url": "https://www.tmtpost.com/channel/cloud",
        "tier": 2,
        "category": "科技资讯",
    },
    {
        "name": "雷锋网",
        "url": "https://www.leiphone.com",
        "list_url": "https://www.leiphone.com/category/cloudcomputing",
        "tier": 2,
        "category": "科技资讯",
    },
    {
        "name": "TechWeb",
        "url": "https://www.techweb.com.cn",
        "list_url": "https://www.techweb.com.cn/",
        "tier": 2,
        "category": "科技资讯",
    },
    {
        "name": "CDCC",
        "url": "http://www.cdcc.org.cn",
        "list_url": "http://www.cdcc.org.cn/",
        "tier": 1,
        "category": "数据中心/云计算",
    },
    {
        "name": "DTDATA",
        "url": "http://www.dtdata.cn",
        "list_url": "http://www.dtdata.cn/",
        "tier": 1,
        "category": "数据中心/云计算",
    },
    {
        "name": "Saasverse",
        "url": "https://saasverse.cn",
        "list_url": "https://saasverse.cn/",
        "tier": 2,
        "category": "投资/商业",
    },
    {
        "name": "Founder Park",
        "url": "https://founderpark.com",
        "list_url": "https://founderpark.com/",
        "tier": 2,
        "category": "投资/商业",
    },
    {
        "name": "中国信息安全",
        "url": "http://www.cismag.com.cn",
        "list_url": "http://www.cismag.com.cn/",
        "tier": 2,
        "category": "综合资讯",
    },
]


def analyze_website(source: Dict, playwright) -> Dict:
    """
    分析单个网站的结构

    返回：
    {
        "name": "媒体名称",
        "status": "success" | "failed",
        "error": "错误信息（如果失败）",
        "analysis": {
            "article_candidates": [...],  # 可能的文章容器选择器
            "title_candidates": [...],     # 可能的标题选择器
            "link_candidates": [...],      # 可能的链接选择器
            "date_candidates": [...],      # 可能的日期选择器
        }
    }
    """
    print(f"\n{'='*60}")
    print(f"分析网站: {source['name']}")
    print(f"URL: {source['list_url']}")
    print(f"{'='*60}")

    result = {
        "name": source["name"],
        "url": source["url"],
        "list_url": source["list_url"],
        "tier": source["tier"],
        "category": source["category"],
        "status": "pending",
        "analysis": {}
    }

    try:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = context.new_page()

        # 访问网站
        print(f"正在访问 {source['list_url']} ...")
        page.goto(source['list_url'], wait_until='domcontentloaded', timeout=15000)
        page.wait_for_timeout(3000)  # 等待JavaScript渲染

        html = page.content()
        soup = BeautifulSoup(html, 'lxml')

        print(f"✓ 页面加载成功，HTML长度: {len(html)}")

        # 分析文章容器
        article_containers = find_article_containers(soup, source['name'])
        result["analysis"]["article_containers"] = article_containers

        # 分析标题选择器
        title_selectors = find_title_selectors(soup, source['name'])
        result["analysis"]["title_selectors"] = title_selectors

        # 分析链接选择器
        link_selectors = find_link_selectors(soup, source['name'])
        result["analysis"]["link_selectors"] = link_selectors

        # 分析日期选择器
        date_selectors = find_date_selectors(soup, source['name'])
        result["analysis"]["date_selectors"] = date_selectors

        # 打印分析结果
        print(f"\n找到 {len(article_containers)} 个可能的文章容器")
        print(f"找到 {len(title_selectors)} 个可能的标题选择器")
        print(f"找到 {len(link_selectors)} 个可能的链接选择器")
        print(f"找到 {len(date_selectors)} 个可能的日期选择器")

        result["status"] = "success"

        browser.close()

    except Exception as e:
        print(f"✗ 分析失败: {str(e)}")
        result["status"] = "failed"
        result["error"] = str(e)

    return result


def find_article_containers(soup: BeautifulSoup, source_name: str) -> List[Dict]:
    """查找可能的文章容器"""
    candidates = []

    # 常见的文章容器class和tag模式
    patterns = [
        ('class', r'article[-_]?(item|list|card|box|entry|post)'),
        ('class', r'news[-_]?(item|list|card|box)'),
        ('class', r'post[-_]?(item|list|card)'),
        ('class', r'content[-_]?(item|list|card)'),
        ('class', r'item'),
        ('class', r'list[-_]?item'),
    ]

    for attr, pattern in patterns:
        elements = soup.find_all(attrs={attr: re.compile(pattern, re.I)})
        for elem in elements[:5]:  # 只取前5个
            class_str = ' '.join(elem.get('class', []))
            if class_str:
                selector = f"{elem.name}.{class_str.split()[0]}"
                candidates.append({
                    "selector": selector,
                    "tag": elem.name,
                    "class": class_str,
                    "count": len(soup.find_all(elem.name, class_=elem.get('class', [])))
                })

    # 去重
    seen = set()
    unique_candidates = []
    for c in candidates:
        if c["selector"] not in seen:
            seen.add(c["selector"])
            unique_candidates.append(c)

    return unique_candidates[:10]  # 返回前10个候选


def find_title_selectors(soup: BeautifulSoup, source_name: str) -> List[Dict]:
    """查找可能的标题选择器"""
    candidates = []

    # 标题通常是 h1-h6 或带有title class的元素
    for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
        elements = soup.find_all(tag)
        for elem in elements[:3]:
            # 检查是否包含链接
            link = elem.find('a')
            if link and link.get('href'):
                selector = f"{tag}"
                if elem.get('class'):
                    selector = f"{tag}.{elem.get('class')[0]}"

                candidates.append({
                    "selector": selector,
                    "link_selector": f"{selector} a",
                    "sample_text": elem.get_text(strip=True)[:50],
                    "sample_href": link.get('href', '')[:100]
                })

    # 查找class包含title的元素
    title_elems = soup.find_all(attrs={'class': re.compile(r'title', re.I)})
    for elem in title_elems[:5]:
        class_str = ' '.join(elem.get('class', []))
        if class_str:
            selector = f"{elem.name}.{class_str.split()[0]}"
            link = elem.find('a')

            candidates.append({
                "selector": selector,
                "link_selector": f"{selector} a" if link else None,
                "sample_text": elem.get_text(strip=True)[:50],
                "sample_href": link.get('href', '')[:100] if link else None
            })

    return candidates[:10]


def find_link_selectors(soup: BeautifulSoup, source_name: str) -> List[Dict]:
    """查找可能的链接选择器"""
    candidates = []

    # 查找所有带href的a标签
    links = soup.find_all('a', href=True)

    for link in links[:20]:
        href = link.get('href', '')
        text = link.get_text(strip=True)

        # 过滤掉太短的文本（可能不是文章标题）
        if len(text) < 10:
            continue

        # 过滤掉明显不是文章的链接
        if any(x in href for x in ['javascript:', '#', 'login', 'register', 'about']):
            continue

        # 构建选择器
        selector = "a"
        if link.get('class'):
            selector = f"a.{link.get('class')[0]}"

        candidates.append({
            "selector": selector,
            "sample_text": text[:50],
            "sample_href": href[:100]
        })

    return candidates[:10]


def find_date_selectors(soup: BeautifulSoup, source_name: str) -> List[Dict]:
    """查找可能的日期选择器"""
    candidates = []

    # 日期相关的class模式
    date_patterns = [
        r'date',
        r'time',
        r'publish',
        r'created',
        r'updated',
        r'meta',
    ]

    for pattern in date_patterns:
        elements = soup.find_all(attrs={'class': re.compile(pattern, re.I)})
        for elem in elements[:5]:
            text = elem.get_text(strip=True)

            # 检查是否包含日期模式
            if re.search(r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}', text) or \
               re.search(r'\d{1,2}[-/]\d{1,2}', text) or \
               any(x in text for x in ['小时前', '分钟前', '天前', '今天', '昨天']):

                class_str = ' '.join(elem.get('class', []))
                if class_str:
                    selector = f"{elem.name}.{class_str.split()[0]}"

                    candidates.append({
                        "selector": selector,
                        "sample_text": text[:50]
                    })

    # 查找time标签
    time_tags = soup.find_all('time')
    for elem in time_tags[:5]:
        candidates.append({
            "selector": "time",
            "sample_text": elem.get_text(strip=True)[:50],
            "datetime_attr": elem.get('datetime', None)
        })

    return candidates[:10]


def main():
    """主函数"""
    print("="*80)
    print("开始批量分析8个媒体源")
    print("="*80)

    results = []

    with sync_playwright() as p:
        for source in SOURCES_TO_ANALYZE:
            result = analyze_website(source, p)
            results.append(result)
            time.sleep(2)  # 避免请求过快

    # 保存结果
    output_file = "tmp/8_sources_analysis_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*80}")
    print(f"分析完成！结果已保存到: {output_file}")
    print(f"{'='*80}")

    # 打印统计
    success_count = sum(1 for r in results if r["status"] == "success")
    failed_count = len(results) - success_count

    print(f"\n总计分析: {len(results)} 个网站")
    print(f"成功: {success_count} 个")
    print(f"失败: {failed_count} 个")

    if failed_count > 0:
        print("\n失败的网站:")
        for r in results:
            if r["status"] == "failed":
                print(f"  - {r['name']}: {r.get('error', 'Unknown error')}")

    return results


if __name__ == "__main__":
    main()

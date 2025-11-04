"""
Use playwright to examine idcquan.com page structure
"""

from playwright.sync_api import sync_playwright
import json


def examine_idcquan():
    """Examine idcquan.com to find correct selectors"""

    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Set user agent to avoid blocking
        page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })

        # Try different URLs
        urls_to_check = [
            "https://www.idcquan.com/",
            "https://news.idcquan.com/",
            "https://www.idcquan.com/Special/idc/",
        ]

        results = {}

        for url in urls_to_check:
            print(f"\n{'='*70}")
            print(f"Examining: {url}")
            print("="*70)

            try:
                # Navigate to page
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(2000)  # Wait for dynamic content

                # Get page title
                title = page.title()
                print(f"\n页面标题: {title}")

                # Find all links that look like news articles
                links = page.query_selector_all("a[href*='/news/']")
                print(f"\n找到 {len(links)} 个包含 /news/ 的链接")

                # Analyze first 10 article links
                article_info = []
                for i, link in enumerate(links[:10]):
                    href = link.get_attribute("href")
                    text = link.text_content().strip()

                    # Get parent elements to understand structure
                    parent = link.evaluate("el => el.parentElement.tagName")
                    parent_class = link.evaluate("el => el.parentElement.className")

                    if text and len(text) > 10:  # Likely article title
                        article_info.append({
                            "index": i + 1,
                            "title": text[:60],
                            "href": href,
                            "parent_tag": parent,
                            "parent_class": parent_class
                        })

                        print(f"\n[{i+1}] {text[:60]}")
                        print(f"    URL: {href}")
                        print(f"    父元素: <{parent} class='{parent_class}'>")

                # Try to find date elements near article links
                print(f"\n\n查找时间元素:")
                date_selectors = [
                    "span.time",
                    "span.date",
                    ".publish-time",
                    "time",
                    "[class*='time']",
                    "[class*='date']"
                ]

                date_elements_found = {}
                for selector in date_selectors:
                    elements = page.query_selector_all(selector)
                    if elements:
                        example = elements[0].text_content().strip()
                        date_elements_found[selector] = {
                            "count": len(elements),
                            "example": example
                        }
                        print(f"  ✓ {selector:25s} - 找到 {len(elements)} 个, 示例: {example}")

                # Save HTML snippet for inspection
                html_file = f"tmp/idcquan_html_{url.replace('https://', '').replace('/', '_')}.html"
                with open(html_file, "w", encoding="utf-8") as f:
                    f.write(page.content())
                print(f"\n💾 HTML已保存到: {html_file}")

                results[url] = {
                    "title": title,
                    "article_count": len(links),
                    "articles": article_info,
                    "date_selectors": date_elements_found
                }

            except Exception as e:
                print(f"❌ 错误: {e}")
                results[url] = {"error": str(e)}

        browser.close()

        # Save results to JSON
        with open("tmp/idcquan_structure.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\n\n{'='*70}")
        print("📊 分析结果已保存到: tmp/idcquan_structure.json")
        print("="*70)


if __name__ == "__main__":
    examine_idcquan()

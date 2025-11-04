"""
Examine multiple media websites to verify selectors
"""

from playwright.sync_api import sync_playwright
import json


def examine_website(url, name):
    """Examine a single website"""
    print(f"\n{'='*70}")
    print(f"Examining: {name}")
    print(f"URL: {url}")
    print("="*70)

    result = {
        "name": name,
        "url": url,
        "status": "unknown",
        "articles": [],
        "selectors_found": {}
    }

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            })

            # Navigate to page
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(3000)
            except Exception as e:
                print(f"❌ Failed to load page: {e}")
                result["status"] = "failed_to_load"
                browser.close()
                return result

            # Get page title
            title = page.title()
            print(f"\n📄 Page Title: {title}")

            # Find all links
            all_links = page.query_selector_all("a[href]")
            print(f"\n🔗 Total links: {len(all_links)}")

            # Try to find article links
            article_links = []
            for link in all_links:
                href = link.get_attribute("href") or ""
                text = link.text_content().strip()

                # Check if it's likely an article link
                if text and len(text) > 15 and (
                    "/news/" in href or
                    "/article/" in href or
                    "detail" in href or
                    ".html" in href or
                    ".shtml" in href
                ):
                    article_links.append({
                        "title": text[:60],
                        "href": href,
                        "parent": link.evaluate("el => el.parentElement.className")
                    })

            print(f"📰 Potential article links: {len(article_links)}")

            if article_links:
                print(f"\n📋 Sample articles:")
                for i, article in enumerate(article_links[:5], 1):
                    print(f"  [{i}] {article['title']}")
                    print(f"      URL: {article['href']}")
                    print(f"      Parent class: {article['parent']}")

            # Try common date selectors
            print(f"\n📅 Date elements:")
            date_selectors = [
                "span.date",
                "span.time",
                ".publish-date",
                ".publish-time",
                "time",
                "[class*='date']",
                "[class*='time']"
            ]

            for selector in date_selectors:
                elements = page.query_selector_all(selector)
                if elements:
                    example = elements[0].text_content().strip()
                    result["selectors_found"][selector] = {
                        "count": len(elements),
                        "example": example
                    }
                    print(f"  ✓ {selector:20s} - {len(elements)} found, e.g.: {example}")

            # Save HTML
            html_file = f"tmp/html_{name.replace(' ', '_')}.html"
            with open(html_file, "w", encoding="utf-8") as f:
                f.write(page.content())
            print(f"\n💾 HTML saved to: {html_file}")

            result["status"] = "success"
            result["articles"] = article_links[:10]
            browser.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        result["status"] = "error"
        result["error"] = str(e)

    return result


def main():
    """Examine all configured media websites"""
    sites = [
        {
            "name": "数据中心世界",
            "url": "https://www.dcworld.cn/"
        },
        {
            "name": "通信世界网",
            "url": "https://www.cww.net.cn/"
        }
    ]

    results = {}

    for site in sites:
        result = examine_website(site["url"], site["name"])
        results[site["name"]] = result

    # Save results
    with open("tmp/multi_site_analysis.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n\n{'='*70}")
    print("📊 Analysis Complete")
    print(f"Results saved to: tmp/multi_site_analysis.json")
    print("="*70)


if __name__ == "__main__":
    main()

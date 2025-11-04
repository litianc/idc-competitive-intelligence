"""
Analyze the top 5 priority media websites
"""

from playwright.sync_api import sync_playwright
import json
import time
import re


def analyze_website(url, name):
    """Analyze a single website and extract selectors"""
    print(f"\n{'='*70}")
    print(f"Analyzing: {name}")
    print(f"URL: {url}")
    print("="*70)

    result = {
        "name": name,
        "url": url,
        "status": "unknown",
        "recommendations": {}
    }

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            })

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(3000)
            except Exception as e:
                print(f"❌ Failed to load: {e}")
                result["status"] = "failed"
                result["error"] = str(e)
                browser.close()
                return result

            print(f"✓ Page loaded: {page.title()}")

            # Find article links
            all_links = page.query_selector_all("a[href]")
            article_links = []

            for link in all_links:
                href = link.get_attribute("href") or ""
                text = link.text_content().strip()

                # Check if it looks like an article
                if text and len(text) > 15 and (
                    "/article" in href or
                    "/news" in href or
                    "/post" in href or
                    ".html" in href or
                    "/p/" in href or
                    re.search(r'/\d+', href)  # Numeric IDs
                ):
                    parent_class = link.evaluate("el => el.parentElement?.className || ''")
                    article_links.append({
                        "title": text[:60],
                        "href": href,
                        "parent_class": parent_class
                    })

            print(f"\n📰 Found {len(article_links)} potential articles")

            if article_links:
                # Analyze parent containers
                parent_classes = {}
                for article in article_links[:20]:
                    pclass = article.get("parent_class", "")
                    if pclass:
                        parent_classes[pclass] = parent_classes.get(pclass, 0) + 1

                # Find most common parent
                if parent_classes:
                    most_common = sorted(parent_classes.items(), key=lambda x: -x[1])[0]
                    print(f"\n🎯 Most common parent class: {most_common[0]} ({most_common[1]} times)")

                # Show samples
                print(f"\n📋 Sample articles:")
                for i, article in enumerate(article_links[:5], 1):
                    print(f"  [{i}] {article['title']}")
                    print(f"      {article['href'][:80]}")

            # Look for date elements
            print(f"\n📅 Looking for date elements...")
            date_selectors = [
                ("span.time", "span with class 'time'"),
                ("span.date", "span with class 'date'"),
                ("time", "HTML time element"),
                (".publish-time", "element with class 'publish-time'"),
                (".publish-date", "element with class 'publish-date'"),
                ("[class*='time']", "any element with 'time' in class"),
                ("[class*='date']", "any element with 'date' in class"),
            ]

            date_found = {}
            for selector, desc in date_selectors:
                elements = page.query_selector_all(selector)
                if elements:
                    example = elements[0].text_content().strip()
                    date_found[selector] = example
                    print(f"  ✓ {selector:25s} ({len(elements)} found) e.g.: {example}")

            # Look for common article containers
            print(f"\n📦 Looking for article containers...")
            container_selectors = [
                "article",
                ".article-item",
                ".news-item",
                ".post-item",
                ".item",
                ".list-item",
                "[class*='article']",
                "[class*='news']",
                "[class*='post']",
            ]

            containers_found = {}
            for selector in container_selectors:
                elements = page.query_selector_all(selector)
                if elements and len(elements) >= 3:  # At least 3 items
                    containers_found[selector] = len(elements)
                    print(f"  ✓ {selector:25s} - {len(elements)} elements")

            # Generate recommendations
            recommendations = {
                "list_url": url,
                "encoding": "utf-8"
            }

            if containers_found:
                # Use the selector with reasonable count (5-50 items)
                best_container = None
                for selector, count in containers_found.items():
                    if 5 <= count <= 50:
                        best_container = selector
                        break
                if not best_container:
                    best_container = list(containers_found.keys())[0]

                recommendations["article_container"] = best_container
                print(f"\n💡 Recommended container: {best_container}")

            if article_links:
                # Try to find title selector
                first_article = article_links[0]
                parent = first_article.get("parent_class", "")

                # Common patterns
                recommendations["title_selector"] = "TODO - check article structure"
                recommendations["link_selector"] = "a"

                print(f"\n💡 Recommended selectors:")
                print(f"   title_selector: {recommendations['title_selector']}")
                print(f"   link_selector: {recommendations['link_selector']}")

            if date_found:
                first_date_selector = list(date_found.keys())[0]
                recommendations["date_selector"] = first_date_selector
                print(f"   date_selector: {first_date_selector}")

            # Save HTML for manual inspection
            html_file = f"tmp/html_{name.replace(' ', '_').replace('/', '_')}.html"
            with open(html_file, "w", encoding="utf-8") as f:
                f.write(page.content())
            print(f"\n💾 HTML saved: {html_file}")

            result["status"] = "success"
            result["recommendations"] = recommendations
            result["article_count"] = len(article_links)
            result["containers_found"] = list(containers_found.keys()) if containers_found else []

            browser.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        result["status"] = "error"
        result["error"] = str(e)

    return result


def main():
    """Analyze top 5 priority websites"""

    websites = [
        {
            "name": "36氪",
            "url": "https://36kr.com/newsflashes"
        },
        {
            "name": "InfoQ",
            "url": "https://www.infoq.cn/topic/cloud-computing"
        },
        {
            "name": "量子位",
            "url": "https://www.qbitai.com/"
        },
        {
            "name": "钛媒体",
            "url": "https://www.tmtpost.com/channel/cloud"
        },
        {
            "name": "CDCC",
            "url": "http://www.cdcc.org.cn/"
        }
    ]

    results = {}

    for site in websites:
        result = analyze_website(site["url"], site["name"])
        results[site["name"]] = result
        time.sleep(2)  # Be polite

    # Save results
    with open("tmp/priority_5_analysis.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # Print summary
    print(f"\n\n{'='*70}")
    print("Analysis Summary")
    print("="*70)

    for name, result in results.items():
        status = result.get("status", "unknown")
        if status == "success":
            print(f"\n✅ {name}")
            print(f"   Articles found: {result.get('article_count', 0)}")
            if result.get("recommendations"):
                recs = result["recommendations"]
                if recs.get("article_container"):
                    print(f"   Container: {recs['article_container']}")
                if recs.get("date_selector"):
                    print(f"   Date: {recs['date_selector']}")
        else:
            print(f"\n❌ {name} - {status}")
            if result.get("error"):
                print(f"   Error: {result['error'][:100]}")

    print(f"\n💾 Results saved to: tmp/priority_5_analysis.json")
    print("="*70)


if __name__ == "__main__":
    main()

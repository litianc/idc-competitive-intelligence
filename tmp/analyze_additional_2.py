"""
Analyze 2 additional media sources: 极客公园 and 云头条
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from playwright.sync_api import sync_playwright
import json
from collections import Counter

def analyze_website(url, name):
    """Analyze website structure"""
    print(f"\n{'='*70}")
    print(f"🔍 Analyzing: {name}")
    print(f"🔗 URL: {url}")
    print('='*70)
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(ignore_https_errors=True)
            
            print(f"   ⏳ Loading page...")
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(2000)
            
            # Save HTML
            html_content = page.content()
            html_file = f"tmp/html_{name}.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"   💾 HTML saved to: {html_file}")
            
            # Find article links
            all_links = page.query_selector_all("a[href]")
            article_links = []
            for link in all_links:
                href = link.get_attribute("href")
                text = link.inner_text().strip()
                if href and text and len(text) > 10:
                    article_links.append({
                        "href": href,
                        "text": text[:60]
                    })
            
            print(f"   📄 Found {len(article_links)} potential article links")
            
            # Find date elements
            date_elements = []
            for selector in ["span.time", "span.date", ".time", ".date", 
                           "[class*='time']", "[class*='date']"]:
                elements = page.query_selector_all(selector)
                for el in elements:
                    text = el.inner_text().strip()
                    if text:
                        date_elements.append({
                            "selector": selector,
                            "text": text
                        })
            
            print(f"   📅 Found {len(date_elements)} date elements")
            if date_elements:
                print(f"   📅 Sample dates: {date_elements[0]['text']}, {date_elements[1]['text'] if len(date_elements) > 1 else ''}")
            
            # Find common containers
            container_patterns = [
                "article", ".article", "[class*='article']",
                ".post", "[class*='post']",
                ".item", "[class*='item']",
                ".news", "[class*='news']",
                ".list-item", ".content-item"
            ]
            
            container_counts = {}
            for pattern in container_patterns:
                count = len(page.query_selector_all(pattern))
                if count > 0:
                    container_counts[pattern] = count
            
            print(f"   📦 Container analysis:")
            sorted_containers = sorted(container_counts.items(), 
                                      key=lambda x: x[1], 
                                      reverse=True)[:5]
            for container, count in sorted_containers:
                print(f"      • {container}: {count} elements")
            
            browser.close()
            
            # Recommendations
            best_container = sorted_containers[0][0] if sorted_containers else "TODO"
            first_date_selector = date_elements[0]['selector'] if date_elements else "TODO"
            
            return {
                "name": name,
                "url": url,
                "status": "success",
                "recommendations": {
                    "list_url": url,
                    "encoding": "utf-8",
                    "article_container": best_container,
                    "title_selector": "TODO - check article structure",
                    "link_selector": "a",
                    "date_selector": first_date_selector
                },
                "article_count": len(article_links),
                "containers_found": [c for c, _ in sorted_containers]
            }
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return {
            "name": name,
            "url": url,
            "status": "error",
            "error": str(e)
        }

def main():
    sources = [
        ("极客公园", "https://www.geekpark.net/"),
        ("云头条", "https://www.yuntoutiao.com/")
    ]
    
    results = {}
    for name, url in sources:
        result = analyze_website(url, name)
        results[name] = result
    
    # Save results
    output_file = "tmp/additional_2_analysis.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*70}")
    print(f"✅ Analysis complete! Results saved to: {output_file}")
    print('='*70)
    
    # Summary
    print("\n📊 Summary:")
    for name, result in results.items():
        status = "✅" if result["status"] == "success" else "❌"
        count = result.get("article_count", 0)
        print(f"{status} {name}: Articles found: {count}")
        if result["status"] == "success":
            container = result["recommendations"].get("article_container", "N/A")
            date_sel = result["recommendations"].get("date_selector", "N/A")
            print(f"   Container: {container}")
            print(f"   Date: {date_sel}")

if __name__ == "__main__":
    main()

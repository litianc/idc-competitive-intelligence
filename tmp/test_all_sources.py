"""
Test all active media sources

Useful for validating configurations after adding new sources
"""

import sys
sys.path.insert(0, '/Users/xyli/Documents/Code/claude-life/competitive-intelligence-web')

from src.scrapers.generic_scraper import ScraperFactory
import json


def main():
    """Test all active media sources"""
    print("=" * 70)
    print("Testing All Active Media Sources")
    print("=" * 70)

    # Load configuration
    config_path = "config/media-sources.json"

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
    except FileNotFoundError:
        # Try template if main config doesn't exist
        config_path = "config/media-sources-template-22.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

    sources = config_data.get("sources", [])
    active_sources = [s for s in sources if s.get("active", False)]

    print(f"\n📊 Configuration Summary:")
    print(f"   Total sources: {len(sources)}")
    print(f"   Active sources: {len(active_sources)}")
    print(f"   Pending configuration: {len(sources) - len(active_sources)}")

    if not active_sources:
        print("\n⚠️  No active sources found.")
        print("   Please set 'active': true for sources you want to test.")
        return

    # Test each active source
    print(f"\n{'=' * 70}")
    print("Testing Active Sources")
    print("=" * 70)

    results = []

    for source in active_sources:
        source_name = source.get("name", "Unknown")
        print(f"\n🔄 Testing: {source_name}")
        print("-" * 70)

        try:
            # Create scraper
            scraper = ScraperFactory.create_scraper(source)

            # Fetch articles
            articles = scraper.fetch_articles(limit=5)

            if articles:
                print(f"   ✅ SUCCESS - Fetched {len(articles)} articles")

                # Show first article as sample
                first = articles[0]
                print(f"\n   Sample Article:")
                print(f"      Title: {first.get('title', 'N/A')[:60]}...")
                print(f"      URL: {first.get('url', 'N/A')}")
                print(f"      Date: {first.get('publish_date', 'N/A')}")

                # Validation
                has_titles = all(a.get('title') for a in articles)
                has_urls = all(a.get('url') for a in articles)
                has_dates = sum(1 for a in articles if a.get('publish_date'))

                print(f"\n   Validation:")
                print(f"      Titles: {len([a for a in articles if a.get('title')])}/{len(articles)}")
                print(f"      URLs: {len([a for a in articles if a.get('url')])}/{len(articles)}")
                print(f"      Dates: {has_dates}/{len(articles)}")

                results.append({
                    "name": source_name,
                    "status": "success",
                    "article_count": len(articles),
                    "validation": {
                        "titles": has_titles,
                        "urls": has_urls,
                        "dates": has_dates
                    }
                })

            else:
                print(f"   ❌ FAILED - No articles fetched")
                print(f"      Check scraper_config selectors")
                results.append({
                    "name": source_name,
                    "status": "no_articles",
                    "article_count": 0
                })

        except Exception as e:
            print(f"   ❌ ERROR - {str(e)}")
            results.append({
                "name": source_name,
                "status": "error",
                "error": str(e)
            })

    # Summary
    print(f"\n{'=' * 70}")
    print("Test Summary")
    print("=" * 70)

    success_count = len([r for r in results if r['status'] == 'success'])
    failed_count = len(results) - success_count

    print(f"\n✅ Successful: {success_count}/{len(results)}")
    print(f"❌ Failed: {failed_count}/{len(results)}")

    if success_count > 0:
        print(f"\n📊 Working Sources:")
        for result in results:
            if result['status'] == 'success':
                print(f"   • {result['name']} ({result['article_count']} articles)")

    if failed_count > 0:
        print(f"\n⚠️  Failed Sources:")
        for result in results:
            if result['status'] != 'success':
                print(f"   • {result['name']} - {result.get('error', result['status'])}")

    # Recommendations
    if failed_count > 0:
        print(f"\n💡 Recommendations:")
        print(f"   1. Run: python tmp/analyze_website.py <URL>")
        print(f"   2. Update scraper_config selectors")
        print(f"   3. Re-test with this script")
        print(f"\n   See: docs/ADD_NEW_MEDIA.md for detailed guide")

    print(f"\n{'=' * 70}")


if __name__ == "__main__":
    main()

"""
Test the IdcquanScraper with real data from the website
"""

import sys
sys.path.insert(0, '/Users/xyli/Documents/Code/claude-life/competitive-intelligence-web')

from src.scrapers.idcquan_scraper import IdcquanScraper
from datetime import date


def main():
    """Test scraper with real data"""
    print("=" * 70)
    print("Testing IdcquanScraper with real data")
    print("=" * 70)

    # Create scraper instance
    scraper = IdcquanScraper()

    print(f"\n📰 Source: {scraper.source_name}")
    print(f"🔗 URL: {scraper.base_url}")

    # Fetch articles
    print("\n🔄 Fetching articles...")
    articles = scraper.fetch_articles(limit=10)

    print(f"\n✅ Successfully fetched {len(articles)} articles\n")

    # Display articles
    if articles:
        print("=" * 70)
        print("📋 Article List")
        print("=" * 70)

        for i, article in enumerate(articles, 1):
            print(f"\n[{i}] {article['title']}")
            print(f"    URL: {article['url']}")
            print(f"    Date: {article['publish_date']}")
            print(f"    Summary: {article['summary'][:60]}..." if len(article['summary']) > 60 else f"    Summary: {article['summary']}")

        # Validation checks
        print("\n" + "=" * 70)
        print("✓ Validation Results")
        print("=" * 70)

        # Check all articles have required fields
        all_have_title = all(article.get('title') for article in articles)
        all_have_url = all(article.get('url') for article in articles)
        all_have_date = all(article.get('publish_date') for article in articles)
        all_have_source = all(article.get('source') for article in articles)

        print(f"\n  ✓ All articles have titles: {all_have_title}")
        print(f"  ✓ All articles have URLs: {all_have_url}")
        print(f"  ✓ All articles have dates: {all_have_date}")
        print(f"  ✓ All articles have source: {all_have_source}")

        # Check date validity
        valid_dates = sum(1 for article in articles if isinstance(article['publish_date'], date))
        print(f"  ✓ Valid date objects: {valid_dates}/{len(articles)}")

        # Check URL pattern
        valid_urls = sum(1 for article in articles if article['url'].startswith('https://news.idcquan.com/'))
        print(f"  ✓ Valid URL pattern: {valid_urls}/{len(articles)}")

        # Overall success
        all_valid = all_have_title and all_have_url and all_have_date and all_have_source
        print(f"\n{'✅ All validations passed!' if all_valid else '❌ Some validations failed'}")

    else:
        print("❌ No articles fetched. Please check the scraper implementation.")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()

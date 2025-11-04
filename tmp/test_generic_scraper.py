"""
Test GenericScraper with idcquan configuration
"""

import sys
sys.path.insert(0, '/Users/xyli/Documents/Code/claude-life/competitive-intelligence-web')

from src.scrapers.generic_scraper import GenericScraper


def main():
    """Test GenericScraper"""
    print("=" * 70)
    print("Testing GenericScraper with Configuration")
    print("=" * 70)

    # Load scraper from config
    print("\n📂 Loading configuration...")
    scraper = GenericScraper.from_config_file(
        config_path="config/media-sources.json",
        source_name="中国IDC圈"
    )

    print(f"✓ Scraper created for: {scraper.name}")
    print(f"✓ Base URL: {scraper.base_url}")
    print(f"✓ List URL: {scraper.list_url}")
    print(f"✓ Tier: {scraper.tier}")

    # Show configuration
    print(f"\n⚙️  Configuration:")
    print(f"   Article container: {scraper.article_container}")
    print(f"   Title selector: {scraper.title_selector}")
    print(f"   Link selector: {scraper.link_selector}")
    print(f"   Date selector: {scraper.date_selector}")
    print(f"   Summary selector: {scraper.summary_selector}")

    # Fetch articles
    print(f"\n🔄 Fetching articles...")
    articles = scraper.fetch_articles(limit=10)

    print(f"\n✅ Successfully fetched {len(articles)} articles\n")

    if articles:
        print("=" * 70)
        print("📋 Article List")
        print("=" * 70)

        for i, article in enumerate(articles, 1):
            print(f"\n[{i}] {article['title']}")
            print(f"    URL: {article['url']}")
            print(f"    Date: {article['publish_date']}")
            if article.get('summary'):
                summary = article['summary'][:60] + "..." if len(article['summary']) > 60 else article['summary']
                print(f"    Summary: {summary}")
            print(f"    Source: {article['source']}")

        # Validation
        print("\n" + "=" * 70)
        print("✓ Validation Results")
        print("=" * 70)

        all_have_title = all(article.get('title') for article in articles)
        all_have_url = all(article.get('url') for article in articles)
        all_have_source = all(article.get('source') for article in articles)
        dates_present = sum(1 for article in articles if article.get('publish_date'))

        print(f"\n  ✓ All articles have titles: {all_have_title}")
        print(f"  ✓ All articles have URLs: {all_have_url}")
        print(f"  ✓ All articles have source: {all_have_source}")
        print(f"  ✓ Articles with dates: {dates_present}/{len(articles)}")

        all_valid = all_have_title and all_have_url and all_have_source
        print(f"\n{'✅ Configuration-driven scraping works!' if all_valid else '❌ Some validations failed'}")

    else:
        print("❌ No articles fetched. Check configuration.")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()

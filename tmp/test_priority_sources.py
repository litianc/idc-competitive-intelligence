"""
Test script specifically for the top 5 priority media sources
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.scrapers.generic_scraper import ScraperFactory
import json

def test_priority_sources():
    print("\n" + "="*70)
    print("Testing Top 5 Priority Media Sources")
    print("="*70 + "\n")
    
    # Load config
    config_path = "config/media-sources.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Priority sources from user's request
    priority_sources = ["36氪", "InfoQ", "量子位", "钛媒体", "CDCC"]
    
    results = {}
    for source_name in priority_sources:
        print(f"\n{'='*70}")
        print(f"🔍 Testing: {source_name}")
        print("="*70)
        
        # Find source in config
        source_config = None
        for source in config.get("sources", []):
            if source.get("name") == source_name:
                source_config = source
                break
        
        if not source_config:
            print(f"   ❌ NOT IN CONFIG - Source not found in media-sources.json")
            results[source_name] = "not_configured"
            continue
        
        if not source_config.get("active", False):
            print(f"   ⏸️  INACTIVE - Source exists but marked as inactive")
            results[source_name] = "inactive"
            continue
        
        # Try to fetch
        try:
            scraper = ScraperFactory.create_scraper(source_config)
            articles = scraper.fetch_articles(limit=3)
            
            if articles and len(articles) > 0:
                print(f"   ✅ SUCCESS - Fetched {len(articles)} articles\n")
                
                for i, article in enumerate(articles, 1):
                    print(f"   Article {i}:")
                    print(f"      📰 {article.get('title', 'N/A')[:60]}...")
                    print(f"      🔗 {article.get('url', 'N/A')}")
                    print(f"      📅 {article.get('publish_date', 'N/A')}")
                    print(f"      💬 {article.get('summary', 'N/A')[:50]}...")
                    print()
                
                results[source_name] = "success"
            else:
                print(f"   ❌ FAILED - No articles fetched")
                print(f"      Possible issues:")
                print(f"      • CSS selectors might be incorrect")
                print(f"      • Website structure changed")
                print(f"      • Network/access issues")
                results[source_name] = "no_articles"
        
        except Exception as e:
            print(f"   ❌ ERROR - {str(e)}")
            results[source_name] = f"error: {str(e)[:50]}"
    
    # Summary
    print("\n" + "="*70)
    print("📊 Summary of Top 5 Priority Sources")
    print("="*70)
    
    success_count = sum(1 for r in results.values() if r == "success")
    total_count = len(priority_sources)
    
    print(f"\n✅ Working: {success_count}/{total_count}")
    for source, result in results.items():
        if result == "success":
            print(f"   • {source}")
    
    if any(r != "success" for r in results.values()):
        print(f"\n⚠️  Issues:")
        for source, result in results.items():
            if result != "success":
                print(f"   • {source}: {result}")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    test_priority_sources()

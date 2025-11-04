"""
Test the 2 newly added pending media sources
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.scrapers.generic_scraper import ScraperFactory
import json

def test_pending_sources():
    print("\n" + "="*70)
    print("Testing 2 Newly Added Pending Media Sources")
    print("="*70 + "\n")
    
    # Load config
    config_path = "config/media-sources.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Find the 2 pending sources
    pending_sources = []
    for source in config.get("sources", []):
        if source.get("name") in ["极客公园", "云头条"]:
            pending_sources.append(source)
    
    print(f"Found {len(pending_sources)} pending sources to test\n")
    
    for source_config in pending_sources:
        source_name = source_config.get("name")
        print("="*70)
        print(f"🔍 Testing: {source_name}")
        print(f"📊 Tier: {source_config.get('tier')}")
        print(f"📁 Category: {source_config.get('category')}")
        print(f"🔗 URL: {source_config.get('scraper_config', {}).get('list_url')}")
        print(f"⚙️  Active: {source_config.get('active')}")
        print("="*70)
        
        # Temporarily activate for testing
        test_config = source_config.copy()
        test_config['active'] = True
        
        try:
            scraper = ScraperFactory.create_scraper(test_config)
            articles = scraper.fetch_articles(limit=3)
            
            if articles and len(articles) > 0:
                print(f"\n   ✅ SUCCESS - Fetched {len(articles)} articles\n")
                
                for i, article in enumerate(articles, 1):
                    print(f"   Article {i}:")
                    print(f"      📰 Title: {article.get('title', 'N/A')[:70]}...")
                    print(f"      🔗 URL: {article.get('url', 'N/A')}")
                    print(f"      📅 Date: {article.get('publish_date', 'N/A')}")
                    if article.get('summary'):
                        print(f"      💬 Summary: {article.get('summary')[:60]}...")
                    print()
                
                print(f"   ✅ Configuration is correct and ready to activate!")
            else:
                print(f"\n   ❌ FAILED - No articles fetched")
                print(f"   ⚠️  Need to adjust CSS selectors in configuration")
        
        except Exception as e:
            print(f"\n   ❌ ERROR - {str(e)}")
        
        print()
    
    print("="*70)
    print("📝 Summary")
    print("="*70)
    print(f"\n这两个媒体源已添加到配置文件，状态为 active: false")
    print(f"当您准备启用时，只需将 active 改为 true 即可\n")
    print("添加的媒体源:")
    print("  1. 极客公园 (geekpark.net) - Tier 2 科技资讯")
    print("  2. 云头条 (yuntoutiao.com) - Tier 1 数据中心/云计算")
    print("\n这两个媒体源可以替代失败的 钛媒体 和 CDCC")
    print("="*70)

if __name__ == "__main__":
    test_pending_sources()

"""
测试LLM摘要生成器
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
from src.processing.llm_summarizer import LLMSummarizer
from src.storage.database import Database

# 加载环境变量
load_dotenv()


def test_single_summary():
    """测试单篇文章摘要生成"""
    print("=" * 80)
    print("🧪 测试1: 单篇文章摘要生成")
    print("=" * 80)

    # 初始化LLM
    summarizer = LLMSummarizer(
        api_key=os.getenv("LLM_API_KEY"),
        api_base=os.getenv("LLM_API_BASE"),
        model=os.getenv("LLM_MODEL"),
    )

    # 测试文章
    title = "深度｜重新定义智算中心生存法则"
    content = """
    停止追逐更新周期，开始追求韧性。未来不是建造更快的算力中心，
    而是教会你的算力中心如何在折旧中生存。智算中心的建设需要考虑
    长期运营成本和技术演进路径，避免过度追求最新硬件配置。
    """

    print(f"\n📄 文章标题: {title}")
    print(f"📝 文章内容: {content[:100]}...")
    print("\n⏳ 正在生成摘要...")

    try:
        summary = summarizer.generate_summary(title, content)

        if summary:
            print(f"\n✅ 生成成功!")
            print(f"📋 摘要内容: {summary}")
            print(f"📏 摘要长度: {len(summary)}字")

            # 验证长度
            if 60 <= len(summary) <= 200:
                print("✅ 摘要长度符合要求 (60-200字)")
            else:
                print(f"⚠️ 摘要长度不符合要求: {len(summary)}字")
        else:
            print("❌ 摘要生成失败")

    except Exception as e:
        print(f"❌ 发生错误: {e}")


def test_database_summary_generation():
    """测试为数据库中的文章生成摘要"""
    print("\n" + "=" * 80)
    print("🧪 测试2: 为数据库文章批量生成摘要")
    print("=" * 80)

    # 连接数据库
    db = Database("tmp/multi_source_intelligence.db")

    # 查询需要生成摘要的文章（摘要为空或很短的）
    print("\n📊 查询需要生成摘要的文章...")
    all_articles = db.get_all_articles()

    # 筛选需要生成摘要的文章
    articles_need_summary = []
    for article in all_articles:
        summary = article.get("summary", "")
        # 如果摘要为空或少于30字，需要重新生成
        if not summary or len(summary) < 30:
            articles_need_summary.append(article)

    print(f"   找到 {len(articles_need_summary)} 篇需要生成摘要的文章")

    if not articles_need_summary:
        print("✅ 所有文章都已有摘要")
        return

    # 只取前3篇进行测试
    test_articles = articles_need_summary[:3]
    print(f"\n🎯 测试处理前 {len(test_articles)} 篇文章:\n")

    for i, article in enumerate(test_articles, 1):
        print(f"{i}. {article['title'][:50]}...")
        print(f"   当前摘要: {article.get('summary', '(无)')[:50]}...")

    # 初始化LLM
    print("\n⏳ 初始化LLM...")
    summarizer = LLMSummarizer(
        api_key=os.getenv("LLM_API_KEY"),
        api_base=os.getenv("LLM_API_BASE"),
        model=os.getenv("LLM_MODEL"),
    )

    # 生成摘要
    print("\n⏳ 开始生成摘要...\n")
    for i, article in enumerate(test_articles, 1):
        print(f"{'=' * 80}")
        print(f"处理文章 {i}/{len(test_articles)}")
        print(f"{'=' * 80}")
        print(f"标题: {article['title']}")

        try:
            # 生成摘要
            summary = summarizer.generate_summary(
                title=article["title"],
                content=article.get("content", ""),
            )

            if summary:
                print(f"✅ 生成成功 (长度: {len(summary)}字)")
                print(f"摘要: {summary}")

                # 更新数据库
                db.update_article_summary(article["id"], summary)
                print("💾 已保存到数据库")
            else:
                print("❌ 生成失败")

        except Exception as e:
            print(f"❌ 错误: {e}")

        print()

    print("=" * 80)
    print("✅ 批量生成完成!")
    print("=" * 80)


def verify_summaries():
    """验证生成的摘要"""
    print("\n" + "=" * 80)
    print("🧪 测试3: 验证生成的摘要")
    print("=" * 80)

    db = Database("tmp/multi_source_intelligence.db")
    all_articles = db.get_all_articles()

    # 统计摘要情况
    total = len(all_articles)
    has_summary = sum(1 for a in all_articles if a.get("summary") and len(a["summary"]) >= 30)
    no_summary = total - has_summary

    print(f"\n📊 摘要统计:")
    print(f"   总文章数: {total}")
    print(f"   已有摘要: {has_summary} ({has_summary*100//total}%)")
    print(f"   无摘要:   {no_summary} ({no_summary*100//total}%)")

    # 显示几个生成的摘要示例
    print(f"\n📋 摘要示例 (显示前3篇):\n")
    articles_with_summary = [a for a in all_articles if a.get("summary") and len(a["summary"]) >= 30]

    for i, article in enumerate(articles_with_summary[:3], 1):
        print(f"{i}. {article['title'][:60]}...")
        print(f"   摘要: {article['summary']}")
        print(f"   长度: {len(article['summary'])}字")
        print()


def main():
    """主测试流程"""
    print("\n" + "=" * 80)
    print("🚀 LLM摘要生成器测试")
    print("=" * 80)
    print(f"\n使用模型: {os.getenv('LLM_MODEL')}")
    print(f"API端点: {os.getenv('LLM_API_BASE')}")
    print()

    # 测试1: 单篇摘要
    test_single_summary()

    # 测试2: 批量生成
    input("\n按回车键继续测试批量生成...")
    test_database_summary_generation()

    # 测试3: 验证结果
    verify_summaries()

    print("\n" + "=" * 80)
    print("✅ 所有测试完成!")
    print("=" * 80)


if __name__ == "__main__":
    main()

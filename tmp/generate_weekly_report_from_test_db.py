"""
使用集成测试数据库生成周报

展示完整的工作流程：
1. 从测试数据库读取文章
2. 生成周报
3. 展示系统能力
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage.database import Database
from src.reporting.report_generator import WeeklyReportGenerator
from datetime import date


def main():
    """主函数"""
    print("="*80)
    print("基于14源集成测试数据生成周报")
    print("="*80)

    # 连接测试数据库
    db_path = "tmp/integration_test_14_sources.db"
    print(f"\n正在连接数据库: {db_path}")

    db = Database(db_path)

    # 统计数据库中的文章
    articles = db.get_all_articles()
    print(f"✓ 数据库中共有 {len(articles)} 篇文章")

    # 按源统计
    source_stats = {}
    for article in articles:
        source = article['source']
        source_stats[source] = source_stats.get(source, 0) + 1

    print("\n按媒体源统计:")
    for source, count in sorted(source_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"  {source}: {count} 篇")

    # 生成周报
    print(f"\n{'='*80}")
    print("开始生成周报...")
    print("="*80)

    generator = WeeklyReportGenerator(database=db)

    # 生成报告
    report_content = generator.generate_report(days=7)

    # 保存到文件
    output_file = f"tmp/IDC_Weekly_Report_14Sources_{date.today().strftime('%Y_%m_%d')}.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report_content)

    print(f"\n✓ 周报已生成: {output_file}")
    print(f"✓ 报告长度: {len(report_content)} 字符")

    # 显示报告预览（前50行）
    print(f"\n{'='*80}")
    print("周报预览（前50行）:")
    print("="*80)

    lines = report_content.split('\n')
    for i, line in enumerate(lines[:50], 1):
        print(line)

    if len(lines) > 50:
        print(f"\n... （还有 {len(lines) - 50} 行，请查看完整文件）")

    db.close()

    print(f"\n{'='*80}")
    print("周报生成完成！")
    print("="*80)
    print(f"\n完整报告文件: {output_file}")
    print(f"文章来源: {len(source_stats)} 个媒体源")
    print(f"文章总数: {len(articles)} 篇")


if __name__ == "__main__":
    main()

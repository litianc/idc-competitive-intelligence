#!/usr/bin/env python3
"""
IDC行业竞争情报系统 - 周报生成脚本

使用方法:
    python3 generate_weekly_report.py           # 生成最近7天的周报
    python3 generate_weekly_report.py --days 14 # 生成最近14天的周报
"""

import argparse
from datetime import date
from pathlib import Path

from src.storage.database import Database
from src.reporting.report_generator import WeeklyReportGenerator


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='生成IDC行业周报')
    parser.add_argument('--days', type=int, default=7,
                       help='统计最近N天的数据（默认7天）')
    parser.add_argument('--db', type=str, default='data/intelligence.db',
                       help='数据库文件路径')
    parser.add_argument('--output', type=str, default=None,
                       help='输出文件路径（默认: reports/IDC_Weekly_Report_YYYY_MM_DD.md）')

    args = parser.parse_args()

    print("="*80)
    print("IDC行业竞争情报系统 - 周报生成")
    print("="*80)

    # 检查数据库
    if not Path(args.db).exists():
        print(f"\n✗ 数据库文件不存在: {args.db}")
        print("  请先运行数据采集: python3 run_collection.py")
        return

    # 连接数据库
    db = Database(args.db)
    articles = db.get_all_articles()
    print(f"\n✓ 数据库连接成功: {args.db}")
    print(f"✓ 数据库中共有 {len(articles)} 篇文章")

    # 按源统计
    source_stats = {}
    for article in articles:
        source = article['source']
        source_stats[source] = source_stats.get(source, 0) + 1

    print(f"\n文章来源分布:")
    for source, count in sorted(source_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"  {source}: {count} 篇")

    # 生成周报
    print(f"\n{'='*80}")
    print(f"开始生成周报（统计最近 {args.days} 天）...")
    print("="*80)

    generator = WeeklyReportGenerator(database=db)
    report_content = generator.generate_report(days=args.days)

    # 确定输出路径
    if args.output:
        output_file = args.output
    else:
        # 默认保存到 reports 目录
        reports_dir = Path('reports')
        reports_dir.mkdir(exist_ok=True)
        output_file = reports_dir / f"IDC_Weekly_Report_{date.today().strftime('%Y_%m_%d')}.md"

    # 保存报告
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report_content)

    print(f"\n✓ 周报已生成!")
    print(f"✓ 文件路径: {output_file}")
    print(f"✓ 报告长度: {len(report_content)} 字符")

    # 显示简要预览
    lines = report_content.split('\n')
    print(f"\n{'='*80}")
    print("周报预览（前30行）:")
    print("="*80)
    for line in lines[:30]:
        print(line)

    if len(lines) > 30:
        print(f"\n... （还有 {len(lines) - 30} 行，请查看完整文件）")

    db.close()

    print(f"\n{'='*80}")
    print("周报生成完成！")
    print("="*80)


if __name__ == "__main__":
    main()

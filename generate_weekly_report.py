#!/usr/bin/env python3
"""
IDC行业竞争情报系统 - 周报生成脚本

使用方法:
    python3 generate_weekly_report.py           # 生成最近7天的周报
    python3 generate_weekly_report.py --days 14 # 生成最近14天的周报
"""

import argparse
import os
from datetime import date
from pathlib import Path

from src.storage.database import Database
from src.reporting.report_generator import WeeklyReportGenerator

# 加载环境变量
def load_env_file(env_path: str = '.env'):
    """加载.env文件中的环境变量"""
    env_file = Path(env_path)
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='生成IDC行业周报')
    parser.add_argument('--days', type=int, default=7,
                       help='统计最近N天的数据（默认7天）')
    parser.add_argument('--db', type=str, default='data/intelligence.db',
                       help='数据库文件路径')
    parser.add_argument('--output', type=str, default=None,
                       help='输出文件路径（默认: reports/IDC_Weekly_Report_YYYY_MM_DD.md）')
    parser.add_argument('--send-email', action='store_true',
                       help='生成周报后自动发送邮件')
    parser.add_argument('--email-only', action='store_true',
                       help='仅发送邮件，不保存文件')

    args = parser.parse_args()

    # 加载环境变量
    load_env_file()

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

    # 保存报告（除非仅发送邮件）
    if not args.email_only:
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

    # 发送邮件（如果需要）
    if args.send_email or args.email_only:
        print(f"\n{'='*80}")
        print("开始发送邮件...")
        print("="*80)

        try:
            from src.notification.email_sender import EmailSender

            # 创建邮件发送器
            sender = EmailSender.from_env()

            # 发送周报邮件（使用板块布局）
            success = sender.send_weekly_report(
                report_content=report_content,
                use_block_layout=True  # 使用板块布局
            )

            if success:
                print("\n✓ 邮件发送成功！")
                print(f"✓ 收件人: {os.getenv('EMAIL_RECIPIENTS', 'li.xiaoyu@vnet.com')}")
            else:
                print("\n✗ 邮件发送失败！请检查邮箱配置。")

        except Exception as e:
            print(f"\n✗ 邮件发送异常: {e}")

    db.close()

    print(f"\n{'='*80}")
    print("周报生成完成！")
    print("="*80)


if __name__ == "__main__":
    main()

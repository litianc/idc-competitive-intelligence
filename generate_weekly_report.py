#!/usr/bin/env python3
"""
IDC行业竞争情报系统 - 周报生成脚本

使用方法:
    python3 generate_weekly_report.py                    # 生成最近7天的周报
    python3 generate_weekly_report.py --days 14          # 生成最近14天的周报
    python3 generate_weekly_report.py --send-email       # 生成并发送邮件
    python3 generate_weekly_report.py --no-pdf           # 不生成PDF
"""

import argparse
import os
from datetime import date
from pathlib import Path

from src.storage.database import Database
from src.reporting.report_generator import WeeklyReportGenerator
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='生成IDC行业周报')
    parser.add_argument('--days', type=int, default=7,
                       help='统计最近N天的数据（默认7天）')
    parser.add_argument('--db', type=str, default='data/intelligence.db',
                       help='数据库文件路径')
    parser.add_argument('--output', type=str, default=None,
                       help='输出文件路径（默认: reports/weekly_report.md）')
    parser.add_argument('--send-email', action='store_true',
                       help='生成周报后自动发送邮件')
    parser.add_argument('--email-only', action='store_true',
                       help='仅发送邮件，不保存文件')
    parser.add_argument('--no-pdf', action='store_true',
                       help='不生成PDF文件')
    parser.add_argument('--no-llm', action='store_true',
                       help='不使用LLM生成摘要')

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

    # 创建生成器（控制LLM摘要）
    generator = WeeklyReportGenerator(
        database=db,
        enable_llm_summary=not args.no_llm
    )

    # 确定输出路径
    if args.output:
        output_file = args.output
    else:
        # 默认保存到 reports 目录
        reports_dir = Path('reports')
        reports_dir.mkdir(exist_ok=True)
        output_file = reports_dir / "weekly_report.md"

    # 保存报告（除非仅发送邮件）
    if not args.email_only:
        # 使用新的generate_and_save方法（支持HTML和PDF）
        result = generator.generate_and_save(
            output_path=str(output_file),
            days=args.days,
            generate_html=True,
            generate_pdf=not args.no_pdf
        )

        print(f"\n✓ 周报已生成!")
        print(f"✓ Markdown: {result['markdown']}")
        if result['html']:
            print(f"✓ HTML:     {result['html']}")
        if result['pdf']:
            pdf_size = os.path.getsize(result['pdf']) / 1024
            print(f"✓ PDF:      {result['pdf']} ({pdf_size:.1f} KB)")
        elif not args.no_pdf:
            print(f"⚠️  PDF生成失败（但不影响其他文件）")

        # 读取报告内容（用于预览和邮件）
        with open(result['markdown'], 'r', encoding='utf-8') as f:
            report_content = f.read()

        # 保存PDF路径供后续使用
        pdf_file = result.get('pdf')
    else:
        # 仅发送邮件模式，直接生成内容
        report_content = generator.generate_report(days=args.days)
        pdf_file = None

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

            # 发送周报邮件（使用板块布局，附加PDF）
            success = sender.send_weekly_report(
                report_content=report_content,
                use_block_layout=True,  # 使用板块布局
                pdf_attachment=pdf_file if not args.email_only else None,  # 使用已生成的PDF
                auto_generate_pdf=args.email_only and not args.no_pdf  # email_only模式下自动生成PDF
            )

            if success:
                print("\n✓ 邮件发送成功！")
                print(f"✓ 收件人: {os.getenv('EMAIL_RECIPIENTS', 'li.xiaoyu@vnet.com')}")
                if pdf_file or (args.email_only and not args.no_pdf):
                    print(f"✓ 已附加PDF文件")
            else:
                print("\n✗ 邮件发送失败！请检查邮箱配置。")

        except Exception as e:
            print(f"\n✗ 邮件发送异常: {e}")
            import traceback
            traceback.print_exc()

    db.close()

    print(f"\n{'='*80}")
    print("周报生成完成！")
    print("="*80)


if __name__ == "__main__":
    main()

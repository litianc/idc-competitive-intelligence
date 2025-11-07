#!/usr/bin/env python3
"""
测试邮件发送功能

功能：
1. 生成最新的周报（Markdown格式）
2. 将周报转换为精美HTML格式
3. 通过SMTP发送到指定邮箱

使用方法:
    python3 tmp/test_email_report.py                    # 使用默认配置
    python3 tmp/test_email_report.py --days 7           # 指定统计天数
    python3 tmp/test_email_report.py --to another@example.com  # 指定收件人
"""

import sys
import os
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.storage.database import Database
from src.reporting.report_generator import WeeklyReportGenerator
from src.notification.email_sender import EmailSender
from src.notification.email_template import generate_html_report

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


def load_env_file(env_path: str = '.env'):
    """加载.env文件中的环境变量"""
    env_file = project_root / env_path
    if not env_file.exists():
        logger.warning(f".env文件不存在: {env_file}")
        return

    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

    logger.info("已从.env文件加载环境变量")


def generate_latest_report(days: int = 7) -> tuple:
    """
    生成最新周报

    Args:
        days: 统计最近N天的数据

    Returns:
        (markdown_content, date_range) 元组
    """
    logger.info("=" * 80)
    logger.info("开始生成周报")
    logger.info("=" * 80)

    # 计算日期范围
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)

    logger.info(f"统计时间范围: {start_date} 至 {end_date}")

    # 连接数据库
    db_path = os.getenv('DATABASE_PATH', 'data/intelligence.db')
    db = Database(db_path)

    # 创建报告生成器
    generator = WeeklyReportGenerator(db)

    # 生成报告
    markdown_content = generator.generate_report(days=days)

    # 格式化日期范围
    date_range = f"{start_date} 至 {end_date}"

    logger.info(f"✓ 周报生成完成，共 {len(markdown_content)} 字符")

    return markdown_content, date_range


def send_email_report(
    markdown_content: str,
    date_range: str,
    recipients: list = None
) -> bool:
    """
    发送邮件周报

    Args:
        markdown_content: Markdown格式的周报内容
        date_range: 日期范围（如"2025-01-06 至 2025-01-12"）
        recipients: 收件人列表

    Returns:
        是否发送成功
    """
    logger.info("=" * 80)
    logger.info("开始发送邮件")
    logger.info("=" * 80)

    try:
        # 创建邮件发送器
        sender = EmailSender.from_env()

        # 构造邮件主题
        subject = f"IDC行业竞争情报周报 - {date_range}"

        # 转换为HTML格式
        logger.info("正在将Markdown转换为HTML...")
        html_content = generate_html_report(
            markdown_content,
            title=subject
        )

        logger.info(f"✓ HTML转换完成，共 {len(html_content)} 字符")

        # 发送邮件
        logger.info("正在连接SMTP服务器并发送邮件...")

        if recipients:
            logger.info(f"收件人: {', '.join(recipients)}")

        success = sender.send_weekly_report(
            report_content=html_content,
            recipients=recipients,
            report_date=date_range
        )

        if success:
            logger.info("=" * 80)
            logger.info("✓ 邮件发送成功！")
            logger.info("=" * 80)
        else:
            logger.error("=" * 80)
            logger.error("✗ 邮件发送失败！")
            logger.error("=" * 80)

        return success

    except Exception as e:
        logger.error(f"✗ 邮件发送异常: {e}", exc_info=True)
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='测试邮件发送功能 - 生成并发送最新周报')
    parser.add_argument('--days', type=int, default=7,
                       help='统计最近N天的数据（默认7天）')
    parser.add_argument('--to', type=str, default=None,
                       help='收件人邮箱（多个邮箱用逗号分隔，默认从环境变量读取）')
    parser.add_argument('--env', type=str, default='.env',
                       help='.env文件路径（默认项目根目录下的.env）')

    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("IDC行业竞争情报系统 - 邮件发送测试")
    logger.info("=" * 80)
    logger.info(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"统计天数: {args.days}天")

    # 加载环境变量
    load_env_file(args.env)

    # 解析收件人
    recipients = None
    if args.to:
        recipients = [r.strip() for r in args.to.split(',')]
        logger.info(f"指定收件人: {', '.join(recipients)}")
    else:
        logger.info("收件人: 使用环境变量配置")

    try:
        # 1. 生成周报
        markdown_content, date_range = generate_latest_report(days=args.days)

        # 2. 发送邮件
        success = send_email_report(
            markdown_content=markdown_content,
            date_range=date_range,
            recipients=recipients
        )

        # 3. 退出
        if success:
            logger.info("\\n测试成功！请检查邮箱是否收到周报。")
            sys.exit(0)
        else:
            logger.error("\\n测试失败！请检查错误日志。")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("\\n用户中断")
        sys.exit(130)

    except Exception as e:
        logger.error(f"\\n测试失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

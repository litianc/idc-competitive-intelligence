#!/usr/bin/env python3
"""
测试新的板块布局邮件
"""

import sys
import os
from pathlib import Path

# 添加项目根目录
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.storage.database import Database
from src.reporting.report_generator import WeeklyReportGenerator
from src.notification.email_sender import EmailSender
from src.notification.email_template_v2 import generate_html_report

# 加载环境变量
def load_env():
    env_file = project_root / '.env'
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

def main():
    print("="*80)
    print("测试新的板块布局邮件")
    print("="*80)

    # 加载环境变量
    load_env()

    # 生成周报
    print("\n1. 生成周报内容...")
    db = Database('data/intelligence.db')
    generator = WeeklyReportGenerator(db)
    markdown_content = generator.generate_report(days=7)
    print(f"   ✓ 周报生成完成: {len(markdown_content)} 字符")

    # 转换为新布局HTML
    print("\n2. 转换为板块布局HTML...")
    html_content = generate_html_report(markdown_content)
    print(f"   ✓ HTML生成完成: {len(html_content)} 字符")

    # 发送邮件
    print("\n3. 发送邮件...")
    sender = EmailSender.from_env()

    # 从环境变量获取收件人
    recipients_str = os.getenv('EMAIL_RECIPIENTS', 'test@example.com')
    recipients = [r.strip() for r in recipients_str.split(',')]

    # 直接使用HTML内容
    success = sender.send_html_email(
        subject="IDC行业竞争情报周报 - 板块布局版",
        html_content=html_content,
        recipients=recipients
    )

    if success:
        print("   ✓ 邮件发送成功！")
    else:
        print("   ✗ 邮件发送失败！")

    print("\n" + "="*80)
    print("测试完成！请查收邮件。")
    print("="*80)


if __name__ == "__main__":
    main()
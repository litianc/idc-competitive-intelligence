#!/usr/bin/env python3
"""
测试邮件收件人显示修复
"""

import os
from dotenv import load_dotenv
from email.mime.multipart import MIMEMultipart
from email.header import Header

load_dotenv()

# 测试1：查看修复前的格式（错误）
print("=" * 60)
print("测试1：修复前的收件人格式（错误）")
print("=" * 60)
msg1 = MIMEMultipart()
msg1['To'] = Header('li.xiaoyu@vnet.com', 'utf-8')
print(f"To header: {msg1['To']}")
print()

# 测试2：查看修复后的格式（正确）
print("=" * 60)
print("测试2：修复后的收件人格式（正确）")
print("=" * 60)
msg2 = MIMEMultipart()
msg2['To'] = 'li.xiaoyu@vnet.com'
print(f"To header: {msg2['To']}")
print()

# 测试3：多个收件人
print("=" * 60)
print("测试3：多个收件人格式（正确）")
print("=" * 60)
recipients = ['user1@example.com', 'user2@example.com']
msg3 = MIMEMultipart()
msg3['To'] = ', '.join(recipients)
print(f"To header: {msg3['To']}")
print()

print("✓ 测试完成")
print()
print("分析：")
print("- 使用Header()包装邮件地址会导致显示为：li.xiaoyu@vnet.com@domain.invalid")
print("- 直接使用字符串则显示正常：li.xiaoyu@vnet.com")
print("- 已在 email_sender.py 中修复此问题")

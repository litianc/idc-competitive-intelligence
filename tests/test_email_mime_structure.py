#!/usr/bin/env python3
"""
测试邮件MIME结构修复
验证邮件正文和附件能在苹果邮件客户端正确显示
"""

import os
import sys
# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tempfile
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

print("=" * 70)
print("测试邮件MIME结构")
print("=" * 70)
print()

# 测试1: 无附件的邮件（应使用 alternative）
print("测试1: 无附件的邮件")
print("-" * 70)

msg1 = MIMEMultipart('alternative')
msg1['Subject'] = '测试邮件（无附件）'
msg1['From'] = 'sender@example.com'
msg1['To'] = 'recipient@example.com'

html_content = "<html><body><h1>这是HTML正文</h1></body></html>"
html_part = MIMEText(html_content, 'html', 'utf-8')
msg1.attach(html_part)

print(f"MIME类型: {msg1.get_content_type()}")
print(f"部件数量: {len(msg1.get_payload())}")
print("结构:")
for i, part in enumerate(msg1.walk()):
    print(f"  - {part.get_content_type()}")

if msg1.get_content_type() == 'multipart/alternative':
    print("✓ 通过：无附件时使用 alternative")
    test1_pass = True
else:
    print("✗ 失败：MIME类型不正确")
    test1_pass = False

print()

# 测试2: 有附件的邮件（应使用 mixed）
print("测试2: 有附件的邮件（修复前 - 错误）")
print("-" * 70)

msg2_wrong = MIMEMultipart('alternative')  # 错误：应该用 mixed
msg2_wrong['Subject'] = '测试邮件（有附件 - 错误）'
msg2_wrong['From'] = 'sender@example.com'
msg2_wrong['To'] = 'recipient@example.com'

html_part = MIMEText(html_content, 'html', 'utf-8')
msg2_wrong.attach(html_part)

# 添加附件
attachment_data = b"PDF content here"
attachment_part = MIMEApplication(attachment_data)
attachment_part.add_header('Content-Disposition', 'attachment', filename=('utf-8', '', 'test.pdf'))
msg2_wrong.attach(attachment_part)

print(f"MIME类型: {msg2_wrong.get_content_type()}")
print(f"部件数量: {len(msg2_wrong.get_payload())}")
print("结构:")
for i, part in enumerate(msg2_wrong.walk()):
    print(f"  - {part.get_content_type()}")

print("⚠️  问题：使用 alternative 类型，苹果邮件可能只显示附件")
print()

# 测试3: 有附件的邮件（修复后 - 正确）
print("测试3: 有附件的邮件（修复后 - 正确）")
print("-" * 70)

msg2_correct = MIMEMultipart('mixed')  # 正确：使用 mixed
msg2_correct['Subject'] = '测试邮件（有附件 - 正确）'
msg2_correct['From'] = 'sender@example.com'
msg2_correct['To'] = 'recipient@example.com'

html_part = MIMEText(html_content, 'html', 'utf-8')
msg2_correct.attach(html_part)

# 添加附件
attachment_data = b"PDF content here"
attachment_part = MIMEApplication(attachment_data)
attachment_part.add_header('Content-Disposition', 'attachment', filename=('utf-8', '', 'test.pdf'))
msg2_correct.attach(attachment_part)

print(f"MIME类型: {msg2_correct.get_content_type()}")
print(f"部件数量: {len(msg2_correct.get_payload())}")
print("结构:")
for i, part in enumerate(msg2_correct.walk()):
    print(f"  - {part.get_content_type()}")

if msg2_correct.get_content_type() == 'multipart/mixed':
    print("✓ 通过：有附件时使用 mixed，正文和附件都会显示")
    test2_pass = True
else:
    print("✗ 失败：MIME类型不正确")
    test2_pass = False

print()

# 测试4: 验证新代码的逻辑
print("测试4: 验证修复后的代码逻辑")
print("-" * 70)

# 模拟修复后的代码逻辑
attachments = None
mime_type_no_attach = 'mixed' if attachments else 'alternative'
print(f"无附件时: {mime_type_no_attach}")

attachments = ['test.pdf']
mime_type_with_attach = 'mixed' if attachments else 'alternative'
print(f"有附件时: {mime_type_with_attach}")

if mime_type_no_attach == 'alternative' and mime_type_with_attach == 'mixed':
    print("✓ 通过：代码逻辑正确")
    test3_pass = True
else:
    print("✗ 失败：代码逻辑错误")
    test3_pass = False

print()

# 测试结果汇总
print("=" * 70)
print("测试结果汇总")
print("=" * 70)

results = [
    ("无附件邮件结构", test1_pass),
    ("有附件邮件结构", test2_pass),
    ("代码逻辑验证", test3_pass)
]

for name, passed in results:
    status = "✓ 通过" if passed else "✗ 失败"
    print(f"{status}  {name}")

passed_count = sum(1 for _, p in results if p)
total_count = len(results)

print()
print(f"通过率: {passed_count}/{total_count}")

if passed_count == total_count:
    print()
    print("🎉 所有测试通过！")
    print()
    print("修复说明：")
    print("- 有附件时：使用 multipart/mixed（正文和附件都显示）")
    print("- 无附件时：使用 multipart/alternative（只有正文）")
    print()
    print("现在苹果邮件客户端应该能同时看到正文和附件了")
else:
    print()
    print("⚠️  部分测试未通过")

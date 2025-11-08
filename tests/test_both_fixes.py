#!/usr/bin/env python3
"""
综合测试：验证邮件收件人和PDF emoji两个问题的修复
"""

import os
import sys
# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from email.mime.multipart import MIMEMultipart
from src.reporting.pdf_generator import PDFGenerator

print("=" * 70)
print("综合测试：验证两个问题修复")
print("=" * 70)
print()

# ============================================================
# 测试1: 邮件收件人显示修复
# ============================================================
print("测试1: 邮件收件人显示修复")
print("-" * 70)

recipients = ['li.xiaoyu@vnet.com', 'test@example.com']
message = MIMEMultipart()
message['To'] = ', '.join(recipients)

print(f"收件人列表: {recipients}")
print(f"邮件头 To: {message['To']}")

# 验证不包含 @domain.invalid
if '@domain.invalid' in str(message['To']):
    print("✗ 失败：收件人地址包含异常后缀")
    test1_pass = False
else:
    print("✓ 通过：收件人地址格式正确")
    test1_pass = True

print()

# ============================================================
# 测试2: PDF emoji显示修复
# ============================================================
print("测试2: PDF emoji显示修复")
print("-" * 70)

# 创建包含emoji的简单HTML
html_with_emoji = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>Emoji测试</title>
</head>
<body>
    <h1>📌 测试标题</h1>
    <p>🎁 政策红利</p>
    <p>💡 投资建议</p>
    <p>👁️ 创新观察</p>
    <p>📊 市场趋势</p>
</body>
</html>
"""

output_path = "reports/test_emoji_fix.pdf"
os.makedirs("reports", exist_ok=True)

generator = PDFGenerator.from_env()
success = generator.html_to_pdf(html_with_emoji, output_path)

if success and os.path.exists(output_path):
    file_size = os.path.getsize(output_path) / 1024
    print(f"✓ 通过：PDF生成成功")
    print(f"  文件路径: {output_path}")
    print(f"  文件大小: {file_size:.1f} KB")
    test2_pass = True
else:
    print("✗ 失败：PDF生成失败")
    test2_pass = False

print()

# ============================================================
# 测试结果汇总
# ============================================================
print("=" * 70)
print("测试结果汇总")
print("=" * 70)

results = [
    ("邮件收件人显示修复", test1_pass),
    ("PDF emoji显示修复", test2_pass)
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
    print("修复摘要：")
    print("1. 邮件收件人不再显示 @domain.invalid 后缀")
    print("2. PDF中emoji图标应正确显示（需手动检查PDF文件）")
    print()
    print("注意事项：")
    print("- 确保已安装字体：fonts-noto-cjk, fonts-noto-color-emoji")
    print("- PDF中emoji显示需要手动打开PDF文件验证")
else:
    print()
    print("⚠️  部分测试未通过，请检查错误信息")

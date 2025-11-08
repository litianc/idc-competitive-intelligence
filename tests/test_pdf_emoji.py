#!/usr/bin/env python3
"""
测试PDF中emoji显示
"""

from src.reporting.pdf_generator import PDFGenerator
import os
import sys
# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 60)
print("测试PDF中emoji显示")
print("=" * 60)
print()

# 创建包含emoji的HTML测试内容
html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>Emoji测试</title>
</head>
<body>
    <h1>📌 本周概览</h1>
    <p>这是一段包含多种emoji的测试文本：</p>

    <h2>🎁 政策红利</h2>
    <p>本周政策领域收录1篇文章</p>

    <h2>💡 投资建议</h2>
    <p>本周投资领域收录1篇文章</p>

    <h2>👁️ 创新观察</h2>
    <p>本周技术领域收录1篇文章</p>

    <h2>📊 市场趋势</h2>
    <p>本周市场领域收录1篇文章</p>

    <div style="margin-top: 30px;">
        <h3>所有测试emoji：</h3>
        <p>📋 ⚖️ 📜 ✅ 🧭 🎁 📡 🏛️</p>
        <p>🔥 💰 💎 🎯 💵 📈 🔍 💡</p>
        <p>🚀 ✨ ⚡ 🔬 🌟 👁️ 🧭 💡</p>
        <p>👁️ ♟️ 📊 💓 📈 🔍 💼 🧭</p>
        <p>📢 🔭 🌐 📡 💡 🤔 💓 📊</p>
    </div>

    <div style="margin-top: 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white; padding: 20px; border-radius: 10px;">
        <h3>渐变背景 + Emoji测试</h3>
        <p>📌 本周共收录115篇IDC行业相关文章</p>
        <p>🎁 政策红利：国家级算力政策密集出台</p>
        <p>💡 投资建议：百亿级项目频现</p>
    </div>
</body>
</html>
"""

# 生成PDF
output_path = "reports/emoji_test.pdf"
os.makedirs("reports", exist_ok=True)

generator = PDFGenerator.from_env()
success = generator.html_to_pdf(html_content, output_path)

if success:
    file_size = os.path.getsize(output_path)
    print(f"✓ PDF生成成功: {output_path}")
    print(f"  文件大小: {file_size / 1024:.1f} KB")
    print()
    print("请打开PDF文件检查emoji是否正确显示：")
    print(f"  {os.path.abspath(output_path)}")
    print()
    print("期望结果：")
    print("  - 所有emoji应正确显示为彩色图标")
    print("  - 中文文字应正确显示")
    print("  - 渐变背景应正确显示")
else:
    print("✗ PDF生成失败")

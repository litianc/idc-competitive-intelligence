"""
测试PDF生成功能

验证：
1. HTML到PDF的转换功能
2. 周报生成流程中的PDF集成
3. PDF文件质量和大小
"""

import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from src.reporting.report_generator import WeeklyReportGenerator
from src.reporting.pdf_generator import PDFGenerator, generate_weekly_report_pdf
from src.notification.email_template_v2 import generate_html_report


def test_basic_pdf_generation():
    """测试基础PDF生成功能"""
    print("=" * 60)
    print("测试1: 基础PDF生成功能")
    print("=" * 60)

    # 创建简单的测试HTML
    test_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            h1 { color: #667eea; }
            .highlight { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                         color: white; padding: 20px; border-radius: 10px; }
        </style>
    </head>
    <body>
        <h1>PDF生成测试</h1>
        <div class="highlight">
            <p>这是一个测试HTML内容，包含渐变背景和中文字符。</p>
            <p>支持emoji: 📌 💡 🔥 ⚡ 📊</p>
        </div>
        <p>普通段落文字测试。</p>
    </body>
    </html>
    """

    # 生成PDF
    os.makedirs("reports", exist_ok=True)
    output_path = "reports/test_basic.pdf"

    generator = PDFGenerator.from_env()
    success = generator.html_to_pdf(test_html, output_path)

    if success and os.path.exists(output_path):
        file_size = os.path.getsize(output_path) / 1024
        print(f"\n✓ 基础PDF生成成功")
        print(f"  文件路径: {output_path}")
        print(f"  文件大小: {file_size:.1f} KB")
        return True
    else:
        print(f"\n✗ 基础PDF生成失败")
        return False


def test_weekly_report_pdf():
    """测试周报PDF生成"""
    print("\n" + "=" * 60)
    print("测试2: 周报PDF生成（完整流程）")
    print("=" * 60)

    try:
        # 生成周报（包含Markdown, HTML, PDF）
        generator = WeeklyReportGenerator(
            db_path="data/intelligence.db",
            enable_llm_summary=True
        )

        output_path = "reports/weekly_report_pdf_test.md"
        result = generator.generate_and_save(
            output_path=output_path,
            days=7,
            generate_html=True,
            generate_pdf=True
        )

        print(f"\n生成结果:")
        print(f"  Markdown: {result['markdown'] or '✗ 失败'}")
        print(f"  HTML:     {result['html'] or '✗ 失败'}")
        print(f"  PDF:      {result['pdf'] or '✗ 失败'}")

        if result['pdf'] and os.path.exists(result['pdf']):
            file_size = os.path.getsize(result['pdf']) / 1024
            print(f"\n✓ 周报PDF生成成功")
            print(f"  文件大小: {file_size:.1f} KB")

            # 检查文件完整性
            if file_size < 10:
                print(f"  ⚠️  警告: PDF文件可能不完整（太小）")
                return False

            return True
        else:
            print(f"\n✗ 周报PDF生成失败")
            return False

    except Exception as e:
        print(f"\n✗ 周报PDF生成异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pdf_from_markdown():
    """测试从已有Markdown生成PDF"""
    print("\n" + "=" * 60)
    print("测试3: 从已有Markdown生成PDF")
    print("=" * 60)

    md_file = "reports/weekly_report_test.md"

    if not os.path.exists(md_file):
        print(f"  ⚠️  跳过测试: Markdown文件不存在 ({md_file})")
        print(f"     请先运行 test_weekly_summary.py 生成测试周报")
        return None

    try:
        # 读取Markdown
        with open(md_file, 'r', encoding='utf-8') as f:
            markdown_content = f.read()

        # 生成HTML
        html_content = generate_html_report(markdown_content)

        # 生成PDF
        pdf_path = generate_weekly_report_pdf(
            html_content=html_content,
            output_dir="reports",
            filename="from_markdown_test.pdf"
        )

        if pdf_path and os.path.exists(pdf_path):
            file_size = os.path.getsize(pdf_path) / 1024
            print(f"\n✓ 从Markdown生成PDF成功")
            print(f"  文件路径: {pdf_path}")
            print(f"  文件大小: {file_size:.1f} KB")
            return True
        else:
            print(f"\n✗ 从Markdown生成PDF失败")
            return False

    except Exception as e:
        print(f"\n✗ 从Markdown生成PDF异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_playwright_installation():
    """检查Playwright安装状态"""
    print("\n" + "=" * 60)
    print("检查环境依赖")
    print("=" * 60)

    try:
        from playwright.sync_api import sync_playwright
        print("✓ Playwright已安装")

        # 检查浏览器
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                browser.close()
                print("✓ Chromium浏览器可用")
                return True
        except Exception as e:
            print(f"✗ Chromium浏览器不可用: {e}")
            print(f"\n请运行以下命令安装浏览器:")
            print(f"  playwright install chromium")
            return False

    except ImportError:
        print("✗ Playwright未安装")
        print(f"\n请运行以下命令安装:")
        print(f"  pip install playwright")
        print(f"  playwright install chromium")
        return False


if __name__ == "__main__":
    print("\n🧪 PDF生成功能测试\n")

    # 检查数据库
    if not os.path.exists("data/intelligence.db"):
        print("⚠️  警告: 数据库文件不存在，测试2可能会失败")
        print("   请先运行采集脚本以生成数据\n")

    # 检查环境
    if not check_playwright_installation():
        print("\n✗ 环境检查失败，无法继续测试")
        sys.exit(1)

    # 运行测试
    results = []

    print("\n" + "=" * 60)
    print("开始测试")
    print("=" * 60)

    # 测试1: 基础PDF生成
    results.append(("基础PDF生成", test_basic_pdf_generation()))

    # 测试2: 周报PDF生成
    results.append(("周报PDF生成", test_weekly_report_pdf()))

    # 测试3: 从Markdown生成PDF
    result3 = test_pdf_from_markdown()
    if result3 is not None:
        results.append(("从Markdown生成PDF", result3))

    # 统计结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    passed = sum(1 for _, result in results if result is True)
    total = len(results)

    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status}  {name}")

    print(f"\n通过率: {passed}/{total}")

    if passed == total:
        print("\n✓ 所有测试通过！")
        print("\n生成的PDF文件:")
        print("  - reports/test_basic.pdf")
        print("  - reports/weekly_report_pdf_test.pdf")
        print("  - reports/from_markdown_test.pdf (如果测试3运行)")
        print("\n下一步:")
        print("  1. 检查PDF文件质量（打开查看）")
        print("  2. 验证中文、emoji、渐变色等元素是否正常显示")
        print("  3. 测试邮件发送功能（如果配置了SMTP）")
        sys.exit(0)
    else:
        print(f"\n✗ {total - passed} 个测试失败")
        sys.exit(1)

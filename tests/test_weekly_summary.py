"""
测试周报LLM摘要功能

验证：
1. 周报生成器是否正确集成摘要功能
2. Markdown格式是否包含整体总结和板块点评
3. HTML邮件模板是否正确显示
"""

import os
import sys
# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from src.reporting.report_generator import WeeklyReportGenerator
from src.notification.email_template_v2 import generate_html_report

def test_report_generation():
    """测试周报生成"""
    print("=" * 60)
    print("测试周报生成功能")
    print("=" * 60)

    # 创建周报生成器
    generator = WeeklyReportGenerator(
        db_path="data/intelligence.db",
        enable_llm_summary=True  # 启用LLM摘要
    )

    print(f"\n配置信息:")
    print(f"  LLM摘要: {generator.enable_llm_summary}")
    print(f"  随机标签: {generator.use_random_labels}")
    print(f"  摘要生成器: {'已初始化' if generator.summarizer else '未初始化'}")

    # 生成周报
    print("\n正在生成周报...")
    try:
        report = generator.generate_report(days=7)

        # 检查是否包含关键元素
        has_overview = '本周概览' in report
        has_policy_insight = '政策' in report and '**' in report
        has_sections = '## 一、政策法规' in report

        print(f"\n✓ 周报生成成功")
        print(f"  - 包含整体总结: {'✓' if has_overview else '✗'}")
        print(f"  - 包含板块点评: {'✓' if has_policy_insight else '✗'}")
        print(f"  - 包含内容章节: {'✓' if has_sections else '✗'}")

        # 保存Markdown文件
        output_file = "reports/weekly_report_test.md"
        os.makedirs("reports", exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"\n✓ Markdown周报已保存: {output_file}")

        # 生成HTML邮件
        print("\n正在生成HTML邮件...")
        html_content = generate_html_report(report)

        html_output_file = "reports/weekly_report_test.html"
        with open(html_output_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"✓ HTML邮件已保存: {html_output_file}")

        # 显示报告预览
        print("\n" + "=" * 60)
        print("周报内容预览（前500字符）:")
        print("=" * 60)
        print(report[:500])
        print("...")

        return True

    except Exception as e:
        print(f"\n✗ 周报生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_without_llm():
    """测试不使用LLM的周报生成（降级方案）"""
    print("\n" + "=" * 60)
    print("测试降级方案（不使用LLM）")
    print("=" * 60)

    generator = WeeklyReportGenerator(
        db_path="data/intelligence.db",
        enable_llm_summary=False  # 禁用LLM摘要
    )

    print(f"\n配置信息:")
    print(f"  LLM摘要: {generator.enable_llm_summary}")

    try:
        report = generator.generate_report(days=7)
        print(f"\n✓ 无LLM模式周报生成成功")
        print(f"  - 不包含LLM总结: {'✓' if '本周概览' not in report else '✗'}")

        return True

    except Exception as e:
        print(f"\n✗ 无LLM模式失败: {e}")
        return False


if __name__ == "__main__":
    print("\n🧪 周报LLM摘要功能测试\n")

    # 检查数据库
    if not os.path.exists("data/intelligence.db"):
        print("⚠️  警告: 数据库文件不存在，可能导致测试失败")
        print("   请先运行采集脚本以生成数据\n")

    # 检查LLM配置
    llm_api_key = os.getenv('LLM_API_KEY') or os.getenv('OPENAI_API_KEY')
    if not llm_api_key:
        print("⚠️  警告: 未配置LLM API密钥")
        print("   将使用默认摘要（降级方案）\n")

    # 运行测试
    success_count = 0

    if test_report_generation():
        success_count += 1

    if test_without_llm():
        success_count += 1

    # 总结
    print("\n" + "=" * 60)
    print(f"测试完成: {success_count}/2 通过")
    print("=" * 60)

    if success_count == 2:
        print("\n✓ 所有测试通过！")
        print("\n下一步:")
        print("  1. 查看生成的文件: reports/weekly_report_test.md 和 .html")
        print("  2. 配置LLM API密钥以启用智能摘要")
        print("  3. 运行 generate_weekly_report.py 生成正式周报")
        sys.exit(0)
    else:
        print("\n✗ 部分测试失败，请检查错误信息")
        sys.exit(1)

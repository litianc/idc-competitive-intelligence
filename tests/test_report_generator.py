"""
测试周报生成器

TDD方式：先写测试，再实现功能
"""

import pytest
from datetime import date, timedelta
from src.reporting.report_generator import WeeklyReportGenerator
from src.storage.database import Database


class TestWeeklyReportGenerator:
    """周报生成器测试类"""

    @pytest.fixture
    def test_db(self):
        """创建测试数据库"""
        db = Database(":memory:")

        # 插入测试数据
        today = date.today()

        # 高优先级投资类文章
        db.insert_article(
            title="某公司完成10亿元C轮融资用于数据中心建设",
            url="https://example.com/1",
            source="中国IDC圈",
            source_tier=1,
            publish_date=today - timedelta(days=1),
            content="某公司宣布完成10亿元C轮融资...",
            summary="某公司完成10亿元C轮融资，将用于在北京、上海、深圳建设大型数据中心，预计新增机柜10000个，提升算力服务能力。",
            category="投资",
            priority="高",
            score=85,
            score_relevance=32,
            score_timeliness=25,
            score_impact=20,
            score_credibility=15,
            link_valid=True,
        )

        # 高优先级技术类文章
        db.insert_article(
            title="新型液冷技术突破PUE降至1.15",
            url="https://example.com/2",
            source="数据中心世界",
            source_tier=1,
            publish_date=today - timedelta(days=2),
            content="某厂商发布新型液冷技术...",
            summary="某厂商发布新型浸没式液冷技术，将数据中心PUE值降至1.15，相比传统风冷节能40%，已在多个大型数据中心应用。",
            category="技术",
            priority="高",
            score=78,
            score_relevance=24,
            score_timeliness=21,
            score_impact=18,
            score_credibility=15,
            link_valid=True,
        )

        # 中优先级市场类文章
        db.insert_article(
            title="2024年数据中心市场分析报告",
            url="https://example.com/3",
            source="InfoQ",
            source_tier=2,
            publish_date=today - timedelta(days=3),
            content="市场研究报告显示...",
            summary="2024年中国数据中心市场规模达3500亿元，同比增长25%，预计2025年将突破4000亿元，AI算力需求成为主要增长动力。",
            category="市场",
            priority="中",
            score=55,
            score_relevance=16,
            score_timeliness=18,
            score_impact=10,
            score_credibility=8,
            link_valid=True,
        )

        # 低优先级文章
        db.insert_article(
            title="某公司举办年会",
            url="https://example.com/4",
            source="36氪",
            source_tier=2,
            publish_date=today - timedelta(days=10),
            content="某公司举办年度员工大会...",
            summary="某公司举办年度员工大会，表彰优秀员工。",
            category="市场",
            priority="低",
            score=20,
            score_relevance=0,
            score_timeliness=0,
            score_impact=0,
            score_credibility=8,
            link_valid=True,
        )

        yield db
        db.close()

    @pytest.fixture
    def generator(self, test_db):
        """创建周报生成器实例"""
        return WeeklyReportGenerator(database=test_db)

    def test_generator_initialization(self, test_db):
        """测试：周报生成器初始化"""
        generator = WeeklyReportGenerator(database=test_db)
        assert generator is not None
        assert generator.db is not None

    def test_get_articles_for_report(self, generator):
        """测试：获取周报文章数据"""
        articles = generator.get_articles_for_report(days=7)

        # 应该只包含7天内的文章（排除10天前的文章）
        assert len(articles) == 3

        # 文章应该按评分降序排列
        scores = [a['score'] for a in articles]
        assert scores == sorted(scores, reverse=True)

    def test_group_articles_by_category(self, generator):
        """测试：按分类分组文章"""
        articles = generator.get_articles_for_report(days=7)
        grouped = generator.group_by_category(articles)

        assert "投资" in grouped
        assert "技术" in grouped
        assert "市场" in grouped

        # 验证分组正确
        assert len(grouped["投资"]) == 1
        assert len(grouped["技术"]) == 1
        assert len(grouped["市场"]) == 1

    def test_group_articles_by_priority(self, generator):
        """测试：按优先级分组文章"""
        articles = generator.get_articles_for_report(days=7)
        grouped = generator.group_by_priority(articles)

        assert "高" in grouped
        assert "中" in grouped

        # 高优先级应该有2篇
        assert len(grouped["高"]) == 2
        # 中优先级应该有1篇
        assert len(grouped["中"]) == 1

    def test_generate_markdown_report(self, generator):
        """测试：生成Markdown格式周报"""
        report = generator.generate_report()

        # 验证报告不为空
        assert report is not None
        assert len(report) > 0

        # 验证包含必要的标题和章节
        assert "# IDC行业周报" in report
        assert "## 一、投资动态" in report
        assert "## 二、技术进展" in report
        assert "## 四、市场动态" in report  # 第三章节是政策法规

        # 验证包含文章标题
        assert "某公司完成10亿元C轮融资" in report
        assert "新型液冷技术突破" in report

    def test_report_chinese_format(self, generator):
        """测试：中文商业格式规范"""
        report = generator.generate_report()

        # 检查中文编号
        assert "一、" in report
        assert "二、" in report
        assert "三、" in report

        # 检查全角括号
        assert "【投资】" in report or "【技术】" in report

        # 不应该出现半角括号
        assert "[投资]" not in report

    def test_report_includes_metadata(self, generator):
        """测试：报告包含元数据"""
        report = generator.generate_report()

        # 应该包含来源和日期
        assert " | " in report

        # 应该包含链接
        assert "[详情]" in report or "http" in report

    def test_report_article_ordering(self, generator):
        """测试：文章按评分排序"""
        articles = generator.get_articles_for_report(days=7)
        high_priority = [a for a in articles if a['priority'] == '高']

        # 高优先级文章应该按评分降序
        if len(high_priority) > 1:
            scores = [a['score'] for a in high_priority]
            assert scores == sorted(scores, reverse=True)

    def test_empty_category_handling(self, generator):
        """测试：处理空分类"""
        # 创建只有投资类文章的数据库
        db = Database(":memory:")
        db.insert_article(
            title="测试文章",
            url="https://example.com/test",
            source="测试来源",
            source_tier=1,
            publish_date=date.today(),
            content="测试内容",
            summary="测试摘要",
            category="投资",
            priority="高",
            score=80,
            score_relevance=32,
            score_timeliness=25,
            score_impact=15,
            score_credibility=15,
            link_valid=True,
        )

        gen = WeeklyReportGenerator(database=db)
        report = gen.generate_report()

        # 应该只有投资动态章节，其他章节应该显示"暂无"或不显示
        assert "## 一、投资动态" in report
        assert "测试文章" in report

        db.close()

    def test_report_file_generation(self, generator, tmp_path):
        """测试：生成并保存周报文件"""
        output_file = tmp_path / "weekly_report.md"

        success = generator.generate_and_save(str(output_file))

        assert success is True
        assert output_file.exists()
        assert output_file.stat().st_size > 0

        # 验证文件内容
        content = output_file.read_text(encoding='utf-8')
        assert "# IDC行业周报" in content

    def test_report_date_range(self, generator):
        """测试：周报日期范围正确"""
        report = generator.generate_report(days=7)

        # 应该包含日期范围信息
        today = date.today()
        # 报告应该提到时间范围
        assert str(today.year) in report

    def test_article_summary_included(self, generator):
        """测试：文章摘要包含在报告中"""
        report = generator.generate_report()

        # 应该包含文章摘要内容
        assert "完成10亿元C轮融资" in report
        assert "浸没式液冷技术" in report or "液冷" in report

    def test_priority_filtering(self, generator):
        """测试：优先级过滤"""
        # 只获取高优先级文章
        articles = generator.get_articles_for_report(days=7)
        high_priority = [a for a in articles if a['priority'] == '高']

        assert len(high_priority) == 2

        # 验证都是高分文章
        for article in high_priority:
            assert article['score'] >= 70

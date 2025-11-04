"""
优先级评分系统单元测试

TDD原则：先写测试，再写实现
测试4维度评分模型：业务相关性、时效性、影响范围、来源可信度
"""

import pytest
from datetime import date, timedelta
from src.scoring.priority_scorer import PriorityScorer


class TestBusinessRelevanceScoring:
    """测试业务相关性评分（40分）"""

    @pytest.fixture
    def scorer(self):
        return PriorityScorer()

    def test_core_keywords_scoring(self, scorer):
        """测试核心关键词评分（IDC、数据中心、云计算等）"""
        # 包含核心关键词的内容
        content = "某公司宣布在北京建设大型数据中心，投资10亿元用于IDC基础设施建设"

        score = scorer.calculate_relevance_score("", content)

        # 包含"数据中心"(10分)和"IDC"(10分)，至少20分
        assert score >= 20
        assert score <= 40  # 不超过上限

    def test_ai_related_keywords(self, scorer):
        """测试AI算力相关关键词"""
        content = "该公司推出新一代GPU服务器，为AI算力中心提供核心支持"

        score = scorer.calculate_relevance_score("", content)

        # 包含"GPU"和"AI算力"
        assert score >= 20

    def test_no_relevant_keywords(self, scorer):
        """测试无相关关键词的内容"""
        content = "某公司举办年度员工大会，表彰优秀员工"

        score = scorer.calculate_relevance_score("", content)

        assert score == 0

    def test_title_and_content_both_count(self, scorer):
        """测试标题和内容都计入评分"""
        title = "IDC行业报告"
        content = "数据中心市场持续增长，云计算需求旺盛"

        score = scorer.calculate_relevance_score(title, content)

        # 标题有"IDC"，内容有"数据中心"和"云计算"
        assert score >= 30

    def test_relevance_score_cap(self, scorer):
        """测试相关性评分上限（40分）"""
        # 包含大量关键词
        content = """
        IDC数据中心云计算云服务AI算力GPU算力中心
        服务器机柜机房液冷制冷PUE边缘计算CDN
        """

        score = scorer.calculate_relevance_score("", content)

        # 最多40分
        assert score == 40


class TestTimelinessScoring:
    """测试时效性评分（25分）"""

    @pytest.fixture
    def scorer(self):
        return PriorityScorer()

    def test_today_article(self, scorer):
        """测试当天发布的文章（25分）"""
        publish_date = date.today()

        score = scorer.calculate_timeliness_score(publish_date)

        assert score == 25

    def test_one_day_ago(self, scorer):
        """测试1天前的文章"""
        publish_date = date.today() - timedelta(days=1)

        score = scorer.calculate_timeliness_score(publish_date)

        # 25 * (1 - 1/7) ≈ 21.4
        assert 21 <= score <= 22

    def test_three_days_ago(self, scorer):
        """测试3天前的文章"""
        publish_date = date.today() - timedelta(days=3)

        score = scorer.calculate_timeliness_score(publish_date)

        # 25 * (1 - 3/7) ≈ 14.3
        assert 14 <= score <= 15

    def test_seven_days_ago(self, scorer):
        """测试7天前的文章（0分）"""
        publish_date = date.today() - timedelta(days=7)

        score = scorer.calculate_timeliness_score(publish_date)

        assert score == 0

    def test_more_than_seven_days_ago(self, scorer):
        """测试超过7天的文章（0分）"""
        publish_date = date.today() - timedelta(days=10)

        score = scorer.calculate_timeliness_score(publish_date)

        assert score == 0

    def test_future_date(self, scorer):
        """测试未来日期（边界情况，应该返回25分）"""
        future_date = date.today() + timedelta(days=1)

        score = scorer.calculate_timeliness_score(future_date)

        # 未来日期应该被视为今天
        assert score == 25


class TestImpactScoring:
    """测试影响范围评分（20分）"""

    @pytest.fixture
    def scorer(self):
        return PriorityScorer()

    def test_large_funding(self, scorer):
        """测试大额融资（≥10亿元）"""
        content = "某公司完成15亿元C轮融资"

        score = scorer.calculate_impact_score("", content)

        assert score == 20

    def test_medium_funding(self, scorer):
        """测试中等融资（5-10亿元）"""
        content = "某公司获得7亿元投资"

        score = scorer.calculate_impact_score("", content)

        assert score == 15

    def test_small_funding(self, scorer):
        """测试小额融资（1-5亿元）"""
        content = "某公司获得2亿元A轮融资"

        score = scorer.calculate_impact_score("", content)

        assert score == 10

    def test_minimal_funding(self, scorer):
        """测试小额融资（<1亿元）"""
        content = "某公司获得5000万元天使轮融资"

        score = scorer.calculate_impact_score("", content)

        assert score == 5

    def test_large_datacenter_project(self, scorer):
        """测试大型数据中心项目（≥1万机柜）"""
        content = "该项目规划建设15000个机柜"

        score = scorer.calculate_impact_score("", content)

        assert score == 20

    def test_medium_datacenter_project(self, scorer):
        """测试中型数据中心项目（5千-1万机柜）"""
        content = "数据中心包含8000个机柜"

        score = scorer.calculate_impact_score("", content)

        assert score == 15

    def test_small_datacenter_project(self, scorer):
        """测试小型数据中心项目（<5千机柜）"""
        content = "项目包含3000个机柜"

        score = scorer.calculate_impact_score("", content)

        assert score == 10

    def test_industry_standard(self, scorer):
        """测试行业标准制定"""
        content = "工信部发布数据中心能效限定值国家标准"

        score = scorer.calculate_impact_score("", content)

        assert score == 20

    def test_major_tech_breakthrough(self, scorer):
        """测试重大技术突破"""
        content = "该技术实现了PUE突破性降低，达到行业领先水平"

        score = scorer.calculate_impact_score("", content)

        assert score == 18

    def test_strategic_cooperation(self, scorer):
        """测试战略合作/并购"""
        content = "两家公司达成战略合作协议"

        score = scorer.calculate_impact_score("", content)

        assert score == 15

    def test_no_impact_indicators(self, scorer):
        """测试无影响指标的内容"""
        content = "公司举办技术交流会"

        score = scorer.calculate_impact_score("", content)

        assert score == 0


class TestCredibilityScoring:
    """测试来源可信度评分（15分）"""

    @pytest.fixture
    def scorer(self):
        return PriorityScorer()

    def test_tier1_source(self, scorer):
        """测试Tier 1媒体（15分）"""
        score = scorer.calculate_credibility_score(tier=1)

        assert score == 15

    def test_tier2_source(self, scorer):
        """测试Tier 2媒体（8分）"""
        score = scorer.calculate_credibility_score(tier=2)

        assert score == 8

    def test_tier3_source(self, scorer):
        """测试Tier 3媒体（3分）"""
        score = scorer.calculate_credibility_score(tier=3)

        assert score == 3

    def test_invalid_tier(self, scorer):
        """测试无效tier值（默认Tier 2）"""
        score = scorer.calculate_credibility_score(tier=99)

        assert score == 8  # 默认Tier 2


class TestTotalScoreCalculation:
    """测试总分计算"""

    @pytest.fixture
    def scorer(self):
        return PriorityScorer()

    def test_calculate_total_score(self, scorer):
        """测试总分计算"""
        title = "某公司完成10亿元融资用于IDC建设"
        content = "某公司宣布完成10亿元C轮融资，资金将用于数据中心基础设施建设"
        publish_date = date.today()
        source_tier = 1

        result = scorer.calculate_total_score(
            title=title,
            content=content,
            publish_date=publish_date,
            source_tier=source_tier,
        )

        # 验证返回结果包含所有字段
        assert "total_score" in result
        assert "relevance_score" in result
        assert "timeliness_score" in result
        assert "impact_score" in result
        assert "credibility_score" in result
        assert "priority" in result

        # 验证总分是4个维度之和
        assert result["total_score"] == (
            result["relevance_score"]
            + result["timeliness_score"]
            + result["impact_score"]
            + result["credibility_score"]
        )

        # 验证总分范围
        assert 0 <= result["total_score"] <= 100

    def test_high_priority_article(self, scorer):
        """测试高优先级文章（≥70分）"""
        # 构造高分文章：核心关键词+当天+大额融资+Tier1媒体
        title = "某公司完成15亿元融资建设AI算力数据中心"
        content = "某公司宣布完成15亿元C轮融资，用于建设大型IDC数据中心和GPU算力中心"
        publish_date = date.today()
        source_tier = 1

        result = scorer.calculate_total_score(title, content, publish_date, source_tier)

        assert result["total_score"] >= 70
        assert result["priority"] == "高"

    def test_medium_priority_article(self, scorer):
        """测试中优先级文章（40-69分）"""
        # 构造中等分数文章：一般关键词+3天前+中等影响+Tier2媒体
        title = "某公司发布新产品"
        content = "某公司发布了新一代云计算产品"
        publish_date = date.today() - timedelta(days=3)
        source_tier = 2

        result = scorer.calculate_total_score(title, content, publish_date, source_tier)

        assert 40 <= result["total_score"] < 70
        assert result["priority"] == "中"

    def test_low_priority_article(self, scorer):
        """测试低优先级文章（<40分）"""
        # 构造低分文章：无关键词+7天前+无影响+Tier3媒体
        title = "某公司举办活动"
        content = "某公司举办了年度员工大会"
        publish_date = date.today() - timedelta(days=7)
        source_tier = 3

        result = scorer.calculate_total_score(title, content, publish_date, source_tier)

        assert result["total_score"] < 40
        assert result["priority"] == "低"


class TestPriorityMapping:
    """测试优先级映射"""

    @pytest.fixture
    def scorer(self):
        return PriorityScorer()

    def test_map_high_priority(self, scorer):
        """测试高优先级映射"""
        assert scorer.map_priority_level(100) == "高"
        assert scorer.map_priority_level(85) == "高"
        assert scorer.map_priority_level(70) == "高"

    def test_map_medium_priority(self, scorer):
        """测试中优先级映射"""
        assert scorer.map_priority_level(69) == "中"
        assert scorer.map_priority_level(55) == "中"
        assert scorer.map_priority_level(40) == "中"

    def test_map_low_priority(self, scorer):
        """测试低优先级映射"""
        assert scorer.map_priority_level(39) == "低"
        assert scorer.map_priority_level(20) == "低"
        assert scorer.map_priority_level(0) == "低"

    def test_boundary_values(self, scorer):
        """测试边界值"""
        assert scorer.map_priority_level(70) == "高"  # 边界：高
        assert scorer.map_priority_level(69) == "中"  # 边界：中
        assert scorer.map_priority_level(40) == "中"  # 边界：中
        assert scorer.map_priority_level(39) == "低"  # 边界：低


class TestEdgeCases:
    """测试边界情况"""

    @pytest.fixture
    def scorer(self):
        return PriorityScorer()

    def test_empty_content(self, scorer):
        """测试空内容"""
        result = scorer.calculate_total_score("", "", date.today(), 2)

        # 只有时效性和可信度得分
        assert result["relevance_score"] == 0
        assert result["timeliness_score"] == 25
        assert result["impact_score"] == 0
        assert result["credibility_score"] == 8
        assert result["total_score"] == 33

    def test_none_values(self, scorer):
        """测试None值"""
        result = scorer.calculate_total_score(None, None, date.today(), 2)

        # 应该能够处理None值
        assert result["relevance_score"] == 0
        assert result["total_score"] >= 0

    def test_very_long_content(self, scorer):
        """测试超长内容"""
        content = "数据中心 " * 1000  # 1000个关键词

        score = scorer.calculate_relevance_score("", content)

        # 应该有上限
        assert score == 40


class TestChineseNumberExtraction:
    """测试中文数字提取"""

    @pytest.fixture
    def scorer(self):
        return PriorityScorer()

    def test_chinese_billions(self, scorer):
        """测试中文"亿"的提取"""
        content1 = "融资10亿元"
        content2 = "融资10亿"
        content3 = "融资金额达到10亿人民币"

        score1 = scorer.calculate_impact_score("", content1)
        score2 = scorer.calculate_impact_score("", content2)
        score3 = scorer.calculate_impact_score("", content3)

        # 都应该识别为10亿
        assert score1 == 20
        assert score2 == 20
        assert score3 == 20

    def test_chinese_ten_thousand(self, scorer):
        """测试中文"万"的提取"""
        content = "投资5000万元"  # 0.5亿

        score = scorer.calculate_impact_score("", content)

        assert score == 5  # <1亿

    def test_mixed_format(self, scorer):
        """测试混合格式"""
        content1 = "1.5亿元融资"
        content2 = "融资1.5亿"

        score1 = scorer.calculate_impact_score("", content1)
        score2 = scorer.calculate_impact_score("", content2)

        assert score1 == 10  # 1-5亿
        assert score2 == 10

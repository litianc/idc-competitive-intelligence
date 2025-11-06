"""
测试内容分类系统

测试4类内容分类：
1. 投资动态
2. 技术进展
3. 政策法规
4. 市场动态
"""

import pytest
from src.classification.category_classifier import CategoryClassifier


class TestCategoryClassifier:
    """测试分类器"""

    @pytest.fixture
    def classifier(self):
        """创建分类器实例"""
        return CategoryClassifier()

    # ========== 分类1：投资动态测试 ==========

    def test_investment_融资(self, classifier):
        """测试融资类关键词"""
        title = "某公司完成10亿元C轮融资"
        content = "本轮融资由知名投资机构领投"

        categories = classifier.classify(title, content)
        assert "投资" in categories

    def test_investment_并购(self, classifier):
        """测试并购类关键词"""
        title = "A公司收购B公司"
        content = "双方达成并购协议，交易金额50亿元"

        categories = classifier.classify(title, content)
        assert "投资" in categories

    def test_investment_IPO(self, classifier):
        """测试IPO类关键词"""
        title = "某公司成功上市"
        content = "公司在纳斯达克挂牌，IPO募资10亿美元"

        categories = classifier.classify(title, content)
        assert "投资" in categories

    def test_investment_估值(self, classifier):
        """测试估值类关键词"""
        title = "某公司估值突破100亿"
        content = "完成新一轮股权融资后，公司估值达到100亿元"

        categories = classifier.classify(title, content)
        assert "投资" in categories

    # ========== 分类2：技术进展测试 ==========

    def test_technology_GPU(self, classifier):
        """测试GPU技术关键词"""
        title = "新一代GPU服务器发布"
        content = "配备最新AI芯片，算力提升10倍"

        categories = classifier.classify(title, content)
        assert "技术" in categories

    def test_technology_液冷(self, classifier):
        """测试液冷技术关键词"""
        title = "数据中心采用液冷技术"
        content = "新型液冷系统显著提升散热效率，PUE降至1.2"

        categories = classifier.classify(title, content)
        assert "技术" in categories

    def test_technology_AI模型(self, classifier):
        """测试AI模型关键词"""
        title = "某公司发布新AI模型"
        content = "模型训练采用最新技术，推理性能大幅提升"

        categories = classifier.classify(title, content)
        assert "技术" in categories

    def test_technology_突破(self, classifier):
        """测试技术突破关键词"""
        title = "国产芯片实现重大突破"
        content = "新一代处理器性能达到国际先进水平，实现技术创新"

        categories = classifier.classify(title, content)
        assert "技术" in categories

    # ========== 分类3：政策法规测试 ==========

    def test_policy_政策(self, classifier):
        """测试政策类关键词"""
        title = "工信部发布数据中心政策"
        content = "新政策旨在规范行业发展，提升能效标准"

        categories = classifier.classify(title, content)
        assert "政策" in categories

    def test_policy_标准(self, classifier):
        """测试标准规范关键词"""
        title = "数据中心国家标准发布"
        content = "新标准对PUE、能耗等指标提出明确要求"

        categories = classifier.classify(title, content)
        assert "政策" in categories

    def test_policy_监管(self, classifier):
        """测试监管类关键词"""
        title = "加强数据中心监管"
        content = "监管部门要求企业获得相关许可和备案"

        categories = classifier.classify(title, content)
        assert "政策" in categories

    def test_policy_规划(self, classifier):
        """测试规划类关键词"""
        title = "发改委发布十四五规划"
        content = "规划指导意见明确数据中心布局方向"

        categories = classifier.classify(title, content)
        assert "政策" in categories

    # ========== 分类4：市场动态测试 ==========

    def test_market_市场份额(self, classifier):
        """测试市场份额关键词"""
        title = "云计算市场格局分析"
        content = "报告显示市场份额排名前三的企业占比达60%"

        categories = classifier.classify(title, content)
        assert "市场" in categories

    def test_market_增长趋势(self, classifier):
        """测试增长趋势关键词"""
        title = "IDC市场持续增长"
        content = "数据显示市场需求旺盛，预测未来三年年均增长20%"

        categories = classifier.classify(title, content)
        assert "市场" in categories

    def test_market_报告(self, classifier):
        """测试市场报告关键词"""
        title = "某机构发布行业研究报告"
        content = "报告分析了市场竞争格局和发展趋势"

        categories = classifier.classify(title, content)
        assert "市场" in categories

    def test_market_价格(self, classifier):
        """测试价格成本关键词"""
        title = "云服务价格调整"
        content = "成本下降推动价格优化，提升利润空间"

        categories = classifier.classify(title, content)
        assert "市场" in categories

    # ========== 多分类测试 ==========

    def test_multiple_categories(self, classifier):
        """测试多分类文章"""
        title = "某公司完成融资并发布新技术"
        content = "公司获得10亿元投资，同时推出新一代GPU技术"

        categories = classifier.classify(title, content)
        assert "投资" in categories
        assert "技术" in categories
        assert len(categories) == 2

    def test_investment_and_policy(self, classifier):
        """测试投资+政策双分类"""
        title = "政府引导基金投资数据中心项目"
        content = "政策支持下，国家基金投资20亿元建设项目"

        categories = classifier.classify(title, content)
        assert "投资" in categories
        assert "政策" in categories

    # ========== 无分类测试 ==========

    def test_no_category(self, classifier):
        """测试无关内容（应归为"其他"）"""
        title = "某公司举办年会"
        content = "公司举办年度员工大会，表彰优秀员工"

        categories = classifier.classify(title, content)
        assert categories == ["其他"]

    def test_empty_content(self, classifier):
        """测试空内容"""
        categories = classifier.classify("", "")
        assert categories == ["其他"]

    # ========== 分类优先级测试 ==========

    def test_category_priority(self, classifier):
        """测试分类优先级：投资 > 技术 > 政策 > 市场"""
        # 包含所有类别关键词
        title = "政府融资支持技术创新，推动市场发展"
        content = """
        政策引导下，某公司获得投资10亿元，
        用于GPU技术研发，预计将改变市场格局
        """

        categories = classifier.classify(title, content)

        # 应该包含所有4个类别
        assert len(categories) == 4
        # 验证顺序：投资 > 技术 > 政策 > 市场
        assert categories[0] == "投资"
        assert categories[1] == "技术"
        assert categories[2] == "政策"
        assert categories[3] == "市场"

    # ========== 边界情况测试 ==========

    def test_none_input(self, classifier):
        """测试None输入"""
        categories = classifier.classify(None, None)
        assert categories == ["其他"]

    def test_very_long_content(self, classifier):
        """测试超长内容"""
        content = "融资 " * 1000  # 1000个关键词
        categories = classifier.classify("", content)
        assert "投资" in categories

    def test_mixed_keywords(self, classifier):
        """测试混合关键词"""
        title = "数据中心建设"
        content = "项目投资5亿"

        categories = classifier.classify(title, content)
        # 只有"投资"关键词明确
        assert "投资" in categories

    # ========== 关键词覆盖率测试 ==========

    def test_all_investment_keywords(self, classifier):
        """测试所有投资关键词"""
        keywords = ["融资", "投资", "并购", "收购", "IPO", "估值", "轮次", 
                   "风投", "PE", "VC", "募资", "资本", "股权", "上市", "挂牌"]

        for keyword in keywords:
            content = f"某公司{keyword}新闻"
            categories = classifier.classify("", content)
            assert "投资" in categories, f"关键词 '{keyword}' 应识别为投资类"

    def test_all_technology_keywords(self, classifier):
        """测试所有技术关键词"""
        keywords = ["GPU", "芯片", "处理器", "算力", "液冷", "风冷", "散热", 
                   "制冷", "新品", "发布", "推出", "上线", "技术", "突破", 
                   "创新", "研发", "AI模型", "训练", "推理", "性能", "效率", "优化"]

        for keyword in keywords:
            content = f"某公司{keyword}新闻"
            categories = classifier.classify("", content)
            assert "技术" in categories, f"关键词 '{keyword}' 应识别为技术类"

    def test_all_policy_keywords(self, classifier):
        """测试所有政策关键词"""
        keywords = ["政策", "法规", "标准", "规范", "监管", "审批", "许可", 
                   "备案", "规划", "指导", "意见", "通知", "国家", "政府", 
                   "工信部", "发改委", "条例", "办法", "细则"]

        for keyword in keywords:
            content = f"{keyword}相关新闻"
            categories = classifier.classify("", content)
            assert "政策" in categories, f"关键词 '{keyword}' 应识别为政策类"

    def test_all_market_keywords(self, classifier):
        """测试所有市场关键词"""
        keywords = ["市场", "份额", "排名", "占比", "增长", "下滑", "趋势", 
                   "预测", "报告", "分析", "研究", "调研", "需求", "供给", 
                   "竞争", "格局", "价格", "成本", "利润"]

        for keyword in keywords:
            content = f"{keyword}相关新闻"
            categories = classifier.classify("", content)
            assert "市场" in categories, f"关键词 '{keyword}' 应识别为市场类"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

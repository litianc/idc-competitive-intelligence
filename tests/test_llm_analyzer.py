"""
LLM文章分析器测试用例

TDD测试驱动开发：先编写测试，再实现功能
"""

import unittest
from unittest.mock import Mock, patch
import json


class TestLLMArticleAnalyzer(unittest.TestCase):
    """LLM文章分析器测试类"""

    def setUp(self):
        """测试前准备"""
        self.api_key = "test_key"
        self.api_base = "http://test.api"
        self.model = "test-model"

    def test_analyze_article_returns_correct_structure(self):
        """测试analyze_article返回正确的数据结构"""
        from src.processing.llm_analyzer import LLMArticleAnalyzer

        analyzer = LLMArticleAnalyzer(self.api_key, self.api_base, self.model)

        # Mock LLM响应
        mock_response = {
            "relevance_score": 18,
            "importance_score": 16,
            "category_score": 9,
            "category": "投资,技术",
            "reason": "涉及50亿元AI算力中心建设",
            "summary": "某公司宣布投资50亿元建设AI算力中心..."
        }

        with patch.object(analyzer, '_call_llm_api', return_value=json.dumps(mock_response)):
            result = analyzer.analyze_article(
                title="某公司投资50亿建设AI算力中心",
                content="详细内容..."
            )

            # 验证返回结构
            self.assertIn('relevance_score', result)
            self.assertIn('importance_score', result)
            self.assertIn('category_score', result)
            self.assertIn('total_score', result)
            self.assertIn('category', result)
            self.assertIn('reason', result)
            self.assertIn('summary', result)

            # 验证数值范围
            self.assertGreaterEqual(result['relevance_score'], 0)
            self.assertLessEqual(result['relevance_score'], 20)
            self.assertGreaterEqual(result['importance_score'], 0)
            self.assertLessEqual(result['importance_score'], 20)
            self.assertGreaterEqual(result['category_score'], 0)
            self.assertLessEqual(result['category_score'], 10)
            self.assertGreaterEqual(result['total_score'], 0)
            self.assertLessEqual(result['total_score'], 50)

    def test_analyze_article_calculates_total_score(self):
        """测试total_score正确计算（相关性+重要性）"""
        from src.processing.llm_analyzer import LLMArticleAnalyzer

        analyzer = LLMArticleAnalyzer(self.api_key, self.api_base, self.model)

        mock_response = {
            "relevance_score": 15,
            "importance_score": 10,
            "category_score": 8,
            "category": "技术",
            "reason": "测试",
            "summary": "测试摘要"
        }

        with patch.object(analyzer, '_call_llm_api', return_value=json.dumps(mock_response)):
            result = analyzer.analyze_article("测试标题", "测试内容")

            # total_score应该是relevance_score + importance_score
            expected_total = 15 + 10
            self.assertEqual(result['total_score'], expected_total)

    def test_analyze_high_relevance_idc_article(self):
        """测试高相关性IDC文章的评分"""
        from src.processing.llm_analyzer import LLMArticleAnalyzer

        analyzer = LLMArticleAnalyzer(self.api_key, self.api_base, self.model)

        # 模拟高相关性文章响应
        mock_response = {
            "relevance_score": 19,
            "importance_score": 18,
            "category_score": 10,
            "category": "投资,技术",
            "reason": "涉及百亿级IDC数据中心投资，配备10万台服务器",
            "summary": "某公司计划投资120亿元在上海建设大型数据中心..."
        }

        with patch.object(analyzer, '_call_llm_api', return_value=json.dumps(mock_response)):
            result = analyzer.analyze_article(
                title="某公司120亿投资建设超大规模数据中心",
                content="该项目包含10万台服务器，采用液冷技术..."
            )

            # 验证高相关性文章的评分
            self.assertGreaterEqual(result['relevance_score'], 18)
            self.assertGreaterEqual(result['total_score'], 35)

    def test_analyze_low_relevance_article(self):
        """测试低相关性文章（如白酒、汽车）的评分"""
        from src.processing.llm_analyzer import LLMArticleAnalyzer

        analyzer = LLMArticleAnalyzer(self.api_key, self.api_base, self.model)

        # 模拟低相关性文章响应
        mock_response = {
            "relevance_score": 2,
            "importance_score": 5,
            "category_score": 3,
            "category": "其他",
            "reason": "属于白酒行业，与IDC无关",
            "summary": "泸州老窖投资建设白酒文化产业园..."
        }

        with patch.object(analyzer, '_call_llm_api', return_value=json.dumps(mock_response)):
            result = analyzer.analyze_article(
                title="泸州老窖投资14亿建设文化产业园",
                content="建设白酒博物馆和文化园区..."
            )

            # 验证低相关性文章的评分
            self.assertLess(result['relevance_score'], 8)  # 应低于采集阈值
            self.assertLess(result['total_score'], 15)

    def test_analyze_handles_llm_json_parsing_error(self):
        """测试LLM返回非JSON时的容错处理"""
        from src.processing.llm_analyzer import LLMArticleAnalyzer

        analyzer = LLMArticleAnalyzer(self.api_key, self.api_base, self.model)

        # Mock返回非JSON格式
        with patch.object(analyzer, '_call_llm_api', return_value="这不是JSON格式"):
            result = analyzer.analyze_article("测试", "测试内容")

            # 应返回默认评分（允许后续人工审核）
            self.assertEqual(result['relevance_score'], 10)
            self.assertEqual(result['importance_score'], 10)
            self.assertIn('解析失败', result['reason'])

    def test_analyze_handles_missing_fields(self):
        """测试LLM返回缺少字段时的容错处理"""
        from src.processing.llm_analyzer import LLMArticleAnalyzer

        analyzer = LLMArticleAnalyzer(self.api_key, self.api_base, self.model)

        # Mock返回不完整的JSON
        mock_response = {
            "relevance_score": 15,
            # 缺少其他字段
        }

        with patch.object(analyzer, '_call_llm_api', return_value=json.dumps(mock_response)):
            result = analyzer.analyze_article("测试", "测试内容")

            # 应有默认值
            self.assertIn('importance_score', result)
            self.assertIn('category', result)
            self.assertIn('summary', result)

    def test_prompt_construction(self):
        """测试Prompt构建是否包含关键要素"""
        from src.processing.llm_analyzer import LLMArticleAnalyzer

        analyzer = LLMArticleAnalyzer(self.api_key, self.api_base, self.model)

        prompt = analyzer._build_prompt("测试标题", "测试内容")

        # 验证Prompt包含关键要素
        self.assertIn("IDC", prompt)
        self.assertIn("数据中心", prompt)
        self.assertIn("相关性", prompt)
        self.assertIn("重要性", prompt)
        self.assertIn("分类", prompt)
        self.assertIn("0-20", prompt)  # 评分范围
        self.assertIn("JSON", prompt)  # 返回格式要求


    def test_multi_category_classification(self):
        """测试多分类支持"""
        from src.processing.llm_analyzer import LLMArticleAnalyzer

        analyzer = LLMArticleAnalyzer(self.api_key, self.api_base, self.model)

        mock_response = {
            "relevance_score": 17,
            "importance_score": 15,
            "category_score": 9,
            "category": "投资,技术,政策",  # 多分类
            "reason": "涉及投资、技术和政策三方面",
            "summary": "测试摘要"
        }

        with patch.object(analyzer, '_call_llm_api', return_value=json.dumps(mock_response)):
            result = analyzer.analyze_article("测试", "测试")

            # 验证支持多分类
            self.assertIn(',', result['category'])
            categories = result['category'].split(',')
            self.assertGreaterEqual(len(categories), 2)


if __name__ == '__main__':
    unittest.main()

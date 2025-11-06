"""
优先级评分引擎

4维度评分模型（总分100分）：
1. 业务相关性（40分）- 基于关键词匹配
2. 时效性（25分）- 基于发布日期衰减
3. 影响范围（20分）- 基于投资额、项目规模等
4. 来源可信度（15分）- 基于媒体源Tier
"""

import re
from datetime import date, timedelta
from typing import Dict, Optional


class PriorityScorer:
    """优先级评分引擎"""

    # 维度1：业务相关性关键词（40分）
    RELEVANCE_KEYWORDS = {
        # 核心关键词（10分/个）
        'core': [
            'IDC', '数据中心', 'AI算力', 'GPU', '算力中心',
            '智算中心', '超算中心'
        ],
        # 重要关键词（5分/个）
        'important': [
            '云计算', '云服务', '服务器', '机柜', '机房',
            '液冷', '制冷', 'PUE', '边缘计算', 'CDN'
        ],
        # 一般关键词（2分/个）
        'general': [
            '算力', '芯片', '处理器', '带宽', '网络',
            '存储', '虚拟化', '容器', '运维'
        ]
    }

    # 维度3：影响范围关键词和阈值
    IMPACT_PATTERNS = {
        # 融资金额（亿元）
        'funding': [
            (10, 20),   # ≥10亿：20分
            (5, 15),    # 5-10亿：15分
            (1, 10),    # 1-5亿：10分
            (0, 5),     # <1亿：5分
        ],
        # 数据中心规模（机柜数）
        'datacenter_scale': [
            (10000, 20),  # ≥1万机柜：20分
            (5000, 15),   # 5千-1万：15分
            (0, 10),      # <5千：10分
        ],
        # 行业影响
        'industry_impact': {
            '标准': 20,
            '国家标准': 20,
            '行业标准': 20,
            '突破': 18,
            '重大突破': 18,
            '技术突破': 18,
            '战略合作': 15,
            '并购': 15,
            '收购': 15,
            '产品发布': 10,
            '新品': 10,
        }
    }

    def calculate_relevance_score(self, title: Optional[str], content: Optional[str]) -> int:
        """
        计算业务相关性评分（40分）

        Args:
            title: 文章标题
            content: 文章内容

        Returns:
            相关性评分（0-40分）
        """
        if not title:
            title = ""
        if not content:
            content = ""

        text = title + " " + content
        score = 0
        found_keywords = set()  # 记录已匹配的关键词，避免重复计分

        # 核心关键词（10分/个，每个只计一次）
        for keyword in self.RELEVANCE_KEYWORDS['core']:
            if keyword in text and keyword not in found_keywords:
                score += 10
                found_keywords.add(keyword)

        # 重要关键词（5分/个，每个只计一次）
        for keyword in self.RELEVANCE_KEYWORDS['important']:
            if keyword in text and keyword not in found_keywords:
                score += 5
                found_keywords.add(keyword)

        # 一般关键词（2分/个，每个只计一次）
        for keyword in self.RELEVANCE_KEYWORDS['general']:
            if keyword in text and keyword not in found_keywords:
                score += 2
                found_keywords.add(keyword)

        # 上限40分
        return min(score, 40)

    def calculate_timeliness_score(self, publish_date: Optional[date]) -> int:
        """
        计算时效性评分（25分）

        使用线性衰减公式：
        - 当天：25分
        - 7天后：0分
        - 衰减公式：25 * (1 - days/7)

        Args:
            publish_date: 发布日期

        Returns:
            时效性评分（0-25分）
        """
        if not publish_date:
            return 0

        today = date.today()

        # 处理未来日期（视为今天）
        if publish_date > today:
            return 25

        days_ago = (today - publish_date).days

        # 7天内线性衰减
        if days_ago >= 7:
            return 0

        score = 25 * (1 - days_ago / 7)
        return int(score)

    def calculate_impact_score(self, title: Optional[str], content: Optional[str]) -> int:
        """
        计算影响范围评分（20分）

        考虑因素：
        1. 融资金额
        2. 数据中心规模
        3. 行业影响（标准、突破、合作等）

        Args:
            title: 文章标题
            content: 文章内容

        Returns:
            影响范围评分（0-20分）
        """
        if not title:
            title = ""
        if not content:
            content = ""

        text = title + " " + content
        max_score = 0

        # 1. 检测融资金额
        funding_score = self._extract_funding_score(text)
        max_score = max(max_score, funding_score)

        # 2. 检测数据中心规模
        datacenter_score = self._extract_datacenter_score(text)
        max_score = max(max_score, datacenter_score)

        # 3. 检测行业影响关键词
        industry_score = self._extract_industry_impact_score(text)
        max_score = max(max_score, industry_score)

        return min(max_score, 20)

    def _extract_funding_score(self, text: str) -> int:
        """提取融资金额并评分"""
        # 匹配模式：数字 + 亿/万
        patterns = [
            r'(\d+\.?\d*)\s*亿',  # X亿
            r'(\d+\.?\d*)\s*万',  # X万
        ]

        amounts = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                amount = float(match)
                # 转换为亿元
                if '万' in pattern:
                    amount = amount / 10000
                amounts.append(amount)

        if not amounts:
            return 0

        # 取最大金额
        max_amount = max(amounts)

        # 根据金额评分
        for threshold, score in self.IMPACT_PATTERNS['funding']:
            if max_amount >= threshold:
                return score

        return 0

    def _extract_datacenter_score(self, text: str) -> int:
        """提取数据中心规模并评分"""
        # 匹配模式：数字 + 机柜（支持"万机柜"、"个机柜"等）
        patterns = [
            r'(\d+\.?\d*)\s*万\s*(?:个)?机柜',  # X万机柜 / X万个机柜
            r'(\d+\.?\d*)\s*(?:个)?机柜',       # X机柜 / X个机柜
        ]

        counts = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                count = float(match)
                # 转换为机柜数
                if '万' in pattern:
                    count = count * 10000
                counts.append(count)

        if not counts:
            return 0

        # 取最大规模
        max_count = max(counts)

        # 根据规模评分
        for threshold, score in self.IMPACT_PATTERNS['datacenter_scale']:
            if max_count >= threshold:
                return score

        return 0

    def _extract_industry_impact_score(self, text: str) -> int:
        """提取行业影响关键词并评分"""
        max_score = 0

        for keyword, score in self.IMPACT_PATTERNS['industry_impact'].items():
            if keyword in text:
                max_score = max(max_score, score)

        return max_score

    def calculate_credibility_score(self, tier: int) -> int:
        """
        计算来源可信度评分（15分）

        Args:
            tier: 媒体源等级（1-3）

        Returns:
            可信度评分
        """
        tier_scores = {
            1: 15,  # Tier 1：权威媒体
            2: 8,   # Tier 2：专业媒体
            3: 3,   # Tier 3：一般媒体
        }

        return tier_scores.get(tier, 8)  # 默认Tier 2

    def calculate_total_score(
        self,
        title: Optional[str],
        content: Optional[str],
        publish_date: Optional[date],
        source_tier: int,
        llm_total_score: Optional[int] = None
    ) -> Dict[str, any]:
        """
        计算总评分（可选整合LLM评分）

        Args:
            title: 文章标题
            content: 文章内容
            publish_date: 发布日期
            source_tier: 媒体源等级
            llm_total_score: LLM总评分（可选，0-50分）

        Returns:
            包含各维度评分和总分的字典
        """
        relevance = self.calculate_relevance_score(title, content)
        timeliness = self.calculate_timeliness_score(publish_date)
        impact = self.calculate_impact_score(title, content)
        credibility = self.calculate_credibility_score(source_tier)

        total = relevance + timeliness + impact + credibility
        priority = self.map_priority_level(total)

        return {
            'relevance_score': relevance,
            'timeliness_score': timeliness,
            'impact_score': impact,
            'credibility_score': credibility,
            'total_score': total,
            'priority': priority
        }

    def map_priority_level(self, total_score: int) -> str:
        """
        映射优先级等级

        Args:
            total_score: 总评分（0-100）

        Returns:
            优先级等级（高/中/低）
        """
        if total_score >= 70:
            return "高"
        elif total_score >= 40:
            return "中"
        else:
            return "低"

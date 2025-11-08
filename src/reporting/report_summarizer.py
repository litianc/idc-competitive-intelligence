"""
周报摘要生成器

使用LLM生成：
1. 周报整体总结（100-200字）
2. 各板块点评（30-50字）
"""

import requests
import json
import logging
import random
import os
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# 板块点评标题词库
SECTION_INSIGHT_LABELS = {
    '政策法规': [
        '政策导向', '监管动态', '政策解读', '合规要点',
        '政策风向', '政策红利', '政策信号', '顶层设计'
    ],
    '投资动态': [
        '投资热点', '资本动向', '投资机会', '市场机遇',
        '资金流向', '投资风向', '项目观察', '投资建议'
    ],
    '技术进展': [
        '技术趋势', '创新亮点', '技术突破', '研发动态',
        '技术前沿', '创新观察', '技术方向', '研发洞察'
    ],
    '市场动态': [
        '市场观察', '竞争格局', '市场信号', '行业脉搏',
        '市场趋势', '需求洞察', '商业机会', '市场风向'
    ],
    '其他动态': [
        '行业动态', '综合观察', '生态观察', '行业信号',
        '补充洞察', '延伸思考', '行业脉动', '综合分析'
    ]
}


# 点评标题图标映射
INSIGHT_ICONS = {
    # 政策类
    '政策导向': '📋', '监管动态': '⚖️', '政策解读': '📜',
    '合规要点': '✅', '政策风向': '🧭', '政策红利': '🎁',
    '政策信号': '📡', '顶层设计': '🏛️',

    # 投资类
    '投资热点': '🔥', '资本动向': '💰', '投资机会': '💎',
    '市场机遇': '🎯', '资金流向': '💵', '投资风向': '📈',
    '项目观察': '🔍', '投资建议': '💡',

    # 技术类
    '技术趋势': '🚀', '创新亮点': '✨', '技术突破': '⚡',
    '研发动态': '🔬', '技术前沿': '🌟', '创新观察': '👁️',
    '技术方向': '🧭', '研发洞察': '💡',

    # 市场类
    '市场观察': '👁️', '竞争格局': '♟️', '市场信号': '📊',
    '行业脉搏': '💓', '市场趋势': '📈', '需求洞察': '🔍',
    '商业机会': '💼', '市场风向': '🧭',

    # 其他类
    '行业动态': '📢', '综合观察': '🔭', '生态观察': '🌐',
    '行业信号': '📡', '补充洞察': '💡', '延伸思考': '🤔',
    '行业脉动': '💓', '综合分析': '📊'
}


def get_random_insight_label(section_name: str, use_random: bool = True) -> str:
    """
    为板块随机选择一个点评标题

    Args:
        section_name: 板块名称
        use_random: 是否使用随机标题（False则返回默认"趋势洞察"）

    Returns:
        点评标题文字
    """
    if not use_random:
        return '趋势洞察'

    labels = SECTION_INSIGHT_LABELS.get(section_name, ['趋势洞察'])
    return random.choice(labels)


def get_insight_icon(label: str) -> str:
    """
    获取点评标题对应的图标

    Args:
        label: 点评标题

    Returns:
        图标字符
    """
    return INSIGHT_ICONS.get(label, '💡')


class WeeklyReportSummarizer:
    """周报摘要生成器"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        model: Optional[str] = None
    ):
        """
        初始化摘要生成器

        Args:
            api_key: LLM API密钥（默认从环境变量读取）
            api_base: LLM API地址（默认从环境变量读取）
            model: LLM模型名称（默认从环境变量读取）
        """
        self.api_key = api_key or os.getenv('LLM_API_KEY') or os.getenv('OPENAI_API_KEY')
        self.api_base = api_base or os.getenv('LLM_API_BASE') or 'https://api.openai.com'
        self.model = model or os.getenv('LLM_MODEL') or os.getenv('OPENAI_MODEL') or 'gpt-4-turbo-preview'
        self.timeout = 30

        if not self.api_key:
            logger.warning("未配置LLM API密钥，摘要生成功能将不可用")

    def generate_insights(
        self,
        articles: List[Dict],
        by_category: Dict[str, List[Dict]]
    ) -> Dict:
        """
        生成周报整体总结和各板块点评

        Args:
            articles: 所有文章列表
            by_category: 按分类分组的文章

        Returns:
            {
                'executive_summary': '整体总结文字',
                'section_insights': {
                    '政策法规': '板块点评',
                    '投资动态': '板块点评',
                    ...
                }
            }
        """
        if not self.api_key:
            logger.warning("LLM API未配置，返回默认摘要")
            return self._get_default_insights(articles, by_category)

        try:
            # 构建prompt
            prompt = self._build_prompt(articles, by_category)

            # 调用LLM API
            response_text = self._call_llm_api(prompt)

            # 解析结果
            insights = self._parse_response(response_text)

            logger.info(f"✓ 周报摘要生成成功，包含{len(insights.get('section_insights', {}))}个板块点评")

            return insights

        except Exception as e:
            logger.error(f"✗ 周报摘要生成失败: {e}")
            return self._get_default_insights(articles, by_category)

    def _build_prompt(self, articles: List[Dict], by_category: Dict) -> str:
        """构建LLM prompt"""

        # 统计信息
        total_count = len(articles)
        high_priority_count = len([a for a in articles if a.get('priority') == '高'])

        # 按分类汇总文章信息
        category_summary = []
        for category in ['政策法规', '投资动态', '技术进展', '市场动态', '其他动态']:
            # 获取该分类的文章
            category_articles = []
            for cat_key, cat_articles in by_category.items():
                # 检查 cat_key 是否为 None
                if cat_key and category.replace('法规', '').replace('动态', '').replace('进展', '') in str(cat_key):
                    category_articles.extend(cat_articles)

            if not category_articles:
                continue

            # 选择该分类的高优先级文章（最多3篇）
            high_priority = [a for a in category_articles if a.get('priority') == '高'][:3]
            if not high_priority:
                high_priority = sorted(category_articles, key=lambda x: x.get('score', 0), reverse=True)[:2]

            articles_text = []
            for article in high_priority:
                articles_text.append(
                    f"  - {article['title']} (评分:{article.get('score', 0)}, {article.get('source', '')})"
                )

            category_summary.append(
                f"{category}（{len(category_articles)}篇）:\n" + "\n".join(articles_text)
            )

        category_text = "\n\n".join(category_summary)

        prompt = f"""你是IDC行业竞争情报分析专家。请基于本周收集的文章，生成周报总结和板块点评。

【本周统计】
- 总文章数: {total_count}篇
- 高优先级: {high_priority_count}篇

【分类文章概览】
{category_text}

【任务要求】
1. executive_summary（整体总结）
   - 字数: 100-200字
   - 内容: 概括本周IDC行业的核心动态，包括政策、投资、技术、市场等方面的重点
   - 突出: 关键数据（投资金额、项目规模、技术指标）和重要趋势
   - 风格: 专业、简洁、有洞察力
   - 格式: 可使用"一是...二是...三是..."或"本周呈现X大特点..."等结构

2. section_insights（板块点评）
   - 为每个有文章的板块生成一句话点评
   - 字数: 30-50字
   - 内容: 点出该板块的核心趋势、关键发现或重要建议
   - 风格: 精炼、观点明确、有指导性
   - 只为有文章的板块生成点评，没有文章的板块不输出

【返回格式】
严格返回JSON格式（不要用markdown代码块包裹）：
{{
  "executive_summary": "本周IDC行业呈现三大亮点：一是政策层面...",
  "section_insights": {{
    "政策法规": "国家级算力政策密集出台，地方配套措施加速落地",
    "投资动态": "百亿级项目频现，AI算力中心成投资热点",
    "技术进展": "液冷技术取得突破，能效比提升显著"
  }}
}}

注意：
1. 只返回纯JSON，不要添加任何markdown格式
2. 只为实际有文章的板块生成点评
3. 点评要具体、有价值，避免空话套话
"""

        return prompt

    def _call_llm_api(self, prompt: str) -> str:
        """
        调用LLM API

        Args:
            prompt: 提示词

        Returns:
            API返回的文本内容
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,  # 降低随机性
            "max_tokens": 600
        }

        try:
            response = requests.post(
                f"{self.api_base}/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.timeout
            )

            response.raise_for_status()

            result = response.json()
            content = result['choices'][0]['message']['content']

            return content.strip()

        except requests.exceptions.Timeout:
            logger.error(f"LLM API调用超时（{self.timeout}秒）")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"LLM API调用失败: {e}")
            raise

    def _parse_response(self, response_text: str) -> Dict:
        """
        解析LLM返回的JSON

        Args:
            response_text: LLM返回的文本

        Returns:
            解析后的字典
        """
        try:
            # 清理可能的markdown代码块
            cleaned_text = response_text.strip()
            if cleaned_text.startswith('```json'):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith('```'):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith('```'):
                cleaned_text = cleaned_text[:-3]
            cleaned_text = cleaned_text.strip()

            # 解析JSON
            data = json.loads(cleaned_text)

            # 验证字段
            executive_summary = data.get('executive_summary', '')
            section_insights = data.get('section_insights', {})

            if not executive_summary:
                logger.warning("LLM未返回整体总结，使用默认值")
                executive_summary = "本周IDC行业动态丰富，详见各板块内容。"

            if not isinstance(section_insights, dict):
                logger.warning("LLM返回的板块点评格式不正确")
                section_insights = {}

            return {
                'executive_summary': executive_summary,
                'section_insights': section_insights
            }

        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e} | 返回内容: {response_text[:200]}")
            raise
        except Exception as e:
            logger.error(f"结果解析异常: {e}")
            raise

    def _get_default_insights(self, articles: List[Dict], by_category: Dict) -> Dict:
        """
        获取默认摘要（LLM不可用时的降级方案）

        Args:
            articles: 文章列表
            by_category: 按分类分组的文章

        Returns:
            默认摘要字典
        """
        total_count = len(articles)
        high_count = len([a for a in articles if a.get('priority') == '高'])
        medium_count = len([a for a in articles if a.get('priority') == '中'])

        # 生成简单的统计型总结
        executive_summary = f"本周共收录{total_count}篇IDC行业相关文章，其中高优先级{high_count}篇，中优先级{medium_count}篇。内容涵盖政策法规、投资动态、技术进展、市场动态等多个领域，详见各板块详细内容。"

        # 为每个板块生成简单点评
        section_insights = {}

        # 检查各个分类
        for category_key, articles_list in by_category.items():
            if not articles_list or not category_key:
                continue

            count = len(articles_list)

            # 根据分类关键字确定板块名称
            if '政策' in str(category_key):
                section_insights['政策法规'] = f"本周政策领域收录{count}篇文章，涉及行业规范与政策导向"
            elif '投资' in str(category_key):
                section_insights['投资动态'] = f"本周投资领域收录{count}篇文章，关注资金流向与项目布局"
            elif '技术' in str(category_key):
                section_insights['技术进展'] = f"本周技术领域收录{count}篇文章，聚焦创新突破与应用实践"
            elif '市场' in str(category_key):
                section_insights['市场动态'] = f"本周市场领域收录{count}篇文章，追踪行业趋势与竞争态势"

        return {
            'executive_summary': executive_summary,
            'section_insights': section_insights
        }

    @classmethod
    def from_env(cls) -> 'WeeklyReportSummarizer':
        """
        从环境变量创建实例（工厂方法）

        Returns:
            WeeklyReportSummarizer实例
        """
        return cls()

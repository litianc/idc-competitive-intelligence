"""
LLM文章智能分析器

整合相关性判断、重要性评分、分类建议和摘要生成为单次API调用
"""

import requests
import json
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class LLMArticleAnalyzer:
    """
    LLM文章智能分析器

    单次API调用完成：
    1. 相关性评分 (0-20分) - 判断是否属于IDC/数据中心/云计算/AI算力领域
    2. 重要性评分 (0-20分) - 评估新闻价值
    3. 分类建议 (0-10分) - 给出分类标签和置信度
    4. 内容摘要 (80-150字) - 生成专业摘要
    """

    def __init__(self, api_key: str, api_base: str, model: str = "GLM-4.5-Air"):
        """
        初始化LLM分析器

        Args:
            api_key: API密钥
            api_base: API基础URL
            model: 使用的模型名称
        """
        self.api_key = api_key
        self.api_base = api_base
        self.model = model
        self.timeout = 30  # API调用超时时间（秒）

    def analyze_article(self, title: str, content: str) -> Dict:
        """
        分析文章并返回完整评分和摘要

        Args:
            title: 文章标题
            content: 文章内容（可以是摘要或正文前500字）

        Returns:
            {
                'relevance_score': int,      # 0-20分
                'importance_score': int,     # 0-20分
                'category_score': int,       # 0-10分
                'total_score': int,          # 0-50分
                'category': str,             # "投资,技术" 或 "政策"
                'reason': str,               # 50字内判断理由
                'summary': str               # 80-150字摘要
            }
        """
        try:
            # 构建Prompt
            prompt = self._build_prompt(title, content)

            # 调用LLM API
            response_text = self._call_llm_api(prompt)

            # 解析返回结果
            result = self._parse_response(response_text, title, content)

            logger.info(f"文章分析完成: {title[:30]}... | 相关性:{result['relevance_score']} 重要性:{result['importance_score']} 总分:{result['total_score']}")

            return result

        except Exception as e:
            logger.error(f"文章分析失败: {title[:30]}... | 错误: {e}")
            # 返回默认评分，允许后续处理
            return self._get_default_result(title, content, str(e))

    def _build_prompt(self, title: str, content: str) -> str:
        """构建分析Prompt"""
        # 截取内容前800字（避免超长内容）
        content_preview = content[:800] if len(content) > 800 else content

        prompt = f"""你是IDC行业竞争情报分析专家。请全面分析以下文章。

【文章信息】
标题：{title}
内容：{content_preview}

【分析任务】
1. 相关性评分（0-20分）
   - 18-20分：核心业务（IDC建设、数据中心投资、算力中心、GPU集采、液冷技术、PUE优化、机柜部署）
   - 12-17分：直接相关（云计算平台、服务器采购、边缘计算节点、CDN网络、数据中心选址）
   - 6-11分：间接相关（芯片供应、网络设备、存储技术、电力供应、制冷设备）
   - 0-5分：不相关（其他行业如白酒、汽车、房地产、娱乐、消费品、金融理财）

2. 重要性评分（0-20分）
   - 考虑因素：投资规模、技术突破、政策影响力、行业地位
   - 18-20分：重大事件（≥100亿投资、国家级政策、重大技术突破）
   - 12-17分：重要事件（10-100亿投资、省级政策、行业标准、重要合作）
   - 6-11分：一般事件（1-10亿投资、企业动态、技术进展）
   - 0-5分：参考信息（百万级项目、一般新闻）

3. 分类建议（置信度0-10分）
   - 主分类：投资、技术、政策、市场
   - 可多选（用逗号分隔，如"投资,技术"）
   - 置信度：对分类把握的确定程度（10=非常确定，5=一般，0=无法判断）

4. 判断理由
   - 50字内说明评分依据（如"涉及50亿IDC投资，属核心业务"）

5. 内容摘要
   - 80-150字中文摘要
   - 突出核心信息：金额、规模、技术要点、政策影响
   - 使用专业术语（如GPU、液冷、PUE、算力、云服务）

【返回格式】严格JSON（不要markdown代码块，直接返回JSON）：
{{
  "relevance_score": 18,
  "importance_score": 16,
  "category_score": 9,
  "category": "投资,技术",
  "reason": "涉及50亿元AI算力中心建设，包含1万个GPU机柜",
  "summary": "某公司宣布投资50亿元..."
}}"""

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
            "temperature": 0.3,  # 降低随机性，提高稳定性
            "max_tokens": 500
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

    def _parse_response(self, response_text: str, title: str, content: str) -> Dict:
        """
        解析LLM返回结果

        Args:
            response_text: LLM返回的文本
            title: 文章标题（用于容错）
            content: 文章内容（用于容错）

        Returns:
            标准化的分析结果
        """
        try:
            # 尝试清理可能的markdown代码块
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

            # 提取并验证字段
            relevance_score = self._validate_score(data.get('relevance_score', 10), 0, 20)
            importance_score = self._validate_score(data.get('importance_score', 10), 0, 20)
            category_score = self._validate_score(data.get('category_score', 5), 0, 10)

            # 计算总分
            total_score = relevance_score + importance_score

            # 获取分类（默认"其他"）
            category = data.get('category', '其他')
            if not category or category.strip() == '':
                category = '其他'

            # 获取理由
            reason = data.get('reason', '')[:100]  # 限制100字

            # 获取摘要
            summary = data.get('summary', '')
            if not summary or len(summary) < 20:
                # 摘要太短或为空，使用标题作为摘要
                summary = title if len(title) <= 150 else title[:147] + "..."

            return {
                'relevance_score': relevance_score,
                'importance_score': importance_score,
                'category_score': category_score,
                'total_score': total_score,
                'category': category,
                'reason': reason,
                'summary': summary
            }

        except json.JSONDecodeError as e:
            logger.warning(f"JSON解析失败: {e} | 返回内容: {response_text[:200]}")
            return self._get_default_result(title, content, "JSON解析失败")

        except Exception as e:
            logger.warning(f"结果解析异常: {e}")
            return self._get_default_result(title, content, f"解析异常: {e}")

    def _validate_score(self, score: any, min_val: int, max_val: int) -> int:
        """
        验证并修正评分范围

        Args:
            score: 原始评分
            min_val: 最小值
            max_val: 最大值

        Returns:
            修正后的评分
        """
        try:
            score_int = int(score)
            if score_int < min_val:
                return min_val
            if score_int > max_val:
                return max_val
            return score_int
        except (ValueError, TypeError):
            # 无法转换为整数，返回中间值
            return (min_val + max_val) // 2

    def _get_default_result(self, title: str, content: str, error_msg: str) -> Dict:
        """
        获取默认结果（用于容错）

        Args:
            title: 文章标题
            content: 文章内容
            error_msg: 错误信息

        Returns:
            默认评分结果
        """
        return {
            'relevance_score': 10,  # 默认中等相关性（允许后续人工审核）
            'importance_score': 10,
            'category_score': 5,
            'total_score': 20,
            'category': '其他',
            'reason': f'LLM分析{error_msg[:30]}，使用默认评分',
            'summary': title if len(title) <= 150 else title[:147] + "..."
        }

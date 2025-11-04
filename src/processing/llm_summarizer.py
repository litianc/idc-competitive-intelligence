"""
LLM摘要生成器

支持多种LLM提供商生成文章摘要
"""

import os
import logging
import requests
import time
from typing import Optional, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class LLMSummarizer:
    """LLM摘要生成器"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        model: str = "gpt-3.5-turbo",
        provider: str = "openai",
    ):
        """
        初始化LLM摘要生成器

        Args:
            api_key: API密钥
            api_base: API基础URL（可选，用于自定义端点）
            model: 模型名称
            provider: 提供商（openai/anthropic/custom）
        """
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.api_base = api_base or os.getenv("LLM_API_BASE")
        self.model = model or os.getenv("LLM_MODEL", "gpt-3.5-turbo")
        self.provider = provider

        if not self.api_key:
            raise ValueError("API密钥未设置")

        logger.info(f"初始化LLM摘要生成器: {self.model} @ {self.api_base or '默认端点'}")

    def generate_summary(
        self,
        title: str,
        content: str,
        max_retries: int = 3,
        retry_delay: int = 2,
    ) -> Optional[str]:
        """
        生成文章摘要

        Args:
            title: 文章标题
            content: 文章内容
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）

        Returns:
            生成的摘要，失败返回None
        """
        # 如果内容为空，只使用标题
        text = content if content else title

        # 构建prompt
        prompt = f"""请为以下IDC/数据中心行业文章生成一个80-150字的中文摘要。

要求：
1. 突出核心信息和业务价值
2. 使用专业术语
3. 简洁明了
4. 不要包含"这篇文章"、"本文"等元信息

文章标题：{title}
文章内容：{text[:2000]}

摘要："""

        # 重试机制
        for attempt in range(max_retries):
            try:
                summary = self._call_api(prompt)
                if summary:
                    # 清理摘要
                    summary = self._clean_summary(summary)

                    # 验证摘要长度
                    if 60 <= len(summary) <= 200:
                        logger.info(f"成功生成摘要 (长度: {len(summary)}字)")
                        return summary
                    else:
                        logger.warning(f"摘要长度不符合要求: {len(summary)}字")
                        if attempt == max_retries - 1:
                            return summary  # 最后一次尝试时返回

            except Exception as e:
                logger.error(f"生成摘要失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)

        return None

    def _call_api(self, prompt: str) -> Optional[str]:
        """
        调用LLM API

        Args:
            prompt: 提示词

        Returns:
            API响应文本
        """
        # 使用OpenAI兼容的API格式
        url = f"{self.api_base}/v1/chat/completions" if self.api_base else "https://api.openai.com/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的IDC/数据中心行业分析师，擅长撰写简洁专业的行业资讯摘要。",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 300,
        }

        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30,
            )

            response.raise_for_status()
            result = response.json()

            # 提取响应内容
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                return content.strip()
            else:
                logger.error(f"API响应格式异常: {result}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"API调用失败: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"响应内容: {e.response.text}")
            raise

    def _clean_summary(self, summary: str) -> str:
        """
        清理摘要文本

        Args:
            summary: 原始摘要

        Returns:
            清理后的摘要
        """
        # 移除常见的元信息前缀
        prefixes_to_remove = [
            "摘要：",
            "概要：",
            "本文",
            "这篇文章",
            "文章",
            "该文",
        ]

        for prefix in prefixes_to_remove:
            if summary.startswith(prefix):
                summary = summary[len(prefix):].strip()

        # 移除前导冒号
        summary = summary.lstrip("：:").strip()

        # 移除多余空格
        summary = " ".join(summary.split())

        return summary

    def batch_generate_summaries(
        self,
        articles: list[Dict],
        delay: float = 1.0,
    ) -> Dict[int, str]:
        """
        批量生成摘要

        Args:
            articles: 文章列表，每个文章包含id, title, content字段
            delay: 每次请求之间的延迟（秒）

        Returns:
            文章ID到摘要的映射
        """
        summaries = {}
        total = len(articles)

        logger.info(f"开始批量生成摘要: {total}篇文章")

        for i, article in enumerate(articles, 1):
            article_id = article.get("id")
            title = article.get("title", "")
            content = article.get("content", "")

            logger.info(f"处理 {i}/{total}: {title[:30]}...")

            try:
                summary = self.generate_summary(title, content)
                if summary:
                    summaries[article_id] = summary
                    logger.info(f"  ✅ 成功生成摘要")
                else:
                    logger.warning(f"  ⚠️ 摘要生成失败")

                # 延迟避免频繁请求
                if i < total:
                    time.sleep(delay)

            except Exception as e:
                logger.error(f"  ❌ 处理失败: {e}")
                continue

        logger.info(f"批量生成完成: {len(summaries)}/{total} 篇成功")
        return summaries


def main():
    """测试LLM摘要生成"""
    # 示例配置
    api_key = "your_api_key"
    api_base = "http://your-api-endpoint"
    model = "gpt-3.5-turbo"

    summarizer = LLMSummarizer(
        api_key=api_key,
        api_base=api_base,
        model=model,
    )

    # 测试文章
    title = "投资26.2亿元，孝感大数据产业园一期项目开工"
    content = """
    10月28日，孝感大数据产业园项目开工。项目总投资26.2亿元，
    占地约300亩，建设内容包括数据中心机房、配套设施等。
    项目建成后将成为湖北省重要的数据中心节点。
    """

    summary = summarizer.generate_summary(title, content)
    print(f"生成的摘要: {summary}")


if __name__ == "__main__":
    main()

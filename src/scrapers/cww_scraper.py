"""
通信世界网自定义爬虫
采集算力、人工智能、大数据三个板块
"""

from datetime import date
from typing import List, Dict
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from urllib.parse import urljoin
import logging
import re

logger = logging.getLogger(__name__)


class CwwScraper:
    """
    通信世界网爬虫

    采集多个板块：算力、人工智能、大数据
    """

    def __init__(self):
        self.name = "通信世界网"
        self.base_url = "https://www.cww.net.cn"
        self.tier = 2

        # 三个板块的URL
        self.section_urls = [
            ("算力", "https://www.cww.net.cn/subjects/nav/rollList/8102"),
            ("人工智能", "https://www.cww.net.cn/subjects/nav/rollList/3009"),
            ("大数据", "https://www.cww.net.cn/subjects/nav/rollList/3008"),
        ]

        # 选择器配置
        self.article_container = "div.pindao.mt0 li"
        self.title_selector = "a"
        self.link_selector = "a"
        self.date_selector = "span.textgray.fr"

    def fetch_articles(self, limit: int = 20) -> List[Dict]:
        """
        从三个板块采集文章

        Args:
            limit: 每个板块最多采集的文章数

        Returns:
            文章列表
        """
        all_articles = []

        for section_name, section_url in self.section_urls:
            try:
                logger.info(f"开始采集板块: {section_name}")
                articles = self._fetch_section(section_url, section_name, limit)
                all_articles.extend(articles)
                logger.info(f"板块 {section_name} 采集到 {len(articles)} 篇文章")
            except Exception as e:
                logger.error(f"采集板块 {section_name} 失败: {e}")
                continue

        return all_articles

    def _fetch_section(self, url: str, section_name: str, limit: int) -> List[Dict]:
        """
        采集单个板块

        Args:
            url: 板块URL
            section_name: 板块名称
            limit: 最多采集数量

        Returns:
            文章列表
        """
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(ignore_https_errors=True)

                page.set_extra_http_headers({
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                })

                # 访问页面
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(2000)

                # 获取HTML
                html_content = page.content()
                browser.close()

                # 解析文章
                articles = self._parse_articles(html_content, url, section_name)
                return articles[:limit]

        except Exception as e:
            logger.error(f"获取板块 {section_name} 页面失败: {e}")
            return []

    def _parse_articles(self, html: str, page_url: str, section_name: str) -> List[Dict]:
        """
        解析HTML获取文章列表

        Args:
            html: HTML内容
            page_url: 页面URL
            section_name: 板块名称

        Returns:
            文章列表
        """
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        articles = []

        # 查找文章容器
        containers = soup.select(self.article_container)

        for container in containers:
            try:
                article = self._extract_article_data(container, page_url, section_name)

                if self._is_valid_article(article):
                    articles.append(article)

            except Exception as e:
                logger.warning(f"解析文章失败: {e}")
                continue

        return articles

    def _extract_article_data(self, container, page_url: str, section_name: str) -> Dict:
        """
        从容器中提取文章数据

        Args:
            container: BeautifulSoup元素
            page_url: 页面URL
            section_name: 板块名称

        Returns:
            文章数据字典
        """
        # 提取标题和链接
        link_elem = container.select_one(self.link_selector)

        if not link_elem:
            return {}

        title = link_elem.text.strip()
        url = link_elem.get("href", "").strip()

        # 转换相对URL为绝对URL
        if url:
            url = urljoin(page_url, url)

        # 提取日期
        publish_date = None
        date_elem = container.select_one(self.date_selector)

        if date_elem:
            date_str = date_elem.text.strip()
            publish_date = self._parse_date(date_str)

        return {
            "title": title,
            "url": url,
            "publish_date": publish_date,
            "summary": f"来自{section_name}板块",
            "source": self.name,
            "source_tier": self.tier,
        }

    def _parse_date(self, date_str: str) -> date:
        """
        解析日期字符串

        Args:
            date_str: 日期字符串（格式：MM-DD）

        Returns:
            date对象
        """
        if not date_str:
            return None

        try:
            # 移除所有空白字符
            date_str_clean = re.sub(r'\s+', '', date_str)

            # 匹配 MM-DD 格式
            match = re.match(r'(\d{1,2})-(\d{1,2})$', date_str_clean)

            if match:
                month, day = match.groups()
                current_year = date.today().year

                try:
                    return date(current_year, int(month), int(day))
                except ValueError:
                    # 无效日期
                    logger.warning(f"无效日期: {date_str}")
                    return None

        except Exception as e:
            logger.warning(f"解析日期失败: {date_str}, 错误: {e}")

        return None

    def _is_valid_article(self, article: Dict) -> bool:
        """
        验证文章是否有效

        Args:
            article: 文章字典

        Returns:
            是否有效
        """
        # 必须有标题、URL和日期
        if not article.get("title"):
            return False

        if not article.get("url"):
            return False

        if not article.get("publish_date"):
            return False

        return True

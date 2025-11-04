"""
Scraper for idcquan.com (中国IDC圈)

This scraper extracts articles from the IDC news website using playwright
to handle dynamic content and BeautifulSoup for HTML parsing.
"""

from datetime import datetime, date
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import logging

logger = logging.getLogger(__name__)


class IdcquanScraper:
    """Scraper for idcquan.com news articles"""

    def __init__(self):
        """Initialize scraper with configuration"""
        self.base_url = "https://news.idcquan.com/"
        self.source_name = "中国IDC圈"

    def fetch_articles(self, limit: int = 20) -> List[Dict]:
        """
        Fetch articles from idcquan.com

        Args:
            limit: Maximum number of articles to fetch

        Returns:
            List of article dictionaries with title, url, publish_date, summary
        """
        try:
            with sync_playwright() as p:
                # Launch browser
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                # Set user agent to avoid blocking
                page.set_extra_http_headers(
                    {
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    }
                )

                # Navigate to news page
                page.goto(self.base_url, wait_until="domcontentloaded", timeout=30000)

                # Wait for content to load
                page.wait_for_timeout(2000)

                # Get HTML content
                html_content = page.content()

                # Close browser
                browser.close()

                # Parse articles from HTML
                articles = self.parse_articles(html_content)

                # Apply limit
                return articles[:limit]

        except Exception as e:
            logger.error(f"Error fetching articles from idcquan.com: {e}")
            return []

    def parse_articles(self, html: str) -> List[Dict]:
        """
        Parse articles from HTML content

        Args:
            html: HTML content as string

        Returns:
            List of article dictionaries
        """
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")

        # Find all article containers
        article_containers = soup.select("div.news.clearfix")

        articles = []

        for container in article_containers:
            try:
                # Extract article data
                article = self._extract_article_data(container)

                # Validate article
                if self._is_valid_article(article):
                    articles.append(article)

            except Exception as e:
                logger.warning(f"Error parsing article: {e}")
                continue

        return articles

    def _extract_article_data(self, container) -> Dict:
        """
        Extract article data from a container element

        Args:
            container: BeautifulSoup element containing article

        Returns:
            Dictionary with article data
        """
        # Extract date
        date_elem = container.select_one("span.date")
        date_str = date_elem.text.strip() if date_elem else ""
        publish_date = self._parse_date(date_str)

        # Extract title from news_nr section
        title_elem = container.select_one("div.news_nr span.title")
        title = title_elem.text.strip() if title_elem else ""

        # Extract URL from bdurl link or news_nr link
        url_elem = container.select_one("a.bdurl") or container.select_one(
            "div.news_nr a.d1"
        )
        url = url_elem.get("href", "").strip() if url_elem else ""

        # Extract summary from news_nr section
        summary_elem = container.select_one("div.news_nr div.d2 span.nei_rong")
        summary = summary_elem.text.strip() if summary_elem else ""

        return {
            "title": title,
            "url": url,
            "publish_date": publish_date,
            "summary": summary,
            "source": self.source_name,
        }

    def _parse_date(self, date_str: str) -> Optional[date]:
        """
        Parse date string to date object

        Args:
            date_str: Date string (format: "2025-11-03 18:02:21" or "2025-11-03")

        Returns:
            date object or None if parsing fails
        """
        if not date_str:
            return None

        try:
            # Try parsing with time
            if " " in date_str:
                dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                return dt.date()

            # Try parsing without time
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.date()

        except ValueError:
            logger.warning(f"Failed to parse date: {date_str}")
            return None

    def _is_valid_article(self, article: Dict) -> bool:
        """
        Validate article has required fields

        Args:
            article: Article dictionary

        Returns:
            True if article is valid, False otherwise
        """
        # Check required fields
        if not article.get("title"):
            return False

        if not article.get("url"):
            return False

        if not article.get("publish_date"):
            return False

        return True

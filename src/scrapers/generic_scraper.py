"""
Generic scraper that works with configuration

This scraper can handle multiple websites by reading CSS selectors
from configuration files, eliminating the need to write separate
scraper classes for each website.
"""

from datetime import datetime, date
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import logging
import re
import json

logger = logging.getLogger(__name__)


class GenericScraper:
    """
    Configuration-driven generic scraper

    Can scrape any website by providing CSS selectors in config.
    """

    def __init__(self, config: Dict):
        """
        Initialize scraper with configuration

        Args:
            config: Dictionary containing scraper configuration
                {
                    "name": "Media Name",
                    "url": "https://example.com",
                    "tier": 1,
                    "scraper_config": {
                        "list_url": "https://example.com/news/",
                        "article_container": "div.article",  # Container for each article
                        "title_selector": "h2 a",
                        "link_selector": "h2 a",
                        "date_selector": ".date",
                        "summary_selector": ".summary",  # Optional
                        "date_format": "%Y-%m-%d",
                        ...
                    }
                }
        """
        self.name = config.get("name", "Unknown")
        self.base_url = config.get("url", "")
        self.tier = config.get("tier", 2)

        # Scraper configuration
        scraper_config = config.get("scraper_config", {})
        self.list_url = scraper_config.get("list_url", self.base_url)
        self.article_container = scraper_config.get("article_container")
        self.title_selector = scraper_config.get("title_selector")
        self.link_selector = scraper_config.get("link_selector")
        self.date_selector = scraper_config.get("date_selector")
        self.summary_selector = scraper_config.get("summary_selector")
        self.date_format = scraper_config.get("date_format", "%Y-%m-%d")
        self.encoding = scraper_config.get("encoding", "utf-8")

    @classmethod
    def from_config_file(cls, config_path: str, source_name: str):
        """
        Create scraper from config file

        Args:
            config_path: Path to media-sources.json
            source_name: Name of the source to use

        Returns:
            GenericScraper instance
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        # Find source by name
        for source in config_data.get("sources", []):
            if source.get("name") == source_name:
                return cls(source)

        raise ValueError(f"Source '{source_name}' not found in config")

    def fetch_articles(self, limit: int = 20) -> List[Dict]:
        """
        Fetch articles from website

        Args:
            limit: Maximum number of articles to fetch

        Returns:
            List of article dictionaries
        """
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                # Create page with SSL errors ignored
                page = browser.new_page(ignore_https_errors=True)

                page.set_extra_http_headers({
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                })

                # Navigate to list page
                page.goto(self.list_url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(2000)

                # Get HTML
                html_content = page.content()
                browser.close()

                # Parse articles
                articles = self.parse_articles(html_content)
                return articles[:limit]

        except Exception as e:
            logger.error(f"Error fetching articles from {self.name}: {e}")
            return []

    def parse_articles(self, html: str) -> List[Dict]:
        """
        Parse articles from HTML

        Args:
            html: HTML content as string

        Returns:
            List of article dictionaries
        """
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        articles = []

        # Find article containers
        if self.article_container:
            containers = soup.select(self.article_container)
        else:
            # If no container specified, try to find articles directly
            containers = [soup]

        for container in containers:
            try:
                article = self._extract_article_data(container, soup)

                if self._is_valid_article(article):
                    articles.append(article)

            except Exception as e:
                logger.warning(f"Error parsing article in {self.name}: {e}")
                continue

        return articles

    def _extract_article_data(self, container, full_soup=None) -> Dict:
        """
        Extract article data from container element

        Args:
            container: BeautifulSoup element containing article
            full_soup: Full page soup (fallback if container search fails)

        Returns:
            Dictionary with article data
        """
        # Extract title
        title = ""
        if self.title_selector:
            title_elem = container.select_one(self.title_selector)
            if title_elem:
                title = title_elem.text.strip()

        # Extract URL
        url = ""
        if self.link_selector:
            link_elem = container.select_one(self.link_selector)
            if link_elem:
                url = link_elem.get("href", "").strip()
                # Convert relative URL to absolute
                if url and not url.startswith("http"):
                    url = self.base_url.rstrip("/") + "/" + url.lstrip("/")

        # Extract date
        publish_date = None
        if self.date_selector:
            date_elem = container.select_one(self.date_selector)
            if date_elem:
                date_str = date_elem.text.strip()
                publish_date = self._parse_date(date_str)

        # Fallback: Try to extract date from URL if not found in HTML
        if not publish_date and url:
            publish_date = self._extract_date_from_url(url)

        # Extract summary (optional)
        summary = ""
        if self.summary_selector:
            summary_elem = container.select_one(self.summary_selector)
            if summary_elem:
                summary = summary_elem.text.strip()

        return {
            "title": title,
            "url": url,
            "publish_date": publish_date,
            "summary": summary,
            "source": self.name,
        }

    def _parse_date(self, date_str: str) -> Optional[date]:
        """
        Parse date string to date object

        Args:
            date_str: Date string

        Returns:
            date object or None if parsing fails
        """
        if not date_str:
            return None

        try:
            # Clean up the string
            date_str = date_str.strip()

            # Try primary format
            if " " in date_str and "-" in date_str:
                # Format with time: "2025-11-03 18:02:21"
                dt = datetime.strptime(date_str.split()[0], "%Y-%m-%d")
                return dt.date()

            # Format without time: "2025-11-03" or "2025/11/03" or "2025.11.03" or "(2025-11-03)"
            # Remove parentheses first
            date_str = date_str.strip('()')
            if re.match(r'\d{4}[-/.]\d{2}[-/.]\d{2}', date_str):
                # Replace / and . with - for uniform parsing
                normalized = date_str.replace('/', '-').replace('.', '-')
                dt = datetime.strptime(normalized, "%Y-%m-%d")
                return dt.date()

        except ValueError:
            pass

        # Try alternative formats
        try:
            from datetime import timedelta

            # Relative time - seconds: "8秒前"
            match = re.search(r'(\d+)秒前', date_str)
            if match:
                return date.today()

            # Relative time - minutes: "10分钟前"
            match = re.search(r'(\d+)分钟前', date_str)
            if match:
                return date.today()

            # Relative time - hours: "10小时前" or "10 小时前" (with space)
            match = re.search(r'(\d+)\s*小时前', date_str)
            if match:
                hours_ago = int(match.group(1))
                # If more than 24 hours, might be yesterday
                if hours_ago >= 24:
                    days_ago = hours_ago // 24
                    return date.today() - timedelta(days=days_ago)
                return date.today()

            # Relative time - days: "3天前"
            match = re.search(r'(\d+)天前', date_str)
            if match:
                days_ago = int(match.group(1))
                return date.today() - timedelta(days=days_ago)

            # Chinese relative days: "昨天", "前天"
            if '昨天' in date_str or '昨日' in date_str:
                return date.today() - timedelta(days=1)
            if '前天' in date_str:
                return date.today() - timedelta(days=2)

            # Short date format: "10-31" (assume current year)
            match = re.match(r'(\d{1,2})-(\d{1,2})$', date_str)
            if match:
                month, day = match.groups()
                current_year = date.today().year
                try:
                    return date(current_year, int(month), int(day))
                except ValueError:
                    # Invalid date (e.g., 02-30), return None
                    pass

            # Chinese format: "2025年11月3日"
            match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', date_str)
            if match:
                year, month, day = match.groups()
                return date(int(year), int(month), int(day))

        except Exception:
            pass

        logger.warning(f"Failed to parse date: {date_str}")
        return None

    def _extract_date_from_url(self, url: str) -> Optional[date]:
        """
        Extract date from URL path

        Supports common URL patterns:
        - /n1/2025/1107/xxx.html  -> 2025-11-07 (人民网)
        - /tech/20251106/xxx.html -> 2025-11-06 (新华网)
        - /202511/t20251103_xxx.html -> 2025-11-03 (国家发改委)
        - /20251106/xxx.html -> 2025-11-06 (国家能源局)

        Args:
            url: Article URL

        Returns:
            date object or None if no date found in URL
        """
        if not url:
            return None

        try:
            # Pattern 1: /YYYY/MMDD/ (e.g., /n1/2025/1107/)
            match = re.search(r'/(\d{4})/(\d{4})/', url)
            if match:
                year = match.group(1)
                mmdd = match.group(2)
                month = mmdd[:2]
                day = mmdd[2:]
                return date(int(year), int(month), int(day))

            # Pattern 2: /YYYYMMDD/ (e.g., /tech/20251106/)
            match = re.search(r'/(\d{8})/', url)
            if match:
                date_str = match.group(1)
                year = date_str[:4]
                month = date_str[4:6]
                day = date_str[6:8]
                return date(int(year), int(month), int(day))

            # Pattern 3: /YYYYMM/tYYYYMMDD_ (e.g., /202511/t20251103_)
            match = re.search(r'/\d{6}/t(\d{8})', url)
            if match:
                date_str = match.group(1)
                year = date_str[:4]
                month = date_str[4:6]
                day = date_str[6:8]
                return date(int(year), int(month), int(day))

        except Exception as e:
            logger.debug(f"Failed to extract date from URL {url}: {e}")

        return None

    def _is_valid_article(self, article: Dict) -> bool:
        """
        Validate article has required fields

        Args:
            article: Article dictionary

        Returns:
            True if valid, False otherwise
        """
        # Must have title and URL
        if not article.get("title"):
            return False

        if not article.get("url"):
            return False

        # Date is optional but recommended
        # (some sites might not show dates on list pages)

        return True


class ScraperFactory:
    """
    Factory to create appropriate scraper for a given source
    """

    # Mapping of sources that need custom scrapers
    CUSTOM_SCRAPERS = {
        "中国IDC圈": "idcquan_scraper.IdcquanScraper"
    }

    @classmethod
    def create_scraper(cls, config: Dict):
        """
        Create appropriate scraper based on configuration

        Args:
            config: Source configuration

        Returns:
            Scraper instance (GenericScraper or custom scraper)
        """
        source_name = config.get("name", "")

        # Check if custom scraper exists
        if source_name in cls.CUSTOM_SCRAPERS:
            # Import and use custom scraper
            module_class = cls.CUSTOM_SCRAPERS[source_name]
            module_name, class_name = module_class.rsplit(".", 1)

            try:
                # Dynamic import
                import importlib
                module = importlib.import_module(f"src.scrapers.{module_name}")
                scraper_class = getattr(module, class_name)
                return scraper_class()
            except Exception as e:
                logger.warning(f"Failed to load custom scraper for {source_name}: {e}")
                logger.info(f"Falling back to GenericScraper")

        # Use generic scraper
        return GenericScraper(config)

    @classmethod
    def create_all_scrapers(cls, config_path: str) -> List:
        """
        Create scrapers for all active sources in config

        Args:
            config_path: Path to media-sources.json

        Returns:
            List of scraper instances
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        scrapers = []
        for source in config_data.get("sources", []):
            if source.get("active", True):
                try:
                    scraper = cls.create_scraper(source)
                    scrapers.append(scraper)
                except Exception as e:
                    logger.error(f"Failed to create scraper for {source.get('name')}: {e}")

        return scrapers

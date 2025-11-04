"""
Tests for IdcquanScraper

Following TDD approach:
1. Write failing tests first
2. Implement minimal code to pass tests
3. Refactor
"""

import pytest
from datetime import datetime, date
from unittest.mock import Mock, patch, MagicMock
from src.scrapers.idcquan_scraper import IdcquanScraper


@pytest.fixture
def scraper():
    """Create scraper instance"""
    return IdcquanScraper()


@pytest.fixture
def sample_html():
    """Sample HTML structure from idcquan.com"""
    return """
    <div class="news clearfix">
        <span class="date">2025-11-03 18:02:21</span>
        <a class="bdurl" href="https://news.idcquan.com/scqb/205766.shtml" target="_blank">
            <img class="newsimg" src="https://example.com/image.png">
        </a>
        <div class="news_nr">
            <a href="https://news.idcquan.com/scqb/205766.shtml" target="_blank" class="d1">
                <span class="title">深度｜重新定义智算中心生存法则</span>
            </a>
            <div class="d2">
                <span class="nei_rong">"停止追逐更新周期，开始追求韧性。未来不是建造更快的算力中心。"</span>
                <a href="https://news.idcquan.com/scqb/205766.shtml" target="_blank">&lt;详情&gt;</a>
            </div>
            <div class="d3">
                <div class="fl">
                    <a href="#">智算</a>
                    <a href="#">算力</a>
                </div>
            </div>
        </div>
    </div>

    <div class="news clearfix">
        <span class="date">2025-11-01 09:54:00</span>
        <a class="bdurl" href="https://news.idcquan.com/news/205758.shtml" target="_blank">
            <img class="newsimg" src="https://example.com/image2.png">
        </a>
        <div class="news_nr">
            <a href="https://news.idcquan.com/news/205758.shtml" target="_blank" class="d1">
                <span class="title">曝某保险巨头豪掷13亿为8000机柜</span>
            </a>
            <div class="d2">
                <span class="nei_rong">某保险巨头投资数据中心项目。</span>
                <a href="https://news.idcquan.com/news/205758.shtml" target="_blank">&lt;详情&gt;</a>
            </div>
        </div>
    </div>
    """


class TestIdcquanScraperInit:
    """Test scraper initialization"""

    def test_scraper_has_base_url(self, scraper):
        """Scraper should have base URL configured"""
        assert scraper.base_url == "https://news.idcquan.com/"

    def test_scraper_has_source_name(self, scraper):
        """Scraper should have source name"""
        assert scraper.source_name == "中国IDC圈"


class TestParseArticles:
    """Test HTML parsing functionality"""

    def test_parse_articles_from_html(self, scraper, sample_html):
        """Should extract articles from HTML"""
        articles = scraper.parse_articles(sample_html)

        assert len(articles) == 2
        assert all(isinstance(article, dict) for article in articles)

    def test_parse_article_title(self, scraper, sample_html):
        """Should extract article title correctly"""
        articles = scraper.parse_articles(sample_html)

        assert articles[0]["title"] == "深度｜重新定义智算中心生存法则"
        assert articles[1]["title"] == "曝某保险巨头豪掷13亿为8000机柜"

    def test_parse_article_url(self, scraper, sample_html):
        """Should extract article URL correctly"""
        articles = scraper.parse_articles(sample_html)

        assert articles[0]["url"] == "https://news.idcquan.com/scqb/205766.shtml"
        assert articles[1]["url"] == "https://news.idcquan.com/news/205758.shtml"

    def test_parse_article_date(self, scraper, sample_html):
        """Should extract and parse date correctly"""
        articles = scraper.parse_articles(sample_html)

        # Date should be parsed as date object
        assert articles[0]["publish_date"] == date(2025, 11, 3)
        assert articles[1]["publish_date"] == date(2025, 11, 1)

    def test_parse_article_summary(self, scraper, sample_html):
        """Should extract article summary"""
        articles = scraper.parse_articles(sample_html)

        expected_summary = '"停止追逐更新周期，开始追求韧性。未来不是建造更快的算力中心。"'
        assert articles[0]["summary"] == expected_summary
        assert articles[1]["summary"] == "某保险巨头投资数据中心项目。"

    def test_parse_empty_html(self, scraper):
        """Should return empty list for empty HTML"""
        articles = scraper.parse_articles("")
        assert articles == []

    def test_parse_html_without_articles(self, scraper):
        """Should return empty list if no articles found"""
        html = "<div>No articles here</div>"
        articles = scraper.parse_articles(html)
        assert articles == []


class TestFetchArticles:
    """Test article fetching from live website"""

    @patch("src.scrapers.idcquan_scraper.sync_playwright")
    def test_fetch_articles_uses_playwright(self, mock_playwright, scraper):
        """Should use playwright to fetch articles"""
        # Mock playwright chain
        mock_browser = MagicMock()
        mock_page = MagicMock()
        mock_page.content.return_value = "<html></html>"

        mock_browser.new_page.return_value = mock_page
        mock_playwright.return_value.__enter__.return_value.chromium.launch.return_value = (
            mock_browser
        )

        scraper.fetch_articles(limit=10)

        # Verify playwright was called
        mock_playwright.return_value.__enter__.return_value.chromium.launch.assert_called_once()

    @patch("src.scrapers.idcquan_scraper.sync_playwright")
    def test_fetch_articles_navigates_to_correct_url(self, mock_playwright, scraper):
        """Should navigate to idcquan news page"""
        mock_browser = MagicMock()
        mock_page = MagicMock()
        mock_page.content.return_value = "<html></html>"

        mock_browser.new_page.return_value = mock_page
        mock_playwright.return_value.__enter__.return_value.chromium.launch.return_value = (
            mock_browser
        )

        scraper.fetch_articles(limit=10)

        # Verify navigation to correct URL
        mock_page.goto.assert_called_once_with(
            "https://news.idcquan.com/", wait_until="domcontentloaded", timeout=30000
        )

    @patch("src.scrapers.idcquan_scraper.sync_playwright")
    def test_fetch_articles_returns_parsed_articles(
        self, mock_playwright, scraper, sample_html
    ):
        """Should return parsed articles from fetched HTML"""
        mock_browser = MagicMock()
        mock_page = MagicMock()
        mock_page.content.return_value = sample_html

        mock_browser.new_page.return_value = mock_page
        mock_playwright.return_value.__enter__.return_value.chromium.launch.return_value = (
            mock_browser
        )

        articles = scraper.fetch_articles(limit=10)

        assert len(articles) == 2
        assert articles[0]["title"] == "深度｜重新定义智算中心生存法则"

    @patch("src.scrapers.idcquan_scraper.sync_playwright")
    def test_fetch_articles_respects_limit(
        self, mock_playwright, scraper, sample_html
    ):
        """Should respect article limit parameter"""
        mock_browser = MagicMock()
        mock_page = MagicMock()
        mock_page.content.return_value = sample_html

        mock_browser.new_page.return_value = mock_page
        mock_playwright.return_value.__enter__.return_value.chromium.launch.return_value = (
            mock_browser
        )

        articles = scraper.fetch_articles(limit=1)

        assert len(articles) == 1

    @patch("src.scrapers.idcquan_scraper.sync_playwright")
    def test_fetch_articles_handles_errors(self, mock_playwright, scraper):
        """Should handle errors gracefully"""
        mock_playwright.return_value.__enter__.return_value.chromium.launch.side_effect = (
            Exception("Network error")
        )

        articles = scraper.fetch_articles(limit=10)

        # Should return empty list on error
        assert articles == []


class TestDateParsing:
    """Test date parsing functionality"""

    def test_parse_date_with_time(self, scraper):
        """Should parse date with time format"""
        date_str = "2025-11-03 18:02:21"
        parsed = scraper._parse_date(date_str)

        assert parsed == date(2025, 11, 3)

    def test_parse_date_without_time(self, scraper):
        """Should parse date without time"""
        date_str = "2025-11-03"
        parsed = scraper._parse_date(date_str)

        assert parsed == date(2025, 11, 3)

    def test_parse_invalid_date(self, scraper):
        """Should return None for invalid date"""
        date_str = "invalid date"
        parsed = scraper._parse_date(date_str)

        assert parsed is None

    def test_parse_empty_date(self, scraper):
        """Should return None for empty date"""
        parsed = scraper._parse_date("")

        assert parsed is None


class TestArticleValidation:
    """Test article validation"""

    def test_validate_complete_article(self, scraper):
        """Should validate complete article"""
        article = {
            "title": "Test Title",
            "url": "https://news.idcquan.com/news/12345.shtml",
            "publish_date": date(2025, 11, 3),
            "summary": "Test summary",
        }

        assert scraper._is_valid_article(article) is True

    def test_validate_article_missing_title(self, scraper):
        """Should reject article without title"""
        article = {
            "title": "",
            "url": "https://news.idcquan.com/news/12345.shtml",
            "publish_date": date(2025, 11, 3),
        }

        assert scraper._is_valid_article(article) is False

    def test_validate_article_missing_url(self, scraper):
        """Should reject article without URL"""
        article = {
            "title": "Test Title",
            "url": "",
            "publish_date": date(2025, 11, 3),
        }

        assert scraper._is_valid_article(article) is False

    def test_validate_article_missing_date(self, scraper):
        """Should reject article without date"""
        article = {
            "title": "Test Title",
            "url": "https://news.idcquan.com/news/12345.shtml",
            "publish_date": None,
        }

        assert scraper._is_valid_article(article) is False

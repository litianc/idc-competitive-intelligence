"""
数据库层单元测试

TDD原则：先写测试，再写实现
这些测试最初会失败（RED），然后我们编写代码让它们通过（GREEN）
"""

import pytest
import sqlite3
from datetime import date, datetime, timedelta
from src.storage.database import Database


class TestDatabaseInitialization:
    """测试数据库初始化"""

    def test_create_database_in_memory(self):
        """测试创建内存数据库"""
        db = Database(":memory:")
        assert db.conn is not None

    def test_create_database_file(self, tmp_path):
        """测试创建文件数据库"""
        db_path = tmp_path / "test.db"
        db = Database(str(db_path))
        assert db_path.exists()
        db.close()

    def test_create_articles_table(self):
        """测试创建articles表"""
        db = Database(":memory:")
        cursor = db.conn.cursor()

        # 检查表是否存在
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='articles'"
        )
        assert cursor.fetchone() is not None

    def test_articles_table_schema(self):
        """测试articles表结构是否包含所有必需字段"""
        db = Database(":memory:")
        cursor = db.conn.cursor()

        cursor.execute("PRAGMA table_info(articles)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        # 验证关键字段存在
        assert "id" in columns
        assert "title" in columns
        assert "url" in columns
        assert "url_hash" in columns
        assert "source" in columns
        assert "publish_date" in columns  # 实际发布日期
        assert "collected_at" in columns  # 采集时间
        assert "content" in columns
        assert "summary" in columns
        assert "category" in columns
        assert "priority" in columns
        assert "score" in columns
        assert "link_valid" in columns


class TestArticleInsertion:
    """测试文章插入"""

    @pytest.fixture
    def db(self):
        """创建测试数据库fixture"""
        database = Database(":memory:")
        yield database
        database.close()

    def test_insert_article_basic(self, db):
        """测试基本文章插入"""
        article_id = db.insert_article(
            title="测试文章",
            url="https://example.com/test",
            source="测试媒体",
            publish_date=date.today(),
            content="测试内容",
        )

        assert article_id is not None
        assert article_id > 0

    def test_insert_article_with_all_fields(self, db):
        """测试插入包含所有字段的文章"""
        publish_date = date(2025, 1, 3)

        article_id = db.insert_article(
            title="完整测试文章",
            url="https://example.com/full-test",
            source="中国IDC圈",
            source_tier=1,
            publish_date=publish_date,
            content="这是完整的测试内容",
            summary="这是测试摘要",
            category="投资",
            priority="高",
            score=85,
            link_valid=True,
        )

        assert article_id > 0

        # 验证数据正确保存
        article = db.get_article_by_id(article_id)
        assert article["title"] == "完整测试文章"
        assert article["url"] == "https://example.com/full-test"
        assert article["source"] == "中国IDC圈"
        assert article["source_tier"] == 1
        assert article["publish_date"] == publish_date
        assert article["summary"] == "这是测试摘要"
        assert article["category"] == "投资"
        assert article["priority"] == "高"
        assert article["score"] == 85
        assert article["link_valid"] == 1

    def test_insert_duplicate_article_by_url(self, db):
        """测试插入重复URL的文章（应该失败或忽略）"""
        url = "https://example.com/duplicate"

        # 第一次插入
        id1 = db.insert_article(
            title="文章1",
            url=url,
            source="测试媒体",
            publish_date=date.today(),
            content="内容1",
        )

        # 第二次插入相同URL
        id2 = db.insert_article(
            title="文章2",  # 标题不同
            url=url,  # URL相同
            source="测试媒体",
            publish_date=date.today(),
            content="内容2",
        )

        # 第二次插入应该返回None或原ID（去重）
        assert id2 is None or id2 == id1

        # 数据库中应该只有一条记录
        articles = db.get_all_articles()
        urls = [a["url"] for a in articles]
        assert urls.count(url) == 1

    def test_url_hash_generation(self, db):
        """测试URL哈希自动生成"""
        article_id = db.insert_article(
            title="测试哈希",
            url="https://example.com/hash-test",
            source="测试媒体",
            publish_date=date.today(),
            content="测试内容",
        )

        article = db.get_article_by_id(article_id)
        assert article["url_hash"] is not None
        assert len(article["url_hash"]) == 32  # MD5长度

    def test_publish_date_vs_collected_at(self, db):
        """测试发布日期和采集时间是分开存储的（关键测试）"""
        # 文章发布日期是3天前
        publish_date = date.today() - timedelta(days=3)

        article_id = db.insert_article(
            title="历史文章",
            url="https://example.com/old-article",
            source="测试媒体",
            publish_date=publish_date,
            content="这是3天前发布的文章",
        )

        article = db.get_article_by_id(article_id)

        # 发布日期应该是3天前
        assert article["publish_date"] == publish_date

        # 采集时间应该是今天（自动设置为当前时间）
        collected_at = datetime.fromisoformat(article["collected_at"])
        assert collected_at.date() == date.today()


class TestArticleRetrieval:
    """测试文章查询"""

    @pytest.fixture
    def db_with_articles(self):
        """创建包含测试数据的数据库"""
        db = Database(":memory:")

        # 插入多篇测试文章
        today = date.today()

        db.insert_article(
            title="今天的文章",
            url="https://example.com/today",
            source="测试媒体",
            publish_date=today,
            content="今天发布",
        )

        db.insert_article(
            title="3天前的文章",
            url="https://example.com/3days-ago",
            source="测试媒体",
            publish_date=today - timedelta(days=3),
            content="3天前发布",
        )

        db.insert_article(
            title="7天前的文章",
            url="https://example.com/7days-ago",
            source="测试媒体",
            publish_date=today - timedelta(days=7),
            content="7天前发布",
        )

        yield db
        db.close()

    def test_get_article_by_id(self, db_with_articles):
        """测试按ID查询文章"""
        article = db_with_articles.get_article_by_id(1)
        assert article is not None
        assert article["id"] == 1
        assert article["title"] == "今天的文章"

    def test_get_article_by_id_not_found(self, db_with_articles):
        """测试查询不存在的文章"""
        article = db_with_articles.get_article_by_id(9999)
        assert article is None

    def test_get_articles_by_date_range(self, db_with_articles):
        """测试按日期范围查询文章"""
        today = date.today()
        start_date = today - timedelta(days=5)
        end_date = today

        articles = db_with_articles.get_articles_by_date_range(start_date, end_date)

        # 应该返回5天内的文章（今天 + 3天前）
        assert len(articles) == 2

    def test_get_articles_for_weekly_report(self, db_with_articles):
        """测试获取周报数据（过去7天）"""
        articles = db_with_articles.get_articles_for_weekly_report()

        # 应该包含今天和3天前的文章，不包含7天前的
        assert len(articles) == 2

        # 文章应该按分数降序排列
        if len(articles) > 1:
            for i in range(len(articles) - 1):
                assert articles[i]["score"] >= articles[i + 1]["score"]

    def test_get_all_articles(self, db_with_articles):
        """测试获取所有文章"""
        articles = db_with_articles.get_all_articles()
        assert len(articles) == 3


class TestArticleUpdate:
    """测试文章更新"""

    @pytest.fixture
    def db(self):
        database = Database(":memory:")
        yield database
        database.close()

    def test_update_article_summary(self, db):
        """测试更新文章摘要"""
        # 插入文章
        article_id = db.insert_article(
            title="测试文章",
            url="https://example.com/test",
            source="测试媒体",
            publish_date=date.today(),
            content="原始内容",
        )

        # 更新摘要
        summary = "这是LLM生成的摘要，长度在80-150字之间" * 3
        db.update_article_summary(article_id, summary)

        # 验证更新
        article = db.get_article_by_id(article_id)
        assert article["summary"] == summary
        assert article["summary_generated"] == 1

    def test_update_article_scores(self, db):
        """测试更新文章评分"""
        article_id = db.insert_article(
            title="测试文章",
            url="https://example.com/test",
            source="测试媒体",
            publish_date=date.today(),
            content="测试内容",
        )

        # 更新评分
        db.update_article_scores(
            article_id=article_id,
            category="技术",
            priority="高",
            score=85,
            score_relevance=35,
            score_timeliness=25,
            score_impact=15,
            score_credibility=15,
        )

        # 验证更新
        article = db.get_article_by_id(article_id)
        assert article["category"] == "技术"
        assert article["priority"] == "高"
        assert article["score"] == 85
        assert article["score_relevance"] == 35
        assert article["score_timeliness"] == 25
        assert article["score_impact"] == 15
        assert article["score_credibility"] == 15
        assert article["processed"] == 1

    def test_update_link_validity(self, db):
        """测试更新链接有效性"""
        article_id = db.insert_article(
            title="测试文章",
            url="https://example.com/test",
            source="测试媒体",
            publish_date=date.today(),
            content="测试内容",
        )

        # 标记链接无效
        db.update_link_validity(article_id, False)

        article = db.get_article_by_id(article_id)
        assert article["link_valid"] == 0

        # 标记链接有效
        db.update_link_validity(article_id, True)

        article = db.get_article_by_id(article_id)
        assert article["link_valid"] == 1


class TestDatabaseQueries:
    """测试复杂查询"""

    @pytest.fixture
    def db_with_scored_articles(self):
        """创建包含评分数据的测试数据库"""
        db = Database(":memory:")

        today = date.today()

        # 插入高优先级投资类文章
        id1 = db.insert_article(
            title="某公司获10亿融资",
            url="https://example.com/investment1",
            source="中国IDC圈",
            source_tier=1,
            publish_date=today,
            content="融资内容",
        )
        db.update_article_scores(id1, "投资", "高", 85, 40, 25, 15, 15)
        db.update_article_summary(id1, "某公司完成10亿元C轮融资" * 5)

        # 插入中优先级技术类文章
        id2 = db.insert_article(
            title="新型液冷技术发布",
            url="https://example.com/tech1",
            source="数据中心世界",
            source_tier=1,
            publish_date=today - timedelta(days=2),
            content="技术内容",
        )
        db.update_article_scores(id2, "技术", "中", 55, 30, 15, 10, 15)
        db.update_article_summary(id2, "某公司发布新一代液冷技术" * 5)

        # 插入低优先级市场类文章
        id3 = db.insert_article(
            title="行业动态简讯",
            url="https://example.com/market1",
            source="通信世界网",
            source_tier=2,
            publish_date=today - timedelta(days=5),
            content="市场内容",
        )
        db.update_article_scores(id3, "市场", "低", 30, 15, 5, 5, 8)
        db.update_article_summary(id3, "本周行业动态汇总" * 5)

        yield db
        db.close()

    def test_get_articles_by_priority(self, db_with_scored_articles):
        """测试按优先级查询"""
        high_priority = db_with_scored_articles.get_articles_by_priority("高")
        assert len(high_priority) == 1
        assert high_priority[0]["title"] == "某公司获10亿融资"

    def test_get_articles_by_category(self, db_with_scored_articles):
        """测试按分类查询"""
        tech_articles = db_with_scored_articles.get_articles_by_category("技术")
        assert len(tech_articles) == 1
        assert tech_articles[0]["title"] == "新型液冷技术发布"

    def test_get_articles_ready_for_report(self, db_with_scored_articles):
        """测试获取准备好的周报文章（已评分、已生成摘要、链接有效）"""
        articles = db_with_scored_articles.get_articles_ready_for_report()

        # 所有3篇文章都应该准备好
        assert len(articles) == 3

        # 验证所有文章都符合条件
        for article in articles:
            assert article["processed"] == 1
            assert article["summary_generated"] == 1
            assert article["link_valid"] == 1
            assert article["summary"] is not None


class TestDatabaseEdgeCases:
    """测试边界情况"""

    def test_empty_database(self):
        """测试空数据库查询"""
        db = Database(":memory:")
        articles = db.get_all_articles()
        assert articles == []

    def test_insert_article_with_special_characters(self):
        """测试包含特殊字符的文章"""
        db = Database(":memory:")

        article_id = db.insert_article(
            title='测试"特殊\'字符&<>',
            url="https://example.com/special?param=value&other=123",
            source="测试媒体",
            publish_date=date.today(),
            content="内容包含\n换行符\t制表符",
        )

        article = db.get_article_by_id(article_id)
        assert article["title"] == '测试"特殊\'字符&<>'
        assert "换行符" in article["content"]

    def test_insert_article_with_future_date(self):
        """测试未来日期（边界检查）"""
        db = Database(":memory:")

        future_date = date.today() + timedelta(days=10)

        # 应该允许插入，但在应用层可能需要验证
        article_id = db.insert_article(
            title="未来文章",
            url="https://example.com/future",
            source="测试媒体",
            publish_date=future_date,
            content="测试内容",
        )

        article = db.get_article_by_id(article_id)
        assert article["publish_date"] == future_date

    def test_database_close_and_reopen(self, tmp_path):
        """测试数据库关闭和重新打开"""
        db_path = tmp_path / "test.db"

        # 创建并插入数据
        db1 = Database(str(db_path))
        article_id = db1.insert_article(
            title="持久化测试",
            url="https://example.com/persistent",
            source="测试媒体",
            publish_date=date.today(),
            content="测试内容",
        )
        db1.close()

        # 重新打开并验证数据
        db2 = Database(str(db_path))
        article = db2.get_article_by_id(article_id)
        assert article is not None
        assert article["title"] == "持久化测试"
        db2.close()

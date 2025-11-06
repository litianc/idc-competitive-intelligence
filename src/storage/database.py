"""
数据库层实现

负责与SQLite数据库交互，包括文章的CRUD操作
"""

import sqlite3
import hashlib
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path


class Database:
    """数据库管理类"""

    def __init__(self, db_path: str = "data/intelligence.db"):
        """
        初始化数据库连接

        Args:
            db_path: 数据库文件路径，使用":memory:"创建内存数据库
        """
        self.db_path = db_path

        # 如果是文件数据库，确保目录存在
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # 使查询结果可以像字典一样访问

        self._create_tables()
        self._create_indexes()

    def _create_tables(self):
        """创建数据库表"""
        cursor = self.conn.cursor()

        # 创建articles表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                -- 基本信息
                title TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                url_hash TEXT UNIQUE NOT NULL,
                source TEXT NOT NULL,
                source_tier INTEGER DEFAULT 2,

                -- 时间信息（关键：区分发布日期和采集时间）
                publish_date DATE NOT NULL,
                collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                -- 内容
                content TEXT,
                summary TEXT,

                -- 分类和评分
                category TEXT,
                categories TEXT,
                priority TEXT,
                score INTEGER DEFAULT 0,

                -- 评分明细
                score_relevance INTEGER DEFAULT 0,
                score_timeliness INTEGER DEFAULT 0,
                score_impact INTEGER DEFAULT 0,
                score_credibility INTEGER DEFAULT 0,

                -- LLM智能评分
                llm_relevance_score INTEGER DEFAULT 0,
                llm_importance_score INTEGER DEFAULT 0,
                llm_category_score INTEGER DEFAULT 0,
                llm_total_score INTEGER DEFAULT 0,
                llm_category_suggestion TEXT,
                llm_reason TEXT,

                -- 质量标记
                link_valid BOOLEAN DEFAULT 1,
                summary_generated BOOLEAN DEFAULT 0,
                processed BOOLEAN DEFAULT 0,

                -- 元数据
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.conn.commit()

    def _create_indexes(self):
        """创建索引以提高查询性能"""
        cursor = self.conn.cursor()

        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_publish_date ON articles(publish_date DESC)",
            "CREATE INDEX IF NOT EXISTS idx_priority ON articles(priority)",
            "CREATE INDEX IF NOT EXISTS idx_category ON articles(category)",
            "CREATE INDEX IF NOT EXISTS idx_collected_at ON articles(collected_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_source ON articles(source)",
            "CREATE INDEX IF NOT EXISTS idx_link_valid ON articles(link_valid)",
            "CREATE INDEX IF NOT EXISTS idx_processed ON articles(processed)",
        ]

        for index_sql in indexes:
            cursor.execute(index_sql)

        self.conn.commit()

    @staticmethod
    def generate_url_hash(url: str) -> str:
        """
        生成URL的MD5哈希

        Args:
            url: 原始URL

        Returns:
            32字符的MD5哈希值
        """
        return hashlib.md5(url.encode("utf-8")).hexdigest()

    def insert_article(
        self,
        title: str,
        url: str,
        source: str,
        publish_date: date,
        content: str,
        source_tier: int = 2,
        summary: Optional[str] = None,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        score: int = 0,
        score_relevance: int = 0,
        score_timeliness: int = 0,
        score_impact: int = 0,
        score_credibility: int = 0,
        llm_relevance_score: int = 0,
        llm_importance_score: int = 0,
        llm_category_score: int = 0,
        llm_total_score: int = 0,
        llm_category_suggestion: Optional[str] = None,
        llm_reason: Optional[str] = None,
        link_valid: bool = True,
    ) -> Optional[int]:
        """
        插入文章到数据库

        Args:
            title: 文章标题
            url: 文章链接
            source: 来源媒体
            publish_date: 文章实际发布日期（重要！）
            content: 文章内容
            source_tier: 媒体等级（1=Tier1, 2=Tier2, 3=Tier3）
            summary: 文章摘要（可选）
            category: 文章分类（可选）
            priority: 优先级（可选）
            score: 评分（可选）
            score_relevance: 业务相关性评分（可选）
            score_timeliness: 时效性评分（可选）
            score_impact: 影响范围评分（可选）
            score_credibility: 来源可信度评分（可选）
            llm_relevance_score: LLM相关性评分（可选，0-20分）
            llm_importance_score: LLM重要性评分（可选，0-20分）
            llm_category_score: LLM分类置信度（可选，0-10分）
            llm_total_score: LLM总分（可选，0-50分）
            llm_category_suggestion: LLM建议的分类（可选）
            llm_reason: LLM判断理由（可选）
            link_valid: 链接是否有效

        Returns:
            插入的文章ID，如果URL重复则返回None
        """
        cursor = self.conn.cursor()

        # 生成URL哈希
        url_hash = self.generate_url_hash(url)

        try:
            cursor.execute(
                """
                INSERT INTO articles (
                    title, url, url_hash, source, source_tier,
                    publish_date, content, summary,
                    category, priority, score,
                    score_relevance, score_timeliness, score_impact, score_credibility,
                    llm_relevance_score, llm_importance_score, llm_category_score, llm_total_score,
                    llm_category_suggestion, llm_reason,
                    link_valid, summary_generated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    title,
                    url,
                    url_hash,
                    source,
                    source_tier,
                    publish_date,
                    content,
                    summary,
                    category,
                    priority,
                    score,
                    score_relevance,
                    score_timeliness,
                    score_impact,
                    score_credibility,
                    llm_relevance_score,
                    llm_importance_score,
                    llm_category_score,
                    llm_total_score,
                    llm_category_suggestion,
                    llm_reason,
                    1 if link_valid else 0,
                    1 if summary else 0,
                ),
            )

            self.conn.commit()
            return cursor.lastrowid

        except sqlite3.IntegrityError:
            # URL已存在，返回None
            return None

    def get_article_by_id(self, article_id: int) -> Optional[Dict[str, Any]]:
        """
        按ID查询文章

        Args:
            article_id: 文章ID

        Returns:
            文章字典，如果不存在则返回None
        """
        cursor = self.conn.cursor()

        cursor.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
        row = cursor.fetchone()

        if row is None:
            return None

        article = dict(row)
        # 转换日期字符串为date对象
        if article.get("publish_date"):
            article["publish_date"] = datetime.strptime(
                article["publish_date"], "%Y-%m-%d"
            ).date()
        return article

    def get_all_articles(self) -> List[Dict[str, Any]]:
        """
        获取所有文章

        Returns:
            文章列表
        """
        cursor = self.conn.cursor()

        cursor.execute("SELECT * FROM articles ORDER BY publish_date DESC")
        rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def get_articles_by_date_range(
        self, start_date: date, end_date: date
    ) -> List[Dict[str, Any]]:
        """
        按日期范围查询文章

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            文章列表
        """
        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT * FROM articles
            WHERE publish_date >= ? AND publish_date <= ?
            ORDER BY publish_date DESC
            """,
            (start_date, end_date),
        )

        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_articles_for_weekly_report(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        获取用于周报的文章（过去N天，不包括第N天）

        Args:
            days: 天数，默认7天

        Returns:
            文章列表，按评分降序排列
        """
        cursor = self.conn.cursor()

        # 过去7天不包括第7天，所以使用 days-1
        start_date = date.today() - timedelta(days=days - 1)

        cursor.execute(
            """
            SELECT * FROM articles
            WHERE publish_date >= ?
            ORDER BY score DESC, publish_date DESC
            """,
            (start_date,),
        )

        rows = cursor.fetchall()
        articles = []
        for row in rows:
            article = dict(row)
            if article.get("publish_date"):
                article["publish_date"] = datetime.strptime(
                    article["publish_date"], "%Y-%m-%d"
                ).date()
            articles.append(article)
        return articles

    def update_article_summary(self, article_id: int, summary: str):
        """
        更新文章摘要

        Args:
            article_id: 文章ID
            summary: 摘要内容
        """
        cursor = self.conn.cursor()

        cursor.execute(
            """
            UPDATE articles
            SET summary = ?,
                summary_generated = 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (summary, article_id),
        )

        self.conn.commit()

    def update_article_scores(
        self,
        article_id: int,
        category: str,
        priority: str,
        score: int,
        score_relevance: int,
        score_timeliness: int,
        score_impact: int,
        score_credibility: int,
    ):
        """
        更新文章评分和分类

        Args:
            article_id: 文章ID
            category: 分类
            priority: 优先级
            score: 总分
            score_relevance: 业务相关性得分
            score_timeliness: 时效性得分
            score_impact: 影响范围得分
            score_credibility: 来源可信度得分
        """
        cursor = self.conn.cursor()

        cursor.execute(
            """
            UPDATE articles
            SET category = ?,
                priority = ?,
                score = ?,
                score_relevance = ?,
                score_timeliness = ?,
                score_impact = ?,
                score_credibility = ?,
                processed = 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                category,
                priority,
                score,
                score_relevance,
                score_timeliness,
                score_impact,
                score_credibility,
                article_id,
            ),
        )

        self.conn.commit()

    def update_link_validity(self, article_id: int, valid: bool):
        """
        更新链接有效性

        Args:
            article_id: 文章ID
            valid: 是否有效
        """
        cursor = self.conn.cursor()

        cursor.execute(
            """
            UPDATE articles
            SET link_valid = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (1 if valid else 0, article_id),
        )

        self.conn.commit()

    def get_articles_by_priority(self, priority: str) -> List[Dict[str, Any]]:
        """
        按优先级查询文章

        Args:
            priority: 优先级（高/中/低）

        Returns:
            文章列表
        """
        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT * FROM articles
            WHERE priority = ?
            ORDER BY score DESC, publish_date DESC
            """,
            (priority,),
        )

        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_articles_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        按分类查询文章

        Args:
            category: 分类（投资/技术/政策/市场）

        Returns:
            文章列表
        """
        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT * FROM articles
            WHERE category = ?
            ORDER BY score DESC, publish_date DESC
            """,
            (category,),
        )

        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_articles_ready_for_report(
        self, days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        获取准备好生成周报的文章

        条件：
        - 在指定天数内
        - 已处理（评分和分类）
        - 已生成摘要
        - 链接有效

        Args:
            days: 天数，默认7天

        Returns:
            文章列表
        """
        cursor = self.conn.cursor()

        start_date = date.today() - timedelta(days=days)

        cursor.execute(
            """
            SELECT * FROM articles
            WHERE publish_date >= ?
              AND processed = 1
              AND summary_generated = 1
              AND link_valid = 1
            ORDER BY score DESC, publish_date DESC
            """,
            (start_date,),
        )

        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def clear_all_articles(self):
        """清空所有历史文章数据"""
        cursor = self.conn.cursor()

        try:
            cursor.execute("DELETE FROM articles")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='articles'")
            self.conn.commit()

            # 执行VACUUM优化数据库文件大小
            cursor.execute("VACUUM")

            return True
        except Exception as e:
            self.conn.rollback()
            raise e

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        """支持上下文管理器"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """支持上下文管理器"""
        self.close()

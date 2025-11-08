"""
周报生成器

根据数据库中的文章数据生成Markdown格式的周报
"""

from datetime import date, timedelta
from typing import List, Dict, Optional
from src.storage.database import Database
from src.reporting.report_summarizer import (
    WeeklyReportSummarizer,
    get_random_insight_label,
    get_insight_icon
)
import logging
import os

logger = logging.getLogger(__name__)


class WeeklyReportGenerator:
    """周报生成器"""

    def __init__(
        self,
        database: Optional[Database] = None,
        db_path: str = "data/intelligence.db",
        enable_llm_summary: Optional[bool] = None
    ):
        """
        初始化周报生成器

        Args:
            database: 数据库实例（可选，用于测试）
            db_path: 数据库文件路径
            enable_llm_summary: 是否启用LLM摘要（None则从环境变量读取）
        """
        if database:
            self.db = database
        else:
            self.db = Database(db_path)

        # LLM摘要配置
        if enable_llm_summary is None:
            self.enable_llm_summary = os.getenv('WEEKLY_SUMMARY_ENABLED', 'true').lower() == 'true'
        else:
            self.enable_llm_summary = enable_llm_summary

        self.use_random_labels = os.getenv('WEEKLY_INSIGHT_LABEL_RANDOM', 'true').lower() == 'true'

        # 初始化摘要生成器
        if self.enable_llm_summary:
            try:
                self.summarizer = WeeklyReportSummarizer.from_env()
            except Exception as e:
                logger.warning(f"LLM摘要生成器初始化失败: {e}，将使用默认摘要")
                self.summarizer = None
        else:
            self.summarizer = None

    def get_articles_for_report(self, days: int = 7) -> List[Dict]:
        """
        获取用于生成周报的文章

        Args:
            days: 天数，默认7天

        Returns:
            文章列表，按评分降序排列
        """
        return self.db.get_articles_for_weekly_report(days=days)

    def group_by_category(self, articles: List[Dict]) -> Dict[str, List[Dict]]:
        """
        按分类分组文章

        Args:
            articles: 文章列表

        Returns:
            分类到文章列表的映射
        """
        grouped = {}
        for article in articles:
            category = article.get("category", "其他")
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(article)

        return grouped

    def group_by_priority(self, articles: List[Dict]) -> Dict[str, List[Dict]]:
        """
        按优先级分组文章

        Args:
            articles: 文章列表

        Returns:
            优先级到文章列表的映射
        """
        grouped = {}
        for article in articles:
            priority = article.get("priority", "低")
            if priority not in grouped:
                grouped[priority] = []
            grouped[priority].append(article)

        return grouped

    def generate_report(self, days: int = 7) -> str:
        """
        生成周报

        Args:
            days: 统计天数，默认7天

        Returns:
            Markdown格式的周报内容
        """
        # 获取文章
        articles = self.get_articles_for_report(days=days)

        if not articles:
            return self._generate_empty_report()

        # 按分类和优先级分组
        by_category = self.group_by_category(articles)
        by_priority = self.group_by_priority(articles)

        # 生成LLM摘要和板块点评
        insights = {}
        if self.enable_llm_summary and self.summarizer:
            try:
                insights = self.summarizer.generate_insights(articles, by_category)
                logger.info("✓ LLM摘要生成成功")
            except Exception as e:
                logger.warning(f"LLM摘要生成失败: {e}，使用默认摘要")
                insights = self.summarizer._get_default_insights(articles, by_category) if self.summarizer else {}

        # 生成报告
        report = self._generate_header()

        # 添加整体总结
        if insights.get('executive_summary'):
            report += self._format_executive_summary(insights['executive_summary'])

        # 跟踪已展示的文章URL（避免重复）
        displayed_urls = set()

        # 获取板块点评
        section_insights = insights.get('section_insights', {})

        # 生成各个章节（政策章节优先，避免被其他章节消费）
        report += self._generate_policy_section(
            by_category, by_priority, displayed_urls,
            insight=section_insights.get('政策法规', '')
        )
        report += self._generate_investment_section(
            by_category, by_priority, displayed_urls,
            insight=section_insights.get('投资动态', '')
        )
        report += self._generate_technology_section(
            by_category, by_priority, displayed_urls,
            insight=section_insights.get('技术进展', '')
        )
        report += self._generate_market_section(
            by_category, by_priority, displayed_urls,
            insight=section_insights.get('市场动态', '')
        )
        report += self._generate_other_section(
            by_category, by_priority, displayed_urls,
            insight=section_insights.get('其他动态', '')
        )

        # 生成统计信息
        report += self._generate_statistics(articles)

        return report

    def _generate_header(self) -> str:
        """生成报告头部"""
        today = date.today()
        week_number = today.isocalendar()[1]

        header = f"""# IDC行业周报 | {today.year}年第{week_number}周

**报告日期**: {today.strftime('%Y年%m月%d日')}
**数据来源**: 多源情报采集系统
**覆盖范围**: IDC/数据中心/云计算/AI算力

---

"""
        return header

    def _format_executive_summary(self, summary: str) -> str:
        """格式化整体总结"""
        return f"""## 📌 本周概览

{summary}

---

"""

    def _generate_investment_section(
        self, by_category: Dict, by_priority: Dict, displayed_urls: set, insight: str = ""
    ) -> str:
        """生成投资动态章节"""
        section = "## 二、投资动态\n\n"

        # 添加板块点评
        if insight:
            label = get_random_insight_label('投资动态', self.use_random_labels)
            icon = get_insight_icon(label)
            section += f"**{icon} {label}**：{insight}\n\n"

        # 获取投资类高优先级文章（支持多分类，如"投资,技术"）
        investment_articles = []
        for category, articles in by_category.items():
            if category and "投资" in category:
                investment_articles.extend(articles)

        # 过滤已展示的文章
        high_priority_investments = [
            a for a in investment_articles
            if a.get("priority") == "高" and a.get("url") not in displayed_urls
        ]

        if high_priority_investments:
            for i, article in enumerate(high_priority_investments, 1):
                section += self._format_article(i, article)
                displayed_urls.add(article['url'])  # 记录已展示
        else:
            # 如果没有高优先级，显示中优先级
            med_priority_investments = [
                a for a in investment_articles
                if a.get("priority") == "中" and a.get("url") not in displayed_urls
            ]
            if med_priority_investments:
                for i, article in enumerate(med_priority_investments[:3], 1):
                    section += self._format_article(i, article)
                    displayed_urls.add(article['url'])  # 记录已展示
            else:
                section += "*本周暂无重点投资动态*\n"

        section += "\n"
        return section

    def _generate_technology_section(
        self, by_category: Dict, by_priority: Dict, displayed_urls: set, insight: str = ""
    ) -> str:
        """生成技术进展章节"""
        section = "## 三、技术进展\n\n"

        # 添加板块点评
        if insight:
            label = get_random_insight_label('技术进展', self.use_random_labels)
            icon = get_insight_icon(label)
            section += f"**{icon} {label}**：{insight}\n\n"

        # 获取技术类高优先级文章（支持多分类，如"技术,政策"）
        tech_articles = []
        for category, articles in by_category.items():
            if category and "技术" in category:
                tech_articles.extend(articles)

        # 过滤已展示的文章
        high_priority_tech = [
            a for a in tech_articles
            if a.get("priority") == "高" and a.get("url") not in displayed_urls
        ]

        if high_priority_tech:
            for i, article in enumerate(high_priority_tech, 1):
                section += self._format_article(i, article)
                displayed_urls.add(article['url'])
        else:
            # 如果没有高优先级，显示中优先级
            med_priority_tech = [
                a for a in tech_articles
                if a.get("priority") == "中" and a.get("url") not in displayed_urls
            ]
            if med_priority_tech:
                for i, article in enumerate(med_priority_tech[:3], 1):
                    section += self._format_article(i, article)
                    displayed_urls.add(article['url'])
            else:
                section += "*本周暂无重点技术进展*\n"

        section += "\n"
        return section

    def _generate_policy_section(self, by_category: Dict, by_priority: Dict, displayed_urls: set, insight: str = "") -> str:
        """生成政策法规章节"""
        section = "## 一、政策法规\n\n"

        # 添加板块点评
        if insight:
            label = get_random_insight_label('政策法规', self.use_random_labels)
            icon = get_insight_icon(label)
            section += f"**{icon} {label}**：{insight}\n\n"

        # 获取政策类文章（支持多分类，如"技术,政策"）
        policy_articles = []
        for category, articles in by_category.items():
            if category and "政策" in category:
                policy_articles.extend(articles)

        # 过滤已展示的文章
        high_priority_policy = [
            a for a in policy_articles
            if a.get("priority") == "高" and a.get("url") not in displayed_urls
        ]

        if high_priority_policy:
            for i, article in enumerate(high_priority_policy, 1):
                section += self._format_article(i, article)
                displayed_urls.add(article['url'])
        else:
            # 优先显示中优先级，再显示低优先级（政策内容重要，多展示）
            med_priority_policy = [
                a for a in policy_articles
                if a.get("priority") == "中" and a.get("url") not in displayed_urls
            ]
            low_priority_policy = [
                a for a in policy_articles
                if a.get("priority") == "低" and a.get("url") not in displayed_urls
            ]

            # 合并中低优先级，最多显示5篇政策
            all_policy = med_priority_policy + low_priority_policy

            if all_policy:
                for i, article in enumerate(all_policy[:5], 1):
                    section += self._format_article(i, article)
                    displayed_urls.add(article['url'])
            else:
                section += "*本周暂无重点政策法规*\n"

        section += "\n"
        return section

    def _generate_market_section(self, by_category: Dict, by_priority: Dict, displayed_urls: set, insight: str = "") -> str:
        """生成市场动态章节"""
        section = "## 四、市场动态\n\n"

        # 添加板块点评
        if insight:
            label = get_random_insight_label('市场动态', self.use_random_labels)
            icon = get_insight_icon(label)
            section += f"**{icon} {label}**：{insight}\n\n"

        # 获取市场类文章（支持多分类，如"技术,市场"）
        market_articles = []
        for category, articles in by_category.items():
            if category and "市场" in category:
                market_articles.extend(articles)

        # 过滤已展示的文章
        high_priority_market = [
            a for a in market_articles
            if a.get("priority") == "高" and a.get("url") not in displayed_urls
        ]

        if high_priority_market:
            for i, article in enumerate(high_priority_market, 1):
                section += self._format_article(i, article)
                displayed_urls.add(article['url'])
        else:
            # 如果没有高优先级，显示中优先级
            med_priority_market = [
                a for a in market_articles
                if a.get("priority") == "中" and a.get("url") not in displayed_urls
            ]
            if med_priority_market:
                for i, article in enumerate(med_priority_market[:3], 1):
                    section += self._format_article(i, article)
                    displayed_urls.add(article['url'])
            else:
                section += "*本周暂无重点市场动态*\n"

        section += "\n"
        return section

    def _generate_other_section(self, by_category: Dict, by_priority: Dict, displayed_urls: set, insight: str = "") -> str:
        """生成其他动态章节"""
        section = "## 五、其他动态\n\n"

        # 添加板块点评
        if insight:
            label = get_random_insight_label('其他动态', self.use_random_labels)
            icon = get_insight_icon(label)
            section += f"**{icon} {label}**：{insight}\n\n"

        # 收集中低优先级的其他文章（排除已详细展示的文章）
        all_categories = ["投资", "技术", "政策", "市场"]
        other_articles = []

        # 收集所有中低优先级文章，排除已展示的
        for category in all_categories:
            articles = by_category.get(category, [])
            med_low_priority = [
                a for a in articles
                if a.get("priority") in ["中", "低"] and a['url'] not in displayed_urls
            ]
            other_articles.extend(med_low_priority)

        # 按评分排序
        other_articles.sort(key=lambda x: x.get("score", 0), reverse=True)

        if other_articles[:5]:
            for i, article in enumerate(other_articles[:5], 1):
                # 简化格式，只显示标题和来源
                section += f"{i}. **{article['title']}**  \n"
                section += f"   【{article.get('category', '其他')}】{article['source']} | {article.get('publish_date', '')} | [详情]({article['url']})\n\n"
        else:
            section += "*暂无其他动态*\n"

        section += "\n"
        return section

    def _generate_statistics(self, articles: List[Dict]) -> str:
        """生成统计信息"""
        section = "---\n\n"
        section += "## 📊 本周统计\n\n"

        # 按优先级统计
        by_priority = self.group_by_priority(articles)
        section += f"- **总文章数**: {len(articles)}\n"
        section += f"- **高优先级**: {len(by_priority.get('高', []))}\n"
        section += f"- **中优先级**: {len(by_priority.get('中', []))}\n"
        section += f"- **低优先级**: {len(by_priority.get('低', []))}\n\n"

        # 按分类统计
        by_category = self.group_by_category(articles)
        section += "**分类分布**:\n"
        for category in ["投资", "技术", "政策", "市场"]:
            count = len(by_category.get(category, []))
            if count > 0:
                section += f"- {category}: {count}篇\n"

        section += "\n---\n\n"
        section += "*本周报由IDC行业竞争情报系统自动生成*\n"

        return section

    def _format_article(self, index: int, article: Dict) -> str:
        """
        格式化单篇文章

        Args:
            index: 序号
            article: 文章数据

        Returns:
            格式化后的文章内容
        """
        output = f"### {index}. {article['title']}\n\n"

        # 元数据行
        metadata = f"**【{article.get('category', '其他')}】** {article['source']} | "
        metadata += f"{article.get('publish_date', '')} | "
        metadata += f"评分: {article.get('score', 0)}\n\n"
        output += metadata

        # 摘要
        summary = article.get("summary", "")
        if summary:
            output += f"{summary}\n\n"

        # 链接
        output += f"[查看详情]({article['url']})\n\n"

        return output

    def _generate_empty_report(self) -> str:
        """生成空报告"""
        return """# IDC行业周报

**报告日期**: {today}

本周暂无符合条件的文章数据。

---

*本周报由IDC行业竞争情报系统自动生成*
""".format(
            today=date.today().strftime("%Y年%m月%d日")
        )

    def generate_and_save(
        self,
        output_path: str,
        days: int = 7,
        generate_html: bool = True,
        generate_pdf: bool = None
    ) -> Dict[str, Optional[str]]:
        """
        生成周报并保存到文件

        Args:
            output_path: Markdown输出文件路径
            days: 统计天数
            generate_html: 是否生成HTML文件
            generate_pdf: 是否生成PDF文件（None则从环境变量读取）

        Returns:
            生成的文件路径字典 {
                'markdown': 'path/to/report.md',
                'html': 'path/to/report.html' or None,
                'pdf': 'path/to/report.pdf' or None
            }
        """
        result = {
            'markdown': None,
            'html': None,
            'pdf': None
        }

        try:
            # 生成Markdown周报
            report = self.generate_report(days=days)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report)

            result['markdown'] = output_path
            logger.info(f"✓ Markdown周报已保存: {output_path}")

            # 生成HTML文件
            if generate_html:
                html_path = output_path.replace('.md', '.html')
                try:
                    from src.notification.email_template_v2 import generate_html_report

                    html_content = generate_html_report(report)

                    with open(html_path, "w", encoding="utf-8") as f:
                        f.write(html_content)

                    result['html'] = html_path
                    logger.info(f"✓ HTML周报已保存: {html_path}")

                    # 生成PDF文件
                    if generate_pdf is None:
                        generate_pdf = os.getenv('PDF_ENABLED', 'true').lower() == 'true'

                    if generate_pdf:
                        try:
                            from src.reporting.pdf_generator import generate_weekly_report_pdf

                            output_dir = os.path.dirname(output_path) or "reports"
                            pdf_path = generate_weekly_report_pdf(
                                html_content=html_content,
                                output_dir=output_dir
                            )

                            if pdf_path:
                                result['pdf'] = pdf_path
                                logger.info(f"✓ PDF周报已保存: {pdf_path}")
                            else:
                                logger.warning("PDF生成失败，但周报生成流程继续")

                        except Exception as e:
                            logger.warning(f"PDF生成失败: {e}，但周报生成流程继续")

                except Exception as e:
                    logger.warning(f"HTML生成失败: {e}，但周报生成流程继续")

            return result

        except Exception as e:
            logger.error(f"保存周报失败: {e}")
            return result

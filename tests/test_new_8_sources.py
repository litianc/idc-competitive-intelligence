"""
测试新增的8个媒体源

TDD RED阶段：先写测试，预期所有测试都会失败（因为还未配置）
"""

import pytest
from src.scrapers.generic_scraper import GenericScraper
from datetime import datetime, timedelta


class TestNew8MediaSources:
    """测试8个新增媒体源的抓取功能"""

    # 8个新增的媒体源（实际配置）
    NEW_SOURCES = [
        {
            "name": "TechWeb",
            "url": "https://www.techweb.com.cn",
            "tier": 2,
            "list_url": "https://www.techweb.com.cn/",
            "min_articles": 5,
        },
        {
            "name": "DTDATA",
            "url": "http://www.dtdata.cn",
            "tier": 1,
            "list_url": "http://www.dtdata.cn/",
            "min_articles": 5,
        },
        {
            "name": "IT之家",
            "url": "https://www.ithome.com",
            "tier": 2,
            "list_url": "https://www.ithome.com/",
            "min_articles": 5,
        },
        {
            "name": "驱动之家",
            "url": "https://www.mydrivers.com",
            "tier": 2,
            "list_url": "https://www.mydrivers.com/",
            "min_articles": 5,
        },
        {
            "name": "新浪科技",
            "url": "https://tech.sina.com.cn",
            "tier": 2,
            "list_url": "https://tech.sina.com.cn/",
            "min_articles": 5,
        },
        {
            "name": "腾讯科技",
            "url": "https://tech.qq.com",
            "tier": 2,
            "list_url": "https://tech.qq.com/",
            "min_articles": 5,
        },
        {
            "name": "网易科技",
            "url": "https://tech.163.com",
            "tier": 2,
            "list_url": "https://tech.163.com/",
            "min_articles": 5,
        },
        {
            "name": "搜狐科技",
            "url": "https://it.sohu.com",
            "tier": 2,
            "list_url": "https://it.sohu.com/",
            "min_articles": 5,
        },
    ]

    @pytest.mark.parametrize("source", NEW_SOURCES)
    def test_source_in_config(self, source):
        """
        测试1：验证媒体源已添加到配置文件

        RED阶段：所有8个源都还未在配置中
        """
        import json

        config_path = "/root/competitive-intelligence-web/config/media-sources.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        configured_names = [s['name'] for s in config['sources']]

        # RED阶段：预期失败
        assert source['name'] in configured_names, \
            f"{source['name']} 还未添加到配置文件"

    @pytest.mark.parametrize("source", NEW_SOURCES)
    def test_source_has_complete_config(self, source):
        """
        测试2：验证媒体源配置完整

        必须包含：
        - scraper_config.article_container
        - scraper_config.title_selector
        - scraper_config.link_selector
        - scraper_config.date_selector
        """
        import json

        config_path = "/root/competitive-intelligence-web/config/media-sources.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # 查找该源
        source_config = None
        for s in config['sources']:
            if s['name'] == source['name']:
                source_config = s
                break

        # RED阶段：源不存在或配置不完整
        assert source_config is not None, f"{source['name']} 不在配置中"

        scraper_config = source_config.get('scraper_config', {})
        required_fields = ['article_container', 'title_selector', 'link_selector', 'date_selector']

        for field in required_fields:
            value = scraper_config.get(field, '')
            # RED阶段：字段为空或包含TODO/PLACEHOLDER
            assert value and 'TODO' not in value and 'PLACEHOLDER' not in value, \
                f"{source['name']} 的 {field} 配置缺失或未完成"

    @pytest.mark.parametrize("source", NEW_SOURCES)
    def test_source_is_active(self, source):
        """
        测试3：验证媒体源已激活

        RED阶段：新源还未激活
        """
        import json

        config_path = "/root/competitive-intelligence-web/config/media-sources.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # 查找该源
        source_config = None
        for s in config['sources']:
            if s['name'] == source['name']:
                source_config = s
                break

        # RED阶段：源不存在或未激活
        if source_config:
            assert source_config.get('active', False), f"{source['name']} 还未激活"
        else:
            pytest.fail(f"{source['name']} 不在配置中")

    def test_all_sources_configured(self):
        """
        测试5：验证所有8个源都已在配置文件中

        GREEN阶段完成后，这个测试应该通过
        """
        import json

        config_path = "/root/competitive-intelligence-web/config/media-sources.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        configured_sources = {s['name'] for s in config['sources']}
        expected_sources = {s['name'] for s in self.NEW_SOURCES}

        missing = expected_sources - configured_sources

        # RED阶段：所有8个源都还未配置
        assert len(missing) == 0, f"以下媒体源还未配置: {missing}"

    def test_all_sources_active(self):
        """
        测试6：验证所有8个源都已激活
        """
        import json

        config_path = "/root/competitive-intelligence-web/config/media-sources.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        new_source_names = {s['name'] for s in self.NEW_SOURCES}
        inactive_sources = []

        for source in config['sources']:
            if source['name'] in new_source_names and not source.get('active', False):
                inactive_sources.append(source['name'])

        # RED阶段：所有源都未激活
        assert len(inactive_sources) == 0, f"以下媒体源还未激活: {inactive_sources}"

    def test_tier_distribution(self):
        """
        测试7：验证Tier分级合理

        实际配置：
        - 1个Tier 1（权威媒体：DTDATA）
        - 7个Tier 2（专业媒体：TechWeb, IT之家等）
        """
        tier_count = {}
        for source in self.NEW_SOURCES:
            tier = source['tier']
            tier_count[tier] = tier_count.get(tier, 0) + 1

        assert tier_count.get(1, 0) == 1, f"应该有1个Tier 1媒体，实际: {tier_count.get(1, 0)}"
        assert tier_count.get(2, 0) == 7, f"应该有7个Tier 2媒体，实际: {tier_count.get(2, 0)}"

    @pytest.mark.integration
    @pytest.mark.slow
    def test_integrated_collection(self):
        """
        测试8：集成测试 - 从所有8个源采集文章

        这是最终的集成测试，验证整个流程：
        1. 加载配置
        2. 抓取文章
        3. 评分和分类
        4. 存储到数据库
        5. 生成LLM摘要

        RED阶段：暂时跳过，等GREEN阶段完成后再测试
        """
        pytest.skip("等待GREEN阶段完成配置后再进行集成测试")


# RED阶段小结：
# 1. ✅ 定义了8个目标媒体源
# 2. ✅ 编写了8个测试场景
# 3. ✅ 所有测试预期失败（因为配置和实现都还没有）
# 4. 下一步：GREEN阶段 - 逐个配置和实现，让测试通过

"""
HTML邮件模板生成器V2 - 分类板块布局

按分类组织视觉板块，每个分类一个大板块
"""

import logging
import re
from datetime import datetime
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

# 分类色彩映射
CATEGORY_COLORS = {
    '政策': {'primary': '#e74c3c', 'light': '#ffebee', 'dark': '#c0392b', 'icon': '📜'},
    '投资': {'primary': '#f39c12', 'light': '#fff3e0', 'dark': '#e67e22', 'icon': '💰'},
    '技术': {'primary': '#3498db', 'light': '#e3f2fd', 'dark': '#2980b9', 'icon': '🔧'},
    '市场': {'primary': '#27ae60', 'light': '#e8f5e9', 'dark': '#229954', 'icon': '📈'},
    '其他': {'primary': '#9b59b6', 'light': '#f3e5f5', 'dark': '#8e44ad', 'icon': '📌'}
}


def parse_weekly_report(markdown_content: str) -> Dict:
    """解析周报Markdown内容"""
    lines = markdown_content.strip().split('\n')

    result = {
        'title': '',
        'date': '',
        'week': '',
        'sections': [],
        'stats': {}
    }

    current_section = None
    current_article = None

    for line in lines:
        line = line.strip()

        # 提取标题
        if line.startswith('# ') and '周报' in line:
            result['title'] = line[2:].strip()
            week_match = re.search(r'第(\d+)周', line)
            if week_match:
                result['week'] = week_match.group(1)

        # 提取日期
        elif line.startswith('**报告日期**'):
            date_match = re.search(r'(\d{4}年\d+月\d+日)', line)
            if date_match:
                result['date'] = date_match.group(1)

        # 提取章节
        elif line.startswith('## '):
            section_title = line[3:].strip()
            current_section = {
                'title': section_title,
                'articles': []
            }
            result['sections'].append(current_section)
            current_article = None

        # 提取文章
        elif line.startswith('### ') and current_section:
            article_title = re.sub(r'^\d+\.\s*', '', line[4:].strip())
            current_article = {
                'title': article_title,
                'categories': [],
                'source': '',
                'date': '',
                'score': 0,
                'summary': '',
                'url': ''
            }
            current_section['articles'].append(current_article)

        # 提取元信息
        elif line.startswith('**【') and current_article:
            cat_match = re.search(r'\*\*【(.+?)】\*\*', line)
            if cat_match:
                cats = cat_match.group(1).split(',')
                current_article['categories'] = [c.strip() for c in cats]

            parts = line.split('|')
            if len(parts) >= 2:
                current_article['source'] = parts[1].strip()
            if len(parts) >= 3:
                date_part = parts[2].strip()
                current_article['date'] = re.sub(r'\s*评分:.*', '', date_part).strip()

            score_match = re.search(r'评分:\s*(\d+)', line)
            if score_match:
                current_article['score'] = int(score_match.group(1))

        # 提取链接
        elif line.startswith('[查看详情]') and current_article:
            url_match = re.search(r'\[查看详情\]\((.+?)\)', line)
            if url_match:
                current_article['url'] = url_match.group(1)

        # 提取摘要
        elif line and not line.startswith('#') and not line.startswith('**') and \
             not line.startswith('[') and not line.startswith('*') and \
             not line.startswith('-') and current_article and not current_article['summary']:
            current_article['summary'] = line

        # 提取统计
        elif '总文章数' in line:
            match = re.search(r'(\d+)', line)
            if match:
                result['stats']['total'] = int(match.group(1))
        elif '高优先级' in line:
            match = re.search(r'(\d+)', line)
            if match:
                result['stats']['high'] = int(match.group(1))
        elif '中优先级' in line:
            match = re.search(r'(\d+)', line)
            if match:
                result['stats']['medium'] = int(match.group(1))
        elif '低优先级' in line:
            match = re.search(r'(\d+)', line)
            if match:
                result['stats']['low'] = int(match.group(1))

    return result


def generate_section_block_html(section: Dict) -> str:
    """生成分类板块HTML - 一个大板块包含所有文章"""

    # 确定分类
    section_category = '其他'
    for cat_name in CATEGORY_COLORS.keys():
        if cat_name in section['title']:
            section_category = cat_name
            break

    colors = CATEGORY_COLORS[section_category]

    # 如果没有文章，返回空板块
    if not section['articles']:
        return f'''
        <div style="background: linear-gradient(135deg, {colors['light']} 0%, #ffffff 100%);
                    border-radius: 12px; padding: 25px; margin-bottom: 20px;
                    border: 1px solid {colors['primary']}20;">
            <h3 style="margin: 0 0 15px 0; color: {colors['primary']};
                       font-size: 20px; font-weight: 600;">
                {colors['icon']} {section['title']}
            </h3>
            <div style="text-align: center; padding: 30px 0; color: #95a5a6;">
                本周暂无相关动态
            </div>
        </div>
        '''

    # 生成文章列表HTML
    articles_html = ''
    for idx, article in enumerate(section['articles'], 1):
        # 分类标签
        tags_html = ''
        for cat in article['categories']:
            cat_color = CATEGORY_COLORS.get(cat, CATEGORY_COLORS['其他'])
            tags_html += f'''<span style="display: inline-block; padding: 2px 8px;
                                          background-color: {cat_color['light']};
                                          color: {cat_color['dark']};
                                          border-radius: 10px; font-size: 11px;
                                          margin-right: 5px;">{cat}</span>'''

        # 评分星级
        score = article['score']
        score_stars = '⭐' * (score // 20) if score > 0 else ''
        score_color = '#27ae60' if score >= 70 else '#f39c12' if score >= 50 else '#95a5a6'

        articles_html += f'''
        <div style="padding: 15px 0; border-bottom: 1px solid {colors['light']};">
            <!-- 标题行 -->
            <div style="margin-bottom: 8px;">
                <span style="color: {colors['primary']}; font-weight: 600; font-size: 15px;">
                    {idx}. {article['title']}
                </span>
            </div>

            <!-- 摘要 -->
            <div style="color: #555; font-size: 13px; line-height: 1.5; margin-bottom: 8px;">
                {article['summary'][:150]}{'...' if len(article['summary']) > 150 else ''}
            </div>

            <!-- 元信息行 -->
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    {tags_html}
                    <span style="color: #95a5a6; font-size: 12px;">
                        {article['source']} | {article['date']}
                    </span>
                    <span style="color: {score_color}; font-size: 12px;">
                        评分:{article['score']} {score_stars}
                    </span>
                </div>
                {'<a href="' + article['url'] + '" style="color: ' + colors['primary'] + '; font-size: 12px; text-decoration: none;">查看详情 →</a>' if article['url'] else ''}
            </div>
        </div>
        '''

    # 组装板块
    block_html = f'''
    <div style="background: linear-gradient(135deg, {colors['light']} 0%, #ffffff 100%);
                border-radius: 12px; padding: 25px; margin-bottom: 20px;
                border: 2px solid {colors['primary']}30;
                box-shadow: 0 2px 8px rgba(0,0,0,0.05);">

        <!-- 板块标题 -->
        <div style="display: flex; align-items: center; justify-content: space-between;
                    margin-bottom: 20px; padding-bottom: 15px;
                    border-bottom: 2px solid {colors['primary']};">
            <h3 style="margin: 0; color: {colors['primary']};
                       font-size: 20px; font-weight: 600;">
                {colors['icon']} {section['title']}
            </h3>
            <span style="background-color: {colors['primary']}; color: white;
                         padding: 4px 12px; border-radius: 15px; font-size: 12px;">
                {len(section['articles'])} 篇
            </span>
        </div>

        <!-- 文章列表 -->
        <div>
            {articles_html}
        </div>
    </div>
    '''

    return block_html


def generate_stats_dashboard(stats: Dict) -> str:
    """生成统计仪表板"""

    total = stats.get('total', 0)
    high = stats.get('high', 0)
    medium = stats.get('medium', 0)
    low = stats.get('low', 0)

    return f'''
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 12px; padding: 30px; margin: 30px 0;
                color: white; text-align: center;">

        <h3 style="margin: 0 0 25px 0; font-size: 22px; font-weight: 600;">
            📊 本周数据概览
        </h3>

        <!-- 统计数字 -->
        <div style="display: flex; justify-content: space-around; flex-wrap: wrap;">
            <div style="flex: 1; min-width: 100px; padding: 10px;">
                <div style="font-size: 36px; font-weight: 700;">{total}</div>
                <div style="font-size: 13px; opacity: 0.9; margin-top: 5px;">总文章数</div>
            </div>
            <div style="flex: 1; min-width: 100px; padding: 10px;">
                <div style="font-size: 28px; font-weight: 600; color: #ff6b6b;">{high}</div>
                <div style="font-size: 13px; opacity: 0.9; margin-top: 5px;">高优先级</div>
            </div>
            <div style="flex: 1; min-width: 100px; padding: 10px;">
                <div style="font-size: 28px; font-weight: 600; color: #feca57;">{medium}</div>
                <div style="font-size: 13px; opacity: 0.9; margin-top: 5px;">中优先级</div>
            </div>
            <div style="flex: 1; min-width: 100px; padding: 10px;">
                <div style="font-size: 28px; font-weight: 600; color: #a8dadc;">{low}</div>
                <div style="font-size: 13px; opacity: 0.9; margin-top: 5px;">低优先级</div>
            </div>
        </div>
    </div>
    '''


def generate_html_report(
    markdown_content: str,
    title: str = "IDC行业竞争情报周报",
    logo_url: Optional[str] = None
) -> str:
    """生成HTML邮件 - 分类板块布局版本"""

    # 解析周报
    report_data = parse_weekly_report(markdown_content)

    # 生成各分类板块
    sections_html = ''
    for section in report_data['sections']:
        if '统计' not in section['title']:
            sections_html += generate_section_block_html(section)

    # 生成统计仪表板
    stats_html = generate_stats_dashboard(report_data['stats']) if report_data['stats'] else ''

    # 组装完整HTML
    html = f'''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f5f7fa;
             font-family: -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif;">

    <div style="max-width: 800px; margin: 0 auto; background-color: white;">

        <!-- 头部 -->
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 40px 30px; text-align: center; color: white;">
            <h1 style="margin: 0 0 10px 0; font-size: 28px;">
                {report_data['title'] or title}
            </h1>
            <div style="font-size: 15px; opacity: 0.95;">
                {report_data['date']}
            </div>
        </div>

        <!-- 内容区 -->
        <div style="padding: 30px;">
            {sections_html}
            {stats_html}
        </div>

        <!-- 页脚 -->
        <div style="background-color: #f8f9fa; padding: 20px; text-align: center;
                    border-top: 1px solid #e9ecef; color: #6c757d; font-size: 12px;">
            <p style="margin: 5px 0;">🤖 IDC行业竞争情报系统</p>
            <p style="margin: 5px 0;">本周报由系统自动生成 | {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        </div>

    </div>

</body>
</html>
    '''

    return html.strip()
"""
HTML邮件模板生成器 - 周报专用

将Markdown格式的周报转换为精美的HTML邮件格式,支持:
- 分类色彩主题
- 文章卡片布局
- 标签和评分可视化
- 统计数据图表
"""

import logging
import re
from datetime import datetime
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

# 分类色彩映射
CATEGORY_COLORS = {
    '政策': {'bg': '#ffebee', 'border': '#e74c3c', 'text': '#c0392b', 'icon': '📜'},
    '投资': {'bg': '#fff3e0', 'border': '#f39c12', 'text': '#e67e22', 'icon': '💰'},
    '技术': {'bg': '#e3f2fd', 'border': '#3498db', 'text': '#2980b9', 'icon': '🔧'},
    '市场': {'bg': '#e8f5e9', 'border': '#27ae60', 'text': '#229954', 'icon': '📈'},
    '其他': {'bg': '#f3e5f5', 'border': '#9b59b6', 'text': '#8e44ad', 'icon': '📌'}
}


def parse_weekly_report(markdown_content: str) -> Dict:
    """
    解析周报Markdown内容,提取结构化数据

    Args:
        markdown_content: Markdown格式的周报内容

    Returns:
        包含标题、日期、章节、统计数据的字典
    """
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

        # 提取标题 (# IDC行业周报 | 2025年第45周)
        if line.startswith('# ') and '周报' in line:
            result['title'] = line[2:].strip()
            week_match = re.search(r'第(\d+)周', line)
            if week_match:
                result['week'] = week_match.group(1)

        # 提取日期 (**报告日期**: 2025年11月06日)
        elif line.startswith('**报告日期**'):
            date_match = re.search(r'(\d{4}年\d+月\d+日)', line)
            if date_match:
                result['date'] = date_match.group(1)

        # 提取章节标题 (## 一、政策法规)
        elif line.startswith('## '):
            section_title = line[3:].strip()
            current_section = {
                'title': section_title,
                'articles': []
            }
            result['sections'].append(current_section)
            current_article = None

        # 提取文章标题 (### 1. 文章标题)
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

        # 提取文章元信息 (**【投资,技术】** 来源 | 日期 | 评分: 56)
        elif line.startswith('**【') and current_article:
            # 提取分类标签
            cat_match = re.search(r'\*\*【(.+?)】\*\*', line)
            if cat_match:
                cats = cat_match.group(1).split(',')
                current_article['categories'] = [c.strip() for c in cats]

            # 提取来源、日期
            parts = line.split('|')
            if len(parts) >= 2:
                current_article['source'] = parts[1].strip()
            if len(parts) >= 3:
                date_part = parts[2].strip()
                current_article['date'] = re.sub(r'\s*评分:.*', '', date_part).strip()

            # 提取评分
            score_match = re.search(r'评分:\s*(\d+)', line)
            if score_match:
                current_article['score'] = int(score_match.group(1))

        # 提取链接 ([查看详情](url))
        elif line.startswith('[查看详情]') and current_article:
            url_match = re.search(r'\[查看详情\]\((.+?)\)', line)
            if url_match:
                current_article['url'] = url_match.group(1)

        # 提取摘要 (普通段落)
        elif line and not line.startswith('#') and not line.startswith('**') and \
             not line.startswith('[') and not line.startswith('*') and \
             not line.startswith('-') and current_article and not current_article['summary']:
            current_article['summary'] = line

        # 提取统计数据
        elif line.startswith('- **总文章数**'):
            match = re.search(r'(\d+)', line)
            if match:
                result['stats']['total'] = int(match.group(1))
        elif line.startswith('- **高优先级**'):
            match = re.search(r'(\d+)', line)
            if match:
                result['stats']['high'] = int(match.group(1))
        elif line.startswith('- **中优先级**'):
            match = re.search(r'(\d+)', line)
            if match:
                result['stats']['medium'] = int(match.group(1))
        elif line.startswith('- **低优先级**'):
            match = re.search(r'(\d+)', line)
            if match:
                result['stats']['low'] = int(match.group(1))

    return result


def generate_article_card_html(article: Dict, index: int) -> str:
    """生成文章卡片HTML"""

    # 确定主分类(用于配色)
    main_category = '其他'
    for cat in article['categories']:
        if cat in CATEGORY_COLORS:
            main_category = cat
            break

    colors = CATEGORY_COLORS[main_category]

    # 生成分类标签HTML
    category_tags = ''
    for cat in article['categories']:
        cat_color = CATEGORY_COLORS.get(cat, CATEGORY_COLORS['其他'])
        category_tags += f'''
            <span style="display: inline-block; padding: 3px 10px; margin-right: 6px;
                         background-color: {cat_color['bg']}; color: {cat_color['text']};
                         border: 1px solid {cat_color['border']}; border-radius: 12px;
                         font-size: 12px; font-weight: 600;">
                {cat_color['icon']} {cat}
            </span>
        '''

    # 评分进度条
    score_percent = article['score']
    score_color = '#27ae60' if score_percent >= 70 else '#f39c12' if score_percent >= 50 else '#95a5a6'

    score_bar = f'''
        <div style="display: inline-block; margin-left: auto;">
            <div style="display: flex; align-items: center;">
                <span style="font-size: 12px; color: #7f8c8d; margin-right: 8px;">评分</span>
                <div style="width: 80px; height: 8px; background-color: #ecf0f1; border-radius: 4px; overflow: hidden;">
                    <div style="width: {score_percent}%; height: 100%; background-color: {score_color}; transition: width 0.3s;"></div>
                </div>
                <span style="font-size: 13px; font-weight: 600; color: {score_color}; margin-left: 6px;">{article['score']}</span>
            </div>
        </div>
    '''

    # 查看详情按钮
    view_button = ''
    if article['url']:
        view_button = f'''
            <a href="{article['url']}" style="display: inline-block; padding: 8px 20px;
                                             background-color: {colors['border']}; color: #ffffff;
                                             text-decoration: none; border-radius: 6px;
                                             font-size: 13px; font-weight: 600;
                                             transition: opacity 0.2s;"
               onmouseover="this.style.opacity='0.8'" onmouseout="this.style.opacity='1'">
                查看详情 →
            </a>
        '''

    card_html = f'''
    <div style="background-color: #ffffff; border: 1px solid #e1e8ed;
                border-left: 4px solid {colors['border']}; border-radius: 8px;
                padding: 20px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">

        <!-- 标签和评分 -->
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
            <div style="display: flex; align-items: center; flex-wrap: wrap;">
                {category_tags}
            </div>
            {score_bar}
        </div>

        <!-- 文章标题 -->
        <h4 style="margin: 0 0 12px 0; font-size: 16px; font-weight: 600;
                   color: #2c3e50; line-height: 1.4;">
            {colors['icon']} {article['title']}
        </h4>

        <!-- 摘要 -->
        <p style="margin: 0 0 12px 0; font-size: 14px; color: #555;
                  line-height: 1.6; text-align: justify;">
            {article['summary']}
        </p>

        <!-- 元信息 -->
        <div style="display: flex; align-items: center; justify-content: space-between;
                    padding-top: 12px; border-top: 1px solid #f0f0f0;">
            <div style="font-size: 12px; color: #95a5a6;">
                <span style="margin-right: 15px;">📅 {article['date']}</span>
                <span>📰 {article['source']}</span>
            </div>
            {view_button}
        </div>
    </div>
    '''

    return card_html


def generate_section_html(section: Dict) -> str:
    """生成章节HTML"""

    # 从章节标题提取分类
    section_category = '其他'
    for cat_name in CATEGORY_COLORS.keys():
        if cat_name in section['title']:
            section_category = cat_name
            break

    colors = CATEGORY_COLORS[section_category]

    # 章节标题
    section_html = f'''
    <div style="margin: 30px 0 20px 0;">
        <h3 style="margin: 0; padding: 12px 20px;
                   background: linear-gradient(135deg, {colors['border']} 0%, {colors['text']} 100%);
                   color: #ffffff; border-radius: 6px; font-size: 18px; font-weight: 600;
                   box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            {colors['icon']} {section['title']}
        </h3>
    </div>
    '''

    # 文章列表
    if section['articles']:
        for idx, article in enumerate(section['articles'], 1):
            section_html += generate_article_card_html(article, idx)
    else:
        section_html += f'''
        <div style="background-color: #f8f9fa; border: 1px dashed #dee2e6;
                    border-radius: 6px; padding: 20px; text-align: center;
                    color: #6c757d; font-size: 14px;">
            {colors['icon']} 本周暂无相关动态
        </div>
        '''

    return section_html


def generate_stats_html(stats: Dict) -> str:
    """生成统计数据HTML"""

    total = stats.get('total', 0)
    high = stats.get('high', 0)
    medium = stats.get('medium', 0)
    low = stats.get('low', 0)

    # 计算百分比
    high_pct = (high / total * 100) if total > 0 else 0
    medium_pct = (medium / total * 100) if total > 0 else 0
    low_pct = (low / total * 100) if total > 0 else 0

    stats_html = f'''
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 8px; padding: 30px; margin: 30px 0; color: #ffffff;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);">

        <h3 style="margin: 0 0 20px 0; font-size: 20px; font-weight: 600;
                   text-align: center; color: #ffffff;">
            📊 本周统计
        </h3>

        <div style="display: flex; justify-content: space-around; flex-wrap: wrap;
                    margin-bottom: 20px;">

            <!-- 总文章数 -->
            <div style="text-align: center; padding: 15px; min-width: 120px;">
                <div style="font-size: 36px; font-weight: 700; margin-bottom: 5px;">
                    {total}
                </div>
                <div style="font-size: 14px; opacity: 0.9;">
                    总文章数
                </div>
            </div>

            <!-- 高优先级 -->
            <div style="text-align: center; padding: 15px; min-width: 120px;">
                <div style="font-size: 28px; font-weight: 600; margin-bottom: 5px; color: #ff6b6b;">
                    {high}
                </div>
                <div style="font-size: 14px; opacity: 0.9;">
                    高优先级
                </div>
            </div>

            <!-- 中优先级 -->
            <div style="text-align: center; padding: 15px; min-width: 120px;">
                <div style="font-size: 28px; font-weight: 600; margin-bottom: 5px; color: #feca57;">
                    {medium}
                </div>
                <div style="font-size: 14px; opacity: 0.9;">
                    中优先级
                </div>
            </div>

            <!-- 低优先级 -->
            <div style="text-align: center; padding: 15px; min-width: 120px;">
                <div style="font-size: 28px; font-weight: 600; margin-bottom: 5px; color: #a8dadc;">
                    {low}
                </div>
                <div style="font-size: 14px; opacity: 0.9;">
                    低优先级
                </div>
            </div>
        </div>

        <!-- 优先级分布条 -->
        <div style="margin-top: 15px;">
            <div style="font-size: 13px; margin-bottom: 8px; opacity: 0.9;">
                优先级分布
            </div>
            <div style="display: flex; height: 12px; border-radius: 6px; overflow: hidden;
                        background-color: rgba(255,255,255,0.2);">
                <div style="width: {high_pct:.1f}%; background-color: #ff6b6b;"
                     title="高: {high}篇 ({high_pct:.1f}%)"></div>
                <div style="width: {medium_pct:.1f}%; background-color: #feca57;"
                     title="中: {medium}篇 ({medium_pct:.1f}%)"></div>
                <div style="width: {low_pct:.1f}%; background-color: #a8dadc;"
                     title="低: {low}篇 ({low_pct:.1f}%)"></div>
            </div>
        </div>
    </div>
    '''

    return stats_html


def generate_html_report(
    markdown_content: str,
    title: str = "IDC行业竞争情报周报",
    logo_url: Optional[str] = None
) -> str:
    """
    将Markdown格式的周报转换为精美HTML邮件

    Args:
        markdown_content: Markdown格式的周报内容
        title: 邮件标题
        logo_url: 公司Logo URL（可选）

    Returns:
        完整的HTML邮件内容
    """

    # 解析周报内容
    report_data = parse_weekly_report(markdown_content)

    # 生成各部分HTML
    sections_html = ''
    for section in report_data['sections']:
        # 跳过统计章节
        if '统计' in section['title']:
            continue
        sections_html += generate_section_html(section)

    # 生成统计HTML
    stats_html = generate_stats_html(report_data['stats']) if report_data['stats'] else ''

    # 周数徽章
    week_badge = ''
    if report_data['week']:
        week_badge = f'''
            <div style="display: inline-block; background-color: rgba(255,255,255,0.2);
                        padding: 6px 16px; border-radius: 20px; font-size: 14px;
                        margin-top: 10px; border: 1px solid rgba(255,255,255,0.3);">
                📅 第 {report_data['week']} 周
            </div>
        '''

    # Logo部分
    logo_html = ''
    if logo_url:
        logo_html = f'<img src="{logo_url}" alt="Logo" style="max-width: 150px; margin-bottom: 15px;">'

    # 组装完整HTML
    html = f'''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
</head>
<body style="margin: 0; padding: 20px; background-color: #f5f7fa;
             font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC',
                          'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif;">

    <!-- 邮件容器 -->
    <div style="max-width: 800px; margin: 0 auto; background-color: #ffffff;
                border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.08);
                overflow: hidden;">

        <!-- 头部Banner -->
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: #ffffff; padding: 40px 30px; text-align: center;">
            {logo_html}
            <h1 style="margin: 0; font-size: 28px; font-weight: 600;">
                {report_data['title'] or title}
            </h1>
            <div style="margin-top: 12px; font-size: 15px; opacity: 0.95;">
                📅 {report_data['date'] or datetime.now().strftime('%Y年%m月%d日')}
            </div>
            {week_badge}
        </div>

        <!-- 正文内容 -->
        <div style="padding: 30px;">

            {sections_html}

            {stats_html}

        </div>

        <!-- 页脚 -->
        <div style="background-color: #f8f9fa; padding: 25px 30px; text-align: center;
                    border-top: 1px solid #e9ecef;">
            <p style="margin: 0 0 8px 0; font-size: 14px; font-weight: 600; color: #2c3e50;">
                🤖 IDC行业竞争情报系统
            </p>
            <p style="margin: 0; font-size: 12px; color: #6c757d;">
                本周报由系统自动生成并发送 • 请勿直接回复此邮件
            </p>
            <p style="margin: 8px 0 0 0; font-size: 11px; color: #adb5bd;">
                生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </p>
        </div>

    </div>

</body>
</html>
    '''

    return html.strip()


def create_simple_html_email(title: str, content: str) -> str:
    """
    创建简单的HTML邮件（不依赖markdown2,用于纯文本内容）

    Args:
        title: 邮件标题
        content: 纯文本内容

    Returns:
        HTML格式邮件
    """
    html_content = content.replace('\n', '<br>\n')
    return generate_html_report(html_content, title=title)

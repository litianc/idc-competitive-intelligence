"""
PDF生成器

使用Playwright将HTML内容转换为PDF文件
"""

import logging
import os
from pathlib import Path
from typing import Optional, Dict
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)


class PDFGenerator:
    """HTML到PDF转换器"""

    def __init__(
        self,
        page_size: str = "A4",
        margin: str = "20mm",
        print_background: bool = True,
        display_header_footer: bool = True
    ):
        """
        初始化PDF生成器

        Args:
            page_size: 页面大小（A4, Letter等）
            margin: 页边距（如 "20mm"）
            print_background: 是否打印背景色和图片
            display_header_footer: 是否显示页眉页脚
        """
        self.page_size = page_size
        self.margin = margin
        self.print_background = print_background
        self.display_header_footer = display_header_footer

    def html_to_pdf(
        self,
        html_content: str,
        output_path: str,
        options: Optional[Dict] = None
    ) -> bool:
        """
        将HTML内容转换为PDF文件

        Args:
            html_content: HTML内容字符串
            output_path: PDF输出文件路径
            options: 自定义PDF选项（覆盖默认配置）

        Returns:
            是否成功生成PDF
        """
        try:
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

            # 在HTML中确保使用正确的字体声明
            # 不使用在线字体，使用系统已安装的中文字体和emoji字体
            if '<head>' in html_content:
                # 检查是否已经有字体样式
                if 'font-family' not in html_content or 'sans-serif' in html_content:
                    font_style = """
                <style>
                    body, * {
                        font-family: 'Noto Sans CJK SC', 'Source Han Sans CN', 'PingFang SC',
                                     'Microsoft YaHei', 'WenQuanYi Micro Hei', 'Hiragino Sans GB',
                                     'SimHei', 'STHeiti', sans-serif, 'Noto Color Emoji', 'Apple Color Emoji', 'Segoe UI Emoji' !important;
                    }
                </style>
                """
                    html_content = html_content.replace('</head>', font_style + '</head>')

            # 准备PDF选项
            pdf_options = self._build_pdf_options(output_path, options)

            # 使用Playwright生成PDF
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=['--font-render-hinting=none', '--disable-font-subpixel-positioning']
                )
                try:
                    page = browser.new_page()

                    # 设置HTML内容
                    page.set_content(html_content, wait_until='load')

                    # 等待页面渲染完成
                    page.wait_for_timeout(500)

                    # 生成PDF
                    page.pdf(**pdf_options)

                    logger.info(f"✓ PDF生成成功: {output_path}")
                    return True

                finally:
                    browser.close()

        except Exception as e:
            logger.error(f"✗ PDF生成失败: {e}", exc_info=True)
            return False

    def html_file_to_pdf(
        self,
        html_file_path: str,
        output_path: str,
        options: Optional[Dict] = None
    ) -> bool:
        """
        将HTML文件转换为PDF

        Args:
            html_file_path: HTML文件路径
            output_path: PDF输出文件路径
            options: 自定义PDF选项

        Returns:
            是否成功生成PDF
        """
        try:
            with open(html_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            return self.html_to_pdf(html_content, output_path, options)

        except Exception as e:
            logger.error(f"✗ 读取HTML文件失败: {e}")
            return False

    def _build_pdf_options(
        self,
        output_path: str,
        custom_options: Optional[Dict] = None
    ) -> Dict:
        """
        构建PDF生成选项

        Args:
            output_path: 输出文件路径
            custom_options: 自定义选项

        Returns:
            PDF选项字典
        """
        # 默认选项
        options = {
            'path': output_path,
            'format': self.page_size,
            'print_background': self.print_background,
            'margin': {
                'top': self.margin,
                'right': self.margin,
                'bottom': self.margin,
                'left': self.margin
            },
            'display_header_footer': self.display_header_footer,
        }

        # 添加页脚（页码）
        if self.display_header_footer:
            options['footer_template'] = """
                <div style="font-size: 10px; text-align: center; width: 100%;
                            color: #999; padding-top: 5px;">
                    第 <span class="pageNumber"></span> 页 / 共 <span class="totalPages"></span> 页
                </div>
            """
            options['header_template'] = '<div></div>'  # 空页眉

        # 合并自定义选项
        if custom_options:
            options.update(custom_options)

        return options

    @classmethod
    def from_env(cls) -> 'PDFGenerator':
        """
        从环境变量创建PDF生成器

        Returns:
            PDFGenerator实例
        """
        page_size = os.getenv('PDF_PAGE_SIZE', 'A4')
        margin = os.getenv('PDF_MARGIN', '20mm')
        print_background = os.getenv('PDF_PRINT_BACKGROUND', 'true').lower() == 'true'
        display_header_footer = os.getenv('PDF_DISPLAY_HEADER_FOOTER', 'true').lower() == 'true'

        return cls(
            page_size=page_size,
            margin=margin,
            print_background=print_background,
            display_header_footer=display_header_footer
        )


def generate_weekly_report_pdf(
    html_content: str,
    output_dir: str = "reports",
    filename: Optional[str] = None
) -> Optional[str]:
    """
    生成周报PDF（便捷函数）

    Args:
        html_content: HTML内容
        output_dir: 输出目录
        filename: PDF文件名（不指定则自动生成）

    Returns:
        生成的PDF文件路径，失败返回None
    """
    try:
        # 自动生成文件名
        if not filename:
            from datetime import date
            today = date.today()
            week_number = today.isocalendar()[1]
            filename = f"IDC周报_第{week_number}周_{today.strftime('%Y-%m-%d')}.pdf"

        # 确保文件名以.pdf结尾
        if not filename.endswith('.pdf'):
            filename += '.pdf'

        output_path = os.path.join(output_dir, filename)

        # 生成PDF
        generator = PDFGenerator.from_env()
        success = generator.html_to_pdf(html_content, output_path)

        if success:
            # 检查文件大小
            file_size = os.path.getsize(output_path)
            file_size_mb = file_size / (1024 * 1024)
            logger.info(f"  PDF文件大小: {file_size_mb:.2f} MB")

            # 警告文件过大
            if file_size_mb > 10:
                logger.warning(f"  ⚠️  PDF文件较大（{file_size_mb:.2f} MB），可能影响邮件发送")

            return output_path
        else:
            return None

    except Exception as e:
        logger.error(f"✗ 生成周报PDF失败: {e}")
        return None

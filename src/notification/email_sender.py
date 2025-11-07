"""
邮件发送模块

使用SMTP协议通过163邮箱发送HTML格式的周报邮件
"""

import logging
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from typing import List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class EmailSender:
    """邮件发送器"""

    def __init__(
        self,
        smtp_host: str = None,
        smtp_port: int = None,
        smtp_user: str = None,
        smtp_pass: str = None,
        use_ssl: bool = True
    ):
        """
        初始化邮件发送器

        Args:
            smtp_host: SMTP服务器地址（默认从环境变量读取）
            smtp_port: SMTP端口（默认从环境变量读取）
            smtp_user: 发件人邮箱（默认从环境变量读取）
            smtp_pass: 邮箱授权码（默认从环境变量读取）
            use_ssl: 是否使用SSL加密
        """
        # 从环境变量加载配置
        self.smtp_host = smtp_host or os.getenv('SMTP_HOST', 'smtp.163.com')
        self.smtp_port = smtp_port or int(os.getenv('SMTP_PORT', '465'))
        self.smtp_user = smtp_user or os.getenv('SMTP_USER', '')
        self.smtp_pass = smtp_pass or os.getenv('SMTP_PASS', '')
        self.use_ssl = use_ssl if use_ssl is not None else os.getenv('SMTP_SECURE', 'true').lower() == 'true'

        # 验证配置
        if not all([self.smtp_host, self.smtp_user, self.smtp_pass]):
            raise ValueError("邮件配置不完整，请检查环境变量: SMTP_HOST, SMTP_USER, SMTP_PASS")

        logger.info(f"邮件发送器已初始化: {self.smtp_user}@{self.smtp_host}:{self.smtp_port} (SSL: {self.use_ssl})")

    def send_html_email(
        self,
        subject: str,
        html_content: str,
        recipients: List[str],
        cc: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None
    ) -> bool:
        """
        发送HTML格式的邮件

        Args:
            subject: 邮件主题
            html_content: HTML格式的邮件正文
            recipients: 收件人列表
            cc: 抄送人列表
            attachments: 附件文件路径列表

        Returns:
            是否发送成功
        """
        try:
            # 创建邮件对象
            message = MIMEMultipart('alternative')
            message['From'] = Header(f"IDC竞争情报系统 <{self.smtp_user}>", 'utf-8')
            message['To'] = Header(', '.join(recipients), 'utf-8')
            message['Subject'] = Header(subject, 'utf-8')

            if cc:
                message['Cc'] = Header(', '.join(cc), 'utf-8')

            # 添加HTML正文
            html_part = MIMEText(html_content, 'html', 'utf-8')
            message.attach(html_part)

            # TODO: 添加附件支持（如果需要）

            # 连接SMTP服务器并发送
            all_recipients = recipients + (cc or [])

            if self.use_ssl:
                # 使用SSL连接
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=30) as server:
                    server.login(self.smtp_user, self.smtp_pass)
                    server.sendmail(self.smtp_user, all_recipients, message.as_string())
            else:
                # 使用TLS连接
                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_pass)
                    server.sendmail(self.smtp_user, all_recipients, message.as_string())

            logger.info(f"✓ 邮件发送成功: {subject}")
            logger.info(f"  收件人: {', '.join(recipients)}")
            if cc:
                logger.info(f"  抄送: {', '.join(cc)}")

            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"✗ SMTP认证失败: {e}")
            logger.error("  请检查邮箱账号和授权码是否正确")
            return False

        except smtplib.SMTPException as e:
            logger.error(f"✗ SMTP错误: {e}")
            return False

        except Exception as e:
            logger.error(f"✗ 邮件发送失败: {e}", exc_info=True)
            return False

    def send_weekly_report(
        self,
        report_content: str,
        recipients: List[str] = None,
        report_date: str = None,
        use_block_layout: bool = True
    ) -> bool:
        """
        发送周报邮件（便捷方法）

        Args:
            report_content: 周报内容（Markdown或HTML格式）
            recipients: 收件人列表（默认从环境变量读取）
            report_date: 报告日期（如"第45周"）

        Returns:
            是否发送成功
        """
        # 获取收件人列表
        if recipients is None:
            recipients_str = os.getenv('EMAIL_RECIPIENTS', 'li.xiaoyu@vnet.com')
            recipients = [r.strip() for r in recipients_str.split(',')]

        # 从Markdown内容提取周数
        import re
        week_match = re.search(r'第(\d+)周', report_content)
        if week_match:
            week_num = week_match.group(0)  # "第45周"
            subject = f"IDC行业竞争情报周报 - {week_num}"
        else:
            # 如果没有找到周数，使用传入的日期或默认格式
            subject = f"IDC行业竞争情报周报"
            if report_date:
                subject += f" - {report_date}"

        # 如果是Markdown格式，转换为HTML
        if not report_content.strip().startswith('<'):
            if use_block_layout:
                # 使用新的板块布局
                from .email_template_v2 import generate_html_report
            else:
                # 使用原有的卡片布局
                from .email_template import generate_html_report
            html_content = generate_html_report(report_content, title=subject)
        else:
            html_content = report_content

        return self.send_html_email(
            subject=subject,
            html_content=html_content,
            recipients=recipients
        )

    @classmethod
    def from_env(cls) -> 'EmailSender':
        """
        从环境变量创建邮件发送器（工厂方法）

        Returns:
            EmailSender实例
        """
        return cls()

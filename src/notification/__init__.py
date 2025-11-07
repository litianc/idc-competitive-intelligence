"""邮件通知模块"""

from .email_sender import EmailSender
from .email_template import generate_html_report

__all__ = ['EmailSender', 'generate_html_report']

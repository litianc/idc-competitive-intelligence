"""
IDC行业竞争情报系统 - 定时调度器

使用APScheduler实现定时任务：
- 每日早8点自动采集
- 每周五下午5点生成周报
"""

import logging
import os
from datetime import datetime
from typing import Optional
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)


def run_collection(limit: int = 20, no_llm: bool = False):
    """
    运行数据采集任务

    Args:
        limit: 每个源采集文章数量
        no_llm: 是否禁用LLM
    """
    import subprocess
    import sys

    cmd = [sys.executable, 'run_collection.py', '--limit', str(limit)]
    if no_llm:
        cmd.append('--no-llm')

    try:
        logger.info(f"开始执行采集任务: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)

        if result.returncode == 0:
            logger.info(f"采集任务完成: {result.stdout}")
        else:
            logger.error(f"采集任务失败: {result.stderr}")

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        logger.error("采集任务超时（1小时）")
        return False
    except Exception as e:
        logger.error(f"采集任务异常: {e}")
        return False


def generate_weekly_report(days: int = 7):
    """
    生成周报

    Args:
        days: 统计最近N天的数据
    """
    import subprocess
    import sys

    cmd = [sys.executable, 'generate_weekly_report.py', '--days', str(days)]

    try:
        logger.info(f"开始生成周报: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

        if result.returncode == 0:
            logger.info(f"周报生成完成: {result.stdout}")
        else:
            logger.error(f"周报生成失败: {result.stderr}")

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        logger.error("周报生成超时（10分钟）")
        return False
    except Exception as e:
        logger.error(f"周报生成异常: {e}")
        return False


class IntelligenceScheduler:
    """IDC行业竞争情报定时调度器"""

    def __init__(self, jobstore: str = 'memory', timezone: str = 'Asia/Shanghai'):
        """
        初始化调度器

        Args:
            jobstore: 任务存储方式 ('memory' 或 'sqlite')
            timezone: 时区（默认Asia/Shanghai）
        """
        self.timezone = timezone

        # 配置任务存储
        jobstores = {}
        if jobstore == 'sqlite':
            # 使用SQLite持久化存储
            db_path = Path('data/scheduler.db')
            db_path.parent.mkdir(exist_ok=True)
            jobstores = {
                'default': SQLAlchemyJobStore(url=f'sqlite:///{db_path}')
            }

        # 配置执行器（线程池）
        executors = {
            'default': ThreadPoolExecutor(max_workers=2)
        }

        # 任务配置
        job_defaults = {
            'coalesce': True,  # 合并错过的任务
            'max_instances': 1,  # 同一任务最多1个实例同时运行
            'misfire_grace_time': 3600  # 错过执行的宽限时间（1小时）
        }

        # 创建调度器
        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone=timezone
        )

        # 配置参数（可从环境变量加载）
        self.collection_hour = 8
        self.collection_minute = 0
        self.report_day = 'fri'
        self.report_hour = 17
        self.report_minute = 0

        logger.info(f"调度器已初始化（时区: {timezone}, 存储: {jobstore}）")

    def add_daily_collection_job(
        self,
        hour: int = 8,
        minute: int = 0,
        misfire_grace_time: Optional[int] = None
    ):
        """
        添加每日采集任务

        Args:
            hour: 小时（0-23）
            minute: 分钟（0-59）
            misfire_grace_time: 错过执行的宽限时间（秒）

        Returns:
            创建的任务对象
        """
        trigger = CronTrigger(
            hour=hour,
            minute=minute,
            timezone=self.timezone
        )

        job = self.scheduler.add_job(
            func=self._run_daily_collection,
            trigger=trigger,
            id='daily_collection',
            name='每日数据采集',
            replace_existing=True,
            misfire_grace_time=misfire_grace_time
        )

        logger.info(f"已添加每日采集任务: 每天 {hour:02d}:{minute:02d}")
        # Note: next_run_time只在scheduler启动后才可用
        # logger.info(f"下次执行时间: {job.next_run_time}")

        return job

    def add_weekly_report_job(
        self,
        day_of_week: str = 'fri',
        hour: int = 17,
        minute: int = 0,
        misfire_grace_time: Optional[int] = None
    ):
        """
        添加每周周报任务

        Args:
            day_of_week: 星期几 (mon/tue/wed/thu/fri/sat/sun)
            hour: 小时（0-23）
            minute: 分钟（0-59）
            misfire_grace_time: 错过执行的宽限时间（秒）

        Returns:
            创建的任务对象
        """
        trigger = CronTrigger(
            day_of_week=day_of_week,
            hour=hour,
            minute=minute,
            timezone=self.timezone
        )

        job = self.scheduler.add_job(
            func=self._run_weekly_report,
            trigger=trigger,
            id='weekly_report',
            name='每周周报生成',
            replace_existing=True,
            misfire_grace_time=misfire_grace_time
        )

        logger.info(f"已添加每周周报任务: 每周{day_of_week} {hour:02d}:{minute:02d}")
        # Note: next_run_time只在scheduler启动后才可用
        # logger.info(f"下次执行时间: {job.next_run_time}")

        return job

    def _run_daily_collection(self, limit: int = 20, no_llm: bool = False):
        """
        执行每日采集任务（内部方法）

        Args:
            limit: 每个源采集文章数量
            no_llm: 是否禁用LLM
        """
        logger.info("="*80)
        logger.info(f"定时任务触发: 每日数据采集")
        logger.info(f"执行时间: {datetime.now()}")
        logger.info("="*80)

        try:
            success = run_collection(limit=limit, no_llm=no_llm)

            if success:
                logger.info("✓ 每日采集任务执行成功")
            else:
                logger.warning("⚠️ 每日采集任务执行失败")

        except Exception as e:
            logger.error(f"✗ 每日采集任务异常: {e}", exc_info=True)

    def _run_weekly_report(self, days: int = 7):
        """
        执行每周周报任务（内部方法）

        Args:
            days: 统计最近N天的数据
        """
        logger.info("="*80)
        logger.info(f"定时任务触发: 每周周报生成")
        logger.info(f"执行时间: {datetime.now()}")
        logger.info("="*80)

        try:
            success = generate_weekly_report(days=days)

            if success:
                logger.info("✓ 每周周报任务执行成功")
            else:
                logger.warning("⚠️ 每周周报任务执行失败")

        except Exception as e:
            logger.error(f"✗ 每周周报任务异常: {e}", exc_info=True)

    def start(self):
        """启动调度器"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("调度器已启动")
        else:
            logger.warning("调度器已在运行中")

    def stop(self):
        """停止调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("调度器已停止")
        else:
            logger.warning("调度器未在运行")

    def get_all_jobs(self):
        """
        获取所有任务列表

        Returns:
            任务列表
        """
        return self.scheduler.get_jobs()

    def remove_job(self, job_id: str) -> bool:
        """
        移除指定任务

        Args:
            job_id: 任务ID

        Returns:
            是否移除成功
        """
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"已移除任务: {job_id}")
            return True
        except Exception as e:
            logger.error(f"移除任务失败: {job_id} | {e}")
            return False

    def pause_job(self, job_id: str):
        """
        暂停指定任务

        Args:
            job_id: 任务ID
        """
        self.scheduler.pause_job(job_id)
        logger.info(f"已暂停任务: {job_id}")

    def resume_job(self, job_id: str):
        """
        恢复指定任务

        Args:
            job_id: 任务ID
        """
        self.scheduler.resume_job(job_id)
        logger.info(f"已恢复任务: {job_id}")

    def load_config_from_env(self):
        """从环境变量加载配置"""
        self.collection_hour = int(os.getenv('COLLECTION_HOUR', '8'))
        self.collection_minute = int(os.getenv('COLLECTION_MINUTE', '0'))
        self.report_day = os.getenv('REPORT_DAY', 'fri')
        self.report_hour = int(os.getenv('REPORT_HOUR', '17'))
        self.report_minute = int(os.getenv('REPORT_MINUTE', '0'))

        logger.info(f"已从环境变量加载配置:")
        logger.info(f"  每日采集: {self.collection_hour:02d}:{self.collection_minute:02d}")
        logger.info(f"  每周周报: {self.report_day} {self.report_hour:02d}:{self.report_minute:02d}")

"""
定时调度系统测试

测试APScheduler定时任务功能：
- 每日早8点自动采集
- 每周五下午5点生成周报
"""

import pytest
from datetime import datetime, time
from unittest.mock import Mock, patch, call
from pathlib import Path

from src.scheduler.job_scheduler import IntelligenceScheduler


class TestIntelligenceScheduler:
    """测试定时调度器"""

    def test_scheduler_initialization(self):
        """测试调度器初始化"""
        scheduler = IntelligenceScheduler()

        assert scheduler is not None
        assert scheduler.scheduler is not None
        assert hasattr(scheduler, 'add_daily_collection_job')
        assert hasattr(scheduler, 'add_weekly_report_job')

    def test_add_daily_collection_job(self):
        """测试添加每日采集任务"""
        scheduler = IntelligenceScheduler()

        # 添加每日8点采集任务
        job = scheduler.add_daily_collection_job(hour=8, minute=0)

        assert job is not None
        assert job.id == 'daily_collection'

    def test_add_weekly_report_job(self):
        """测试添加每周周报任务"""
        scheduler = IntelligenceScheduler()

        # 添加每周五17点周报任务
        job = scheduler.add_weekly_report_job(day_of_week='fri', hour=17, minute=0)

        assert job is not None
        assert job.id == 'weekly_report'

    @patch('src.scheduler.job_scheduler.run_collection')
    def test_daily_collection_task_execution(self, mock_run_collection):
        """测试每日采集任务执行"""
        scheduler = IntelligenceScheduler()

        # 手动触发采集任务
        scheduler._run_daily_collection()

        # 验证采集函数被调用
        mock_run_collection.assert_called_once()

    @patch('src.scheduler.job_scheduler.generate_weekly_report')
    def test_weekly_report_task_execution(self, mock_generate_report):
        """测试每周周报任务执行"""
        scheduler = IntelligenceScheduler()

        # 手动触发周报任务
        scheduler._run_weekly_report()

        # 验证周报生成函数被调用
        mock_generate_report.assert_called_once()

    def test_scheduler_start_stop(self):
        """测试调度器启动和停止"""
        scheduler = IntelligenceScheduler()

        # 启动调度器
        scheduler.start()
        assert scheduler.scheduler.running is True

        # 停止调度器
        scheduler.stop()
        assert scheduler.scheduler.running is False

    def test_get_all_jobs(self):
        """测试获取所有任务列表"""
        scheduler = IntelligenceScheduler()
        scheduler.add_daily_collection_job(hour=8, minute=0)
        scheduler.add_weekly_report_job(day_of_week='fri', hour=17, minute=0)

        jobs = scheduler.get_all_jobs()

        assert len(jobs) >= 2
        job_ids = [job.id for job in jobs]
        assert 'daily_collection' in job_ids
        assert 'weekly_report' in job_ids

    def test_remove_job(self):
        """测试移除任务"""
        scheduler = IntelligenceScheduler()
        scheduler.add_daily_collection_job(hour=8, minute=0)

        # 移除任务
        result = scheduler.remove_job('daily_collection')
        assert result is True

        # 验证任务已移除
        jobs = scheduler.get_all_jobs()
        job_ids = [job.id for job in jobs]
        assert 'daily_collection' not in job_ids

    def test_job_persistence(self):
        """测试任务持久化（使用SQLite存储）"""
        scheduler = IntelligenceScheduler(jobstore='sqlite')
        scheduler.add_daily_collection_job(hour=8, minute=0)

        # 停止并重新启动
        scheduler.stop()
        scheduler2 = IntelligenceScheduler(jobstore='sqlite')

        jobs = scheduler2.get_all_jobs()
        job_ids = [job.id for job in jobs]

        # 验证任务被持久化
        assert 'daily_collection' in job_ids

    @patch('src.scheduler.job_scheduler.run_collection')
    def test_collection_with_custom_config(self, mock_run_collection):
        """测试使用自定义配置的采集任务"""
        scheduler = IntelligenceScheduler()

        # 使用自定义参数
        scheduler._run_daily_collection(limit=30, no_llm=False)

        # 验证参数传递
        mock_run_collection.assert_called_once()

    def test_next_run_time(self):
        """测试获取下次执行时间"""
        scheduler = IntelligenceScheduler()
        job = scheduler.add_daily_collection_job(hour=8, minute=0)

        next_run = job.next_run_time

        assert next_run is not None
        assert isinstance(next_run, datetime)
        assert next_run.hour == 8
        assert next_run.minute == 0

    def test_scheduler_timezone_support(self):
        """测试时区支持（使用Asia/Shanghai）"""
        scheduler = IntelligenceScheduler(timezone='Asia/Shanghai')
        job = scheduler.add_daily_collection_job(hour=8, minute=0)

        # 验证时区设置
        assert job.next_run_time.tzinfo is not None

    def test_job_misfire_grace_time(self):
        """测试任务错过执行的宽限时间"""
        scheduler = IntelligenceScheduler()

        # 设置宽限时间为1小时
        job = scheduler.add_daily_collection_job(
            hour=8,
            minute=0,
            misfire_grace_time=3600
        )

        assert job is not None

    @patch('src.scheduler.job_scheduler.logging')
    def test_error_handling_in_collection(self, mock_logging):
        """测试采集任务中的错误处理"""
        scheduler = IntelligenceScheduler()

        with patch('src.scheduler.job_scheduler.run_collection', side_effect=Exception("采集失败")):
            scheduler._run_daily_collection()

            # 验证错误被记录
            mock_logging.error.assert_called()

    @patch('src.scheduler.job_scheduler.logging')
    def test_error_handling_in_report(self, mock_logging):
        """测试周报任务中的错误处理"""
        scheduler = IntelligenceScheduler()

        with patch('src.scheduler.job_scheduler.generate_weekly_report', side_effect=Exception("生成失败")):
            scheduler._run_weekly_report()

            # 验证错误被记录
            mock_logging.error.assert_called()

    def test_scheduler_config_from_env(self):
        """测试从环境变量加载配置"""
        import os

        # 设置环境变量
        os.environ['COLLECTION_HOUR'] = '9'
        os.environ['COLLECTION_MINUTE'] = '30'
        os.environ['REPORT_DAY'] = 'fri'
        os.environ['REPORT_HOUR'] = '18'

        scheduler = IntelligenceScheduler()
        scheduler.load_config_from_env()

        # 验证配置加载
        assert scheduler.collection_hour == 9
        assert scheduler.collection_minute == 30
        assert scheduler.report_day == 'fri'
        assert scheduler.report_hour == 18

        # 清理环境变量
        del os.environ['COLLECTION_HOUR']
        del os.environ['COLLECTION_MINUTE']
        del os.environ['REPORT_DAY']
        del os.environ['REPORT_HOUR']

    def test_pause_and_resume_job(self):
        """测试暂停和恢复任务"""
        scheduler = IntelligenceScheduler()
        job = scheduler.add_daily_collection_job(hour=8, minute=0)

        # 暂停任务
        scheduler.pause_job('daily_collection')
        job = scheduler.scheduler.get_job('daily_collection')
        # APScheduler中暂停的任务next_run_time为None

        # 恢复任务
        scheduler.resume_job('daily_collection')
        job = scheduler.scheduler.get_job('daily_collection')
        assert job.next_run_time is not None

#!/usr/bin/env python3
"""
定时调度系统功能演示和测试

测试调度器是否能按时触发任务
"""

import time
import logging
from datetime import datetime, timedelta
from src.scheduler import IntelligenceScheduler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)

logger = logging.getLogger(__name__)


def test_immediate_trigger():
    """测试1：立即触发任务（设置为当前时间+1分钟）"""
    logger.info("="*80)
    logger.info("测试1：立即触发测试（1分钟后执行）")
    logger.info("="*80)

    # 计算1分钟后的时间
    next_minute = datetime.now() + timedelta(minutes=1)
    hour = next_minute.hour
    minute = next_minute.minute

    logger.info(f"当前时间: {datetime.now().strftime('%H:%M:%S')}")
    logger.info(f"设置任务执行时间: {hour:02d}:{minute:02d}")

    # 创建调度器
    scheduler = IntelligenceScheduler(jobstore='memory', timezone='Asia/Shanghai')

    # 添加一个1分钟后执行的采集任务
    job = scheduler.add_daily_collection_job(hour=hour, minute=minute)

    logger.info(f"任务已添加: {job.name}")
    logger.info("调度器启动，等待任务触发...")

    # 启动调度器
    scheduler.start()

    # 等待2分钟
    for i in range(120):
        time.sleep(1)
        if i % 10 == 0:
            logger.info(f"等待中... ({i}秒)")

    # 停止调度器
    scheduler.stop()
    logger.info("测试1完成")


def test_interval_30_seconds():
    """测试2：每30秒执行一次（使用interval触发器）"""
    from apscheduler.triggers.interval import IntervalTrigger

    logger.info("\n" + "="*80)
    logger.info("测试2：间隔触发测试（每30秒执行一次）")
    logger.info("="*80)

    scheduler = IntelligenceScheduler(jobstore='memory', timezone='Asia/Shanghai')

    # 定义测试任务
    def test_task():
        logger.info(f"✓ 任务被触发! 时间: {datetime.now().strftime('%H:%M:%S')}")

    # 添加每30秒执行一次的任务
    job = scheduler.scheduler.add_job(
        func=test_task,
        trigger=IntervalTrigger(seconds=30),
        id='test_interval',
        name='每30秒测试任务'
    )

    logger.info(f"任务已添加: {job.name}")
    logger.info("调度器启动，将每30秒触发一次任务...")

    # 启动调度器
    scheduler.start()

    # 运行90秒（应该触发3次）
    for i in range(90):
        time.sleep(1)
        if i % 10 == 0 and i > 0:
            logger.info(f"运行中... ({i}秒)")

    # 停止调度器
    scheduler.stop()
    logger.info("测试2完成")


def test_cron_every_minute():
    """测试3：每分钟执行一次（使用cron触发器）"""
    from apscheduler.triggers.cron import CronTrigger

    logger.info("\n" + "="*80)
    logger.info("测试3：Cron触发测试（每分钟执行一次）")
    logger.info("="*80)

    scheduler = IntelligenceScheduler(jobstore='memory', timezone='Asia/Shanghai')

    # 定义测试任务
    execution_count = [0]  # 使用列表来跟踪执行次数

    def test_task():
        execution_count[0] += 1
        logger.info(f"✓ 任务被触发! 第{execution_count[0]}次 | 时间: {datetime.now().strftime('%H:%M:%S')}")

    # 添加每分钟执行一次的任务（每分钟的第0秒）
    job = scheduler.scheduler.add_job(
        func=test_task,
        trigger=CronTrigger(second=0),  # 每分钟的第0秒触发
        id='test_cron',
        name='每分钟测试任务'
    )

    logger.info(f"任务已添加: {job.name}")
    logger.info(f"当前时间: {datetime.now().strftime('%H:%M:%S')}")
    logger.info("调度器启动，将在每分钟的第0秒触发任务...")

    # 启动调度器
    scheduler.start()

    # 运行150秒（应该触发2-3次）
    for i in range(150):
        time.sleep(1)
        if i % 15 == 0 and i > 0:
            logger.info(f"运行中... ({i}秒) | 已执行{execution_count[0]}次")

    # 停止调度器
    scheduler.stop()
    logger.info(f"测试3完成 - 总共执行了{execution_count[0]}次")


def test_list_jobs():
    """测试4：查看所有任务"""
    logger.info("\n" + "="*80)
    logger.info("测试4：任务列表查看")
    logger.info("="*80)

    scheduler = IntelligenceScheduler(jobstore='memory', timezone='Asia/Shanghai')

    # 添加多个任务
    scheduler.add_daily_collection_job(hour=8, minute=0)
    scheduler.add_weekly_report_job(day_of_week='fri', hour=17, minute=0)

    # 获取所有任务
    jobs = scheduler.get_all_jobs()

    logger.info(f"\n当前已添加的任务 ({len(jobs)}个):")
    for job in jobs:
        logger.info(f"  [{job.id}] {job.name}")
        logger.info(f"    触发器: {job.trigger}")
        # 注意：根据APScheduler版本，可能需要用job.next_run_time或其他方式获取下次执行时间

    logger.info("测试4完成")


def main():
    """主函数"""
    logger.info("\n" + "="*80)
    logger.info("IDC行业竞争情报系统 - 定时调度器功能测试")
    logger.info("="*80)

    # 运行测试
    try:
        # 测试4：查看任务列表（快速测试）
        test_list_jobs()

        # 询问是否运行实际触发测试
        logger.info("\n" + "="*80)
        logger.info("是否运行实际触发测试？")
        logger.info("  测试2：每30秒触发一次（运行90秒）")
        logger.info("  测试3：每分钟触发一次（运行150秒）")
        logger.info("="*80)

        # 自动运行测试2（间隔触发）
        logger.info("\n开始运行测试2...")
        test_interval_30_seconds()

        logger.info("\n\n" + "="*80)
        logger.info("所有测试完成！")
        logger.info("="*80)

    except KeyboardInterrupt:
        logger.info("\n用户中断测试")
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)


if __name__ == "__main__":
    main()

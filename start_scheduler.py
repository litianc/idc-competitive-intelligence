#!/usr/bin/env python3
"""
IDC行业竞争情报系统 - 定时调度器启动脚本

功能：
- 每日早8点自动采集数据
- 每周五下午5点生成周报
- 支持前台运行或后台daemon模式

使用方法:
    python3 start_scheduler.py                    # 前台运行
    python3 start_scheduler.py --daemon           # 后台运行
    python3 start_scheduler.py --config scheduler.ini  # 使用配置文件
"""

import argparse
import logging
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

from src.scheduler import IntelligenceScheduler


# 配置日志
def setup_logging(log_file: str = 'logs/scheduler.log', log_level: str = 'INFO'):
    """
    配置日志系统

    Args:
        log_file: 日志文件路径
        log_level: 日志级别
    """
    # 创建日志目录
    log_path = Path(log_file)
    log_path.parent.mkdir(exist_ok=True)

    # 日志格式
    log_format = '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    # 配置日志
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def load_config(config_file: str = None):
    """
    加载配置文件（INI格式）

    Args:
        config_file: 配置文件路径

    Returns:
        配置字典
    """
    import configparser

    config = {
        'collection_hour': 8,
        'collection_minute': 0,
        'collection_limit': 20,
        'collection_no_llm': False,
        'report_day': 'fri',
        'report_hour': 17,
        'report_minute': 0,
        'report_days': 7,
        'jobstore': 'sqlite',
        'timezone': 'Asia/Shanghai'
    }

    if config_file and Path(config_file).exists():
        parser = configparser.ConfigParser()
        parser.read(config_file, encoding='utf-8')

        if 'scheduler' in parser:
            config.update({
                'collection_hour': parser.getint('scheduler', 'collection_hour', fallback=8),
                'collection_minute': parser.getint('scheduler', 'collection_minute', fallback=0),
                'collection_limit': parser.getint('scheduler', 'collection_limit', fallback=20),
                'collection_no_llm': parser.getboolean('scheduler', 'collection_no_llm', fallback=False),
                'report_day': parser.get('scheduler', 'report_day', fallback='fri'),
                'report_hour': parser.getint('scheduler', 'report_hour', fallback=17),
                'report_minute': parser.getint('scheduler', 'report_minute', fallback=0),
                'report_days': parser.getint('scheduler', 'report_days', fallback=7),
                'jobstore': parser.get('scheduler', 'jobstore', fallback='sqlite'),
                'timezone': parser.get('scheduler', 'timezone', fallback='Asia/Shanghai')
            })

    return config


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='IDC行业竞争情报定时调度器')
    parser.add_argument('--config', type=str, default=None,
                       help='配置文件路径（INI格式）')
    parser.add_argument('--daemon', action='store_true',
                       help='以daemon模式运行（后台）')
    parser.add_argument('--log-file', type=str, default='logs/scheduler.log',
                       help='日志文件路径')
    parser.add_argument('--log-level', type=str, default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='日志级别')

    args = parser.parse_args()

    # 配置日志
    setup_logging(log_file=args.log_file, log_level=args.log_level)
    logger = logging.getLogger(__name__)

    # 加载配置
    config = load_config(args.config)

    logger.info("="*80)
    logger.info("IDC行业竞争情报系统 - 定时调度器")
    logger.info("="*80)
    logger.info(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"运行模式: {'后台daemon' if args.daemon else '前台'}")
    logger.info(f"日志文件: {args.log_file}")
    logger.info(f"日志级别: {args.log_level}")

    # 显示配置
    logger.info("\n调度配置:")
    logger.info(f"  时区: {config['timezone']}")
    logger.info(f"  任务存储: {config['jobstore']}")
    logger.info(f"  每日采集: {config['collection_hour']:02d}:{config['collection_minute']:02d}")
    logger.info(f"    - 采集数量: 每源{config['collection_limit']}篇")
    logger.info(f"    - LLM分析: {'禁用' if config['collection_no_llm'] else '启用'}")
    logger.info(f"  每周周报: 每周{config['report_day']} {config['report_hour']:02d}:{config['report_minute']:02d}")
    logger.info(f"    - 统计天数: {config['report_days']}天")

    # 创建调度器
    scheduler = IntelligenceScheduler(
        jobstore=config['jobstore'],
        timezone=config['timezone']
    )

    # 添加任务
    logger.info("\n添加定时任务...")

    # 1. 每日采集任务
    daily_job = scheduler.add_daily_collection_job(
        hour=config['collection_hour'],
        minute=config['collection_minute']
    )

    # 2. 每周周报任务
    weekly_job = scheduler.add_weekly_report_job(
        day_of_week=config['report_day'],
        hour=config['report_hour'],
        minute=config['report_minute']
    )

    # 显示任务信息
    logger.info("\n已添加的任务:")
    for job in scheduler.get_all_jobs():
        logger.info(f"  [{job.id}] {job.name}")
        # Note: next_run_time只在调度器启动后才可用

    # 启动调度器
    logger.info("\n启动调度器...")
    scheduler.start()
    logger.info("✓ 调度器已启动，等待任务触发...")

    # 显示下次执行时间（调度器启动后）
    logger.info("\n任务执行时间:")
    for job in scheduler.get_all_jobs():
        logger.info(f"  [{job.id}] {job.name}")
        logger.info(f"    下次执行: {job.next_run_time}")

    # 信号处理（优雅退出）
    def signal_handler(signum, frame):
        logger.info("\n收到退出信号，正在停止调度器...")
        scheduler.stop()
        logger.info("调度器已停止")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 主循环
    try:
        if args.daemon:
            # daemon模式：持续运行
            logger.info("调度器已进入daemon模式（按Ctrl+C退出）")
            while True:
                time.sleep(60)  # 每分钟检查一次
        else:
            # 前台模式：显示状态
            logger.info("调度器已进入前台模式（按Ctrl+C退出）")
            logger.info("\n任务状态监控:")
            while True:
                # 每10秒显示一次任务状态
                jobs = scheduler.get_all_jobs()
                for job in jobs:
                    logger.info(f"  [{job.id}] 下次执行: {job.next_run_time}")

                time.sleep(10)

    except KeyboardInterrupt:
        logger.info("\n用户中断，正在停止调度器...")
        scheduler.stop()
        logger.info("调度器已停止")


if __name__ == "__main__":
    main()

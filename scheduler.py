"""스케줄러 - 하루 3회 자동 발행 (07:00, 14:00, 20:00)"""

import schedule
import time
import subprocess
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def run_publish():
    """발행 실행"""
    logger.info(f"=== 자동 발행 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
    try:
        result = subprocess.run(
            ['python', 'app.py', 'run'],
            capture_output=True,
            text=True,
            cwd='/Users/twinssn/Desktop/tour-auto-publisher'
        )
        logger.info(result.stdout)
        if result.stderr:
            logger.error(result.stderr)
    except Exception as e:
        logger.error(f"발행 실패: {e}")


def main():
    logger.info("Tour Auto Publisher 스케줄러 시작")
    logger.info("발행 시간: 07:00, 14:00, 20:00")
    
    # 스케줄 설정
    schedule.every().day.at("07:00").do(run_publish)
    schedule.every().day.at("14:00").do(run_publish)
    schedule.every().day.at("20:00").do(run_publish)
    
    logger.info("스케줄러 대기 중...")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # 1분마다 체크


if __name__ == '__main__':
    main()

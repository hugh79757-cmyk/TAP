#!/usr/bin/env python3
"""Tour Auto Publisher v10.0 - API 기반 캠핑장 시스템"""

import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

log_dir = Path(__file__).parent / 'logs'
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def run_publish():
    """메인 발행 함수 v10.0"""
    logger.info("=" * 50)
    logger.info("TAP v10.0 시작")
    logger.info("=" * 50)
    
    from core.blogger_publisher import load_publisher
    from core.ai_writer import load_ai_writer
    from core.title_generator import load_title_generator
    from core.camping_data import get_camping_data, get_random_theme
    from core.content_processor import process_content
    from core.config import ANGLE_MAP, DEFAULT_LABEL
    
    publisher = load_publisher()
    writer = load_ai_writer()
    title_gen = load_title_generator()
    
    if not writer:
        logger.error("OPENAI_API_KEY 없음")
        return
    
    # 1. 테마 + 데이터
    theme = get_random_theme()
    logger.info(f"[1] 테마: {theme}")
    
    data = get_camping_data(theme)
    if not data:
        logger.warning(f"'{theme}' 데이터 없음, 글램핑 폴백")
        data = get_camping_data('글램핑')
    
    if not data:
        logger.error("데이터 없음")
        return
    
    items = data['items']
    display_region = data['display_region']
    sigungu = data['sigungu']
    
    logger.info(f"[2] 지역: {display_region} {sigungu}")
    logger.info(f"[3] 장소: {len(items)}개")
    for item in items:
        logger.info(f"    - {item['title']}")
    
    # 2. 제목
    title = title_gen.generate(display_region, theme, len(items), sigungu=sigungu)
    logger.info(f"[4] 제목: {title}")
    
    # 3. AI 글 생성
    angle = ANGLE_MAP.get(theme, theme)
    logger.info(f"[5] AI 생성 중... (앵글: {angle})")
    
    try:
        raw_content = writer.generate_full_content(
            items=items,
            theme=theme,
            region=f"{display_region} {sigungu}",
            angle=angle
        )
    except Exception as e:
        logger.error(f"AI 생성 실패: {e}")
        return
    
    # 4. 후처리
    final_content = process_content(raw_content, items, display_region, theme)
    logger.info(f"[6] 후처리 완료 ({len(final_content)}자)")
    
    # 5. 발행
    labels = [DEFAULT_LABEL, theme, display_region]
    logger.info(f"[7] 발행 중... (라벨: {labels})")
    
    try:
        result = publisher.create_post(
            title=title,
            content=final_content,
            labels=labels,
            is_draft=False
        )
        logger.info(f"[8] 발행 완료: {result.get('url', 'URL 없음')}")
    except Exception as e:
        logger.error(f"발행 실패: {e}")
        return
    
    logger.info("=" * 50)
    logger.info("작업 완료!")
    logger.info("=" * 50)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        run_publish()
    else:
        print("사용법: python app.py run")

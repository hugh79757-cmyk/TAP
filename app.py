import logging
import sys
from pathlib import Path

Path('logs').mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def generate_and_publish():
    from core.content_generator import load_content_generator
    from core.wordpress_publisher import load_publisher
    
    logger.info("=" * 50)
    logger.info("콘텐츠 생성 시작")
    
    generator = load_content_generator()
    publisher = load_publisher()
    
    # 이미지 확보 가능한 주제 선택 (최대 3번 재시도)
    items, region, theme_data = generator.select_theme_with_images()
    
    theme = theme_data.get('theme', '')
    source = theme_data.get('source', '')
    angle = theme_data.get('angle', '')
    
    logger.info(f"선택된 주제: {theme}")
    logger.info(f"데이터 소스: {source}")
    logger.info(f"각도: {angle}")
    logger.info(f"선택된 지역: {region}")
    logger.info(f"최종 데이터: {len(items)}건")
    logger.info(f"AI 사용: {generator.use_ai}")
    
    if not items:
        logger.error("데이터가 없습니다")
        return
    
    min_items = generator.settings.get('content', {}).get('min_items', 3)
    max_items = generator.settings.get('content', {}).get('max_items', 6)
    
    items = items[:max_items]
    
    title = generator.generate_title(theme, items, region, theme_data)
    logger.info(f"생성된 제목: {title}")
    
    post_data = generator.generate_post(items, theme, region, theme_data)
    
    try:
        result = publisher.create_post(
            title=title,
            content=post_data['content'],
            status=generator.settings.get('wordpress', {}).get('default_status', 'draft'),
            tags=post_data.get('tags', []),
            featured_image_url=post_data.get('featured_image', ''),
            excerpt=post_data.get('excerpt', '')
        )
        
        logger.info("발행 완료!")
        logger.info(f"  - ID: {result.get('id')}")
        logger.info(f"  - URL: {result.get('url')}")
        logger.info(f"  - 상태: {result.get('status')}")
        
    except Exception as e:
        logger.error(f"발행 실패: {e}")


def test_themes():
    """주제 목록 확인"""
    from core.content_generator import ContentGenerator
    import yaml
    
    config_path = Path(__file__).parent / "config" / "themes.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        themes = yaml.safe_load(f)
    
    logger.info("=" * 50)
    logger.info("등록된 주제 목록")
    logger.info("=" * 50)
    
    total = 0
    for source, theme_list in themes.items():
        logger.info(f"\n[{source}] - {len(theme_list)}개")
        for i, t in enumerate(theme_list, 1):
            logger.info(f"  {i}. {t['theme']} ({t['angle']})")
        total += len(theme_list)
    
    logger.info(f"\n총 {total}개 주제")


def test_camping_api():
    logger.info("캠핑 API 테스트...")
    try:
        from core.camping_api import load_camping_client
        api = load_camping_client()
        result = api.get_campsite_list(num_of_rows=5)
        logger.info(f"캠핑장 조회 성공: {len(result)}건")
        for item in result:
            logger.info(f"  - {item.get('facltNm')}")
    except Exception as e:
        logger.error(f"캠핑 API 실패: {e}")


def test_durunubi_api():
    logger.info("두루누비 API 테스트...")
    try:
        from core.durunubi_api import load_durunubi_client
        api = load_durunubi_client()
        result = api.search_walking_trails(num_of_rows=3)
        logger.info(f"걷기길 조회 성공: {len(result)}건")
    except Exception as e:
        logger.error(f"두루누비 API 실패: {e}")


def test_photo_api():
    logger.info("관광사진 API 테스트...")
    try:
        from core.photo_api import load_photo_client
        api = load_photo_client()
        result = api.search_photos("캠핑", num_of_rows=3)
        logger.info(f"사진 검색 성공: {len(result)}건")
    except Exception as e:
        logger.error(f"관광사진 API 실패: {e}")


def test_ai():
    logger.info("OpenAI 연결 테스트...")
    try:
        from core.ai_writer import load_ai_writer
        writer = load_ai_writer()
        logger.info("AI 연결 성공!")
    except Exception as e:
        logger.error(f"AI 테스트 실패: {e}")


def test_all():
    logger.info("=" * 50)
    logger.info("전체 API 테스트")
    logger.info("=" * 50)
    test_camping_api()
    test_durunubi_api()
    test_photo_api()
    test_ai()
    logger.info("테스트 완료")


def print_help():
    print("""
Tour Auto Publisher - 관광 콘텐츠 자동 발행기

사용법:
  python app.py run           - 콘텐츠 생성 및 발행
  python app.py themes        - 등록된 주제 확인
  python app.py test-camping  - 캠핑 API 테스트
  python app.py test-durunubi - 두루누비 API 테스트
  python app.py test-photo    - 관광사진 API 테스트
  python app.py test-ai       - OpenAI 테스트
  python app.py test-all      - 전체 API 테스트
""")


def main():
    if len(sys.argv) < 2:
        print_help()
        return
    
    command = sys.argv[1]
    
    commands = {
        'run': generate_and_publish,
        'themes': test_themes,
        'test-camping': test_camping_api,
        'test-durunubi': test_durunubi_api,
        'test-photo': test_photo_api,
        'test-ai': test_ai,
        'test-all': test_all,
    }
    
    if command in commands:
        commands[command]()
    else:
        print_help()


if __name__ == '__main__':
    main()

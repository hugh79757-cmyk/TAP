import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
from core.database import Session, PostLog

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_publish():
    logger.info("최고 품질 AI 콘텐츠 생성을 시작합니다.")
    from core.content_generator import load_content_generator
    from core.blogger_publisher import load_publisher
    from core.ai_writer import load_ai_writer
    from core.title_generator import load_title_generator

    generator = load_content_generator()
    publisher = load_publisher()
    writer = load_ai_writer()
    title_gen = load_title_generator()

    if not writer:
        logger.error("OPENAI_API_KEY가 설정되지 않았습니다.")
        return

    # 1. 데이터 페칭
    items, region, theme_data = generator.select_theme_with_images()
    if not items: 
        logger.warning("새로운 장소를 찾지 못했습니다.")
        return

    # 2. AI 본문 생성
    raw_content = writer.generate_full_content(items, theme_data['theme'], region, theme_data['angle'])
    
    # 3. 이미지 및 지도 후처리
    final_content = generator.process_html(raw_content, items, theme_data['theme'], region=region)
    
    # 4. 다양한 제목 생성
    title = title_gen.generate(region, theme_data['theme'], len(items))
    logger.info(f"생성된 제목: {title}")

    # 5. 중복 검사
    current_embedding = writer.get_embedding(final_content)
    with Session() as session:
        past_posts = session.query(PostLog).all()
        for past in past_posts:
            if past.embedding:
                sim = writer.calculate_similarity(current_embedding, past.embedding)
                if sim > 0.95:
                    logger.warning(f"유사도 과다 ({sim:.4f}). 중단합니다.")
                    return
        session.add(PostLog(title=title, embedding=current_embedding))
        session.commit()

    # 6. Blogger 발행 (실제 발행)
    try:
        result = publisher.create_post(
            title=title, 
            content=final_content, 
            labels=['국내여행'],  # 라벨 통일
            is_draft=False
        )
        logger.info(f"성공! Blogger 발행 완료: {result.get('url')}")
    except Exception as e:
        logger.error(f"발행 실패: {e}")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'run':
        run_publish()

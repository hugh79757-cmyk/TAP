#!/usr/bin/env python3
"""Tour Auto Publisher - CSV + API 통합 시스템"""

import os
import re
import random
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# 로그 디렉토리 생성
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
    """메인 발행 함수"""
    logger.info("CSV + API 통합 콘텐츠 생성을 시작합니다.")
    
    from core.blogger_publisher import load_publisher
    from core.ai_writer import load_ai_writer
    from core.title_generator import load_title_generator
    from core.csv_data_loader import load_csv_loader
    
    publisher = load_publisher()
    writer = load_ai_writer()
    title_gen = load_title_generator()
    csv_loader = load_csv_loader()
    
    if not writer:
        logger.error("OPENAI_API_KEY가 설정되지 않았습니다.")
        return
    
    # 랜덤 테마 선택
    theme_data = csv_loader.get_random_theme()
    theme = theme_data['theme']
    theme_type = theme_data['type']
    
    # 아이템 조회 (limit=None이면 3~6 랜덤)
    items = csv_loader.get_items_by_theme(theme_data, limit=None)
    
    if not items:
        logger.warning(f"테마 '{theme}'에 데이터 없음. 글램핑으로 폴백")
        theme_data = {'theme': '글램핑', 'type': 'camping'}
        theme = '글램핑'
        theme_type = 'camping'
        items = csv_loader.get_items_by_theme(theme_data, limit=None)
    
    if not items:
        logger.error("사용 가능한 데이터가 없습니다.")
        return
    
    # 지역 추출 (첫 번째 아이템의 도 기준)
    region = items[0].get('do', '전국')
    if not region or region == 'nan':
        region = '전국'
    
    # 모든 아이템이 같은 지역인지 확인
    logger.info(f"선택된 지역: {region}, 아이템 수: {len(items)}개")
    for item in items:
        logger.info(f"  - {item['title']} ({item.get('do', '')} {item.get('sigungu', '')})")
    
    angle_map = {
        '글램핑': '럭셔리 캠핑',
        '카라반': '이동식 숙소',
        '반려견 동반': '반려동물과 함께',
        '낚시': '낚시 명당',
        '여름 물놀이': '시원한 물놀이',
        '가을 단풍': '단풍 명소',
        '자연풍경여행': '자연 속 힐링',
        '맛있는여행': '맛집 탐방',
        '전통·역사여행': '역사 탐방',
        '액티비티여행': '액티비티 체험',
        '축제여행': '축제 즐기기',
        '이색체험여행': '이색 체험',
        '명소여행': '명소 탐방',
    }
    angle = angle_map.get(theme, theme)
    
    logger.info(f"테마: {theme}, 지역: {region}, 아이템: {len(items)}개")
    
    # AI 콘텐츠 생성
    try:
        raw_content = writer.generate_full_content(
            items=items,
            theme=theme,
            region=region,
            angle=angle
        )
    except Exception as e:
        logger.error(f"콘텐츠 생성 실패: {e}")
        return
    
    # 후처리: 이미지 + 네이버 지도 링크 추가
    final_content = raw_content
    
    for item in items:
        title = item['title']
        addr = item.get('addr', '')
        map_url = item.get('map_url', '')
        image_url = item.get('image', '')
        
        # 주소 유효성 검사
        addr_valid = addr and addr.strip() and addr != 'nan' and addr != 'None'
        
        # info-box 생성
        info_parts = []
        if addr_valid:
            info_parts.append(f'<p><strong>주소:</strong> {addr}</p>')
        if map_url:
            info_parts.append(f'<p><a href="{map_url}" target="_blank">📍 {title} 네이버 지도에서 보기</a></p>')
        
        info_box = f'<div class="info-box">\n{"".join(info_parts)}\n</div>' if info_parts else ''
        
        # h3 태그 찾기
        title_keyword = title[:8] if len(title) >= 8 else title
        pattern = f'(<h3[^>]*>.*?{re.escape(title_keyword)}.*?</h3>)'
        match = re.search(pattern, final_content, re.IGNORECASE | re.DOTALL)
        
        if match:
            replacement = match.group(1)
            
            # 이미지가 있으면 추가 (alt 태그 포함)
            if image_url and image_url.startswith('http'):
                alt_text = f"{title} - {region} {theme}"
                img_tag = f'<figure><img src="{image_url}" alt="{alt_text}" title="{title}"/></figure>'
                replacement += '\n' + img_tag
            
            # info-box 추가
            if info_box:
                replacement += '\n' + info_box
            
            final_content = final_content.replace(match.group(1), replacement, 1)
    
    # 기존 "주소 정보 없음" 관련 텍스트 모두 제거
    final_content = re.sub(r'<p>\s*주소:\s*주소 정보 없음\s*</p>', '', final_content)
    final_content = re.sub(r'<p>\s*주소:\s*</p>', '', final_content)
    final_content = re.sub(r'주소:\s*주소 정보 없음', '', final_content)
    final_content = re.sub(r'주소 정보 없음', '', final_content)
    final_content = re.sub(r'주소:\s*nan', '', final_content, flags=re.IGNORECASE)
    final_content = re.sub(r'주소:\s*None', '', final_content, flags=re.IGNORECASE)
    final_content = re.sub(r'주소:\s*$', '', final_content, flags=re.MULTILINE)
    
    # 빈 줄 정리
    final_content = re.sub(r'\n{3,}', '\n\n', final_content)
    
    # 안내 문구 추가
    notice = '<p class="notice">※ 운영 시간, 예약 방법, 이용 요금 등 최신 정보는 네이버 지도에서 확인하시기 바랍니다. 방문 전 해당 장소의 공식 페이지나 전화 문의를 통해 정확한 정보를 확인하시는 것을 권장합니다.</p>'
    final_content += f'\n{notice}'
    
    # 제목 생성
    title = title_gen.generate(region, theme, len(items))
    logger.info(f"제목: {title}")
    
    # Blogger 발행
    try:
        result = publisher.create_post(
            title=title,
            content=final_content,
            labels=['국내여행', theme, region],
            is_draft=False
        )
        logger.info(f"발행 완료: {result.get('url', 'URL 없음')}")
    except Exception as e:
        logger.error(f"발행 실패: {e}")
        return
    
    logger.info("작업 완료!")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        run_publish()
    else:
        print("사용법: python app.py run")

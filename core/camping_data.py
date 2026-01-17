"""캠핑장 데이터 조회 (API 기반) - v10.0"""
import random
from collections import defaultdict
from core.camping_api import load_camping_client
from core.naver_map import get_naver_map_link
from core.config import REGION_ALIASES


def get_random_region_name(api_name: str) -> str:
    """API 지역명을 다양한 표현으로 변환"""
    aliases = REGION_ALIASES.get(api_name, [api_name])
    return random.choice(aliases)


def get_camping_data(theme: str = '글램핑', min_items: int = 3, max_items: int = 6) -> dict:
    """
    테마별 캠핑장 데이터 조회 (시군구 일관성 + 이미지 필터링)
    
    Returns:
        {
            'items': [...],
            'do_name': '경기도',
            'display_region': '경기',
            'sigungu': '가평군',
            'theme': '글램핑'
        }
    """
    api = load_camping_client()
    all_items = api.get_campsite_list(num_of_rows=500)
    
    if not all_items:
        return None
    
    # 1. 이미지 있는 항목만 필터링
    items_with_image = [item for item in all_items if item.get('firstImageUrl')]
    
    # 2. 테마별 필터링
    if theme == '글램핑':
        filtered = [item for item in items_with_image if item.get('glampInnerFclty')]
    elif theme == '카라반':
        filtered = [item for item in items_with_image if item.get('caravInnerFclty')]
    elif theme in ['반려동물 동반', '반려견 동반']:
        filtered = [item for item in items_with_image if item.get('animalCmgCl') == '가능']
    else:
        filtered = items_with_image
    
    if not filtered:
        filtered = items_with_image  # 폴백: 이미지 있는 전체
    
    # 3. 시군구별 그룹핑
    grouped = defaultdict(list)
    for item in filtered:
        do_name = item.get('doNm', '')
        sigungu = item.get('sigunguNm', '')
        if do_name and sigungu:
            key = (do_name, sigungu)
            grouped[key].append(item)
    
    # 4. 3개 이상 데이터 있는 시군구만 필터링
    valid_regions = {k: v for k, v in grouped.items() if len(v) >= min_items}
    
    if not valid_regions:
        return None
    
    # 5. 랜덤 시군구 선택
    selected_key = random.choice(list(valid_regions.keys()))
    do_name, sigungu = selected_key
    candidates = valid_regions[selected_key]
    
    # 6. 랜덤 개수 선택 (3~6개)
    count = random.randint(min_items, min(max_items, len(candidates)))
    selected_items = random.sample(candidates, count)
    
    # 7. 결과 포맷팅
    results = []
    for item in selected_items:
        name = item.get('facltNm', '')
        results.append({
            'title': name,
            'addr': item.get('addr1', ''),
            'do': do_name,
            'sigungu': sigungu,
            'overview': item.get('intro', '') or item.get('lineIntro', ''),
            'image': item.get('firstImageUrl', ''),
            'map_url': get_naver_map_link(name),
            'tel': item.get('tel', ''),
            'homepage': item.get('homepage', ''),
            'source': 'api_camping'
        })
    
    return {
        'items': results,
        'do_name': do_name,
        'display_region': get_random_region_name(do_name),
        'sigungu': sigungu,
        'theme': theme
    }


def get_random_theme() -> str:
    """랜덤 테마 선택"""
    themes = ['글램핑', '카라반', '반려동물 동반']
    return random.choice(themes)


if __name__ == '__main__':
    # 테스트
    data = get_camping_data('글램핑')
    if data:
        print(f"지역: {data['display_region']} {data['sigungu']}")
        print(f"테마: {data['theme']}")
        print(f"개수: {len(data['items'])}개")
        for item in data['items']:
            print(f"  - {item['title']}")

"""데이터 로더 유틸리티"""
import re
import requests
from urllib.parse import quote

COMPOUND_PLACES = [
    '일출봉', '해돋이봉', '국립공원', '도립공원', '선운산', '자연휴양림', '수목원',
    '해수욕장', '워터파크', '테마파크', '놀이공원', '스카이워크', '출렁다리',
    '케이블카', '곤돌라', '전망대', '타워', '랜드', '월드', '파크'
]

PLACE_KEYWORDS = [
    '축제', '해수욕장', '해변', '비치', '사찰', '절', '암', '궁', '성',
    '공원', '수목원', '식물원', '동물원', '아쿠아리움', '박물관', '미술관',
    '전시관', '기념관', '타워', '전망대', '케이블카', '스카이워크',
    '폭포', '계곡', '호수', '저수지', '강', '바다', '섬', '해안',
    '산', '봉', '령', '고개', '둘레길', '올레길', '트레일',
    '시장', '마을', '리', '동굴', '온천', '스파', '워터파크',
    '테마파크', '놀이공원', '리조트', '펜션', '캠핑장', '글램핑',
    '휴양림', '자연휴양림', '생태공원', '습지', '갯벌',
    '항', '포구', '선착장', '등대', '방파제',
    '카페', '맛집', '식당', '횟집', '한옥', '고택',
    # 전통 건축물
    '서원', '향교', '서당', '재', '루', '당', '헌', '정', '각',
    '사', '원', '관', '대'
]

EXCLUDE_WORDS = ['도로', '길', '로', '거리', '코스', '여행', '드라이브', '시간', '가이드']

SIGUNGU_NAMES = [
    '시', '군', '구', '동', '읍', '면', '리',
    '서울', '부산', '대구', '인천', '광주', '대전', '울산', '세종',
    '포항', '안동', '나주', '여수', '담양', '정선', '문경', '파주', '양양'
]


def extract_place_name(title: str) -> str:
    """기사 제목에서 장소명 추출"""
    if not title:
        return ''
    
    # 1. 복합 장소명 먼저 찾기
    for compound in COMPOUND_PLACES:
        pattern = rf'([가-힣]+{compound})'
        matches = re.findall(pattern, title)
        if matches:
            result = max(matches, key=len)
            if result not in EXCLUDE_WORDS and len(result) >= 3:
                return result
    
    # 2. 일반 키워드로 끝나는 단어 찾기
    for keyword in PLACE_KEYWORDS:
        pattern = rf'([가-힣]+{keyword})'
        matches = re.findall(pattern, title)
        if matches:
            result = max(matches, key=len)
            # 최소 3글자 이상, 키워드만 있는 경우 제외
            if result not in EXCLUDE_WORDS and len(result) >= 3 and result != keyword:
                return result
    
    # 3. 따옴표 안의 내용에서 장소 키워드 확인
    quote_pattern = r"['\"]([^'\"]+)['\"]"
    quote_matches = re.findall(quote_pattern, title)
    if quote_matches:
        for match in quote_matches:
            for keyword in PLACE_KEYWORDS + COMPOUND_PLACES:
                if keyword in match:
                    sub_pattern = rf'([가-힣]+{keyword})'
                    sub_matches = re.findall(sub_pattern, match)
                    if sub_matches:
                        result = max(sub_matches, key=len)
                        if result not in EXCLUDE_WORDS and len(result) >= 3:
                            return result
    
    # 4. 쉼표로 분리된 마지막 부분
    if ',' in title:
        last_part = title.split(',')[-1].strip()
        for keyword in PLACE_KEYWORDS + COMPOUND_PLACES:
            if keyword in last_part:
                pattern = rf'([가-힣]+{keyword})'
                matches = re.findall(pattern, last_part)
                if matches:
                    result = max(matches, key=len).strip()
                    if result not in EXCLUDE_WORDS and len(result) >= 3:
                        return result
    
    return ''


def is_only_sigungu(query: str) -> bool:
    """시군구명만 있는지 확인"""
    if not query:
        return True
    query = query.strip()
    for name in SIGUNGU_NAMES:
        if query == name or (query.endswith(name) and len(query) <= 4):
            return True
    return False


def make_naver_map_url(name: str) -> str:
    """네이버 지도 URL 생성"""
    if not name or not name.strip():
        return ''
    if name in EXCLUDE_WORDS:
        return ''
    if is_only_sigungu(name):
        return ''
    if len(name.strip()) < 3:
        return ''
    encoded = quote(name.strip())
    return f"https://map.naver.com/v5/search/{encoded}"


def is_image_valid(url: str) -> bool:
    """이미지 URL 유효성 검사"""
    if not url:
        return False
    try:
        response = requests.head(url, timeout=5, allow_redirects=True)
        return response.status_code == 200
    except:
        return False


def search_photo(photo_api, keywords: list, used_images: set) -> str:
    """Photo API로 이미지 검색"""
    if not photo_api:
        return ''
    for keyword in keywords:
        try:
            results = photo_api.search_photos(keyword, num_of_rows=5)
            if results:
                for photo in results:
                    url = photo.get('galWebImageUrl', '')
                    if url and url not in used_images:
                        url = url.replace('http://', 'https://')
                        if is_image_valid(url):
                            return url
        except:
            continue
    return ''


def search_naver_image(naver_api, query: str, used_images: set) -> str:
    """네이버 이미지 검색"""
    if not naver_api:
        return ''
    try:
        results = naver_api.search(query, display=5)
        for item in results:
            url = item.get('url', '')
            if url and url not in used_images:
                if is_image_valid(url):
                    return url
    except:
        pass
    return ''


def get_image(photo_api, naver_api, place_name: str, do_name: str, sigungu: str, used_images: set) -> str:
    """이미지 획득 (Photo API → 네이버 폴백)"""
    keywords = [f"{sigungu} 캠핑", f"{do_name} 캠핑", f"{sigungu} 자연", f"{sigungu} 풍경", do_name]
    
    image_url = search_photo(photo_api, keywords, used_images)
    if image_url:
        return image_url
    
    naver_keywords = [place_name, f"{sigungu} {place_name}", f"{place_name} 캠핑장"]
    for keyword in naver_keywords:
        image_url = search_naver_image(naver_api, keyword, used_images)
        if image_url:
            return image_url
    return ''

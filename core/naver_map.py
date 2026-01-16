"""네이버 지도 링크 생성 모듈"""

import urllib.parse


def get_naver_map_link(title: str, region: str = "") -> str:
    """네이버 지도 검색 링크 생성 (장소명만 사용)
    
    Args:
        title: 장소명
        region: 지역명 (사용 안 함)
    
    Returns:
        네이버 지도 검색 URL
    """
    if not title:
        return ''
    
    # 장소명만 사용 (지역명 제외)
    encoded = urllib.parse.quote(title)
    return f"https://map.naver.com/v5/search/{encoded}"

"""여행기사 데이터 조회"""
import random
from .utils import extract_place_name, is_only_sigungu, make_naver_map_url, get_image, is_image_valid


def get_available_article_regions(df, category: str) -> list:
    """사용 가능한 기사 지역 목록"""
    if df is None or df.empty:
        return []
    
    cat_col = None
    for col in ['콘텐츠분류명', '분류명', '카테고리']:
        if col in df.columns:
            cat_col = col
            break
    
    region_col = None
    for col in ['지역명', '지역', '도']:
        if col in df.columns:
            region_col = col
            break
    
    if not cat_col or not region_col:
        return []
    
    filtered = df[df[cat_col].str.contains(category, na=False)]
    region_counts = filtered[region_col].value_counts()
    return region_counts[region_counts >= 3].index.tolist()


def get_articles_by_category(loader, category: str, region: str = None, limit: int = None) -> list:
    """카테고리별 여행기사 조회"""
    if loader.article_df is None or loader.article_df.empty:
        return []
    
    # 컬럼 찾기
    cat_col = next((c for c in ['콘텐츠분류명', '분류명', '카테고리'] if c in loader.article_df.columns), None)
    title_col = next((c for c in ['콘텐츠명', '제목', '기사제목'] if c in loader.article_df.columns), None)
    region_col = next((c for c in ['지역명', '지역', '도'] if c in loader.article_df.columns), None)
    sigungu_col = next((c for c in ['시군구명', '시군구'] if c in loader.article_df.columns), None)
    img_col = next((c for c in ['대표이미지 URL', '이미지URL', '이미지'] if c in loader.article_df.columns), None)
    url_col = next((c for c in ['기사상세정보URL', '상세URL', 'URL'] if c in loader.article_df.columns), None)
    
    if not all([cat_col, title_col]):
        return []
    
    filtered = loader.article_df[loader.article_df[cat_col].str.contains(category, na=False)]
    
    # 지역 필터링
    if region and region_col:
        filtered = filtered[filtered[region_col].str.contains(region, na=False)]
    else:
        available_regions = get_available_article_regions(loader.article_df, category)
        if available_regions and region_col:
            selected_region = random.choice(available_regions)
            filtered = filtered[filtered[region_col].str.contains(selected_region, na=False)]
    
    if filtered.empty:
        return []
    
    if limit is None:
        limit = random.randint(3, min(6, len(filtered)))
    
    sampled = filtered.sample(n=min(limit, len(filtered)))
    
    results = []
    used_images = set()
    
    for _, row in sampled.iterrows():
        title = str(row.get(title_col, ''))
        do_name = str(row.get(region_col, '')) if region_col else ''
        sigungu = str(row.get(sigungu_col, '')) if sigungu_col else ''
        img_url = str(row.get(img_col, '')) if img_col else ''
        detail_url = str(row.get(url_col, '')) if url_col else ''
        
        # 이미지 처리
        if img_url and img_url.lower() not in ['nan', 'none', '']:
            img_url = img_url.replace('http://', 'https://')
            if not is_image_valid(img_url):
                img_url = ''
        else:
            img_url = ''
        
        if not img_url:
            img_url = get_image(loader.photo_api, loader.naver_image_api, title, do_name, sigungu, used_images)
        
        if img_url:
            used_images.add(img_url)
        
        # 장소명 추출 및 지도 URL
        place_name = extract_place_name(title)
        map_url = ''
        if place_name and not is_only_sigungu(place_name):
            map_url = make_naver_map_url(place_name)
        
        results.append({
            'title': title,
            'addr': '',
            'region': do_name,
            'do': do_name,
            'sigungu': sigungu,
            'overview': '',
            'detail_url': detail_url,
            'map_url': map_url,
            'image': img_url,
            'source': 'csv_article'
        })
    
    return results

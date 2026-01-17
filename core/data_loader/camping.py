"""캠핑장 데이터 조회"""
import pandas as pd
import random
from .utils import make_naver_map_url, get_image


def filter_by_theme(df: pd.DataFrame, theme: str) -> pd.DataFrame:
    """테마별 필터링"""
    if theme == '글램핑':
        if '주요시설 글램핑' in df.columns:
            return df[pd.to_numeric(df['주요시설 글램핑'], errors='coerce').fillna(0) > 0]
    elif theme == '카라반':
        if '주요시설 카라반' in df.columns:
            return df[pd.to_numeric(df['주요시설 카라반'], errors='coerce').fillna(0) > 0]
    elif theme in ['반려견', '반려견 동반']:
        if '반려동물출입' in df.columns:
            return df[df['반려동물출입'].str.contains('가능', na=False)]
    return df


def get_available_regions(df: pd.DataFrame, theme: str) -> list:
    """사용 가능한 지역 목록"""
    filtered = filter_by_theme(df, theme)
    if filtered.empty or '도' not in filtered.columns:
        return []
    region_counts = filtered['도'].value_counts()
    return region_counts[region_counts >= 3].index.tolist()


def get_camping_by_theme(loader, theme: str, region: str = None, limit: int = None) -> list:
    """테마별 캠핑장 조회"""
    if loader.camping_df is None or loader.camping_df.empty:
        return []
    
    filtered = filter_by_theme(loader.camping_df, theme)
    if filtered.empty:
        return []
    
    # 지역 필터링
    if region and '도' in filtered.columns:
        filtered = filtered[filtered['도'].str.contains(region, na=False)]
    elif '도' in filtered.columns:
        available_regions = get_available_regions(loader.camping_df, theme)
        if available_regions:
            selected_region = random.choice(available_regions)
            filtered = filtered[filtered['도'].str.contains(selected_region, na=False)]
    
    if filtered.empty:
        return []
    
    if limit is None:
        limit = random.randint(3, min(6, len(filtered)))
    
    sampled = filtered.sample(n=min(limit, len(filtered)))
    
    results = []
    used_images = set()
    
    for _, row in sampled.iterrows():
        name = str(row.get('야영장명', ''))
        addr = str(row.get('주소', ''))
        do_name = str(row.get('도', ''))
        sigungu = str(row.get('시군구', ''))
        
        if addr.lower() in ['nan', 'none', ''] or '주소 정보 없음' in addr:
            addr = ''
        
        image_url = get_image(loader.photo_api, loader.naver_image_api, name, do_name, sigungu, used_images)
        if image_url:
            used_images.add(image_url)
        
        results.append({
            'title': name,
            'addr': addr,
            'region': do_name,
            'do': do_name,
            'sigungu': sigungu,
            'overview': '',
            'facilities': '',
            'pets': '',
            'map_url': make_naver_map_url(name),
            'image': image_url,
            'source': 'csv_camping'
        })
    
    return results

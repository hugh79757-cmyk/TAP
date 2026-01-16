"""CSV 파일 기반 데이터 로더 + Photo API 이미지 연동 + 이미지 검증"""

import pandas as pd
import requests
from pathlib import Path
import random
import urllib.parse


class CSVDataLoader:
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / "data"
        self.camping_df = None
        self.articles_df = None
        self.photo_api = None
        self._load_data()
        self._init_photo_api()
    
    def _load_data(self):
        """CSV 파일들 로드"""
        camping_file = self.data_dir / "한국관광공사 전국 야영장 등록 현황_20260106.csv"
        if camping_file.exists():
            self.camping_df = pd.read_csv(camping_file, encoding='cp949', on_bad_lines='skip')
        
        articles_file = self.data_dir / "한국관광공사_여행기사목록_20251107.csv"
        if articles_file.exists():
            self.articles_df = pd.read_csv(articles_file, encoding='cp949', on_bad_lines='skip')
    
    def _init_photo_api(self):
        """Photo API 초기화"""
        try:
            from core.photo_api import load_photo_client
            self.photo_api = load_photo_client()
        except:
            self.photo_api = None
    
    def _make_naver_map_url(self, name: str) -> str:
        """네이버 지도 검색 URL 생성"""
        encoded = urllib.parse.quote(name)
        return f"https://map.naver.com/v5/search/{encoded}"
    
    def _is_image_valid(self, url: str) -> bool:
        """이미지 URL이 실제로 존재하는지 확인"""
        if not url:
            return False
        try:
            resp = requests.head(url, timeout=5, allow_redirects=True)
            return resp.status_code == 200
        except:
            return False
    
    def _search_photo(self, keywords: list, used_images: set) -> str:
        """키워드 리스트로 사진 검색, 중복 제외, https 변환, 유효성 검증"""
        if not self.photo_api:
            return ""
        
        for keyword in keywords:
            if not keyword:
                continue
            try:
                photos = self.photo_api.search_photos(keyword, num_of_rows=10)
                for photo in photos:
                    url = photo.get('galWebImageUrl', '')
                    if url and url not in used_images:
                        # http -> https 변환
                        if url.startswith('http://'):
                            url = url.replace('http://', 'https://')
                        
                        # 이미지 유효성 검증
                        if self._is_image_valid(url):
                            used_images.add(url)
                            return url
            except:
                continue
        return ""
    
    def _get_available_regions(self, theme: str) -> list:
        """해당 테마에서 3개 이상 데이터가 있는 지역 목록 반환"""
        if self.camping_df is None:
            return []
        
        df = self.camping_df.copy()
        
        theme_filters = {
            '글램핑': df['주요시설 글램핑'] > 0,
            '카라반': df['주요시설 카라반'] > 0,
            '반려견 동반': df['반려동물출입'].isin(['가능', '가능(소형견)']),
            '낚시': df['테마환경'].str.contains('낚시', na=False),
            '여름 물놀이': df['테마환경'].str.contains('여름물놀이', na=False),
            '가을 단풍': df['테마환경'].str.contains('가을단풍', na=False),
            '일출 명소': df['테마환경'].str.contains('일출', na=False),
            '일몰 명소': df['테마환경'].str.contains('일몰', na=False),
            '걷기길': df['테마환경'].str.contains('걷기길', na=False),
            '액티비티': df['테마환경'].str.contains('액티비티', na=False),
        }
        
        if theme in theme_filters:
            df = df[theme_filters[theme]]
        
        region_counts = df.groupby('도').size()
        valid_regions = region_counts[region_counts >= 3].index.tolist()
        
        return valid_regions
    
    def get_camping_by_theme(self, theme: str, region: str = None, limit: int = None) -> list:
        """테마별 캠핑장 조회 + 이미지 + 지역 필터링 강화"""
        if self.camping_df is None:
            return []
        
        df = self.camping_df.copy()
        
        theme_filters = {
            '글램핑': df['주요시설 글램핑'] > 0,
            '카라반': df['주요시설 카라반'] > 0,
            '반려견 동반': df['반려동물출입'].isin(['가능', '가능(소형견)']),
            '낚시': df['테마환경'].str.contains('낚시', na=False),
            '여름 물놀이': df['테마환경'].str.contains('여름물놀이', na=False),
            '가을 단풍': df['테마환경'].str.contains('가을단풍', na=False),
            '일출 명소': df['테마환경'].str.contains('일출', na=False),
            '일몰 명소': df['테마환경'].str.contains('일몰', na=False),
            '걷기길': df['테마환경'].str.contains('걷기길', na=False),
            '액티비티': df['테마환경'].str.contains('액티비티', na=False),
        }
        
        if theme in theme_filters:
            df = df[theme_filters[theme]]
        
        if not region:
            available_regions = self._get_available_regions(theme)
            if not available_regions:
                return []
            region = random.choice(available_regions)
        
        df = df[df['도'] == region]
        
        if len(df) == 0:
            return []
        
        if limit is None:
            limit = random.randint(3, min(6, len(df)))
        
        if len(df) > limit:
            df = df.sample(n=limit)
        
        results = []
        used_images = set()
        
        for _, row in df.iterrows():
            name = str(row['야영장명']).strip()
            addr = str(row['주소']) if pd.notna(row['주소']) and str(row['주소']) != 'nan' else ''
            do_name = str(row['도']) if pd.notna(row['도']) else ''
            sigungu = str(row['시군구']) if pd.notna(row['시군구']) else ''
            
            search_keywords = [
                f"{sigungu} 캠핑" if sigungu else None,
                f"{do_name} 캠핑",
                f"{sigungu} 자연" if sigungu else None,
                f"{sigungu} 풍경" if sigungu else None,
                do_name
            ]
            image_url = self._search_photo([k for k in search_keywords if k], used_images)
            
            results.append({
                'title': name,
                'addr': addr,
                'region': f"{do_name} {sigungu}".strip(),
                'do': do_name,
                'sigungu': sigungu,
                'overview': str(row.get('테마환경', '')) if pd.notna(row.get('테마환경', '')) else '',
                'facilities': str(row.get('부대시설', '')) if pd.notna(row.get('부대시설', '')) else '',
                'pets': str(row.get('반려동물출입', '')) if pd.notna(row.get('반려동물출입', '')) else '',
                'map_url': self._make_naver_map_url(name),
                'image': image_url,
                'source': 'csv_camping'
            })
        
        return results
    
    def get_articles_by_category(self, category: str, region: str = None, limit: int = None) -> list:
        """카테고리별 여행기사 조회"""
        if self.articles_df is None:
            return []
        
        df = self.articles_df.copy()
        
        if category:
            df = df[df['콘텐츠분류명'].str.contains(category, na=False)]
        
        if region:
            df = df[df['지역명'].str.contains(region, na=False)]
        
        if len(df) == 0:
            return []
        
        if limit is None:
            limit = random.randint(3, min(6, len(df)))
        
        if len(df) > limit:
            df = df.sample(n=limit)
        
        results = []
        for _, row in df.iterrows():
            name = str(row['콘텐츠명']).strip()
            image_url = str(row.get('대표이미지 URL', '')) if pd.notna(row.get('대표이미지 URL', '')) else ''
            
            if image_url.startswith('http://'):
                image_url = image_url.replace('http://', 'https://')
            
            # 이미지 유효성 검증
            if image_url and not self._is_image_valid(image_url):
                image_url = ''
            
            results.append({
                'title': name,
                'region': str(row['지역명']) if pd.notna(row['지역명']) else '',
                'do': str(row['지역명']) if pd.notna(row['지역명']) else '',
                'category': str(row['콘텐츠분류명']) if pd.notna(row['콘텐츠분류명']) else '',
                'image': image_url,
                'detail_url': str(row.get('기사상세정보URL', '')) if pd.notna(row.get('기사상세정보URL', '')) else '',
                'addr': '',
                'overview': str(row['콘텐츠분류명']) if pd.notna(row['콘텐츠분류명']) else '',
                'map_url': self._make_naver_map_url(name),
                'source': 'csv_article'
            })
        
        return results
    
    def get_random_theme(self) -> dict:
        """랜덤 테마 선택"""
        camping_themes = [
            {'theme': '글램핑', 'type': 'camping'},
            {'theme': '카라반', 'type': 'camping'},
            {'theme': '반려견 동반', 'type': 'camping'},
        ]
        
        article_themes = [
            {'theme': '자연풍경여행', 'type': 'article'},
            {'theme': '맛있는여행', 'type': 'article'},
            {'theme': '전통·역사여행', 'type': 'article'},
            {'theme': '액티비티여행', 'type': 'article'},
            {'theme': '명소여행', 'type': 'article'},
        ]
        
        if random.random() < 0.7:
            return random.choice(camping_themes)
        else:
            return random.choice(article_themes)
    
    def get_items_by_theme(self, theme_data: dict, limit: int = None) -> list:
        """테마에 따라 아이템 조회"""
        theme = theme_data['theme']
        theme_type = theme_data['type']
        
        if theme_type == 'camping':
            return self.get_camping_by_theme(theme, limit=limit)
        elif theme_type == 'article':
            return self.get_articles_by_category(theme, limit=limit)
        return []


def load_csv_loader():
    return CSVDataLoader()

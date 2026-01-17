"""데이터 로더 베이스 클래스"""
import pandas as pd
import random
from pathlib import Path


class BaseDataLoader:
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent.parent / "data"
        self.camping_df = None
        self.article_df = None
        self.photo_api = None
        self.naver_image_api = None
        self._load_data()
        self._init_apis()
    
    def _load_data(self):
        camping_file = self.data_dir / "고캠핑정보조회_야영장정보목록_20260106.csv"
        # [v10.0 비활성화] 여행기사 - 이미 큐레이팅된 콘텐츠 재사용은 품질 저하 유발
        # article_file = self.data_dir / "한국관광공사_여행기사목록_20251107.csv"
        
        try:
            self.camping_df = pd.read_csv(camping_file, encoding='cp949', on_bad_lines='skip')
        except:
            try:
                self.camping_df = pd.read_csv(camping_file, encoding='utf-8', on_bad_lines='skip')
            except:
                self.camping_df = pd.DataFrame()
        
        # [v10.0 비활성화] 여행기사 CSV 로드 - 2026-01-17 제거
        # 사유: 이미 가공된 콘텐츠를 AI로 재가공 시 품질 저하
        # 대안: 캠핑장 원본 데이터 + 네이버 이미지 검색으로 오리지널 콘텐츠 생성
        # try:
        #     self.article_df = pd.read_csv(article_file, encoding='euc-kr', on_bad_lines='skip')
        # except:
        #     try:
        #         self.article_df = pd.read_csv(article_file, encoding='cp949', on_bad_lines='skip')
        #     except:
        #         self.article_df = pd.DataFrame()
        self.article_df = pd.DataFrame()  # 빈 DataFrame 유지 (하위 호환성)
    
    def _init_apis(self):
        try:
            from core.photo_api import load_photo_client
            self.photo_api = load_photo_client()
        except:
            self.photo_api = None
        
        try:
            from core.naver_image_api import load_naver_image_api
            self.naver_image_api = load_naver_image_api()
        except:
            self.naver_image_api = None
    
    def get_random_theme(self) -> tuple:
        """랜덤 테마 선택"""
        camping_themes = ['글램핑', '카라반', '반려동물 동반']
        
        # [v10.0 비활성화] 여행기사 테마 - 2026-01-17 제거
        # article_categories = ['건축기행', '맛집', '액티비티', '드라이브', '명소']
        
        # [v10.0 변경] 기존: 캠핑 50% / 기사 50% → 변경: 캠핑 100%
        # if random.random() < 0.5:
        #     return ('camping', random.choice(camping_themes))
        # else:
        #     return ('article', random.choice(article_categories))
        
        return ('camping', random.choice(camping_themes))

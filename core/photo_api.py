# core/photo_api.py
"""한국관광공사 관광사진 정보 API 모듈"""

import requests
from typing import Optional
from pathlib import Path
import yaml


class PhotoAPI:
    """관광사진 API 클라이언트"""
    
    def __init__(self, service_key: str):
        self.service_key = service_key
        self.base_url = "http://apis.data.go.kr/B551011/PhotoGalleryService1"
    
    def _request(self, endpoint: str, params: dict) -> dict:
        default_params = {
            "serviceKey": self.service_key,
            "MobileOS": "ETC",
            "MobileApp": "TourAutoPublisher",
            "_type": "json"
        }
        params.update(default_params)
        
        url = f"{self.base_url}/{endpoint}"
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        header = data.get("response", {}).get("header", {})
        if header.get("resultCode") != "0000":
            error_msg = header.get("resultMsg", "Unknown error")
            raise Exception(f"Photo API Error: {error_msg}")
        
        return data
    
    def get_photo_list(
        self,
        num_of_rows: int = 20,
        page_no: int = 1,
        arrange: str = "A"
    ) -> list:
        """사진 갤러리 목록 조회 - galleryList1"""
        params = {
            "numOfRows": num_of_rows,
            "pageNo": page_no,
            "arrange": arrange
        }
        
        data = self._request("galleryList1", params)
        items = data.get("response", {}).get("body", {}).get("items", {})
        
        if not items:
            return []
        
        return items.get("item", [])
    
    def search_photos(
        self,
        keyword: str,
        num_of_rows: int = 20,
        page_no: int = 1
    ) -> list:
        """키워드로 사진 검색 - gallerySearchList1"""
        params = {
            "numOfRows": num_of_rows,
            "pageNo": page_no,
            "keyword": keyword
        }
        
        data = self._request("gallerySearchList1", params)
        items = data.get("response", {}).get("body", {}).get("items", {})
        
        if not items:
            return []
        
        item_data = items.get("item", [])
        # 단일 항목이면 리스트로 변환
        if isinstance(item_data, dict):
            return [item_data]
        return item_data
    
    def get_photo_detail(self, content_id: str) -> list:
        """사진 상세 목록 조회 - galleryDetailList1"""
        params = {
            "galContentId": content_id
        }
        
        data = self._request("galleryDetailList1", params)
        items = data.get("response", {}).get("body", {}).get("items", {})
        
        if not items:
            return []
        
        item_data = items.get("item", [])
        if isinstance(item_data, dict):
            return [item_data]
        return item_data
    
    def get_photos_by_theme(self, theme: str, count: int = 10) -> list:
        """테마별 사진 조회"""
        theme_keywords = {
            "바다": ["해변", "바다", "해수욕장", "일몰", "해안"],
            "산": ["산", "등산", "트레킹", "단풍", "숲"],
            "캠핑": ["캠핑", "글램핑", "야영", "자연"],
            "도시": ["야경", "도심", "거리", "서울"],
            "전통": ["한옥", "고궁", "전통", "사찰"],
            "축제": ["축제", "행사", "공연", "꽃"],
            "걷기": ["길", "산책", "둘레길", "공원"],
            "자전거": ["자전거", "라이딩", "강변"],
        }
        
        keywords = theme_keywords.get(theme, [theme])
        
        all_photos = []
        for keyword in keywords:
            try:
                photos = self.search_photos(keyword, num_of_rows=10)
                all_photos.extend(photos)
            except Exception:
                continue
        
        # 중복 제거
        seen = set()
        unique_photos = []
        for photo in all_photos:
            photo_id = photo.get("galContentId")
            if photo_id and photo_id not in seen:
                seen.add(photo_id)
                unique_photos.append(photo)
        
        return unique_photos[:count]


def load_photo_client() -> PhotoAPI:
    config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    service_key = config["tour_api"]["service_key"]
    return PhotoAPI(service_key)

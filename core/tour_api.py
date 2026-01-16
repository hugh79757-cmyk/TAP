# core/tour_api.py
"""한국관광공사 TourAPI 연동 모듈"""

import requests
from typing import Optional
from pathlib import Path
import yaml


class TourAPI:
    """TourAPI 클라이언트"""
    
    CONTENT_TYPES = {
        "관광지": 12,
        "문화시설": 14,
        "축제": 15,
        "여행코스": 25,
        "레포츠": 28,
        "숙박": 32,
        "쇼핑": 38,
        "음식점": 39
    }
    
    AREA_CODES = {
        "서울": 1, "인천": 2, "대전": 3, "대구": 4, "광주": 5,
        "부산": 6, "울산": 7, "세종": 8, "경기": 31, "강원": 32,
        "충북": 33, "충남": 34, "경북": 35, "경남": 36,
        "전북": 37, "전남": 38, "제주": 39
    }
    
    def __init__(self, service_key: str):
        self.service_key = service_key
        self.base_url = "http://apis.data.go.kr/B551011/KorService1"
    
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
        
        if data.get("response", {}).get("header", {}).get("resultCode") != "0000":
            error_msg = data.get("response", {}).get("header", {}).get("resultMsg", "Unknown error")
            raise Exception(f"API Error: {error_msg}")
        
        return data
    
    def search_keyword(
        self,
        keyword: str,
        num_of_rows: int = 20,
        page_no: int = 1,
        content_type: Optional[int] = None,
        area_code: Optional[int] = None
    ) -> list:
        params = {
            "keyword": keyword,
            "numOfRows": num_of_rows,
            "pageNo": page_no
        }
        
        if content_type:
            params["contentTypeId"] = content_type
        if area_code:
            params["areaCode"] = area_code
        
        data = self._request("searchKeyword1", params)
        items = data.get("response", {}).get("body", {}).get("items", {})
        
        if not items:
            return []
        
        return items.get("item", [])
    
    def get_area_based_list(
        self,
        area_code: int,
        num_of_rows: int = 20,
        content_type: Optional[int] = None
    ) -> list:
        params = {
            "areaCode": area_code,
            "numOfRows": num_of_rows,
            "pageNo": 1,
            "arrange": "Q"
        }
        
        if content_type:
            params["contentTypeId"] = content_type
        
        data = self._request("areaBasedList1", params)
        items = data.get("response", {}).get("body", {}).get("items", {})
        
        if not items:
            return []
        
        return items.get("item", [])
    
    def get_detail_common(self, content_id: str) -> dict:
        params = {
            "contentId": content_id,
            "defaultYN": "Y",
            "firstImageYN": "Y",
            "addrinfoYN": "Y",
            "overviewYN": "Y"
        }
        
        data = self._request("detailCommon1", params)
        items = data.get("response", {}).get("body", {}).get("items", {})
        
        if not items:
            return {}
        
        item_list = items.get("item", [])
        return item_list[0] if item_list else {}


def load_api_client() -> TourAPI:
    config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    service_key = config["tour_api"]["service_key"]
    return TourAPI(service_key)

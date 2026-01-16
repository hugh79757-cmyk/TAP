# core/durunubi_api.py
"""한국관광공사 두루누비(걷기/자전거길) API 모듈"""

import requests
from typing import Optional
from pathlib import Path
import yaml


class DurunubiAPI:
    """두루누비 API 클라이언트"""
    
    COURSE_TYPES = {
        "걷기길": "1",
        "자전거길": "2"
    }
    
    def __init__(self, service_key: str):
        self.service_key = service_key
        self.base_url = "https://apis.data.go.kr/B551011/Durunubi"
    
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
            raise Exception(f"Durunubi API Error: {error_msg}")
        
        return data
    
    def get_course_list(
        self,
        course_type: str = "1",
        num_of_rows: int = 20,
        page_no: int = 1,
        area_code: Optional[str] = None
    ) -> list:
        params = {
            "numOfRows": num_of_rows,
            "pageNo": page_no,
            "crsKorNm": "",
            "routeIdx": "",
            "crsLevel": "",
            "brdDiv": course_type
        }
        
        if area_code:
            params["areaCd"] = area_code
        
        data = self._request("courseList", params)
        items = data.get("response", {}).get("body", {}).get("items", {})
        
        if not items:
            return []
        
        return items.get("item", [])
    
    def get_course_detail(self, route_idx: str) -> dict:
        params = {"routeIdx": route_idx}
        
        data = self._request("courseDetail", params)
        items = data.get("response", {}).get("body", {}).get("items", {})
        
        if not items:
            return {}
        
        item_list = items.get("item", [])
        return item_list[0] if item_list else {}
    
    def search_walking_trails(
        self,
        keyword: str = "",
        num_of_rows: int = 20,
        area_code: Optional[str] = None
    ) -> list:
        params = {
            "numOfRows": num_of_rows,
            "pageNo": 1,
            "crsKorNm": keyword,
            "brdDiv": "1"
        }
        
        if area_code:
            params["areaCd"] = area_code
        
        data = self._request("courseList", params)
        items = data.get("response", {}).get("body", {}).get("items", {})
        
        if not items:
            return []
        
        return items.get("item", [])
    
    def search_bike_trails(
        self,
        keyword: str = "",
        num_of_rows: int = 20,
        area_code: Optional[str] = None
    ) -> list:
        params = {
            "numOfRows": num_of_rows,
            "pageNo": 1,
            "crsKorNm": keyword,
            "brdDiv": "2"
        }
        
        if area_code:
            params["areaCd"] = area_code
        
        data = self._request("courseList", params)
        items = data.get("response", {}).get("body", {}).get("items", {})
        
        if not items:
            return []
        
        return items.get("item", [])
    
    def get_popular_trails(self, trail_type: str = "walking", count: int = 10) -> list:
        if trail_type == "walking":
            items = self.get_course_list(course_type="1", num_of_rows=count * 2)
        else:
            items = self.get_course_list(course_type="2", num_of_rows=count * 2)
        
        with_image = [i for i in items if i.get("crsImg")]
        without_image = [i for i in items if not i.get("crsImg")]
        
        result = with_image + without_image
        return result[:count]


def load_durunubi_client() -> DurunubiAPI:
    config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    service_key = config["tour_api"]["service_key"]
    return DurunubiAPI(service_key)

"""한국관광공사 두루누비(걷기/자전거길) API 모듈"""

import os
import requests
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class DurunubiAPI:
    """두루누비 API 클라이언트"""
    
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
        
        item = items.get("item", [])
        return item if isinstance(item, list) else [item]


def load_durunubi_client() -> DurunubiAPI:
    service_key = os.getenv('TOUR_API_KEY')
    if not service_key:
        raise ValueError("TOUR_API_KEY가 .env에 설정되지 않았습니다.")
    return DurunubiAPI(service_key)

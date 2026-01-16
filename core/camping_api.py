"""한국관광공사 고캠핑 API 모듈"""

import requests
from pathlib import Path
import yaml


class CampingAPI:
    """고캠핑 API 클라이언트"""
    
    def __init__(self, service_key: str):
        self.service_key = service_key
        self.base_url = "https://apis.data.go.kr/B551011/GoCamping"
    
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
            raise Exception(f"GoCamping API Error: {error_msg}")
        
        return data
    
    def get_campsite_list(self, num_of_rows: int = 20, page_no: int = 1) -> list:
        params = {
            "numOfRows": num_of_rows,
            "pageNo": page_no
        }
        
        data = self._request("basedList", params)
        items = data.get("response", {}).get("body", {}).get("items", {})
        
        if not items:
            return []
        
        return items.get("item", [])
    
    def search_campsite(self, keyword: str, num_of_rows: int = 20) -> list:
        params = {
            "numOfRows": num_of_rows,
            "pageNo": 1,
            "keyword": keyword
        }
        
        data = self._request("searchList", params)
        items = data.get("response", {}).get("body", {}).get("items", {})
        
        if not items:
            return []
        
        return items.get("item", [])


def load_camping_client() -> CampingAPI:
    config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    service_key = config["tour_api"]["service_key"]
    return CampingAPI(service_key)

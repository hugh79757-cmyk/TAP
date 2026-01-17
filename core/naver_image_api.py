# core/naver_image_api.py
"""네이버 이미지 검색 API 모듈"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()


class NaverImageAPI:
    def __init__(self):
        self.client_id = os.getenv('NAVER_CLIENT_ID')
        self.client_secret = os.getenv('NAVER_CLIENT_SECRET')
        self.base_url = "https://openapi.naver.com/v1/search/image"
    
    def search(self, query: str, display: int = 5) -> list:
        """이미지 검색"""
        if not self.client_id or not self.client_secret:
            return []
        
        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret
        }
        params = {
            "query": query,
            "display": display,
            "sort": "sim"
        }
        
        try:
            resp = requests.get(self.base_url, headers=headers, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            
            results = []
            for item in data.get('items', []):
                url = item.get('link', '')
                # https 변환
                if url.startswith('http://'):
                    url = url.replace('http://', 'https://')
                results.append({
                    'url': url,
                    'title': item.get('title', '').replace('<b>', '').replace('</b>', ''),
                    'width': item.get('sizewidth', ''),
                    'height': item.get('sizeheight', ''),
                })
            return results
        except:
            return []
    
    def get_image_for_place(self, place_name: str, region: str = "") -> str:
        """장소명으로 이미지 URL 반환"""
        # 검색어 조합
        queries = [
            f"{place_name}",
            f"{region} {place_name}" if region else None,
            f"{place_name} 캠핑장",
        ]
        
        for query in queries:
            if not query:
                continue
            results = self.search(query, display=3)
            for r in results:
                url = r.get('url', '')
                if url and self._is_valid_image(url):
                    return url
        return ""
    
    def _is_valid_image(self, url: str) -> bool:
        """이미지 URL 유효성 검사"""
        if not url:
            return False
        try:
            resp = requests.head(url, timeout=5, allow_redirects=True)
            return resp.status_code == 200
        except:
            return False


def load_naver_image_api():
    return NaverImageAPI()

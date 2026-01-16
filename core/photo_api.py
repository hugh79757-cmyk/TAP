import os
import requests
from dotenv import load_dotenv

load_dotenv()

class PhotoAPI:
    def __init__(self):
        self.service_key = os.getenv('TOUR_API_KEY')
        self.base_url = "http://apis.data.go.kr/B551011/PhotoGalleryService1"

    def search_photos(self, keyword, num_of_rows=10):
        if not self.service_key: return []
        params = {
            "serviceKey": self.service_key,
            "numOfRows": num_of_rows,
            "MobileOS": "ETC",
            "MobileApp": "TAP",
            "_type": "json",
            "keyword": keyword
        }
        try:
            resp = requests.get(f"{self.base_url}/gallerySearchList1", params=params, timeout=30)
            items = resp.json().get('response', {}).get('body', {}).get('items', {}).get('item', [])
            return [items] if isinstance(items, dict) else items
        except:
            return []

def load_photo_client():
    return PhotoAPI()

import os
import requests
from dotenv import load_dotenv

load_dotenv()

class CampingAPI:
    def __init__(self):
        self.service_key = os.getenv('TOUR_API_KEY')
        self.base_url = "https://apis.data.go.kr/B551011/GoCamping"

    def get_campsite_list(self, num_of_rows=500):
        if not self.service_key:
            raise ValueError("TOUR_API_KEY가 설정되지 않았습니다.")
        params = {
            "serviceKey": self.service_key,
            "numOfRows": num_of_rows,
            "MobileOS": "ETC",
            "MobileApp": "TAP",
            "_type": "json"
        }
        try:
            resp = requests.get(f"{self.base_url}/basedList", params=params, timeout=30)
            return resp.json().get('response', {}).get('body', {}).get('items', {}).get('item', [])
        except Exception as e:
            print(f"Camping API Error: {e}")
            return []

def load_camping_client():
    return CampingAPI()

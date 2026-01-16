import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()

class WordPressPublisher:
    def __init__(self):
        self.site_url = os.getenv('WP_SITE_URL', '').rstrip('/')
        self.username = os.getenv('WP_USERNAME')
        self.password = os.getenv('WP_APP_PASSWORD')
        self.auth = HTTPBasicAuth(self.username, self.password)

    def create_post(self, title, content, status='draft'):
        if not all([self.site_url, self.username, self.password]):
            raise ValueError("WP 설정 환경 변수가 부족합니다.")
        
        url = f"{self.site_url}/wp-json/wp/v2/posts"
        data = {'title': title, 'content': content, 'status': status}
        resp = requests.post(url, auth=self.auth, json=data)
        resp.raise_for_status()
        return resp.json()

def load_publisher():
    return WordPressPublisher()

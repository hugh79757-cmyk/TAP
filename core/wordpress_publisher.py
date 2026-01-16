"""WordPress 발행 모듈"""

import requests
from requests.auth import HTTPBasicAuth
from pathlib import Path
import yaml
import logging
import re

logger = logging.getLogger(__name__)


class WordPressPublisher:
    def __init__(self, site_url: str, username: str, app_password: str):
        self.site_url = site_url.rstrip('/')
        self.auth = HTTPBasicAuth(username, app_password)
        self.api_base = f"{self.site_url}/wp-json/wp/v2"
        
        try:
            from core.image_optimizer import load_image_optimizer
            self.image_optimizer = load_image_optimizer(max_width=800, quality=70)
        except ImportError:
            self.image_optimizer = None
        
        self.uploaded_images = {}
    
    def _request(self, method: str, endpoint: str, **kwargs):
        url = f"{self.api_base}/{endpoint}"
        response = requests.request(method, url, auth=self.auth, **kwargs)
        response.raise_for_status()
        return response.json()
    
    def create_post(self, title: str, content: str, status: str = 'draft',
                    categories: list = None, tags: list = None,
                    featured_image_url: str = None, excerpt: str = None) -> dict:
        
        content = self._process_content_images(content)
        
        featured_media_id = None
        if featured_image_url:
            featured_media_id = self._upload_image_from_url(featured_image_url, title)
        
        data = {
            'title': title,
            'content': content,
            'status': status,
            'excerpt': excerpt or ''
        }
        
        if categories:
            data['categories'] = categories
        if featured_media_id:
            data['featured_media'] = featured_media_id
        
        # 태그 처리 제거
        
        result = self._request('POST', 'posts', json=data)
        
        return {
            'id': result.get('id'),
            'url': result.get('link'),
            'status': result.get('status')
        }
    
    def _process_content_images(self, content: str) -> str:
        if not self.image_optimizer:
            return content
        
        img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
        
        def replace_image(match):
            full_tag = match.group(0)
            img_url = match.group(1)
            
            if self.site_url in img_url:
                return full_tag
            
            if img_url in self.uploaded_images:
                new_url = self.uploaded_images[img_url]
                return full_tag.replace(img_url, new_url)
            
            try:
                optimized = self.image_optimizer.optimize_from_url(img_url)
                if optimized:
                    media_id = self._upload_optimized_image(optimized)
                    if media_id:
                        media_info = self._request('GET', f'media/{media_id}')
                        new_url = media_info.get('source_url', img_url)
                        self.uploaded_images[img_url] = new_url
                        logger.info(f"이미지 업로드: {optimized['size_kb']:.0f}KB")
                        return full_tag.replace(img_url, new_url)
            except Exception as e:
                logger.error(f"이미지 처리 실패: {e}")
            
            return full_tag
        
        return re.sub(img_pattern, replace_image, content)
    
    def _upload_optimized_image(self, optimized: dict) -> int:
        try:
            headers = {
                'Content-Disposition': f'attachment; filename="{optimized["filename"]}"',
                'Content-Type': optimized['mime_type']
            }
            
            response = requests.post(
                f"{self.api_base}/media",
                auth=self.auth,
                headers=headers,
                data=optimized['data']
            )
            response.raise_for_status()
            
            return response.json().get('id')
            
        except Exception as e:
            logger.error(f"이미지 업로드 실패: {e}")
            return None
    
    def _upload_image_from_url(self, image_url: str, title: str) -> int:
        if image_url in self.uploaded_images:
            return None
        
        if self.image_optimizer:
            optimized = self.image_optimizer.optimize_from_url(image_url)
            if optimized:
                media_id = self._upload_optimized_image(optimized)
                if media_id:
                    try:
                        media_info = self._request('GET', f'media/{media_id}')
                        self.uploaded_images[image_url] = media_info.get('source_url', '')
                    except:
                        pass
                    return media_id
        
        try:
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            filename = image_url.split('/')[-1].split('?')[0]
            
            headers = {
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Type': response.headers.get('Content-Type', 'image/jpeg')
            }
            
            upload_response = requests.post(
                f"{self.api_base}/media",
                auth=self.auth,
                headers=headers,
                data=response.content
            )
            upload_response.raise_for_status()
            
            return upload_response.json().get('id')
            
        except Exception as e:
            logger.error(f"이미지 업로드 실패: {e}")
            return None


def load_publisher():
    config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    wp = config.get('wordpress', {})
    return WordPressPublisher(
        site_url=wp.get('site_url', ''),
        username=wp.get('username', ''),
        app_password=wp.get('app_password', '')
    )

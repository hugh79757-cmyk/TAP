"""이미지 최적화 모듈 - 리사이징 및 WebP 변환"""

import requests
from PIL import Image
from io import BytesIO
from pathlib import Path
import hashlib
import logging

logger = logging.getLogger(__name__)


class ImageOptimizer:
    """이미지 다운로드, 리사이징, WebP 변환"""
    
    def __init__(self, max_width: int = 800, quality: int = 70):
        self.max_width = max_width
        self.quality = quality
        self.cache_dir = Path(__file__).parent.parent / "cache" / "images"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _fix_url(self, url: str) -> str:
        """http → https 변환"""
        if url and url.startswith('http://'):
            return url.replace('http://', 'https://')
        return url
    
    def _is_valid_url(self, url: str) -> bool:
        """유효한 URL인지 확인"""
        if not url:
            return False
        if not url.startswith('http'):
            return False
        if url in ['이미지URL', 'URL', 'http://example.com']:
            return False
        return True
    
    def optimize_from_url(self, image_url: str) -> dict:
        """URL에서 이미지 다운로드 후 최적화
        
        Returns:
            dict: {data, mime_type, filename, size_kb} 또는 None
        """
        if not self._is_valid_url(image_url):
            logger.warning(f"유효하지 않은 URL: {image_url}")
            return None
        
        image_url = self._fix_url(image_url)
        
        try:
            # 캐시 확인
            cache_key = hashlib.md5(image_url.encode()).hexdigest()
            cache_path = self.cache_dir / f"{cache_key}.webp"
            
            if cache_path.exists():
                logger.info(f"캐시 사용: {cache_key[:8]}...")
                with open(cache_path, 'rb') as f:
                    data = f.read()
                return {
                    'data': data,
                    'mime_type': 'image/webp',
                    'filename': f"{cache_key}.webp",
                    'size_kb': len(data) / 1024
                }
            
            # 다운로드
            logger.info(f"이미지 다운로드: {image_url[:60]}...")
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            original_data = response.content
            original_kb = len(original_data) / 1024
            
            # PIL로 열기
            img = Image.open(BytesIO(original_data))
            
            # RGBA → RGB 변환
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # 리사이징
            if img.width > self.max_width:
                ratio = self.max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((self.max_width, new_height), Image.LANCZOS)
            
            # WebP로 저장
            output = BytesIO()
            img.save(output, format='WEBP', quality=self.quality, optimize=True)
            optimized_data = output.getvalue()
            
            optimized_kb = len(optimized_data) / 1024
            
            # 최적화 후 더 커지면 원본 사용 (JPEG로)
            if optimized_kb >= original_kb:
                logger.info(f"원본 유지: {original_kb:.0f}KB (WebP {optimized_kb:.0f}KB)")
                
                # 원본을 리사이징만 해서 JPEG로 저장
                img_original = Image.open(BytesIO(original_data))
                if img_original.mode in ('RGBA', 'P'):
                    img_original = img_original.convert('RGB')
                
                if img_original.width > self.max_width:
                    ratio = self.max_width / img_original.width
                    new_height = int(img_original.height * ratio)
                    img_original = img_original.resize((self.max_width, new_height), Image.LANCZOS)
                
                output_jpg = BytesIO()
                img_original.save(output_jpg, format='JPEG', quality=self.quality, optimize=True)
                final_data = output_jpg.getvalue()
                final_kb = len(final_data) / 1024
                
                # JPEG도 원본보다 크면 그냥 원본
                if final_kb >= original_kb:
                    return {
                        'data': original_data,
                        'mime_type': 'image/jpeg',
                        'filename': f"{cache_key}.jpg",
                        'size_kb': original_kb
                    }
                
                return {
                    'data': final_data,
                    'mime_type': 'image/jpeg',
                    'filename': f"{cache_key}.jpg",
                    'size_kb': final_kb
                }
            
            reduction = (1 - optimized_kb / original_kb) * 100
            logger.info(f"최적화: {original_kb:.0f}KB → {optimized_kb:.0f}KB ({reduction:.0f}% 감소)")
            
            # 캐시 저장
            with open(cache_path, 'wb') as f:
                f.write(optimized_data)
            
            return {
                'data': optimized_data,
                'mime_type': 'image/webp',
                'filename': f"{cache_key}.webp",
                'size_kb': optimized_kb
            }
            
        except Exception as e:
            logger.error(f"이미지 최적화 실패: {e}")
            return None


def load_image_optimizer(max_width: int = 800, quality: int = 70):
    return ImageOptimizer(max_width=max_width, quality=quality)

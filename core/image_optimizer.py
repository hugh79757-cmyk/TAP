import requests
from PIL import Image
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

class ImageOptimizer:
    def __init__(self, max_width=800, quality=75):
        self.max_width = max_width
        self.quality = quality

    def optimize(self, url):
        try:
            resp = requests.get(url, timeout=20)
            img = Image.open(BytesIO(resp.content))
            
            # RGB 변환 (PNG/RGBA 대응)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            # 리사이징
            if img.width > self.max_width:
                ratio = self.max_width / img.width
                img = img.resize((self.max_width, int(img.height * ratio)), Image.LANCZOS)
            
            # WebP 변환
            output = BytesIO()
            img.save(output, format="WEBP", quality=self.quality, optimize=True)
            return output.getvalue()
        except Exception as e:
            logger.error(f"이미지 최적화 실패: {e}")
            return None

def load_optimizer():
    return ImageOptimizer()

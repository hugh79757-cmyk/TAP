import logging
import requests
import imagehash
from PIL import Image
from io import BytesIO
from core.database import Session, ImageLog
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class ImageHandler:
    PHASH_THRESHOLD = 6

    def __init__(self, photo_api=None):
        self.photo_api = photo_api
        self.session_used = set()

    def _get_phash(self, image_content):
        try:
            img = Image.open(BytesIO(image_content)).convert('RGB')
            return str(imagehash.phash(img))
        except Exception as e:
            logger.error(f"Hash 생성 실패: {e}")
            return None

    def is_duplicate(self, url):
        if not url:
            return True
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            content = resp.content
            
            current_hash = self._get_phash(content)
            if not current_hash: return True

            with Session() as session:
                if session.query(ImageLog).filter_by(url=url).first():
                    return True
                
                all_images = session.query(ImageLog).all()
                for img_record in all_images:
                    if img_record.phash:
                        distance = imagehash.hex_to_hash(current_hash) - imagehash.hex_to_hash(img_record.phash)
                        if distance < self.PHASH_THRESHOLD:
                            return True
                
                new_img = ImageLog(url=url, phash=current_hash)
                session.add(new_img)
                session.commit()
                return False
        except Exception as e:
            logger.warning(f"이미지 중복 체크 실패: {e}")
            return True

    def get_image(self, item, region="", theme=""):
        # 1. 원본 이미지 시도
        url = item.get('firstimage', '')
        if url and not self.is_duplicate(url):
            return url
        
        # 2. PhotoAPI로 검색
        if self.photo_api:
            title = item.get('title', '')
            keywords = self._build_search_keywords(title, region, theme)
            logger.info(f"이미지 검색 키워드: {keywords}")
            
            for keyword in keywords:
                photos = self.photo_api.search_photos(keyword, num_of_rows=5)
                for p in photos:
                    p_url = p.get('galWebImageUrl', '')
                    if p_url and not self.is_duplicate(p_url):
                        return p_url
        
        return ""

    def _build_search_keywords(self, title, region, theme):
        """검색 키워드 조합 생성"""
        keywords = []
        
        # 제목에서 핵심어 추출
        if title:
            # "서해랑길 88코스" -> "서해랑길"
            core_name = title.split()[0] if ' ' in title else title
            keywords.append(core_name)
            keywords.append(title)
        
        # 지역 + 테마 조합
        if region and theme:
            keywords.append(f"{region} {theme}")
        
        if region:
            keywords.append(region)
        
        if theme:
            keywords.append(theme)
        
        return [k for k in keywords if k]

    def check_images_available(self, items, region="", theme="", min_images=2):
        found_count = 0
        
        for item in items:
            url = item.get('firstimage', '')
            if url:
                found_count += 1
            elif self.photo_api:
                title = item.get('title', '')
                keywords = self._build_search_keywords(title, region, theme)
                for keyword in keywords:
                    photos = self.photo_api.search_photos(keyword, num_of_rows=1)
                    if photos:
                        found_count += 1
                        break
            
            if found_count >= min_images:
                break
        
        logger.info(f"이미지 사전 체크: {found_count}개 확보 가능 (최소 {min_images}개 필요)")
        return found_count >= min_images

    def reset(self):
        self.session_used = set()

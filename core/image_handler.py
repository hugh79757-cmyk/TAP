"""이미지 검색 및 처리 모듈 - 영구 중복 방지"""

import json
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class ImageHandler:
    """이미지 검색 및 URL 처리 (영구 중복 방지)"""
    
    HISTORY_FILE = Path(__file__).parent.parent / "cache" / "used_images.json"
    
    FALLBACK_KEYWORDS = {
        'camping': ['캠핑', '캠핑장', '자연', '숲', '야영'],
        'durunubi': ['걷기', '산책', '트레킹', '둘레길', '해안', '산'],
        'durunubi_walk': ['걷기', '산책', '트레킹', '둘레길', '해안', '산'],
        'durunubi_bike': ['자전거', '라이딩', '자전거길', '강변', '해안'],
    }
    
    def __init__(self, photo_api=None):
        self.photo_api = photo_api
        self.session_used = set()  # 현재 세션에서 사용된 이미지
        self._load_history()
    
    def _load_history(self):
        """영구 저장된 사용 이미지 로드"""
        self.HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            if self.HISTORY_FILE.exists():
                with open(self.HISTORY_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.all_used = set(data.get('images', []))
                    logger.info(f"이미지 히스토리 로드: {len(self.all_used)}개")
            else:
                self.all_used = set()
        except Exception as e:
            logger.warning(f"이미지 히스토리 로드 실패: {e}")
            self.all_used = set()
    
    def _save_history(self):
        """사용된 이미지 영구 저장"""
        try:
            # 기존 + 새로 사용된 이미지 합치기
            all_images = list(self.all_used | self.session_used)
            
            # 최근 1000개만 유지 (너무 커지지 않도록)
            if len(all_images) > 1000:
                all_images = all_images[-1000:]
            
            with open(self.HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    'images': all_images,
                    'last_updated': datetime.now().isoformat(),
                    'count': len(all_images)
                }, f, ensure_ascii=False, indent=2)
            
            logger.info(f"이미지 히스토리 저장: {len(all_images)}개")
        except Exception as e:
            logger.warning(f"이미지 히스토리 저장 실패: {e}")
    
    def reset(self):
        """세션 초기화 (새 글 작성 시)"""
        self.session_used = set()
    
    def finalize(self):
        """세션 종료 시 저장"""
        self._save_history()
    
    def _is_used(self, url: str) -> bool:
        """이미지가 이미 사용되었는지 확인"""
        return url in self.all_used or url in self.session_used
    
    def _mark_used(self, url: str):
        """이미지를 사용됨으로 표시"""
        self.session_used.add(url)
    
    def _fix_url(self, url: str) -> str:
        """http → https 변환"""
        if url and url.startswith('http://'):
            url = url.replace('http://', 'https://')
        return url
    
    def _search_from_api(self, keywords: list) -> str:
        """관광사진 API에서 이미지 검색"""
        if not self.photo_api:
            return ''
        
        for kw in keywords:
            if not kw:
                continue
            try:
                logger.info(f"사진 검색: {kw}")
                photos = self.photo_api.search_photos(kw, num_of_rows=10)
                logger.info(f"  -> {len(photos)}건")
                
                for p in photos:
                    url = p.get('galWebImageUrl', '')
                    url = self._fix_url(url)
                    
                    if url and not self._is_used(url):
                        self._mark_used(url)
                        logger.info(f"  -> 선택: {url[:50]}...")
                        return url
            except Exception as e:
                logger.error(f"사진 검색 실패 ({kw}): {e}")
        
        return ''
    
    def get_image(self, item: dict, region: str = "", theme: str = "") -> str:
        """이미지 URL 획득"""
        # 1. 원본 이미지
        url = item.get('firstimage', '')
        url = self._fix_url(url)
        
        if url and not self._is_used(url):
            self._mark_used(url)
            logger.info(f"원본 이미지: {item.get('title', '')}")
            return url
        
        # 2. API 검색
        title = item.get('title', '')
        source = item.get('source', 'camping')
        
        keywords = [title]
        
        if region:
            keywords.append(region.split()[0] if ' ' in region else region)
        
        if theme:
            keywords.append(theme)
        
        fallbacks = self.FALLBACK_KEYWORDS.get(source, [])
        keywords.extend(fallbacks)
        
        return self._search_from_api(keywords)
    
    def check_images_available(self, items: list, region: str = "", theme: str = "", min_images: int = 3) -> bool:
        """이미지 확보 가능 여부 확인"""
        temp_used = set()
        found_count = 0
        
        for item in items:
            url = item.get('firstimage', '')
            url = self._fix_url(url)
            
            if url and not self._is_used(url) and url not in temp_used:
                temp_used.add(url)
                found_count += 1
                continue
            
            if self.photo_api:
                title = item.get('title', '')
                source = item.get('source', 'camping')
                
                keywords = [title, region, theme]
                keywords.extend(self.FALLBACK_KEYWORDS.get(source, []))
                
                for kw in keywords:
                    if not kw:
                        continue
                    try:
                        photos = self.photo_api.search_photos(kw, num_of_rows=10)
                        for p in photos:
                            purl = self._fix_url(p.get('galWebImageUrl', ''))
                            if purl and not self._is_used(purl) and purl not in temp_used:
                                temp_used.add(purl)
                                found_count += 1
                                break
                        if found_count > len(items) * 0.5:
                            break
                    except:
                        pass
        
        logger.info(f"이미지 사전 체크: {found_count}/{len(items)}개 확보 가능")
        return found_count >= min_images

"""콘텐츠 생성 메인 모듈"""

from pathlib import Path
import yaml
import random
import logging
import re
from collections import defaultdict

from core.theme_selector import ThemeSelector
from core.image_handler import ImageHandler
from core.naver_map import get_naver_map_link

logger = logging.getLogger(__name__)

MAX_RETRY = 3


class ContentGenerator:
    """콘텐츠 생성기"""
    
    def __init__(self):
        self.config_path = Path(__file__).parent.parent / "config"
        self.cache_path = Path(__file__).parent.parent / "cache"
        
        self._settings = None
        self._themes = None
        self._regions = None
        self._theme_selector = None
        self._image_handler = None
        self._camping_api = None
        self._durunubi_api = None
        self._photo_api = None
        self._ai_writer = None
    
    @property
    def settings(self):
        if self._settings is None:
            with open(self.config_path / "settings.yaml", 'r', encoding='utf-8') as f:
                self._settings = yaml.safe_load(f)
        return self._settings
    
    @property
    def themes(self):
        if self._themes is None:
            with open(self.config_path / "themes.yaml", 'r', encoding='utf-8') as f:
                self._themes = yaml.safe_load(f)
        return self._themes
    
    @property
    def regions(self):
        if self._regions is None:
            with open(self.config_path / "regions.yaml", 'r', encoding='utf-8') as f:
                self._regions = yaml.safe_load(f)
        return self._regions
    
    @property
    def use_ai(self):
        key = self.settings.get('openai', {}).get('api_key', '')
        use = self.settings.get('content', {}).get('use_ai', False)
        return bool(key and key.startswith('sk-') and use)
    
    @property
    def theme_selector(self):
        if self._theme_selector is None:
            history_file = self.cache_path / "theme_history.json"
            self._theme_selector = ThemeSelector(self.themes, history_file)
        return self._theme_selector
    
    @property
    def image_handler(self):
        if self._image_handler is None:
            self._image_handler = ImageHandler(self.photo_api)
        return self._image_handler
    
    @property
    def ai_writer(self):
        if self._ai_writer is None and self.use_ai:
            from core.ai_writer import load_ai_writer
            self._ai_writer = load_ai_writer()
        return self._ai_writer
    
    @property
    def camping_api(self):
        if self._camping_api is None:
            from core.camping_api import load_camping_client
            self._camping_api = load_camping_client()
        return self._camping_api
    
    @property
    def durunubi_api(self):
        if self._durunubi_api is None:
            from core.durunubi_api import load_durunubi_client
            self._durunubi_api = load_durunubi_client()
        return self._durunubi_api
    
    @property
    def photo_api(self):
        if self._photo_api is None:
            try:
                from core.photo_api import load_photo_client
                self._photo_api = load_photo_client()
            except Exception as e:
                logger.error(f"photo_api 로드 실패: {e}")
        return self._photo_api
    
    def select_theme(self) -> dict:
        return self.theme_selector.select()
    
    def select_theme_with_images(self) -> tuple:
        """이미지 확보 가능한 주제 선택"""
        for attempt in range(MAX_RETRY):
            logger.info(f"주제 선택 시도 {attempt + 1}/{MAX_RETRY}")
            
            theme_data = self.select_theme()
            items, region, theme_data = self.fetch_items(theme_data)
            
            if not items:
                logger.warning("데이터 없음, 다른 주제 선택")
                continue
            
            min_items = self.settings.get('content', {}).get('min_items', 3)
            if self.image_handler.check_images_available(items[:6], region, theme_data.get('theme', ''), min_items):
                logger.info("이미지 확보 가능, 진행")
                return items, region, theme_data
            
            logger.warning("이미지 부족, 다른 주제 선택")
        
        logger.error("이미지 확보 실패, 마지막 결과로 진행")
        return items, region, theme_data
    
    def fetch_items(self, theme_data: dict) -> tuple:
        source = theme_data.get('source', 'camping')
        
        if source == 'camping':
            items = self._fetch_camping()
        elif source == 'durunubi_walk':
            items = self._fetch_walk()
        elif source == 'durunubi_bike':
            items = self._fetch_bike()
        else:
            items = []
        
        if not items:
            return [], '', theme_data
        
        filtered = self._filter_items(items, theme_data)
        grouped = self._group_by_region(filtered)
        
        if not grouped:
            return filtered[:6], '', theme_data
        
        valid = {k: v for k, v in grouped.items() if len(v) >= 3}
        if valid:
            region = random.choice(list(valid.keys()))
        else:
            region = max(grouped.keys(), key=lambda k: len(grouped[k]))
        
        result = grouped[region]
        random.shuffle(result)
        return result, region, theme_data
    
    def _fetch_camping(self) -> list:
        try:
            data = self.camping_api.get_campsite_list(num_of_rows=500)
            return [self._norm_camping(i) for i in data if i.get('addr1') or i.get('doNm')]
        except Exception as e:
            logger.error(f"캠핑 조회 실패: {e}")
            return []
    
    def _fetch_walk(self) -> list:
        try:
            data = self.durunubi_api.search_walking_trails(num_of_rows=200)
            logger.info(f"걷기길 {len(data)}건 조회")
            return [self._norm_durunubi(i) for i in data]
        except Exception as e:
            logger.error(f"걷기길 조회 실패: {e}")
            return []
    
    def _fetch_bike(self) -> list:
        try:
            data = self.durunubi_api.search_bike_trails(num_of_rows=200)
            return [self._norm_durunubi(i) for i in data]
        except Exception as e:
            logger.error(f"자전거길 조회 실패: {e}")
            return []
    
    def _norm_camping(self, i: dict) -> dict:
        hp = i.get('homepage', '') or ''
        if hp and not hp.startswith('http'):
            hp = ''
        
        pets = ''
        if '가능' in (i.get('animalCmgCl') or ''):
            pets = '동반 가능'
        elif '불가' in (i.get('animalCmgCl') or ''):
            pets = '동반 불가'
        
        return {
            'title': i.get('facltNm', ''),
            'addr1': i.get('addr1', '') or f"{i.get('doNm', '')} {i.get('sigunguNm', '')}".strip(),
            'firstimage': i.get('firstImageUrl', ''),
            'overview': i.get('intro', '') or i.get('featureNm', '') or i.get('lineIntro', ''),
            'tel': i.get('tel', ''),
            'homepage': hp,
            'opentime': i.get('operDeCl', '') or i.get('operPdCl', ''),
            'facilities': i.get('sbrsCl', ''),
            'pets': pets,
            'camptype': i.get('induty', ''),
            'location_type': i.get('lctCl', ''),
            'manage_type': i.get('mangeDivNm', ''),
            'trailer_yn': 'Y' if i.get('trlerAcmpnyAt') == 'Y' else '',
            'brazier': i.get('brazierCl', ''),
            'nearby': i.get('posblFcltyCl', ''),
            'toilet_count': int(i.get('toiletCo', 0) or 0),
            'shower_count': int(i.get('swrmCo', 0) or 0),
            'sink_count': int(i.get('wtrplCo', 0) or 0),
            'source': 'camping'
        }
    
    def _norm_durunubi(self, i: dict) -> dict:
        dist = i.get('crsDstnc', '')
        if dist:
            try:
                dist = f"{float(str(dist).replace('km','').strip())}km"
            except:
                pass
        
        time_val = i.get('crsTotlRqrmHour', '')
        time_str = ''
        if time_val:
            try:
                h = float(time_val)
                if h >= 1:
                    time_str = f"약 {int(h)}시간"
                else:
                    time_str = f"약 {int(h * 60)}분"
            except:
                pass
        
        lvl = {'1': '쉬움', '2': '보통', '3': '어려움'}.get(str(i.get('crsLevel', '')), '')
        
        return {
            'title': i.get('crsKorNm', '') or i.get('crsNm', ''),
            'addr1': i.get('sigun', '') or i.get('areaName', ''),
            'firstimage': i.get('crsImgUrl', '') or i.get('imageUrl', ''),
            'overview': i.get('crsSummary', '') or i.get('crsContents', ''),
            'tel': i.get('crsTel', ''),
            'homepage': i.get('crsHomepage', ''),
            'distance': dist,
            'time': time_str,
            'level': lvl,
            'source': 'durunubi'
        }
    
    def _filter_items(self, items: list, theme_data: dict) -> list:
        key = theme_data.get('filter_key')
        if not key:
            return items
        
        filtered = []
        for item in items:
            val = item.get(key, '')
            
            if isinstance(val, int):
                if theme_data.get('filter_min') and val >= theme_data['filter_min']:
                    filtered.append(item)
                elif theme_data.get('filter_max') and val <= theme_data['filter_max']:
                    filtered.append(item)
                continue
            
            val = str(val)
            
            if theme_data.get('filter_value') and val == theme_data['filter_value']:
                filtered.append(item)
            elif theme_data.get('filter_contains') and theme_data['filter_contains'] in val:
                filtered.append(item)
            elif theme_data.get('filter_max'):
                try:
                    num = float(val.replace('km', '').strip())
                    if num <= theme_data['filter_max']:
                        filtered.append(item)
                except:
                    pass
            elif theme_data.get('filter_min'):
                try:
                    num = float(val.replace('km', '').strip())
                    if num >= theme_data['filter_min']:
                        filtered.append(item)
                except:
                    pass
        
        return filtered if filtered else items
    
    def _get_region_group(self, addr: str) -> str:
        if not addr:
            return ''
        for group, cities in self.regions.items():
            for city in cities:
                if city in addr:
                    return group
        parts = addr.split()
        return parts[0] if parts else ''
    
    def _group_by_region(self, items: list) -> dict:
        grouped = defaultdict(list)
        for item in items:
            group = self._get_region_group(item.get('addr1', ''))
            if group:
                grouped[group].append(item)
        return grouped
    
    def generate_title(self, theme: str, items: list, region: str, theme_data: dict) -> str:
        angle = theme_data.get('angle', '')
        if self.use_ai and self.ai_writer:
            try:
                return self.ai_writer.generate_title(theme, items, region, angle)
            except Exception as e:
                logger.error(f"AI 제목 생성 실패: {e}")
        return f"{region} {theme} {len(items)}곳 정보"
    
    def generate_post(self, items: list, theme: str, region: str, theme_data: dict) -> dict:
        self.image_handler.reset()
        angle = theme_data.get('angle', '')
        
        for item in items:
            item['firstimage'] = self.image_handler.get_image(item, region, theme)
            item['naver_map_link'] = get_naver_map_link(item.get('title', ''))
        
        # 이미지 사용 기록 저장
        self.image_handler.finalize()
        
        clean = []
        for i in items:
            cleaned = {k: v for k, v in i.items() if v and v != '확인 필요' and v != '–' and v != '-'}
            clean.append(cleaned)
        
        if self.use_ai and self.ai_writer:
            try:
                content = self.ai_writer.generate_full_content(clean, theme, region, angle)
                content = self._insert_images(content, clean)
                content = self._insert_map_links(content, clean)
                content = self._clean_empty_items(content)
                
                return {
                    'content': content,
                    'tags': [],  # 태그 제거
                    'excerpt': self.ai_writer.generate_excerpt(theme, len(clean), region, angle),
                    'featured_image': clean[0].get('firstimage', '') if clean else ''
                }
            except Exception as e:
                logger.error(f"AI 생성 실패: {e}")
        
        return {
            'content': self._build_html(clean, theme, region),
            'tags': [],  # 태그 제거
            'excerpt': f"{region} {theme} {len(clean)}곳 정보",
            'featured_image': clean[0].get('firstimage', '') if clean else ''
        }
    
    def _insert_images(self, content: str, items: list) -> str:
        for item in items:
            title = item.get('title', '')
            img_url = item.get('firstimage', '')
            
            if not title or not img_url:
                continue
            
            pattern = rf'(<h3>[^<]*{re.escape(title)}[^<]*</h3>)'
            
            img_html = f'''
<figure class="wp-block-image">
<img src="{img_url}" alt="{title}" loading="lazy"/>
</figure>'''
            
            content = re.sub(pattern, rf'\1{img_html}', content, count=1)
        
        return content
    
    def _insert_map_links(self, content: str, items: list) -> str:
        for item in items:
            title = item.get('title', '')
            map_link = item.get('naver_map_link', '')
            
            if not title or not map_link:
                continue
            
            map_html = f'<p><strong>지도:</strong> <a href="{map_link}" target="_blank" rel="noopener">네이버 지도에서 보기</a></p>'
            
            pattern = rf'(<h3>[^<]*{re.escape(title)}[^<]*</h3>.*?)(</div>)'
            
            def add_map(match):
                before = match.group(1)
                closing = match.group(2)
                if '네이버 지도에서 보기' not in before:
                    return before + map_html + closing
                return match.group(0)
            
            content = re.sub(pattern, add_map, content, count=1, flags=re.DOTALL)
        
        return content
    
    def _clean_empty_items(self, content: str) -> str:
        empty_patterns = [
            r'<p><strong>[^<]+:</strong>\s*[–\-]\s*</p>',
            r'<p><strong>[^<]+:</strong>\s*</p>',
            r'<p><strong>전화:</strong>\s*[–\-]?\s*</p>',
            r'<p><strong>운영:</strong>\s*[–\-]?\s*</p>',
        ]
        
        for pattern in empty_patterns:
            content = re.sub(pattern, '', content)
        
        return content
    
    def _build_html(self, items: list, theme: str, region: str) -> str:
        n = len(items)
        
        h = f"<p>{region} 지역 {theme} {n}곳을 소개합니다.</p>\n"
        h += f"<h2>{region} {theme} {n}곳</h2>\n"
        
        for idx, i in enumerate(items, 1):
            h += f"<h3>{idx}. {i.get('title','')}</h3>\n"
            if i.get('firstimage'):
                h += f'<figure class="wp-block-image"><img src="{i["firstimage"]}" alt="{i.get("title","")}" loading="lazy"/></figure>\n'
            if i.get('overview'):
                h += f"<p>{i['overview'][:300]}</p>\n"
            h += '<div class="info-box">\n'
            if i.get('addr1'):
                h += f'<p><strong>주소:</strong> {i["addr1"]}</p>\n'
            if i.get('tel'):
                h += f'<p><strong>전화:</strong> {i["tel"]}</p>\n'
            if i.get('naver_map_link'):
                h += f'<p><strong>지도:</strong> <a href="{i["naver_map_link"]}" target="_blank" rel="noopener">네이버 지도에서 보기</a></p>\n'
            h += '</div>\n'
        
        h += "<h2>마무리</h2>\n"
        h += f"<p>{region} {theme} {n}곳을 정리했습니다.</p>"
        
        return h


def load_content_generator():
    return ContentGenerator()

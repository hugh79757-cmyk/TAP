import logging
import random
import re
import unicodedata
from pathlib import Path
import yaml
from collections import defaultdict
from core.theme_selector import ThemeSelector
from core.image_handler import ImageHandler
from core.database import Session, PlaceLog
from core.naver_map import get_naver_map_link

logger = logging.getLogger(__name__)

def normalize_title(title):
    if not title: return ""
    t = unicodedata.normalize('NFKD', title)
    t = re.sub(r'\s+', '', t)
    t = re.sub(r'[^\w가-힣]', '', t)
    return t.lower()

def extract_base_name(title):
    """'서해랑길 88코스' -> '서해랑길' 추출"""
    if not title: return ""
    match = re.match(r'^([가-힣]+(?:길|로|trail)?)', title)
    return match.group(1) if match else title[:4]

class ContentGenerator:
    def __init__(self):
        self.config_path = Path(__file__).parent.parent / "config"
        self._regions = None
        self._image_handler = None

    @property
    def regions(self):
        if self._regions is None:
            with open(self.config_path / "regions.yaml", 'r', encoding='utf-8') as f:
                self._regions = yaml.safe_load(f)
        return self._regions

    def _get_region_group(self, addr):
        for group, cities in self.regions.items():
            for city in cities:
                if city in addr: return group
        return None

    def _get_image_handler(self):
        if self._image_handler is None:
            from core.photo_api import load_photo_client
            self._image_handler = ImageHandler(photo_api=load_photo_client())
        return self._image_handler

    def fetch_items(self, theme_data):
        source = theme_data.get('source', 'camping')
        
        if source == 'camping':
            return self._fetch_camping(theme_data)
        elif source in ('durunubi_walk', 'durunubi_bike'):
            return self._fetch_durunubi(theme_data, source)
        else:
            return self._fetch_camping(theme_data)

    def _fetch_camping(self, theme_data):
        from core.camping_api import load_camping_client
        api = load_camping_client()
        raw_items = api.get_campsite_list(num_of_rows=200)
        
        filter_key = theme_data.get('filter_key')
        filter_contains = theme_data.get('filter_contains')
        filter_value = theme_data.get('filter_value')
        
        if filter_key and (filter_contains or filter_value):
            filtered = []
            for item in raw_items:
                val = item.get(filter_key, '')
                if filter_contains and filter_contains in str(val):
                    filtered.append(item)
                elif filter_value and str(val) == str(filter_value):
                    filtered.append(item)
            logger.info(f"테마 필터링: {len(raw_items)} -> {len(filtered)}")
            raw_items = filtered if filtered else raw_items
        
        grouped = defaultdict(list)
        with Session() as session:
            for item in raw_items:
                title = item.get('facltNm')
                addr = item.get('addr1', '')
                group = self._get_region_group(addr)
                if not group: continue
                
                norm_name = normalize_title(title)
                if not session.query(PlaceLog).filter_by(title_norm=norm_name).first():
                    grouped[group].append({
                        'title': title,
                        'addr1': addr,
                        'overview': item.get('intro', '') or item.get('lineIntro', ''),
                        'firstimage': item.get('firstImageUrl', ''),
                        'source': 'camping'
                    })
        
        valid_regions = [k for k, v in grouped.items() if len(v) >= 3]
        if not valid_regions: return [], "", theme_data
        
        selected_region = random.choice(valid_regions)
        return grouped[selected_region][:6], selected_region, theme_data

    def _fetch_durunubi(self, theme_data, source):
        from core.durunubi_api import load_durunubi_client
        api = load_durunubi_client()
        
        course_type = "1" if source == 'durunubi_walk' else "2"
        raw_items = api.get_course_list(course_type=course_type, num_of_rows=200)
        
        filter_key = theme_data.get('filter_key')
        filter_contains = theme_data.get('filter_contains')
        filter_value = theme_data.get('filter_value')
        
        if filter_key and (filter_contains or filter_value):
            filtered = []
            for item in raw_items:
                val = item.get(filter_key, '')
                if filter_contains and filter_contains in str(val):
                    filtered.append(item)
                elif filter_value and str(val) == str(filter_value):
                    filtered.append(item)
            logger.info(f"테마 필터링: {len(raw_items)} -> {len(filtered)}")
            raw_items = filtered if filtered else raw_items
        
        # 시리즈명 다양성 필터
        seen_series = set()
        diverse_items = []
        for item in raw_items:
            title = item.get('crsKorNm', '')
            base = extract_base_name(title)
            if base not in seen_series:
                seen_series.add(base)
                diverse_items.append(item)
        
        logger.info(f"시리즈 필터링: {len(raw_items)} -> {len(diverse_items)}")
        raw_items = diverse_items if len(diverse_items) >= 5 else raw_items
        
        grouped = defaultdict(list)
        with Session() as session:
            for item in raw_items:
                title = item.get('crsKorNm', '')
                addr = item.get('sigun', '') or item.get('areaNm', '')
                group = self._get_region_group(addr)
                if not group: continue
                
                norm_name = normalize_title(title)
                if not session.query(PlaceLog).filter_by(title_norm=norm_name).first():
                    grouped[group].append({
                        'title': title,
                        'addr1': addr,
                        'overview': item.get('crsContents', '') or item.get('crsSummary', ''),
                        'firstimage': item.get('crsImg', ''),
                        'source': source
                    })
        
        valid_regions = [k for k, v in grouped.items() if len(v) >= 3]
        if not valid_regions: return [], "", theme_data
        
        selected_region = random.choice(valid_regions)
        items = grouped[selected_region][:6]
        
        return items, selected_region, theme_data

    def process_html(self, content, items, theme, region=""):
        """HTML 후처리 - 이미지 및 지도 링크 삽입"""
        handler = self._get_image_handler()
        
        # 각 장소의 h3 태그를 찾아서 순서대로 처리
        for item in items:
            title = item['title']
            
            # 1. 이미지 삽입
            img_url = handler.get_image(item, region=region, theme=theme)
            if img_url:
                img_tag = f'<figure class="wp-block-image"><img src="{img_url}" alt="{title} {theme}"/></figure>'
                # h3 태그 뒤에 이미지 삽입
                title_keyword = title.split()[0] if ' ' in title else title[:10]
                pattern = f'(<h3>[^<]*{re.escape(title_keyword)}[^<]*</h3>)'
                if re.search(pattern, content):
                    content = re.sub(pattern, f'\\1\n{img_tag}', content, count=1)
            
            # 2. 지도 링크 - 해당 장소의 info-box에만 삽입
            map_url = get_naver_map_link(title)
            map_tag = f'<p><a href="{map_url}" target="_blank">📍 네이버 지도에서 보기</a></p>'
            
            # 해당 장소 섹션의 info-box 찾기 (h3 태그 이후의 첫 번째 info-box)
            title_keyword = title.split()[0] if ' ' in title else title[:10]
            
            # 패턴: h3 태그 ~ 다음 h3 또는 h2 전까지의 info-box
            section_pattern = f'(<h3>[^<]*{re.escape(title_keyword)}[^<]*</h3>.*?)(<div class="info-box">)(.*?)(</div>)'
            
            def replace_info_box(match):
                before = match.group(1)
                box_open = match.group(2)
                box_content = match.group(3)
                box_close = match.group(4)
                
                # 이미 지도 링크가 있는지 확인
                if '네이버 지도' not in box_content:
                    return f'{before}{box_open}{box_content}\n{map_tag}\n{box_close}'
                return match.group(0)
            
            content = re.sub(section_pattern, replace_info_box, content, count=1, flags=re.DOTALL)
        
        # 3. 마무리 섹션에 안내 문구 추가
        notice = '<p class="notice">※ 가격 정보와 상세 문의 사항은 네이버 지도 후기를 참조해 주세요.</p>'
        if '마무리</h2>' in content and notice not in content:
            # 마무리 섹션의 마지막 </p> 뒤에 추가
            content = re.sub(
                r'(마무리</h2>.*?)(<p>.*?</p>)(\s*)$',
                f'\\1\\2\n{notice}\\3',
                content,
                flags=re.DOTALL
            )
        
        return content

    def select_theme_with_images(self):
        with open(self.config_path / "themes.yaml", 'r', encoding='utf-8') as f:
            themes = yaml.safe_load(f)
        selector = ThemeSelector(themes, Path("cache/theme_history.json"))
        
        handler = self._get_image_handler()
        
        for attempt in range(3):
            theme_data = selector.select()
            items, region, theme_data = self.fetch_items(theme_data)
            
            if items and handler.check_images_available(items, region, theme_data.get('theme', ''), min_images=2):
                logger.info(f"시도 {attempt + 1}: 성공")
                return items, region, theme_data
            
            logger.info(f"시도 {attempt + 1}: 이미지 부족, 재시도")
        
        return [], "", {}


def load_content_generator():
    return ContentGenerator()

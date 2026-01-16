"""주제 선택 및 히스토리 관리 모듈"""

import json
import random
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class ThemeSelector:
    TRAIL_SERIES = ['남파랑길', '서해랑길', '해파랑길', '동해랑길', 'DMZ평화의길']
    
    def __init__(self, themes: dict, history_file: Path):
        self.themes = themes
        self.history_file = history_file
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _load_history(self) -> dict:
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 필수 키 보장
                    if 'recent_sources' not in data:
                        data['recent_sources'] = []
                    if 'recent_regions' not in data:
                        data['recent_regions'] = []
                    if 'recent_series' not in data:
                        data['recent_series'] = []
                    return data
        except Exception as e:
            logger.warning(f"히스토리 로드 실패: {e}")
        return {'recent_sources': [], 'recent_regions': [], 'recent_series': []}
    
    def _save_history(self, source: str = None, region: str = None, series: str = None):
        try:
            history = self._load_history()
            
            if source:
                history['recent_sources'].append(source)
                history['recent_sources'] = history['recent_sources'][-5:]
            
            if region:
                history['recent_regions'].append(region)
                history['recent_regions'] = history['recent_regions'][-3:]
            
            if series:
                history['recent_series'].append(series)
                history['recent_series'] = history['recent_series'][-5:]
            
            history['last_updated'] = datetime.now().isoformat()
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"히스토리 저장 실패: {e}")
    
    def get_excluded_regions(self) -> list:
        history = self._load_history()
        return history.get('recent_regions', [])[-2:]
    
    def get_excluded_series(self) -> list:
        history = self._load_history()
        return history.get('recent_series', [])[-3:]
    
    def record_usage(self, region: str, title: str):
        series = None
        for s in self.TRAIL_SERIES:
            if s in title:
                series = s
                break
        
        self._save_history(region=region, series=series)
    
    def select(self) -> dict:
        history = self._load_history()
        recent = history.get('recent_sources', [])
        all_sources = list(self.themes.keys())
        
        exclude = recent[-1:] if recent else []
        available = [s for s in all_sources if s not in exclude]
        
        if not available:
            available = all_sources
            logger.info("모든 소스 최근 사용됨, 전체에서 선택")
        
        source = random.choice(available)
        theme_data = random.choice(self.themes[source])
        theme_data['source'] = source
        
        self._save_history(source=source)
        
        logger.info(f"선택: {theme_data.get('theme')} (소스: {source})")
        logger.info(f"제외된 소스: {exclude}")
        
        return theme_data

"""주제 선택 및 히스토리 관리 모듈"""

import json
import random
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class ThemeSelector:
    """주제 선택기 - 최근 사용된 소스 제외하고 선택"""
    
    def __init__(self, themes: dict, history_file: Path):
        self.themes = themes
        self.history_file = history_file
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _load_history(self) -> list:
        """최근 사용된 소스 로드"""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('recent_sources', [])[-5:]
        except Exception as e:
            logger.warning(f"히스토리 로드 실패: {e}")
        return []
    
    def _save_history(self, source: str):
        """사용된 소스 저장"""
        try:
            history = self._load_history()
            history.append(source)
            history = history[-5:]  # 최근 5개만 유지
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'recent_sources': history,
                    'last_updated': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"히스토리 저장 실패: {e}")
    
    def select(self) -> dict:
        """주제 선택 (최근 2개 소스 제외)"""
        recent = self._load_history()
        all_sources = list(self.themes.keys())
        
        # 최근 2개 소스 제외
        exclude = recent[-2:] if len(recent) >= 2 else recent
        available = [s for s in all_sources if s not in exclude]
        
        # 모두 제외되면 전체에서 선택
        if not available:
            available = all_sources
            logger.info("모든 소스 최근 사용됨, 전체에서 선택")
        
        source = random.choice(available)
        theme_data = random.choice(self.themes[source])
        theme_data['source'] = source
        
        self._save_history(source)
        
        logger.info(f"선택: {theme_data.get('theme')} (소스: {source})")
        logger.info(f"제외된 소스: {exclude}")
        
        return theme_data

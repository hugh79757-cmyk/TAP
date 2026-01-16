# core/title_generator.py
"""다양한 제목 템플릿 기반 제목 생성기"""

import random
import re
import yaml
from pathlib import Path
from datetime import datetime


class TitleGenerator:
    def __init__(self):
        self.templates = self._load_templates()
    
    def _load_templates(self) -> list:
        """모든 카테고리의 템플릿을 하나의 리스트로 로드"""
        template_path = Path(__file__).parent.parent / "config" / "title_templates.yaml"
        
        with open(template_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        all_templates = []
        for category, templates in data.items():
            if isinstance(templates, list):
                all_templates.extend(templates)
        
        return all_templates
    
    def _get_season(self) -> str:
        """현재 월 기반 계절 반환"""
        month = datetime.now().month
        if month in [3, 4, 5]:
            return "봄"
        elif month in [6, 7, 8]:
            return "여름"
        elif month in [9, 10, 11]:
            return "가을"
        else:
            return "겨울"
    
    def generate(self, region: str, theme: str, count: int = None, 
                 category: str = None) -> str:
        """제목 생성"""
        template = random.choice(self.templates)
        
        now = datetime.now()
        variables = {
            "region": region,
            "theme": theme,
            "year": now.year,
            "month": now.month,
            "season": self._get_season(),
        }
        
        # {count} 변수 제거
        template = re.sub(r'\s*{count}곳', '', template)
        template = re.sub(r'\s*{count}선', '', template)
        template = re.sub(r'\s*{count}', '', template)
        
        try:
            title = template.format(**variables)
        except KeyError:
            title = f"{region} {theme} 추천"
        
        # 빈 공백 정리
        title = re.sub(r'\s+', ' ', title).strip()
        
        return title
    
    def generate_multiple(self, region: str, theme: str, count: int = None, 
                          num_titles: int = 5) -> list:
        """여러 제목 생성"""
        titles = set()
        attempts = 0
        max_attempts = num_titles * 3
        
        while len(titles) < num_titles and attempts < max_attempts:
            title = self.generate(region, theme, count)
            titles.add(title)
            attempts += 1
        
        return list(titles)


def load_title_generator():
    return TitleGenerator()


if __name__ == "__main__":
    gen = TitleGenerator()
    print(f"총 템플릿 수: {len(gen.templates)}개\n")
    
    titles = gen.generate_multiple("강원도", "글램핑", num_titles=10)
    print("생성된 제목 샘플:")
    for i, title in enumerate(titles, 1):
        print(f"  {i}. {title}")

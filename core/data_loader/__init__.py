"""데이터 로더 패키지"""
from .base import BaseDataLoader
from .camping import get_camping_by_theme
from .article import get_articles_by_category


class CSVDataLoader(BaseDataLoader):
    def get_camping_by_theme(self, theme: str, region: str = None, limit: int = None) -> list:
        return get_camping_by_theme(self, theme, region, limit)
    
    def get_articles_by_category(self, category: str, region: str = None, limit: int = None) -> list:
        return get_articles_by_category(self, category, region, limit)
    
    def get_items_by_theme(self, theme_type: str, theme: str, region: str = None, limit: int = None) -> list:
        if theme_type == 'camping':
            return self.get_camping_by_theme(theme, region, limit)
        else:
            return self.get_articles_by_category(theme, region, limit)


def load_csv_loader():
    return CSVDataLoader()

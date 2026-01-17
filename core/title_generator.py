"""네이버 스타일 제목 생성기 v4.4 - 어디가좋을까 제거"""
import random
from datetime import datetime


class TitleGenerator:
    TIME = [
        '1월', '새해', '연초', '2026', '요즘 핫한', '최근 인기', '올해 꼭 가볼',
        '겨울', '겨울 시즌', '한겨울', '연말', '올해', '이번 겨울', '시즌',
        '지금 가기 좋은', '올겨울', '떠나기 좋은 계절', '휴식이 필요할 때'
    ]
    
    MOOD = [
        '힐링', '가족', '가성비', '아이와 함께', '자연 속', '조용한', '럭셔리', '프리미엄',
        '인생', '감성', '핫한', '분위기 좋은', '청정', '특별한 하루',
        '뷰 맛집', '프라이빗', '한적한', '로맨틱'
    ]
    
    FACILITY_MAP = {
        '글램핑': ['글램핑', '글램핑장', '글램핑 명소'],
        '카라반': ['카라반', '카라반 캠핑장', '카라반 명소'],
        '반려동물 동반': ['애견 동반 캠핑장', '펫 캠핑장', '반려견 캠핑장', '애견 캠핑장'],
        '반려견 동반': ['애견 동반 캠핑장', '펫 캠핑장', '반려견 캠핑장', '애견 캠핑장'],
    }
    
    ACTION_WITH_NUM = [
        '추천 {count}곳', 'TOP {count}', 'BEST {count}', '{count}곳 모음',
        '{count}곳 가이드', '{count}선'
    ]
    
    ACTION_NO_NUM = [
        '추천', '핵심 정리', '가이드', '알짜 정보', '모음', '여기!'
    ]
    
    PATTERNS = [
        '{time}, {location} {mood} {facility} {action}',
        '{time} {mood} {location} {facility} {action}',
        '{mood} {facility} {action}, {location}',
        '{location} {mood} {facility} {action}',
        '{mood} {location} {facility} {action}, {time}',
        '{location} {facility} {action}',
        '{mood} {facility} 찾는다면, {location} {action}',
        '{location} {facility} 가이드',
    ]
    
    SEASON_TIME = {
        1: ['1월', '새해', '올해', '연초', '겨울', '한겨울', '올겨울'],
        2: ['2월', '겨울', '이번 겨울', '시즌', '올겨울'],
        3: ['3월', '봄', '초봄', '봄 시즌'],
        4: ['4월', '봄', '벚꽃 시즌', '봄나들이'],
        5: ['5월', '봄', '가정의 달', '초여름'],
        6: ['6월', '초여름', '여름', '휴가철'],
        7: ['7월', '여름', '한여름', '휴가 시즌', '여름휴가'],
        8: ['8월', '여름', '한여름', '휴가철', '피서'],
        9: ['9월', '가을', '초가을', '가을 시즌'],
        10: ['10월', '가을', '단풍 시즌', '가을 나들이'],
        11: ['11월', '가을', '늦가을', '만추'],
        12: ['12월', '겨울', '연말', '겨울 시즌', '크리스마스'],
    }
    
    def __init__(self):
        self.used_titles = []
    
    def _get_seasonal_time(self) -> str:
        month = datetime.now().month
        if random.random() < 0.7:
            return random.choice(self.SEASON_TIME.get(month, self.TIME))
        return random.choice(self.TIME)
    
    def _get_location(self, do_name: str, sigungu: str) -> str:
        if not sigungu or sigungu == 'nan':
            return do_name
        
        is_si = sigungu.endswith('시')
        
        if is_si:
            options = [
                sigungu,
                f"{sigungu} 근처",
                f"{sigungu} 주변",
                f"{sigungu} 인근",
                f"{do_name} {sigungu}",
            ]
        else:
            options = [
                sigungu,
                f"{do_name} {sigungu}",
            ]
        
        return random.choice(options)
    
    def _get_facility(self, theme: str) -> str:
        if theme and theme in self.FACILITY_MAP:
            return random.choice(self.FACILITY_MAP[theme])
        return theme if theme else '캠핑장'
    
    def generate(self, do_name: str, theme: str = None, count: int = None, sigungu: str = None) -> str:
        if count is None:
            count = random.randint(3, 6)
        
        location = self._get_location(do_name, sigungu) if sigungu else do_name
        time = self._get_seasonal_time()
        mood = random.choice(self.MOOD)
        facility = self._get_facility(theme)
        
        if random.random() < 0.5:
            action = random.choice(self.ACTION_WITH_NUM).format(count=count)
        else:
            action = random.choice(self.ACTION_NO_NUM)
        
        pattern = random.choice(self.PATTERNS)
        title = pattern.format(
            time=time,
            location=location,
            mood=mood,
            facility=facility,
            action=action,
            count=count
        )
        
        attempts = 0
        while title in self.used_titles and attempts < 10:
            pattern = random.choice(self.PATTERNS)
            mood = random.choice(self.MOOD)
            facility = self._get_facility(theme)
            title = pattern.format(
                time=time,
                location=location,
                mood=mood,
                facility=facility,
                action=action,
                count=count
            )
            attempts += 1
        
        self.used_titles.append(title)
        if len(self.used_titles) > 10:
            self.used_titles.pop(0)
        
        return title
    
    def generate_multiple(self, do_name: str, theme: str = None, count: int = 5, sigungu: str = None) -> list:
        return [self.generate(do_name, theme, sigungu=sigungu) for _ in range(count)]


def load_title_generator():
    return TitleGenerator()

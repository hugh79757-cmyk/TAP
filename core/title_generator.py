# core/title_generator.py
"""네이버 스타일 제목 생성기 v4.0 - 순서 변경 + 지역 세분화 + 시/군 구분"""

import random
from datetime import datetime


class TitleGenerator:
    
    TIME = [
        "1월", "새해", "올해", "2026년",
        "이번 주말", "주말 여행", "당일치기",
        "겨울", "겨울 시즌", "한겨울",
        "연말", "연초", "설 연휴", "명절",
        "요즘 뜨는", "올겨울", "지금 가기 좋은", "휴가철",
    ]
    
    MOOD = [
        "감성", "힐링", "프라이빗", "가족",
        "커플", "혼캠", "초보자용", "가성비",
        "뷰 맛집", "인생샷", "조용한", "한적한",
        "청정", "자연 속", "아이와 함께", "반려견 동반",
        "럭셔리", "프리미엄", "숨은 명소", "현지인 추천",
    ]
    
    FACILITY = [
        "글램핑장", "캠핑장", "카라반", "야영장", 
        "오토캠핑장", "캠핑 명소", "캠핑 스팟",
        "글램핑", "카라반 캠핑장", "캠핑 여행지",
    ]
    
    ACTION_WITH_NUM = [
        "추천 {count}곳", "BEST {count}", "TOP {count}",
        "{count}곳 총정리", "{count}곳 모음", "{count}선",
    ]
    
    ACTION_NO_NUM = [
        "추천", "총정리", "완벽 가이드", "모음",
        "어디가 좋을까", "핵심 정리", "알짜 정보",
    ]
    
    PATTERNS = [
        "{time}, {location} {mood} {facility} {action}",
        "{location} {mood} {facility} {action}, {time}",
        "{location} {mood} {facility} {action}",
        "{mood} {facility} {action}, {location}",
        "{mood} {location} {facility} {action}",
        "{time} {mood} {location} {facility} {action}",
        "{location} {facility} 어디가 좋을까? {mood} {action}",
        "{mood} {facility} 찾는다면, {location} {action}",
    ]
    
    SEASON_TIME = {
        1: ["1월", "새해", "겨울", "한겨울", "올겨울", "연초"],
        2: ["2월", "겨울", "설 연휴", "명절"],
        3: ["3월", "봄", "초봄", "봄 시즌"],
        4: ["4월", "봄", "봄나들이", "벚꽃 시즌"],
        5: ["5월", "봄", "가정의 달", "초여름"],
        6: ["6월", "여름", "초여름", "휴가철"],
        7: ["7월", "여름", "한여름", "휴가 시즌", "여름휴가"],
        8: ["8월", "여름", "한여름", "휴가철", "피서"],
        9: ["9월", "가을", "초가을", "가을 시즌"],
        10: ["10월", "가을", "단풍 시즌", "가을 여행"],
        11: ["11월", "가을", "늦가을", "단풍"],
        12: ["12월", "겨울", "연말", "크리스마스", "올겨울"],
    }
    
    def __init__(self):
        self.used_titles = []
    
    def _get_seasonal_time(self):
        """현재 월에 맞는 시기 표현 반환"""
        month = datetime.now().month
        seasonal = self.SEASON_TIME.get(month, self.TIME)
        if random.random() < 0.7:
            return random.choice(seasonal)
        return random.choice(self.TIME)
    
    def _get_location(self, do_name: str, sigungu: str) -> str:
        """시/군에 따라 적절한 지역 표현 반환"""
        if not sigungu:
            return do_name
        
        # 시(市)인 경우 - 인근/근처/주변 사용 가능
        if sigungu.endswith('시'):
            options = [
                sigungu,
                f"{sigungu} 인근",
                f"{sigungu} 근처",
                f"{sigungu} 주변",
                f"{do_name} {sigungu}",
            ]
        # 군(郡)인 경우 - 지역명만 사용
        else:
            options = [
                sigungu,
                f"{do_name} {sigungu}",
            ]
        
        return random.choice(options)
    
    def generate(self, do_name: str, theme: str = None, count: int = None, sigungu: str = None) -> str:
        """제목 생성"""
        if count is None:
            count = random.randint(3, 6)
        
        location = self._get_location(do_name, sigungu) if sigungu else do_name
        time = self._get_seasonal_time()
        mood = random.choice(self.MOOD)
        facility = random.choice(self.FACILITY)
        
        if random.random() > 0.5:
            action = random.choice(self.ACTION_WITH_NUM).format(count=count)
        else:
            action = random.choice(self.ACTION_NO_NUM)
        
        pattern = random.choice(self.PATTERNS)
        
        title = pattern.format(
            time=time,
            location=location,
            mood=mood,
            facility=facility,
            action=action
        )
        
        # 중복 방지
        attempts = 0
        while title in self.used_titles and attempts < 10:
            time = self._get_seasonal_time()
            mood = random.choice(self.MOOD)
            facility = random.choice(self.FACILITY)
            if random.random() > 0.5:
                action = random.choice(self.ACTION_WITH_NUM).format(count=count)
            else:
                action = random.choice(self.ACTION_NO_NUM)
            pattern = random.choice(self.PATTERNS)
            title = pattern.format(
                time=time,
                location=location,
                mood=mood,
                facility=facility,
                action=action
            )
            attempts += 1
        
        self.used_titles.append(title)
        if len(self.used_titles) > 10:
            self.used_titles.pop(0)
        
        return title
    
    def generate_multiple(self, do_name: str, theme: str = None, count: int = 5, sigungu: str = None) -> list:
        """여러 제목 생성"""
        return [self.generate(do_name, theme, sigungu=sigungu) for _ in range(count)]


def load_title_generator():
    return TitleGenerator()


if __name__ == "__main__":
    gen = TitleGenerator()
    
    print("=== 제목 생성기 v4.0 테스트 ===\n")
    
    test_cases = [
        ("강원도", "춘천시"),
        ("강원도", "홍천군"),
        ("경기도", "가평군"),
        ("충남", "태안군"),
    ]
    
    for do_name, sigungu in test_cases:
        print(f"--- {do_name} {sigungu} ---")
        for i in range(3):
            title = gen.generate(do_name, "글램핑", sigungu=sigungu)
            print(f"  {i+1}. {title}")
        print()

import os
import re
import random
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
import logging
import datetime

load_dotenv()
logger = logging.getLogger(__name__)


class AIWriter:
    FORBIDDEN_PATTERNS = [
        r'```html',
        r'```',
        r'<\!DOCTYPE.*?>',
        r'<html.*?>',
        r'</html>',
        r'<head>.*?</head>',
        r'<body.*?>',
        r'</body>',
        r'<style.*?>.*?</style>',
        r'<script.*?>.*?</script>',
    ]
    
    FORBIDDEN_WORDS = [
        '인생', '꿀팁', '강추', '대박',
        '소개해드리겠습니다', '소개하겠습니다', '반갑습니다', '안녕하세요', 
        '블로거입니다', '소개해 드릴게요', '알려드릴게요', '가보셨나요', 
        '필독', '꼭 가봐야', '인생샷', '최강', '완벽한', '엄선한',
        '소개합니다', '알아보겠습니다', '살펴보겠습니다', '떠나보시길 바랍니다',
        '특히'
    ]
    
    TITLE_TEMPLATES = [
        "{region} {facility} 추천! {angle} 좋아하는 분들을 위한 안내",
        "{angle} 좋아하는 분들을 위한 {region} {facility} {count}곳",
        "{region} {facility} BEST {count} ({angle})",
        "{region} 근교 {facility}, {angle} 즐기기 좋은 곳 {count}선",
        "{angle} 캠퍼를 위한 {region} {facility} {count}곳",
        "{region}에서 {angle} 즐길 수 있는 {facility} {count}선",
        "{region} {angle} {facility} 총정리 {count}곳",
        "{region} {facility} 완전정복! {angle} 명소 {count}곳 모음",
        "{year}년 {region} {facility} {count}곳 총정리 ({angle})",
        "{region} {facility} 어디로 갈까? {angle} 명소 {count}곳",
        "{angle} 가능한 {region} {facility} {count}곳 한눈에 보기",
        "{region} {angle} {facility} 모음집 :: {count}곳",
        "{region} {facility} 다녀왔습니다 - {angle} {count}곳 후기",
        "{angle} 떠나기 좋은 {region} {facility} {count}곳 방문기",
        "{region} {facility} 솔직 후기 :: {angle} {count}곳 비교",
        "직접 가본 {region} {facility} {count}곳 ({angle})",
        "{season}에 가기 좋은 {region} {facility} {count}선 ({angle})",
        "{season} {region} 여행 :: {angle} {facility} {count}곳 안내",
        "{season} 휴가지로 딱! {region} {angle} {facility} {count}선",
        "{season} 시즌 {region} {facility} {count}곳, {angle} 특집",
        "가족과 함께하기 좋은 {region} {facility} {count}곳 ({angle})",
        "{angle} 함께할 수 있는 {region} {facility} 안내 {count}선",
        "초보 캠퍼도 OK! {region} {angle} {facility} {count}곳",
        "{region}에서 {angle} 하기 좋은 {facility} BEST {count}",
    ]
    
    FACILITY_MAP = {
        'camping': ['캠핑장', '오토캠핑장', '야영장'],
        'durunubi_walk': ['둘레길', '걷기길', '산책코스', '트레킹코스'],
        'durunubi_bike': ['자전거길', '라이딩코스', '사이클링코스'],
    }
    
    SEASONS = ['봄', '여름', '가을', '겨울', '주말', '휴가철', '연휴']
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')

    def get_embedding(self, text: str) -> list:
        response = self.client.embeddings.create(
            input=[text.replace("\n", " ")[:8000]],
            model="text-embedding-3-small"
        )
        return response.data[0].embedding

    def calculate_similarity(self, vec1: list, vec2: list) -> float:
        v1, v2 = np.array(vec1), np.array(vec2)
        return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))

    def generate_title(self, theme: str, region: str, angle: str, count: int, source: str = 'camping') -> str:
        template = random.choice(self.TITLE_TEMPLATES)
        season = random.choice(self.SEASONS)
        year = datetime.datetime.now().year
        
        facilities = self.FACILITY_MAP.get(source, ['캠핑장'])
        facility = random.choice(facilities)
        
        title = template.format(
            region=region,
            theme=theme,
            angle=angle,
            count=count,
            season=season,
            year=year,
            facility=facility
        )
        
        logger.info(f"생성된 타이틀: {title}")
        return title

    def _clean_content(self, content: str) -> str:
        for pattern in self.FORBIDDEN_PATTERNS:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE|re.DOTALL)
        
        for word in self.FORBIDDEN_WORDS:
            content = re.sub(rf'\b{re.escape(word)}\b', '', content, flags=re.IGNORECASE)
            content = re.sub(rf'{re.escape(word)}', '', content, flags=re.IGNORECASE)
        
        content = re.sub(r'<img[^>]*>', '', content)
        content = re.sub(r'<figure[^>]*>.*?</figure>', '', content, flags=re.DOTALL)
        
        content = re.sub(r'<p>\s*<strong>전화:</strong>\s*[-–—]?\s*</p>', '', content)
        content = re.sub(r'<p>\s*<strong>운영:</strong>\s*[-–—]?\s*</p>', '', content)
        content = re.sub(r'<p>\s*<strong>운영시간:</strong>\s*[-–—]?\s*</p>', '', content)
        content = re.sub(r'<p>\s*<strong>홈페이지:</strong>\s*[-–—]?\s*</p>', '', content)
        content = re.sub(r'<p>\s*<strong>입장료:</strong>\s*[-–—]?\s*</p>', '', content)
        
        content = re.sub(r'<p>\s*</p>', '', content)
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        return content.strip()

    def generate_full_content(self, items: list, theme: str, region: str, angle: str) -> str:
        places_info = []
        for i, item in enumerate(items, 1):
            addr = item.get('addr1', '주소 정보 없음')
            overview = item.get('overview', '') or ''
            tel = item.get('tel', '')
            
            info = f"{i}. {item['title']}\n   주소: {addr}"
            if tel and tel != '-':
                info += f"\n   전화: {tel}"
            if overview:
                info += f"\n   특징: {overview[:150]}"
            places_info.append(info)

        prompt = f"""여행 블로그 글을 작성하세요. HTML 태그만 사용하세요.

주제: {region} {theme}
관점: {angle}

[장소 정보]
{chr(10).join(places_info)}

[글 구조 - 반드시 이 순서로]

1. 설명문 (p 태그, 5문장 이상):
<p>{region}의 매력과 {theme}의 특징을 설명하는 도입부입니다. 문장1. 문장2. 문장3. 문장4. 문장5.</p>

2. 주제 소제목 (h2):
<h2>{region} {theme}</h2>

3. 각 장소 (h3 + p + info-box):
<h3>장소명</h3>
<p>장소 설명 4-5문장.</p>
<div class="info-box"><p><strong>주소:</strong> 실제주소</p></div>

4. 마무리 (h2 + p):
<h2>마무리</h2>
<p>마무리 5문장 이상. 전체 요약과 방문 팁.</p>

[문체]
- 경어체 (~입니다, ~습니다)
- 객관적이고 신뢰감 있는 톤

[금지]
- "특히" 단어 절대 금지
- "소개합니다", "알아보겠습니다" 금지
- 마크다운 코드 블록 금지
- <img> 태그 금지

<p>로 바로 시작하세요 (설명문부터):"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=3500,
            temperature=0.7
        )
        raw = response.choices[0].message.content
        return self._clean_content(raw)


def load_ai_writer():
    return AIWriter() if os.getenv('OPENAI_API_KEY') else None

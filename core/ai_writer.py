"""AI 글쓰기 모듈"""

from openai import OpenAI
from pathlib import Path
import yaml
import re


class AIWriter:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", temperature: float = 0.7):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
    
    def generate_title(self, theme: str, items: list, region: str = "", angle: str = "") -> str:
        places = [item.get('title', '') for item in items[:5]]
        count = len(items)
        
        prompt = f"""여행 정보 블로그 제목을 작성하세요.

주제: {theme}
지역: {region}
각도: {angle}
장소 수: {count}곳
대표 장소: {', '.join(places[:3])}

[규칙]
- 지역명 필수 포함
- 25~45자, 숫자 포함

[금지]
- "추천", "베스트", "꿀팁", "인생", "필수"
- 느낌표, 물음표

[예시]
- 강아지와 함께 가기 좋은 가평 캠핑장 5곳
- 겨울에도 운영하는 강원 영서 캠핑장 4곳
- 계곡 바로 앞 충북 캠핑장 6곳

제목:"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.7
        )
        
        title = response.choices[0].message.content.strip()
        title = title.replace('"', '').replace("'", "").strip()
        
        # 금지어 제거
        for word in ['추천', '베스트', '꿀팁', '인생', '필수']:
            title = title.replace(word, '')
        
        return title.strip()
    
    def generate_full_content(self, items: list, theme: str, region: str = "", angle: str = "") -> str:
        places_info = []
        place_names = []
        
        for i, item in enumerate(items, 1):
            place_names.append(item.get('title', ''))
            lines = [f"{i}. {item.get('title', '')}"]
            
            for key, label in [
                ('addr1', '주소'), ('tel', '전화'), ('homepage', '홈페이지'),
                ('overview', '개요'), ('distance', '거리'), ('time', '소요시간'),
                ('level', '난이도'), ('opentime', '운영'), ('facilities', '편의시설'),
                ('pets', '반려동물')
            ]:
                val = item.get(key, '')
                if val:
                    lines.append(f"- {label}: {val[:300] if key == 'overview' else val}")
            
            places_info.append('\n'.join(lines))
        
        count = len(items)
        
        prompt = f"""여행 정보 블로그 글을 작성하세요.

주제: {theme}
지역: {region}
각도: {angle}
장소 수: {count}곳

[장소 정보]
{chr(10).join(places_info)}

[HTML 구조 - 정확히 따라주세요]

<p>도입부 (반드시 5문장 이상):
- 첫째: {region} 지역의 특징
- 둘째: {angle} 관점에서 이 글을 쓴 이유
- 셋째: 소개할 {count}곳이 어떤 곳인지
- 넷째: 대표 장소 2~3곳 이름 직접 언급
- 다섯째: 이 글에서 얻을 수 있는 정보
</p>

<h2>{region} {theme} {count}곳</h2>

<h3>1. 장소명</h3>
<p>장소 설명 (반드시 4~5문장):
- 위치와 접근성
- 시설/코스의 특징
- {angle} 관점에서의 장점
- 어떤 사람에게 적합한지
</p>
<div class="info-box">
<p><strong>주소:</strong> 실제주소</p>
<p><strong>전화:</strong> 전화번호 (있으면)</p>
<p><strong>운영:</strong> 운영시간 (있으면)</p>
</div>

(2번~{count}번도 동일 형식)

<h2>마무리</h2>
<p>마무리 (반드시 5문장 이상):
- 첫째: {count}곳 전체 요약
- 둘째: {angle} 기준 방문 시 참고할 점
- 셋째: 장소 1~2곳 다시 언급하며 특징 강조
- 넷째: 예약이나 방문 시 주의사항
- 다섯째: {region} 지역의 다른 볼거리 언급
</p>

[절대 금지]
- img 태그, figure 태그 (이미지는 별도 처리)
- "안녕하세요", "반갑습니다", "~입니다" 로 시작
- "50대", "블로거", "오늘은", "소개해드리겠습니다"
- "특히", "추천드립니다", "강력 추천"
- "여러분", "~해보세요!", "감사합니다"
- "확인 필요", "현장 문의"

[필수]
- 경어체 사용: "~입니다", "~있습니다"
- 도입부 5문장 이상
- 마무리 5문장 이상
- 각 장소 설명 4~5문장
- 총 2500자 이상

글:"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000,
            temperature=self.temperature
        )
        
        content = response.choices[0].message.content.strip()
        
        # 후처리: 금지어 및 불필요한 표현 제거
        content = self._clean_content(content)
        
        return content
    
    def _clean_content(self, content: str) -> str:
        """금지어 및 불필요한 표현 제거"""
        
        # img, figure 태그 제거
        content = re.sub(r'<figure[^>]*>.*?</figure>', '', content, flags=re.DOTALL)
        content = re.sub(r'<img[^>]*/?>', '', content)
        
        # 금지 표현 제거
        remove_patterns = [
            r'안녕하세요[!.,]?\s*',
            r'반갑습니다[!.,]?\s*',
            r'50대\s*(여행\s*)?(정보\s*)?블로거[가-힣]*[!.,]?\s*',
            r'오늘은\s*',
            r'소개해\s*드리[가-힣]*[!.,]?\s*',
            r'특히\s*',
            r'추천\s*드립니다[!.,]?\s*',
            r'강력\s*추천[!.,]?\s*',
            r'감사합니다[!.,]?\s*',
        ]
        
        for pattern in remove_patterns:
            content = re.sub(pattern, '', content)
        
        # 빈 p 태그 제거
        content = re.sub(r'<p>\s*</p>', '', content)
        
        # 연속 공백 정리
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        return content.strip()
    
    def generate_tags(self, theme: str, items: list, region: str = "", angle: str = "") -> list:
        prompt = f"여행 블로그 태그 10개 (쉼표 구분, 해시태그 없이): {region} {theme} {angle}"
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.5
        )
        
        tags = response.choices[0].message.content.strip().split(',')
        return [t.strip().replace('#', '') for t in tags[:10]]
    
    def generate_excerpt(self, theme: str, count: int, region: str = "", angle: str = "") -> str:
        prompt = f"블로그 메타 설명 2문장 (120~155자, 경어체): {region} {theme} {count}곳 {angle}"
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.6
        )
        
        return response.choices[0].message.content.strip()


def load_ai_writer():
    config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    openai_config = config.get('openai', {})
    return AIWriter(
        api_key=openai_config.get('api_key', ''),
        model=openai_config.get('model', 'gpt-4o-mini'),
        temperature=openai_config.get('temperature', 0.7)
    )

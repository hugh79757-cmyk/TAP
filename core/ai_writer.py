# core/ai_writer.py
"""AI 글쓰기 모듈 - GPT 기반"""

import os
import re
from openai import OpenAI


class AIWriter:
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    
    def _clean_content(self, content: str) -> str:
        """HTML 정리"""
        content = content.strip()
        content = re.sub(r'^```html?\s*', '', content)
        content = re.sub(r'\s*```$', '', content)
        content = re.sub(r'\n{3,}', '\n\n', content)
        return content
    
    def generate_full_content(self, items: list, theme: str, region: str, angle: str) -> str:
        """전체 블로그 글 생성"""
        
        places_info = []
        for i, item in enumerate(items, 1):
            title = item.get('title', '')
            overview = item.get('overview', '')
            facilities = item.get('facilities', '')
            tel = item.get('tel', '')
            
            info = f"{i}. {title}"
            if facilities:
                info += f"\n   시설: {facilities[:100]}"
            if tel:
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

1. 도입부 (p 태그, 5문장 이상):
<p>{region}의 매력과 {theme}의 특징을 설명하는 도입부입니다.</p>

2. 주제 소제목 (h2):
<h2>{region} {theme}</h2>

3. 각 장소 (h3 + p만):
<h3>장소명</h3>
<p>장소 설명 4-5문장. 분위기, 특징, 추천 포인트 등.</p>

4. 마무리 (h2 + p):
<h2>마무리</h2>
<p>마무리 5문장 이상. 전체 요약과 방문 팁.</p>

[중요]
- 주소, 전화번호, 지도 링크는 작성하지 마세요 (별도 추가됨)
- info-box, div 태그 사용 금지
- 각 장소는 h3 + p만 사용

[문체]
- 경어체 (~입니다, ~습니다)
- 객관적이고 신뢰감 있는 톤

[금지]
- "특히" 단어 절대 금지
- 주소 정보 작성 금지
- div 태그 금지

<p>로 바로 시작하세요:"""

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

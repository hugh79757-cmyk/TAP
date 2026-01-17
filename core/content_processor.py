"""콘텐츠 후처리 모듈"""
import re
from .config import NOTICE_TEXT


def get_sigungu_consistency(items: list) -> str:
    """아이템들의 시군구 일관성 확인
    
    Returns:
        시군구가 모두 같으면 해당 시군구명, 다르면 빈 문자열
    """
    sigungu_set = set()
    for item in items:
        sg = item.get('sigungu', '')
        if sg and sg != 'nan':
            sigungu_set.add(sg)
    
    if len(sigungu_set) == 1:
        return list(sigungu_set)[0]
    return ''


def insert_images_and_links(content: str, items: list, do_name: str, theme: str) -> str:
    """이미지와 네이버 지도 링크 삽입"""
    final_content = content
    
    for item in items:
        title = item['title']
        addr = item.get('addr', '')
        map_url = item.get('map_url', '')
        image_url = item.get('image', '')
        
        addr_valid = addr and addr.strip() and addr != 'nan' and addr != 'None'
        
        info_parts = []
        if addr_valid:
            info_parts.append(f'<p><strong>주소:</strong> {addr}</p>')
        if map_url:
            info_parts.append(f'<p><a href="{map_url}" target="_blank">📍 네이버 지도에서 보기</a></p>')
        
        info_box = f'<div class="info-box">\n{"".join(info_parts)}\n</div>' if info_parts else ''
        
        title_keyword = title[:8] if len(title) >= 8 else title
        pattern = f'(<h3[^>]*>.*?{re.escape(title_keyword)}.*?</h3>)'
        match = re.search(pattern, final_content, re.IGNORECASE | re.DOTALL)
        
        if match:
            replacement = match.group(1)
            
            if image_url and image_url.startswith('http'):
                alt_text = f"{title} - {do_name} {theme}"
                img_tag = f'<figure><img src="{image_url}" alt="{alt_text}" title="{title}"/></figure>'
                replacement += '\n' + img_tag
            
            if info_box:
                replacement += '\n' + info_box
            
            final_content = final_content.replace(match.group(1), replacement, 1)
    
    return final_content


def clean_content(content: str) -> str:
    """불필요한 텍스트 제거"""
    content = re.sub(r'<p>\s*주소:\s*주소 정보 없음\s*</p>', '', content)
    content = re.sub(r'<p>\s*주소:\s*</p>', '', content)
    content = re.sub(r'주소:\s*주소 정보 없음', '', content)
    content = re.sub(r'주소 정보 없음', '', content)
    content = re.sub(r'주소:\s*nan', '', content, flags=re.IGNORECASE)
    content = re.sub(r'주소:\s*None', '', content, flags=re.IGNORECASE)
    content = re.sub(r'주소:\s*$', '', content, flags=re.MULTILINE)
    content = re.sub(r'\n{3,}', '\n\n', content)
    return content


def add_notice(content: str) -> str:
    """안내 문구 추가"""
    notice = f'<p class="notice">{NOTICE_TEXT}</p>'
    return content + f'\n{notice}'


def process_content(raw_content: str, items: list, do_name: str, theme: str) -> str:
    """콘텐츠 전체 후처리"""
    content = insert_images_and_links(raw_content, items, do_name, theme)
    content = clean_content(content)
    content = add_notice(content)
    return content

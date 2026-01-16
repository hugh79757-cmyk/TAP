# core/blogger_publisher.py
"""Google Blogger API v3 - OAuth 방식"""

import os
import logging
import pickle
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class BloggerPublisher:
    SCOPES = ['https://www.googleapis.com/auth/blogger']
    
    def __init__(self):
        self.blog_id = os.getenv('BLOGGER_BLOG_ID')
        self.token_file = Path(os.getenv('BLOGGER_TOKEN_FILE', 'token.pickle'))
        self.client_secret = Path(os.getenv('BLOGGER_CLIENT_SECRET', 'client_secret.json'))
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """OAuth 인증"""
        if not self.blog_id:
            raise ValueError("BLOGGER_BLOG_ID가 .env에 설정되지 않았습니다.")
        
        creds = None
        
        if self.token_file.exists():
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("토큰 갱신 중...")
                creds.refresh(Request())
            else:
                if not self.client_secret.exists():
                    raise FileNotFoundError(
                        f"클라이언트 시크릿 파일을 찾을 수 없습니다: {self.client_secret}"
                    )
                logger.info("새 토큰 발급 중...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.client_secret), self.SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('blogger', 'v3', credentials=creds)
        logger.info("Blogger API 인증 성공")
    
    def create_post(self, title: str, content: str, labels: list = None,
                    is_draft: bool = True, max_retries: int = 3) -> dict:
        """블로그 포스트 생성"""
        post_body = {
            'kind': 'blogger#post',
            'title': title,
            'content': content
        }
        
        if labels:
            post_body['labels'] = labels
        
        for attempt in range(max_retries):
            try:
                result = self.service.posts().insert(
                    blogId=self.blog_id,
                    body=post_body,
                    isDraft=is_draft
                ).execute()
                
                status = "임시저장" if is_draft else "발행"
                logger.info(f"Blogger {status} 완료: {result.get('url')}")
                
                return {
                    'id': result.get('id'),
                    'url': result.get('url'),
                    'link': result.get('url'),
                    'title': result.get('title'),
                    'status': 'draft' if is_draft else 'published'
                }
                
            except HttpError as e:
                logger.warning(f"시도 {attempt + 1}/{max_retries} 실패: {e}")
                if attempt == max_retries - 1:
                    raise
            except Exception as e:
                logger.error(f"포스트 생성 실패: {e}")
                raise
    
    def publish_draft(self, post_id: str) -> dict:
        """임시저장 글을 발행"""
        try:
            result = self.service.posts().publish(
                blogId=self.blog_id,
                postId=post_id
            ).execute()
            logger.info(f"발행 완료: {result.get('url')}")
            return result
        except HttpError as e:
            logger.error(f"발행 실패: {e}")
            raise


def load_publisher():
    """발행기 로드"""
    return BloggerPublisher()

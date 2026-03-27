import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service(credentials_file='credentials.json', token_file='token.json'):
    """
    Google OAuth 2.0 흐름을 통해 Gmail API(읽기 전용) 서비스 객체를 반환합니다.
    token.json이 없거나 만료된 경우 브라우저를 열어 최초 로그인을 유도합니다.
    """
    creds = None
    
    # 이전에 저장된 인증 토큰이 있는지 확인
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    # 유효한 인증 정보가 없으면, 브라우저 로그인을 통한 인증(OAuth) 처리
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)
            
        # 다음 실행을 위해 토큰 저장
        with open(token_file, 'w') as token:
            token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)
    return service

if __name__ == '__main__':
    # 테스트용 실행 코드 (스크립트 단독 실행 시 토큰 생성 여부 확인)
    print("Gmail API 인증 모듈 테스트 중...")
    service = get_gmail_service()
    profile = service.users().getProfile(userId='me').execute()
    print(f"인증 성공! 이메일 계정: {profile['emailAddress']}")

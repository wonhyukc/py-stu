import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


import google.auth


def get_gmail_service(credentials_file="credentials.json", token_file="token.json"):
    """
    Google OAuth 2.0 흐름을 통해 Gmail API(읽기 전용) 서비스 객체를 반환합니다.
    token.json이 없거나 만료된 경우 브라우저를 열어 최초 로그인을 유도합니다.
    WIF 환경 등 credentials.json이 없는 경우 Application Default Credentials를 사용합니다.
    """
    creds = None

    # 이전에 저장된 인증 토큰이 있는지 확인
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    # 유효한 인증 정보가 없으면, 인증(OAuth) 처리 또는 WIF 시도
    if not creds or not creds.valid:
        if not os.path.exists(credentials_file):
            print(
                "ℹ️ credentials.json이 없으므로 WIF(Application Default Credentials)를 시도합니다."
            )
            creds, _ = google.auth.default(scopes=SCOPES)
            from google.auth import impersonated_credentials

            # WIF 환경에서 DWD(도메인 전체 위임)를 적용하기 위해 명시적으로 subject를 추가합니다.
            target_principal = "fedora-2603@drive-project-84200.iam.gserviceaccount.com"

            # google-github-actions/auth 가 이미 impersonated_credentials 를 반환하는 경우
            if (
                hasattr(creds, "source_credentials")
                and getattr(creds, "service_account_email", None) == target_principal
            ):
                creds = impersonated_credentials.Credentials(
                    source_credentials=creds.source_credentials,
                    target_principal=target_principal,
                    target_scopes=SCOPES,
                    subject="wonhyukc@stu.ac.kr",
                )
            else:
                creds = impersonated_credentials.Credentials(
                    source_credentials=creds,
                    target_principal=target_principal,
                    target_scopes=SCOPES,
                    subject="wonhyukc@stu.ac.kr",
                )
            return build("gmail", "v1", credentials=creds)

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)

        # 다음 실행을 위해 토큰 저장
        with open(token_file, "w") as token:
            token.write(creds.to_json())

    service = build("gmail", "v1", credentials=creds)
    return service


if __name__ == "__main__":
    # 테스트용 실행 코드 (스크립트 단독 실행 시 토큰 생성 여부 확인)
    print("Gmail API 인증 모듈 테스트 중...")
    service = get_gmail_service()
    profile = service.users().getProfile(userId="me").execute()
    print(f"인증 성공! 이메일 계정: {profile['emailAddress']}")

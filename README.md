# py-stu
학생들의 성적과 과제를 처리하기 위한 Python 프로젝트입니다.

## 주요 기능
- 구글 시트 연동을 통한 성적 및 과제 데이터 관리
- 이메일 발송 자동화 (Google API 연동)
- `secret.json` credential을 통한 안전한 API 접근

## 대상 과목 및 학생 데이터 (`students/`)
- **Python (파이썬)**: `students/py-students.md`
- **Web (웹 프로그래밍)**: 2개 분반으로 구성되어 운영됩니다. `students/wb-students.md`
- **전체 시간표**: `students/timetable.md`

## 인증 키 발급 방법 (`secret.json`)
프로젝트에서 Google API (구글 시트 및 이메일 연동)를 사용하기 위해서는 `secret.json` 형태의 인증키가 필요합니다. 다음 과정을 통해 발급받으세요:

1. [Google Cloud Console](https://console.cloud.google.com/)에 접속하여 프로젝트를 생성하거나 선택합니다.
2. 사이드바에서 **API 및 서비스** > **라이브러리**로 이동하여 사용할 API(예: **Google Sheets API**, **Gmail API** 등)를 검색하고 사용 설정합니다.
3. **API 및 서비스** > **사용자 인증 정보(Credentials)** 메뉴로 이동합니다.
4. 상단의 **사용자 인증 정보 만들기**를 클릭하고 **서비스 계정(Service Account)**을 선택합니다.
5. 서비스 계정 이름 및 세부 정보를 입력하고 생성합니다. (필요 시 역할 부여)
6. 생성된 서비스 계정 목록에서 해당 계정을 클릭하여 상세 페이지로 이동합니다.
7. 상단 탭에서 **키(Keys)**를 선택합니다.
8. **키 추가** > **새 키 만들기**를 클릭하고 키 유형을 **JSON**으로 선택하여 생성(다운로드)합니다.
9. 다운로드된 파일의 이름을 `secret.json`으로 변경하고, 본 프로젝트의 루트 경로(`.gitignore` 등 소스관리에 포함되지 않도록 주의)에 위치시킵니다.

### ⚠️ Gmail API 사용 시 추가 설정 (서비스 계정 위임)
서비스 계정(`secret.json`)을 통해 기관/개인 이메일 계정으로 Gmail 접근 및 메일 전송을 하려면 **도메인 전체 위임(Domain-Wide Delegation)**이 필수적으로 설정되어야 합니다.

1. **Google Workspace 관리자 콘솔**에 로그인합니다.
2. **보안** > **액세스 및 데이터 관리** > **API 관리** > **도메인 전체 위임** 메뉴로 이동합니다.
3. **새로 추가**를 클릭하고, 발급받은 서비스 계정의 **클라이언트 ID**(유니크 ID 번호)를 입력합니다.
4. OAuth 범위에 `https://mail.google.com/` 등을 추가하고 승인합니다.
5. Python 코드 내에서 API 연동 시 위임할 실제 이메일 계정 주소(`subject` 파라미터)를 명시하여 연결합니다.

> **참고**: 일반 개인 계정(`@gmail.com`)은 도메인 정책 위임이 불가능하므로, 서비스 계정 대신 **OAuth 2.0 클라이언트 ID** 방식(사용자 동의 후 브라우저 연동)이나 **앱 비밀번호**(App Passwords) 방식을 사용해야 합니다.

## 개발 및 테스트 환경 구축 (Harness Setup)
프로젝트 코드를 수정하기 전, 다음의 과정으로 가상환경을 구성하고 테스트 도구를 설치해야 합니다. `bin/harness-check.sh` 등의 프리커밋 훅을 정상적으로 동작시키기 위한 필수 과정입니다.

1. **가상환경 생성 및 활성화**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. **테스트 패키지 설치**:
   ```bash
   pip install -r requirements-test.txt
   ```

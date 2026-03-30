#!/bin/bash
# 이 스크립트는 Google Cloud Workload Identity Federation을 py-stu 프로젝트 리포지토리에 맞게 자동 구성합니다.
# gcloud가 설치 및 로그인된 환경(예: 로컬 머신 또는 Cloud Shell)에서 실행해 주세요.

PROJECT_ID="drive-project-84200"
SERVICE_ACCOUNT="fedora-2603@drive-project-84200.iam.gserviceaccount.com"
GITHUB_REPO="wonhyukc/py-stu"
POOL_NAME="github-actions-pool"
PROVIDER_NAME="github-actions-provider"

# gcloud 명령어가 사용 가능한지 확인
if ! command -v gcloud &> /dev/null
then
    echo "❌ gcloud 명령어를 찾을 수 없습니다. gcloud SDK가 설치된 환경에서 실행해 주세요."
    exit 1
fi

echo "🔍 프로젝트 번호(Project Number) 조회 중..."
export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
echo "✅ Project Number 조회 성공: $PROJECT_NUMBER"

echo "========================================="
echo "1. 워크로드 아이덴티티 풀(Pool) 생성: $POOL_NAME"
echo "========================================="
gcloud iam workload-identity-pools create "$POOL_NAME" \
  --project="$PROJECT_ID" \
  --location="global" \
  --display-name="GitHub Actions Pool for py-stu" \
  || echo "⚠️ 풀 생성 실패 (이미 존재할 수 있습니다. 계속 진행합니다.)"

echo "========================================="
echo "2. OIDC 공급업체(Provider) 설정: $PROVIDER_NAME"
echo "========================================="
gcloud iam workload-identity-pools providers create-oidc "$PROVIDER_NAME" \
  --project="$PROJECT_ID" \
  --location="global" \
  --workload-identity-pool="$POOL_NAME" \
  --display-name="GitHub Actions Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --attribute-condition="assertion.repository == '$GITHUB_REPO'" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  || echo "⚠️ 공급업체 추가 실패 (이미 존재할 수 있습니다. 계속 진행합니다.)"

echo "========================================="
echo "3. 리포지토리에 서비스 계정 가장 권한 부여"
echo "========================================="
gcloud iam service-accounts add-iam-policy-binding "$SERVICE_ACCOUNT" \
  --project="$PROJECT_ID" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$POOL_NAME/attribute.repository/$GITHUB_REPO"

echo "========================================="
echo "🎉 구성 완료! (Setup Complete!)"
echo "========================================="
echo "GitHub Actions의 .github/workflows/*.yml 파일에 다음 인증 블록을 추가하여 사용하세요:"
echo ""
echo "    - name: Authenticate to Google Cloud"
echo "      uses: google-github-actions/auth@v1"
echo "      with:"
echo "        workload_identity_provider: 'projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$POOL_NAME/providers/$PROVIDER_NAME'"
echo "        service_account: '$SERVICE_ACCOUNT'"
echo ""

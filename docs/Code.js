function createGithubAssignmentForm() {
  // 1. 폼 기본 설정 (Form Basics)
  var form = FormApp.create('주차별 과제 제출 폼 (Weekly Assignment Submission via GitHub Commit Hash)');
  form.setDescription('본 시스템은 제출 시간과 GitHub 커밋 이력을 교차 검증합니다. 한 번 제출한 이후에는 레포지토리의 소스를 임의로 수정(Overwrite)하지 마십시오.\n\nThis system cross-verifies submission time and GitHub commit history. Please do not overwrite your repository source code after submission.');
  
  // 교차 검증을 위해 학생들의 구글 계정 이메일 수집 켜기
  form.setCollectEmail(true);

  // 2. 수강 트랙 (필수)
  var trackItem = form.addMultipleChoiceItem();
  trackItem.setTitle('1. 현재 수강 중인 트랙(분반)을 선택하세요. / Please select your current track (class).')
           .setChoices([
             trackItem.createChoice('파이썬 (Python)'),
             trackItem.createChoice('web-A'),
             trackItem.createChoice('web-B')
           ])
           .setRequired(true);

  // 3. 학번 (필수, 202로 시작하는 10자리 숫자 정규식 적용)
  var studentIdItem = form.addTextItem();
  studentIdItem.setTitle('2. 학번 번호 / Student ID')
               .setHelpText('숫자로만 10자리(202로 시작) 정확히 기입하세요. / Enter exactly a 10-digit number starting with 202. (e.g. 2026300001)')
               .setRequired(true);

  // 학번 검증: 제공된 샘플(2026300076 등)의 특징을 분석하여 "202로 시작하는 10자리 숫자"로 강화
  var studentIdValidation = FormApp.createTextValidation()
    .requireTextMatchesPattern('^202[0-9]{7}$')
    .setHelpText('올바른 학번 형식이 아닙니다(202로 시작하는 10자리 숫자). / Invalid format (must be a 10-digit number starting with 202).')
    .build();
  studentIdItem.setValidation(studentIdValidation);

  // 4. GitHub 레포지토리 링크 (필수, 'github' 단어 확인)
  var repoLinkItem = form.addTextItem();
  repoLinkItem.setTitle('3. GitHub Repository 주소 URL / GitHub Repository URL')
              .setHelpText('반드시 "github" 단어가 포함된 유효한 URL이어야 합니다. / Must be a valid URL containing the word "github".')
              .setRequired(true);
  
  var githubUrlValidation = FormApp.createTextValidation()
    .requireTextMatchesPattern('.*github.*')
    .setHelpText('유효한 GitHub 주소가 아닙니다. 주소창을 정확히 복사해 주세요. / Invalid GitHub URL. Please copy closely from the address bar.')
    .build();
  repoLinkItem.setValidation(githubUrlValidation);

  // 5. 최신 Commit Hash (필수, 영문/숫자 검증)
  var hashItem = form.addTextItem();
  hashItem.setTitle('4. 최신 Commit Hash / Latest Commit Hash')
          .setHelpText('7자리 이상의 영문자(a-f 등)와 숫자가 결합된 커밋 해시 코드를 붙여넣으세요. / Paste the commit hash code (alphanumeric combination, at least 7 characters). Spaces or special characters are not allowed.')
          .setRequired(true);

  var hashValidation = FormApp.createTextValidation()
    .requireTextMatchesPattern('^[a-zA-Z0-9]{7,40}$')
    .setHelpText('잘못된 해시 형식입니다(특수문자/공백 금지). / Invalid hash format (No spaces/special characters allowed).')
    .build();
  hashItem.setValidation(hashValidation);

  // 6. 폼 응답 목적지(연결할 스프레드시트) 설정
  // 작성해주신 ID의 스프레드시트로 응답이 들어가도록 연동합니다.
  form.setDestination(FormApp.DestinationType.SPREADSHEET, '1_o-F6UaQ2WOe0nH2zuT_0xpwiOm1ebmWo2sEQzQptEk');

  // 실행 완료 시 로그 출력
  Logger.log('폼 생성 완료! 아래 URL을 학생들에게 공유하세요: / Form successfully created!');
  Logger.log('배포용 URL (학생 배포용): ' + form.getPublishedUrl());
  Logger.log('편집용 URL (강사용): ' + form.getEditUrl());
}




function cleanupOldSheetsAndForms() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheets = ss.getSheets();
  
  // 유지할 시트의 정확한 이름을 입력하세요. (예: '설문지 응답 3' 또는 '시트 3')
  // 이름에 ' 3'이 포함되어 있으면 삭제를 건너뛰도록 기본 설정했습니다.
  var keepKeyword = "3"; 
  
  // 구글 시트는 최소 1개의 탭이 무조건 남아있어야 하므로, 만약 3번 탭이 못 찾아지면 중단되도록 안전장치 마련
  var sheetToKeepExists = sheets.some(function(s) { return s.getName().indexOf(keepKeyword) !== -1; });
  if (!sheetToKeepExists) {
    Logger.log("오류: 유지할 탭('3'이 포함된 시트)을 찾지 못하여 삭제 작업을 중단합니다. 시트 이름을 확인하세요.");
    return;
  }

  for (var i = 0; i < sheets.length; i++) {
    var sheet = sheets[i];
    var sheetName = sheet.getName();
    
    // '3'이 포함되지 않은 나머지 탭들만 골라서 삭제 진행
    if (sheetName.indexOf(keepKeyword) === -1) { 
      
      // 1. 해당 시트에 연결된 구글 폼이 있다면 먼저 '연동 해제(Unlink)' 수행
      var formUrl = sheet.getFormUrl();
      if (formUrl) {
        try {
          var form = FormApp.openByUrl(formUrl);
          form.removeDestination(); // 폼의 응답 목적지를 끊음
          Logger.log(sheetName + " 에 연결되어 있던 폼 연동을 해제했습니다.");
        } catch(e) {
          Logger.log(sheetName + " 의 폼 연동 해제 실패 (이미 삭제된 폼이거나 권한 문제): " + e);
        }
      }
      
      // 2. 폼 연동이 끊어진 해당 시트를 최종적으로 완전히 삭제
      ss.deleteSheet(sheet);
      Logger.log(sheetName + " 시트를 완전히 삭제했습니다.");
    }
  }
  
  Logger.log("✅ 청소 완료! '3'이 포함된 시트만 남기고 모두 제거되었습니다.");
}

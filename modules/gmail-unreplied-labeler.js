/**
 * 내가 답장하지 않은 메일(마지막 메일이 내가 보낸 것이 아닌 타래)에 
 * '미답변' 라벨을 자동으로 붙이는 Google Apps Script입니다.
 * 
 * [설치 및 사용법]
 * 1. 구글 드라이브나 브라우저에서 Google Apps Script (script.google.com) 접속 및 새 프로젝트 생성
 * 2. 이 코드를 복사하여 Code.gs (또는 새 스크립트 파일)에 붙여넣기
 * 3. labelUnrepliedEmails 함수를 선택 후 [실행] 버튼을 눌러 권한 승인
 * 4. 좌측 시계 모양 아이콘(트리거)을 눌러 이 함수가 '시간 기반'으로 (예: 매 10분, 또는 1시간마다) 실행되도록 설정
 */

function labelUnrepliedEmails() {
  // 1. 사용할 라벨 이름 설정
  var labelName = "noreply"; 
  var label = GmailApp.getUserLabelByName(labelName);
  
  // 라벨이 지메일에 존재하지 않으면 새로 생성
  if (!label) {
    label = GmailApp.createLabel(labelName);
  }

  // 2. 현재 스크립트를 실행하는 내 이메일 주소 가져오기 (예: wonhyukc@stu.ac.kr)
  var myEmail = Session.getActiveUser().getEmail(); 

  // 3. 필터링할 메일 타래 검색
  // 여기서는 '받은편지함(inbox)'에 있는 메일 중 최대 100개를 가져옵니다.
  // 필요에 따라 'in:inbox subject:"과제 0.7"' 처럼 구체적인 쿼리로 변경 가능합니다.
  var threads = GmailApp.search('in:inbox', 0, 100); 
  
  for (var i = 0; i < threads.length; i++) {
    var thread = threads[i];
    var messages = thread.getMessages();
    
    // 4. 타래(스레드) 내의 가장 최신(마지막) 메일 확인
    var lastMessage = messages[messages.length - 1];
    var fromAddress = lastMessage.getFrom();
    
    // 5. 조건 판별 로직
    if (fromAddress.indexOf(myEmail) === -1) {
      // 가장 마지막 메일의 발신자가 '나'가 아닌 경우
      // => 학생이 보낸 메일이고 내가 아직 답장을 안 한 상태, 또는 학생이 내 답장에 재답장을 보낸 상태
      thread.addLabel(label);
    } else {
      // 가장 마지막 메일의 발신자가 '나'인 경우
      // => 내가 성공적으로 답장을 보낸 상태
      thread.removeLabel(label);
    }
  }
}

/**
 * 시트를 열 때마다 구글 시트 상단에 'Q&A 알림 설정' 메뉴를 추가합니다.
 * 이 메뉴를 통해 사용자가 직접 트리거를 켤 수 있습니다.
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('Q&A 알림 설정')
    .addItem('새 질문 자동 감지(onChange) 켜기', 'createOnChangeTrigger')
    .addToUi();
}

function checkNewQuestionsAndNotify() {
  // 실제 시트의 탭 이름으로 변경해주세요. (예: "Q&A", "설문응답" 등)
  const SHEET_NAME = "Q&A";

  // 알림을 받을 본인 이메일 주소로 변경해주세요.
  const EMAIL_ADDRESS = "wonhyukc@stu.ac.kr";

  // 현재 스크립트가 포함된 스프레드시트를 활성화합니다.
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  if (!ss) {
    console.error("이 스크립트는 구글 시트 내부(확장 프로그램 > Apps Script)에서 실행되어야 합니다.");
    return;
  }

  const sheet = ss.getSheetByName(SHEET_NAME);

  if (!sheet) {
    console.error(`Sheet name "${SHEET_NAME}" not found.`);
    return;
  }

  const startRow = 2; // 데이터가 시작하는 행 (헤더가 1행인 경우 2행부터)
  const lastRow = sheet.getLastRow();

  if (lastRow < startRow) return;

  // A열(1)부터 D열(4)까지 가져옵니다. 
  // 실제 D열에 '알림상태' 열을 만드셔야 합니다.
  const dataRange = sheet.getRange(startRow, 1, lastRow - 1, 4);
  const data = dataRange.getValues();

  let newQuestions = [];

  for (let i = 0; i < data.length; i++) {
    const question = String(data[i][0] || "").trim(); // A열
    const answer = String(data[i][1] || "").trim();   // B열
    const notifyStatus = String(data[i][3] || "").trim(); // D열

    // 질문은 있고, 답변은 비어있고, 발송됨 상태가 아닐 때
    if (question !== "" && answer === "" && notifyStatus !== "발송됨") {
      newQuestions.push(question);

      // D열(4)에 '발송됨' 표시
      sheet.getRange(startRow + i, 4).setValue("발송됨");
    }
  }

  if (newQuestions.length > 0) {
    let message = `답변이 없는 새로운 질문이 ${newQuestions.length}건 있습니다.\n\n`;
    message += `시트 링크:\n${ss.getUrl()}\n\n`;
    message += "--- 새 질문 내용 ---\n";

    for (const q of newQuestions) {
      message += `- ${q}\n`;
    }

    MailApp.sendEmail(EMAIL_ADDRESS, "[알림] Q&A 시트에 새 질문이 있습니다!", message);
  }
}

/**
 * 시트에 새로운 내용이 추가(변경)될 때마다 즉시 확인하는 트리거를 생성합니다.
 * 구글 앱스 스크립트 웹 화면에서 이 함수를 딱 한 번만 실행해주면 됩니다.
 */
function createOnChangeTrigger() {
  const triggers = ScriptApp.getProjectTriggers();
  for (const trigger of triggers) {
    if (trigger.getHandlerFunction() === "checkNewQuestionsAndNotify") {
      ScriptApp.deleteTrigger(trigger);
    }
  }

  ScriptApp.newTrigger("checkNewQuestionsAndNotify")
    .forSpreadsheet(SpreadsheetApp.getActiveSpreadsheet())
    .onChange()
    .create();

  console.log("새 질문 즉시 감지 트리거(onChange) 설정 완료.");
}

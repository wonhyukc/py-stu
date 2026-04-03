/**
 * 구글 앱스 스크립트(GAS): 분반별 + 주차 매칭 로직
 */

const SEMESTER_START_DATE = new Date("2026-03-02T00:00:00+09:00");

function assignPeerEvaluations() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sourceSheetStatus = ss.getSheetByName("과제 05 응답"); 
  if (!sourceSheetStatus) {
    // 지정된 이름이 없으면 구글 폼 응답이 쌓이는 가장 첫 번째(왼쪽) 탭을 자동으로 불러옵니다.
    sourceSheetStatus = ss.getSheets()[0]; 
  }
  
  if (!sourceSheetStatus) {
    SpreadsheetApp.getUi().alert("어떤 시트도 찾을 수 없습니다. 빈 문서입니다.");
    return;
  }
  
  const ui = SpreadsheetApp.getUi();
  const response = ui.prompt(
    "매칭 주차 입력",
    "몇 주차 과제를 매칭하시겠습니까? (예: 6)",
    ui.ButtonSet.OK_CANCEL
  );
  
  if (response.getSelectedButton() !== ui.Button.OK) return;
  const targetWeek = parseInt(response.getResponseText(), 10);
  if (isNaN(targetWeek)) return;
  
  // 마감 기한: 목표 주차 + 7일 = 월요일 오전 9시
  let deadline = new Date(SEMESTER_START_DATE);
  deadline.setDate(deadline.getDate() + (targetWeek * 7));
  deadline.setHours(9, 0, 0, 0);
  
  let startTime = new Date(deadline);
  startTime.setDate(startTime.getDate() - 7);

  const data = sourceSheetStatus.getDataRange().getValues();
  if (data.length <= 1) return;
  const headers = data[0];
  
  const timeColIdx = 0; 
  const secColIdx = 2; // C열은 인덱스 2
  const idColIdx = headers.findIndex(h => h.includes("학번"));
  const linkColIdx = headers.findIndex(h => h.toLowerCase().includes("github") || h.includes("링크"));
  
  if (idColIdx === -1) return;

  let sections = {}; 
  let validCount = 0;

  for (let i = 1; i < data.length; i++) {
    const r = data[i];
    const timestamp = new Date(r[timeColIdx]);
    
    // 기한 검사 (월요일 9시 이전 들어온 것만)
    if (timestamp <= deadline && timestamp > startTime) {
      const sec = r[secColIdx] ? r[secColIdx].toString().trim() : "미분류";
      const sId = r[idColIdx];
      const sLink = (linkColIdx !== -1) ? r[linkColIdx] : "";
      
      if (sId) {
        if (!sections[sec]) sections[sec] = [];
        sections[sec].push({ id: sId, link: sLink });
        validCount++;
      }
    }
  }
  
  if (validCount === 0) {
    ui.alert("해당 주차 마감기한(" + Utilities.formatDate(deadline, "Asia/Seoul", "MM/dd HH:mm") + ") 내에 제출된 정상 데이터가 없습니다.");
    return;
  }

  let matchResults = [];
  
  for (let sec in sections) {
    let students = sections[sec];
    
    // 배열 랜덤 섞기
    for (let i = students.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [students[i], students[j]] = [students[j], students[i]];
    }
    
    const N = students.length;
    for (let i = 0; i < N; i++) {
      let reviewer = students[i];
      let t1 = students[(i + 1) % N];
      let t2 = N > 2 ? students[(i + 2) % N] : students[(i + 1) % N];
      let t3 = N > 3 ? students[(i + 3) % N] : students[(i + 1) % N];
      matchResults.push([sec, reviewer.id, t1.id, t1.link, t2.id, t2.link, t3.id, t3.link]);
    }
  }
  
  const resultSheetName = targetWeek + "주차 배정결과";
  let resultSheet = ss.getSheetByName(resultSheetName);
  if (!resultSheet) resultSheet = ss.insertSheet(resultSheetName);
  else resultSheet.clear();
  
  const resultHeaders = ["분반", "평가자 학번", "대상자1", "링크1", "대상자2", "링크2", "대상자3", "링크3"];
  resultSheet.appendRow(resultHeaders);
  
  if (matchResults.length > 0) {
    resultSheet.getRange(2, 1, matchResults.length, resultHeaders.length).setValues(matchResults);
  }
  
  resultSheet.getRange("A1:H1").setFontWeight("bold").setBackground("#e0e0e0");
  resultSheet.autoResizeColumns(1, 8);
  ui.alert("분반별 독립 매칭 완료! 총 " + validCount + "건 처리됨.");
}

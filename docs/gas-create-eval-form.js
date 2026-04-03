/**
 * 통합형 상호평가 구글 폼 자동 생성 스크립트 (수정본)
 */

function createUniversalEvalForm() {
  var form = FormApp.create("통합형 과제 상호평가 폼");
  form.setDescription("매주 제공되는 깃허브 루브릭(peer-eval-rubric.md) 배점표를 참고하여 동료 과제를 평가해 주세요.\n\n주의: 1점 이상의 높은 배점을 입력할 때는 자신이 기준을 정확히 확인했는지 반드시 재검토 바랍니다.");
  
  // 이메일 수집 (설정에서 인증됨으로 강제 켜놓는 부분)
  // form.setRequireLogin(true); // 기관 내 접속 강제 옵션 (필요시 활성화)

  var weekItem = form.addListItem();
  weekItem.setTitle("1. 평가 주차 (Week)").setRequired(true);
  var weekChoices = [];
  for (var i = 1; i <= 16; i++) { weekChoices.push(weekItem.createChoice(i + "주차")); }
  weekItem.setChoices(weekChoices);

  var trackItem = form.addListItem();
  trackItem.setTitle("2. 평가 대상 과제의 트랙")
           .setChoiceValues(["K 트랙", "Web 프로그래밍 트랙", "Python 트랙"])
           .setRequired(true);

  var myIdItem = form.addTextItem()
      .setTitle("3. 본인의 학번 (평가자)")
      .setRequired(true);

  var targetIdItem = form.addTextItem()
      .setTitle("4. 평가 대상자의 학번 (피평가자)")
      .setRequired(true);

  form.addPageBreakItem().setTitle("루브릭 점수 기입 (Rubric Scoring)")
      .setHelpText("공지된 이번 주차 루브릭 기준표의 배점에 따라 0~5 사이의 숫자를 직접 입력하세요.\n해당 주차에 항목이 없다면 비워두시면 됩니다.");

  // Q1 ~ Q10 생성 (직접 숫자 입력 및 0~5 데이터 검증)
  var textValidation = FormApp.createTextValidation()
    .setHelpText("0 이상 5 이하의 숫자만 입력 가능합니다. (대부분 0 또는 1)")
    .requireNumberBetween(0, 5)
    .build();

  for (var q = 1; q <= 10; q++) {
    var item = form.addTextItem();
    item.setTitle("Q" + q + ". [루브릭 " + q + "번 항목] 획득 점수")
        .setHelpText("0~5 숫자로 입력")
        .setValidation(textValidation)
        .setRequired(q === 1 ? true : false); // 1번만 필수
  }

  // 1점 이상 입력에 대한 최종 확인 체크
  form.addCheckboxItem()
      .setTitle("최종 제출 전 검토 확인")
      .setHelpText("구글 폼은 숫자에 따른 개별 팝업 경고창 지원이 되지 않아 이 항목으로 대체합니다.")
      .setChoiceValues(["본 점수표에 1점 이상으로 배점한 문항들이 있습니다. 기준을 명확하게 확인하였으며 이에 확신합니다."])
      .setRequired(true);

  Logger.log("생성된 폼 URL: " + form.getPublishedUrl());
  Logger.log("본인 학번 엔트리 ID (사전채우기용): entry." + myIdItem.getId());
  Logger.log("대상 학번 엔트리 ID (사전채우기용): entry." + targetIdItem.getId());
  SpreadsheetApp.getUi().alert("수정된 폼 자동 생성 완료! (로그를 확인하세요)");
}

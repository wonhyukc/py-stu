function createAppealForm() {
  // 1. 폼 생성
  var form = FormApp.create('평가 결과 이의제기 (Appeal Form)');
  form.setDescription('평가 결과에 대해 이의를 제기할 수 있는 양식입니다. (This is a form to appeal your evaluation results.)');

  // 2. 학번 문항 (10자리 숫자, 2026으로 시작)
  var studentIdItem = form.addTextItem();
  studentIdItem.setTitle('학번 (Student ID)')
               .setRequired(true);
  var studentIdValidation = FormApp.createTextValidation()
    .requireTextMatchesPattern('^2026\\d{6}$')
    .setHelpText('학번은 2026으로 시작하는 10자리 숫자여야 합니다. (Must be 10 digits starting with 2026)')
    .build();
  studentIdItem.setValidation(studentIdValidation);

  // 3. 이름 문항
  var nameItem = form.addTextItem();
  nameItem.setTitle('이름 (Name)')
          .setRequired(true);

  // 4. 트랙 문항
  var trackItem = form.addTextItem();
  trackItem.setTitle('트랙 (Track)')
           .setRequired(true);

  // 5. 이의제기 유형 (드롭다운)
  var typeItem = form.addListItem();
  typeItem.setTitle('이의제기 유형 (Type of Appeal)')
          .setChoices([
            typeItem.createChoice('과제 (Assignment)'),
            typeItem.createChoice('상호평가 (Peer Review)'),
            typeItem.createChoice('시험 (Exam)'),
            typeItem.createChoice('이메일과제 (Email Assignment)'),
            typeItem.createChoice('수업참여 (Participation)'),
            typeItem.createChoice('기타 (Others)')
          ])
          .setRequired(true);

  // 6. 기대 점수 문항 (숫자만)
  var scoreItem = form.addTextItem();
  scoreItem.setTitle('받았어야 한다는 점수 (Expected Score)')
           .setRequired(true);
  var scoreValidation = FormApp.createTextValidation()
    .requireNumber()
    .setHelpText('숫자만 입력해 주세요. (Numbers only)')
    .build();
  scoreItem.setValidation(scoreValidation);

  // 7. 문항 이의제기 내용 (장문형)
  var contentItem = form.addParagraphTextItem();
  contentItem.setTitle('문항 이의제기 내용 (Reason for Appeal)')
             .setHelpText('구체적인 이의제기 사유를 작성해 주세요.')
             .setRequired(true);

  // 실행 결과 로그 출력
  Logger.log('=========================================');
  Logger.log('✅ 설문지 생성 완료!');
  Logger.log('설문지 편집 링크: ' + form.getEditUrl());
  Logger.log('=========================================');
}

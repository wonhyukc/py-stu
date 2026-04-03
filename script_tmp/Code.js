function processFormAdvanced() {
  var form = FormApp.getActiveForm();
  
  // 3번 문항 타이틀 변경 (평가당하는 사람 -> 과제 제출자)
  var items = form.getItems();
  for (var i = 0; i < items.length; i++) {
    var title = items[i].getTitle();
    if (title && (title.indexOf("피평가자") !== -1 || title.indexOf("평가당하는 사람") !== -1 || title.indexOf("과제 제출자의 학번") !== -1)) {
      items[i].setTitle("3. 과제 제출자의 학번 / Student ID of the Assignment Submitter");
      break;
    }
  }
}

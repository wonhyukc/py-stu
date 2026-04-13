import os
import re
import time
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

try:
    from bin.extract_06_emails import parse_students
except ImportError:
    import sys

    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    from bin.extract_06_emails import parse_students


def download_photos():
    print("학생 목록을 로드합니다...")
    name_to_id, id_to_track = parse_students()
    student_names = list(name_to_id.keys())

    download_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../output/photos")
    )
    os.makedirs(download_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            channel="chrome",
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            accept_downloads=True,
        )
        page = context.new_page()

        print("Navigating to mail.google.com...")
        page.goto("https://mail.google.com/")
        print(
            ">>> 브라우저가 화면에 팝업되었습니다. 직접 로그인해주세요! (최대 3분 대기합니다) <<<"
        )

        try:
            page.wait_for_selector('input[name="q"]', timeout=180000)
            print("로그인 확인 완료! 받은편지함 진입 성공.")
        except Exception:
            print("3분 내에 로그인이 확인되지 않거나 Inbox를 렌더링하지 못했습니다.")
            browser.close()
            return

        page.wait_for_timeout(2000)

        # 0.6 주차 과제 및 이미지 첨부파일 대상 검색 (50KB 이상 크기 지정으로 서명 및 아주 작은 불필요 이미지 스킵)
        query = '("과제" OR "0.6") has:attachment larger:50K '
        search_query = (
            query
            + "(filename:jpg OR filename:png OR filename:jpeg OR filename:gif) after:2026/04/05"
        )
        print(f"다음 쿼리로 메일을 검색합니다: {search_query}")
        page.fill('input[name="q"]', search_query)
        page.keyboard.press("Enter")

        print("검색 결과 대기 중...")
        page.wait_for_timeout(5000)

        rows = page.locator("tr.zA")
        count = rows.count()
        print(f"이미지 첨부파일이 포함된 총 {count}개의 이메일을 발견했습니다.")

        for i in range(count):
            try:
                # 목록 렌더링이 재설정될 수 있으므로 매번 다시 잡기
                rows = page.locator("tr.zA")
                if i >= rows.count():
                    continue
                row = rows.nth(i)

                # 보낸 사람 추출 (미리 목록에서)
                sender_loc = row.locator("div.yW span[name]")
                sender_name = ""
                sender_email = ""
                if sender_loc.count() > 0:
                    sender_name = (
                        sender_loc.first.get_attribute("name")
                        or sender_loc.first.inner_text()
                    )
                    sender_email = sender_loc.first.get_attribute("email") or ""

                # 리스트 화면에서 진짜 첨부파일 아이콘이 있는지 확인 (서명 이미지 등 무시)
                has_att = (
                    row.locator("img.yE").count() > 0
                    or row.locator('[aria-label="Attachment"]').count() > 0
                    or row.locator('[aria-label="첨부파일"]').count() > 0
                    or "Attachment" in row.inner_html()
                    or "첨부파일" in row.inner_html()
                )

                if not has_att:
                    print(f"[{i+1}/{count}] 패스 (명시적 첨부파일 없음): {sender_name}")
                    continue

                print(f"[{i+1}/{count}] 클릭하여 메일 열기: {sender_name}")
                # tr 대신 안전하게 제목 영역(span.bog) 또는 날짜 영역을 클릭합니다.
                click_target = row.locator("span.bog").first
                if click_target.count() == 0:
                    click_target = row.locator("td.xW").first

                # 강제 클릭(force) 시도
                click_target.click(force=True)
                page.wait_for_timeout(2000)
                page.wait_for_load_state("networkidle", timeout=5000)

                # 메시지 렌더링을 위해 페이지 아래로 스크롤
                page.mouse.wheel(0, 5000)
                page.wait_for_timeout(2000)

                # Gmail은 첨부파일 컨테이너에 download_url 이라는 속성을 숨겨둡니다.
                # 속성 형식: "image/jpeg:filename.jpg:https://mail.google.com/mail/..."
                download_urls_data = page.evaluate("""() => {
                    const elements = document.querySelectorAll('[download_url]');
                    const urls = [];
                    elements.forEach(el => {
                        urls.push(el.getAttribute('download_url'));
                    });

                    // a 태그 중에 첨부파일 다운로드 링크가 있는 경우도 백업으로 추출
                    const aTags = document.querySelectorAll('a[href*="disp=safe"]');
                    aTags.forEach(a => {
                        urls.push("unknown:unknown:" + a.href);
                    });

                    return urls;
                }""")

                # 중복 제거
                download_urls_data = list(set(download_urls_data))

                # 실제 이미지 파일들만 선별
                valid_downloads = []
                for data in download_urls_data:
                    parts = data.split(":", 2)
                    if len(parts) == 3:
                        _, fname, url = parts
                    elif len(parts) > 0 and data.startswith("http"):
                        _, fname, url = "unknown", "unknown", data
                    else:
                        continue

                    url_lower = data.lower()
                    if (
                        ".jpg" in url_lower
                        or ".png" in url_lower
                        or ".jpeg" in url_lower
                        or ".gif" in url_lower
                        or "disp=safe" in url_lower
                    ):
                        valid_downloads.append((fname, url))

                print(f"   -> 발견된 사진 다운로드 링크 수: {len(valid_downloads)}")

                for idx, (original_name, dl_url) in enumerate(valid_downloads):
                    # 다운로드 URL로 직접 접근하여 다운로드 트리거
                    with page.expect_download(timeout=15000) as download_info:
                        page.evaluate(f'window.location.href = "{dl_url}";')

                    download = download_info.value
                    final_original_name = (
                        original_name
                        if original_name != "unknown"
                        else download.suggested_filename
                    )

                    # 파일 이름에 학생 이름이 있는지 확인
                    has_name = False
                    clean_filename = re.sub(r"\s+", "", final_original_name).lower()
                    for s_name in student_names:
                        if s_name in clean_filename:
                            has_name = True
                            break

                    if not has_name:
                        # 이름이 없으면 보낸 사람 이름이나 이메일 적용
                        prefix = (
                            sender_name.replace(" ", "")
                            if sender_name
                            else sender_email
                        )
                        new_name = f"{prefix}_{final_original_name}"
                    else:
                        new_name = final_original_name

                    save_path = os.path.join(download_dir, new_name)
                    download.save_as(save_path)
                    print(f"   -> 원본: {final_original_name} | 저장: {new_name}")

                # 메일 목록으로 돌아가기 (Inbox 버튼 클릭 또는 Go Back)
                page.go_back()
                page.wait_for_timeout(2000)

            except Exception as e:
                print(f"Row {i} 다운로드 에러: {e}")
                # 혹시 메일 안에 갇혔다면 뒤로 가기
                if 'input[name="q"]' not in page.content():
                    page.go_back()
                continue

        browser.close()
        print(f"모든 다운로드 완료! 경로: {download_dir}")


if __name__ == "__main__":
    download_photos()

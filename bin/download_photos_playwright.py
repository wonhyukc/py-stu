import os
import re
import time
import hashlib
from urllib.parse import unquote
from playwright.sync_api import sync_playwright
from PIL import Image
from difflib import get_close_matches

try:
    import pillow_heif

    pillow_heif.register_heif_opener()
except ImportError:
    print(
        "[경고] pillow-heif 미설치 - HEIC 파일은 크기만 체크합니다. pip install pillow-heif"
    )

MIN_FILE_SIZE = 30_000  # 30KB 미만 → 아이콘/서명 이미지로 간주
MIN_PIXELS = 100 * 100  # 100×100px 미만 → 썸네일로 간주


def compute_hash(file_path):
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        buf = f.read(65536)
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(65536)
    return hasher.hexdigest()


def is_valid_photo(file_path):
    size = os.path.getsize(file_path)
    if size < MIN_FILE_SIZE:
        return False, f"파일 크기 {size}B < {MIN_FILE_SIZE}B"
    try:
        img = Image.open(file_path)
        w, h = img.size
        if w * h < MIN_PIXELS:
            return False, f"해상도 {w}x{h} 너무 작음"
        return True, "OK"
    except Exception as e:
        return False, f"이미지 열기 실패: {e}"


try:

    from bin.extract_06_emails import parse_students
except ImportError:
    import sys

    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    from bin.extract_06_emails import parse_students


def download_photos():
    print("학생 목록을 로드합니다...")
    name_to_id, id_to_track, id_to_names = parse_students()

    download_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../output/photos")
    )
    os.makedirs(download_dir, exist_ok=True)

    existing_hashes = set()
    for fname in os.listdir(download_dir):
        fp = os.path.join(download_dir, fname)
        if os.path.isfile(fp):
            existing_hashes.add(compute_hash(fp))

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            channel="chrome",
            args=["--disable-blink-features=AutomationControlled"],
        )

        state_file = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../.bin/playwright_state.json")
        )
        use_saved_state = os.path.exists(state_file)

        context_options = {
            "user_agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "accept_downloads": True,
        }
        if use_saved_state:
            print(f"저장된 인증 세션({state_file})을 불러옵니다...")
            context_options["storage_state"] = state_file

        context = browser.new_context(**context_options)
        page = context.new_page()

        print("Navigating to mail.google.com...")
        page.goto("https://mail.google.com/")

        if use_saved_state:
            try:
                page.wait_for_selector('input[name="q"]', timeout=8000)
                print("저장된 세션으로 로그인 상태 검증 성공!")
            except Exception:
                print("저장된 세션이 만료되었습니다. 다시 로그인을 진행해야 합니다.")
                use_saved_state = False

        if not use_saved_state:
            print(
                ">>> 브라우저가 화면에 팝업되었습니다. 직접 로그인해주세요! (최대 3분 대기합니다) <<<"
            )
            try:
                page.wait_for_selector('input[name="q"]', timeout=180000)
                print("로그인 확인 완료! 받은편지함 진입 성공.")
                os.makedirs(os.path.dirname(state_file), exist_ok=True)
                context.storage_state(path=state_file)
                print("새로운 로그인 세션을 저장했습니다.")
            except Exception as e:
                print(
                    f"3분 내에 로그인이 확인되지 않거나 화면 렌더링(input[name='q'])을 기다리는 중 오류가 발생했습니다. 원인: {e}"
                )
                browser.close()
                return

        page.wait_for_timeout(2000)

        # 0.6 주차 과제 및 이미지 첨부파일 대상 검색 (답장/전달 제외)
        query = "has:attachment -subject:re -subject:fwd -subject:fw "
        search_query = (
            query
            + "(filename:jpg OR filename:png OR filename:jpeg OR filename:gif"
            + " OR filename:heic OR filename:heif OR filename:webp) after:2026/04/05"
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

                # 제목 추출 (스레드 처리된 경우 Re: 등이 숨김될 수 있으나 최대한 표출)
                subject_loc = row.locator("span.bog")
                subject_text = ""
                if subject_loc.count() > 0:
                    subject_text = subject_loc.first.inner_text().strip()

                # 답장, 전달 메일 건너뛰기 (이미 쿼리에 포함됐으나 이중 방어망)
                subj_lower = subject_text.lower()
                if (
                    subj_lower.startswith(("re:", "fw:", "fwd:"))
                    or "[re]" in subj_lower
                    or "[fw]" in subj_lower
                ):
                    print(
                        f"[{i+1}/{count}] 패스 (답장/전달): {sender_name} | {subject_text}"
                    )
                    continue

                # 리스트 화면에서 진짜 첨부파일 아이콘이 있는지 확인 (서명 이미지 등 무시)
                # 인라인 이미지를 위해 해당 조건을 완화 (검색 쿼리가 이미 이미지/첨부 파일을 포함함)

                print(
                    f"[{i+1}/{count}] 클릭하여 메일 열기: {sender_name} | {subject_text}"
                )

                try:
                    # 안전하게 전체 row 클릭 (JS 기반)
                    row.evaluate("el => el.click()")
                except Exception:
                    pass

                page.wait_for_timeout(3000)

                # [중요 방어] 메일 스레드(대화형 보기)로 묶여 예전 사진이 접힌 경우, 이미지 다운로더가 DOM을 찾지 못합니다.
                # 이를 막기 위해 열린 화면에서 접힌 부분을 강제로 누릅니다.
                try:
                    page.evaluate("""() => {
                        // 1. 우측 상단 '모든 이메일 펼치기', 'Expand all' 클릭
                        const qs = '[aria-label="모든 메일 펼치기"], [aria-label="모두 펼치기"], ' +
                                   '[aria-label="Expand all"], [data-tooltip="모두 펼치기"], ' +
                                   '[data-tooltip="Expand all"]';
                        const expandBtns = document.querySelectorAll(qs);
                        for(let b of expandBtns) { b.click(); }

                        // 2. 개별적으로 접힌 헤더 강제 클릭 (Gmail UI 트리거)
                        const collapsed = document.querySelectorAll('div[data-message-id][aria-expanded="false"]');
                        for(let c of collapsed) { c.click(); }
                    }""")
                    page.wait_for_timeout(2000)
                except Exception:
                    pass
                # 제거: page.wait_for_load_state("networkidle", timeout=5000) -- Gmail과 같은 SPA에서는 백그라운드 소켓 연결 탓에 항상 에러 발생 가능

                # 메시지 렌더링을 위해 페이지 끝까지 반복 스크롤 (지연 로딩 이미지 대응)
                _prev_h = -1
                for _ in range(10):
                    _cur_h = page.evaluate("document.body.scrollHeight")
                    if _cur_h == _prev_h:
                        break
                    _prev_h = _cur_h
                    page.mouse.wheel(0, 3000)
                    page.wait_for_timeout(1500)

                # 6가지 방식으로 이미지 URL 추출
                download_urls_data = page.evaluate("""() => {
                    const urls = [];

                    // 방법 1: 표준 첨부파일 download_url 속성
                    document.querySelectorAll('[download_url]').forEach(el => {
                        urls.push(el.getAttribute('download_url'));
                    });

                    // 방법 2: 보안 링크 (disp=safe)
                    document.querySelectorAll('a[href*="disp=safe"]').forEach(a => {
                        urls.push('unknown:unknown:' + a.href);
                    });

                    // 방법 3: Gmail 인라인 이미지
                    document.querySelectorAll('img[src*="mail.google.com/mail/u/"]').forEach((img, i) => {
                        if (img.clientWidth > 50 || img.naturalWidth > 50) {
                            urls.push('inline:inline_image_' + i + '.jpg:' + img.src);
                        }
                    });

                    // 방법 4: data-attachment-id 속성 (Gmail UI 업데이트 대응)
                    document.querySelectorAll('[data-attachment-id]').forEach(el => {
                        const aid = el.getAttribute('data-attachment-id');
                        if (aid) {
                            const u = 'https://mail.google.com/mail/u/0/?ui=2&attid=' + aid + '&disp=safe&zw';
                            urls.push('unknown:attachment_' + aid + '.jpg:' + u);
                        }
                    });

                    // 방법 5: 다운로드 버튼 href
                    ['a[aria-label*="다운로드"]', 'a[aria-label*="Download"]'].forEach(sel => {
                        document.querySelectorAll(sel).forEach(el => {
                            if (el.href) urls.push('unknown:download_btn.jpg:' + el.href);
                        });
                    });

                    // 방법 6: googleusercontent.com 인라인 이미지 (대형)
                    document.querySelectorAll('img[src*="googleusercontent.com"]').forEach((img, i) => {
                        if ((img.clientWidth > 80 || img.naturalWidth > 80) && img.src.includes('mail')) {
                            urls.push('inline:gusercontent_' + i + '.jpg:' + img.src);
                        }
                    });

                    return [...new Set(urls)];
                }""")

                IMAGE_EXTENSIONS = (
                    ".jpg",
                    ".jpeg",
                    ".png",
                    ".gif",
                    ".heic",
                    ".heif",
                    ".webp",
                )
                CONTENT_TYPE_TO_EXT = {
                    "image/jpeg": ".jpg",
                    "image/png": ".png",
                    "image/gif": ".gif",
                    "image/heic": ".heic",
                    "image/heif": ".heif",
                    "image/webp": ".webp",
                }

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
                        any(ext in url_lower for ext in IMAGE_EXTENSIONS)
                        or "disp=safe" in url_lower
                        or "inline" in data
                        or "attachment" in data[:30]
                    ):
                        try:
                            response = page.request.get(url, timeout=15000)
                            if response.ok:
                                ct = response.headers.get("content-type", "image/jpeg")
                                ext = CONTENT_TYPE_TO_EXT.get(
                                    ct.split(";")[0].strip(), ".jpg"
                                )
                                real_fname = (
                                    fname
                                    if (fname and fname != "unknown")
                                    else f"attached_img{ext}"
                                )
                                file_bytes = response.body()
                                valid_downloads.append((real_fname, file_bytes, ext))
                        except Exception as e:
                            print(f"URL 직접 다운로드 에러: {e}")
                            continue

                print(f"   -> 유효한 사진 다운로드 수: {len(valid_downloads)}")

                for idx, (final_original_name, file_bytes, file_ext) in enumerate(
                    valid_downloads
                ):
                    temp_path = os.path.join(
                        download_dir, f"temp_{int(time.time())}_{idx}{file_ext}"
                    )
                    try:
                        with open(temp_path, "wb") as f:
                            f.write(file_bytes)
                    except Exception as e:
                        print(f"다운로드 파일 쓰기 실패: {e}")
                        continue

                    file_hash = compute_hash(temp_path)
                    if file_hash in existing_hashes:
                        print(
                            f"   -> [중복 패스] 이미 저장된 사진입니다: {final_original_name}"
                        )
                        os.remove(temp_path)
                        continue

                    valid, reason = is_valid_photo(temp_path)
                    if not valid:
                        print(
                            f"   -> [삭제] 유효하지 않은 이미지 ({reason}): {final_original_name}"
                        )
                        os.remove(temp_path)
                        continue

                    existing_hashes.add(file_hash)

                    clean_sender = re.sub(r"\s+", "", sender_name).lower()
                    student_id = name_to_id.get(clean_sender) or name_to_id.get(
                        sender_email.lower()
                    )

                    if not student_id:
                        m_id = re.search(r"\d{10}", subject_text)
                        if m_id:
                            student_id = m_id.group(0)
                        else:
                            # Fuzzy Matching (유사도 검증)
                            all_known_names = list(name_to_id.keys())
                            matches = get_close_matches(
                                clean_sender, all_known_names, n=1, cutoff=0.7
                            )
                            if matches:
                                student_id = name_to_id[matches[0]]

                    kor_name = ""
                    eng_name = ""
                    track_no = ""
                    if student_id:
                        if student_id in id_to_names:
                            kor_name = id_to_names[student_id]["kor"]
                            eng_name = id_to_names[student_id]["eng"]
                        if student_id in id_to_track:
                            track_no = id_to_track[student_id]

                    prefix = (
                        kor_name
                        if kor_name
                        else (
                            eng_name
                            if eng_name
                            else (
                                sender_name.replace(" ", "")
                                if sender_name
                                else sender_email.split("@")[0]
                            )
                        )
                    )
                    if not prefix:
                        prefix = "Unknown"

                    sid_str = student_id if student_id else "NoID"
                    track_str = track_no if track_no else "NoTrack"

                    new_name = f"{track_str}_{prefix}_{sid_str}_{final_original_name}"

                    final_path = os.path.join(download_dir, new_name)
                    os.rename(temp_path, final_path)
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

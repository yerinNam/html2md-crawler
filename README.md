# html2md-crawler

**Playwright 기반 대규모 웹 크롤러**  
웹 페이지를 자동으로 렌더링하고, HTML을 정제(clean)한 뒤 Markdown으로 변환합니다.  
생성된 Markdown은 LLM 입력에 최적화되어 있으며, 동적 페이지(`iframe`, `shadow root`, `JS-rendered`)까지 지원합니다.

---

## 🚀 Features

- **Web → HTML → Markdown** 파이프라인 완비  
  → LLM-friendly 구조 (semantic paragraph, heading 유지)  
- **Dynamic Rendering 지원**
  - Playwright Chromium (headful/headless 선택)
  - Lazy-load, shadow DOM, iframe 내부까지 캡처  
- **Bot Detection Resistance**
  - 실제 Chrome 프로필 복제 기반 실행
  - UA, timezone, locale, viewport 모두 실제 사용자 환경과 동일
  - `webdriver` 플래그 제거 / `navigator` 프록시 해제  

  **CreepJS 실제 탐지 결과**
  ```
  fingerprint: 0% headless
  webDriverIsOn: false
  hasHeadlessUA: false
  hasHeadlessWorkerUA: false

  0% stealth:
  hasIframeProxy: false
  hasHighChromeIndex: false
  hasBadChromeRuntime: false
  hasToStringProxy: false
  hasBadWebGL: false
  ```
  → **Bot 차단 걱정 없음. 완전한 실제 브라우징 시뮬레이션.**

---

## ⚠️ 크롤링 주의사항 (Disclaimer)

- 본 코드는 **연구·개발용 / 합법적 접근이 허용된 웹페이지**에 한해 사용해야 합니다.  
- 대상 사이트의 **robots.txt, 이용약관, 저작권 정책**을 반드시 확인하세요.  
- 해당 프로젝트 및 작성자는 **비인가 수집, 상업적 스크래핑, 제3자 피해**에 대해 책임지지 않습니다.  
- 본 코드를 이용함으로써 발생하는 모든 법적 책임은 사용자에게 있습니다.

---

## 🧩 Dependencies

- Playwright
- html2markdown (PyPI)
- Python ≥ 3.10

---

## ⚙️ Installation & Run

### 1️⃣ Clone the repository
```bash
git clone https://github.com/yerinNam/html2md-crawler.git
cd html2md-crawler
```

### 2️⃣ Install dependencies
``` bash
pip install -r requirements.txt
playwright install chromium

# 만약 'playwright' 명령이 없다고 나오면:
# python -m playwright install chromium
```

### 3️⃣ Run the crawler

#### 🪟 Windows PowerShell
```powershell
python -m crawler.main `
  --urls "./urls.txt" `
  --ok-html "./ok_html.jsonl" `
  --ok-md   "./ok_markdown.jsonl" `
  --err     "./err.jsonl" `
  --concurrency 4 `
  --origin-concurrency 1
```

#### 🐧 Linux / macOS (Bash, Zsh)
``` bash
python -m crawler.main \
  --urls "./urls.txt" \
  --ok-html "./ok_html.jsonl" \
  --ok-md   "./ok_markdown.jsonl" \
  --err     "./err.jsonl" \
  --concurrency 4 \
  --origin-concurrency 1
```

---

### ⚙️ Command-line Options

| Argument | Type | Description |
|-----------|------|-------------|
| `--urls` | `str` | URL 리스트 파일 경로 (`.txt`, 줄 단위) |
| `--ok-html` | `str` | HTML 결과 저장 JSONL 파일 경로 |
| `--ok-md` | `str` | Markdown 결과 저장 JSONL 파일 경로 |
| `--err` | `str` | 오류 로그 JSONL 파일 경로 |
| `--headless` | `flag` | Headless 모드로 실행 (기본: 창 표시됨) |
| `--concurrency` | `int` | 전체 동시 실행 스레드 수 *(기본 4)* |
| `--origin-concurrency` | `int` | 동일 오리진 내 최대 동시 요청 수 *(기본 1)* |
| `--proxy` | `str` | HTTP 프록시 주소 (`http://user:pass@host:port`) |

---

## 🪪 License

이 프로젝트는 다음 오픈소스 라이선스를 따릅니다:
- Playwright License (MIT)
- html2markdown License (MIT)

© 2025, yerinNam.  
모든 상업적 사용 및 법적 책임은 사용자에게 있습니다.
  

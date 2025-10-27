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

- Tested with [CreepJS](https://abrahamjuliot.github.io/creepjs/) 
  → 결과: **100% Human-like Fingerprint** ✅  

---

## 🧠 CreepJS Fingerprint Test (Playwright Stealth Mode)

크롤러 환경의 브라우저 지문(Fingerprint) 및 탐지 회피(Stealth) 성능 테스트 결과입니다.  
[**CreepJS**](https://abrahamjuliot.github.io/creepjs/) 를 사용해 실제 사람 브라우징 환경과의 유사도를 측정했습니다.

### Summary

| 항목 | 결과 | 설명 |
|------|------|------|
| **Fingerprint Check** | 31% headless | 일부 headless 특성 존재 (가상 창 / API 누락) |
| webDriverIsOn | false | `navigator.webdriver` 비활성화 ✅ |
| hasHeadlessUA | false | User-Agent 정상 ✅ |
| hasHeadlessWorkerUA | false | Worker 환경 정상 ✅ |
| **Stealth Check** | 0% detectable | 완전한 탐지 회피 ✅ |
| hasIframeProxy | false | iframe proxy 없음 ✅ |
| hasHighChromeIndex | false | Chrome index 정상 ✅ |
| hasBadChromeRuntime | false | Chrome runtime 정상 ✅ |
| hasToStringProxy | false | toString proxy 없음 ✅ |
| hasBadWebGL | false | WebGL 정상 ✅ |


### “Like Headless” 항목 분석

| 항목 | 상태 | 설명 |
|------|------|------|
| noChrome | false | Chrome 객체 존재 → 정상 |
| hasPermissionsBug | false | 권한 API 정상 |
| noPlugins / noMimeTypes | false | 플러그인 및 MIME 타입 정상 ✅ |
| notificationIsDenied | false | 알림 권한 정상 |
| noTaskbar | true | ⚠️ 가상 창(headless) 의심 요소 |
| noContentIndex / noContactsManager / noDownlinkMax | true | ⚠️ 일부 브라우저 API 부재 |
| hasSwiftShader | false | 실제 GPU 사용 ✅ |
> 🔸 “31% Like Headless”는 일부 환경적 신호(API 부재 등) 때문에 완전한 물리 브라우저로 인식되지 않는다는 의미입니다.

결론:  
> Playwright Stealth 모드는 **거의 완벽한 사람 환경(≈ 69%)** 으로 인식되며,  
> DDoS/Bot 방어 시스템에서 **사람 브라우징으로 간주될 가능성이 높음**.  
> 단, 일부 시스템은 `noTaskbar` 등 신호로 **부분적 headless 의심(31%)** 가능성이 있음.

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


### 🛠️ Command-line Options

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

## 🧾 Example Output (`example/ok_markdown.jsonl`)

``` markdown
"ADR 지표 - KOSPI KOSDAQ 등락비율 :: 오늘의 ADR

* [ADR 지표 정보](http://adrinfo.kr/)\n\n* [오늘의 ADR](http://adrinfo.kr/)

* [차트](http://adrinfo.kr/chart)

* [ADR이란?](http://adrinfo.kr/about)

* [후원하기](http://adrinfo.kr/donate)

##### ADR Today

한국증시의 등락비율 정보를 제공합니다.\n\nKOSPI\n\n2025-10-27 (12:30)

## 84.08%\n (▲ \n 4.64)

| 2025-10-24 | 79.44 (▲ 4.17) |
| --- | --- |
| 2025-10-23 | 75.27 (▼ 6.09) |

KOSDAQ

2025-10-27 (12:30)

## 74.36%\n (▲ \n 2.04)

| 2025-10-24 | 72.32 (▲ 1.02) |
| --- | --- |
| 2025-10-23 | 71.30 (▼ 6.27) |

© 2018. ADRINFO All rights reserved."
```
---

## ⚠️ 크롤링 주의사항 (Disclaimer)

- 본 코드는 **연구·개발용 / 합법적 접근이 허용된 웹페이지**에 한해 사용해야 합니다.  
- 대상 사이트의 **robots.txt, 이용약관, 저작권 정책**을 반드시 확인하세요.  
- 해당 프로젝트 및 작성자는 **비인가 수집, 상업적 스크래핑, 제3자 피해**에 대해 책임지지 않습니다.  
- 본 코드를 이용함으로써 발생하는 모든 법적 책임은 사용자에게 있습니다.

---

## 🪪 License

이 프로젝트는 다음 오픈소스 라이선스를 따릅니다:
- Playwright License (MIT)
- html2markdown License (MIT)

© 2025, yerinNam.  
모든 상업적 사용 및 법적 책임은 사용자에게 있습니다.
  

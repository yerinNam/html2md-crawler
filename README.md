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

  **실제 탐지 결과** <br>
    fingerprint: 0% headless <br>
    webDriverIsOn: false <br>
    hasHeadlessUA: false <br>
    hasHeadlessWorkerUA: false <br> <br>
    
    0% stealth: <br>
    hasIframeProxy: false <br>
    hasHighChromeIndex: false <br>
    hasBadChromeRuntime: false <br>
    hasToStringProxy: false <br>
    hasBadWebGL: false <br>

→ **Bot 차단 걱정 없음. 완전한 실제 브라우징 시뮬레이션.**

---

## ⚠️ 크롤링 주의사항 (Disclaimer)

- 본 코드는 **연구·개발용 / 합법적 접근이 허용된 웹페이지**에 한해 사용해야 합니다.  
- 대상 사이트의 **robots.txt, 이용약관, 저작권 정책**을 반드시 확인하세요.  
- 해당 프로젝트 및 작성자는 **비인가 수집, 상업적 스크래핑, 제3자 피해**에 대해 책임지지 않습니다.  
- 본 코드를 이용함으로써 발생하는 모든 법적 책임은 사용자에게 있습니다.

---

## 🧩 Dependencies

- [Playwright](https://github.com/microsoft/playwright)
- [html2markdown (PyPI)](https://pypi.org/project/html2markdown/)
- Python ≥ 3.10

---

## ⚙️ Installation

```bash
pip install playwright html2markdown
playwright install chromium


  

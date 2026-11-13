# philab-apps.github.io

필랩(Philab) 개발자 사이트. GitHub Pages 로 내보내는 정적 HTML 이다 — 빌드 도구·스크립트·외부 글꼴·분석·쿠키 없음.

```
index.html            홈(한국어)  /
en/index.html         홈(영어)    /en/
site.css              공용 스타일(앱 색 토큰 · 라이트/다크)
tongcap/index.html    Tongcap(영어 — 첫 페이지)  /tongcap/
tongcap/<언어>/       ko · es · ja · zh-Hans · zh-Hant
tongcap/icon.png      앱 아이콘 256px
scripts/check.py      검사
.nojekyll             Jekyll 을 거치지 않고 파일 그대로 내보낸다
```

## 검사

```bash
python3 scripts/check.py <Tongcap 저장소 경로>            # 커밋 전에(1초 안)
python3 scripts/check.py <Tongcap 저장소 경로> --online   # 바깥 링크(App Store·처리방침)까지 실제로 요청
```

보는 것: 사이트 파일만 있는지 · 로컬 서버로 모든 페이지 200 · 사이트 안 링크가 있는 파일을 가리키는지 · `<script>`·외부 글꼴·분석 0 · mailto 는 `philab.help@gmail.com` 하나 · 개인 이름 0 · `lang`·`hreflang` 짝 · Tongcap 이름·부제가 Tongcap 저장소 `docs/스토어-문구.md` 와, 처리방침 링크가 `PolicyPage.swift` 와, 앱 ID 가 `docs/출시-신고값.md` 와 글자까지 같은지. 시작할 때 사본을 일부러 깨뜨려(고정본 다섯) 규칙이 떨어지는지 스스로 본다. Tongcap 저장소 경로가 틀리면 건너뛰지 않고 실패한다.

스토어 이름·부제나 처리방침 주소가 바뀌면 Tongcap 저장소를 먼저 고치고, 여기 HTML 여섯 장(+ 홈 카드 부제 둘)을 같은 글자로 고친 뒤 검사를 돌린다.

## 앱 폴더 더하는 법

1. `<앱>/index.html`(영어) 와 `<앱>/<언어>/index.html` 을 `tongcap/` 꼴 그대로 만든다 — 머리의 `hreflang` 대체 링크(자기 자신·`x-default` 포함)를 모든 언어 페이지에 똑같이, 언어 고르기 `<details>` 는 지금 언어에 `aria-current="page"`.
2. 아이콘은 `<앱>/icon.png`(256px, `alt=""`).
3. 홈 두 장(`index.html`·`en/index.html`)의 "앱" 절에 `app-card` 를 하나씩 더한다 — 카드는 같은 언어 페이지로.
4. `scripts/check.py` 는 지금 Tongcap 의 이름·부제·처리방침만 대조한다. 새 앱의 기준 파일이 생기면 같은 꼴로 더한다.

## App Store 배지 넣는 자리

지금은 배지 대신 글자 링크다(`<a class="badge">` — 그 언어의 "App Store에서 다운로드" 문구). Apple 공식 검정 배지 SVG 를 받으면:

| 언어 | 파일 | 쓰는 페이지 |
|---|---|---|
| ko | `badges/app-store-ko.svg` | `tongcap/ko/` |
| en | `badges/app-store-en.svg` | `tongcap/` |
| es | `badges/app-store-es.svg` | `tongcap/es/` |
| ja | `badges/app-store-ja.svg` | `tongcap/ja/` |
| zh-Hans | `badges/app-store-zh-Hans.svg` | `tongcap/zh-Hans/` |
| zh-Hant | `badges/app-store-zh-Hant.svg` | `tongcap/zh-Hant/` |

- `<a class="badge">` 안의 글자를 `<img src="../../badges/app-store-ko.svg" alt="(배지에 쓰인 그 언어 문구)">` 로 바꾼다(영어 페이지는 `../badges/…`). 높이는 `site.css` 가 3rem(48px) — Apple 최소 40px, 둘레 빈칸은 높이의 1/4.
- 배지 그림은 고치거나 색을 바꾸지 않고, 한 화면에 하나만, Apple 서버에서 직접 불러오지 않는다(방문자 정보가 넘어간다 — 저장소에 둔다).
- 배지를 쓰면 바닥 상표 표기에 Apple 과 Apple 로고를 더한다(예: "Apple, Apple 로고, iPhone 및 App Store는 …").

## 지원 링크 넣는 자리

Tongcap 지원 페이지(Notion 공개본) 주소 기록을 아직 찾지 못해 "도움말" 묶음에 지원 줄이 없다. 주소가 정해지면 처리방침 줄 아래에 같은 꼴로 더한다:

```html
<li><a href="(그 언어 지원 주소)">지원<span class="ext" aria-hidden="true">↗</span></a></li>
```

줄 이름: ko 지원 · en Support · es Soporte · ja サポート · zh-Hans 支持 · zh-Hant 支援.

## 공개 순서

밖으로 나가는 일이라 허락을 받은 뒤에 한다.

```bash
python3 scripts/check.py <Tongcap 저장소 경로> --online      # 1. 통과 확인
gh repo create philab-apps/philab-apps.github.io --public \
  --source . --remote origin --push                         # 2. 저장소 만들고 main 푸시
gh api -X POST repos/philab-apps/philab-apps.github.io/pages \
  -f 'source[branch]=main' -f 'source[path]=/'              # 3. Pages 켜기(이미 켜졌으면 409 — 괜찮다)
gh api repos/philab-apps/philab-apps.github.io/pages --jq '.status, .html_url'   # 4. built 확인
curl -sI https://philab-apps.github.io/tongcap/ | head -1   # 5. 200 확인(처음은 몇 분 걸린다)
```

`app-ads.txt` 는 AdMob 게시자 ID 가 나온 뒤 뿌리에 둔다(그 전에는 만들지 않는다).

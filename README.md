# Philab

일상의 작은 불편을 덜어 주는 앱을 소개하는 필랩의 포트폴리오 사이트.
GitHub Pages에서 제공하는 정적 HTML과 CSS입니다. 배포 서비스의 빌드 단계나 브라우저 자바스크립트는 필요하지 않습니다. 앱 목록을 수정할 때만 아래 생성 명령으로 HTML을 갱신해 함께 커밋합니다.

## 구성

- `/`: 한국어 홈. 스튜디오 소개, 전체 앱 목록, 개발 방향, 문의.
- `/en/`: 영어 홈.
- `/tongcap/`: 통캡 영어 상세 페이지.
- `/tongcap/ko/`, `/tongcap/ja/`, `/tongcap/es/`, `/tongcap/de/`, `/tongcap/fr/`, `/tongcap/it/`, `/tongcap/zh-Hans/`, `/tongcap/zh-Hant/`: 언어별 상세 페이지.
- `/tongcap/privacy/`, `/tongcap/support/`: 영어 개인정보 처리방침과 지원 페이지. 다른 8개 언어는 각 상세 페이지 경로 아래 `privacy/`, `support/`를 사용합니다.
- `content/tongcap/documents.json`: 공개 Notion 문서 12개(2026-11-15)와 de·fr·it 처리방침·지원 6개의 원문, 출처, 원문 해시.
- `content/tongcap/links.json`: 언어별 기존 Notion 주소와 새 GitHub Pages 주소.
- `scripts/render_documents.py`: 원문을 공통 문서 디자인의 정적 HTML로 생성.
- `site.css`: 공통 디자인, 모바일 배치, 시스템 다크 모드, 키보드 포커스와 동작 줄이기 대응.
- `brand/`: 앱과 구분되는 필랩의 공용 아이콘.
- `apps.json`: 홈에 표시할 출시 앱의 이름·아이콘·플랫폼·한국어/영어 소개와 상세 페이지 주소.
- `scripts/render_apps.py`: 앱 목록을 한국어/영어 홈의 정적 카드로 생성.
- `tongcap/icon.png`: 통캡의 앱 아이콘.
- `app-ads.txt`: 기존 AdMob 등록 정보.
- `.nojekyll`: 정적 파일을 그대로 게시하도록 지정.

통캡 페이지에는 기능, 웹 캡처 사용법, 무료/Pro 구분, 무료 체험 안내, FAQ, 이 사이트의 지원·개인정보 처리방침 링크가 있습니다. 화면 그림은 CSS로 만든 기능 설명용 일러스트이며 실제 앱 스크린샷이 아닙니다. 언어 선택과 FAQ는 HTML `details` 요소로 동작합니다. 자바스크립트, 외부 글꼴, 분석 도구, 쿠키를 사용하지 않습니다.

## 로컬 미리보기

```bash
python3 -m http.server 4173 --bind 127.0.0.1
```

브라우저에서 `http://127.0.0.1:4173/`를 엽니다. 별도 패키지 설치는 필요 없습니다.

## 새 앱 추가하기

홈은 필랩 브랜드와 전체 앱 목록을 소개하고, 앱별 기능·가격·지원·개인정보 내용은 `/<앱 ID>/` 아래 상세 페이지에 둡니다. 홈의 소개 문구와 대표 이미지는 특정 앱에 종속되지 않습니다. 실제 출시한 앱만 목록에 추가하며, 미정 앱이나 빈 카드는 표시하지 않습니다.

1. `/<앱 ID>/index.html`에 영어 상세 페이지, `/<앱 ID>/ko/index.html`에 한국어 상세 페이지를 만듭니다. 통캡 페이지의 머리·언어 메뉴·바닥 구조를 참고하되, 앱 이름·설명·ID·지원·정책·App Store 주소와 `canonical`·`hreflang`을 해당 앱에 맞게 교체합니다. 앱마다 필요한 추가 언어를 제공할 수 있습니다.
2. 앱 폴더에 아이콘을 넣습니다. `apps.json`의 `apps` 배열에 기존 통캡 항목과 같은 구조로 추가합니다. `id`는 폴더명과 일치하는 고유 값, `icon`과 `locales.*.path`는 사이트 루트 기준의 상대 경로입니다. `platform`에는 실제 지원 플랫폼을 적고, 각 언어의 `subtitle`, `description`, `tags`(1~3개)를 입력합니다. 배열 순서가 표시 순서입니다.
3. 아래 명령을 실행합니다. 두 홈의 `apps:generated` 주석 사이만 갱신하므로 그 안의 카드를 직접 수정하지 않습니다.

```bash
python3 scripts/render_apps.py
python3 scripts/render_apps.py --check
```

카드는 한 앱일 때 넓은 가로 배치, 여러 앱일 때 데스크톱 2열, 모바일 1열로 자동 배치됩니다. 앱을 더하기 위해 홈 구조나 CSS를 수정할 필요가 없습니다. 생성기는 중복 ID, 누락된 아이콘·상세 페이지, 언어와 경로 불일치, 오래된 생성 결과를 검사합니다.

앱 목록, 생성된 두 홈, 새 앱 폴더를 함께 커밋합니다. 새 언어를 추가할 경우 `scripts/check.py`의 허용 언어 목록도 확인합니다. 기존 검사기의 스토어 문구 대조는 통캡만 대상으로 하므로 새 앱의 스토어 정보도 별도로 대조해야 합니다.

## 검사

```bash
python3 scripts/render_apps.py --check
python3 scripts/render_documents.py --check
python3 scripts/check.py <Tongcap 저장소 경로>
python3 scripts/check.py <Tongcap 저장소 경로> --online
```

기존 검사기는 앱 소스 저장소의 `docs/스토어-문구.md`, `PolicyPage.swift`, `docs/출시-신고값.md`를 기준으로 앱 이름·부제·정책 링크·앱 ID를 대조합니다. 소스 저장소가 없으면 이 명령은 실패합니다. 그 밖에 29개 페이지의 언어 연결, 로컬 링크, HTTP 응답, 외부 자원 부재, 문의 주소, AdMob 형식을 확인하고, 오류를 주입하는 9개 고정본으로 검사기 자체도 검증합니다. 문서의 제목·문단 순서·본문·링크·원문 해시도 대조합니다. 앱의 정책 URL은 `links.json`의 이전 전 또는 이전 후 주소와 일치해야 하고, 사이트의 정책·지원 링크는 새 주소로 연결되어야 합니다. 개인정보 처리방침에 원래 있던 Google Korea 연락처는 그대로 유지합니다.

스토어 이름·부제나 정책 주소를 변경할 때에는 앱 저장소를 기준으로 모든 언어 페이지와 홈 카드의 값을 함께 수정합니다. 기능이나 가격 정책을 변경하면 6개 언어의 기능·요금·FAQ 문구도 함께 확인합니다. 가격은 지역별로 다르므로 사이트에 금액을 고정하지 않습니다.

디자인 변경 후에는 데스크톱과 320px·390px 모바일 너비에서 줄바꿈, 가로 넘침, 언어 선택, FAQ, 페이지 내 이동, 다운로드·지원 링크를 확인합니다. `canonical`, `hreflang`, Open Graph 메타데이터는 각 페이지의 실제 주소를 유지해야 합니다.

## 배포

이 저장소는 이미 GitHub Pages에 연결되어 있으며 `main` 브랜치의 루트가 공개 사이트에 자동 배포됩니다. 변경 내용을 검토하고 검증한 뒤 반영합니다. 공개 반영은 허락을 받은 뒤 진행합니다.

```bash
gh api repos/philab-apps/philab-apps.github.io/pages --jq '.status, .html_url'
```

`app-ads.txt`는 광고 설정에서 참조되므로 유지합니다. 기존 Notion 문서는 아래 전환이 끝나도 당분간 공개 상태를 유지합니다.


## 개인정보 처리방침·지원 문서 관리

2026-11-15에 Notion의 6개 언어 개인정보 처리방침과 지원 페이지를 복사했습니다. **정책 시행일은 원문과 같은 2026-11-11**이며, 이전 날짜로 바꾸지 않았습니다. 제목·문구·목록·강조·외부 참고 링크를 보존했고, 지원 문서 안의 통캡 정책 링크만 같은 언어의 새 페이지로 연결했습니다. 개인정보 처리에 대한 약속을 새로 작성하거나 변경하지 않았습니다. Notion은 수정·비공개·삭제하지 않았습니다.

긴 정책에는 목차와 인쇄 스타일을 제공하고, 지원에는 문의처·FAQ를 배치했습니다. 언어 메뉴는 같은 종류의 문서로 이동합니다. 모든 문서는 로그인과 자바스크립트 없이 읽을 수 있습니다.

문서를 수정할 때는 `content/tongcap/documents.json`을 먼저 고친 뒤 다음을 실행합니다. 원문 텍스트를 의도적으로 변경하는 경우 해당 문서의 `source_text_sha256`도 새 `blocks[*].text`를 줄바꿈으로 이어 붙인 UTF-8 문자열의 SHA-256 값으로 갱신해야 합니다. 단순 디자인 변경은 원문과 해시를 수정하지 않습니다.

```bash
python3 scripts/render_documents.py
python3 scripts/render_documents.py --check
```

## 다음 앱 배포 시 URL 교체

웹사이트는 새 주소에 연결되어 있습니다. **이번 이전에서 App Store Connect와 앱 소스는 변경하지 않았습니다.** 다음 앱 배포를 준비할 때 아래 주소로 교체합니다. 기존 주소는 `content/tongcap/links.json`에 함께 기록되어 있습니다.

| 언어 / 스토어 로캘 | 개인정보 처리방침 URL | 지원 URL |
| --- | --- | --- |
| 한국어 / `ko` | [https://philab-apps.github.io/tongcap/ko/privacy/](https://philab-apps.github.io/tongcap/ko/privacy/) | [https://philab-apps.github.io/tongcap/ko/support/](https://philab-apps.github.io/tongcap/ko/support/) |
| 영어 / `en-US` | [https://philab-apps.github.io/tongcap/privacy/](https://philab-apps.github.io/tongcap/privacy/) | [https://philab-apps.github.io/tongcap/support/](https://philab-apps.github.io/tongcap/support/) |
| 일본어 / `ja` | [https://philab-apps.github.io/tongcap/ja/privacy/](https://philab-apps.github.io/tongcap/ja/privacy/) | [https://philab-apps.github.io/tongcap/ja/support/](https://philab-apps.github.io/tongcap/ja/support/) |
| 스페인어 / `es-ES` | [https://philab-apps.github.io/tongcap/es/privacy/](https://philab-apps.github.io/tongcap/es/privacy/) | [https://philab-apps.github.io/tongcap/es/support/](https://philab-apps.github.io/tongcap/es/support/) |
| 중국어 간체 / `zh-Hans` | [https://philab-apps.github.io/tongcap/zh-Hans/privacy/](https://philab-apps.github.io/tongcap/zh-Hans/privacy/) | [https://philab-apps.github.io/tongcap/zh-Hans/support/](https://philab-apps.github.io/tongcap/zh-Hans/support/) |
| 중국어 번체 / `zh-Hant` | [https://philab-apps.github.io/tongcap/zh-Hant/privacy/](https://philab-apps.github.io/tongcap/zh-Hant/privacy/) | [https://philab-apps.github.io/tongcap/zh-Hant/support/](https://philab-apps.github.io/tongcap/zh-Hant/support/) |

1. App Store Connect의 언어별 **Privacy Policy URL**과 앱 버전 정보의 **Support URL**을 표의 주소로 변경합니다. 앱의 실제 스토어 로캘을 확인하고 대응하는 언어 주소를 사용합니다.
2. 앱 안의 개인정보 처리방침·지원 링크도 같은 주소로 교체합니다. `Packages/TallShotCore/Sources/TallShotCore/PolicyPage.swift`와 지원 URL을 보관하는 소스를 확인합니다. 앱 소스의 URL 검사 및 출시 문서도 함께 갱신합니다. `PolicyPage.swift`의 URL 구성 방식이 달라지면 이 사이트 검사기의 `load_truth` 파서도 함께 조정합니다.
3. 출시할 빌드에서 각 언어의 정책·지원 화면과 이메일 문의 연결을 열어 확인합니다.
4. 이전 버전 사용자를 위해 Notion은 당분간 유지합니다. 유지 기간에 정책 내용을 변경하면 두 공개 사본도 일치하도록 관리합니다.

전환 안내는 [Apple의 앱 개인정보 관리 안내](https://developer.apple.com/help/app-store-connect/manage-app-information/manage-app-privacy/)와 [버전별 앱 정보 안내](https://developer.apple.com/help/app-store-connect/reference/app-information/platform-version-information/)를 참고합니다.

### 1.1 개인정보 처리방침 갱신 (2026-11-16)

여섯 언어 정책은 Tongcap 앱의 `App/Resources/<언어>.lproj/PrivacyPolicy.md`와 같은 원문으로 갱신했습니다. 보상형 광고와 실패 진단 항목을 포함하며 시행일은 2026-11-16입니다. `documents.json`의 `source`는 이 앱 원문 경로이고, 최초 이전 출처는 `previous_source`로 남깁니다. 지원 문서는 기존 원문을 유지합니다. 앱의 정책 URL도 GitHub Pages 주소를 사용합니다.

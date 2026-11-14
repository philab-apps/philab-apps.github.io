# Philab

일상의 작은 불편을 덜어 주는 iPhone 앱을 소개하는 개발자 사이트.
GitHub Pages에서 제공하는 정적 HTML과 CSS이며 빌드 단계가 없습니다.

## 구성

- `/`: 한국어 홈. 스튜디오 소개, 통캡 소개, 개발 방향, 문의.
- `/en/`: 영어 홈.
- `/tongcap/`: 통캡 영어 상세 페이지.
- `/tongcap/ko/`, `/tongcap/ja/`, `/tongcap/es/`, `/tongcap/zh-Hans/`, `/tongcap/zh-Hant/`: 언어별 상세 페이지.
- `site.css`: 공통 디자인, 모바일 배치, 시스템 다크 모드, 키보드 포커스와 동작 줄이기 대응.
- `tongcap/icon.png`: 기존 앱 아이콘.
- `app-ads.txt`: 기존 AdMob 등록 정보.
- `.nojekyll`: 정적 파일을 그대로 게시하도록 지정.

통캡 페이지에는 기능, 웹 캡처 사용법, 무료/Pro 구분, 무료 체험 안내, FAQ, 기존 지원·개인정보 처리방침 링크가 있습니다. 화면 그림은 CSS로 만든 기능 설명용 일러스트이며 실제 앱 스크린샷이 아닙니다. 언어 선택과 FAQ는 HTML `details` 요소로 동작합니다. 자바스크립트, 외부 글꼴, 분석 도구, 쿠키를 사용하지 않습니다.

## 로컬 미리보기

```bash
python3 -m http.server 4173 --bind 127.0.0.1
```

브라우저에서 `http://127.0.0.1:4173/`를 엽니다. 별도 패키지 설치는 필요 없습니다.

## 검사

```bash
python3 scripts/check.py <Tongcap 저장소 경로>
python3 scripts/check.py <Tongcap 저장소 경로> --online
```

기존 검사기는 앱 소스 저장소의 `docs/스토어-문구.md`, `PolicyPage.swift`, `docs/출시-신고값.md`를 기준으로 앱 이름·부제·정책 링크·앱 ID를 대조합니다. 소스 저장소가 없으면 이 명령은 실패합니다. 그 밖에 8개 페이지의 언어 연결, 로컬 링크, HTTP 응답, 외부 자원 부재, 문의 주소, AdMob 형식을 확인하고, 오류를 주입하는 6개 고정본으로 검사기 자체도 검증합니다.

스토어 이름·부제나 정책 주소를 변경할 때에는 앱 저장소를 기준으로 모든 언어 페이지와 홈 카드의 값을 함께 수정합니다. 기능이나 가격 정책을 변경하면 6개 언어의 기능·요금·FAQ 문구도 함께 확인합니다. 가격은 지역별로 다르므로 사이트에 금액을 고정하지 않습니다.

디자인 변경 후에는 데스크톱과 320px·390px 모바일 너비에서 줄바꿈, 가로 넘침, 언어 선택, FAQ, 페이지 내 이동, 다운로드·지원 링크를 확인합니다. `canonical`, `hreflang`, Open Graph 메타데이터는 각 페이지의 실제 주소를 유지해야 합니다.

## 배포

이 저장소는 이미 GitHub Pages에 연결되어 있으며 `main` 브랜치의 루트가 공개 사이트에 자동 배포됩니다. 변경 내용을 검토하고 검증한 뒤 반영합니다. 공개 반영은 허락을 받은 뒤 진행합니다.

```bash
gh api repos/philab-apps/philab-apps.github.io/pages --jq '.status, .html_url'
```

기존 앱 지원·정책 주소와 `app-ads.txt`는 App Store 및 광고 설정에서 참조될 수 있으므로 디자인 수정 시 유지합니다.

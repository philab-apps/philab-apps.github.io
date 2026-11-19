#!/usr/bin/env python3
"""필랩 개발자 사이트 검사 — 파이썬 표준 라이브러리만.

쓰기:  python3 scripts/check.py <Tongcap 저장소 경로> [--online]

보는 것(실패하면 끝 코드 1):
  파일   저장소에 사이트 파일만(HTML·CSS·그림·README·이 스크립트 — docs/·.claude/·다른 .md 없음)
  서버   로컬 서버(http.server)로 모든 페이지와 사이트 안 링크가 200
  링크   사이트 안 href·src 가 있는 파일을 가리킴, 자리 표시 링크(#) 없음, 바깥 링크는 목록만(--online 이면 실제 요청)
  밖     <script> 0 · 바깥 <link>·그림 0 · 외부 글꼴·분석(googleapis·googletagmanager 등) 0
  메일   제품·홈은 문의 mailto 하나, 문서는 원문의 문의·관련 기관 메일 보존 · 개인 이름 0
  언어   <html lang> · hreflang 대체 링크가 서로 짝(자기 자신 포함·x-default) · 언어 고르기 링크가 그 언어 페이지로
  Tongcap  이름·부제 = docs/스토어-문구.md · 처리방침 링크 = links.json의 이전 후 URL(앱 소스는 이전 전·후 주소 허용) · 앱 ID = docs/출시-신고값.md
시작할 때 자가점검: 사이트 사본을 일부러 깨뜨려(고정본 아홉) 규칙마다 실패가 나는지 본다.
"""
import html.parser
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import threading
import urllib.request
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urljoin, urlsplit

SITE = 'https://philab-apps.github.io'
MAIL = 'philab.help@gmail.com'
LANGS = ['ko', 'en', 'es', 'de', 'fr', 'it', 'ja', 'zh-Hans', 'zh-Hant']
STORE_LOC = {'ko': 'ko', 'en': 'en-US', 'es': 'es-ES', 'de': 'de-DE', 'fr': 'fr-FR', 'it': 'it', 'ja': 'ja', 'zh-Hans': 'zh-Hans', 'zh-Hant': 'zh-Hant'}
POLICY_LABEL = {'ko': '개인정보 처리방침', 'en': 'Privacy Policy', 'es': 'Política de privacidad',
                'de': 'Datenschutzerklärung', 'fr': 'Politique de confidentialité', 'it': 'Informativa sulla privacy',
                'ja': 'プライバシーポリシー', 'zh-Hans': '隐私政策', 'zh-Hant': '隱私權政策'}
SELF = 'scripts/check.py'
ALLOWED_FILES = [r'README\.md', r'apps\.json', r'scripts/render_apps\.py', r'scripts/render_documents\.py',
                 r'content/tongcap/(?:documents|links)\.json', r'\.nojekyll', r'robots\.txt', r'sitemap\.xml', r'google[0-9a-f]+\.html', r'\.gitignore', r'site\.css', r'app-ads\.txt', re.escape(SELF),
                 r'(?:[A-Za-z0-9-]+/)*index\.html', r'[A-Za-z0-9-]+/(?:[A-Za-z0-9-]+/)*[A-Za-z0-9-]+\.(?:png|svg)']
BANNED_TEXT = ['fonts.googleapis', 'fonts.gstatic', 'googletagmanager', 'google-analytics', 'gtag(', 'document.cookie']
PERSONAL = re.compile(r'phil+ip|필립|\bchung\b', re.I)  # 개인 이름 — 상호 "필랩·Philab" 은 걸리지 않는다
EMAIL = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+')
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr'}


# ---------- HTML 를 작은 나무로 ----------
class Node:
    def __init__(self, tag, attrs, parent):
        self.tag, self.attrs, self.parent, self.kids = tag, dict(attrs), parent, []

    def cls(self):
        return (self.attrs.get('class') or '').split()

    def text(self, label=False):
        """label=True 면 aria-hidden·.val(메일 값) 을 뺀 이름 글자만"""
        out = []
        for k in self.kids:
            if isinstance(k, str):
                out.append(k)
            elif k.tag == 'br':
                out.append('\n')
            elif not (label and (k.attrs.get('aria-hidden') == 'true' or 'val' in k.cls())):
                out.append(k.text(label))
        return ''.join(out)

    def all(self):
        for k in self.kids:
            if isinstance(k, Node):
                yield k
                yield from k.all()


class Tree(html.parser.HTMLParser):
    def __init__(self, src):
        super().__init__(convert_charrefs=True)
        self.root = Node('#doc', {}, None)
        self.cur = self.root
        self.feed(src)
        self.close()

    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs, self.cur)
        self.cur.kids.append(n)
        if tag not in VOID:
            self.cur = n

    def handle_startendtag(self, tag, attrs):
        self.cur.kids.append(Node(tag, attrs, self.cur))

    def handle_endtag(self, tag):
        n = self.cur
        while n is not self.root and n.tag != tag:
            n = n.parent
        if n is not self.root:
            self.cur = n.parent

    def handle_data(self, data):
        self.cur.kids.append(data)


def norm(s):
    return ' '.join(s.split())


# ---------- Tongcap 저장소에서 기준 값 읽기 (못 읽으면 실패) ----------
def load_truth(tongcap):
    def read(rel):
        p = os.path.join(tongcap, rel)
        if not os.path.isfile(p):
            sys.exit(f'실패: Tongcap 저장소에 {rel} 없음 — 경로 {tongcap!r} 확인')
        return open(p, encoding='utf-8').read()

    swift = read('Packages/TallShotCore/Sources/TallShotCore/PolicyPage.swift')
    addresses = re.findall(r'case \.(\w+): "(https://philab-apps\.github\.io/tongcap/[^\"]+)"', swift)
    case_lang = {'zhHans': 'zh-Hans', 'zhHant': 'zh-Hant'}
    policy = {case_lang.get(c, c): address for c, address in addresses}
    if set(policy) != set(LANGS):
        sys.exit(f'실패: PolicyPage.swift 에서 처리방침 주소 아홉을 못 읽음(읽은 것 {sorted(policy)})')

    md = read('docs/스토어-문구.md')
    store = {}
    for lang, loc in STORE_LOC.items():
        sec = re.search(r'^## ' + re.escape(loc) + r'\n(.*?)(?=^## |\Z)', md, re.S | re.M)
        name = sec and re.search(r'^### 이름\n+```text\n(.+?)\n```', sec.group(1), re.M)
        sub = sec and re.search(r'^### 부제\n+```text\n(.+?)\n```', sec.group(1), re.M)
        if not (name and sub):
            sys.exit(f'실패: 스토어-문구.md 의 {loc} 이름·부제를 못 읽음')
        store[lang] = (name.group(1).strip(), sub.group(1).strip())

    m = re.search(r'\|\s*앱 Apple ID\s*\|\s*`(\d+)`', read('docs/출시-신고값.md'))
    if not m:
        sys.exit('실패: 출시-신고값.md 에서 앱 Apple ID 를 못 읽음')
    return policy, store, m.group(1)


# ---------- 사이트 읽기 ----------
def site_files(root):
    out = []
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x != '.git']
        out += [os.path.relpath(os.path.join(d, f), root) for f in files if f != '.DS_Store']
    return sorted(out)


def page_url(rel):  # tongcap/ko/index.html → https://…/tongcap/ko/
    return SITE + '/' + rel[:-len('index.html')]


def local(root, url):  # 사이트 안 주소 → 파일 경로, 밖이면 None
    u = urlsplit(url)
    if f'{u.scheme}://{u.netloc}' != SITE:
        return None
    p = unquote(u.path)
    return os.path.join(root, p.lstrip('/'), 'index.html') if p.endswith('/') else os.path.join(root, p.lstrip('/'))


def load_pages(root):
    pages = {}
    for rel in site_files(root):
        if rel.endswith('index.html'):
            t = Tree(open(os.path.join(root, rel), encoding='utf-8').read()).root
            pages[page_url(rel)] = (rel, t)
    return pages


# ---------- 규칙 ----------
def check_static(root, truth):
    """서버·바깥 요청 없이 보는 규칙 전부. (오류 목록, 바깥 링크, 사이트 안 주소) 를 돌려준다."""
    policy, store, app_id = truth
    err, external, internal = [], set(), set()
    files = site_files(root)
    pages = load_pages(root)
    documents = json.load(open(os.path.join(root, 'content/tongcap/documents.json'), encoding='utf-8'))
    migrations = json.load(open(os.path.join(root, 'content/tongcap/links.json'), encoding='utf-8'))
    migration = {d['language']: d for d in migrations}
    document_by_url = {SITE + d['path']: d for d in documents}
    required_docs = {SITE + '/tongcap/' + ('' if lang == 'en' else lang + '/') + kind + '/'
                     for lang in LANGS for kind in ('privacy', 'support')}
    if set(document_by_url) != required_docs or len(documents) != 18:
        err.append('지원·정책 원문은 9개 언어 × 2종류여야 한다')
    for d in documents:
        digest = hashlib.sha256('\n'.join(b['text'] for b in d['blocks']).encode()).hexdigest()
        if digest != d['source_text_sha256']:
            err.append(f'{d["path"]}: 원문 내용 해시 불일치')
        entry = migration[d['lang']][d['kind']]
        # de·fr·it 는 옛 Notion 문서가 없어 notion_url 이 없다
        if entry['github_pages_url'] != SITE + d['path'] or entry.get('notion_url', d['source']) != d.get('previous_source', d['source']):
            err.append(f'{d["path"]}: 이전 URL 목록과 원문 출처 불일치')
        if SITE + d['path'] not in pages:
            err.append(f'{d["path"]}: 이전 문서 없음')
    for lang in LANGS:
        if policy[lang] not in migration[lang]['privacy'].values():
            err.append(f'{lang}: 앱의 처리방침 URL이 이전 전·후 주소에 없음')

    # 파일
    for f in files:
        if not any(re.fullmatch(p, f) for p in ALLOWED_FILES):
            err.append(f'사이트 파일 아님: {f}')
    texts = {f: open(os.path.join(root, f), encoding='utf-8', errors='replace').read()
             for f in files if f != SELF and not f.endswith('.png')}
    if 'app-ads.txt' in texts and not re.fullmatch(r'google\.com, pub-\d+, DIRECT, f08c47fec0942fa0\n', texts['app-ads.txt']):
        err.append('app-ads.txt: "google.com, pub-<게시자 ID>, DIRECT, f08c47fec0942fa0" 한 줄이어야 한다')
    for f, s in texts.items():
        for b in BANNED_TEXT:
            if b in s:
                err.append(f'{f}: 외부 글꼴·분석 흔적 "{b}"')
        for m in PERSONAL.finditer(s):
            err.append(f'{f}: 개인 이름 "{m.group(0)}"')
        if f.endswith(('.css', '.html')) and re.search(r'@import|url\(\s*["\']?(?:https?:)?//', s):
            err.append(f'{f}: CSS 가 바깥 자원을 부름')
        seen = html.unescape(re.sub(r'<[^>]+>', ' ', s.replace('<wbr>', ''))) if f.endswith('.html') else s
        for m in EMAIL.finditer(seen):  # 보이는 글의 메일 주소(태그 속성은 아래 mailto 규칙이 본다)
            # Preserve the public Google Korea contact already present in policy originals.
            original_policy = f == 'content/tongcap/documents.json' or page_url(f) in document_by_url and document_by_url[page_url(f)]['kind'] == 'privacy'
            if m.group(0) != MAIL and not (original_policy and m.group(0) == 'googlekrsupport@google.com'):
                err.append(f'{f}: 다른 메일 주소 {m.group(0)}')
    # 하한 — 0장 읽고 통과하지 않게
    if len(pages) < 29:
        err.append(f'페이지가 {len(pages)}장뿐(하한 29)')
    # sitemap.xml — 사이트 안 주소만, 실제 있는 쪽만(로컬 서버가 200 을 주는 쪽)
    locs = re.findall(r'<loc>([^<]*)</loc>', texts.get('sitemap.xml', ''))
    if not locs:
        err.append('sitemap.xml 에 <loc> 이 없음')
    for u in locs:
        f = local(root, u)
        if f is None or not os.path.isfile(f):
            err.append(f'sitemap.xml: 사이트 안에 없는 주소 {u}')

    tongcap_langs, home_langs = set(), set()
    for url, (rel, doc) in pages.items():
        E = lambda m: err.append(f'{rel}: {m}')
        nodes = list(doc.all())
        htm = next((n for n in nodes if n.tag == 'html'), None)
        lang = htm.attrs.get('lang') if htm else None
        if lang not in LANGS:
            E(f'<html lang> 이 {lang!r} — {LANGS} 중 하나여야')
            continue
        # 밖
        for n in nodes:
            if n.tag == 'script':
                E('<script> 있음 — 스크립트 0')
            if n.tag in ('iframe', 'object', 'embed'):
                E(f'<{n.tag}> 있음')
            if n.tag == 'link' and n.attrs.get('rel') != 'alternate' and local(root, urljoin(url, n.attrs.get('href', ''))) is None:
                E(f'바깥 <link>: {n.attrs.get("href")}')
            if n.tag in ('img', 'source', 'video', 'audio') and local(root, urljoin(url, n.attrs.get('src', ''))) is None:
                E(f'바깥 그림·미디어: {n.attrs.get("src")}')
        # 링크
        mailtos = []
        for n in nodes:
            for attr in ('href', 'src'):
                v = n.attrs.get(attr)
                if v is None or n.tag in ('meta',):
                    continue
                if v.startswith('mailto:'):
                    mailtos.append(v)
                    continue
                if v == '' or v.startswith('#'):
                    E(f'자리 표시 링크 {attr}="{v}"')
                    continue
                full = urljoin(url, v)
                f = local(root, full)
                if f is None:
                    external.add(full)
                elif os.path.isdir(f):
                    E(f'폴더 링크 끝에 / 없음: {v}')
                elif not os.path.isfile(f):
                    E(f'없는 파일을 가리킴: {v}')
                else:
                    internal.add(urlsplit(full).path)
        # 메일
        if url in document_by_url:
            source_tree = Tree(''.join(b['html'] for b in document_by_url[url]['blocks'])).root
            original_mailtos = [n.attrs['href'] for n in source_tree.all() if n.tag == 'a' and n.attrs.get('href', '').startswith('mailto:')]
            if mailtos != original_mailtos or f'mailto:{MAIL}' not in mailtos:
                E('문서의 문의 메일 링크가 원문과 다름')
        elif mailtos != [f'mailto:{MAIL}']:
            E(f'mailto 는 {MAIL} 하나여야 — {mailtos}')
        # 언어 — 대체 링크 짝
        alts = {(n.attrs.get('hreflang'), urljoin(url, n.attrs.get('href', ''))) for n in nodes
                if n.tag == 'link' and n.attrs.get('rel') == 'alternate'}
        alt_of = dict(alts)
        if len(alt_of) != len(alts):
            E('한 hreflang 에 대체 링크가 둘')
        if alt_of.get(lang) != url:
            E(f'hreflang="{lang}" 자기 자신 대체 링크 없음')
        if 'x-default' not in alt_of or local(root, alt_of['x-default']) is None:
            E('hreflang="x-default" 없음')
        for h, u in alts:
            f = local(root, u)
            if f is None or u not in pages:
                E(f'대체 링크 {h} → 없는 페이지 {u}')
                continue
            if h == 'x-default':
                continue
            other = pages[u][1]
            olang = next((n.attrs.get('lang') for n in other.all() if n.tag == 'html'), None)
            if olang != h:
                E(f'대체 링크 hreflang="{h}" 인데 그 페이지 lang="{olang}"')
            oalts = {(n.attrs.get('hreflang'), urljoin(u, n.attrs.get('href', ''))) for n in other.all()
                     if n.tag == 'link' and n.attrs.get('rel') == 'alternate'}
            if oalts != alts:
                E(f'대체 링크 묶음이 {pages[u][0]} 와 다름(짝이 안 맞음)')
        # 언어 고르기 링크
        picks = [n for n in nodes if n.tag == 'a' and 'hreflang' in n.attrs]
        for n in picks:
            h = n.attrs['hreflang']
            if n.attrs.get('lang') != h:
                E(f'언어 링크 hreflang="{h}" 인데 lang="{n.attrs.get("lang")}"')
            if urljoin(url, n.attrs.get('href', '')) != alt_of.get(h):
                E(f'언어 링크 {h} 가 대체 링크와 다른 곳으로: {n.attrs.get("href")}')
        if {n.attrs['hreflang'] for n in picks} | {lang} != set(alt_of) - {'x-default'}:
            E('언어 고르기 링크와 대체 링크의 언어가 다름')

        # Tongcap 페이지
        if url in document_by_url:
            source = document_by_url[url]
            source_nodes = [n for n in nodes if 'data-source-block' in n.attrs]
            if [n.attrs['data-source-block'] for n in source_nodes] != [str(i) for i in range(len(source['blocks']))]:
                E('원문 문단 순서·개수 불일치')
            if [norm(n.text()) for n in source_nodes] != [norm(b['text']) for b in source['blocks']]:
                E('원문 내용 불일치')
            if [n.text() for n in nodes if n.tag == 'h1'] != [source['title']]:
                E('원문 제목 불일치')
            source_links = [n.attrs['href'] for n in Tree(''.join(b['html'] for b in source['blocks'])).root.all() if n.tag == 'a']
            actual_links = [n.attrs['href'] for parent in source_nodes for n in parent.all() if n.tag == 'a']
            if actual_links != source_links:
                E('원문 본문 링크 불일치')
            expected_alts = {h: SITE + '/tongcap/' + ('' if h == 'en' else h + '/') + source['kind'] + '/' for h in LANGS}
            if {h: u for h, u in alt_of.items() if h != 'x-default'} != expected_alts:
                E('문서의 언어 메뉴는 같은 종류의 문서로 연결해야 한다')
        elif url in {SITE + '/tongcap/' + ('' if code == 'en' else code + '/') for code in LANGS}:
            tongcap_langs.add(lang)
            name, sub = store[lang]
            pick = lambda pred: [norm(n.text()) for n in nodes if pred(n)]
            for what, got, want in [('이름(h1)', pick(lambda n: n.tag == 'h1'), [name]),
                                    ('이름(title)', pick(lambda n: n.tag == 'title'), [name]),
                                    ('부제(.sub)', pick(lambda n: 'sub' in n.cls()), [sub]),
                                    ('부제(description)', [n.attrs.get('content') for n in nodes
                                                          if n.tag == 'meta' and n.attrs.get('name') == 'description'], [sub])]:
                if got != want:
                    E(f'{what} {got} ≠ 스토어-문구.md {STORE_LOC[lang]} {want}')
            pol = [n.attrs.get('href') for n in nodes if n.tag == 'a' and norm(n.text(label=True)) == POLICY_LABEL[lang]]
            if [urljoin(url, p) for p in pol] != [migration[lang]['privacy']['github_pages_url']]:
                E(f'처리방침 링크 {pol} ≠ 이전 URL 목록 {lang}')
            if not any(n.tag == 'a' and urljoin(url, n.attrs.get('href', '')) == migration[lang]['support']['github_pages_url'] for n in nodes):
                E('이전된 지원 페이지 링크 없음')
            banner = [n.attrs.get('content') for n in nodes if n.tag == 'meta' and n.attrs.get('name') == 'apple-itunes-app']
            if banner != [f'app-id={app_id}']:
                E(f'스마트 앱 배너 {banner} ≠ app-id={app_id}')
            stores = [n.attrs.get('href', '') for n in nodes if n.tag == 'a' and 'apps.apple.com' in n.attrs.get('href', '')]
            if len(stores) != 1 or not re.fullmatch(r'https://apps\.apple\.com/[a-z]{2}/app/id' + app_id + r'(\?l=[A-Za-z-]+)?', stores[0]):
                E(f'App Store 링크 {stores} — https://apps.apple.com/<나라>/app/id{app_id} 하나여야')
        elif url in (SITE + '/', SITE + '/en/'):
            home_langs.add(lang)
            for card in (n for n in nodes if 'app-card' in n.cls()):
                target = urljoin(url, card.attrs.get('href', ''))
                if not target.startswith(SITE + '/tongcap/'):
                    continue
                subs = [norm(n.text()) for n in card.all() if 'app-sub' in n.cls()]
                if subs != [store[lang][1]]:
                    E(f'Tongcap 카드 부제 {subs} ≠ 스토어-문구.md {STORE_LOC[lang]} {store[lang][1]!r}')
                tlang = target in pages and next(n.attrs.get('lang') for n in pages[target][1].all() if n.tag == 'html')
                if tlang != lang:
                    E(f'Tongcap 카드가 다른 언어 페이지로 감 {card.attrs.get("href")}')
    if tongcap_langs != set(LANGS):
        err.append(f'Tongcap 페이지 언어가 {sorted(tongcap_langs)} — 여섯이어야')
    if home_langs != {'ko', 'en'}:
        err.append(f'홈 언어가 {sorted(home_langs)} — ko·en 이어야')
    return err, sorted(external), sorted(internal | {urlsplit(u).path for u in pages})


def check_server(root, paths):
    """로컬 서버로 모든 페이지·사이트 안 자원이 200 인지"""
    class Quiet(SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    srv = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=root))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    err = []
    try:
        for p in paths:
            try:
                code = urllib.request.urlopen(f'http://127.0.0.1:{srv.server_port}{p}', timeout=10).status
            except Exception as e:  # noqa: BLE001 — 404 도 여기로 온다
                code = getattr(e, 'code', repr(e))
            if code != 200:
                err.append(f'로컬 서버 {p} → {code}')
    finally:
        srv.shutdown()
        srv.server_close()
    if not paths:
        err.append('로컬 서버로 잴 주소가 0개')
    return err


def check_online(urls):
    err = []
    for u in urls:
        req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0 (site link check)'})
        try:
            code = urllib.request.urlopen(req, timeout=20).status
        except Exception as e:  # noqa: BLE001
            code = getattr(e, 'code', repr(e))
        print(f'  {code}  {u}')
        if code != 200:
            err.append(f'바깥 링크 {u} → {code}')
    return err


# ---------- 자가점검: 사본을 깨뜨려 규칙이 떨어지는지 ----------
FIXTURES = [  # (파일, 바꿀 글, 새 글, 나와야 할 오류 낱말)
    ('index.html', '</head>', '<script src="https://www.googletagmanager.com/gtag/js?id=G-X"></script></head>', '<script>'),
    ('tongcap/ja/index.html', 'href="/tongcap/ja/privacy/"', 'href="/tongcap/privacy/"', '처리방침 링크'),
    ('tongcap/es/index.html', 'href="../ja/" lang="ja"', 'href="../zh-Hans/" lang="ja"', '언어 링크 ja'),
    ('tongcap/zh-Hant/index.html', '<p class="sub">網頁與聊天記錄完整存成一張長圖</p>', '<p class="sub">網頁與聊天記錄完整存成一張圖</p>', '부제(.sub)'),
    ('app-ads.txt', 'DIRECT', 'RESELLER', 'app-ads.txt'),
    ('sitemap.xml', '/tongcap/it/privacy/', '/tongcap/it/nowhere/', 'sitemap.xml'),
    ('docs/메모.md', None, '# 내부 메모', '사이트 파일 아님'),
    ('tongcap/ko/privacy/index.html', '시행일: 2026년 11월 18일', '시행일: 2026년 11월 17일', '원문 내용 불일치'),
    ('tongcap/support/index.html', 'Tap &quot;Restore Purchases&quot; in Settings.', 'Tap Settings.', '원문 내용 불일치'),
]


def self_test(root, truth):
    tmp = tempfile.mkdtemp()
    try:
        base = os.path.join(tmp, 'clean')
        shutil.copytree(root, base, ignore=shutil.ignore_patterns('.git'))
        clean = check_static(base, truth)[0]
        if clean:
            return [f'자가점검: 깨끗한 사본에서 오류 {len(clean)}개(먼저 아래 본 검사를 고친다)']
        bad = []
        for i, (f, old, new, want) in enumerate(FIXTURES):
            d = os.path.join(tmp, str(i))
            shutil.copytree(base, d)
            p = os.path.join(d, f)
            if old is None:
                os.makedirs(os.path.dirname(p), exist_ok=True)
                open(p, 'w').write(new)
            else:
                s = open(p, encoding='utf-8').read()
                if old not in s:
                    bad.append(f'자가점검 고정본 {i}: {f} 에 "{old}" 가 없어 깨뜨리지 못함 — 고정본을 고친다')
                    continue
                open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
            errs = check_static(d, truth)[0]
            if not any(want in e for e in errs):
                bad.append(f'자가점검 고정본 {i}({f}): "{want}" 오류가 안 나옴 — 규칙이 깨졌다 {errs[:3]}')
        return bad
    finally:
        shutil.rmtree(tmp)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(args) != 1:
        sys.exit(__doc__)
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    truth = load_truth(os.path.expanduser(args[0]))

    static_err, external, internal = check_static(root, truth)
    err = static_err + check_server(root, internal) + (self_test(root, truth) if not static_err else [])
    print(f'페이지 {len(load_pages(root))}장 · 로컬 서버로 주소 {len(internal)}개 · '
          + (f'자가점검 고정본 {len(FIXTURES)}개' if not static_err else '자가점검은 본 검사가 먼저 실패해 안 돌림'))
    print(f'바깥 링크 {len(external)}개' + (' — 실제 요청:' if '--online' in sys.argv else ' (--online 이면 실제 요청)'))
    if '--online' in sys.argv:
        err += check_online(external)
    else:
        for u in external:
            print(f'  {u}')
    for e in err:
        print(f'실패: {e}')
    print('통과' if not err else f'실패 {len(err)}건')
    sys.exit(1 if err else 0)


if __name__ == '__main__':
    main()

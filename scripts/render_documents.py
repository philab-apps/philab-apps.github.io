#!/usr/bin/env python3
"""Render Tongcap's help documents (privacy in nine languages, support in six) using only the standard library."""
import hashlib
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = 'https://philab-apps.github.io'
LANGUAGES = {'ko': '한국어', 'en': 'English', 'ja': '日本語', 'es': 'Español', 'de': 'Deutsch', 'fr': 'Français', 'it': 'Italiano', 'zh-Hans': '简体中文', 'zh-Hant': '繁體中文'}
# 앱 소개·지원 쪽이 있는 언어. de·fr·it 는 처리방침만 있다(스토어 문구를 합친 뒤 소개·지원을 더한다).
PRODUCT_LANGS = ('ko', 'en', 'ja', 'es', 'zh-Hans', 'zh-Hant')
LABELS = {
    'ko': ('개인정보 처리방침', '지원', '이 페이지의 내용', '본문으로 바로가기', '맨 위로', '필랩'),
    'en': ('Privacy Policy', 'Support', 'On this page', 'Skip to content', 'Back to top', 'Philab'),
    'ja': ('プライバシーポリシー', 'サポート', '目次', '本文へスキップ', 'ページの先頭へ', 'Philab'),
    'es': ('Política de privacidad', 'Soporte', 'En esta página', 'Saltar al contenido', 'Volver arriba', 'Philab'),
    'zh-Hans': ('隐私政策', '支持', '本页内容', '跳至正文', '返回顶部', 'Philab'),
    'zh-Hant': ('隱私權政策', '支援', '本頁內容', '跳至內文', '返回頂端', 'Philab'),
    'de': ('Datenschutzerklärung', 'Support', 'Auf dieser Seite', 'Zum Inhalt springen', 'Nach oben', 'Philab'),
    'fr': ('Politique de confidentialité', 'Assistance', 'Sur cette page', 'Aller au contenu', 'Haut de page', 'Philab'),
    'it': ('Informativa sulla privacy', 'Assistenza', 'In questa pagina', 'Vai al contenuto', 'Torna su', 'Philab'),
}


def product_path(lang):
    if lang not in PRODUCT_LANGS:
        lang = 'en'
    return '/tongcap/' + ('' if lang == 'en' else lang + '/')


def doc_languages(kind):
    return LANGUAGES if kind == 'privacy' else {c: n for c, n in LANGUAGES.items() if c in PRODUCT_LANGS}


def document_path(lang, kind):
    return '/tongcap/' + ('' if lang == 'en' else lang + '/') + kind + '/'


def render(doc):
    lang, kind = doc['lang'], doc['kind']
    policy, support, contents, skip, back, brand = LABELS[lang]
    path = document_path(lang, kind)
    assert doc['path'] == path
    e = html.escape
    title = e(doc['title'])
    home = '/' if lang == 'ko' else '/en/'
    languages = doc_languages(kind)
    description = doc['blocks'][1 if kind == 'privacy' else 0]['text']
    alternate = '\n'.join(f'<link rel="alternate" hreflang="{code}" href="{SITE}{document_path(code, kind)}">' for code in languages)
    language_links = '\n'.join(f'<li><a href="{document_path(code, kind)}" lang="{code}" hreflang="{code}"' + (' aria-current="page"' if code == lang else '') + f'>{label}</a></li>' for code, label in languages.items())
    tabs = ''.join(f'<a href="{document_path(lang, value)}"' + (' aria-current="page"' if value == kind else '') + f'>{label}</a>' for value, label in [('privacy', policy)] + ([('support', support)] if lang in PRODUCT_LANGS else []))
    toc = []
    body = []
    in_list = False
    section = 0
    for i, block in enumerate(doc['blocks']):
        typ = block['type']
        if typ != 'bullet' and in_list:
            body.append('</ul>')
            in_list = False
        attrs = f'data-source-block="{i}"'
        if typ == 'heading':
            if section:
                body.append('</section>')
            section += 1
            section_id = f'section-{section}'
            toc.append(f'<li><a href="./#{section_id}">{e(block["text"])}</a></li>')
            body.append(f'<section class="doc-section doc-section-{section}" aria-labelledby="{section_id}"><h2 id="{section_id}" {attrs}>{block["html"]}</h2>')
        elif typ == 'bullet':
            if not in_list:
                body.append('<ul class="doc-list">')
                in_list = True
            body.append(f'<li {attrs}>{block["html"]}</li>')
        elif typ == 'paragraph':
            cls = 'doc-date' if kind == 'privacy' and i == 0 else 'doc-intro' if section == 0 else 'doc-paragraph'
            body.append(f'<p class="{cls}" {attrs}>{block["html"]}</p>')
        else:
            raise ValueError(f'Unsupported block type: {typ}')
    if in_list:
        body.append('</ul>')
    if section:
        body.append('</section>')
    toc_html = '<ol>' + ''.join(toc) + '</ol>'
    content = '\n'.join(body)
    return f'''<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · Philab</title>
<meta name="description" content="{e(description, quote=True)}">
<meta name="theme-color" content="#F6F5F1" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#191B18" media="(prefers-color-scheme: dark)">
<link rel="icon" href="/tongcap/icon.png">
<link rel="stylesheet" href="/site.css">
<link rel="canonical" href="{SITE}{path}">
{alternate}
<link rel="alternate" hreflang="x-default" href="{SITE}{document_path('en', kind)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Philab">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{e(description, quote=True)}">
<meta property="og:url" content="{SITE}{path}">
<meta property="og:image" content="{SITE}/tongcap/icon.png">
</head>
<body class="document-page document-{kind}">
<a class="skip-link" href="./#main">{skip}</a>
<header class="top wrap">
<a class="mark" href="{home}" aria-label="Philab"><span class="mark-symbol" aria-hidden="true"><i></i><i></i><i></i></span>philab<span class="brand-dot">.</span></a>
<nav aria-label="Tongcap"><a href="{product_path(lang)}">Tongcap <span aria-hidden="true">↗</span></a></nav>
<details class="lang"><summary>{LANGUAGES[lang]}</summary><ul>{language_links}</ul></details>
</header>
<main id="main" class="wrap doc-main">
<div class="doc-hero" id="top">
<a class="doc-app" href="{product_path(lang)}"><img src="/tongcap/icon.png" width="36" height="36" alt=""><span>Tongcap</span></a>
<h1>{title}</h1>
<nav class="doc-tabs" aria-label="Tongcap">{tabs}</nav>
</div>
<div class="doc-layout">
<aside class="doc-sidebar"><nav class="doc-toc" aria-label="{contents}"><p>{contents}</p>{toc_html}</nav></aside>
<div class="doc-reading">
<details class="doc-toc-mobile"><summary>{contents}</summary><nav aria-label="{contents}">{toc_html}</nav></details>
<article class="doc-content" aria-label="{title}">
{content}
</article>
<a class="doc-back" href="./#top">{back} <span aria-hidden="true">↑</span></a>
</div>
</div>
</main>
<footer class="foot wrap"><span class="footer-wordmark" aria-hidden="true">philab.</span><p>© 2026 <a href="{home}">{brand}</a></p><p><a href="{product_path(lang)}">Tongcap <span aria-hidden="true">↗</span></a></p></footer>
</body>
</html>
'''


def main():
    documents = json.loads((ROOT / 'content/tongcap/documents.json').read_text())
    expected = {(lang, kind) for kind in ('privacy', 'support') for lang in doc_languages(kind)}
    assert len(documents) == 15 and {(d['lang'], d['kind']) for d in documents} == expected
    errors = []
    for doc in documents:
        # 원문 해시에는 시행일과 문단 순서가 포함된다. source는 앱 원문 또는 이전 Notion 문서다.
        digest = hashlib.sha256('\n'.join(b['text'] for b in doc['blocks']).encode()).hexdigest()
        if digest != doc['source_text_sha256']:
            errors.append(f'Original text changed: {doc["path"]}')
            continue
        rendered = render(doc)
        target = ROOT / doc['path'].lstrip('/') / 'index.html'
        if '--check' in sys.argv:
            if not target.exists() or target.read_text() != rendered:
                errors.append(f'Generated page needs updating: {doc["path"]}')
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(rendered)
    if errors:
        sys.exit('\n'.join(errors))
    print('15 documents: ' + ('up to date; original-text hashes verified' if '--check' in sys.argv else 'rendered'))


if __name__ == '__main__':
    main()

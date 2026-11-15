#!/usr/bin/env python3
"""Render Tongcap's six-language help documents using only the standard library."""
import hashlib
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = 'https://philab-apps.github.io'
LANGUAGES = {'ko': '한국어', 'en': 'English', 'ja': '日本語', 'es': 'Español', 'zh-Hans': '简体中文', 'zh-Hant': '繁體中文'}
LABELS = {
    'ko': ('개인정보 처리방침', '지원', '이 페이지의 내용', '본문으로 바로가기', '맨 위로', '필랩'),
    'en': ('Privacy Policy', 'Support', 'On this page', 'Skip to content', 'Back to top', 'Philab'),
    'ja': ('プライバシーポリシー', 'サポート', '目次', '本文へスキップ', 'ページの先頭へ', 'Philab'),
    'es': ('Política de privacidad', 'Soporte', 'En esta página', 'Saltar al contenido', 'Volver arriba', 'Philab'),
    'zh-Hans': ('隐私政策', '支持', '本页内容', '跳至正文', '返回顶部', 'Philab'),
    'zh-Hant': ('隱私權政策', '支援', '本頁內容', '跳至內文', '返回頂端', 'Philab'),
}


def product_path(lang):
    return '/tongcap/' + ('' if lang == 'en' else lang + '/')


def document_path(lang, kind):
    return product_path(lang) + kind + '/'


def render(doc):
    lang, kind = doc['lang'], doc['kind']
    policy, support, contents, skip, back, brand = LABELS[lang]
    path = document_path(lang, kind)
    assert doc['path'] == path
    e = html.escape
    title = e(doc['title'])
    home = '/' if lang == 'ko' else '/en/'
    description = doc['blocks'][1 if kind == 'privacy' else 0]['text']
    alternate = '\n'.join(f'<link rel="alternate" hreflang="{code}" href="{SITE}{document_path(code, kind)}">' for code in LANGUAGES)
    language_links = '\n'.join(f'<li><a href="{document_path(code, kind)}" lang="{code}" hreflang="{code}"' + (' aria-current="page"' if code == lang else '') + f'>{label}</a></li>' for code, label in LANGUAGES.items())
    tabs = ''.join(f'<a href="{document_path(lang, value)}"' + (' aria-current="page"' if value == kind else '') + f'>{label}</a>' for value, label in [('privacy', policy), ('support', support)])
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
    expected = {(lang, kind) for lang in LANGUAGES for kind in ('privacy', 'support')}
    assert len(documents) == 12 and {(d['lang'], d['kind']) for d in documents} == expected
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
    print('12 documents: ' + ('up to date; original-text hashes verified' if '--check' in sys.argv else 'rendered'))


if __name__ == '__main__':
    main()

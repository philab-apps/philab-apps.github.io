#!/usr/bin/env python3
"""Render the two home-page app catalogs. No browser JavaScript or build service.

python3 scripts/render_apps.py          # update committed HTML
python3 scripts/render_apps.py --check  # fail if generated cards are stale
"""
import argparse
import html
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
START = '<!-- apps:generated:start -->'
END = '<!-- apps:generated:end -->'
HOMES = {'ko': 'index.html', 'en': 'en/index.html'}


def local_file(root, value, directory=False):
    if not isinstance(value, str) or not re.fullmatch(r'[a-zA-Z0-9_./-]+', value):
        raise ValueError(f'Expected a relative local path: {value!r}')
    if value.startswith('/') or '..' in value.split('/'):
        raise ValueError(f'Path must stay within the site: {value!r}')
    if directory and not value.endswith('/'):
        raise ValueError(f'Page path must end in /: {value}')
    target = root / value / 'index.html' if directory else root / value
    if not target.is_file():
        raise ValueError(f'Missing file: {target.relative_to(root)}')
    return target


def load_apps(root=ROOT):
    apps = json.loads((root / 'apps.json').read_text(encoding='utf-8'))['apps']
    if not isinstance(apps, list) or not apps:
        raise ValueError('apps must contain at least one published app')
    ids, paths = set(), set()
    for app in apps:
        slug = app['id']
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', slug) or slug in ids:
            raise ValueError(f'Invalid or duplicate app id: {slug}')
        ids.add(slug)
        local_file(root, app['icon'])
        for field in ('name', 'platform'):
            if not isinstance(app[field], str) or not app[field].strip():
                raise ValueError(f'{slug}: {field} must be non-empty text')
        for lang in HOMES:
            copy = app['locales'][lang]
            path = copy['path']
            if path in paths or not path.startswith(slug + '/'):
                raise ValueError(f'{slug}: duplicate or unrelated detail path: {path}')
            paths.add(path)
            target = local_file(root, path, directory=True)
            if not re.search(r'<html\s+lang=[\"\']' + re.escape(lang) + r'[\"\']', target.read_text(encoding='utf-8')):
                raise ValueError(f'{path}: page language must match {lang}')
            for field in ('subtitle', 'description'):
                if not isinstance(copy[field], str) or not copy[field].strip():
                    raise ValueError(f'{slug}/{lang}: {field} must be non-empty text')
            if not isinstance(copy['tags'], list) or not 1 <= len(copy['tags']) <= 3:
                raise ValueError(f'{slug}/{lang}: use one to three tags')
            if any(not isinstance(tag, str) or not tag.strip() for tag in copy['tags']):
                raise ValueError(f'{slug}/{lang}: tags must be non-empty text')
    return apps


def render(apps, lang):
    esc = html.escape
    prefix = '' if lang == 'ko' else '../'
    action = '앱 자세히 보기' if lang == 'ko' else 'Explore the app'
    cards = []
    for app in apps:
        copy = app['locales'][lang]
        tags = ''.join(f'<span>{esc(tag)}</span>' for tag in copy['tags'])
        cards.append(f'''  <li>
    <a class="app-card catalog-card" href="{esc(prefix + copy['path'])}" data-app="{esc(app['id'])}" aria-labelledby="app-{esc(app['id'])}-name app-{esc(app['id'])}-subtitle">
      <div class="catalog-art" aria-hidden="true"><span class="catalog-art-grid"></span><img src="{esc(prefix + app['icon'])}" width="128" height="128" alt=""><span class="catalog-art-label">{esc(app['name'])} / {esc(app['platform'])}</span></div>
      <div class="catalog-copy">
        <div class="app-card-top"><span>{esc(app['platform'])}</span><span class="card-arrow" aria-hidden="true">↗</span></div>
        <h3 class="app-name" id="app-{esc(app['id'])}-name">{esc(app['name'])}<span class="brand-dot" aria-hidden="true">.</span></h3>
        <p class="app-sub" id="app-{esc(app['id'])}-subtitle">{esc(copy['subtitle'])}</p>
        <p class="catalog-description">{esc(copy['description'])}</p>
        <div class="catalog-tags">{tags}</div>
        <span class="app-card-bottom">{action}<span aria-hidden="true">→</span></span>
      </div>
    </a>
  </li>''')
    return '<ul class="app-grid">\n' + '\n'.join(cards) + '\n</ul>'


def update(root=ROOT, check=False):
    apps = load_apps(root)
    pending = []
    for lang, path in HOMES.items():
        file = root / path
        current = file.read_text(encoding='utf-8')
        if current.count(START) != 1 or current.count(END) != 1:
            raise ValueError(f'{path}: expected one generated catalog block')
        before, rest = current.split(START)
        _, after = rest.split(END)
        desired = before + START + '\n' + render(apps, lang) + '\n' + END + after
        if current != desired:
            pending.append((file, desired))
    if check and pending:
        raise ValueError('Stale app cards. Run python3 scripts/render_apps.py')
    for file, desired in pending:
        file.write_text(desired, encoding='utf-8')
    return len(apps)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    try:
        count = update(check=args.check)
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.exit(1, f'Catalog error: {error}\n')
    print(f'{count} published app(s); both home catalogs are current.')

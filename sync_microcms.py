#!/usr/bin/env python3
"""Build CMS pages without changing the original hand-authored HTML templates."""
import datetime as dt
import html
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parent
SERVICE=os.getenv('MICROCMS_SERVICE_ID','yamada-lab-nara')
KEY=os.getenv('MICROCMS_API_KEY','')
CATEGORIES={'研究成果':'research','学会・研究発表':'research','受賞':'award','イベント・交流':'event','お知らせ':'event'}

def get_records(endpoint):
    if not KEY: raise RuntimeError('MICROCMS_API_KEY is missing; no CMS files were changed.')
    items=[]; offset=0
    while True:
        url=f'https://{SERVICE}.microcms.io/api/v1/{endpoint}?limit=100&offset={offset}'
        req=urllib.request.Request(url,headers={'X-MICROCMS-API-KEY':KEY})
        with urllib.request.urlopen(req,timeout=30) as resp: data=json.load(resp)
        batch=data.get('contents',[]);items.extend(batch)
        if not batch or len(items)>=data.get('totalCount',len(items)): break
        offset+=len(batch)
    return items

def safe_id(s):
    if not re.fullmatch(r'[A-Za-z0-9_-]+',str(s)):
        raise ValueError(f'Unsafe CMS content ID: {s!r}')
    return str(s)

def val(obj,key):return html.escape(str(obj.get(key) or ''),quote=True)

def image_url(obj):
    image=obj.get('thumbnail')
    if isinstance(image,dict):return image.get('url','')
    return ''

def img_tag(obj,cls='',prefix=''):
    url=image_url(obj)
    if not url:return ''
    if not url.startswith('https://'):return ''
    return f'<img class="{cls}" src="{html.escape(url,quote=True)}" alt="{val(obj,"title")}" loading="lazy">'

def date(obj):
    d=obj.get('date') or obj.get('publishedAt') or ''
    return str(d)[:10]

def date_label(obj):return date(obj).replace('-','.')

def soup_from_template(name):return BeautifulSoup((ROOT/'cms'/'templates'/name).read_text(encoding='utf-8'),'html.parser')

def add_fragment(soup, parent, markup, before=False):
    fragment=BeautifulSoup(markup,'html.parser')
    for node in list(fragment.contents):
        if before:parent.insert(0,node)
        else:parent.append(node)

def article_page(item,kind):
    ident=safe_id(item['id']); isnews=kind=='news'
    title=val(item,'title'); label='NEWS & TOPICS' if isnews else 'TECHNOLOGY SEEDS'
    back='news.html' if isnews else 'seeds.html'
    category=val(item,'category');summary=val(item,'summary')
    body=item.get('body') or ''
    # microCMS rich-editor content is HTML; strip scripts, inline event handlers and embeds.
    frag=BeautifulSoup(body,'html.parser')
    for tag in frag.find_all(['script','iframe','object','embed','form','style']):tag.decompose()
    for tag in frag.find_all(True):
        for attr in list(tag.attrs):
            if attr.lower().startswith('on') or attr.lower() in ('srcdoc','style'):del tag.attrs[attr]
        for attr in ('href','src'):
            if tag.has_attr(attr) and not (str(tag[attr]).startswith(('https://','http://','/','../','assets/','#'))):del tag[attr]
    parts=[f'<p class="eyebrow">{label}</p>',f'<h1>{title}</h1>']
    if isnews:parts.append(f'<p>{date_label(item)}　{category}</p>')
    if summary:parts.append(f'<p class="cms-summary">{summary}</p>')
    image=img_tag(item,'article-photo')
    if image:parts.append(image)
    parts.append(f'<div class="cms-rich-body">{frag}</div>')
    if not isnews:
        for field,caption in [('features','技術の特徴'),('applications','想定される用途')]:
            if item.get(field):parts.append(f'<h2>{caption}</h2><p>{val(item,field)}</p>')
        if item.get('references'):parts.append(f'<h2>関連論文・特許</h2>{item["references"]}')
        if item.get('documentUrl') and str(item['documentUrl']).startswith('https://'):
            parts.append(f'<p><a href="{val(item,"documentUrl")}" target="_blank" rel="noopener">関連資料を見る ↗</a></p>')
    else:
        if item.get('sourceUrl') and str(item['sourceUrl']).startswith('https://'):
            parts.append(f'<p><a href="{val(item,"sourceUrl")}" target="_blank" rel="noopener">掲載元：{val(item,"sourceName") or "元記事"} ↗</a></p>')
    parts.append(f'<p class="article-back"><a href="../{back}">← {"NEWS一覧" if isnews else "研究シーズ"}に戻る</a></p>')
    shell=''.join(parts)
    return f"""<!DOCTYPE html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} | 山田研究室</title><link rel="stylesheet" href="../assets/site.css"><link rel="stylesheet" href="../assets/redesign.css"><link rel="stylesheet" href="../assets/cms.css"></head><body><header class="site-header"><div class="head-inner"><a class="brand" href="../index.html"><span class="brand-text"><strong>奈良高専 山田研究室</strong><small>Yamada Laboratory | NARA KOSEN</small></span></a><button class="menu-toggle" id="menu-toggle" aria-label="メニューを開く">☰</button><nav class="nav" id="nav"><a href="../index.html">ホーム</a><a href="../research.html">研究紹介</a><a href="../seeds.html">研究シーズ</a><a href="../facilities.html">研究設備</a><a href="../members.html">メンバー</a><a href="../publications.html">論文・業績</a><a href="../news.html">ニュース</a><a href="../contact.html">お問い合わせ</a></nav></div></header><main><section class="page-banner"><div class="shell"><div class="breadcrumb"><a href="../index.html">TOP</a> / <a href="../{back}">{label}</a> / ARTICLE</div><p class="eyebrow">{label}</p><h1>{title}</h1></div></section><article class="section"><div class="shell article-shell">{shell}</div></article></main><footer class="site-footer"><div class="shell"><h2>YAMADA LABORATORY</h2><p>奈良工業高等専門学校 物質化学工学科</p><div class="footer-note">© 2026 Yamada Laboratory</div></div></footer><script src="../assets/site.js"></script></body></html>"""

def main():
    # Fetch all endpoints first: a failing API never partially changes the website.
    news=get_records('news'); seeds=get_records('seeds')
    news.sort(key=date,reverse=True)
    seeds.sort(key=lambda x:(int(x.get('sortOrder') or 9999),x.get('id','')))
    for endpoint,items in [('news',news),('seeds',seeds)]:
        for item in items:safe_id(item['id'])
    home=soup_from_template('index.html');archive=soup_from_template('news.html');seedspage=soup_from_template('seeds.html')
    for item in reversed(news):
        ident=safe_id(item['id']); url=f'news/{ident}.html'; title=val(item,'title')
        category=val(item,'category'); group=CATEGORIES.get(item.get('category'),'event')
        picture=img_tag(item)
        row=f'<a class="news-row" data-category="{group}" href="{url}">{picture}<time>{date_label(item)}</time><span class="tag">{category}</span><b>{title}</b><span class="arrow">↗</span></a>'
        parent=archive.select_one('.news-rows')
        if parent and not parent.select_one(f'a[href="{url}"]'):add_fragment(archive,parent,row,before=True)
        homeparent=home.select_one('.home-news-list')
        row=f'<a class="home-news-row" data-category="{group}" href="{url}">{picture}<time>{date_label(item)}</time><span class="news-pill">{category}</span><strong>{title}</strong><span aria-hidden="true" class="row-arrow">→</span></a>'
        if homeparent and not homeparent.select_one(f'a[href="{url}"]'):add_fragment(home,homeparent,row,before=True)
    for i,item in reversed(list(enumerate(seeds))):
        ident=safe_id(item['id']);url=f'seeds/{ident}.html';title=val(item,'title')
        picture=img_tag(item)
        card=f'<a class="seed-carousel-card" href="{url}"><div class="seed-carousel-photo">{picture}</div><div class="seed-carousel-copy"><span>{i+1:02d} / {val(item,"category")}</span><strong>{title}</strong><b aria-hidden="true">→</b></div></a>'
        rail=home.select_one('#seed-carousel')
        if rail and not rail.select_one(f'a[href="{url}"]'):add_fragment(home,rail,card,before=True)
        jump=seedspage.select_one('.seeds-jump')
        if jump:add_fragment(seedspage,jump,f'<a href="{url}"><span>CMS</span> {title} <span aria-hidden="true">↗</span></a>')
    for doc in (home,archive,seedspage):
        if doc.head:
            link=doc.new_tag('link',rel='stylesheet',href='assets/cms.css');doc.head.append(link)
    for name,doc in [('index.html',home),('news.html',archive),('seeds.html',seedspage)]:
        (ROOT/name).write_text(str(doc),encoding='utf-8')
    for endpoint,items in [('news',news),('seeds',seeds)]:
        directory=ROOT/endpoint;directory.mkdir(exist_ok=True)
        for item in items:
            path=directory/(safe_id(item['id'])+'.html')
            # Keep pre-existing, manually edited articles intact.
            if path.exists() and not path.read_text(encoding='utf-8').startswith('<!DOCTYPE html><!-- generated-by-microcms -->'):
                print('Skipping hand-authored page:',path);continue
            content=article_page(item,endpoint)
            path.write_text('<!DOCTYPE html><!-- generated-by-microcms -->'+content[len('<!DOCTYPE html>'):],encoding='utf-8')
    print(f'CMS build complete: {len(news)} news / {len(seeds)} seeds')

if __name__=='__main__':
    try:main()
    except (RuntimeError,urllib.error.HTTPError,urllib.error.URLError,ValueError) as exc:
        print(f'CMS update failed: {exc}',file=sys.stderr);sys.exit(1)

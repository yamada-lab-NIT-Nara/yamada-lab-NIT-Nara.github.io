from pathlib import Path
import json, os, urllib.request, urllib.parse, re, shutil
from datetime import datetime
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parent
T=ROOT/'cms'/'templates'

def get_items(api):
    fixture=os.environ.get('MICROCMS_FIXTURE_DIR')
    if fixture:
        return json.loads((Path(fixture)/(api+'.json')).read_text(encoding='utf8'))['contents']
    key=os.environ.get('MICROCMS_API_KEY')
    service=os.environ.get('MICROCMS_SERVICE_ID','yamada-lab-nara')
    if not key: raise RuntimeError('MICROCMS_API_KEY is not configured')
    all_items=[]; offset=0
    while True:
        url=f'https://{service}.microcms.io/api/v1/{api}?'+urllib.parse.urlencode({'limit':100,'offset':offset})
        req=urllib.request.Request(url,headers={'X-MICROCMS-API-KEY':key})
        with urllib.request.urlopen(req,timeout=25) as r: data=json.load(r)
        all_items+=data.get('contents',[])
        offset+=len(data.get('contents',[]))
        if offset>=data.get('totalCount',0) or not data.get('contents'):break
    return all_items

def soup(path): return BeautifulSoup(path.read_text(encoding='utf8'),'html.parser')
def write(path,html):path.parent.mkdir(parents=True,exist_ok=True);path.write_text('<!DOCTYPE html>\n'+str(html.html),encoding='utf8')
def img_url(item):
    x=item.get('thumbnail') or {}
    return x.get('url','') if isinstance(x,dict) else ''
def date(item):
    d=item.get('date') or item.get('publishedAt') or ''
    try:return datetime.fromisoformat(d.replace('Z','+00:00')).strftime('%Y.%m.%d')
    except ValueError:return d[:10]
def el(s,tag,cls=None,text=None,**attrs):
    t=s.new_tag(tag,**attrs)
    if cls:t['class']=cls.split()
    if text is not None:t.string=str(text)
    return t
def insert_html(target,html):
    frag=BeautifulSoup(html or '', 'html.parser')
    for node in list(frag.contents):target.append(node)
def cat_news(x):
    x=x or 'お知らせ'
    return ('research' if x in ('研究成果','学会・研究発表') else 'student' if x=='受賞' else 'event')
def safeid(x):
    if not re.fullmatch(r'[a-zA-Z0-9_-]+',x or ''):raise ValueError('Invalid microCMS content ID')
    return x

def build_news(news):
    home=soup(T/'index.html'); archive=soup(T/'news.html')
    rail=home.select_one('.home-news-list'); listing=archive.select_one('.news-rows')
    if not rail or not listing:raise RuntimeError('NEWS containers missing from templates')
    rail.clear();listing.clear()
    for item in sorted(news,key=lambda x:x.get('date') or x.get('publishedAt') or '',reverse=True):
        cid=safeid(item['id']); title=item.get('title') or '無題'; category=item.get('category') or 'お知らせ'; dt=date(item); url=f'news/{cid}.html'; photo=img_url(item)
        a=el(home,'a','home-news-row',href=url);a['data-category']=cat_news(category)
        if photo:a.append(el(home,'img',src=photo,alt=title,loading='lazy'))
        else:a.append(el(home,'span','cms-no-image'))
        a.append(el(home,'time',text=dt));a.append(el(home,'span','news-pill',category));a.append(el(home,'strong',text=title));a.append(el(home,'span','row-arrow','→'));rail.append(a)
        b=el(archive,'a','news-row',href=url);b['data-category']='award' if category=='受賞' else 'event'
        if photo:b.append(el(archive,'img',src=photo,alt=title,loading='lazy'))
        else:b.append(el(archive,'span','cms-no-image'))
        b.append(el(archive,'time',text=dt));b.append(el(archive,'span','tag',category));b.append(el(archive,'b',text=title));b.append(el(archive,'span','arrow','↗'));listing.append(b)
        detail=soup(T/'article.html');detail.title.string=f'{title} | 山田研究室'
        detail.select_one('.page-banner h1').string=category
        detail.select_one('.page-banner .shell > p:last-child').string=dt
        article=detail.select_one('article .article-shell');article.clear()
        article.append(el(detail,'time',text=dt));article.append(el(detail,'h2',text=title))
        if photo:article.append(el(detail,'img','article-photo',src=photo,alt=title,loading='lazy'))
        content=el(detail,'div','cms-richtext');insert_html(content,item.get('body',''));article.append(content)
        if item.get('sourceUrl'):
            p=el(detail,'p');a=el(detail,'a',text=item.get('sourceName') or '関連リンク',href=item['sourceUrl'],target='_blank',rel='noopener noreferrer');p.append(a);article.append(p)
        p=el(detail,'p');p.append(el(detail,'a',text='← NEWS一覧へ戻る',href='../news.html'));article.append(p)
        write(ROOT/url,detail)
    if not news:
        rail.append(el(home,'p',text='現在、公開中のお知らせはありません。'))
        listing.append(el(archive,'p',text='現在、公開中のお知らせはありません。'))
    for s in (home,archive):
        for note in s.select('.source-note,.news-preview-note'):note.decompose()
    write(ROOT/'index.html',home);write(ROOT/'news.html',archive)

def build_seeds(items):
    home=soup(ROOT/'index.html');page=soup(T/'seeds.html')
    rail=home.select_one('#seed-carousel'); jump=page.select_one('.seeds-jump')
    if not rail or not jump:raise RuntimeError('SEEDS containers missing from templates')
    rail.clear();jump.clear()
    for old in list(page.select('section.seeds-section')):old.decompose()
    anchor=page.select_one('section.seeds-contact-band')
    for i,item in enumerate(sorted(items,key=lambda x:(x.get('sortOrder') if isinstance(x.get('sortOrder'),(int,float)) else 9999,x.get('title',''))),1):
        cid=safeid(item['id']);title=item.get('title') or '無題';cat=item.get('category') or '研究シーズ';photo=img_url(item)
        url=f'seeds/{cid}.html'
        card=el(home,'a','seed-carousel-card',href=url)
        ph=el(home,'div','seed-carousel-photo')
        if photo:ph.append(el(home,'img',src=photo,alt=title,loading='lazy'))
        card.append(ph);copy=el(home,'div','seed-carousel-copy');copy.append(el(home,'span',text=f'{i:02d} / {cat}'));copy.append(el(home,'strong',text=title));copy.append(el(home,'b','', '→'));card.append(copy);rail.append(card)
        jump.append(el(page,'a',text=f'{i:02d}  {title}  ↗',href=url))
        section=el(page,'section','section seeds-section alt' if i%2 else 'section seeds-section')
        inner=el(page,'div','shell');head=el(page,'div','seeds-heading');h=el(page,'div');h.append(el(page,'span','seeds-eyebrow',f'{i:02d} · {cat}'));h.append(el(page,'h2',text=title));h.append(el(page,'p','seeds-subtitle',item.get('summary') or ''));head.append(h);head.append(el(page,'a','seeds-small-link','詳細を見る →',href=url));inner.append(head)
        section.append(inner);anchor.insert_before(section)
        detail=soup(T/'seed-detail.html');detail.title.string=f'{title} | 研究シーズ | 山田研究室';detail.select_one('.page-banner h1').string=title
        body=detail.select_one('.cms-seed-detail');body.clear()
        if photo:body.append(el(detail,'img','cms-seed-image',src=photo,alt=title,loading='lazy'))
        body.append(el(detail,'p','seeds-subtitle',item.get('summary') or ''))
        for field,heading in [('body','技術概要'),('features','技術の特徴'),('applications','応用分野'),('references','関連資料・文献')]:
            if item.get(field):
                body.append(el(detail,'h2',text=heading));block=el(detail,'div','cms-richtext');insert_html(block,item[field]);body.append(block)
        if item.get('documentUrl'):
            p=el(detail,'p');p.append(el(detail,'a','seeds-cta','研究シーズ資料を見る ↗',href=item['documentUrl'],target='_blank',rel='noopener noreferrer'));body.append(p)
        body.append(el(detail,'p'));body.append(el(detail,'a',text='← 研究シーズ一覧へ戻る',href='../seeds.html'))
        write(ROOT/url,detail)
    if not items:
        rail.append(el(home,'p',text='研究シーズは準備中です。'))
        jump.append(el(page,'p',text='研究シーズは準備中です。'))
    write(ROOT/'index.html',home);write(ROOT/'seeds.html',page)



def member_photo(item):
    image=item.get('photo') or {}
    return image.get('url','') if isinstance(image,dict) else ''

def build_members(items):
    page=soup(T/'members.html')
    section=page.select_one('#members .shell')
    if section is None:raise RuntimeError('MEMBERS section missing from template')
    section.clear()
    section.append(el(page,'p','eyebrow','People'))
    section.append(el(page,'h2',text='研究室メンバー'))
    people=sorted(items,key=lambda x:(x.get('sortOrder') if isinstance(x.get('sortOrder'),(int,float)) else 9999,x.get('name','')))
    faculty=[p for p in people if p.get('category')=='教員']
    students=[p for p in people if p.get('category')=='学生']
    others=[p for p in people if p.get('category') not in ('教員','学生')]
    for heading,group in [('教員',faculty),('学生',students),('その他',others)]:
        if not group:continue
        section.append(el(page,'h3','cms-member-group-title',heading))
        grid=el(page,'div','cms-member-grid');section.append(grid)
        for p in group:
            cid=safeid(p['id']);name=p.get('name') or '氏名未登録'
            is_faculty=p.get('category')=='教員'
            card=el(page,'a' if is_faculty else 'div','cms-member-card',**({'href':f'members/{cid}.html'} if is_faculty else {}))
            photo=member_photo(p)
            if photo:card.append(el(page,'img','cms-member-photo',src=photo,alt=name,loading='lazy'))
            info=el(page,'div','cms-member-info');info.append(el(page,'strong',text=name))
            if p.get('nameEn'):info.append(el(page,'span','cms-member-en',p['nameEn']))
            if p.get('position'):info.append(el(page,'span',text=p['position']))
            if p.get('academicYear') and not is_faculty:info.append(el(page,'small',text=f"{p['academicYear']}年度"))
            if is_faculty:info.append(el(page,'small',text='プロフィールを見る →'))
            card.append(info);grid.append(card)
            if not is_faculty:continue
            detail=soup(T/'member-detail.html')
            detail.title.string=f'{name} | メンバー | 山田研究室'
            detail.select_one('.page-banner h1').string=name
            subtitle=detail.select_one('.page-banner .shell > p:last-child')
            subtitle.string=' / '.join(filter(None,[p.get('nameEn'),p.get('position')]))
            body=detail.select_one('.cms-member-detail');body.clear()
            if photo:body.append(el(detail,'img','cms-member-portrait',src=photo,alt=name,loading='lazy'))
            for field,label in [('degree','学位'),('affiliation','所属'),('researchTheme','研究テーマ'),('profile','プロフィール'),('career','学歴・職歴'),('awards','受賞歴'),('societies','所属学会')]:
                val=p.get(field)
                if not val:continue
                body.append(el(detail,'h2',text=label))
                if field in ('profile','career','awards'):
                    div=el(detail,'div','cms-richtext');insert_html(div,val);body.append(div)
                else:body.append(el(detail,'p',text=str(val)))
            links=[('researchmapUrl','researchmap'),('orcidUrl','ORCID'),('externalUrl','外部リンク')]
            if any(p.get(k) for k,_ in links):
                body.append(el(detail,'h2',text='関連リンク'))
                for field,label in links:
                    if p.get(field):
                        line=el(detail,'p');line.append(el(detail,'a',text=label+' ↗',href=p[field],target='_blank',rel='noopener noreferrer'));body.append(line)
            if p.get('email'):
                body.append(el(detail,'h2',text='連絡先'))
                body.append(el(detail,'p',text=p['email']))
            back=el(detail,'p');back.append(el(detail,'a',text='← メンバー一覧へ戻る',href='../members.html'));body.append(back)
            write(ROOT/'members'/f'{cid}.html',detail)
    if not people:section.append(el(page,'p',text='メンバー情報は準備中です。'))
    write(ROOT/'members.html',page)

def main():
    # Fetch everything before touching the output; failures preserve the published HTML.
    news=get_items('news');seeds=get_items('seeds');members=get_items('members')
    print(f'microCMS API fetch successful: news={len(news)}, seeds={len(seeds)}, members={len(members)}',flush=True)
    for x in news+seeds+members:safeid(x['id'])
    build_news(news);build_seeds(seeds);build_members(members)
    print('Generated CMS pages successfully')
if __name__=='__main__':main()

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
def category_text(x, default=''):
    if isinstance(x, list):
        return '・'.join(str(v) for v in x if v is not None) or default
    if isinstance(x, dict):
        return str(x.get('name') or x.get('value') or x.get('id') or default)
    return str(x) if x is not None else default

# Category values are the explicit microCMS select labels, not keywords in headlines.
# A multi-select value can contain several labels; some older labels also join
# independent categories with Japanese middle dots.
NEWS_CATEGORY_MAP = {
    'イベント': {'event'}, '交流': {'event'}, 'イベント・交流': {'event'},
    '研究成果': {'research'}, '研究': {'research'},
    '設備': {'research'}, '研究設備': {'research'},
    '学会': {'research'}, '研究発表': {'research'}, '学会発表': {'research'},
    '受賞': {'award'}, '表彰': {'award'},
    'お知らせ': set(),
}

def news_categories(raw):
    if isinstance(raw, list):
        labels = [category_text(v).strip() for v in raw]
    else:
        labels = [category_text(raw).strip()]
    groups = set()
    for label in labels:
        # Split compound labels such as イベント・交流・研究成果.
        for part in re.split(r'[・／/,、\s]+', label):
            if part:
                groups.update(NEWS_CATEGORY_MAP.get(part, set()))
    return groups

def cat_news(raw):
    groups = news_categories(raw)
    return ' '.join(g for g in ('event','research','award') if g in groups)

def news_archive_categories(raw):
    groups = news_categories(raw)
    # Archive combines awards and research results in one tab.
    return ' '.join(g for g in ('event','award') if g in groups or (g == 'award' and 'research' in groups))

def safeid(x):
    if not re.fullmatch(r'[a-zA-Z0-9_-]+',x or ''):raise ValueError('Invalid microCMS content ID')
    return x

def build_news(news):
    home=soup(T/'index.html'); archive=soup(T/'news.html')
    rail=home.select_one('.home-news-list'); listing=archive.select_one('.news-rows')
    if not rail or not listing:raise RuntimeError('NEWS containers missing from templates')
    rail.clear();listing.clear()
    for item in sorted(news,key=lambda x:x.get('date') or x.get('publishedAt') or '',reverse=True):
        cid=safeid(item['id']); title=item.get('title') or '無題'; category=category_text(item.get('category'),'お知らせ'); dt=date(item); url=f'news/{cid}.html'; photo=img_url(item)
        a=el(home,'a','home-news-row',href=url);a['data-category']=cat_news(item.get('category'))
        if photo:a.append(el(home,'img',src=photo,alt=title,loading='lazy'))
        else:a.append(el(home,'span','cms-no-image'))
        a.append(el(home,'time',text=dt));a.append(el(home,'span','news-pill',category));a.append(el(home,'strong',text=title));a.append(el(home,'span','row-arrow','→'));rail.append(a)
        b=el(archive,'a','news-row',href=url);b['data-category']=news_archive_categories(item.get('category'))
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
        cid=safeid(item['id']);title=item.get('title') or '無題';cat=category_text(item.get('category'),'研究シーズ');photo=img_url(item)
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
    section['class']=['shell','cms-members-shell']
    section.clear()
    section.append(el(page,'p','eyebrow','People'))
    section.append(el(page,'h2',text='研究室メンバー'))
    section.append(el(page,'p','cms-members-lead',text='教員・学生の研究活動を紹介します。教員の経歴や研究分野はプロフィールからご覧いただけます。'))
    people=sorted(items,key=lambda x:(x.get('sortOrder') if isinstance(x.get('sortOrder'),(int,float)) else 9999,x.get('name','')))
    faculty=[p for p in people if '教員' in category_text(p.get('category')).split('・')]
    students=[p for p in people if '学生' in category_text(p.get('category')).split('・')]
    others=[p for p in people if not any(v in category_text(p.get('category')).split('・') for v in ('教員','学生'))]
    student_years=sorted({str(x.get('academicYear')) for x in students if x.get('academicYear') is not None},reverse=True)
    groups=[('教員',faculty)]
    if student_years:
        for year in student_years:
            groups.append((f'{year}年度', [x for x in students if str(x.get('academicYear'))==year]))
        ungrouped=[x for x in students if x.get('academicYear') is None]
        if ungrouped:groups.append(('学生（年度未設定）',ungrouped))
    else:groups.append(('学生',students))
    groups.append(('その他',others))
    for heading,group in groups:
        if not group:continue
        faculty_group=heading=='教員'
        wrapper=el(page,'div','cms-member-section')
        wrapper.append(el(page,'h3','cms-member-group-title',heading))
        if not faculty_group and heading != 'その他':
            # Student records are displayed as a compact, accessible year-based table.
            # position is the existing CMS field for the academic level.
            def student_level(p):
                value=str(p.get('position') or '').replace(' ', '').replace('　', '')
                if '専攻科' in value or 'Advanced' in value:
                    match=re.search(r'[12１２]',value)
                    return (0, -(int(match.group().translate(str.maketrans('１２','12'))) if match else 0))
                if '本科' in value or '学科' in value or '年' in value:
                    match=re.search(r'[1-5１-５]',value)
                    return (1, -(int(match.group().translate(str.maketrans('１２３４５','12345'))) if match else 0))
                return (2, 0)
            table=el(page,'table','cms-student-table')
            table.append(el(page,'caption','cms-student-table-caption',heading+'の学生一覧'))
            thead=el(page,'thead');tr=el(page,'tr')
            for title in ('学年','氏名','英語表記'):tr.append(el(page,'th',text=title,scope='col'))
            thead.append(tr);table.append(thead)
            tbody=el(page,'tbody')
            for p in sorted(group,key=lambda x:(student_level(x),x.get('sortOrder') if isinstance(x.get('sortOrder'),(int,float)) else 9999,x.get('name') or '')):
                tr=el(page,'tr')
                tr.append(el(page,'td','cms-student-level',p.get('position') or '—'))
                tr.append(el(page,'td','cms-student-name',p.get('name') or '氏名未登録'))
                tr.append(el(page,'td','cms-student-en',p.get('nameEn') or '—'))
                tbody.append(tr)
            table.append(tbody);wrapper.append(table);section.append(wrapper)
            continue
        grid=el(page,'div','cms-member-grid cms-faculty-grid' if faculty_group else 'cms-member-grid cms-student-grid')
        wrapper.append(grid);section.append(wrapper)
        for p in group:
            cid=safeid(p['id']);name=p.get('name') or '氏名未登録'
            is_faculty='教員' in category_text(p.get('category')).split('・')
            card=el(page,'a' if is_faculty else 'div','cms-member-card cms-faculty-card' if is_faculty else 'cms-member-card cms-student-card',**({'href':f'members/{cid}.html'} if is_faculty else {}))
            photo=member_photo(p)
            visual=el(page,'div','cms-member-photo-wrap')
            if photo:visual.append(el(page,'img','cms-member-photo',src=photo,alt=name,loading='lazy'))
            else:visual.append(el(page,'span','cms-member-photo-placeholder','MEMBER'))
            card.append(visual)
            info=el(page,'div','cms-member-info')
            if is_faculty:info.append(el(page,'span','cms-member-label','FACULTY / 教員'))
            if p.get('position'):info.append(el(page,'span','cms-member-position',p['position']))
            info.append(el(page,'strong',text=name))
            if p.get('nameEn'):info.append(el(page,'span','cms-member-en',p['nameEn']))
            if is_faculty:
                if p.get('affiliation'):info.append(el(page,'span','cms-member-affiliation',p['affiliation']))
                if p.get('researchTheme'):info.append(el(page,'p','cms-member-research',p['researchTheme']))
                info.append(el(page,'span','cms-member-more','プロフィールを見る →'))
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

def facility_photo(item):
    x=item.get('photo') or {}
    return x.get('url','') if isinstance(x,dict) else ''

def facility_summary(item):
    raw=item.get('description') or ''
    if not isinstance(raw,str):return ''
    return BeautifulSoup(raw,'html.parser').get_text(' ',strip=True)

def facility_tags(item):
    raw=item.get('applications') or ''
    if not isinstance(raw,str):return []
    return [v.strip(' ・\t\u3000') for v in re.split(r'[\n\r]+|(?<!\S)[・●•](?=\s|\S)',raw) if v.strip(' ・\t\u3000')]

# Use a small, consistent set of display groups instead of creating one section
# for each microCMS label. The original microCMS category remains on each card.
FACILITY_GROUP_ORDER = (
    '表面・形態観察',
    '組成・構造分析',
    '電気化学測定・評価',
    '材料合成・試料調製',
    'その他の研究設備',
)

def facility_group(item):
    category = category_text(item.get('category')).strip()
    name = str(item.get('name') or '')
    combined = (category + ' ' + name).lower()
    # Explicit device names take precedence over generic CMS labels.
    if any(x in combined for x in ('電気化学', 'ポテンショ', '充放電', 'インピーダンス', '燃料電池', 'サイクリックボルタン', 'tdgsc', 'potentiostat', 'galvanostat', 'battery cycler', 'electrochemical')):
        return '電気化学測定・評価'
    if any(x in combined for x in ('合成', '調製', '乾燥', '熱処理', '焼成', '炉', 'グローブボックス', '撹拌', '蒸着', 'スピンコート', '成膜', '電気炉', 'vacuum oven', 'furnace', 'glovebox')):
        return '材料合成・試料調製'
    if any(x in combined for x in ('xps', 'xrd', 'eds', 'edx', '蛍光x線', '回折', '分光', '組成', '結晶構造', 'x線光電子', 'x線回折', 'ftir', 'raman', 'ラマン', '赤外', '元素分析', '熱分析', 'tg-dsc', 'tg/dsc', 'tgdsc', 'dsc')):
        return '組成・構造分析'
    if any(x in combined for x in ('sem', 'spm', 'afm', '顕微鏡', '表面観察', '形態観察', '走査型', '電子顕微鏡', 'microscop')):
        return '表面・形態観察'
    if any(x in combined for x in ('評価', '測定')):
        return '電気化学測定・評価' if '電極' in combined else 'その他の研究設備'
    return 'その他の研究設備'

def build_facilities(items):
    home=soup(ROOT/'index.html')
    page=soup(T/'facilities.html')
    rail=home.select_one('.facility-column')
    grid=page.select_one('.equipment-grid')
    if rail is None or grid is None:raise RuntimeError('FACILITIES containers missing')
    items=sorted(items,key=lambda x:(x.get('sortOrder') if isinstance(x.get('sortOrder'),(int,float)) else 9999,x.get('name') or ''))

    # CMS is the single source of truth for instrument cards.
    # The original HTML is retained as a layout template, not as instrument data.
    grid.clear()
    grouped = {}
    for item in items:
        grouped.setdefault(facility_group(item), []).append(item)
    sequence = 0
    for group_name in FACILITY_GROUP_ORDER:
        group_items = grouped.get(group_name, [])
        if not group_items:
            continue
        section = el(page,'section','cms-equipment-group')
        heading = el(page,'h3','cms-equipment-group-title',group_name)
        section.append(heading)
        cards = el(page,'div','cms-equipment-group-grid')
        section.append(cards)
        grid.append(section)
        for item in group_items:
            sequence += 1
            i = sequence
            cid=safeid(item['id'])
            name=item.get('name') or '名称未設定'
            photo=facility_photo(item)
            card=el(page,'article','equipment-card cms-equipment-card',id='facility-'+cid)
            cat=category_text(item.get('category'),'RESEARCH FACILITY')
            card.append(el(page,'span','equipment-index',f'{i:02d} / {cat}'))
            card.append(el(page,'h3',text=name))
            if photo:
                card.append(el(page,'img','equipment-actual-photo',src=photo,alt=name+' 実機写真',loading='lazy'))
            if item.get('nameEn'):
                card.append(el(page,'p','cms-equipment-en',item['nameEn']))
            spec=' / '.join(str(v) for v in (item.get('manufacturer'),item.get('model')) if v)
            if spec:card.append(el(page,'p','cms-equipment-spec',spec))
            if item.get('description'):
                desc=el(page,'div','cms-richtext cms-equipment-description')
                insert_html(desc,item['description']);card.append(desc)
            tags=facility_tags(item)
            if tags:
                wrap=el(page,'ul','cms-equipment-applications')
                for tag in tags:wrap.append(el(page,'li',text=tag))
                card.append(wrap)
            cards.append(card)
    if not items:
        grid.append(el(page,'p','cms-facilities-empty','研究設備情報は準備中です。'))

    # The home feature retains its original 248px image slot and the existing
    # button/gallery. Only the photo/title/description become rotating CMS data.
    featured=[x for x in items if x.get('showOnHome') is True]
    if featured:
        original_image=rail.select_one('.facility-image')
        if original_image is None:raise RuntimeError('Home facility image missing')
        original_title=rail.find('h3',recursive=False)
        original_description=rail.find('p',recursive=False)
        slider=el(home,'div','cms-facility-slider')
        slider['aria-label']='主要研究設備スライダー'
        slides=el(home,'div','cms-facility-slides')
        for i,item in enumerate(featured):
            cid=safeid(item['id']);name=item.get('name') or '研究設備'
            card=el(home,'a','cms-facility-slide'+(' is-active' if i==0 else ''),href='facilities.html#facility-'+cid)
            card['aria-hidden']='false' if i==0 else 'true'
            photo=facility_photo(item)
            if photo:card.append(el(home,'img','cms-facility-slide-photo',src=photo,alt=name,loading='lazy'))
            else:card.append(el(home,'div','cms-facility-no-photo','RESEARCH FACILITIES'))
            card.append(el(home,'h3','cms-facility-slide-title',name))
            description=facility_summary(item)
            if description:card.append(el(home,'p','cms-facility-slide-description',description[:90]+('…' if len(description)>90 else '')))
            slides.append(card)
        slider.append(slides)
        if len(featured)>1:
            controls=el(home,'div','cms-facility-controls')
            controls.append(el(home,'button','cms-facility-prev','‹',type='button',**{'aria-label':'前の設備'}))
            dots=el(home,'div','cms-facility-dots')
            for i in range(len(featured)):
                dot=el(home,'button','cms-facility-dot'+(' is-active' if i==0 else ''),type='button',**{'aria-label':f'{i+1}番目の設備を表示'})
                dot['data-index']=str(i);dots.append(dot)
            controls.append(dots)
            controls.append(el(home,'button','cms-facility-next','›',type='button',**{'aria-label':'次の設備'}))
            slider.append(controls)
        original_image.replace_with(slider)
        if original_title:original_title.decompose()
        if original_description:original_description.decompose()
    # With no featured CMS items, leave the original FE-SEM feature unchanged.
    write(ROOT/'index.html',home)
    write(ROOT/'facilities.html',page)

def main():
    # Fetch everything before touching the output; failures preserve the published HTML.
    news=get_items('news');seeds=get_items('seeds');members=get_items('members');facilities=get_items('facilities')
    print(f'microCMS API fetch successful: news={len(news)}, seeds={len(seeds)}, members={len(members)}, facilities={len(facilities)}',flush=True)
    for x in news+seeds+members+facilities:safeid(x['id'])
    build_news(news);build_seeds(seeds);build_members(members);build_facilities(facilities)
    print('Generated CMS pages successfully')
if __name__=='__main__':main()

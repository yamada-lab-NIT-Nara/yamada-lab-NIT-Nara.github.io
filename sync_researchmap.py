#!/usr/bin/env python3
"""Sync *public* researchmap achievements after JST API permission is obtained.

Requires RESEARCHMAP_API_TOKEN if API credentials are issued; API access approval
must be secured before enabling the scheduled workflow. Never expose tokens in HTML.
"""
import json, os, urllib.parse, urllib.request, datetime, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parent
PERMALINK = 'read0151252'
CATEGORIES = {'published_papers':'publications','presentations':'presentations','awards':'awards'}
OUT = ROOT/'data'/'researchmap.json'

def request(category):
    url = f'https://api.researchmap.jp/{PERMALINK}/{category}?limit=100'
    headers={'Accept':'application/json','User-Agent':'YamadaLabWebsite/1.0 (researchmap permitted integration)'}
    token=os.getenv('RESEARCHMAP_API_TOKEN','').strip()
    if token: headers['Authorization']='Bearer '+token
    with urllib.request.urlopen(urllib.request.Request(url,headers=headers), timeout=25) as resp:
        return json.load(resp)

def items_from(data):
    if isinstance(data,list): return data
    if isinstance(data,dict):
        for k in ('items','results','data','list'):
            if isinstance(data.get(k),list): return data[k]
    raise ValueError('Unexpected API response shape; inspect response and adjust before publishing')

def localized(v):
    if isinstance(v,str):return v
    if isinstance(v,dict):
        for lang in ('en','ja'):
            if isinstance(v.get(lang),str) and v[lang]:return v[lang]
        for val in v.values():
            if isinstance(val,str) and val:return val
    return ''

def sanitize(raw):
    if not isinstance(raw,dict):return None
    title=localized(raw.get('paper_title') or raw.get('presentation_title') or raw.get('title') or raw.get('award_title'))
    if not title:return None
    date=str(raw.get('publication_date') or raw.get('presentation_date') or raw.get('award_date') or raw.get('from_date') or '')[:10]
    year=date[:4] if len(date)>=4 and date[:4].isdigit() else ''
    doi=raw.get('doi','')
    if isinstance(doi,dict):doi=localized(doi)
    doi=str(doi or '').removeprefix('https://doi.org/').strip()
    if doi and not doi.startswith('10.'):doi=''
    # allow only known source links, no javascript/foreign URL injected into output
    url='https://doi.org/'+urllib.parse.quote(doi,safe='/._-') if doi else f'https://researchmap.jp/{PERMALINK}'
    journal=localized(raw.get('publication_name') or raw.get('journal_name') or raw.get('publisher') or raw.get('conference_name') or raw.get('award_organization'))
    return {'title':title[:650],'year':year,'date':date,'venue':journal[:350],'url':url}

def main():
    if os.getenv('RESEARCHMAP_API_APPROVED','').lower()!='true':
        print('API access not yet approved: leaving existing website data unchanged.')
        return
    result={'source':f'https://researchmap.jp/{PERMALINK}', 'updated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(), 'categories':{}}
    for typ,key in CATEGORIES.items():
        raw=items_from(request(typ))
        result['categories'][key]=[row for row in (sanitize(x) for x in raw) if row]
        print(key, len(result['categories'][key]))
    OUT.parent.mkdir(exist_ok=True)
    tmp=OUT.with_suffix('.tmp')
    tmp.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    tmp.replace(OUT)
if __name__=='__main__':
    try: main()
    except Exception as e:
        print(f'Sync failed; retaining last successful data: {e}',file=sys.stderr)
        sys.exit(1)

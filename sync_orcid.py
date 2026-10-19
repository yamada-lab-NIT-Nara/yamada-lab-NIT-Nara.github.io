"""Refresh the site's public journal-article list from ORCID's authenticated Public API.

Fail closed: no credentials or no valid journal articles means no file changes.
"""
import datetime as dt
import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path

ORCID_ID = '0000-0003-0958-1529'
OUTPUT = Path(__file__).resolve().parent / 'data' / 'orcid.json'
API = f'https://pub.orcid.org/v3.0/{ORCID_ID}/works'
FUNDING_API = f'https://pub.orcid.org/v3.0/{ORCID_ID}/fundings'
FUNDING_OUTPUT = OUTPUT.parent / 'funding.json'


def request(url, *, form=None, token=None):
    headers = {'Accept': 'application/json', 'User-Agent': 'YamadaLaboratoryWebsite/1.0 (academic publications sync)'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    body = urllib.parse.urlencode(form).encode() if form else None
    with urllib.request.urlopen(urllib.request.Request(url, data=body, headers=headers), timeout=30) as reply:
        return json.load(reply)


def year_for(item):
    value = (item.get('publication-date') or {}).get('year') or {}
    s = value.get('value') or ''
    return int(s) if re.fullmatch(r'\d{4}', s) else 0


def get_doi(item):
    for record in (item.get('external-ids') or {}).get('external-id', []):
        if (record.get('external-id-type') or '').lower() == 'doi':
            value = (record.get('external-id-value') or '').strip()
            if value:
                return value.removeprefix('https://doi.org/').removeprefix('http://doi.org/')
    return None


def funding_year(item, key):
    value = ((item.get(key) or {}).get('year') or {}).get('value')
    return str(value) if value and re.fullmatch(r'\d{4}', str(value)) else ''


def funding_records(payload):
    """Normalize ORCID public funding summaries; never infer award amounts or roles."""
    records = {}
    for group in payload.get('group', []):
        for item in group.get('funding-summary', []):
            title = (((item.get('title') or {}).get('title') or {}).get('value') or '').strip()
            if not title:
                continue
            org = ((item.get('organization') or {}).get('name') or '').strip()
            start = funding_year(item, 'start-date')
            end = funding_year(item, 'end-date')
            ids = []
            for identifier in ((item.get('external-ids') or {}).get('external-id') or []):
                kind = (identifier.get('external-id-type') or '').strip()
                value = (identifier.get('external-id-value') or '').strip()
                if kind and value:
                    ids.append({'type': kind, 'value': value})
            link = ((item.get('url') or {}).get('value') or '').strip()
            if not link.startswith(('https://', 'http://')):
                link = ''
            key = (title.casefold(), org.casefold(), start)
            record = {'title': title, 'organization': org, 'start_year': start,
                      'end_year': end, 'type': item.get('type') or '',
                      'identifiers': ids, 'url': link}
            if key not in records or len(ids) > len(records[key]['identifiers']):
                records[key] = record
    return sorted(records.values(), key=lambda r: (r['start_year'], r['title']), reverse=True)


def sync_funding(token):
    """Failure must never delete previously fetched funding data."""
    try:
        payload = request(FUNDING_API, token=token)
        records = funding_records(payload)
        if not records:
            print('No public ORCID funding records found; retaining previous funding data.')
            return
        result = {'source': f'https://orcid.org/{ORCID_ID}',
                  'updated_at': dt.datetime.now(dt.timezone.utc).isoformat(),
                  'funding': records}
        FUNDING_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        FUNDING_OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(f'Saved {len(records)} public ORCID funding records.')
    except Exception as exc:
        print(f'ORCID funding sync unavailable; retaining previous data: {exc}')


def main():
    client_id = os.getenv('ORCID_CLIENT_ID')
    secret = os.getenv('ORCID_CLIENT_SECRET')
    if not client_id or not secret:
        print('No ORCID API credentials; retaining current publication data.')
        return
    credentials = request('https://orcid.org/oauth/token', form={
        'client_id': client_id, 'client_secret': secret,
        'grant_type': 'client_credentials', 'scope': '/read-public'
    })
    sync_funding(credentials['access_token'])
    works = request(API, token=credentials['access_token'])
    journal_types = {'journal-article'}
    entries = {}
    for group in works.get('group', []):
        summaries = [s for s in group.get('work-summary', []) if s.get('publication-type') in journal_types]
        # The actual ORCID works response uses 'publication-type' as 'publication-type' or 'external type'? 
        summaries = summaries or [s for s in group.get('work-summary', []) if s.get('type') in journal_types]
        if not summaries:
            continue
        summary = sorted(summaries, key=lambda s: (bool(get_doi(s)), year_for(s)), reverse=True)[0]
        title = ((summary.get('title') or {}).get('title') or {}).get('value', '').strip()
        doi = get_doi(summary)
        if not title or not doi:
            continue  # Show only DOI-backed published journal articles
        norm = doi.lower().strip()
        url = 'https://doi.org/' + urllib.parse.quote(doi, safe='/._-;()')
        entries[norm] = {'title': title, 'year': year_for(summary) or None,
                         'venue': (summary.get('journal-title') or {}).get('value') or 'Journal article',
                         'url': url, 'doi': doi}
    if not entries:
        print('No verified DOI-backed journal articles found; retaining previous data.')
        return
    records = sorted(entries.values(), key=lambda x: (x['year'] or 0, x['title']), reverse=True)
    payload = {'source': f'https://orcid.org/{ORCID_ID}',
               'updated_at': dt.datetime.now(dt.timezone.utc).isoformat(),
               'publications': records}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Saved {len(records)} public DOI-backed journal articles.')

if __name__ == '__main__':
    main()

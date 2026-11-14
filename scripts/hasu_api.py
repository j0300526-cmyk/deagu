"""Collect official Hasu XML server-side without logging credentials or request URLs."""
from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
import os
from pathlib import Path
import re
import xml.etree.ElementTree as ET

import requests

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data/raw/hasu_api'
ENDPOINT='https://apis.data.go.kr/B554808/Hasu/svHasu'


def credential():
    value=os.environ.get('HASU_SERVICE_KEY','').strip()
    if not value:
        p=ROOT/'.env.local'
        if p.exists():
            for line in p.read_text(encoding='utf-8-sig').splitlines():
                if line.startswith('HASU_SERVICE_KEY='):
                    value=line.split('=',1)[1].strip().strip('"\'')
    if not value: raise RuntimeError('HASU_SERVICE_KEY is not configured locally')
    return value


def schema():
    text=(ROOT/'data/raw/hasu_portal.html').read_text(encoding='utf-8')
    match=re.search(r'const swaggerJson = `(.*?)`;',text,re.S)
    if not match: raise RuntimeError('Official Swagger schema missing')
    spec=json.loads(match.group(1))
    RAW.mkdir(parents=True,exist_ok=True)
    (RAW/'swagger.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf-8')
    return spec


def request(day: str, page: int=1, rows: int=1000, refresh: bool=False):
    date.fromisoformat(day)
    key=credential()
    RAW.mkdir(parents=True,exist_ok=True)
    path=RAW/f'{day}_page{page}.xml'
    params={'ymd':day,'pageNo':page,'numOfRows':rows}
    if path.exists() and not refresh:
        content=path.read_bytes();status=200;cached=True
    else:
        try:
            response=requests.get(ENDPOINT,params={**params,'serviceKey':key},timeout=(15,65))
        except requests.RequestException as error:
            # requests exception strings include the credential-bearing URL; do not emit them.
            return {'date':day,'page':page,'error':type(error).__name__},[]
        status=response.status_code;content=response.content;cached=False
        if key.encode() in content: return {'date':day,'page':page,'error':'credential_reflection_not_saved'},[]
    record={'date':day,'page':page,'http_status':status,'cached':cached,'bytes':len(content),
            'sha256':hashlib.sha256(content).hexdigest(),'endpoint':ENDPOINT,'params':params}
    try: root=ET.fromstring(content)
    except ET.ParseError:
        record['error']='non_xml_response';return record,[]
    def field(name):
        node=root.find('.//'+name)
        return node.text.strip() if node is not None and node.text else None
    record.update({name:field(name) for name in ['resultCode','resultMsg','totalCount','numOfRows','pageNo','returnAuthMsg','errMsg']})
    items=[{child.tag:child.text for child in item} for item in root.findall('.//item')]
    record['items_n']=len(items)
    record['fields']=sorted({key for item in items for key in item})
    if not cached and status==200 and record['resultCode']=='00':
        # Cache only complete, parseable success responses. A failed API response must be retryable.
        path.write_bytes(content)
    return record,items


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--dates',nargs='+',default=['2025-01-01','2025-12-31','2026-11-12'])
    parser.add_argument('--schema',action='store_true')
    args=parser.parse_args()
    if args.schema:
        spec=schema()
        print('OPERATIONS',list(spec['paths']))
        op=spec['paths']['/svHasu']['get']
        print('FIELDS',json.dumps(op['responses']['200']['schema'],ensure_ascii=False,indent=2))
    records=[]
    for day in args.dates:
        record,items=request(day)
        records.append(record)
        print(json.dumps(record,ensure_ascii=False))
        if items: print('ITEM_SAMPLE',json.dumps(items[:2],ensure_ascii=False))
    (RAW/'probe_metadata.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')

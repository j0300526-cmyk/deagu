"""Collect one calendar year of official records, accounting for query/operation-day offset."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
import json
import logging

from hasu_api import RAW, request


def collect(year: int, workers: int=3):
    logger=logging.getLogger('hasu.collect')
    start,end=date(year,1,1),date(year,12,31)
    # Probed official responses report opdate=ymd-1 day. Actual opdate is still checked downstream.
    days=[start+timedelta(days=i+1) for i in range((end-start).days+1)]
    metadata=[]
    def fetch(day):
        record,items=request(day.isoformat())
        total=int(record.get('totalCount') or 0)
        if total>len(items):
            for page in range(2,(total+999)//1000+1):
                extra,more=request(day.isoformat(),page=page)
                if extra.get('resultCode')!='00':record['pagination_error']=True
                items.extend(more)
        record['operation_dates']=sorted({x.get('opdate','') for x in items})
        record['complete']=record.get('resultCode')=='00' and len(items)==total and total>0 and not record.get('pagination_error')
        record['collected_items_n']=len(items)
        if not record['complete']:
            logger.error('query_date=%s incomplete result=%s collected=%s expected=%s',
                         day.isoformat(),record.get('resultCode'),len(items),total)
        return record
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures={executor.submit(fetch,day):day for day in days}
        for i,future in enumerate(as_completed(futures),1):
            day=futures[future]
            try: metadata.append(future.result())
            except Exception as error:
                logger.error('query_date=%s failed: %s',day.isoformat(),type(error).__name__)
                metadata.append({'date':day.isoformat(),'complete':False,'error':type(error).__name__})
            if i%30==0 or i==len(days):
                logger.info('Collected %s/%s query days; complete=%s',i,len(days),sum(x['complete'] for x in metadata))
                (RAW/f'collection_{year}.json').write_text(json.dumps(sorted(metadata,key=lambda x:x['date']),ensure_ascii=False,indent=2),encoding='utf-8')
    if not all(x['complete'] for x in metadata):
        raise RuntimeError(f'{sum(not x["complete"] for x in metadata)} query days incomplete; cache and manifest preserved for retry')
    return metadata


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--year',type=int,default=2025)
    args=parser.parse_args()
    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(name)s %(message)s')
    collect(args.year)

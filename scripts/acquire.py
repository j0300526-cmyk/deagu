"""Download public official sources. Never bypass authentication or CAPTCHA."""
from pathlib import Path
import hashlib, json
import requests

RAW = Path(__file__).resolve().parents[1] / 'data/raw'
RAW.mkdir(parents=True, exist_ok=True)


def download(url, name, signature):
    p = RAW/name
    if p.exists():
        print('보존 (기존 원본)',name); return
    try:
        r=requests.get(url,timeout=120);r.raise_for_status()
        if signature and not r.content.startswith(signature):
            raise ValueError('원본 형식 미확인: 로그인·오류·CAPTCHA 여부 확인 필요')
        p.write_bytes(r.content)
        print('확보',name,len(r.content),hashlib.sha256(r.content).hexdigest())
    except Exception as e:
        print('확보 불가',name,str(e),'→ DATA_SOURCES.md 수동 다운로드 절차 참조')


if __name__ == '__main__':
    for year,seq in [(2024,12),(2025,13)]:
        download(f'https://www.mcee.go.kr/home/file/readDownloadFile.do?fileId=140188&fileSeq={seq}',f'statistics_{year}_catalog.xlsx',b'PK')
    for year,enc,seq in [(2024,'9c354647b5875e5d8641bfcf00cb99f09366e28bd3e57aac',1),(2025,'970b9c632bbdff8bcda91fa869495da9a945872419d47722',2)]:
        download(f'https://www.gir.go.kr/home/file/readDownloadFile.do?encFileId={enc}&fileSeq={seq}',f'gir_{year}.pdf',b'%PDF')
    try:
        j=requests.get('https://www.data.go.kr/tcs/dss/selectFileDataDownload.do',params={
            'publicDataPk':'3073222','publicDataDetailPk':'uddi:3f441edb-382c-4a63-8f3a-ff7d3a2f8f25',
            'atchFileId':'','fileDetailSn':'1','publicDataTyCode':'PR0051'},timeout=45).json()
        if not j.get('status'): raise ValueError('포털 다운로드 승인 상태 확인 불가')
        from urllib.parse import urlencode
        url='https://www.data.go.kr/cmm/cmm/fileDownload.do?'+urlencode({'atchFileId':j['atchFileId'],'fileDetailSn':j['fileDetailSn'],'dataNm':j['dataSetFileDetailInfo']['dataNm']})
        download(url,'facilities_portal_download.csv',b'\xef\xbb\xbf')
    except Exception as e: print('전국 CSV 재수집 실패:',str(e),'DATA_SOURCES.md 참고')

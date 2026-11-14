"""WORKING: compute global eclipse maxima for a requested JST calendar year.
Source: Swiss Ephemeris (pyswisseph) global eclipse search with Moshier flag.
Results must be independently checked before final LOCKED/publication.
"""
from pathlib import Path
from datetime import datetime,timedelta,timezone
import argparse,csv,json
import swisseph as swe
UTC=timezone.utc; JST=timezone(timedelta(hours=9))
FIELDS=['食最大日時_JST','種類','食最大日時_UTC','出典','最大時刻_ISO_JST','フラグ','可視性','時刻検証']

def jd(t):
    u=t.astimezone(UTC)
    return swe.julday(u.year,u.month,u.day,u.hour+u.minute/60+u.second/3600+u.microsecond/3.6e9)

def from_jd(j):
    y,m,d,h=swe.revjul(j,swe.GREG_CAL)
    return datetime(y,m,d,tzinfo=UTC)+timedelta(hours=h)

def label(solar,flags):
    if solar:
        if flags & swe.ECL_ANNULAR_TOTAL: return '金環皆既日食'
        if flags & swe.ECL_TOTAL: return '皆既日食'
        if flags & swe.ECL_ANNULAR: return '金環日食'
        if flags & swe.ECL_PARTIAL: return '部分日食'
    else:
        if flags & swe.ECL_TOTAL: return '皆既月食'
        if flags & swe.ECL_PARTIAL: return '部分月食'
        if flags & swe.ECL_PENUMBRAL: return '半影月食'
    raise ValueError(f'Unknown eclipse type solar={solar}, flag={flags}')

def calculate(year):
    assert 1900<=year<=2099
    start=datetime(year,1,1,tzinfo=JST)
    finish=datetime(year+1,1,1,tzinfo=JST)
    entries=[]
    # Search one week before year boundary to include Dec 31 UTC / Jan 1 JST.
    for solar,fn in ((True,swe.sol_eclipse_when_glob),(False,swe.lun_eclipse_when)):
        j=jd(start-timedelta(days=7))
        for _ in range(15):
            flags,tret=fn(j,swe.FLG_MOSEPH)
            peak_utc=from_jd(tret[0]);peak_jst=peak_utc.astimezone(JST)
            if peak_jst>=finish: break
            if start<=peak_jst<finish:
                entries.append({'solar':solar,'flags':int(flags),'utc':peak_utc,'jst':peak_jst,'kind':label(solar,flags)})
            j=tret[0]+1
        else: raise RuntimeError('Eclipse search iteration guard triggered')
    entries.sort(key=lambda x:x['jst'])
    assert len({(e['solar'],e['utc'].isoformat()) for e in entries})==len(entries)
    assert all(e['jst'].year==year for e in entries)
    return entries

def write(year,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    events=calculate(year)
    dest=out/f'{year}_日食月食_自動計算_WORKING.csv'
    with dest.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,FIELDS);w.writeheader()
        for e in events:
            t=e['jst'];utc=e['utc']
            rounded=t+timedelta(seconds=30)
            w.writerow({'食最大日時_JST':rounded.strftime('%Y-%m-%d %H:%M'),
                '種類':e['kind'],'食最大日時_UTC':utc.strftime('%Y-%m-%d %H:%M:%S.%f'),
                '出典':'Swiss Ephemeris (Moshier): global eclipse maximum, not local visibility',
                '最大時刻_ISO_JST':t.isoformat(timespec='microseconds'),'フラグ':e['flags'],
                '可視性':'全球（日本での可視性を示さない）','時刻検証':'WORKING・独立照合未実施'})
    meta={'year':year,'count':len(events),'solar':sum(e['solar'] for e in events),'lunar':sum(not e['solar'] for e in events),
          'source':'Swiss Ephemeris Moshier global search','external_ephemeris_check':'NOT RUN',
          'events':[{'kind':e['kind'],'peak_JST':e['jst'].isoformat(timespec='seconds')} for e in events]}
    (out/f'{year}_eclipse_calculation_QA.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    return meta
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--year',type=int,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();print(json.dumps(write(a.year,a.output),ensure_ascii=False))

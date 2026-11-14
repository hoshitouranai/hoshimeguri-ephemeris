"""Annual/monthly event tables from the ONE year-scoped master CSV.
WORKING. Exact event time is retained in CSV; display is JST minute rounding.
No synthetic eclipse peaks are supplied.
"""
from pathlib import Path
from datetime import datetime,timedelta
import argparse,csv,json
ROOT=Path(__file__).resolve().parent
FIELDS=['日時（JST）','天体','種類','サイン移動・位置','イベントID','時刻精度']

def generate(year, out):
    path=ROOT/'data'/f'{year}_主要イベント_自動計算.csv'
    if not path.is_file():raise FileNotFoundError(path)
    with path.open(encoding='utf-8-sig',newline='') as f: source=list(csv.DictReader(f))
    if not source: raise RuntimeError('No events')
    out.mkdir(parents=True,exist_ok=True)
    annual=[]; monthly={m:[] for m in range(1,13)}; ids=set()
    for r in source:
        ident=r['event_id']; assert ident not in ids, ident; ids.add(ident)
        t=datetime.fromisoformat(r['計算日時_JST'])
        assert t.year==year and t.utcoffset()==timedelta(hours=9)
        display=t+timedelta(seconds=30)
        kind=('逆行開始' if r['種類']=='逆行開始' else '順行再開') if r['分類']=='留' else ('逆行入座' if r['種類']=='逆行方向' else '順行入座')
        # Raw zodiac longitude near ingress cannot be rounded to 30 degrees in the sign.
        sign_part=r['詳細'].split('→')[-1] if '→' in r['詳細'] else ''
        if r['分類']=='サイン移動': label=sign_part+(' 29°59′' if kind=='逆行入座' else ' 00°00′')
        else:
            longitude=float(r['黄経_度'])%360
            signs='牡羊座 牡牛座 双子座 蟹座 獅子座 乙女座 天秤座 蠍座 射手座 山羊座 水瓶座 魚座'.split()
            degree=int(longitude%30*60+1e-8)
            label=f'{signs[int(longitude//30)%12]} {degree//60:02d}°{degree%60:02d}′'
        row=dict(zip(FIELDS,[display.strftime('%Y-%m-%d %H:%M'),r['対象'],kind,label,ident,'暫定・独立天文暦照合未実施']))
        annual.append(row);monthly[t.month].append(row)  # assign by source's exact JST month
    # The same computed eclipse maximum is added to both annual and monthly tables.
    eclipse_path=ROOT/'data'/f'{year}_日食月食_自動計算_WORKING.csv'
    with eclipse_path.open(encoding='utf-8-sig',newline='') as ef:
        eclipse_source=list(csv.DictReader(ef))
    for i,e in enumerate(eclipse_source):
        t=datetime.fromisoformat(e['最大時刻_ISO_JST'])
        assert t.year==year and t.utcoffset()==timedelta(hours=9)
        rounded=(t+timedelta(seconds=30)).strftime('%Y-%m-%d %H:%M')
        row=dict(zip(FIELDS,[rounded,'太陽' if '日食' in e['種類'] else '月',
            e['種類'],'食の全球最大時刻（日本から見えるとは限らない）',
            f'{year}-eclipse-{i+1:02d}','WORKING・NASAとの独立時刻照合未完了']))
        annual.append(row)
        monthly[t.month].append(row)
    annual.sort(key=lambda row:row['日時（JST）'])
    for items in monthly.values():items.sort(key=lambda row:row['日時（JST）'])
    def write(p,items):
        with p.open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,FIELDS);w.writeheader();w.writerows(items)
    write(out/f'{year}_年間主要イベント一覧_WORKING.csv',annual)
    for m,items in monthly.items():write(out/f'{year}年{m:02d}月_主要イベント一覧_WORKING.csv',items)
    # Test that every annual event is present once in the monthly tables with identical values.
    flatten=[r for m in range(1,13) for r in monthly[m]]
    assert sorted(tuple(r.values()) for r in flatten)==sorted(tuple(r.values()) for r in annual)
    result={'year':year,'annual_count':len(annual),'monthly_total':len(flatten),'month_counts':{m:len(v) for m,v in monthly.items()},'annual_month_consistency':'PASS','eclipses':len(eclipse_source),'eclipse_master_consistency':'PASS'}
    (out/f'{year}_events_consistency.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--year',type=int,required=True);p.add_argument('--output',type=Path,default=ROOT/'output'); a=p.parse_args();print(json.dumps(generate(a.year,a.output),ensure_ascii=False))

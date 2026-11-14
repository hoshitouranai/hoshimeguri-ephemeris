"""Single-year entry point for WORKING annual + monthly diagrams and event data."""
from pathlib import Path
import argparse,json,subprocess,sys,shutil,csv,hashlib
ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--year',type=int,required=True)
parser.add_argument('--months',default='all',help='all or comma-separated months, e.g. 2')
parser.add_argument('--skip-cover-pdf',action='store_true',help='For QA: render the cover PNG only is not yet supported; default creates cover PNG and PDF')
a=parser.parse_args()
assert 1900<=a.year<=2099
months=list(range(1,13)) if a.months=='all' else [int(x) for x in a.months.split(',')]
assert len(set(months))==len(months) and all(1<=m<=12 for m in months)
YEAR=a.year
p=subprocess.run([sys.executable,str(ROOT/'generate_year_data.py'),'--year',str(YEAR),'--output',str(ROOT/'data')],check=True,capture_output=True,text=True)
print('Calculated',p.stdout.strip(),flush=True)
subprocess.run([sys.executable,str(ROOT/'render_event_lists.py'),'--year',str(YEAR),'--output',str(ROOT/'output')],check=True,capture_output=True,text=True)
print('Annual + 12 monthly event lists OK',flush=True)
for m in months:
 subprocess.run([sys.executable,str(ROOT/'render_month_year.py'),'--year',str(YEAR),'--month',str(m)],check=True,capture_output=True,text=True)
 print('Month',m,'OK',flush=True)
annual=ROOT/'output'/f'{YEAR}_annual.png'
subprocess.run([sys.executable,str(ROOT/'annual_work'/'annual_engine.py'),'--year',str(YEAR),'--chiron-ephe-dir',str(ROOT/'ephe'),'--output',str(annual)],check=True,capture_output=True,text=True)
print('Annual OK',flush=True)
subprocess.run([sys.executable,str(ROOT/'render_mercury_year.py'),'--year',str(YEAR),'--output',str(ROOT/'output')],check=True,capture_output=True,text=True)
# 2027-adopted two-column Mercury layout, from year-specific generated CSV.
mercury_csv=ROOT/'output'/f'{YEAR}_水星年間運行詳細_ヘッド_キロン_WORKING.csv'
subprocess.run([sys.executable,str(ROOT/'render_mercury_2027_layout.py'),'--year',str(YEAR),'--csv',str(mercury_csv),'--outdir',str(ROOT/'output')],check=True,capture_output=True,text=True)
print('Mercury annual detail (2027-adopted layout) OK',flush=True)
subprocess.run([sys.executable,str(ROOT/'cover'/'cover_year.py'),'--year',str(YEAR)],check=True,capture_output=True,text=True)
print('Adopted B cover OK',flush=True)
cover=ROOT/'cover'/'output'/f'星めぐり天文暦{YEAR}_表紙B案_採用版.png'
assert cover.is_file() and cover.stat().st_size>10000
mercury_accepted=ROOT/'output'/f'{YEAR}_水星の運行詳細_2027年版統一.png'
assert mercury_accepted.is_file() and mercury_accepted.stat().st_size>10000
imgs=[annual,cover,mercury_accepted]+[ROOT/'output'/f'{YEAR}年{m:02d}月_v16_年間共通候補.png' for m in months]
assert all(x.is_file() and x.stat().st_size>10000 for x in imgs)
for m in months:
 path=ROOT/'output'/f'{YEAR}年{m:02d}月_詳細イベント_試作.csv'
 with path.open(encoding='utf-8-sig',newline='') as f:
  rows=list(csv.DictReader(f))
 assert all(r['日時_JST'].startswith(f'{YEAR}-{m:02d}') for r in rows)
qa={'year':YEAR,'status':'WORKING; not independently validated','month_count':len(months),'annual':str(annual.relative_to(ROOT)),'eclipse_peak':'Swiss Ephemeris Moshier global maxima; unverified externally', 'cover':'B adopted, year-selectable', 'event_table':'single year-specific master' ,'sources':'New year Moshier calculation; no 2027 event CSV or output PNG used','outputs':{str(x.relative_to(ROOT)):hashlib.sha256(x.read_bytes()).hexdigest() for x in imgs}}
(ROOT/'output'/f'{YEAR}_build_log.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2))
print(f'FINISHED {YEAR}: annual + {len(months)} months',flush=True)
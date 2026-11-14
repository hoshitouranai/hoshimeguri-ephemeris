"""Independent catalog spot-check for eclipse maximum (NASA GSFC) dates/times.
Reference: https://eclipse.gsfc.nasa.gov/solar.html ; https://eclipse.gsfc.nasa.gov/lunar.html
Times below are UTC. Year selection in project follows JST, so Dec 31 2028 UTC eclipse occurs Jan 1 2029 JST.
NASA and Swiss Ephemeris definitions / delta-T assumptions need reconciliation; FAIL is intentional if >30 s.
"""
from pathlib import Path
from datetime import datetime,timezone
import csv,json,argparse
NASA={
 '2028-01-12 04:14:13':'部分月食', '2028-01-26 15:08:58':'金環日食',
 '2028-07-06 18:20:57':'部分月食', '2028-07-22 02:56:39':'皆既日食',
 '2028-12-31 16:53:15':'皆既月食', '2029-01-14 17:13:47':'部分日食',
 '2029-06-12 04:06:13':'部分日食', '2029-06-26 03:23:22':'皆既月食',
 '2029-07-11 15:37:18':'部分日食', '2029-12-05 15:03:57':'部分日食',
 '2029-12-20 22:43:12':'皆既月食',
}
def verify(root):
 results=[]
 for year in (2028,2029):
  with (root/'data'/f'{year}_日食月食_自動計算_WORKING.csv').open(encoding='utf-8-sig') as f:
   rows=list(csv.DictReader(f))
  for row in rows:
   measured=datetime.fromisoformat(row['最大時刻_ISO_JST']).astimezone(timezone.utc).replace(tzinfo=None)
   candidates=[(abs((measured-datetime.strptime(k,'%Y-%m-%d %H:%M:%S')).total_seconds()),k) for k,v in NASA.items() if v==row['種類']]
   err,nasa=min(candidates)
   results.append({'JST_year':year,'kind':row['種類'],'NASA_UTC':nasa,'computed_UTC':measured.isoformat(timespec='seconds'),'abs_difference_sec':round(err,2),'within_30_seconds':err<=30})
 assert len(results)==11
 result={'status':'FAIL (NASA timestamp mismatch >30 seconds): no LOCKED','threshold_sec':30,'count':len(results),'max_abs_difference_sec':max(r['abs_difference_sec'] for r in results),'mean_abs_difference_sec':round(sum(r['abs_difference_sec'] for r in results)/len(results),2),'type_date_count':'PASS','maximum_time':'FAIL','nasa_sources':['https://eclipse.gsfc.nasa.gov/solar.html','https://eclipse.gsfc.nasa.gov/lunar.html'],'results':results}
 (root/'QA_ECLIPSES_NASA_2028_2029.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
 a=p.parse_args();print(json.dumps({k:v for k,v in verify(a.root).items() if k!='results'},ensure_ascii=False))

"""Stage36: independent *execution* of Moshier position/speed at master event instants.
Not an independent astronomical ephemeris: both calculations use Swiss Ephemeris/Moshier.
"""
import csv,io,json,zipfile,hashlib
from datetime import datetime,timezone,timedelta
from pathlib import Path
import swisseph as swe
from annual_engine import BODIES
MASTER='data/2027_主要9天体イベント統合マスター_69件_v16.csv'
def at(t,planet):
 u=t.astimezone(timezone.utc);jd=swe.julday(u.year,u.month,u.day,u.hour+u.minute/60+u.second/3600+u.microsecond/3600000000)
 v,flags=swe.calc_ut(jd,BODIES[planet],swe.FLG_MOSEPH|swe.FLG_SPEED)
 return v[0],v[3]
def signed_delta(a,b):return (a-b+180)%360-180
def check(zip_path):
 with zipfile.ZipFile(zip_path) as z:
  raw=z.read(MASTER);rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
 output=[];fail=[]
 for r in rows:
  t=datetime.fromisoformat(r['計算日時_JST']); lon,speed=at(t,r['対象']); target=float(r['黄経_度']); delta=abs(signed_delta(lon,target));kind=r['分類']
  if kind=='留':
   bef=at(t-timedelta(minutes=15),r['対象'])[1];aft=at(t+timedelta(minutes=15),r['対象'])[1]
   crossing=(bef*aft<0); tolerance=0.002; ok=delta<0.005 and crossing
   note='speed sign at ±15 min confirms station crossing; same Moshier astronomical basis'
  else:
   bef=at(t-timedelta(minutes=15),r['対象'])[0];aft=at(t+timedelta(minutes=15),r['対象'])[0]
   crossing=signed_delta(bef,target)*signed_delta(aft,target)<0;ok=delta<0.005 and crossing
   note='longitude boundary crossing at ±15 min; same Moshier astronomical basis'
  res={'event_id':r['event_id'],'body':r['対象'],'kind':kind,'subtype':r['種類'],'master_time_jst':r['計算日時_JST'],'master_longitude':target,'recomputed_longitude':round(lon,9),'longitude_error_deg':round(delta,9),'recomputed_speed_deg_day':round(speed,10),'crossing_15min':crossing,'same_engine_self_consistent':bool(ok),'independent_ephemeris_verified':False,'note':note}
  output.append(res)
  if not ok:fail.append(res)
 return {'verification_scope':'master event longitude and station sign at precise timestamp via fresh call to Swiss Ephemeris Moshier','independent_ephemeris':False,'master_sha256':hashlib.sha256(raw).hexdigest(),'events':len(rows),'passed':len(rows)-len(fail),'failed':len(fail),'fail_ids':[x['event_id'] for x in fail],'rows':output,'external_reference_checks':[{'event':'Mars stations retrograde','JST':'2027-01-10 21:59','source':'OmenMe Swiss Ephemeris/JPL DE441 2026-09-05','status':'date/time matches publicly listed 12:59 UTC (minute precision)'},{'event':'Mars stations direct','JST':'2027-04-01 23:08','source':'OmenMe Swiss Ephemeris/JPL DE441 2026-09-05','status':'date/time matches publicly listed 14:08 UTC (minute precision)'},{'event':'Jupiter ingress Virgo','JST':'2027-07-26 approx 13:45','source':'CelestialDB estimated 04:45 UTC','status':'independent published approx differs from some existing records; requires minute level verification'}]}
if __name__=='__main__':
 p=Path(__file__).parent
 report=check(p/'colors_v17.zip')
 (p/'stage36_event_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 with (p/'stage36_event_audit.csv').open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=report['rows'][0].keys());w.writeheader();w.writerows(report['rows'])
 print({k:v for k,v in report.items() if k in ('events','passed','failed','fail_ids')})

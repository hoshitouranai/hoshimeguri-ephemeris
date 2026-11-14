"""Recalculate year-scoped ingress and station inputs. Never copies a prior year's events.
DRAFT: Moshier numerical precision, eclipses not supplied by this generator.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import argparse,csv,math,json
import swisseph as swe
from scipy.optimize import brentq
JST=timezone(timedelta(hours=9)); UTC=timezone.utc
SIGNS='牡羊座 牡牛座 双子座 蟹座 獅子座 乙女座 天秤座 蠍座 射手座 山羊座 水瓶座 魚座'.split()
BODIES={'太陽':swe.SUN,'水星':swe.MERCURY,'金星':swe.VENUS,'火星':swe.MARS,'木星':swe.JUPITER,'土星':swe.SATURN,'天王星':swe.URANUS,'海王星':swe.NEPTUNE,'冥王星':swe.PLUTO}
def jd(t):
 u=t.astimezone(UTC);return swe.julday(u.year,u.month,u.day,u.hour+u.minute/60+u.second/3600+u.microsecond/3.6e9)
def calc(j,body):return swe.calc_ut(j,body,swe.FLG_MOSEPH|swe.FLG_SPEED)[0]
def time_at(j):return datetime.fromtimestamp((j-2440587.5)*86400,UTC).astimezone(JST)
def calculate(year):
 st=jd(datetime(year,1,1,tzinfo=JST));en=jd(datetime(year+1,1,1,tzinfo=JST));events=[]
 for name,ident in BODIES.items():
  # 3-hour samples guard both slow stations and fast sign crossings
  a=st;xa=calc(a,ident)
  while a<en-1e-9:
   b=min(a+0.125,en);xb=calc(b,ident)
   raw=(xb[0]-xa[0]+180)%360-180
   for k in range(12):
    target=k*30
    d=((xa[0]-target+180)%360)-180
    if (raw>0 and d<0<=d+raw) or (raw<0 and d>0>=d+raw):
     rt=brentq(lambda q:((calc(q,ident)[0]-target+180)%360)-180,a,b,xtol=1e-10)
     to=SIGNS[k] if raw>0 else SIGNS[(k-1)%12]
     frm=SIGNS[(k-1)%12] if raw>0 else SIGNS[k]
     events.append(dict(name=name,time=time_at(rt),lon=calc(rt,ident)[0],kind='ingress',retro=raw<0,details=f'{frm}→{to}'))
   if xa[3]*xb[3]<0:
    rt=brentq(lambda q:calc(q,ident)[3],a,b,xtol=1e-10)
    events.append(dict(name=name,time=time_at(rt),lon=calc(rt,ident)[0],kind='station',retro=xb[3]<0,details='数値求根'))
   a,xa=b,xb
 # Moon ingress separate: each sign boundary
 a=st;xa=calc(a,swe.MOON)
 while a<en-1e-9:
  b=min(a+0.125,en);xb=calc(b,swe.MOON);raw=(xb[0]-xa[0]+180)%360-180
  for k in range(12):
   target=k*30;d=((xa[0]-target+180)%360)-180
   if d<0<=d+raw:
    rt=brentq(lambda q:((calc(q,swe.MOON)[0]-target+180)%360)-180,a,b,xtol=1e-10)
    events.append(dict(name='月',time=time_at(rt),lon=float(target),kind='ingress',retro=False,details=SIGNS[k]))
  a,xa=b,xb
 events.sort(key=lambda e:e['time']); assert all(e['time'].year==year for e in events)
 # precision reporting, includes dates and provenance
 return events

def write(year,out):
 events=calculate(year);out.mkdir(parents=True,exist_ok=True)
 def dump(filename,fields,rows):
  with (out/filename).open('w',encoding='utf-8-sig',newline='') as f:
   w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
 major=[];moon=[]
 for i,e in enumerate(events):
  if e['name']=='月':
   moon.append({'日時_JST':e['time'].strftime('%Y-%m-%d %H:%M'),'月':e['time'].month,'移動先':e['details'],'黄経度':round(e['lon'])%360,'計算手法':'Swiss Ephemeris Moshier・地心トロピカル・数値求根'})
  else:
   major.append({'event_id':f'{year}-auto-{i:04d}','対象':e['name'],'分類':'サイン移動' if e['kind']=='ingress' else '留','種類':('逆行方向' if e['retro'] else '順行方向') if e['kind']=='ingress' else ('逆行開始' if e['retro'] else '順行開始'),'計算日時_JST':e['time'].isoformat(),'黄経_度':f"{e['lon']:.10f}",'詳細':e['details'],'計算根拠':'Swiss Ephemeris Moshier・数値求根','既存台帳照合':'未実施','既存台帳との差_秒':'','外部資料照合':'未実施','直接DE440_DE441求根':'未実施','時刻掲載区分':'暫定（分単位・独立照合未了）','元ファイル':'指定年自動生成'})
 dump(f'{year}_主要イベント_自動計算.csv',list(major[0]),major)
 dump(f'{year}_月サイン移動_自動計算.csv',list(moon[0]),moon)
 from calculate_eclipses_year import write as write_eclipses
 eclipse_meta=write_eclipses(year,out)
 meta={'year':year,'major_count':len(major),'moon_ingress_count':len(moon),'eclipses':f"{eclipse_meta['count']} calculated, independent verification pending",'independent_ephemeris_comparison':'未実施','old_year_csv_used':False,'first':events[0]['time'].isoformat(),'last':events[-1]['time'].isoformat()}
 (out/f'{year}_calc_status.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
 return meta
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--year',type=int,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(write(a.year,a.output),ensure_ascii=False))

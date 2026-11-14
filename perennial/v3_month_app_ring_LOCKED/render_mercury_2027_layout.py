"""Recreate the adopted 2027 Mercury-detail page layout for any computed year.
Does not change the immutable 2027 LOCKED original or calculated event CSV.
Requires: Pillow and Swiss Ephemeris, source-data CSV from the perennial generator.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math
from pathlib import Path
from datetime import datetime,timezone,timedelta
from PIL import Image,ImageDraw,ImageFont
import swisseph as swe

SRC=Path(__file__).resolve().parent
ROOT=SRC
W,H=3508,2480
SX,SY=W/1179,H/834
B='#273a45'; BG='#f6f7ed'; GREEN='#e7eedf'; ALT='#f3f5ec'; HEAD='#e7ede2'
SIGNS='牡羊座 牡牛座 双子座 蟹座 獅子座 乙女座 天秤座 蠍座 射手座 山羊座 水瓶座 魚座'.split()
COLORS=['#c33e48','#42854d','#b78a10','#aa586b','#bd7717','#6a9541','#37968e','#b74768','#6567b2','#4e6174','#2777aa','#8060a4']
JST=timezone(timedelta(hours=9))
FREG='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
FBOLD='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
FGLYPH='/usr/share/fonts/opentype/freefont/FreeSerif.otf'

def pt(x,y):return round(x*SX),round(y*SY)
def rect(d, xy,fill,outline=None,width=1,radius=0):
 x0,y0,x1,y1=xy;box=(*pt(x0,y0),*pt(x1,y1))
 if radius:d.rounded_rectangle(box,radius=round(radius*SY),fill=fill,outline=outline,width=max(1,round(width*SY)))
 else:d.rectangle(box,fill=fill,outline=outline,width=max(1,round(width*SY)))
def font(size,bold=False):return ImageFont.truetype(FBOLD if bold else FREG,round(size*SY),index=0)
def text(d,x,y,s,size=12,bold=False,color=B,anchor='lt'):
 d.text(pt(x,y),str(s),font=font(size,bold),fill=color,anchor=anchor)
def line(d,x0,y0,x1,y1,color,width=1):d.line((*pt(x0,y0),*pt(x1,y1)),fill=color,width=max(1,round(width*SY)))
def truncate_sign(s):return s.split()[0]
def event_parts(r):
 dt=datetime.strptime(r['日時_JST'],'%Y-%m-%d %H:%M')
 kind=r['分類'];sign=truncate_sign(r['水星サイン度数']); degree=r['水星サイン度数'].split()[-1]
 if kind in ('順行入座','逆行入座'):
  target=SIGNS.index(sign)
  previous=SIGNS[(target+1)%12] if kind=='逆行入座' else SIGNS[(target-1)%12]
  label='入座（逆行中）' if kind=='逆行入座' else '入座'
  movement=[(previous,COLORS[SIGNS.index(previous)]),(' → ',B),(sign,COLORS[target])]
 elif kind=='逆行開始':movement=[(sign,COLORS[SIGNS.index(sign)])];label='逆行開始'
 else:movement=[(sign,COLORS[SIGNS.index(sign)])];label='順行再開'
 return (f'{dt.month}/{dt.day}',dt.strftime('%H:%M'),movement,degree,label)
def lon(t,planet):
 u=t.astimezone(timezone.utc)
 jd=swe.julday(u.year,u.month,u.day,u.hour+u.minute/60+u.second/3600)
 return swe.calc_ut(jd,planet,swe.FLG_MOSEPH)[0][0]%360

def summary(year):
 swe.set_ephe_path(str(SRC / "ephe"))
 t0=datetime(year,1,1,0,0,tzinfo=JST);t1=datetime(year,12,31,23,59,tzinfo=JST)
 values={}
 for label,p in [('キロン',swe.CHIRON),('ドラゴンヘッド',swe.TRUE_NODE)]:
  a,b=lon(t0,p),lon(t1,p)
  def degree(v):return f'{SIGNS[int(v//30)]}{int(v%30):02d}°{int((v%30%1)*60):02d}′'
  values[label]=(degree(a),degree(b))
 return values

def draw_table(d,rows,left,top,bottom=537):
 # Coordinates derived from 2027-11-15 LOCKED v3 page 3, no pixel-copying of printed content.
 width=520;x=left
 rect(d,(x,top,x+width,bottom),None,outline='#b4c6ad',width=1)
 rect(d,(x,top,x+width,top+32),HEAD)
 edges=[x+12,x+81,x+151,x+330,x+403]
 for px,h in zip(edges,['日付','時刻','サイン','度数','天体の動き']):text(d,px,top+8,h,12,bold=True)
 row_h=min(32,(bottom-(top+32))/max(1,len(rows)));start=top+32
 for i,row in enumerate(rows):
  y=start+i*row_h
  if i%2:rect(d,(x+1,y,x+width-1,y+row_h),ALT)
  date,clock,movement,degree,label=event_parts(row)
  text(d,x+11,y+8,date,12,bold=True,color='#253e4e')
  text(d,x+80,y+8,clock,12,bold=True,color='#253e4e')
  advance=x+151
  for part,color in movement:
   text(d,advance,y+8,part,12,bold=True,color=color)
   advance+=d.textlength(part,font=font(12,True))/SX
  text(d,x+330,y+8,degree,12,color='#435666')
  col='#c54b4c' if label=='逆行開始' else '#388c79' if label=='順行再開' else B
  text(d,x+401,y+8,label,11.8,bold=True,color=col)

def make(year,source,out):
 with source.open(encoding='utf-8-sig',newline='') as f:
  rows=list(csv.DictReader(f))
 if not rows or any(int(r['年'])!=year for r in rows):raise ValueError('CSV does not match requested year')
 rows.sort(key=lambda x:x['日時_JST'])
 if len(rows)>36:raise ValueError('At most 36 Mercury events fit on one page; rendering stops rather than silently losing events')
 img=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(img)
 logo=Image.open(SRC/'icon_2027_original.png').convert('RGB');logo=logo.resize(pt(40,40),Image.Resampling.LANCZOS)
 img.paste(logo,pt(59,37))
 text(d,116,41,'HOSHITOURANAI',22,bold=True,color='#2e4141')
 text(d,328,43,'｜',20,color='#74817b')
 text(d,360,41,'星めぐり天文暦',22,bold=True,color='#2e4141')
 text(d,538,43,'｜',20,color='#74817b')
 text(d,569,41,f'{year}年 水星の運行詳細',22,bold=True,color='#2e4141')
 text(d,59,95,f'サイン移動{sum("入座" in r["分類"] for r in rows)}件＋留{sum("入座" not in r["分類"] for r in rows)}件　｜ 日本標準時 JST ｜ 地心・トロピカル黄道',11,color='#6b766f')
 left_count=math.ceil(len(rows)/2)
 draw_table(d,rows[:left_count],59,114)
 draw_table(d,rows[left_count:],599,114)
 # Annual reference panel follows adopted 2027 layout. Values computed per year.
 rect(d,(60,556,1119,786),'#fff9ed',outline='#e9cbb6',radius=8,width=1.5)
 rect(d,(60,556,1119,591),'#f1f3df')
 text(d,76,562,'その他の天体の動き（年間参考情報）',18,bold=True,color='#334e52')
 notes=summary(year)
 for i,(mark,title,body) in enumerate([
  ('⚷','キロン',f'{year}年の年初は{notes["キロン"][0]}付近、年末は{notes["キロン"][1]}付近。'),
  ('☊','ドラゴンヘッド',f'{year}年の年初は{notes["ドラゴンヘッド"][0]}付近、年末は{notes["ドラゴンヘッド"][1]}付近（トゥルーノード）。'),
  ('☽','月','月のサイン移動と月相は、各月の「月間天文暦」に掲載しています。')]):
  y=599+i*68
  if i:line(d,74,y-5,1104,y-5,'#e9d1c2',.8)
  d.text(pt(83,y+7),mark,font=ImageFont.truetype(FGLYPH,round(22*SY)),fill='#8a9b80',anchor='lt')
  text(d,121,y+9,title,15,bold=True,color='#344b59')
  text(d,289,y+9,body,13.1,color='#415669')
 text(d,60,806,'※ 年間参考情報は概況。JST／地心・トロピカル黄道。',10,color='#86938d')
 out.mkdir(parents=True,exist_ok=True)
 png=out/f'{year}_水星の運行詳細_2027年版統一.png'
 pdf=out/f'{year}_水星の運行詳細_2027年版統一.pdf'
 img.save(png,optimize=True)
 img.save(pdf,'PDF',resolution=300.0)
 return {'year':year,'event_count':len(rows),'png':png.name,'pdf':pdf.name,'sha256_png':hashlib.sha256(png.read_bytes()).hexdigest()}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--year',type=int,required=True);p.add_argument('--csv',type=Path);p.add_argument('--outdir',type=Path,default=SRC/'output');a=p.parse_args()
 csvfile=a.csv or ROOT/'output'/f'{a.year}_水星年間運行詳細_ヘッド_キロン_WORKING.csv'
 print(json.dumps(make(a.year,csvfile,a.outdir),ensure_ascii=False,indent=2))

from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import argparse,json
parser=argparse.ArgumentParser(description='10-column major planetary event table')
parser.add_argument('--data',required=True)
parser.add_argument('--icon',required=True)
parser.add_argument('--output',required=True)
args=parser.parse_args()
input_data=json.loads(Path(args.data).read_text(encoding='utf-8'))
assert len(input_data['events'])<=10, '10-column limit exceeded'
assert len(input_data['planets'])==12, 'expected 12 body rows'
assert len(input_data['values'])==12 and all(len(r)==len(input_data['events']) for r in input_data['values']), 'event/value mismatch'
W,H=2000,1414
im=Image.new('RGB',(W,H),'#F6F8ED');d=ImageDraw.Draw(im)
reg='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc';bold='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc';symbol='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
f=lambda n,b=False:ImageFont.truetype(bold if b else reg,n)
fs=lambda n:ImageFont.truetype(symbol,n)
ink='#34485B';gold='#C7AD77';grid='#9BA7A0'
icon=Image.open(args.icon).convert('RGB').resize((68,68))
im.paste(icon,(102,65))
def txt_center(s,ft,cx,cy,fill=ink):
 bb=d.textbbox((0,0),s,font=ft); d.text((cx-(bb[2]-bb[0])/2-bb[0],cy-(bb[3]-bb[1])/2-bb[1]),s,font=ft,fill=fill)
title=f"HOSHITOURANAI  │  星めぐり天文暦  │  {input_data['year']}年{input_data['month']} 主要天体イベント"
font_title=f(40,True)
bb=d.textbbox((0,0),title,font=font_title)
d.text((198,99-(bb[3]-bb[1])/2-bb[1]),title,font=font_title,fill=ink)
d.text((102,157),f"イベント時刻別エフェメリス｜日本標準時 JST｜地心・トロピカル黄道",font=f(20),fill='#65705D')
signs=input_data['signs']
planets=input_data['planets']
# 原本の数字の転記。外部の再照合前の試作データ。
values=input_data['values']
events=input_data['events']
L,T,R,B=100,218,1900,1216
lc=222; cw=(R-L-lc)//10; hh=154;rh=(B-T-hh)//12
def pastel(hexcolor, white_ratio=0.85):
 rgb=tuple(int(hexcolor[i:i+2],16) for i in (1,3,5))
 return tuple(round(v*(1-white_ratio)+255*white_ratio) for v in rgb)
# fill cells first, rules last
d.rectangle((L,T,R,B),fill='white')
d.rectangle((L,T,L+lc,T+hh),fill='#EFF4DF')
for j in range(10):
 x=L+lc+j*cw
 d.rectangle((x,T,x+cw,T+hh),fill=(pastel(signs[(events[j][1] if events[j][1] in signs else values[next(i for i,p in enumerate(planets) if p[0]==events[j][0])][j][0])],0.78) if j<len(events) else ('#FFFFFF' if j%2==0 else '#FAF5EA')))
 for i in range(12):
  y=T+hh+i*rh
  d.rectangle((x,y,x+cw,y+rh),fill=(pastel(signs[values[i][j][0]],0.85) if j < len(values[i]) else ('#FFFFFF' if i%2==0 else '#FAF5EA')))
for i,(g,name,c) in enumerate(planets):
 y=T+hh+i*rh
 d.rectangle((L,y,L+lc,y+rh),fill='white' if i%2==0 else '#FAF5EA')
 txt_center(g,fs(28),L+33,y+rh/2,c)
 txt_center(name,f(25 if len(name)<7 else 19,True),L+149,y+rh/2,ink)
txt_center('主要天体',f(31,True),L+lc/2,T+57)
txt_center('イベント時の位置',f(21),L+lc/2,T+105)
for j,(g,sg,ev,day,time) in enumerate(events):
 x=L+lc+j*cw; cx=x+cw/2
 pcol=next(p[2] for p in planets if p[0]==g)
 txt_center(g,fs(31),cx-25,T+26,pcol)
 txt_center((sg if sg in signs else values[next(i for i,p in enumerate(planets) if p[0]==g)][j][0]),fs(29),cx+24,T+26,signs[(sg if sg in signs else values[next(i for i,p in enumerate(planets) if p[0]==g)][j][0])])
 # final approved vocabulary for event class
 if '逆行開始' in ev: action='逆行開始';color='#C64B53'
 elif '順行再開' in ev: action='順行再開';color='#1E8C86'
 elif '逆行戻り' in ev or '逆行中入座' in ev: action='逆行中入座';color='#C64B53'
 else: action='入座';color=ink
 txt_center(action,f(20,True),cx,T+73,color)
 txt_center(day+'  '+time,f(20,True),cx,T+115)
for i in range(12):
 cy=T+hh+i*rh+rh/2
 for j,cell in enumerate(values[i]):
  x=L+lc+j*cw;cx=x+cw/2
  s,degree,*r=cell
  txt_center(s,fs(26),cx-40,cy-7,signs[s]);txt_center(degree,f(24,True),cx+15,cy-7)
  if r:txt_center('R',f(17,True),cx,cy+19,'#C64B53')
# grid lines
for j in range(11):
 x=L+lc+j*cw;d.line((x,T,x,B),fill=grid,width=3)
d.line((L+lc,T,L+lc,B),fill=grid,width=4)
for i in range(13):
 y=T+hh+i*rh;d.line((L,y,R,y),fill=grid,width=2)
d.line((L,T+hh,R,T+hh),fill=gold,width=5)
d.rectangle((L,T,R,B),outline=gold,width=6)
# Approved footer geometry, generated from source data (no image paint-over)
d.rounded_rectangle((100,1217,1900,1380),radius=14,fill='#FFF3F5',outline='#E9CFC0',width=3)
d.text((127,1230),'表の読み方',font=f(29,True),fill=ink)
d.text((127,1272),'各列は主要天体イベントの発生日時（JST）',font=f(22),fill=ink)
d.text((127,1305),'各セルはサインと度数・分。',font=f(22),fill=ink)
d.text((127,1338),'R',font=f(22,True),fill='#C64B53')
d.text((150,1338),'＝逆行中。空欄はイベントがない列です。',font=f(22),fill=ink)
d.text((1015,1230),'確認用・イベント時刻は照合中',font=f(29,True),fill=ink)
out=args.output;im.save(out)
print(out,'size',im.size,'table right',L+lc+10*cw)

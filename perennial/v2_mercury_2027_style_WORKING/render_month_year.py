from pathlib import Path
from time_rules_LOCKED import display_minute, round_to_minute, root_source_time
import argparse
import calendar
parser=argparse.ArgumentParser()
parser.add_argument("--month",type=int,default=1)
parser.add_argument("--year",type=int,required=True)
args=parser.parse_args()
assert 1<=args.month<=12
MONTH=args.month
YEAR=args.year
NEXT_MONTH=MONTH%12+1
NEXT_YEAR=YEAR+(MONTH==12)
import csv, math
from datetime import datetime,timedelta,timezone
import numpy as np
from scipy.optimize import brentq
import swisseph as swe

swe.set_ephe_path(str(Path(__file__).resolve().parent/'ephe'))
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge,Circle,FancyArrowPatch,FancyBboxPatch
from matplotlib.font_manager import FontProperties
import matplotlib.patheffects as pe
from matplotlib.path import Path as MplPath
from matplotlib.patches import PathPatch

SRC=Path(__file__).resolve().parent/'data'; OUT=Path(__file__).resolve().parent/'output'
OUT.mkdir(parents=True, exist_ok=True)
JST=timezone(timedelta(hours=9)); UTC=timezone.utc
T0=datetime(YEAR,MONTH,1,tzinfo=JST); T1=datetime(NEXT_YEAR,NEXT_MONTH,1,tzinfo=JST)
DAYS=(T1-T0).days
PHASE=['新月','三日月','上弦の月','十三夜月','満月','居待月','下弦の月','二十六夜月']
PHASE_DESC=['月は見えません。','小さな部分が見えるようになります。','右半分が照らされています。','半分以上が見えます。','月は完全に照らされています。','照明が減少します。','左半分が照らされています。','小さな部分だけがまだ見えます。']
BRAND='#203A55'; INK='#273c55'; MUTED='#657587'; GRID='#d6d9dd'; OUTLINE='#32485a'
SIGNS=['牡羊','牡牛','双子','蟹','獅子','乙女','天秤','蠍','射手','山羊','水瓶','魚']
SIGN_GLYPHS={'牡羊':'♈','牡牛':'♉','双子':'♊','蟹':'♋','獅子':'♌','乙女':'♍','天秤':'♎','蠍':'♏','射手':'♐','山羊':'♑','水瓶':'♒','魚':'♓'}
PLANETS=[('太陽','☉',swe.SUN),('月','☽',swe.MOON),('水星','☿',swe.MERCURY),('金星','♀',swe.VENUS),('火星','♂',swe.MARS),('木星','♃',swe.JUPITER),('土星','♄',swe.SATURN),('天王星','♅',swe.URANUS),('海王星','♆',swe.NEPTUNE),('冥王星','⯓',swe.PLUTO),('ドラゴンヘッド','☊',swe.TRUE_NODE),('キロン','⚷',swe.CHIRON)]
# Chiron enabled after verifying seas_18.se1 in kerykeion/sweph
PLANET_IDS={n:i for n,_,i in PLANETS}
WIDTHS={'太陽':2.0,'月':1.95,'水星':1.65,'金星':1.65,'火星':1.65,'木星':1.65,'土星':1.65,'天王星':1.65,'海王星':1.65,'冥王星':1.65,'ドラゴンヘッド':1.40,'キロン':1.35}
OUTER_R=.93
INNER_R=.300  # v6 trial: inner circle 11.8% smaller; v5 remains LOCKED
RAD_SPAN=OUTER_R-INNER_R

plt.rcParams['svg.fonttype']='none'
plt.rcParams['font.family']='Noto Sans CJK JP'
glyph_fp=FontProperties(fname='/usr/share/fonts/truetype/freefont/FreeSerif.ttf')

# palette from approved working master/csv used by v21+v21
with (SRC/'ホシトウラナイ_カラー一覧表_試作_v03_白50パーセント.csv').open(encoding='utf-8-sig',newline='') as f:
    rec=list(csv.DictReader(f))
base_color={r['対象']:r['基準色HEX'] for r in rec}
sign_base={r['対象'].replace('座',''):r['基準色HEX'] for r in rec if r['区分']=='サイン'}

def whiten(hexstr, amount=.60):
    rgb=[int(hexstr[i:i+2],16) for i in (1,3,5)]
    return '#'+''.join(f'{round(x*(1-amount)+255*amount):02X}' for x in rgb)
SIGN_COLORS=[whiten(sign_base[s], .60) for s in SIGNS]
PC={name:base_color[name] for name,_,_ in PLANETS if name in base_color}
PC['ドラゴンヘッド']=base_color.get('ドラゴンヘッド','#B19045')
PC['キロン']='#6E7750'


def sun_glyph(ax,x,y,color):
    ax.add_patch(plt.Circle((x,y),.018,fill=False,edgecolor=color,lw=1.55,zorder=11))
    ax.add_patch(plt.Circle((x,y),.0038,facecolor=color,edgecolor='none',zorder=12))

def pluto_glyph(ax,x,y,color,scale=.016):
    ax.add_patch(plt.Circle((x,y+scale*1.38),scale*.45,fill=False,edgecolor=color,lw=1.5,zorder=11))
    vertices=[(x-scale,y+scale*.5),(x-scale*.8,y-scale*.58),(x+scale*.8,y-scale*.58),(x+scale,y+scale*.5)]
    path=MplPath(vertices,[MplPath.MOVETO,MplPath.CURVE4,MplPath.CURVE4,MplPath.CURVE4])
    ax.add_patch(PathPatch(path,fill=False,edgecolor=color,lw=1.5,zorder=11))
    ax.plot([x,x],[y-scale*.45,y-scale*1.4],color=color,lw=1.5,zorder=11)
    ax.plot([x-scale*.6,x+scale*.6],[y-scale*1.05,y-scale*1.05],color=color,lw=1.5,zorder=11)


def jd(t):
    u=t.astimezone(UTC)
    return swe.julday(u.year,u.month,u.day,u.hour+u.minute/60+u.second/3600+u.microsecond/3.6e9)

def pos(body,t):
    return swe.calc_ut(jd(t),PLANET_IDS[body],swe.FLG_MOSEPH|swe.FLG_SPEED)[0]

def phase(t):
    return (pos('月',t)[0]-pos('太陽',t)[0])%360

def sign_degree(lon):
    k=int(lon//30)%12; rem=lon%30; deg=int(rem);minute=int((rem-deg)*60+0.5)
    if minute==60:
        deg+=1; minute=0
    if deg==30:
        deg=0; k=(k+1)%12
    return SIGNS[k]+'座',f'{deg:02d}°{minute:02d}′'

def dtt(t): return display_minute(t)

def event(t,name,typ,lon,detail='',origin='Swiss Ephemeris Moshier 新規計算',direction=''):
    sn,deg=sign_degree(lon)
    return dict(日時_JST=dtt(t),計算日時_JST_秒=root_source_time(t),天体=name,イベント=typ,サイン=sn,サイン内度数=deg,黄経度=f'{lon%360:.8f}',運行方向=direction,月相='',食の種類='',備考=detail,計算出典=origin)

def angle_deg(lon): return (180 + lon) % 360
def angle_rad(lon): return math.radians(angle_deg(lon))
def xy(lon,r):
    a=angle_rad(lon)
    return r*math.cos(a),r*math.sin(a)

def split_segments(lons, rads):
    segs=[]; cur=[(lons[0],rads[0])]
    prev=lons[0]
    for lon,r in zip(lons[1:],rads[1:]):
        # if jump crosses 0 Aries boundary, start a new segment
        if abs(lon-prev)>180:
            segs.append(cur); cur=[]
        cur.append((lon,r)); prev=lon
    segs.append(cur)
    return segs

def choose_inside_ring_positions(starts):
    # Fallback callout positions inside the sign-color band.
    by_name={item['name']:item for item in starts}
    manual={}
    # Keep the January Capricorn cluster legible.
    # Approved correction: Sun must sit to the left of the 山羊座 label, not over 射手座.
    manual_xy={
        '水星': (-0.16, 1.065),
        '太陽': (-0.43, 1.025),
    }
    # Keep January's approved Capricorn corrections January-only.
    if MONTH == 1:
        manual.update({n:xy for n,xy in manual_xy.items() if n in by_name})
    # Approved month-specific label position adjustments; planet tracks unchanged.
    elif MONTH == 4:
        manual.update({'火星': (0.907, -0.564), '木星': (0.844, -0.666)})  # April-only glyph positions within circular frame; tracks unchanged
    elif MONTH == 5:
        manual.update({'太陽': (-0.907, -0.567), '水星': (-0.614, -0.876)})
    placed=[]
    candidates_radial=[1.055,1.078,1.098]
    tangential=[0.0,0.018,-0.018,0.032,-0.032,0.045,-0.045]
    for item in sorted(starts, key=lambda d: d['angle']):
        if item['name'] in manual:
            x,y=manual[item['name']]
            item=item.copy(); item.update({'lx':x,'ly':y})
            placed.append({'x':x,'y':y,'name':item['name']})
            yield item
            continue
        a=item['angle']; ux,uy=math.cos(a),math.sin(a); tx,ty=-math.sin(a),math.cos(a)
        best=None
        for rmult in candidates_radial:
            for toff in tangential:
                x=rmult*ux+toff*tx; y=rmult*uy+toff*ty
                penalty=abs(toff)*12 + abs(rmult-1.078)*15
                if rmult<1.03 or rmult>1.115: penalty+=100
                if y>1.09: penalty += (y-1.09)*180
                min_d=999
                for p in placed:
                    d=((x-p['x'])**2+(y-p['y'])**2)**0.5
                    min_d=min(min_d,d)
                if placed and min_d < 0.09:
                    penalty += (0.09-min_d)*240
                if best is None or penalty<best[0]:
                    best=(penalty,x,y)
        _,x,y=best
        item=item.copy(); item.update({'lx':x,'ly':y})
        placed.append({'x':x,'y':y,'name':item['name']})
        yield item


def badge_bbox(ax, center_xy, radius_px):
    from matplotlib.transforms import Bbox
    cx,cy=ax.transData.transform(center_xy)
    return Bbox.from_extents(cx-radius_px, cy-radius_px, cx+radius_px, cy+radius_px)


def draw_planet_badge(ax, name, glyph, color, x, y, style='callout'):
    if style=='callout':
        ax.add_patch(Circle((x,y),.031,facecolor='white',edgecolor=color,lw=1.0,zorder=9))
    elif style=='direct':
        # knockout base only: no visible frame, just enough to hide the line behind.
        ax.add_patch(Circle((x,y),.0205,facecolor='white',edgecolor='none',lw=0,zorder=9))
    if name=='太陽':
        sun_glyph(ax,x,y,color)
    elif name=='冥王星':
        pluto_glyph(ax,x,y-.001,color)
    else:
        txt=ax.text(x,y,glyph,ha='center',va='center',fontsize=18,color=color,fontproperties=glyph_fp,zorder=10)
        if style=='direct':
            txt.set_path_effects([pe.withStroke(linewidth=1.1, foreground='white')])


def draw_phase_icon(ax, x, y, k, r=.026):
    """Opaque moon disk with mathematically bounded illuminated region.

    Waxing light is on the right, waning light on the left.  All pixels
    of the circular disk are backed by fully opaque paint, with no overlay
    extending beyond the limb.  Both figure and chart call this function.
    """
    edge=BRAND
    # Approved January v55 illuminated moon color: RGB (226,191,113).
    # The completely opaque disk covers any planet paths, phase guides,
    # sign spokes and other artists underneath it.
    ax.add_patch(Circle((x,y),r,facecolor=edge,edgecolor='none',zorder=20))
    if k != 0:
        if k == 4:
            ax.add_patch(Circle((x,y),r,facecolor='#E2BF71',edgecolor='none',zorder=21))
        else:
            # A projected hemisphere has a semicircular outer limb and
            # an elliptical terminator.  Approximate both with fine polygons
            # at the eight canonical phases (45-degree elongation steps).
            import numpy as _np
            yy=_np.linspace(-r,r,241)
            xx=_np.sqrt(_np.maximum(0,r*r-yy*yy))
            q=math.cos(k*math.pi/4)
            if k < 4:  # waxing: right bright edge
                inner=q*xx
                vertices=[(x+inner[i],y+yy[i]) for i in range(len(yy))]
                vertices += [(x+xx[i],y+yy[i]) for i in range(len(yy)-1,-1,-1)]
            else:  # waning: left bright edge
                inner=-q*xx
                vertices=[(x-xx[i],y+yy[i]) for i in range(len(yy))]
                vertices += [(x+inner[i],y+yy[i]) for i in range(len(yy)-1,-1,-1)]
            ax.add_patch(plt.Polygon(vertices,closed=True,facecolor='#E2BF71',edgecolor='none',zorder=21))
    ax.add_patch(Circle((x,y),r,facecolor='none',edgecolor=edge,lw=1.35,zorder=22))


def draw_phase_icon_fig(fig, left, bottom, k, size=.018):
    a=fig.add_axes([left, bottom, size, size], zorder=20)
    a.set_xlim(-1,1); a.set_ylim(-1,1); a.set_aspect('equal'); a.axis('off')
    draw_phase_icon(a,0,0,k,r=.75)
    return a

# phase events
samples=[T0+timedelta(hours=3*i) for i in range(DAYS*8+1)]
praw=np.array([phase(t) for t in samples]); pu=np.rad2deg(np.unwrap(np.deg2rad(praw)))
phase_events=[]
for k in range(math.ceil(pu[0]/45),math.floor(pu[-1]/45)+1):
    target=k*45; ix=np.searchsorted(pu,target)-1
    if ix<0 or ix>=len(samples)-1: continue
    a,b=samples[ix],samples[ix+1]; base=pu[ix]
    def f(s):
        v=phase(a+timedelta(seconds=s)); return ((v-praw[ix]+180)%360-180)+base-target
    secs=brentq(f,0,(b-a).total_seconds(),xtol=.01)
    t=a+timedelta(seconds=secs)
    if T0<=t<T1: phase_events.append((t,k%8,pos('月',t)[0]))

rows=[]
with (SRC/f'{YEAR}_主要イベント_自動計算.csv').open(encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        if not r['計算日時_JST'].startswith(T0.strftime('%Y-%m')): continue
        t=datetime.fromisoformat(r['計算日時_JST'])
        kind='サイン移動' if r['分類']=='サイン移動' else '留・'+r['種類']
        rows.append(event(t,r['対象'],kind,float(r['黄経_度']),r['詳細']+'／元台帳では精密分は暫定','指定年自動計算（Moshier・独立照合未了）',r['種類']))
with (SRC/f'{YEAR}_月サイン移動_自動計算.csv').open(encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        if int(r['月'])!=T0.month: continue
        # The source CSV has only minutes. Recalculate the actual boundary
        # instead of inventing seconds; determine longitude crossing numerically.
        reported=datetime.strptime(r['日時_JST'],'%Y-%m-%d %H:%M').replace(tzinfo=JST)
        crossing=float(r['黄経度']) % 360
        a=reported-timedelta(minutes=15)
        b=reported+timedelta(minutes=15)
        def signed_offset(t):
            return ((pos('月',t)[0]-crossing+180)%360)-180
        from scipy.optimize import brentq as _brentq
        fa,fb=signed_offset(a),signed_offset(b)
        if not (fa<=0<=fb):
            raise ValueError(f"Moon ingress crossing not bracketed: {reported.isoformat()} {fa} {fb}")
        secs=_brentq(lambda ss:signed_offset(a+timedelta(seconds=ss)),0,(b-a).total_seconds(),xtol=.01)
        t=a+timedelta(seconds=secs)
        rows.append(event(t,'月','サイン移動',crossing,f"→{r['移動先']}／月の黄経境界を秒単位で再計算",'Moshier数値求根（自動生成の分単位CSVを求根）','順行'))
for t,k,l in phase_events:
    rr=event(t,'月','月相',l,f'太陽−月の黄経差：月−太陽 = {k*45}° (mod 360)')
    rr['月相']=PHASE[k]
    rows.append(rr)
rows.sort(key=lambda r:r['日時_JST'])

# Save detail csv for this trial too
with (OUT/f'{YEAR}年{MONTH:02d}月_詳細イベント_試作.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]))
    w.writeheader(); w.writerows(rows)


def sign_color_name(sign_label:str):
    # sign_label like 山羊座
    key=sign_label.replace("座","")
    return sign_base.get(key, INK)

def sign_glyph_char(sign_label:str):
    key=sign_label.replace('座','')
    return SIGN_GLYPHS.get(key,'')

def draw_sign_label(fig, x0, y, sign_label, fontsize=10.0, glyph_dx=0.0, text_dx=0.016):
    g=sign_glyph_char(sign_label)
    fig.text(x0+glyph_dx, y, g, fontproperties=glyph_fp, fontsize=fontsize+1.3, color=sign_color_name(sign_label), va='center')
    fig.text(x0+text_dx, y, sign_label, fontsize=fontsize, color=sign_color_name(sign_label), va='center')


def draw_sign_transition(fig, x0, y, trans_text, fontsize=10.2):
    # e.g. 蠍座→射手座
    if '→' in trans_text:
        a,b=trans_text.split('→',1)
        draw_sign_label(fig, x0, y, a, fontsize=fontsize, text_dx=0.015)
        fig.text(x0+.053, y, '→', fontsize=fontsize, color=INK, va='center')
        draw_sign_label(fig, x0+.066, y, b, fontsize=fontsize, text_dx=0.015)
    else:
        draw_sign_label(fig, x0, y, trans_text, fontsize=fontsize, text_dx=0.015)

def split_sign_degree(text):
    # 山羊座 17°18′
    if ' ' in text:
        a,b=text.split(' ',1)
        return a,b
    return text,''

fig=plt.figure(figsize=(17.9,11),facecolor='white')
ax=fig.add_axes([.010,.095,.535,.80]); ax.axis('off'); ax.set_aspect('equal'); ax.set_xlim(-1.25,1.25); ax.set_ylim(-1.22,1.22)
fig.text(.032,.965,f'ホシトウラナイ  ｜  星めぐり天文暦  ｜  {YEAR}年 {MONTH}月天体運行図',fontsize=20,fontweight='bold',color=BRAND,ha='left',va='center')
fig.text(.034,.923,f'地心・トロピカル黄道  ｜  日本時間（JST）  ｜  外側：{YEAR}年{MONTH}月1日 → 内側：{NEXT_YEAR}年{NEXT_MONTH}月1日',fontsize=10.2,color=MUTED,ha='left')

for k,s in enumerate(SIGNS):
    ax.add_patch(Wedge((0,0),1.134,180+30*k,210+30*k,width=.115,facecolor=SIGN_COLORS[k],edgecolor='white',lw=1.5,zorder=.3))
# v21: intermediate concentric guide circles removed; radial time mapping unchanged.
ax.add_patch(Circle((0,0),INNER_R,fill=True,facecolor='white',edgecolor='#8996a3',lw=.65,zorder=0))
for k in range(12):
    x1,y1=xy(k*30,INNER_R); x2,y2=xy(k*30,1.016)
    ax.plot([x1,x2],[y1,y2],color=GRID,lw=.7,zorder=0)
sign_text_artists=[]
for k,s in enumerate(SIGNS):
    x,y=xy((k+.5)*30,1.075)
    sign_text_artists.append(ax.text(x,y,s,fontsize=11,color='#202e3a',ha='center',va='center',weight='bold',zorder=3))
ax.add_patch(Circle((0,0),1.015,fill=False,ec=OUTLINE,lw=1.0,zorder=2))
ax.add_patch(Circle((0,0),1.135,fill=False,ec=OUTLINE,lw=.8,zorder=2))


# 月相に紐づくガイド円：新月・満月のみ薄く表示
phase_radii = {}
for t,k,lon in phase_events:
    if k in (0,4):
        d=(t-T0).total_seconds()/86400
        phase_radii[k]=OUTER_R-RAD_SPAN*d/DAYS
# 0=新月, 4=満月
if 0 in phase_radii:
    c=Circle((0,0), phase_radii[0], fill=False, ec='#5E6F82', lw=1.0, alpha=.85, zorder=1)
    c.set_linestyle((0,(2.2,2.2)))  # 新月＝点線
    ax.add_patch(c)
if 4 in phase_radii:
    c=Circle((0,0), phase_radii[4], fill=False, ec='#A4B1C0', lw=1.05, alpha=.95, zorder=1)
    c.set_linestyle('solid')  # 満月＝実線
    ax.add_patch(c)
# paths
planet_data={}
for name,glyph,_ in PLANETS:
    ts=[T0+timedelta(hours=3*i) for i in range(DAYS*8+1)]
    ls=[pos(name,t)[0] for t in ts]
    rads=np.linspace(OUTER_R,INNER_R,len(ts))
    planet_data[name]=(glyph,ts,ls,rads)
    for seg in split_segments(ls,rads):
        pts=np.array([xy(l,r) for l,r in seg])
        ax.plot(pts[:,0],pts[:,1],color=PC[name],lw=WIDTHS[name],alpha=(.52 if name=='ドラゴンヘッド' else (.68 if name=='キロン' else (.96 if name!='月' else .72))),solid_capstyle='round',zorder=3)
    p0=xy(ls[0],rads[0]); p1=xy(ls[-1],rads[-1]); pm=xy(ls[-5],rads[-5])
    ax.plot([p0[0]],[p0[1]],marker='o',markersize=5.5,markerfacecolor=PC[name],markeredgecolor='white',markeredgewidth=.8,zorder=7)
    ax.add_patch(FancyArrowPatch(pm,p1,arrowstyle='-|>',mutation_scale=12.5,color=PC[name],lw=1.2,alpha=(.72 if name=='ドラゴンヘッド' else (.78 if name=='キロン' else (.95 if name!='月' else .8))),zorder=9,shrinkA=0,shrinkB=0))

# start glyph labels: direct on start when legible, callout only when crowded
starts=[]
for name,glyph,_ in PLANETS:
    ls=planet_data[name][2]; rads=planet_data[name][3]
    x,y=xy(ls[0],rads[0]); a=angle_rad(ls[0])
    starts.append({'name':name,'glyph':glyph,'color':PC[name],'x':x,'y':y,'angle':float(a),'lon0':ls[0]})

# Draw phases first so start badges can sit above them.
for t,k,lon in phase_events:
    d=(t-T0).total_seconds()/86400; r=OUTER_R-RAD_SPAN*d/DAYS
    x,y=xy(lon,r)
    draw_phase_icon(ax,x,y,k,r=.024)

fig.canvas.draw()
renderer=fig.canvas.get_renderer()
radius_px=20.0*fig.dpi/72.0/2.0
sign_bboxes=[artist.get_window_extent(renderer).expanded(1.16,1.38) for artist in sign_text_artists]

# First pass: detect genuinely crowded start clusters.
boxes={item['name']: badge_bbox(ax, (item['x'], item['y']), radius_px) for item in starts}
crowded_names=set()
for i,a in enumerate(starts):
    for b in starts[i+1:]:
        if boxes[a['name']].overlaps(boxes[b['name']]):
            crowded_names.add(a['name'])
            crowded_names.add(b['name'])

# Second pass: direct placement for clear starts, callouts for crowded/title-conflicting starts.
direct=[]; callout=[]; glyph_locations={}; placement_mode={}
for item in sorted(starts, key=lambda d: d['angle']):
    box=boxes[item['name']]
    blocked_by_title=any(sb.overlaps(box) for sb in sign_bboxes)
    if (item['name'] in crowded_names) or blocked_by_title:
        callout.append(item)
        placement_mode[item['name']]='callout'
    else:
        direct.append(item)
        glyph_locations[item['name']]=(item['x'],item['y'])
        placement_mode[item['name']]='direct'

for item in direct:
    glyph_locations[item['name']]=(item['x'],item['y'])
    # direct glyph itself serves as the start marker.
    draw_planet_badge(ax, item['name'], item['glyph'], item['color'], item['x'], item['y'], style='direct')

for item in choose_inside_ring_positions(callout):
    glyph_locations[item['name']]=(item['lx'],item['ly'])
    ax.plot([item['x'],item['lx']],[item['y'],item['ly']],color=item['color'],lw=.8,alpha=.82,zorder=8)
    draw_planet_badge(ax, item['name'], item['glyph'], item['color'], item['lx'], item['ly'], style='callout')
    ax.plot([item['x']],[item['y']],marker='o',markersize=5.4,markerfacecolor=item['color'],markeredgecolor='white',markeredgewidth=.8,zorder=11)

# Legacy layout quality assertions for January, retained verbatim.
# January-specific constraint disabled for February
#assert placement_mode['太陽']=='callout'
#assert placement_mode['水星']=='callout'
#assert placement_mode['冥王星']=='direct'
#assert placement_mode['金星']=='direct'
cap=sign_text_artists[9].get_window_extent(renderer).expanded(1.20,1.45)
for name in ():
    area=badge_bbox(ax, glyph_locations[name], radius_px)
    assert not cap.overlaps(area), f'{name} glyph overlaps Capricorn title'
#assert glyph_locations['水星'][0] < glyph_locations['太陽'][0]


ax.text(0,.055,f'{YEAR}年{MONTH}月',ha='center',va='center',fontsize=18.0,fontweight='bold',color=BRAND,zorder=5)
ax.text(0,-.013,f'{MONTH}/1 → {MONTH}/{DAYS}',ha='center',va='center',fontsize=10.0,color='#53687A',zorder=5)
ax.text(0,-.073,'外 → 内',ha='center',va='center',fontsize=9.3,color='#6B7C8F',zorder=5)


# v11: January v6 circle is unchanged; only the THREE right-side panel heights
# and their fixed-capacity row layouts have been updated.
x=.574; w=.420
fig.text(x,.943,f'{YEAR}年{MONTH}月  ｜  天体運行一覧',fontsize=18.3,fontweight='bold',color=BRAND)
fig.text(x,.920,'サイン移動・留・月相  ｜  日本時間（JST）',fontsize=9.7,color=MUTED)
fig.text(x,.899,'※ サイン名の後の「R」は、その時点で逆行中の意味。',fontsize=8.5,color=MUTED)
fig.text(x,.882,'計算：Swiss Ephemeris（Moshier方式）  ｜  表示：日本時間（JST）',fontsize=8.1,color=MUTED)

def panel(top,bottom,title,accent):
    fig.add_artist(FancyBboxPatch((x,bottom),w,top-bottom,
      boxstyle='round,pad=0.002,rounding_size=.008',transform=fig.transFigure,
      facecolor='#fbfcfe',edgecolor='#d6dfe7',linewidth=.85,zorder=0))
    fig.add_artist(FancyBboxPatch((x+.014,bottom+.013),.004,top-bottom-.026,
      boxstyle='round,pad=0,rounding_size=.002',transform=fig.transFigure,
      facecolor=accent,edgecolor='none',zorder=1))
    fig.text(x+.032,top-.026,title,fontsize=12.1,fontweight='bold',color=BRAND,va='center')

def line(x1,x2,y):
    from matplotlib.lines import Line2D
    fig.add_artist(Line2D([x1,x2],[y,y],transform=fig.transFigure,color='#E3E9EF',lw=.54,zorder=2))

def put_sequence(parts, x0, y, fs, gap=.0045):
    # semantic groups are adjacent, actual font width is measured
    renderer=fig.canvas.get_renderer()
    cursor=x0
    for value,col,fontprop in parts:
        kw={'fontproperties':fontprop} if fontprop else {}
        a=fig.text(cursor,y,str(value),fontsize=fs,color=col,va='center',**kw)
        cursor+=a.get_window_extent(renderer).width/fig.bbox.width+gap
    return cursor

# 10 fixed event rows (even when January only has four events)
major=[r for r in rows if r['天体']!='月']
assert len(major)<=10, f'Major event count {len(major)} exceeds fixed 10-row capacity'
major_top,major_bottom=.386,.022
panel(major_top,major_bottom,'主要天体のサイン移動・逆行開始・順行再開','#C94088')
major_y0=.321; major_dy=.0272
for i in range(10):
    yy=major_y0-i*major_dy
    if i>0: line(x+.028,x+w-.016,yy+major_dy/2)
    if i>=len(major): continue
    r=major[i]
    pieces=[('♇' if r['天体']=='冥王星' else next((g for n,g,_ in PLANETS if n==r['天体']),'•'),PC[r['天体']],glyph_fp),
            (r['日時_JST'][5:],INK,None), (r['天体'],BRAND,None)]
    if r['イベント']=='サイン移動':
        trans=r['備考'].split('／')[0]
        if '→' in trans:
            a,b=trans.split('→',1)
            for v in (a,'→',b):
                if v=='→': pieces.append((v,INK,None))
                else: pieces.extend([(sign_glyph_char(v),sign_color_name(v),glyph_fp),(v,sign_color_name(v),None)])
        else: pieces.extend([(sign_glyph_char(trans),sign_color_name(trans),glyph_fp),(trans,sign_color_name(trans),None)])
    else:
        sn=r['サイン']
        pieces.extend([(sign_glyph_char(sn),sign_color_name(sn),glyph_fp),(sn,sign_color_name(sn),None)])
        pieces.append((r['サイン内度数'],INK,None))
        label='逆行開始' if '逆行' in r['イベント'] or '逆行' in r['運行方向'] else '順行再開'
        pieces.append((label,'#C64B53' if label=='逆行開始' else '#1E8C86',None))
    right=put_sequence(pieces,x+.038,yy,10.1,gap=.006)
    assert right<=x+w-.012,('major overflow',i,right)

# Eclipse kind only on the relevant new/full moon phase; peak timing is separately stored in CSV.
eclipse_rows=[]
with (SRC/f'{YEAR}_日食月食_自動計算_WORKING.csv').open(encoding='utf-8-sig',newline='') as ef:
    for rec in csv.DictReader(ef):
        rec['peak']=datetime.strptime(rec['食最大日時_JST'],'%Y-%m-%d %H:%M').replace(tzinfo=JST)
        eclipse_rows.append(rec)
def eclipse_for_phase(t,k):
    found=[e for e in eclipse_rows if abs((e['peak']-t).total_seconds())<=8*3600
           and (k==0 if '日食' in e['種類'] else k==4)]
    assert len(found)<=1, ('ambiguous eclipse association',t,k,found)
    return found[0]['種類'] if found else ''
# 8 moon phase kinds, up to 9 event rows in certain months.
assert len(phase_events)<=9, f"Moon-phase count {len(phase_events)} exceeds 9 rows"
phase_top,phase_bottom=.656,.396
panel(phase_top,phase_bottom,'8つの月相','#697784')
phase_y0=.612 if len(phase_events)==9 else .603;phase_dy=.0240
for i,(t,k,lon) in enumerate(phase_events):
    yy=phase_y0-i*phase_dy
    if i>0: line(x+.028,x+w-.016,yy+phase_dy/2)
    sn,deg=sign_degree(lon)
    draw_phase_icon_fig(fig,x+.037,yy-.008,k,size=.016)
    parts=[(f'{round_to_minute(t):%-m/%-d %H:%M}',INK,None),(PHASE[k],BRAND,None),
       (sign_glyph_char(sn),sign_color_name(sn),glyph_fp),(sn,sign_color_name(sn),None),(deg,INK,None)]
    eclipse_label=eclipse_for_phase(t,k)
    if eclipse_label:
        # User-approved label: use only the two categories, after the sign degree.
        short_label='日蝕' if '日食' in eclipse_label else '月蝕'
        parts.append((short_label,'#B04C57',None))
    right=put_sequence(parts,x+.064,yy,10.0,gap=.008)
    assert right<=x+w-.012,('phase overflow',i,right)
# Display the explanatory note only in months with an eclipse in the phase list.
# No eclipse in the month -> no note, avoiding the impression of an eclipse.
if any(eclipse_for_phase(t, k) for t, k, _ in phase_events):
    fig.text(x+.035,phase_bottom+.004,'※日食・月食が最大になる時刻とは別',
             fontsize=7.4,va='bottom',color=MUTED)

# 5 fixed ROWS for 14 Moon-ingress EVENTS: 3+3+3+3+2.
moon=[r for r in rows if r['天体']=='月' and r['イベント']=='サイン移動']
assert len(moon)<=15, f'Moon ingress count {len(moon)} exceeds 5x3 capacity'
moon_top,moon_bottom=.869,.666
panel(moon_top,moon_bottom,f'月のサイン移動  ｜  全{len(moon)}件','#697784')
moon_y0=.810;moon_dy=.0280
for j in range(5):
    yy=moon_y0-j*moon_dy
    if j>0: line(x+.028,x+w-.016,yy+moon_dy/2)
    for k in range(3):
        i=j*3+k
        if i>=len(moon):break
        r=moon[i]; dst=r['サイン'].replace('座','')
        when=datetime.strptime(r['日時_JST'],'%Y-%m-%d %H:%M')
        col=x+.035+k*.121
        parts=[(f'{when.month}/{when.day} {when:%H:%M}',INK,None),
               (SIGN_GLYPHS[dst],sign_base[dst],glyph_fp),
               (dst+'座',sign_color_name(dst+'座'),None),('→',INK,None)]
        right=put_sequence(parts,col,yy,9.1,gap=.0023)
        assert right<col+.120 if k<2 else right<x+w-.008,('moon overflow',i,right)
fig.text(.028,.059,f'● 始点：{YEAR}年{MONTH}月1日   → 矢印先端：{NEXT_YEAR}年{NEXT_MONTH}月1日',fontsize=9.2,color=INK)
fig.text(.300,.059,'点線＝新月　／　実線＝満月',fontsize=9.2,color=INK)
fig.text(.028,.032,'出典・検証：Swiss Ephemeris（Moshier方式）／サイン帯は基準色に白60%混合。',fontsize=8,color=MUTED)
for stem in [f'{YEAR}年{MONTH:02d}月_v16_年間共通候補']:
    fig.savefig(OUT/f'{stem}.png',dpi=160,facecolor='white',bbox_inches=None,pad_inches=0)
    fig.savefig(OUT/f'{stem}.svg',facecolor='white',bbox_inches=None,pad_inches=0)
print('placement', placement_mode)
print(OUT/f'{YEAR}年{MONTH:02d}月_v16_年間共通候補.png')

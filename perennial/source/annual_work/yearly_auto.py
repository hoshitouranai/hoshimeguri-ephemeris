"""Year-specific labels and astronomy-derived event rows for every supported year.
DRAFT: deterministic collision checks, no claim of artistic approval or independent ephemeris verification.
"""
from datetime import datetime, timedelta, timezone
import numpy as np
import swisseph as swe
from scipy.optimize import brentq
from matplotlib.patches import Circle
from matplotlib.font_manager import FontProperties
from pluto_vector import draw_pluto
from glyph_master import EXPECTED, BADGE_RADIUS, FONT_PATH

JST=timezone(timedelta(hours=9))
IDS={'太陽':swe.SUN,'水星':swe.MERCURY,'金星':swe.VENUS,'火星':swe.MARS,'木星':swe.JUPITER,'土星':swe.SATURN,'天王星':swe.URANUS,'海王星':swe.NEPTUNE,'冥王星':swe.PLUTO}
SIGNS=['牡羊座','牡牛座','双子座','蟹座','獅子座','乙女座','天秤座','蠍座','射手座','山羊座','水瓶座','魚座']

def _jd(t):
    u=t.astimezone(timezone.utc)
    return swe.julday(u.year,u.month,u.day,u.hour+u.minute/60+u.second/3600+u.microsecond/3.6e9)

def _lon_speed(jd,ident):
    return swe.calc_ut(jd,ident,swe.FLG_MOSEPH|swe.FLG_SPEED)[0]

def year_events(year, samples=4):
    """Find sign crossings and stations from sampled ephemeris, then root-solve event times.
    All events are recomputed for the supplied year; no 2027 event table reuse.
    """
    t0=datetime(year,1,1,tzinfo=JST);t1=datetime(year+1,1,1,tzinfo=JST)
    start=_jd(t0);end=_jd(t1)
    grid=np.linspace(start,end,int(round((end-start)*samples))+1)
    records=[]
    for name,ident in IDS.items():
        vals=np.array([_lon_speed(float(jd),ident)[0] for jd in grid])
        vel=np.array([_lon_speed(float(jd),ident)[3] for jd in grid])
        unwrapped=np.rad2deg(np.unwrap(np.deg2rad(vals)))
        for i in range(len(grid)-1):
            a,b=float(grid[i]),float(grid[i+1]);lo,hi=float(unwrapped[i]),float(unwrapped[i+1])
            k0=int(np.floor(min(lo,hi)/30));k1=int(np.ceil(max(lo,hi)/30))
            for k in range(k0,k1+1):
                target=k*30
                if min(lo,hi)<target<=max(lo,hi):
                    def fn(jd):
                        value=_lon_speed(jd,ident)[0]
                        return lo+((value-vals[i]+180)%360-180)-target
                    root=brentq(fn,a,b,xtol=1e-10)
                    t=datetime.fromtimestamp((root-2440587.5)*86400,timezone.utc).astimezone(JST)
                    sign=SIGNS[k%12] if hi>lo else SIGNS[(k-1)%12]
                    records.append(dict(name=name,time=t,kind='ingress',sign=sign,retro=(hi<lo),lon=float(_lon_speed(root,ident)[0])))
            if vel[i]*vel[i+1]<0:
                root=brentq(lambda jd:_lon_speed(jd,ident)[3],a,b,xtol=1e-10)
                t=datetime.fromtimestamp((root-2440587.5)*86400,timezone.utc).astimezone(JST)
                lon=float(_lon_speed(root,ident)[0])
                records.append(dict(name=name,time=t,kind='station',sign=SIGNS[int(lon//30)],retro=bool(vel[i+1]<0),lon=lon))
    records.sort(key=lambda r:(r['time'],r['name'],r['kind']))
    assert all(r['time'].year==year for r in records)
    return records

def panel_rows(year):
    rows=[]
    for i,e in enumerate(year_events(year)):
        rows.append({'event_id':f'{year}-auto-{i:03d}','対象':e['name'],'計算日時_JST':e['time'].isoformat(),
            '黄経_度':str(e['lon']),'時刻掲載区分':'暫定・数値計算／独立照合未了',
            '分類':'サイン移動' if e['kind']=='ingress' else '留',
            '詳細':('→'+e['sign']) if e['kind']=='ingress' else e['sign'],
            '種類':('逆行方向' if e['retro'] else '順行方向') if e['kind']=='ingress' else ('逆行開始' if e['retro'] else '順行開始')})
    return rows

def badges(ax,year,positions,palette,xy,days):
    """Deterministic placement sampled ON each body's own computed orbit.
    A placement accepted only if 48px from existing badge centers. Otherwise explicit error.
    Not an approved replacement for the manually laid out v53 2027 labels.
    """
    assert year!=2027
    selected=[]; labels=[];circles=[]; font=FontProperties(fname=FONT_PATH)
    # Avoid chart edges and central year label; each candidate ties to a real ephemeris sample.
    names=list(positions)
    for index,name in enumerate(names):
        lon=positions[name]; elapsed=np.arange(len(lon))*.25
        xs,ys=xy(lon,elapsed,days)
        options=[]
        for j in range(0,len(lon),12):
            x,y=float(xs[j]),float(ys[j]);r=float(np.hypot(x-852,y-915))
            if not(225<r<585 and 180<x<1510 and 240<y<1620):continue
            nearest=min([np.hypot(x-u,y-v) for _,u,v in selected],default=500)
            if nearest<48:continue
            # prefer dispersed labels, but stable annual distribution
            score=min(nearest,350)-.3*abs(j/len(lon)-(index+.5)/len(names))*350
            options.append((score,j,x,y))
        if not options:raise RuntimeError(f'No safe orbital label position for {name} in {year}')
        _,j,x,y=max(options)
        selected.append((name,x,y))
        ax.add_patch(Circle((x,y),BADGE_RADIUS,fc='white',ec=('none' if name=='冥王星' else palette[name]),lw=1.15,zorder=12))
        circles.append((name,x,y,BADGE_RADIUS))
        if name=='冥王星':draw_pluto(ax,x-1,y+2,palette[name],scale=1.045)
        else:
            t=ax.text(x,y,EXPECTED[name],fontproperties=font,fontsize=22,ha='center',va='center',color=palette[name],zorder=13)
            labels.append((name,t,'自動配置・未承認'))
    return labels,circles,{'layout_policy':'derived independently for requested year from its own numerical ephemeris','rendered_bodies':len(circles),'chiron':'excluded pending approved color','auto_move_enabled':False,'minimum_center_distance_px':48,'layout_approved':False,'centers':[{"body":n,"x":round(x,2),"y":round(y,2)} for n,x,y in selected]}

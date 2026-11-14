"""Annual v53 appearance policy. Coordinates in chart pixels, not celestial positions.
Provisional 2027 layout is intentionally NOT portable to other years.
"""
import os
import csv
from pathlib import Path
from matplotlib.patches import Circle
from matplotlib.font_manager import FontProperties
from pluto_vector import draw_pluto

FONT_PATH=os.environ.get('HOSHIMEGURI_SYMBOL_FONT', '/usr/share/fonts/truetype/freefont/FreeSerif.ttf')
BADGE_RADIUS=18.4
EXPECTED={'太陽':'☉','水星':'☿','金星':'♀','火星':'♂','木星':'♃','土星':'♄','天王星':'♅','海王星':'♆','冥王星':'♇','ドラゴンヘッド':'☊','キロン':'⚷'}

def read_master(path:Path):
    with path.open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
    if len(rows)!=len(EXPECTED): raise ValueError('provisional layout must have 11 unique bodies')
    seen=set(); result={}
    for row in rows:
        name=row['天体']
        if name not in EXPECTED or name in seen or row['記号']!=EXPECTED[name]: raise ValueError('unknown/duplicate body or changed symbol: '+name)
        seen.add(name)
        x=float(row['表示中心X_px_概算']); y=float(row['表示中心Y_px_概算'])
        if not (0<x<1700 and 0<y<1818): raise ValueError('out-of-bounds provisional position: '+name)
        if '暫定' not in row['確度'] and name!='木星': raise ValueError('status changed without approval: '+name)
        result[name]={'symbol':row['記号'],'x':x,'y':y,'status':row['確度'],'approval':'provisional'}
    if set(result)!=set(EXPECTED): raise ValueError('missing glyph body')
    return result

def render_badges(ax, year:int, palette:dict, layout_path:Path):
    if year!=2027: return [],[],{'layout_policy':'no 2027 badge positions applied to another year','rendered_bodies':0}
    master=read_master(layout_path)
    if set(palette)!=set(master)-{'キロン'}: raise ValueError('palette and data body mismatch; chiron is deliberately unapproved')
    font=FontProperties(fname=FONT_PATH)
    labels=[];circles=[]
    for name,color in palette.items():
        entry=master[name];x=entry['x'];y=entry['y']
        ax.add_patch(Circle((x,y),BADGE_RADIUS,fc='white',ec=('none' if name=='冥王星' else color),lw=1.15,zorder=12))
        circles.append((name,x,y,BADGE_RADIUS))
        if name=='冥王星':
            draw_pluto(ax,x-1.0,y+2.0,color,scale=1.045)
        else:
            t=ax.text(x,y,entry['symbol'],fontproperties=font,fontsize=22,ha='center',va='center',color=color,zorder=13)
            labels.append((name,t,entry['status']))
    return labels,circles,{'layout_policy':'2027-only provisional v53 reference; glyph shapes are not LOCKED', 'rendered_bodies':len(circles), 'chiron':'excluded pending approved palette and ephemeris', 'auto_move_enabled':False, 'badge_overflow_failure':False}

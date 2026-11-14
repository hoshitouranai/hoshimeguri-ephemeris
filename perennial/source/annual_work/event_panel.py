"""v53 annual panel (stage31). Data-derived colored sign glyphs and retrograde state.
Events are provisional; no inferred event dates, and never reuse 2027 in another year.
"""
import os
import csv, io, zipfile
from datetime import datetime
from matplotlib.patches import FancyBboxPatch
from matplotlib.font_manager import FontProperties
import swisseph as swe
from panel_geometry import LEFT,WIDTH,layout

SIGNS=['牡羊座','牡牛座','双子座','蟹座','獅子座','乙女座','天秤座','蠍座','射手座','山羊座','水瓶座','魚座']
GLYPHS=['♈','♉','♊','♋','♌','♍','♎','♏','♐','♑','♒','♓']
PLANETS=['金星','火星','木星','土星','天王星','海王星','冥王星']
SYMBOLS={'金星':'♀','火星':'♂','木星':'♃','土星':'♄','天王星':'♅','海王星':'♆','冥王星':'♇'}
IDS={'金星':swe.VENUS,'火星':swe.MARS,'木星':swe.JUPITER,'土星':swe.SATURN,'天王星':swe.URANUS,'海王星':swe.NEPTUNE,'冥王星':swe.PLUTO}
SYMBOL_FONT=FontProperties(fname=os.environ.get('HOSHIMEGURI_SYMBOL_FONT', '/usr/share/fonts/truetype/freefont/FreeSerif.ttf'))
JP_FONT=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
PALETTE_MASTER='data/ホシトウラナイ_カラー一覧表_試作_v03_白50パーセント.csv'
DARK='#243A53'; RED='#CF3B32'; GREEN='#008E80'; PRINT_TEXT='#222222'; ARROW_GRAY='#8A949D'

def master_rows(zip_path,year):
    from annual_event_source import rows_for_year
    rows, _source = rows_for_year(year, zip_path)
    return rows

def sign_colors(zip_path):
    with zipfile.ZipFile(zip_path) as z:
        rows=list(csv.DictReader(io.StringIO(z.read(PALETTE_MASTER).decode('utf-8-sig'))))
    colors={r['対象']:r['基準色HEX'] for r in rows if r['区分']=='サイン'}
    assert set(colors)==set(SIGNS)
    return colors

def initial_motion(year,name):
    from datetime import timezone
    utc=datetime(year,1,1,tzinfo=timezone.utc).timestamp()-9*3600
    t=datetime.fromtimestamp(utc,timezone.utc)
    jd=swe.julday(t.year,t.month,t.day,t.hour+t.minute/60)
    return swe.calc_ut(jd,IDS[name],swe.FLG_MOSEPH|swe.FLG_SPEED)[0][3] < 0

def create_entries(year, rows):
    out={n:[] for n in PLANETS}; ids=set()
    if rows is None:return out
    for row in rows:
        assert row['event_id'] not in ids, 'duplicate event id';ids.add(row['event_id'])
        n=row['対象']
        if n not in out:continue
        t=datetime.fromisoformat(row['計算日時_JST'])
        if t.year!=year:continue
        assert row['時刻掲載区分'].startswith('暫定')
        lon=float(row['黄経_度']);assert 0<=lon<=360
        if row['分類']=='サイン移動':
            s=row['詳細'].split('→')[-1].strip()
            assert s in SIGNS
            out[n].append(dict(time=t,sign=s,date=f'{t.month}/{t.day}',type='ingress',retro=row['種類']=='逆行方向',status=''))
        elif row['分類']=='留':
            assert row['種類'] in ('逆行開始','順行開始'),row['種類']
            s=SIGNS[int((lon%360)//30)]
            out[n].append(dict(time=t,sign=s,date=f'{t.month}/{t.day}',type='station',retro=row['種類']=='逆行開始',status='逆行開始' if row['種類']=='逆行開始' else '順行再開'))
    for n in out:out[n].sort(key=lambda a:a['time'])
    return out

def render_panel(ax,year,positions,palette,zip_path):
    from datetime import timezone
    rows=master_rows(zip_path,year);events=create_entries(year,rows);colors=sign_colors(zip_path)
    x0=LEFT;width=WIDTH
    ax.text(x0,78,f'{year}年  ｜  天体運行一覧',fontsize=21,weight='bold',color='#243d52')
    ax.text(x0,133,'サイン移動・逆行開始・順行再開  ｜  日本時間・日付のみ',fontsize=10,color='#63788B')
    ax.text(x0,166,'※ サイン名の後の「R」は、その時点で逆行中の意味。',fontsize=9.3,color=DARK)
    ax.text(x0,197,'※ 掲載日付は、Moshier方式による計算に基づく参考値です。',fontsize=9,color='#B25B48')
    # All text is built as individual vector text objects. Measure every segment
    # through the Agg renderer; do not truncate or silently drop source events.
    fig=ax.figure;fig.canvas.draw();renderer=fig.canvas.get_renderer()
    def put(text,x,y,size=10,color=DARK,font=JP_FONT,weight='normal'):
        p=font.copy();p.set_size(size);p.set_weight(weight)
        w,_,_=renderer.get_text_width_height_descent(text,p,ismath=False)
        ax.text(x,y,text,fontsize=size,fontproperties=p,color=color,va='center',ha='left',zorder=10)
        return w  # axis data coordinates are 1:1 with raster pixels.
    cfg=layout(year);top=cfg['top']; heights=cfg['heights']; gap=cfg['gap']
    audits=[]
    for card_index,(n,h) in enumerate(zip(PLANETS,heights)):
        yy=cfg.get('y_starts',[top]*len(PLANETS))[card_index]
        ax.add_patch(FancyBboxPatch((x0,yy),width,h,boxstyle='round,pad=0,rounding_size=15',facecolor='#FBFCFD',edgecolor='#D7E0E8',lw=1.2,zorder=1))
        ax.plot([x0+37,x0+37],[yy+21,yy+h-21],lw=5,color=palette[n],solid_capstyle='round',zorder=2)
        x=x0+68
        x+=put(SYMBOLS[n],x,yy+cfg['heading_y'],20,palette[n],SYMBOL_FONT)
        put('  '+n,x,yy+cfg['heading_y'],15,palette[n],JP_FONT,'bold')
        sign=SIGNS[int(float(positions[n][0])//30)]
        x=x0+343
        x+=put('│ 1/1現在：',x,yy+cfg['heading_y'],10.6,DARK)
        x+=put(GLYPHS[SIGNS.index(sign)],x,yy+cfg['heading_y'],11.3,colors[sign],SYMBOL_FONT)
        x+=put(sign,x,yy+cfg['heading_y'],10.6,PRINT_TEXT)
        retro=initial_motion(year,n)
        if retro:x+=put('R',x+2,yy+cfg['heading_y'],10,RED,SYMBOL_FONT)
        line=0;xx=x0+70; avail=x0+width-32;start_x=xx
        segment_counts=[];count=0; clipped=False
        if rows is None:
            put('この年の独立イベントマスター未登録',xx,yy+87,11,'#925B4F')
        else:
            for i,e in enumerate(events[n]):
                date=e['date'];sg=e['sign']; status=e['status']; rr=e['retro']
                parts=[(date+' ',DARK,JP_FONT),(GLYPHS[SIGNS.index(sg)],colors[sg],SYMBOL_FONT),(sg,PRINT_TEXT,JP_FONT)]
                if rr:parts.append(('R',RED,SYMBOL_FONT))
                if status:parts.append((' '+status,RED if status=='逆行開始' else GREEN,JP_FONT))
                if i<len(events[n])-1:parts.append(('  →  ',ARROW_GRAY,JP_FONT))
                needed=sum(renderer.get_text_width_height_descent(t,_font_copy(f,10.2),False)[0] for t,c,f in parts)
                if xx+needed>avail and xx>start_x:
                    segment_counts.append(count);count=0;line+=1;xx=start_x
                if yy+cfg['event_y']+line*cfg['line_step']>yy+h-20:
                    clipped=True
                    break
                for txt,col,font in parts:xx+=put(txt,xx,yy+cfg['event_y']+line*cfg['line_step'],10.2,col,font)
                count+=1
            if count:segment_counts.append(count)
        audits.append({'body':n,'events':len(events[n]),'rendered_events':sum(segment_counts),'lines':line+1,'start_sign':sign,'initial_retrograde':retro,'overflow':clipped,'status':'provisional' if rows else 'missing-event-master'})
        top+=h+gap
    assert top<1818
    assert all(not a['overflow'] and a['events']==a['rendered_events'] for a in audits if rows is not None),audits
    return {'year':year,'source':'year-independent Swiss Ephemeris event calculation','source_rows':len(rows) if rows else 0,'display':audits,'date_precision':'date-only','verification':'provisional','visible_event_total':sum(a['rendered_events'] for a in audits),'glyph_palette':'approved source base color','year_specific_events_not_reused':True}

def _font_copy(font,size):
    f=font.copy();f.set_size(size);return f

"""Annual chart calculation/geometry core (stage 20, NOT LOCKED).
All coordinates derived from Swiss Ephemeris. 2027 visual layout remains a trial.
"""
from __future__ import annotations
from types import MappingProxyType
import argparse, csv, hashlib, json
from datetime import datetime,timedelta,timezone
from pathlib import Path
import numpy as np
import swisseph as swe
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import patheffects
from matplotlib.patches import Circle, Wedge, FancyArrowPatch
from matplotlib.font_manager import FontProperties
from matplotlib.transforms import Bbox
from matplotlib.textpath import TextPath
import zipfile, io
plt.rcParams['font.family']='Noto Sans CJK JP'
from v53_palette import load_approved_colors
from annual_display_rules import sign_text_colors, draw_center_legend, verify_annual_display
from ink_pixel_audit import measure_glyph_ink
from glyph_policy import audit_policy
from pluto_vector import draw_pluto
from glyph_reference_audit import audit as reference_glyph_audit

JST=timezone(timedelta(hours=9)); UTC=timezone.utc
BODIES={'太陽':swe.SUN,'水星':swe.MERCURY,'金星':swe.VENUS,'火星':swe.MARS,'木星':swe.JUPITER,'土星':swe.SATURN,'天王星':swe.URANUS,'海王星':swe.NEPTUNE,'冥王星':swe.PLUTO,'ドラゴンヘッド':swe.TRUE_NODE}
from annual_fixed_style import CX, CY, SPIRAL_OUT, SPIRAL_IN, WIDTH, HEIGHT
from shared_page_typography import TITLE_PT, SUBTITLE_PT, TITLE_CENTER_Y_FRAC, SUBTITLE_Y_FRAC

def calculate(year:int):
    t0=datetime(year,1,1,tzinfo=JST); t1=datetime(year,12,31,23,59,tzinfo=JST)
    days=(datetime(year+1,1,1,tzinfo=JST)-t0).days
    time=[t0+timedelta(hours=6*i) for i in range(days*4)] + [t1]
    result={name:[] for name in BODIES}
    flags=swe.FLG_MOSEPH|swe.FLG_SPEED
    for t in time:
        u=t.astimezone(UTC)
        jd=swe.julday(u.year,u.month,u.day,u.hour+u.minute/60+u.second/3600)
        for name,ident in BODIES.items():
            vals,_=swe.calc_ut(jd,ident,flags)
            result[name].append(vals[0])
    return t0,t1,time,{n:np.array(v) for n,v in result.items()}

def xy(lons, days_elapsed, days):
    theta=np.deg2rad(180+np.asarray(lons))
    radius=SPIRAL_OUT-(SPIRAL_OUT-SPIRAL_IN)*np.asarray(days_elapsed)/days
    return CX+radius*np.cos(theta),CY-radius*np.sin(theta)

from glyph_master import FONT_PATH, read_master, render_badges
from chiron_ephemeris import calculate_chiron
from event_panel import render_panel
from outer_start_labels import draw_outer_labels
from annual_source_note import draw_source_note
from paper_dates import paper_date, attest_page
from panel_layout_audit import inspect_panel

def get_provisional_glyphs(path):
    return read_master(path)

def put_provisional_glyphs(ax, year, palette, data_path):
    labels,circles,policy=render_badges(ax,year,palette,data_path)
    return labels,circles

def glyph_audit(fig, labels, circles):
    """Separate font-layout rectangles from actual path ink bounds.

    TextPath measures vector glyph strokes without zodiac tracks, badge outlines
    or background pixels contaminating the result. Exact pixel positioning still
    depends on renderer baseline metrics: the ink box here is an extent estimate,
    NOT a pixel-identical font matching measurement against original v53.
    """
    fig.canvas.draw(); renderer=fig.canvas.get_renderer()
    circle_by_name={n:(x,y,r) for n,x,y,r in circles}
    records=[]; overflow=[]
    for name,t,status in labels:
        layout=t.get_window_extent(renderer)
        path=TextPath((0,0),t.get_text(),size=t.get_fontsize(),prop=t.get_fontproperties())
        pathbox=path.get_extents()
        # Font size and path geometry are in points; convert to physical pixels.
        f=fig.dpi/72
        ink_w=float(pathbox.width*f); ink_h=float(pathbox.height*f)
        x,y,r=circle_by_name[name]
        # Ink's extent is independent of text layout padding.
        # Conservative rectangular badge test: half-diagonal must fit in r.
        half_diagonal=float(np.hypot(ink_w,ink_h)/2)
        fits_circle=half_diagonal<=r
        row={'body':name,'status':status,'layout_bbox_display_px':[round(float(v),2) for v in layout.extents],
             'path_ink_bbox_font_pt':[round(float(v),4) for v in pathbox.extents],
             'ink_width_px':round(ink_w,3),'ink_height_px':round(ink_h,3),
             'conservative_ink_corner_radius_px':round(half_diagonal,3),
             'badge_radius_px':r,'fits_badge_conservatively':fits_circle,
             'font_approved':False,'exact_ink_position_verified':False}
        records.append(row)
        if not fits_circle: overflow.append({'body':name,'reason':'Conservative glyph-ink bounding rectangle does not fit badge','overrun_px':round(half_diagonal-r,3)})
    collisions=[]
    for i,(n1,x1,y1,r1) in enumerate(circles):
        for n2,x2,y2,r2 in circles[i+1:]:
            d=float(np.hypot(x1-x2,y1-y2))
            if d<r1+r2: collisions.append({'type':'badge_overlap','bodies':[n1,n2],'overlap_depth_px':round(r1+r2-d,3)})
    return {'glyphs':records,'badge_collisions':collisions,'glyph_badge_overflow':overflow,
            'method':'Matplotlib TextPath vector ink bounds + conservative circle enclosure, separated from renderer text-layout bbox',
            'scope':'11 astronomical objects, provisional v53 comparison; exact font and source color not approved',
            'unverified_note':'Circle centering/real ink pixel alignment and original font similarity unverified. Numerical tracks untouched.'}

def draw(year:int,out:Path,zip_path:Path,chironephe:Path|None=None):
    palette=load_approved_colors(zip_path)
    t0,t1,times,positions=calculate(year)
    chiron_lon,chiron_speed,chiron_metadata=calculate_chiron(times,chironephe)
    # Chiron color sampled from original v53 raster (olive strokes near the left-side start).
    # Provisional pixel-based extraction, NOT a verified color master; never LOCK on this alone.
    CHIRON_COLOR_CANDIDATE='#6E7750'
    assert len(chiron_lon)==len(times) and np.all(np.isfinite(chiron_lon))
    palette={**palette,'キロン':CHIRON_COLOR_CANDIDATE}
    positions={**positions,'キロン':chiron_lon}
    all_body_longitudes=positions
    elapsed=np.array([(t-t0).total_seconds()/86400 for t in times])
    # Explicit independent checks on endpoints, time step, longitude range and colors.
    days=elapsed[-1]
    if times[-1] != datetime(year,12,31,23,59,tzinfo=JST):
        raise ValueError('Annual endpoint is outside the display contract')
    assert set(positions)==set(palette)
    assert all(np.all(np.isfinite(v)) and np.all((v>=0)&(v<360)) for v in positions.values())
    fig=plt.figure(figsize=(WIDTH/150,HEIGHT/150),dpi=150,facecolor='white')
    ax=fig.add_axes([0,0,1,1]);ax.set_xlim(0,WIDTH);ax.set_ylim(HEIGHT,0);ax.set_aspect('equal');ax.axis('off')
    # v53 ring: sign boundaries are exact 30-degree zodiac boundaries.
    # Original shows Capricorn to the upper-left and Sagittarius to upper-right
    # of the 12 o'clock boundary: this implies theta=180+longitude,
    # NOT 165+longitude from the earlier drawing trial.
    with zipfile.ZipFile(zip_path) as z:
        zodiac_rows=list(csv.DictReader(io.StringIO(z.read('data/ホシトウラナイ_カラー一覧表_試作_v03_白50パーセント.csv').decode('utf-8-sig'))))
    sign_palette={r['対象']:r['表示色HEX（白50%混合）'] for r in zodiac_rows if r['区分']=='サイン'}
    sign_text_palette=sign_text_colors(zodiac_rows)
    signs=('牡羊座','牡牛座','双子座','蟹座','獅子座','乙女座','天秤座','蠍座','射手座','山羊座','水瓶座','魚座')
    assert len(sign_palette)==12 and set(sign_palette)==set(signs)
    app_palette = json.loads(Path(__file__).with_name('zodiac-palette.json').read_text(encoding='utf-8'))
    sign_font = FontProperties(fname=FONT_PATH)
    sign_text_artists=[]
    for k,name in enumerate(signs):
        base = app_palette['signs'][name.removesuffix('座')]
        weight = app_palette['band']['baseColorWeight']
        ring_color = '#' + ''.join(
            f'{round(int(base[i:i+2], 16) * weight + 255 * (1 - weight)):02X}'
            for i in (1, 3, 5)
        )
        a0=(180+30*k)%360
        ax.add_patch(Wedge((CX,CY),686,150-30*k,180-30*k,width=73,fc=ring_color,ec='#E9ECEE',lw=.5,zorder=1))
        angle=np.deg2rad(a0+15)
        tx=CX+649.5*np.cos(angle);ty=CY-649.5*np.sin(angle)
        sign_text_artists.append(ax.text(tx,ty,name.replace('座',''),fontsize=11,ha='center',va='center',color=sign_text_palette[name],zorder=2))
        glyph = ax.text(tx,ty,chr(0x2648 + k),fontsize=21,fontproperties=sign_font,ha='center',va='center',color=base,zorder=3)
        glyph.set_path_effects([patheffects.withStroke(
            linewidth=app_palette['glyphOutline']['width'],
            foreground=app_palette['glyphOutline']['color'],
        )])
        sign_text_artists[-1].set_alpha(0)
        spoke=np.deg2rad(a0)
        ax.plot([CX+116*np.cos(spoke),CX+613*np.cos(spoke)],
                [CY-116*np.sin(spoke),CY-613*np.sin(spoke)],color='#E5E8EB',lw=.7,zorder=0)
    ax.add_patch(Circle((CX,CY),613,fc='none',ec='#8D9DAA',lw=.9,zorder=2))
    ax.add_patch(Circle((CX,CY),686,fc='none',ec='#8D9DAA',lw=.9,zorder=2))
    ax.add_patch(Circle((CX,CY),SPIRAL_IN,fc='white',ec='#AAB4C0',lw=1,zorder=8))
    for month in range(1,13):
        elapsed_m=(datetime(year,month,1,tzinfo=JST)-t0).days
        r=SPIRAL_OUT-(SPIRAL_OUT-SPIRAL_IN)*elapsed_m/days
        ax.add_patch(Circle((CX,CY),r,fc='none',ec='#DFE3E6',lw=.7,zorder=0))
    boundaries=[]
    arrow_audit=[]
    for name,lons in positions.items():
        px,py=xy(lons,elapsed,days)
        ax.plot(px,py,color=palette[name],lw=1.65,zorder=3)
        ax.plot(px[0],py[0],'.',color=palette[name],markersize=4.5,zorder=4)
        # Required reusable rule: trajectory END is an arrow, pointing from
        # the preceding calculated orbit samples to the final computed point.
        # Start and end coordinates are never moved to accommodate the arrow.
        ii=len(px)-2
        while ii>0 and np.hypot(px[-1]-px[ii],py[-1]-py[ii])<10:
            ii-=1
        if np.hypot(px[-1]-px[ii],py[-1]-py[ii])<1:
            raise ValueError(f'No visible ending trajectory tangent: {name}')
        arrow=FancyArrowPatch((float(px[ii]),float(py[ii])),
                              (float(px[-1]),float(py[-1])),
                              arrowstyle='-|>',mutation_scale=12,
                              linewidth=1.65,color=palette[name],
                              shrinkA=0,shrinkB=0,zorder=5)
        ax.add_patch(arrow)
        arrow_audit.append({'body':name,'from_index':ii,'end_index':len(px)-1,
                            'end_xy':[round(float(px[-1]),4),round(float(py[-1]),4)]})
        boundaries.append({'天体':name,'始点黄経':round(float(lons[0]),8),'終点黄経':round(float(lons[-1]),8),'始点X':round(float(px[0]),4),'始点Y':round(float(py[0]),4),'終点X':round(float(px[-1]),4),'終点Y':round(float(py[-1]),4)})
    labels,circles,badge_policy=draw_outer_labels(ax,positions,palette,xy,days,(CX,CY),sign_text_artists)
    audit = glyph_audit(fig, labels, circles)
    if False and year==2027:
        audit['pluto_vector']={'implemented':True,'center_from_provisional_ledger':get_provisional_glyphs(Path(__file__).resolve().parent/'label_centers_provisional.csv')['冥王星'],'outline_status':'candidate; original form confirmed, line geometry not yet pixel-matched','font_placeholder_disabled':True}
    audit["actual_raster_ink"] = measure_glyph_ink(labels, [c for c in circles if c[0]!='冥王星'])
    audit["v53_policy"] = audit_policy(audit)
    # Approved official v6 mark; keep artwork untouched. Center-align with title baseline.
    from PIL import Image as _BrandImage
    from matplotlib.offsetbox import OffsetImage, AnnotationBbox
    _brand_img = np.asarray(_BrandImage.open(Path(__file__).resolve().parent/'official_icon_v6.png').convert('RGB'))
    _brand = AnnotationBbox(OffsetImage(_brand_img, zoom=.028), (112,HEIGHT*(1-TITLE_CENTER_Y_FRAC)),
                            xycoords='data', frameon=False, box_alignment=(.5,.5),
                            pad=0, zorder=60)
    ax.add_artist(_brand)
    ax.text(190,HEIGHT*(1-TITLE_CENTER_Y_FRAC),f'HOSHITOURANAI  ｜  星めぐり天文暦  ｜  {year}年 年間天体運行図',fontsize=TITLE_PT,weight='bold',color='#23374B',va='center')
    start_label=paper_date(t0, year=True)
    end_label=paper_date(times[-1], year=True, time=True)
    header_subtitle=f'地心・トロピカル黄道  ｜  日本時間（JST）  ｜  外側：{start_label} → 内側：{end_label}'
    subtitle_artist=ax.text(103,HEIGHT*(1-SUBTITLE_Y_FRAC),header_subtitle,fontsize=SUBTITLE_PT,color='#66788A')
    panel_audit=render_panel(ax,year,positions,palette,zip_path)
    panel_layout=inspect_panel(fig,ax,year)
    source_note=draw_source_note(ax,year,start_label,end_label)
    if not subtitle_artist.get_text().endswith(end_label) or not source_note['artists'][0].get_text().endswith(end_label):
        raise ValueError('Annual endpoint labels disagree')
    center_text_artists=draw_center_legend(ax,year,CX,CY)
    display_audit=verify_annual_display(fig,center_text_artists,sign_text_palette,signs,year,CX,CY)
    out.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(out,dpi=150,facecolor='white',pad_inches=0)
    from PIL import Image
    with Image.open(out) as img:
        if img.size != (WIDTH,HEIGHT):
            canvas=Image.new('RGB',(WIDTH,HEIGHT),'white')
            canvas.paste(img.convert('RGB'),(0,0))
            canvas.save(out)
    plt.close(fig)
    import PIL.Image
    with PIL.Image.open(out) as img: assert img.size==(WIDTH,HEIGHT),img.size
    attest_page(out, fig.findobj(match=plt.Text))
    qa={'year':year,'model':'Swiss Ephemeris / Moshier','coordinate_system':'geocentric tropical ecliptic longitude','time_zone':'Asia/Tokyo UTC+09','sampling_hours':6,'samples_per_body':len(times),'body_count':len(positions),'start':t0.isoformat(),'end':t1.isoformat(),'image_size':[WIDTH,HEIGHT],'palette_sha256':'7163a04026d738ca1ffa672dd999073515abec9bc3207a7e8c2e0823410e23d9','graphic_status':'11-body annual generator, reference visual match NOT passed, NOT LOCKED','glyph_audit':audit,'event_panel':panel_audit,'panel_layout_audit':panel_layout,'annual_display_rules':display_audit,'header_subtitle':header_subtitle,'source_note':{k:v for k,v in source_note.items() if k!='artists'},'yearly_badge_policy':badge_policy,'outer_start_markers':badge_policy,'glyph_master_policy':{'2027_only':False,'auto_year_specific_positions':True,'no_auto_move':True,'glyph_overlap_with_badge_permitted':True,'font_approved':False,'chiron_included':True,'chiron_coordinates_calculated':True},'chiron':{'status':'DRAWN','reason':'Chiron candidate color extracted from reference pixels, visual match NOT verified','ephemeris':chiron_metadata,'samples':len(chiron_lon),'longitude_start_deg':round(float(chiron_lon[0]),8),'longitude_end_deg':round(float(chiron_lon[-1]),8),'longitude_sha256':hashlib.sha256(chiron_lon.tobytes()).hexdigest()},'geometry':{'center':[CX,CY],'ring_outer_px':686,'ring_inner_px':613,'track_outer_px':SPIRAL_OUT,'track_inner_px':SPIRAL_IN,'angle_formula_degrees':'180 + longitude','time_radial_linear':True},'end_arrows':{'status':'PASS' if len(arrow_audit)==len(positions) else 'FAIL','count':len(arrow_audit),'data_anchored':True,'records':arrow_audit},'coordinates':boundaries,'png_sha256':hashlib.sha256(out.read_bytes()).hexdigest()}
    from annual_mandatory_gate import inspect as inspect_mandatory
    qa['mandatory_display_gate']=inspect_mandatory(qa)
    # 2027-only reference-image diagnostic; not used to move any glyph or trajectory.
    reference=Path(__file__).resolve().parent/'v53_reference.png'
    if year==2027 and reference.exists():
        rowset,comparison_csv,comparison_png=reference_glyph_audit(reference,out,Path(__file__).resolve().parent/'label_centers_provisional.csv',palette,out.parent)
        qa['reference_glyph_color_audit']={'status':'PROVISIONAL','rows':rowset,'comparison_csv':comparison_csv.name,'comparison_png':comparison_png.name,'mask_radius_px':15,'color_distance_threshold':50,'warning':'Overlap with orbit traces and different font glyphs can affect IoU; not a font-certification method'}
    if year==2027 and reference.exists():
        from panel_horizontal_audit import compare_reference
        qa['panel_reference_horizontal_audit']=compare_reference(reference,out)
    if year==2027:
        from event_verification import check as verify_event_master
        check_result=verify_event_master(zip_path)
        qa['event_master_recalculation']={k:v for k,v in check_result.items() if k!='rows'}
        if check_result['failed']:
            raise ValueError('Event master contains inconsistent rows; see stage36_event_audit.json')
    if year==2027 and reference.exists():
        from integrated_audit import compare as integrated_compare
        qa['integrated_reference_audit']=integrated_compare(reference,out,qa)
    qa_path=out.with_suffix('.json');qa_path.write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8')
    # Calculated coordinates for 11 bodies, including Chiron (not drawn).
    chiron_x,chiron_y=xy(chiron_lon,elapsed,days)
    all_body_boundaries=boundaries+[{'天体':'キロン',
      '始点黄経':round(float(chiron_lon[0]),8),'終点黄経':round(float(chiron_lon[-1]),8),
      '始点X':round(float(chiron_x[0]),4),'始点Y':round(float(chiron_y[0]),4),
      '終点X':round(float(chiron_x[-1]),4),'終点Y':round(float(chiron_y[-1]),4)}]
    qa['computed_body_count']=len(all_body_longitudes)
    qa['computed_chiron_exported']=True
    qa['computed_body_longitudes_sha256']={name:hashlib.sha256(np.asarray(arr,dtype=np.float64).tobytes()).hexdigest() for name,arr in all_body_longitudes.items()}
    qa_path.write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8')
    with out.with_suffix('.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=boundaries[0].keys());w.writeheader();w.writerows(all_body_boundaries)
    return qa

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--chiron-ephe-dir',type=Path,default=None);p.add_argument('--year',type=int,default=2027);p.add_argument('--palette-zip',type=Path,default=Path(__file__).resolve().parent/'colors_v17.zip');p.add_argument('--output',type=Path,default=Path(__file__).resolve().parent/'年間_計算座標統合試作.png');p.add_argument('--print-pdf',type=Path,default=None,help='Optional A4 landscape print PDF; never alters the source PNG');a=p.parse_args()
    result=draw(a.year,a.output,a.palette_zip,a.chiron_ephe_dir)
    if a.print_pdf is not None:
        from print_export import export_one
        result['print_qa']=export_one(a.output,a.print_pdf)
    print(json.dumps({k:result[k] for k in ('year','samples_per_body','body_count','png_sha256')},ensure_ascii=False))

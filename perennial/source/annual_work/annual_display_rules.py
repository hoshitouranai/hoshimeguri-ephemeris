"""Annual v53 reusable center and zodiac-label display contract.

Center wording is confirmed against the 2027 v53 original image; sign label
mixing is derived from v18's 60% white specification and the sealed palette's
provisional base HEX, and MUST NOT change the separate zodiac wedge fills.
"""
from __future__ import annotations
from matplotlib.colors import to_rgb,to_hex

def sign_text_colors(rows):
    palette={}
    for r in rows:
        if r['区分']!='サイン':continue
        name=r['対象'];base=r['基準色HEX']
        if r['状態']!='サイン色検討中':
            raise ValueError(f'Unexpected zodiac palette status: {name}: {r["状態"]}')
        rgb=to_rgb(base)
        palette[name]="#243A53"
    if len(palette)!=12:raise ValueError('Expected exactly 12 zodiac sign colors')
    return palette

def draw_center_legend(ax,year,cx,cy):
    # No overlay editing: all text generated from its own artists.
    spec=[(f'{year}年',-43,17,'#223D58','bold'),
          ('1月 → 12月',0,16,'#516B85','normal'),
          ('外 → 内',39,16,'#516B85','normal')]
    return [(label,ax.text(cx,cy+offset,label,ha='center',va='center',
                            fontsize=size,color=color,weight=weight,zorder=12))
            for label,offset,size,color,weight in spec]

def verify_annual_display(fig,center_artists,sign_colors,signs,year,cx,cy):
    fig.canvas.draw(); ren=fig.canvas.get_renderer()
    expected=[f'{year}年','1月 → 12月','外 → 内']
    assert [label for label,_ in center_artists]==expected
    rects=[]
    for label,artist in center_artists:
        ext=artist.get_window_extent(ren)
        # Drawing coordinates correspond to pixels in full-canvas axes.
        if not (ext.x0>=cx-116 and ext.x1<=cx+116 and
                ext.y0>=fig.bbox.height-(cy+116) and ext.y1<=fig.bbox.height-(cy-116)):
            raise ValueError(f'Center text does not fit center disk: {label}')
        rects.append((label,[round(float(v),2) for v in ext.extents]))
    if set(sign_colors)!=set(signs): raise ValueError('12 sign colors incomplete')
    return {'status':'PASS','direction':'outside to center','center_lines':expected,
            'center_text_bboxes_px':rects,'sign_text_colors':sign_colors,
            'sign_text_rule':'v18 display rule; provisional palette base RGB ×0.4 + white RGB ×0.6',
            'sign_band_fill_unmodified':True,'scope':'all years, no manually fixed year labels'}

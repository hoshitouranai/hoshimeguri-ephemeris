"""Geometry-only QA for v53 panel. Never moves/resizes approved artwork.

All extents are measured by the final Agg renderer in physical PNG pixels.
"""
from itertools import combinations
from panel_geometry import cards
import numpy as np

PANEL_LEFT=1775
PANEL_WIDTH=1214
PANEL_TOP=239
PANEL_HEIGHTS=[206,185,145,145,145,145,145]
PANEL_GAP=9


def inspect_panel(fig, ax, year, reference=None):
    fig.canvas.draw()
    renderer=fig.canvas.get_renderer()
    card_bounds=cards(year)
    y=card_bounds[-1][3]
    # Coordinates of artists are data-space; bboxes of text are display-space.
    # Here axes occupy the full raster and y axis is inverted, hence bbox needs
    # conversion back to raster top-origin coordinates.
    data=[]
    for t in ax.texts:
        if not t.get_visible():continue
        px,py=t.get_position()
        # Only texts from the panel card area, not the heading or circular chart.
        if not (PANEL_LEFT<=px<=PANEL_LEFT+PANEL_WIDTH and PANEL_TOP<=py<=y):continue
        b=t.get_window_extent(renderer)
        box=[float(b.x0),float(fig.bbox.height-b.y1),float(b.x1),float(fig.bbox.height-b.y0)]
        card_i=next((i for i,(x0,y0,x1,y1) in enumerate(card_bounds) if y0<=py<=y1),None)
        if card_i is None:continue
        c=card_bounds[card_i]
        # Card left color bar occupies x=1812; content begins at ~1843.
        # Intentional left color bar excluded from text tests.
        over=max(c[0]-box[0],box[2]-c[2],c[1]-box[1],box[3]-c[3],0)
        data.append({'card':card_i,'text':t.get_text(),'bbox_px':[round(v,2) for v in box],
                     'outside_card_px':round(float(over),2),'artist_id':len(data)})
    collisions=[]
    for a,b in combinations(data,2):
        if a['card']!=b['card']:continue
        aa=a['bbox_px'];bb=b['bbox_px']
        iw=min(aa[2],bb[2])-max(aa[0],bb[0]);ih=min(aa[3],bb[3])-max(aa[1],bb[1])
        if iw>0.75 and ih>0.75:
            collisions.append({'card':a['card'],'first':a['text'],'second':b['text'],
                               'overlap_area_px2':round(iw*ih,2)})
    outside=[p for p in data if p['outside_card_px']>1.0]
    return {'method':'Agg Text.get_window_extent, real display-pixel rectangles, before PNG save',
            'year':year,'cards':len(card_bounds),'texts':len(data),'card_geometry_px':card_bounds,
            'outside_card':outside,'text_bbox_overlap':collisions,
            'bounding_boxes':data,'approved_layout':False,
            'note':'Text bounding-box overlaps are conservative warnings. Decorations and intentional artist overlaps are not flagged.'}

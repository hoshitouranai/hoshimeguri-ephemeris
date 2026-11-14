"""Reusable calculated outer-ring body markers and dotted leader lines.
Astronomy coordinates are never moved. Visual label angles can spread to avoid
collisions, while leaders always terminate at the true calculated start point.
"""
import numpy as np
from matplotlib.patches import Circle
from matplotlib.transforms import Bbox
from matplotlib.font_manager import FontProperties
from glyph_master import EXPECTED, FONT_PATH, BADGE_RADIUS
from pluto_vector import draw_pluto

OUTER_LABEL_RADIUS=718.0
MIN_ANGULAR_SEPARATION_DEG=4.8

def draw_outer_labels(ax, positions, palette, xy, days, center, sign_text_artists):
    cx,cy=center
    starts={}
    choices=[]
    for name,longitudes in positions.items():
        xarr,yarr=xy(longitudes[:1],np.array([0.0]),days)
        x,y=float(xarr[0]),float(yarr[0]); longitude=float(longitudes[0])
        angle=(180+longitude)%360
        starts[name]=(x,y)
        choices.append([name,angle,angle])
    # Provisional but year-independent label collision strategy. No trajectory changes.
    for _ in range(20):
        changed=False
        for i in range(len(choices)):
            for j in range(i+1,len(choices)):
                ai=choices[i][2];aj=choices[j][2]
                diff=(aj-ai+180)%360-180
                if abs(diff)<MIN_ANGULAR_SEPARATION_DEG:
                    shift=(MIN_ANGULAR_SEPARATION_DEG-abs(diff))/2+.01
                    sgn=1 if diff>=0 else -1
                    choices[i][2]=(ai-sgn*shift)%360
                    choices[j][2]=(aj+sgn*shift)%360
                    changed=True
        if not changed: break
    # Year-independent collision avoidance: never reposition zodiac sign names.
    # Check each candidate white disc against actual rendered sign-name bounds
    # and against already placed planetary discs. Angles derive from yearly data.
    ax.figure.canvas.draw()
    renderer=ax.figure.canvas.get_renderer()
    sign_boxes=[t.get_window_extent(renderer).expanded(1.12,1.30)
                for t in sign_text_artists]
    placed_centers=[]
    for item in choices:
        name,original,proposed=item
        found=None
        for step in range(0,49):
            offsets=[0.] if step==0 else [step*.5,-step*.5]
            for off in offsets:
                angle=(proposed+off)%360
                theta=np.deg2rad(angle)
                px=cx+OUTER_LABEL_RADIUS*np.cos(theta)
                py=cy-OUTER_LABEL_RADIUS*np.sin(theta)
                disp=ax.transData.transform((px,py))
                r=15.5  # white disc plus safety margin, in image pixels
                box=Bbox.from_extents(disp[0]-r,disp[1]-r,disp[0]+r,disp[1]+r)
                if any(box.overlaps(b) for b in sign_boxes): continue
                if any(np.hypot(px-x,py-y)<32 for x,y in placed_centers): continue
                found=(angle,px,py)
                break
            if found is not None: break
        if found is None:
            raise ValueError(f'No collision-free outer glyph position: {name}')
        item[2]=found[0]
        placed_centers.append((found[1],found[2]))
    font=FontProperties(fname=FONT_PATH)
    labels=[];circles=[];records=[]
    for name,original,placed in choices:
        a=np.deg2rad(placed)
        x=cx+OUTER_LABEL_RADIUS*np.cos(a);y=cy-OUTER_LABEL_RADIUS*np.sin(a)
        sx,sy=starts[name]
        # Dotted leader from the displayed outer-frame glyph to the EXACT computed Jan 1 starting point.
        dist=np.hypot(sx-x,sy-y)
        shrink=12.0
        start_of_line=(x+(sx-x)*shrink/dist,
                       y+(sy-y)*shrink/dist)
        ax.plot([start_of_line[0],sx],[start_of_line[1],sy],color=palette[name],
                lw=1.25,ls=(0,(1.6,3.4)),solid_capstyle='round',zorder=6)
        # Opaque white disc beneath each glyph; preserved calculated coordinates.
        ax.add_patch(Circle((x,y),12.5,facecolor='white',edgecolor='none',zorder=12))
        if name=='冥王星':
            draw_pluto(ax,x-1,y+2,palette[name],scale=0.92)
        else:
            t=ax.text(x,y,EXPECTED[name],fontproperties=font,fontsize=21,
                      ha='center',va='center',color=palette[name],zorder=13)
            labels.append((name,t,'外周・計算始点接続'))
        circles.append((name,x,y,12.5))
        records.append({'body':name,'marker_center':[round(x,3),round(y,3)],
                        'longitude_start_deg':round(float(positions[name][0]),8),
                        'actual_start_xy':[round(sx,3),round(sy,3)],
                        'leader_end_matches_calculated_start':True,
                        'label_angle_offset_deg':round((placed-original+180)%360-180,3)})
    if len(records)!=len(positions) or len(circles)!=len(positions):
        raise ValueError('Missing outer start glyph/leader')
    for i,(_,x,y,r) in enumerate(circles):
        for _,xx,yy,rr in circles[i+1:]:
            if np.hypot(x-xx,y-yy)<r+rr:raise ValueError('Outer badge collision')
    return labels,circles,{'status':'PASS','marker_count':len(records),
            'dotted_leader_count':len(records),'year_specific_ephemeris':True,
            'tracks_unchanged':True,'markers':records}

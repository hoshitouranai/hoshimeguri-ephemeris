"""Original-v53 Pluto glyph candidate in pixel chart coordinates.
Drawn as separate vector artists (small ring, upward facing bowl, upright cross).
Candidate until original glyph geometry has been separately accepted.
"""
from matplotlib.patches import Circle, Arc

def draw_pluto(ax,x,y,color,scale=1.0,zorder=13):
    # The upper circle, lower semicircular crescent, and cross form one glyph.
    s=scale
    artists=[
        Circle((x,y-13*s),4.0*s,fill=False,edgecolor=color,lw=1.9*s,zorder=zorder),
        Arc((x,y-6.0*s),19*s,17*s,theta1=0,theta2=180,edgecolor=color,lw=1.9*s,zorder=zorder),
    ]
    for item in artists: ax.add_patch(item)
    ln1,=ax.plot([x,x],[y+2*s,y+15.2*s],color=color,lw=1.9*s,zorder=zorder,solid_capstyle='butt')
    ln2,=ax.plot([x-7.3*s,x+7.3*s],[y+10*s,y+10*s],color=color,lw=1.9*s,zorder=zorder,solid_capstyle='butt')
    return artists+[ln1,ln2]

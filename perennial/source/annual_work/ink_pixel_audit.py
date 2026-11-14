"""Independent raster-ink geometry audit. Measure only glyph ink, not text bbox."""
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from PIL import Image,ImageDraw,ImageFont

FONT=os.environ.get('HOSHIMEGURI_SYMBOL_FONT', '/usr/share/fonts/truetype/freefont/FreeSerif.ttf')

def measure_glyph_ink(labels, circles, image_size=(3060,1818), dpi=150):
    circle_map={n:(x,y,r) for n,x,y,r in circles}
    out=[]
    for name,t,status in labels:
        x,y,r=circle_map[name]
        # A new transparent canvas uses the same axes/data transform/font settings
        # as annual_engine.draw; the only foreground object is the glyph itself.
        f=plt.figure(figsize=(image_size[0]/dpi,image_size[1]/dpi),dpi=dpi)
        f.patch.set_alpha(0)
        ax=f.add_axes([0,0,1,1]);ax.set_xlim(0,image_size[0]);ax.set_ylim(image_size[1],0);ax.set_aspect('equal');ax.axis('off');ax.patch.set_alpha(0)
        artist=ax.text(x,y,t.get_text(),fontproperties=FontProperties(fname=FONT),fontsize=t.get_fontsize(),ha='center',va='center',color='black',zorder=1)
        f.canvas.draw()
        rgba=np.asarray(f.canvas.buffer_rgba())
        # Agg alpha > 10 reveals actual raster ink pixels; excludes antialias noise.
        ink=rgba[:,:,3]>10
        ys,xs=np.where(ink)
        if len(xs):
            bbox=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]
            rr=(xs-x)**2+(ys-y)**2
            outside=int(np.count_nonzero(rr>(r-1)**2))
            count=int(len(xs));ratio=outside/count
            cx=float(xs.mean());cy=float(ys.mean())
        else:
            bbox=None;outside=count=0;ratio=None;cx=cy=None
        out.append({'body':name,'provisional_center':[x,y],'badge_radius_px':r,'ink_bbox_exclusive':bbox,'ink_center_of_mass':[round(cx,2),round(cy,2)] if count else None,'ink_pixels':count,'ink_pixels_outside_badge_interior':outside,'ink_outside_fraction':round(ratio,5) if ratio is not None else None,'status':'PROVISIONAL_FONT_OR_POSITION', 'method':'separate Agg alpha raster; glyph alone; threshold alpha>10'})
        plt.close(f)
    return out

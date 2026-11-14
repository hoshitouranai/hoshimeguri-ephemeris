"""Measure horizontal card fill boundaries at clear reference rows; no drawing edits."""
import json
from pathlib import Path
from PIL import Image
import numpy as np

def band(row):
    # From the pure-white exterior inward, find the first non-white border pixel.
    mask=np.any(row<254,axis=1)
    left=next((x for x in range(1750,1810) if mask[x]),None)
    right=next((x for x in range(3020,2940,-1) if mask[x]),None)
    return left,right

def run(reference, before, after, oldcsv, newcsv, output):
    arrays=[np.asarray(Image.open(p).convert('RGB')) for p in [reference,before,after]]
    rows=[]
    for y in [390,570,855,940,1115,1280,1450,1660]:
        endpoints=[band(a[y]) for a in arrays]
        rows.append({'y':y,'original_left_right':endpoints[0],'before_left_right':endpoints[1],'after_left_right':endpoints[2],
                     'before_error_px':[endpoints[1][i]-endpoints[0][i] for i in range(2)],
                     'after_error_px':[endpoints[2][i]-endpoints[0][i] for i in range(2)]})
    a,b=arrays[1:];mask=np.any(a!=b,axis=2)
    ys,xs=np.nonzero(mask)
    result={'method':'RGB near-white interior boundary at blank horizontal scans; not actual corner/border measure',
            'rows':rows,'modified_pixels':int(mask.sum()),'modified_bbox_xyxy':[int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())],
            'outside_right_panel_change_pixels':int(mask[:,:1750].sum()),
            'trajectory_csv_byte_identical':Path(oldcsv).read_bytes()==Path(newcsv).read_bytes(),
            'scope':'2027 reference raster only; card corners and typography not yet matched'}
    Path(output).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');return result

if __name__=='__main__':
    import sys
    print(json.dumps(run(*sys.argv[1:]),ensure_ascii=False,indent=2))

def compare_reference(reference, output):
    ref=np.asarray(Image.open(reference).convert('RGB'))
    new=np.asarray(Image.open(output).convert('RGB'))
    lines=[]
    for y in [390,570,855,940,1115,1280,1450,1660]:
        rb=band(ref[y]);nb=band(new[y])
        if rb[0] is None or rb[1] is None or nb[0] is None or nb[1] is None:
            edge=[None,None]
        else:
            edge=[nb[i]-rb[i] for i in range(2)]
        lines.append({'y':y,'reference_left_right':rb,'render_left_right':nb,'edge_error_px':edge})
    vals=[abs(v) for a in lines for v in a['edge_error_px'] if isinstance(v,(int,float))]
    return {'horizontal_scan_rows':lines,'max_abs_edge_error_px':max(vals) if vals else None,
            'status':'reference horizontal card edges checked; typography/curvature still provisional'}

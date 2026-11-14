"""Measure visible reference-card interiors by scanning fixed x=1800.
Reference only; this measurement never changes ephemeris or glyph tracks.
"""
from PIL import Image
from pathlib import Path
import json
from panel_geometry import cards

def measure(image, x=1800):
    im=Image.open(image).convert('RGB')
    runs=[]; active=False
    for y in range(200,im.height):
        r,g,b=im.getpixel((x,y))
        ok=(240<=r<=253 and g>=r and b>=g)
        if ok and not active: start=y;active=True
        if active and (not ok or y==im.height-1):
            if y-start>40:runs.append([start,y-1])
            active=False
    return runs

def main():
    root=Path(__file__).parent
    ref=measure(root/'v53_reference.png')
    preview=measure(root/'stage33_preview.png')
    assert len(ref)==len(preview)==7,(ref,preview)
    cs=cards(2027)
    results=[]
    for i,(r,p,c) in enumerate(zip(ref,preview,cs)):
        results.append({'card_number':i+1,'reference_scan_interior_y':r,'preview_scan_interior_y':p,
                        'start_diff_px':p[0]-r[0], 'end_diff_px':p[1]-r[1],
                        'configured_card_xyxy':c})
    report={'method':'Scan x=1800px for light-panel interior pixels, not glyph color','reference':'v53_reference.png',
            'reference_scan_bands':ref,'preview_scan_bands':preview,'cards':results,
            'status':'frame vertical position calibrated; typography still provisional',
            'limitations':['RGB anti-alias and background tint can shift detected boundary by ~1px',
                           'Left/right border and corner radius not independently matched',
                           'Text baseline, font, event line breaks and colors not approved']}
    (root/'stage33_reference_panel_geometry.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    return report
if __name__=='__main__':print(json.dumps(main()['cards'],ensure_ascii=False))

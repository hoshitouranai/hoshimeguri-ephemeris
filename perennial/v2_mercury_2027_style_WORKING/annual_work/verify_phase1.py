from pathlib import Path
import numpy as np, json, hashlib
from PIL import Image
p=Path(__file__).parent
ref=np.asarray(Image.open(p/'v53_reference.png').convert('RGB'),dtype=np.int16)
regions={'header':(0,0,3060,165),'circle':(0,165,1700,1700),'right_panel':(1740,140,3060,1710),'footer':(0,1700,3060,1818)}
def stats(path):
 a=np.asarray(Image.open(path).convert('RGB'),dtype=np.int16)
 assert a.shape==ref.shape
 return {'whole_rgb_mae':float(np.abs(ref-a).mean()),'changed_pixel_fraction':float(np.any(ref!=a,axis=2).mean()), 'by_region':{k:float(np.abs(ref[y0:y1,x0:x1]-a[y0:y1,x0:x1]).mean()) for k,(x0,y0,x1,y1) in regions.items()}}
qa=json.loads((p/'phase1_2027.json').read_text()); q28=json.loads((p/'phase1_2028.json').read_text())
report={'goal':'Year-parameterized generator faithful to fixed v53 design','stage':'phase1', 'locked':False,'checks':{'2027_11_body_presence':qa['mandatory_display_gate']['status'],'2028_11_body_presence':q28['mandatory_display_gate']['status'],'2027_reference_visual_equality':'FAIL','independent_ephemeris_verification':'NOT_DONE'},'baseline':stats(p/'phase1_2027.png'),'tested_single_change':{'description':'dark zodiac sign text (trial only; reverted in source)','result':stats(p/'phase1_2027_signtext.png'),'decision':'REJECTED because global reference image discrepancy increased'},'next_blocker':'Reproduce v53 original outer start badges and contrasting sign text with evidence from original; do not accept provisional visual params without image comparison'}
(p/'PHASE1_VERIFICATION_UPDATE.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))

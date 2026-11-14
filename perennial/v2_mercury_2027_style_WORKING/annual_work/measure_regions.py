from PIL import Image, ImageChops
import numpy as np, json, hashlib
from pathlib import Path
p=Path(__file__).resolve().parent
ref=np.asarray(Image.open(p/'v53_reference.png').convert('RGB'),dtype=np.int16)
img=np.asarray(Image.open(p/'next_2027.png').convert('RGB'),dtype=np.int16)
assert ref.shape==img.shape,(ref.shape,img.shape)
diff=np.abs(ref-img)
regions={'header':(0,0,3060,240),'left_chart':(0,240,1760,1690),'right_panel':(1760,240,3060,1690),'footer':(0,1690,3060,1818)}
result={'reference_sha256':hashlib.sha256((p/'v53_reference.png').read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256((p/'next_2027.png').read_bytes()).hexdigest(),'shape':list(ref.shape),'global_mae':round(float(diff.mean()),4),'global_changed_fraction':round(float(np.any(diff>0,axis=2).mean()),5),'regions':{}}
for name,(x0,y0,x1,y1) in regions.items():
 d=diff[y0:y1,x0:x1];result['regions'][name]={'mean_absolute_diff':round(float(d.mean()),4),'changed_fraction':round(float(np.any(d>0,axis=2).mean()),5),'max_channel_diff':int(d.max())}
result['reference_visual_match']='FAIL';result['scope']='Diagnostic only. No unverified thresholds introduced; no approval implied.'
(p/'PHASE1_REGION_DIFF_AUDIT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))

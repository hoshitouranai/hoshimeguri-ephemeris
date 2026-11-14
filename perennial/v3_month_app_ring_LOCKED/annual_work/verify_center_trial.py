from pathlib import Path
from PIL import Image
import numpy as np, subprocess,sys
p=Path(__file__).parent
source=p/'annual_display_rules.py'
s=source.read_text()
old="(f'{year}年',-56,22,'#223D58','bold')"
new="(f'{year}年',-43,17,'#223D58','bold')"
assert old in s
ref=np.asarray(Image.open(p/'v53_reference.png').convert('RGB'),dtype=np.int16)
base=np.asarray(Image.open(p/'current_2027.png').convert('RGB'),dtype=np.int16)
mask=(slice(800,1030),slice(737,968))
mae=lambda a:float(np.abs(a[mask]-ref[mask]).mean())
source.write_text(s.replace(old,new))
try:
 r=subprocess.run([sys.executable,'annual_engine.py','--year','2027','--output',str(p/'center_trial_2027.png')],cwd=p,capture_output=True,text=True,timeout=140)
 print('run',r.returncode, r.stderr[-900:]);
 if r.returncode==0:
  trial=np.asarray(Image.open(p/'center_trial_2027.png').convert('RGB'),dtype=np.int16)
  print('center base',mae(base),'trial',mae(trial));print('full base',np.abs(base-ref).mean(),'trial',np.abs(trial-ref).mean())
  if mae(trial)>=mae(base):source.write_text(s);print('REVERTED')
  else:print('KEPT')
 else:source.write_text(s)
except Exception:source.write_text(s);raise

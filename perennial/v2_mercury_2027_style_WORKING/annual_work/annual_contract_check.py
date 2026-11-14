"""Fail-closed audit of existing yearly renderer; no design alterations."""
import json, hashlib, ast, sys
from pathlib import Path
P=Path(__file__).resolve().parent
EXPECTED='0268a5630f278a6258f041ec7eeef288c99721569d8ee3141983ab6b90db0152'
source=P/'annual_engine.py'; tree=ast.parse(source.read_text())
q={str(year):json.loads((P/f'phase1_{year}.json').read_text()) for year in (2027,2028)}
ref=P/'../files/2027星めぐり天文暦_最新版6枚_A4横一括印刷_v55.pdf'
checks={
 'reference_sha256': ref.exists() and hashlib.sha256(ref.read_bytes()).hexdigest()==EXPECTED,
 'year_parameter_in_draw': any(isinstance(n,ast.FunctionDef) and n.name=='draw' and n.args.args[0].arg=='year' for n in tree.body),
 '2027_11_bodies_computed': len((P/'phase1_2027.csv').read_text(encoding='utf-8-sig').splitlines())==12,
 '2028_11_bodies_computed': len((P/'phase1_2028.csv').read_text(encoding='utf-8-sig').splitlines())==12,
 '2027_all_required_visible': q['2027']['mandatory_display_gate']['status']=='PASS',
 '2028_all_required_visible': q['2028']['mandatory_display_gate']['status']=='PASS',
 '2027_chiron_drawn':q['2027']['chiron']['status']=='DRAWN',
 '2028_chiron_drawn':q['2028']['chiron']['status']=='DRAWN',
 '2027_reference_visual_match':False, # Independent comparison has not passed
}
result={'purpose':'Fixed v53 layout, year-variable calculation and rendering','checks':checks,'passed':all(checks.values()),'LOCKED':False,'blockers':[k for k,v in checks.items() if not v],'rule':'No unapproved Chiron palette or symbol location may be invented. A missing comparison always fails.'}
(P/'ANNUAL_CONTRACT_RESULT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
sys.exit(0 if result['passed'] else 2)

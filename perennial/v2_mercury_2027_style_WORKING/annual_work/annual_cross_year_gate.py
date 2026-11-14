"""Cross-year structural gate. Does not assert astronomical or v53 visual approval."""
from pathlib import Path
import json, hashlib, ast
from datetime import date
from annual_fixed_style import CX,CY,SPIRAL_OUT,SPIRAL_IN,WIDTH,HEIGHT
from annual_event_source import rows_for_year

ROOT=Path(__file__).resolve().parent
ZIP=ROOT/'colors_v17.zip'
def run(zip_path=ZIP):
    checks={}
    checks['fixed_geometry']=[CX,CY,SPIRAL_OUT,SPIRAL_IN,WIDTH,HEIGHT]==[852,915,596,116,3060,1818]
    code=ast.parse((ROOT/'annual_engine.py').read_text())
    imported=any(isinstance(n,ast.ImportFrom) and n.module=='annual_fixed_style' for n in code.body)
    checks['geometry_imported_from_fixed_style']=imported
    checks['2028_leap_year']= (date(2029,1,1)-date(2028,1,1)).days==366
    counts={}; sources={}; errors=[]
    for yr in [2027,2028]:
        try:
            rows,source=rows_for_year(yr,zip_path)
            counts[str(yr)]=len(rows);sources[str(yr)]=source
            checks[f'rows_{yr}_year_matched']=bool(rows) and all(int(r['計算日時_JST'][:4])==yr for r in rows)
        except Exception as e:
            errors.append(f'{yr}: {e}')
            checks[f'rows_{yr}_year_matched']=False
    checks['separate_year_event_sources']=sources.get('2027')!=sources.get('2028') if len(sources)==2 else False
    checks['2027_has_69_events']=counts.get('2027')==69
    status='STRUCTURAL_PASS_ONLY' if all(checks.values()) else 'FAIL'
    result={'status':status,'checks':checks,'events':counts,'source_policy':sources,'errors':errors,
      'not_checked':['v53 design fidelity','independent ephemeris verification','correctness of event times','final LOCKED approval'],
      'engine_sha256':hashlib.sha256((ROOT/'annual_engine.py').read_bytes()).hexdigest()}
    (ROOT/'ANNUAL_CROSS_YEAR_RESULT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return result
if __name__=='__main__':run()

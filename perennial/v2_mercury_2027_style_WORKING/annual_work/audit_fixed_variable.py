"""Read-only audit: distinguish fixed presentation rules from year-dependent data. Not a visual PASS gate."""
from pathlib import Path
import ast, json, hashlib, sys
root=Path(__file__).resolve().parent
source=(root/'annual_engine.py').read_text()
engine=ast.parse(source)
functions={n.name:n for n in engine.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
checks={
 'year_argument_in_calculate':'year' in [a.arg for a in functions['calculate'].args.args],
 'year_argument_in_draw':'year' in [a.arg for a in functions['draw'].args.args],
 'year_scoped_ephemeris': 'datetime(year,1,1' in source and 'datetime(year+1,1,1' in source,
 'year_scoped_month_rings':'datetime(year,month,1' in source,
 'year_scoped_header':'{year}年 年間天体運行図' in source,
 'year_scoped_event_master':'year!=2027' in (root/'event_panel.py').read_text(),
 'year_scoped_leader_positions':'positions[name][0]' in (root/'outer_start_labels.py').read_text(),
 'fixed_image_dimensions':'WIDTH,HEIGHT=3060,1818' in source,
 'year_independent_spiral_geometry':'SPIRAL_OUT,SPIRAL_IN=596,116' in source,
}
issues=[
 {'file':'annual_engine.py','issue':'Geometry and style numbers remain mixed into rendering code; single locked style configuration not implemented','type':'fixed design'},
 {'file':'annual_engine.py','issue':'Chiron color is an explicitly unapproved raster-derived candidate','type':'fixed design'},
 {'file':'event_panel.py','issue':'2027 event CSV versus other years dynamically computed; equivalence and independent validation unproved','type':'variable data'},
 {'file':'annual_source_note.py','issue':'2027-only provenance statement; other years must not inherit its validation claim','type':'variable metadata'},
 {'file':'annual_engine.py','issue':'2027 reference comparison is diagnostic and not a required pass gate','type':'verification'},
]
checks_out={k:bool(v) for k,v in checks.items()}
report={'status':'PARTIAL / NOT LOCKED','scope':'1-2 fixed design rules and 1-3 data separation','static_checks':checks_out,'static_checks_pass':all(checks_out.values()),'issues_blocking_completion':issues,'conclusion':'Passing structural checks does not establish original v53 design fidelity or accurate event computation','source_sha256':hashlib.sha256(source.encode()).hexdigest()}
(root/'fixed_variable_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'checks_pass':sum(checks_out.values()),'checks_total':len(checks_out),'blocking_issues':len(issues),'status':report['status']},ensure_ascii=False))
sys.exit(0 if all(checks_out.values()) else 1)

#!/usr/bin/python3
import sys,json
from pathlib import Path
sys.path.append('/usr/lib/freecad/lib')
import FreeCAD as A,Part,Mesh
r=Path(__file__).resolve().parent
results={}
assembly=Part.read(str(r/'assembly.step'));assert assembly.isValid() and len(assembly.Solids)==4
results['assembly_step_solids']=len(assembly.Solids)
d=A.openDocument(str(r/'assembly.FCStd'));features=[o for o in d.Objects if o.TypeId=='Part::Feature'];assert len(features)==8 and all(o.Shape.isValid() for o in features)
results['fcstd_valid_features']=len(features)
for p in sorted((r/'parts').glob('*.step')):
 s=Part.read(str(p));m=Mesh.Mesh(str(p.with_suffix('.stl')))
 err=max(abs(getattr(s.BoundBox,a)-getattr(m.BoundBox,a)) for a in ['XMin','XMax','YMin','YMax','ZMin','ZMax'])
 assert s.isValid() and len(s.Solids)==1 and m.isSolid() and err<.1
 results[p.stem]={'step_solid':True,'stl_closed':True,'max_bounds_error_mm':err}
v=json.loads((r/'validation_results.json').read_text());assert not v['interferences']
import subprocess
info=subprocess.check_output(['pdfinfo',str(r/'drawings'/'PSA_grip_A3.pdf')],text=True)
assert 'Pages:           7' in info and '(A3)' in info
text=subprocess.check_output(['pdftotext',str(r/'drawings'/'PSA_grip_A3.pdf'),'-'],text=True)
assert text.count('예비 시제품용')==7 and all(x in text for x in ['D4.3','D3.3','94.00','154.00'])
results['pdf_pages']=7;results['pdf_size']='A3';results['required_text_present']=True
(r/'export_checks.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))

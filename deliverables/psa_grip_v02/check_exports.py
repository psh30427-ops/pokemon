#!/usr/bin/python3
"""Executed release checks; requires FreeCAD and Poppler."""
from pathlib import Path
import sys,json,subprocess
sys.path.append('/usr/lib/freecad/lib')
import FreeCAD as A,Part,Mesh
R=Path(__file__).resolve().parent;checks={}
step=Part.read(str(R/'assembly.step'));assert step.isValid() and len(step.Solids)==4
checks['assembly_step_valid_solids']=4
D=A.openDocument(str(R/'assembly.FCStd'));features=[o for o in D.Objects if o.TypeId=='Part::Feature'];assert len(features)==9 and all(o.Shape.isValid() for o in features)
checks['native_valid_features']=len(features)
for f in sorted((R/'parts').glob('*.step')):
 s=Part.read(str(f));m=Mesh.Mesh(str(f.with_suffix('.stl')));p=Mesh.Mesh(str(R/'STL_PRINT'/f'{f.stem}_PRINT_mm.stl'))
 assert s.isValid() and len(s.Solids)==1 and m.isSolid() and p.isSolid()
 delta=max(abs(getattr(s.BoundBox,a)-getattr(m.BoundBox,a)) for a in ['XMin','XMax','YMin','YMax','ZMin','ZMax']);assert delta<.1
 err=abs(abs(p.Volume)-s.Volume)/s.Volume;assert err<.002
 assert p.BoundBox.ZMin>=-.0001 and p.BoundBox.XMin>=-.0001 and p.BoundBox.YMin>=-.0001
 checks[f.stem]={'original_stl_closed':True,'print_stl_closed':True,'step_stl_bbox_error_mm':delta,'print_relative_volume_error':err,'print_bbox_mm':[p.BoundBox.XLength,p.BoundBox.YLength,p.BoundBox.ZLength]}
r=json.loads((R/'validation_results.json').read_text());assert len(r['sampled_grip_extension_mm'])==17 and not r['interferences'];assert r['gate_bolt_min_edge_ligament_mm']>=.7
checks['sampled_envelope_interference_count']=0;checks['gate_edge_ligament_mm']=r['gate_bolt_min_edge_ligament_mm']
info=subprocess.check_output(['pdfinfo',str(R/'drawings'/'PSA_grip_V02_A3.pdf')],text=True);assert 'Pages:           6' in info and '(A3)' in info
text=subprocess.check_output(['pdftotext',str(R/'drawings'/'PSA_grip_V02_A3.pdf'),'-'],text=True);assert text.count('예비 시제품용')==6 and '154.00' in text and '94.00' in text
checks['a3_pdf_pages']=6
(R/'export_checks.json').write_text(json.dumps(checks,indent=2));print(json.dumps(checks,indent=2))

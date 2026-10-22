#!/usr/bin/python3
"""Read-only checks plus export_checks.json; FreeCAD and Poppler required."""
import sys,json,subprocess
from pathlib import Path
sys.path.append('/usr/lib/freecad/lib')
import FreeCAD as A,Part,Mesh
R=Path(__file__).resolve().parent;report={}
for r in [R,R/'variants'/'aluminum_case']:
 data=json.loads((r/'validation_results.json').read_text());checks={}
 s=Part.read(str(r/'PSA_Grip_V02_Assembly.step'));assert s.isValid() and len(s.Solids)==6
 checks['assembly_printed_solids']=6
 d=A.openDocument(str(r/'PSA_Grip_V02.FCStd'));features=[o for o in d.Objects if o.TypeId=='Part::Feature'];assert all(o.Shape.isValid() for o in features)
 checks['native_valid_features']=len(features)
 for p in sorted((r/'STEP_parts').glob('*.step')):
  s=Part.read(str(p));m=Mesh.Mesh(str(r/'STL'/f'{p.stem}.stl'));out=Mesh.Mesh(str(r/'STL_PRINT'/f'{p.stem}.stl'))
  assert s.isValid() and len(s.Solids)==1 and m.isSolid() and out.isSolid()
  delta=max(abs(getattr(s.BoundBox,a)-getattr(m.BoundBox,a)) for a in ['XMin','XMax','YMin','YMax','ZMin','ZMax']);assert delta<.1
  err=abs(abs(out.Volume)-s.Volume)/s.Volume;assert err<.002 and out.BoundBox.ZMin>=-.0001
  checks[p.stem]={'stl_closed':True,'step_original_stl_bbox_error_mm':delta,'print_relative_volume_error':err}
 for k in ['body_interferences','hardware_interferences','gate_open_sweep_interferences','payload_insertion_interferences']:assert data[k]==[]
 assert len(data['sample_angles_deg'])==19 and all(v>0 for v in data['gate_blocks_on_each_end_wall_mm3'])
 info=subprocess.check_output(['pdfinfo',str(r/'drawings'/'PSA_Grip_V02_Manufacturing_A3.pdf')],text=True);assert 'Pages:           10' in info and '(A3)' in info
 text=subprocess.check_output(['pdftotext',str(r/'drawings'/'PSA_Grip_V02_Manufacturing_A3.pdf'),'-'],text=True);assert text.count('예비 시제품용')==10 and 'D5.2' in text
 guide=subprocess.check_output(['pdfinfo',str(r/'drawings'/'Assembly_and_Print_Guide_ko.pdf')],text=True);assert 'Pages:           2' in guide
 checks['pdf_A3_pages']=10;checks['assembly_guide_pages']=2;checks['sampled_interferences']=0
 report[data['variant']]=checks;A.closeDocument(d.Name)
(R/'export_checks.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

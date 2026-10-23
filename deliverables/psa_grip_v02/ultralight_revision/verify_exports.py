#!/usr/bin/python3
"""Independent exported-file checks. Requires FreeCAD, pdfinfo/pdftotext, Blender optional."""
import sys,json,csv,math,subprocess
from pathlib import Path
sys.path.append('/usr/lib/freecad/lib')
import FreeCAD as A,Part,Mesh
R=Path(__file__).resolve().parent
out={'checks':[],'failures':[]}
def check(label,condition,details=None):
 item={'check':label,'passed':bool(condition),'details':details};out['checks'].append(item)
 if not condition:out['failures'].append(item)
results=json.loads((R/'comparison_results.json').read_text())
for key,v in results.items():
 r=R/key
 for name,ws in v['weights'].items():
  sh=Part.read(str(r/'STEP_parts'/(name+'.step')));mesh=Mesh.Mesh(str(r/'STL_PRINT'/(name+'.stl')))
  check(key+'/'+name+'/solid',sh.isValid() and len(sh.Solids)==1)
  check(key+'/'+name+'/STEP_volume',abs(sh.Volume-ws['volume_mm3'])<1e-4)
  check(key+'/'+name+'/STL_closed_positive',mesh.isSolid() and mesh.Volume>0)
  check(key+'/'+name+'/STL_volume',abs(mesh.Volume/sh.Volume-1)<.002)
  check(key+'/'+name+'/STL_floor_mm',abs(mesh.BoundBox.ZMin)<1e-4,[mesh.BoundBox.XLength,mesh.BoundBox.YLength,mesh.BoundBox.ZLength])
  check(key+'/'+name+'/mass',abs(sh.Volume*ws['density_g_cm3']/1000*ws['quantity']-ws['total_mass_g'])<1e-5)
 with (r/'BOM.csv').open() as f:bom=list(csv.DictReader(f))
 check(key+'/BOM_mass',abs(sum(float(x['total_g']) for x in bom)-v['mass']['additional_nominal_g'])<.002)
 check(key+'/BOM_quantities',all(int(next(q for q in bom if q['part']==n)['qty'])==ws['quantity'] for n,ws in v['weights'].items()))
 for f in (r/'CAD').glob('*.step'):
  sh=Part.read(str(f));check(key+'/'+f.name+'/valid',sh.isValid() and len(sh.Solids)>0,len(sh.Solids))
 doc=A.openDocument(str(r/'CAD'/'PSA_Grip_Ultralight.FCStd'))
 objs=[o for o in doc.Objects if hasattr(o,'Shape')];check(key+'/FCStd_reopen',len(objs)>0 and all(o.Shape.isValid() for o in objs),len(objs));A.closeDocument(doc.Name)
 check(key+'/collision_results',all(not v[x] for x in ['sampled_interferences','insertion_interferences','gate_open_interferences']))
 for ext,cgs in v['center_of_mass_by_extension'].items():check(key+'/CG_mass_'+ext,abs(cgs['with_phone']['mass_g']-v['mass']['with_phone_nominal_g'])<.001)
for f in R.rglob('*.pdf'):
 info=subprocess.check_output(['pdfinfo',str(f)],text=True)
 pages=1 if f.parent==R else 6
 check(str(f.relative_to(R))+'/pages',f'Pages:           {pages}' in info,info.splitlines())
 check(str(f.relative_to(R))+'/A3', '1190.55 x 841.89' in info)
 text=subprocess.check_output(['pdftotext',str(f),'-'],text=True)
 check(str(f.relative_to(R))+'/warning',text.count('예비 시제품용')==pages)
if (R.parents[2]/'.git').exists():check('V01_and_prior_V02_preserved',not subprocess.check_output(['git','diff','--name-only','dcf031d','--','deliverables/psa_grip_v01','deliverables/psa_grip_v02/circular_popup_revision'],cwd=R.parents[2],text=True).strip())
(R/'export_verification.json').write_text(json.dumps(out,indent=2))
print(json.dumps({'checks':len(out['checks']),'failures':out['failures']},ensure_ascii=False,indent=2))
if out['failures']:sys.exit(1)

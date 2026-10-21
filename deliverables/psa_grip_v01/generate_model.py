#!/usr/bin/python3
"""Run: QT_QPA_PLATFORM=offscreen /usr/bin/python3 generate_model.py
FreeCAD 1.0 Part workbench; mm, g. Regenerates all output files.
"""
import sys, os, math, json, csv, itertools
from pathlib import Path
sys.path.append('/usr/lib/freecad/lib')
os.environ.setdefault('MPLCONFIGDIR','/tmp/psa-mpl')
import FreeCAD as A, Part, Mesh
from FreeCAD import Vector as V
ROOT=Path(__file__).resolve().parent
for d in ['parts','drawings','renders','states']: (ROOT/d).mkdir(exist_ok=True)
DEFAULT={'case_w':86.,'case_h':142.,'case_t':11.,'clear_xy':1.,'back':3.,'outer_wall':3.,'pad_z_compressed':.6,'pad_xy_compressed':.6,'pad_free':.8,'z_free_clearance':.6,'lip':2.,'lip_overlap':1.5,'arm_length':32.,'arm_width':18.,'arm_thickness':8.,'hinge_d':4.3,'lock_d':3.3,'gate_d':3.4,'pivot_z':-6.,'lock_r':8.,'phone_w':71.5,'phone_h':149.6,'phone_t':8.25,'phone_mass':199.,'phone_case_mass':25.,'hardware_and_liner_mass':15.,'phone_case_t':1.5,'camera_w':38.,'camera_h':38.,'camera_projection':4.,'camera_x':-15.,'camera_y':52.,'payload_mass':120.,'module_mass':18.,'petg_density':1.27,'mag_module_d':56.,'mag_module_t':2.}
pfile=ROOT/'design_parameters.json'
p=json.loads(pfile.read_text()) if pfile.exists() else DEFAULT
pfile.write_text(json.dumps(p,indent=2))
w,h,t=p['case_w'],p['case_h'],p['case_t']; cx=w/2+p['clear_xy']; cy=h/2+p['clear_xy']; ox=cx+p['outer_wall']; oy=cy+5
floor=p['back']; lipz=floor+p['pad_z_compressed']+t+p['z_free_clearance']; top=lipz+p['lip']; L=p['arm_length']; z0=p['pivot_z']; r=p['lock_r']
def box(x,y,z,dx,dy,dz): return Part.makeBox(dx,dy,dz,V(x,y,z))
def cyl(rad,length,pos,axis=(0,0,1)): return Part.makeCylinder(rad,length,V(*pos),V(*axis))
def fuse(sh):
 s=sh[0]
 for q in sh[1:]:s=s.fuse(q)
 return s.removeSplitter()
def cut(s,tools):
 for q in tools:s=s.cut(q)
 return s.removeSplitter()
# Back tray open at +Y. Front strips overlap only 0.5 mm of nominal case edge.
cradle=fuse([box(-ox,-oy,0,2*ox,2*oy,floor),box(-ox,-oy,floor,2*ox,5,top-floor),box(-ox,-cy,floor,3,2*cy-3,top-floor),box(cx,-cy,floor,3,2*cy-3,top-floor),box(-cx,-cy,lipz,p['lip_overlap'],2*cy-3,2),box(cx-p['lip_overlap'],-cy,lipz,p['lip_overlap'],2*cy-3,2)])
# Twin hinge cheeks, x faces at +/-10.5 leave 1.5 mm total washer clearance per side.
cheeks=[box(x,-12,-18.5,8,24,18.5) for x in [-18.5,10.5]]
cradle=fuse([cradle]+cheeks)
holes=[cyl(p['hinge_d']/2,40,(-20,0,z0),(1,0,0))]
for a in [0,60,90]:
 rad=math.radians(a);holes.append(cyl(p['lock_d']/2,40,(-20,r*math.cos(rad),z0-r*math.sin(rad)),(1,0,0)))
for x in [-40,40]: holes.append(cyl(p['gate_d']/2,10,(x,cy+2.5,-1)))
# Independent tether slot: 6 x 3, through back plate, beyond nominal case edge.
holes.append(box(-3,-oy+1,-1,6,3,6))
cradle=cut(cradle,holes)
gate=fuse([box(-ox,cy,3,2*ox,5,2),box(-ox,cy,5,2*ox,5,top-5),box(-ox,cy-2.5,lipz,2*ox,7.5,2)])
gate=cut(gate,[cyl(p['gate_d']/2,30,(x,cy+2.5,-1)) for x in [-40,40]])
# Capsule link. All dimensions are in assembly coordinates at folded position.
arm=fuse([box(-9,0,z0-4,18,L,8),cyl(4,18,(-9,0,z0),(1,0,0)),cyl(4,18,(-9,L,z0),(1,0,0))])
arm=cut(arm,[cyl(p['hinge_d']/2,24,(-12,y,z0),(1,0,0)) for y in [0,L]]+[cyl(p['lock_d']/2,24,(-12,r,z0),(1,0,0))])
# Base is a flat adapter with four M3 through holes, not a fully specified magnetic module.
base=fuse([cyl(30,4,(0,L,-23))]+[box(x,L-7,-19,8,14,17.5) for x in [-18.5,10.5]])
base=cut(base,[cyl(p['hinge_d']/2,40,(-20,L,z0),(1,0,0))]+[cyl(3.4/2,8,(x,L+y,-25)) for x,y in [(21,0),(-21,0),(0,21),(0,-21)]])
parts={'01_cradle':cradle,'02_top_gate':gate,'03_link':arm,'04_base_adapter':base}
case=box(-w/2,-h/2,floor+p['pad_z_compressed'],w,h,t)
def state(angle):
 a=math.radians(angle); bp=(L*math.cos(a),z0-L*math.sin(a));link=arm.copy();link.rotate(V(0,0,z0),V(1,0,0),-angle)
 b=base.copy();b.translate(V(0,bp[0]-L,bp[1]-z0))
 mod=cyl(p['mag_module_d']/2,p['mag_module_t'],(0,bp[0],-25+bp[1]-z0))
 phoneback=-25+bp[1]-z0
 phone=box(-p['phone_w']/2,bp[0]-p['phone_h']/2,phoneback-p['phone_t']-p['phone_case_t'],p['phone_w'],p['phone_h'],p['phone_t']+p['phone_case_t'])
 camera=box(p['camera_x']-p['camera_w']/2,bp[0]+p['camera_y']-p['camera_h']/2,phoneback,p['camera_w'],p['camera_h'],p['camera_projection'])
 return {'01_cradle':cradle,'02_top_gate':gate,'03_link':link,'04_base_adapter':b,'REF_case':case,'REF_module':mod,'REF_phone':phone,'REF_camera':camera}
colors={'01_cradle':(.16,.28,.40),'02_top_gate':(.9,.5,.15),'03_link':(.15,.58,.60),'04_base_adapter':(.3,.35,.4),'REF_case':(.65,.7,.76),'REF_phone':(.17,.17,.2),'REF_module':(.55,.55,.55),'REF_camera':(.1,.1,.1)}
doc=A.newDocument('PSA_Grip_V01')
params=doc.addObject('Spreadsheet::Sheet','Parameters')
params.set('A1','Parameter');params.set('B1','mm / g');params.set('C1','Status')
for i,(k,val) in enumerate(p.items(),2):
 params.set('A'+str(i),k);params.set('B'+str(i),str(val));params.set('C'+str(i),'SELLER' if k in ['case_w','case_h','case_t'] else 'ASSUMED')
for name,s in state(0).items():
 ob=doc.addObject('Part::Feature',name);ob.Label=name;ob.Shape=s
 ob.addProperty('App::PropertyString','DesignStatus').DesignStatus='PRELIMINARY - measure and test before release'
doc.recompute();doc.saveAs(str(ROOT/'assembly.FCStd'))
Part.Compound(list(parts.values())).exportStep(str(ROOT/'assembly.step'))
checks={}; masses={}; meshes={}
for name,s in parts.items():
 s.exportStep(str(ROOT/'parts'/f'{name}.step'))
 mesh=Mesh.Mesh(s.tessellate(.15));mesh.write(str(ROOT/'parts'/f'{name}.stl'))
 re=Part.read(str(ROOT/'parts'/f'{name}.step')); rm=Mesh.Mesh(str(ROOT/'parts'/f'{name}.stl'))
 bb=s.BoundBox
 checks[name]={'valid':s.isValid(),'solids':len(s.Solids),'closed':s.isClosed(),'volume_mm3':s.Volume,'step_valid':re.isValid(),'step_volume_delta':abs(re.Volume-s.Volume),'stl_solid':rm.isSolid(),'stl_facets':rm.CountFacets,'bounds_mm':[bb.XLength,bb.YLength,bb.ZLength]}
 masses[name]=s.Volume/1000*p['petg_density'];meshes[name]=s.tessellate(.3)
for ang in [0,60,90]:
 sd=state(ang);objs=[]
 for k,s in sd.items():
  if not k.startswith('REF'): objs.append(s)
 Part.Compound(objs).exportStep(str(ROOT/'states'/f'assembly_{ang}deg.step'))
collisions=[]
for ang in range(0,91,5):
 ss=state(ang)
 for k,j in itertools.combinations(ss,2):
  # phone-camera intentionally overlap only on shared surface; include all pairs.
  v=ss[k].common(ss[j]).Volume
  if v>1e-5:collisions.append({'angle':ang,'a':k,'b':j,'volume_mm3':round(v,5)})
# Mass and centers for each state, rigid proxy mass for case+slab and purchase module.
centers={}
def com_of(s):
 total=s.Volume
 return V(*[sum(q.Volume*getattr(q.CenterOfMass,k) for q in s.Solids)/total for k in ['x','y','z']])
for ang in [0,60,90]:
 ss=state(ang);weighted=[]
 for k in parts:weighted.append((masses[k],com_of(ss[k])))
 weighted.append((p['hardware_and_liner_mass'],V(0,0,-6)))
 for k,m in [('REF_case',p['payload_mass']),('REF_module',p['module_mass']),('REF_phone',p['phone_mass']+p['phone_case_mass'])]:weighted.append((m,com_of(ss[k])))
 total=sum(m for m,c in weighted);com=[sum(m*getattr(c,axis) for m,c in weighted)/total for axis in ['x','y','z']]
 centers[str(ang)]={'total_mass_g':total,'COM_mm':com}
result={'parts':checks,'interferences':collisions,'mass_g_solid_equivalent':masses,'assembly_mass_COM':centers,'assumed_camera_only':True,'sweep_samples_deg':list(range(0,91,5))}
(ROOT/'validation_results.json').write_text(json.dumps(result,indent=2))
with (ROOT/'parameters.csv').open('w') as f:
 wr=csv.writer(f);wr.writerow(['parameter','value','unit','status','source'])
 for k,v in p.items():wr.writerow([k,v,'g/cm3' if k=='petg_density' else ('g' if 'mass' in k else 'mm'),'SELLER_DECLARED' if k in ['case_w','case_h','case_t'] else 'ASSUMED','User seller image' if k in ['case_w','case_h','case_t'] else 'Engineering assumption; measure before manufacture'])
with (ROOT/'BOM.csv').open('w') as f:
 wr=csv.writer(f);wr.writerow(['id','description','qty','material/spec','estimated_g','status'])
 for k,m in masses.items():wr.writerow([k,k,1,'PETG; 1.27 g/cm3 solid equivalent',round(m,2),'PRINT PROTOTYPE'])
 for row in [('P01','Existing case + PSA slab',1,'86x142x11 Al alloy seller envelope',120,'ASSUMED mass'),('P02','M4 pivot bolt',2,'M4 x 50 + nyloc nut + washers','', 'Measure grip length; no thread in bearing if possible'),('P03','Upper hinge locking pin',1,'3 mm steel retained pin, >=40 mm usable','', 'ASSUMED; positive retained pin'),('P04','Gate bolt + nyloc nut',2,'M3 x 12 + broad washers','', 'ASSUMED; verify engagement'),('P05','Hinge shims',4,'1.5 mm stack each cheek side; adjust','', 'FIT TO MEASURED PRINT'),('P06','Liner strips',1,'0.8 mm soft silicone/TPU; compressed 0.6','', 'Retain without adhesive on case'),('P07','Commercial magnetic module',1,'Envelope D56x2, mass18g; unqualified',18,'INTERFACE NOT RELEASED'),('P08','Independent phone tether',1,'Loop routed to phone case tether anchor','', 'REQUIRED FOR DUMMY TEST'),('P09','Base fasteners',4,'M3 through hole pattern R21 at cardinal points','', 'UNMATCHED TO PURCHASE MODULE')]:wr.writerow(row)
print(json.dumps(result,indent=2))
# Generate drawing and rendering artifacts with companion script.
import runpy
runpy.run_path(str(ROOT/'make_documents.py'),init_globals={'model_parts':parts,'get_state':state,'p':p,'root':ROOT,'result':result,'colors':colors,'masses':masses})

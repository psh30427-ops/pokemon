#!/usr/bin/python3
"""Actual two-payload, pin-gate, four-bar prototype. mm. FreeCAD 1.0.
Run /usr/bin/python3 generate_model.py; also invokes documents.py and Blender.
"""
import sys,os,json,csv,math,itertools,subprocess,runpy,hashlib,zipfile
from pathlib import Path
sys.path.append('/usr/lib/freecad/lib')
import FreeCAD as A,Part,Mesh
from FreeCAD import Vector as V
ROOT=Path(__file__).resolve().parent
DEFAULT={'slab_w':81.,'slab_h':136.,'slab_t':6.,'slab_corner_r':3.,'slab_mass_g':50.,'case_w':86.,'case_h':142.,'case_t':11.,'case_corner_r':2.,'case_mass_g':120.,'xy_clearance_per_side':.8,'rear_pad_compressed':.5,'front_pad_compressed':.4,'rear_t':3.,'lip_t':1.8,'rail_t':3.2,'gate_slot_clearance':.3,'gate_magnet_d':5.,'gate_magnet_t':2.,'magnet_radial_clearance':.1,'magnet_bond_allowance':.2,'link_length':28.,'link_width':18.,'link_t':8.,'fork_gap':19.,'fork_t':9.,'hinge_hole_d':3.2,'hinge_pin_d':3.,'index_radius':6.,'station_half_spacing':25.,'base_w':64.,'base_h':64.,'base_t':3.,'base_back_z':-20.,'pivot_z':-6.,'adhesive_t':1.,'phone_w':71.5,'phone_h':149.6,'phone_t':8.25,'phone_case_t':1.5,'phone_mass_g':224.,'camera_w':38.,'camera_h':38.,'camera_t':4.,'camera_x':-15.,'camera_y':52.,'hardware_mass_g':28.,'pad_and_adhesive_mass_g':7.,'petg_density':1.27}
f=ROOT/'design_parameters.json';p=json.loads(f.read_text()) if f.exists() else DEFAULT;f.write_text(json.dumps(p,indent=2))
def box(x,y,z,dx,dy,dz):return Part.makeBox(dx,dy,dz,V(x,y,z))
def cylinder(r,length,pos,axis=(0,0,1)):return Part.makeCylinder(r,length,V(*pos),V(*axis))
def fuse(seq):
 s=seq[0]
 for q in seq[1:]:s=s.fuse(q)
 return s.removeSplitter()
def cut(s,seq):
 for q in seq:s=s.cut(q)
 return s.removeSplitter()
def roundbox(w,h,z,t,r,cy=0):
 s=box(-w/2,cy-h/2,z,w,h,t);es=[e for e in s.Edges if e.BoundBox.ZLength>t-.001 and e.BoundBox.XLength<.001 and e.BoundBox.YLength<.001]
 return s.makeFillet(r,es)
def com(s):return V(*[sum(q.Volume*getattr(q.CenterOfMass,k) for q in s.Solids)/s.Volume for k in ['x','y','z']])
def pin_x(y,z):
 s=fuse([cylinder(1.5,43,(-20,y,z),(1,0,0)),cylinder(3,2,(-22,y,z),(1,0,0))])
 return cut(s,[cylinder(.6,8,(21,y,z-4))])
all_results={}
for variant,folder in [('direct_slab',ROOT),('aluminum_case',ROOT/'variants'/'aluminum_case')]:
 for d in ['STL','STL_PRINT','STEP_parts','drawings','renders','states']: (folder/d).mkdir(parents=True,exist_ok=True)
 prefix='slab' if variant=='direct_slab' else 'case';w,h,t=p[prefix+'_w'],p[prefix+'_h'],p[prefix+'_t'];payloadmass=p[prefix+'_mass_g']
 cx=w/2+p['xy_clearance_per_side'];cy=h/2+p['xy_clearance_per_side'];ox=cx+p['rail_t'];oy=cy+p['rail_t'];rear=p['rear_t'];lipz=rear+p['rear_pad_compressed']+t+p['front_pad_compressed'];top=lipz+p['lip_t'];podx=cx+6;podtop=cy+5;podmin=cy-13;gatepinY=cy-5
 L=p['link_length'];S=p['station_half_spacing'];pz=p['pivot_z'];ir=p['index_radius'];forkin=p['fork_gap']/2;forkout=forkin+p['fork_t'];ax=p['hinge_hole_d']/2;bt=p['base_t'];bz=p['base_back_z'];stations=[-S,S]
 assert h>120 and w>70 and p['link_width']<p['fork_gap']
 # Rear perimeter + load bridge; fully open front/label area except narrow edge lips.
 rim=cut(roundbox(2*ox,2*oy,0,rear,4),[roundbox(w-4,h-4,-1,rear+2,2)])
 bridge=fuse([roundbox(48,100,0,rear,5),box(-ox,-11,0,2*ox,22,rear)])
 frame=fuse([rim,bridge,box(-ox,-oy,rear,2*ox,oy-cy,top-rear),box(-ox,-cy,rear,p['rail_t'],2*cy-2.5,top-rear),box(cx,-cy,rear,p['rail_t'],2*cy-2.5,top-rear),box(-cx,-cy,lipz,1.8,2*cy-2.5,p['lip_t']),box(cx-1.8,-cy,lipz,1.8,2*cy-2.5,p['lip_t'])]+[box(x-6,podmin,0,12,podtop-podmin,top) for x in [-podx,podx]])
 mountxy=[(x,y) for x in [-17,17] for y in [-42,42]]
 tools=[]
 for x in [-podx,podx]:
  tools += [box(x-3.8,cy-11,3,7.6,14,top+1),cylinder(p['gate_magnet_d']/2+p['magnet_radial_clearance'],p['gate_magnet_t']+p['magnet_bond_allowance']+.1,(x,gatepinY,3-p['gate_magnet_t']-p['magnet_bond_allowance']))]
 for x,y in mountxy:tools += [cylinder(1.7,rear+3,(x,y,-1)),cylinder(3.1,2,(x,y,rear-1.8))]
 tools.append(box(-3,-oy+.5,-1,6,2,rear+2));frame=cut(frame,tools)
 # Magnetic lift-then-slide gate; positive end walls carry the +Y escape load.
 gate=fuse([box(-podx-6,cy+3,top+.3,2*podx+12,4,2.5),box(-cx,cy,3.3,2*cx,3,top-3.3),box(-cx,cy-2,lipz,2*cx,9,p['lip_t']),box(-cx,cy+3,top-1,2*cx,4,3.8)]+[box(x-3.5,cy-10.7,3.3,7,13.7,4) for x in [-podx,podx]]+[box(x-3.5,cy+1,7.3,7,2,top+2.8-7.3) for x in [-podx,podx]])
 gate=cut(gate,[cylinder(p['gate_magnet_d']/2+p['magnet_radial_clearance'],p['gate_magnet_t']+p['magnet_bond_allowance']+.1,(x,gatepinY,3.2)) for x in [-podx,podx]])
 # Frame connector, fork pairs and integral 90-degree stop blocks.
 connector=roundbox(44,96,-2,2,4)
 for sy in stations:
  connector=fuse([connector]+[box(x,sy-12,-15.5,p['fork_t'],24,13.5) for x in [-forkout,forkin]]+[box(-forkin,sy-7,-15.5,2*forkin,2.7,4.5)])
 ct=[cylinder(1.7,5,(x,y,-3)) for x,y in mountxy]
 for sy in stations:
  ct.append(cylinder(ax,60,(-30,sy,pz),(1,0,0)))
  for a in [0,90]:ct.append(cylinder(ax,60,(-30,sy+ir*math.cos(math.radians(a)),pz-ir*math.sin(math.radians(a))),(1,0,0)))
 connector=cut(connector,ct)
 # One link printed twice; closed reference coordinates centered at upper station -S.
 link=fuse([box(-p['link_width']/2,-S,pz-4,p['link_width'],L,8),cylinder(4,p['link_width'],(-p['link_width']/2,-S,pz),(1,0,0)),cylinder(4,p['link_width'],(-p['link_width']/2,-S+L,pz),(1,0,0))])
 link=cut(link,[cylinder(ax,60,(-30,y,pz),(1,0,0)) for y in [-S,-S+L,-S+ir]])
 base=roundbox(p['base_w'],p['base_h'],bz,bt,7,L)
 for sy in stations:
  base=fuse([base]+[box(x,L+sy-4.5,bz+bt,p['fork_t'],9,-2.5-(bz+bt)) for x in [-forkout,forkin]])
 base=cut(base,[cylinder(ax,60,(-30,L+sy,pz),(1,0,0)) for sy in stations])
 parts={'01_Main_Frame':frame,'02_Locking_Gate':gate,'03_Grip_Connector':connector,'04_Collapsible_Grip':link,'05_Phone_Base':base}
 quantities={k:(2 if k=='04_Collapsible_Grip' else 1) for k in parts}
 payload=roundbox(w,h,rear+p['rear_pad_compressed'],t,p[prefix+'_corner_r'])
 # Free-thickness side liner, separate TPU cut/print piece, quantity2.
 liner=box(0,0,0,1,110,t)
 extras={'06_TPU_Side_Liner':liner}
 def pose(deg,hardware=False,graphics=False,withphone=True):
  rad=math.radians(deg);dy=L*math.cos(rad);dz=-L*math.sin(rad)
  a=link.copy();a.rotate(V(0,-S,pz),V(1,0,0),-deg);bb=a.copy();bb.translate(V(0,2*S,0));bas=base.copy();bas.translate(V(0,dy-L,dz))
  out={'01_Main_Frame':frame,'02_Locking_Gate':gate,'03_Grip_Connector':connector,'04_Link_A':a,'04_Link_B':bb,'05_Phone_Base':bas,'REF_Payload':payload}
  adh=roundbox(p['base_w']-2,p['base_h']-2,bz+dz-p['adhesive_t'],p['adhesive_t'],6,dy);out['REF_Adhesive']=adh
  if withphone:
   pb=bz+dz-p['adhesive_t'];out['REF_Phone']=roundbox(p['phone_w'],p['phone_h'],pb-p['phone_t']-p['phone_case_t'],p['phone_t']+p['phone_case_t'],8,dy)
   out['REF_Camera']=box(p['camera_x']-p['camera_w']/2,dy+p['camera_y']-p['camera_h']/2,pb,p['camera_w'],p['camera_h'],p['camera_t'])
  if hardware:
   for i,sy in enumerate(stations):
    out[f'HW_Upper_Pivot_{i}']=pin_x(sy,pz);out[f'HW_Lower_Pivot_{i}']=pin_x(sy+dy,pz+dz)
    if deg in [0,90]:out[f'HW_Index_Pin_{i}']=pin_x(sy+ir*math.cos(rad),pz-ir*math.sin(rad))
   for i,x in enumerate([-podx,podx]):
    out[f'HW_Frame_Magnet_{i}']=cylinder(p['gate_magnet_d']/2,p['gate_magnet_t'],(x,gatepinY,3-p['gate_magnet_t']))
    out[f'HW_Gate_Magnet_{i}']=cylinder(p['gate_magnet_d']/2,p['gate_magnet_t'],(x,gatepinY,3.3))
   for i,(x,y) in enumerate(mountxy):
    out[f'HW_Mount_Screw_{i}']=fuse([cylinder(1.5,6.25,(x,y,-5)),cylinder(2.85,1.65,(x,y,1.25))]);out[f'HW_Mount_Nut_{i}']=cut(cylinder(3.2,2.3,(x,y,-4.5)),[cylinder(1.6,4,(x,y,-5))])
  if graphics and prefix=='slab':
   # Render-only neutral card and label; no fabricated PSA certification/artwork.
   z=rear+p['rear_pad_compressed']+(t/2 if prefix=='slab' else t+.03)
   out['ART_Card']=box(-31.5,-53,z,63,88,.12);out['ART_Label']=box(-35,h/2-26,z,70,19,.12)
  return out
 doc=A.newDocument('PSA_Grip_V02_'+variant);sheet=doc.addObject('Spreadsheet::Sheet','Parameters')
 for row,(k,v) in enumerate(p.items(),1):sheet.set('A'+str(row),k);sheet.set('B'+str(row),str(v));sheet.set('C'+str(row),'UNMEASURED')
 for k,s in pose(0,True,False).items():
  o=doc.addObject('Part::Feature','Part_'+k);o.Label=k;o.Shape=s;o.addProperty('App::PropertyString','Status').Status='PRINTED PART' if k[:2] in ['01','02','03','04','05'] else 'REFERENCE / STANDARD HARDWARE'
 doc.recompute();doc.saveAs(str(folder/'PSA_Grip_V02.FCStd'))
 for ang in [0,90]:Part.Compound([s for k,s in pose(ang).items() if not k.startswith('REF')]).exportStep(str(folder/'states'/f'Assembly_{ang}deg.step'))
 Part.Compound([s for k,s in pose(0).items() if not k.startswith('REF')]).exportStep(str(folder/'PSA_Grip_V02_Assembly.step'))
 checks={};masses={}
 for name,s in {**parts,**extras}.items():
  assert s.isValid() and len(s.Solids)==1,(variant,name,'not one valid solid')
  s.exportStep(str(folder/'STEP_parts'/f'{name}.step'));m=Mesh.Mesh(s.tessellate(.12));m.write(str(folder/'STL'/f'{name}.stl'))
  q=s.copy()
  if name=='01_Main_Frame':q.rotate(V(0,0,0),V(0,1,0),90)
  if name=='02_Locking_Gate':q.rotate(V(0,0,0),V(1,0,0),-90)
  if name=='03_Grip_Connector':q.rotate(V(0,0,0),V(1,0,0),180)
  if name=='06_TPU_Side_Liner':q.rotate(V(0,0,0),V(0,1,0),90)
  if name=='04_Collapsible_Grip':q.rotate(V(0,0,0),V(0,1,0),90)
  B=q.BoundBox;q.translate(V(-B.XMin,-B.YMin,-B.ZMin));Mesh.Mesh(q.tessellate(.12)).write(str(folder/'STL_PRINT'/f'{name}.stl'))
  rr=Part.read(str(folder/'STEP_parts'/f'{name}.step'));rm=Mesh.Mesh(str(folder/'STL_PRINT'/f'{name}.stl'))
  assert rr.isValid() and rm.isSolid()
  masses[name]=s.Volume/1000*(1.20 if name in extras else p['petg_density'])
  checks[name]={'valid_solid':True,'quantity':quantities.get(name,2),'volume_mm3':s.Volume,'mass_solid_equiv_g':masses[name],'step_volume_error_mm3':abs(rr.Volume-s.Volume),'stl_closed':rm.isSolid(),'print_bounds_mm':[q.BoundBox.XLength,q.BoundBox.YLength,q.BoundBox.ZLength],'stl_relative_volume_error':abs(abs(rm.Volume)-s.Volume)/s.Volume}
 # All mechanical and payload/phone envelopes in 19 sampled positions. Artwork excluded.
 collisions=[]
 for ang in range(0,91,5):
  ss=pose(ang)
  for k,j in itertools.combinations(ss,2):
   v=ss[k].common(ss[j]).Volume
   if v>1e-5:collisions.append({'angle':ang,'a':k,'b':j,'mm3':v})
 hardware_hits=[]
 for ang in [0,45,90]:
  ss=pose(ang,True);keys=[k for k in ss if k.startswith('HW_')]
  for k in keys:
   for j in ss:
    if j.startswith('HW_') and keys.index(j)<=keys.index(k):continue
    if j==k:continue
    v=ss[k].common(ss[j]).Volume
    if v>1e-5:hardware_hits.append({'angle':ang,'a':k,'b':j,'mm3':v})
 # Gate removal first +Z beyond end walls, then +Y; magnets removed with gate.
 gate_sweep=[];insertion=[];lift_clear=top-3.3+.6
 for n in range(16):
  for stage in [0,1]:
   g=gate.copy();g.translate(V(0,0 if stage==0 else n*(h+10)/15,n*lift_clear/15 if stage==0 else lift_clear));v=g.common(frame).Volume
   if v>1e-5:gate_sweep.append({'stage':stage,'sample':n,'mm3':v})
  delta=n*(h+10)/15;s=payload.copy();s.translate(V(0,delta,0));v=s.common(frame).Volume
  if v>1e-5:insertion.append({'delta_y':delta,'mm3':v})
 # Each gate tongue is blocked by its mechanical +Y end wall, independent of magnet force.
 blocked=[]
 for x in [-podx,podx]:
  foot=box(x-3.5,cy-10.7+2,3.3,7,13.7,4);blocked.append(foot.common(frame).Volume)
 assert all(v>0 for v in blocked),'Gate stop walls do not block gate'
 cmstates={}
 for ang in [0,90]:
  ss=pose(ang);weights=[(masses[k]*quantities[k],com(ss[k] if k!='04_Collapsible_Grip' else ss['04_Link_A'])) for k in parts if k!='04_Collapsible_Grip']
  weights += [(masses['04_Collapsible_Grip'],com(ss[k])) for k in ['04_Link_A','04_Link_B']]
  weights += [(payloadmass,com(payload)),(p['phone_mass_g'],com(ss['REF_Phone'])),(p['hardware_mass_g']+p['pad_and_adhesive_mass_g'],V(0,0,-5))]
  mt=sum(m for m,c in weights);cmstates[str(ang)]={'mass_g':mt,'COM_mm':[sum(m*getattr(c,a) for m,c in weights)/mt for a in ['x','y','z']]}
 result={'variant':variant,'payload_mm':[w,h,t],'payload_status':'ASSUMED, NOT MEASURED' if prefix=='slab' else 'SELLER REFERENCE, NOT MEASURED','parts':checks,'sample_angles_deg':list(range(0,91,5)),'body_interferences':collisions,'hardware_interferences':hardware_hits,'gate_open_sweep_interferences':gate_sweep,'payload_insertion_interferences':insertion,'gate_blocks_on_each_end_wall_mm3':blocked,'COM_states':cmstates,'frame_size_mm':[2*(podx+6),cy+7+oy,top+2.8],'folded_thickness_with_gate_mm':top+2.8-bz+p['adhesive_t'],'open_thickness_with_gate_mm':top+2.8-bz+L+p['adhesive_t'],'physical_tests':False,'stand_validated':False,'magnetic_attachment_validated':False}
 (folder/'validation_results.json').write_text(json.dumps(result,indent=2));all_results[variant]=result
 with (folder/'BOM.csv').open('w') as f:
  wr=csv.writer(f,lineterminator='\n');wr.writerow(['part','qty','material','notes'])
  for k in parts:wr.writerow([k,quantities[k],'PETG','Silver is filament color, not titanium'])
  wr.writerow(['06_TPU_Side_Liner',2,'TPU 85-95A trial','1x110xpayload thickness; trim and tune preload'])
  for row in [('HW_Pivot_Pins',4,'Steel D3 clevis pins','Usable grip >=39mm, cross-hole/R-clip; catalog verify'),('HW_Index_Pins',2,'Steel D3 clevis pins','Same stack as pivots, lock 0/90 degrees'),('HW_Gate_Magnets',4,'Neodymium D5x2 ASSUMED','Two opposite-polarity pairs; vendor coating/temp/force unqualified'),('HW_R_Clips',6,'Steel','Tool-free retention; geometry NOT modeled, fit test'),('HW_Pin_Washers',16,'Steel/polymer','Thin fit washers; stack to measure, NOT modeled'),('HW_Mount_Screws',4,'M3 button head x10 trial','Head D<=6.2 H<=1.8; length/stack measure'),('HW_Mount_Nuts',4,'M3 nyloc + broad washers','Washers outside nut clearance; actual stack check'),('HW_Axial_Shims',8,'Polymer/steel','0.5mm each link side nominal, fit to print'),('Rear/Front edge pads',1,'Silicone/TPU','Rear free0.6/compressed0.5; front free0.5/compressed0.4; cut strips'),('Phone adhesive film',1,'Phone-case compatible structural tape/adhesive','62x62x1 envelope; material/strength NOT QUALIFIED'),('Independent phone tether',1,'Commercial','Phone case anchor; do not rely solely on frame tether slot')]:wr.writerow(row)
 # CAD-based color-separated renders; steel hardware is always gray.
 def renderdata(name,angle,scheme,phone=True,rearview=False,exploded=False,gateopen=False):
  ss=pose(angle,True,True,phone)
  if gateopen:
   for key in list(ss):
    if key=='02_Locking_Gate' or key.startswith('HW_Gate_Magnet'):
     sh=ss[key].copy();sh.translate(V(0,15,top-3.3+.6));ss[key]=sh
  if exploded:
   ss={k:s for k,s in ss.items() if not k.startswith(('REF_Adhesive','ART_'))}
   for i,(k,s) in enumerate(ss.copy().items()):
    q=s.copy();q.translate(V((i%3)*32,0,-i*5));ss[k]=q
  data={}
  for k,s in ss.items():
   color=(.035,.04,.045)
   if scheme=='titanium' and k in ['02_Locking_Gate','03_Grip_Connector','04_Link_A','04_Link_B']:color=(.48,.51,.54)
   if k.startswith('HW_'):color=(.42,.45,.48)
   if k=='REF_Payload':color=(.6,.65,.7)
   if k=='REF_Phone':color=(.14,.15,.17)
   if k=='REF_Camera':color=(.05,.055,.06)
   if k=='REF_Adhesive':color=(.18,.18,.18)
   if k=='ART_Card':color=(.10,.27,.44)
   if k=='ART_Label':color=(.92,.92,.89)
   vv,ff=s.tessellate(.2);data[k]={'vertices':[[v.x,v.y,v.z] for v in vv],'faces':[list(f) for f in ff],'color':color,'transparent':k=='REF_Payload' and prefix=='slab','metal':k.startswith('HW_')}
  (folder/'renders'/f'{name}.mesh.json').write_text(json.dumps(data))
 if variant=='direct_slab':
  for scheme in ['black','titanium']:
   renderdata(scheme+'_front',90,scheme,False);renderdata(scheme+'_rear',90,scheme,False,True);renderdata(scheme+'_folded_phone',0,scheme,True);renderdata(scheme+'_open_phone',90,scheme,True)
  renderdata('titanium_exploded',90,'titanium',False,False,True)
  renderdata('titanium_gate_open',0,'titanium',False,False,False,True)
 else:
  renderdata('black_open_phone',90,'black',True);renderdata('titanium_folded_phone',0,'titanium',True);renderdata('titanium_rear',90,'titanium',False,True)
 runpy.run_path(str(ROOT/'documents.py'),init_globals={'root':folder,'p':p,'parts':parts,'extras':extras,'result':result,'pose':pose,'geometry':{'cx':cx,'cy':cy,'ox':ox,'oy':oy,'top':top,'lipz':lipz,'podx':podx,'gatepinY':gatepinY,'forkin':forkin,'forkout':forkout,'pz':pz,'S':S,'L':L,'ir':ir,'mountxy':mountxy}})
 doc.saveAs(str(folder/'PSA_Grip_V02.FCStd'));A.closeDocument(doc.Name)
print(json.dumps({k:{x:len(v[x]) for x in ['body_interferences','hardware_interferences','gate_open_sweep_interferences','payload_insertion_interferences']} for k,v in all_results.items()},indent=2))
(ROOT/'comparison_results.json').write_text(json.dumps(all_results,indent=2))
# Existing V01 is read-only input. Build all actual CAD images in one Blender run.
if '--skip-render' not in sys.argv:
 subprocess.run(['/usr/bin/blender','-b','-t','4','--python',str(ROOT/'render_blender.py')],check=True,stdout=subprocess.DEVNULL)
for q in ROOT.rglob('*.FCBak'):q.unlink()
files=sorted(q for q in ROOT.rglob('*') if q.is_file() and q.name!='SHA256SUMS.txt')
(ROOT/'SHA256SUMS.txt').write_text('\n'.join(hashlib.sha256(q.read_bytes()).hexdigest()+'  '+str(q.relative_to(ROOT)) for q in files)+'\n')
with zipfile.ZipFile(ROOT.parent/'psa_grip_v02.zip','w',zipfile.ZIP_DEFLATED) as z:
 for q in sorted(ROOT.rglob('*')):
  if q.is_file():z.write(q,q.relative_to(ROOT.parent))
print('Generation complete; physical printing and load tests NOT performed.')

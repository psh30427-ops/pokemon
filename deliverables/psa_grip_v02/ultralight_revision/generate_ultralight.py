#!/usr/bin/python3
"""A/B/C weight comparison and manufacturing geometry. mm / g.
Actual FreeCAD solids; OEM pop-up reference envelope NOT printable mechanism.
"""
import sys,json,math,csv,itertools,runpy,subprocess
from pathlib import Path
sys.path.append('/usr/lib/freecad/lib')
import FreeCAD as A,Part,Mesh
from FreeCAD import Vector as V
R=Path(__file__).resolve().parent
DEFAULT={'slab_w':81.,'slab_h':136.,'slab_t':6.,'slab_corner_r':3.,'slab_mass_g':50.,'slab_mass_low_g':35.,'slab_mass_high_g':80.,'phone_w':71.5,'phone_h':149.6,'phone_t_with_case':9.75,'phone_and_case_g':224.,'camera_x':-34.,'camera_y':33.,'camera_w':38.,'camera_h':38.,'camera_bump_t':4.,'side_clearance':.6,'rear_pad_compressed':.4,'front_pad_compressed':.3,'PETG_density':1.27,'TPU_density':1.20,'adhesive_density':1.0,'magnet_density':7.5,'gate_magnet_d':3.,'gate_magnet_t':1.5,'gate_magnet_count':4,'magnet_epoxy_g':.12,'pad_adhesive_g':.15,'popup_mass_nominal_g':8.,'popup_mass_low_g':6.,'popup_mass_high_g':12.,'popup_upper_d':40.,'popup_lower_d':38.,'popup_closed_h':6.,'popup_open_h':22.,'popup_bond_t':.2,'phone_adhesive_t':.8,'additional_mass_target_g':30.}
f=R/'parameters.json';p=json.loads(f.read_text()) if f.exists() else DEFAULT;f.write_text(json.dumps(p,indent=2))
assert (p['gate_magnet_d'],p['gate_magnet_t'],p['gate_magnet_count'])==(3.,1.5,4), 'This gate geometry supports only D3x1.5 magnets, qty4. Redesign gate/pockets before changing these inputs.'
SPECS={'A_minimum':{'wall':1.5,'back':1.2,'lip_t':.9,'lip_w':1.4,'back_overlap':1.,'pad_t':1.2,'base_d':42.,'base_t':0.0,'rib_w':2.,'rib_t':1.2,'ribs':'horizontal','pad_len':18.,'corner_extra':0.},'B_daily':{'wall':1.8,'back':1.5,'lip_t':1.1,'lip_w':1.6,'back_overlap':1.5,'pad_t':1.5,'base_d':44.,'base_t':0.0,'rib_w':2.6,'rib_t':1.5,'ribs':'diagonal','pad_len':24.,'corner_extra':.3},'C_protective':{'wall':2.0,'back':1.9,'lip_t':1.4,'lip_w':1.8,'back_overlap':2.,'pad_t':1.9,'base_d':46.,'base_t':1.6,'rib_w':3.4,'rib_t':1.9,'ribs':'diagonal_plus_horizontal','pad_len':30.,'corner_extra':.8}}
(R/'design_specs.json').write_text(json.dumps(SPECS,indent=2))
def box(x,y,z,w,h,t):return Part.makeBox(w,h,t,V(x,y,z))
def cyl(rad,z,t,x=0,y=0):return Part.makeCylinder(rad,t,V(x,y,z))
def rounded(w,h,z,t,r):
 s=box(-w/2,-h/2,z,w,h,t);es=[e for e in s.Edges if e.BoundBox.ZLength>t-.001 and e.BoundBox.XLength<.001 and e.BoundBox.YLength<.001]
 return s.makeFillet(r,es)
def fuse(seq):
 s=seq[0]
 for q in seq[1:]:s=s.fuse(q)
 return s.removeSplitter()
def cut(s,seq):
 for q in seq:s=s.cut(q)
 return s.removeSplitter()
def rib(x,y,width,thick):
 L=math.hypot(x,y);s=box(0,-width/2,0,L,width,thick);s.rotate(V(0,0,0),V(0,0,1),math.degrees(math.atan2(y,x)));return s
def centroid(sh):
 return sum((q.CenterOfMass*q.Volume for q in sh.Solids),V())/sum(q.Volume for q in sh.Solids)
summary={}
for key,d in SPECS.items():
 root=R/key
 for folder in ['CAD','STEP_parts','STL_PRINT','drawings','renders']: (root/folder).mkdir(parents=True,exist_ok=True)
 if d['base_t']==0:
  for old in [root/'STEP_parts'/'03_Adhesive_Base.step',root/'STL_PRINT'/'03_Adhesive_Base.stl']:
   if old.exists():old.unlink()
 for oldname in ['silver_rear_open','silver_folded_phone','silver_open_phone']:
  for suffix in ['.mesh.json','.png']:
   old=root/'renders'/(oldname+suffix)
   if old.exists():old.unlink()
 w,h,t=p['slab_w'],p['slab_h'],p['slab_t'];cx=w/2+p['side_clearance'];cy=h/2+p['side_clearance'];ox=cx+d['wall'];oy=cy+d['wall'];back=d['back'];lipz=back+p['rear_pad_compressed']+t+p['front_pad_compressed'];top=lipz+d['lip_t'];headtop=lipz+6.6;podx=ox-6.;magY=cy+2.4
 # The reference image drives a continuous rounded outer outline. No external locking ears.
 totalH=oy+cy+6.;centerY=(cy+6.-oy)/2
 outline=rounded(2*ox,totalH,0,top,4);outline.translate(V(0,centerY,0))
 tall_outline=rounded(2*ox,totalH,0,headtop,4);tall_outline.translate(V(0,centerY,0))
 shell=cut(outline,[box(-cx,-cy,back,2*cx,2*cy,top+1),box(-ox-1,cy,back,2*ox+2,7,top+1),rounded(w-2*d['back_overlap'],h-2*d['back_overlap'],-1,back+2,2)])
 lips=[box(-cx,-cy+1,lipz,d['lip_w'],2*cy-2.7,d['lip_t']),box(cx-d['lip_w'],-cy+1,lipz,d['lip_w'],2*cy-2.7,d['lip_t']),box(-cx,-cy,lipz,2*cx,d['lip_w'],d['lip_t'])]
 endpoints=[(-ox+.8,0),(ox-.8,0)] if d['ribs']=='horizontal' else [(sx*(ox-2),sy*(oy-3)) for sx,sy in itertools.product([-1,1],[-1,1])]
 if d['ribs']=='diagonal_plus_horizontal':endpoints += [(-ox+.8,0),(ox-.8,0)]
 ribs=[rib(x,y,d['rib_w'],d['rib_t']) for x,y in endpoints]
 if key=='B_daily':
  for x,y in endpoints:
   L=math.hypot(x,y);fin=box(20.5,-.8,-4,L-20.5,1.6,4)
   edges=[e for e in fin.Edges if abs(e.Length-(L-20.5))<.001 and abs(e.BoundBox.ZMin+4)<.001 and abs(e.BoundBox.ZMax+4)<.001]
   fin=fin.makeFillet(.3,edges);fin.rotate(V(0,0,0),V(0,0,1),math.degrees(math.atan2(y,x)));ribs.append(fin)
 pods=[box(x-4.3,cy+.1,lipz,8.6,5.9,5.4).common(tall_outline) for x in [-podx,podx]]
 sidebridges=[box(x,cy-3,0,d['wall'],9,headtop-1.2).common(tall_outline) for x in [-ox,cx]]
 podties=[box(x,cy+.1,lipz,3.2,4.5,5.4).common(tall_outline) for x in [-ox,podx+2.8]]
 frame=fuse([shell]+lips+ribs+pods+sidebridges+podties+[cyl(21,-d['pad_t'],d['pad_t'])])
 tools=[]
 for x in [-podx,podx]:tools += [box(x-2.8,cy+.1,lipz+2.3,5.6,4.6,headtop+1),cyl(1.6,lipz+.6,1.8,x,magY)]
 frame=cut(frame,tools)
 # Corner material stays inside the clean outline: local rear gussets instead of ears.
 if d['corner_extra']:
  for sx in [-1,1]:
   band=box(sx*(ox-2.5)-2.5,-oy,0,5,8,d['corner_extra'])
   band=band.common(outline)
   frame=fuse([frame,band])
 # Flush upper gate, open by lifting +Z. Closed +Y escape is blocked by two shoulders.
 gatecap=tall_outline.common(box(-ox-1,cy-1.2,headtop-1,2*ox+2,8,1))
 lowercap=outline.common(box(-cx,cy-1.2,lipz,2*cx,1.25,d['lip_t']))
 bridge=box(-podx+4.4,cy,lipz,2*(podx-4.4),6,d['lip_t'])
 stops=[box(x,cy,back+.4,6,.8,lipz-back-.4) for x in [-28,22]]
 skirt=box(-podx+4.4,cy+5,lipz,2*(podx-4.4),1,headtop-lipz)
 gate=fuse([gatecap,lowercap,bridge,skirt]+stops+[box(x-2.5,cy+.4,lipz+2.6,5,4,3) for x in [-podx,podx]])
 gate=cut(gate,[cyl(1.6,lipz+2.5,1.8,x,magY) for x in [-podx,podx]])
 # Black TPU inner edging, shallow groove. Free material mass is counted in full.
 trimring=cut(rounded(2*(cx-.1),2*(cy-.1),0,.45,3),[rounded(2*(cx-1.1),2*(cy-1.1),-1,2,2)])
 trimU=trimring.common(box(-cx-1,-cy-1,-1,2*cx+2,2*cy-.75,3))
 trimG=trimring.common(box(-cx-1,cy-1.65,-1,2*cx+2,3,3))
 # Ensure a 0.10mm butt gap at the moving gate.
 trimU=cut(trimU,[box(-cx-1,cy-1.75,-1,2*cx+2,4,3)])
 for body,trim in [('frame',trimU),('gate',trimG)]:
  groove=trim.copy();groove.translate(V(0,0,top-.25))
  if body=='frame':frame=cut(frame,[groove])
  else:gate=cut(gate,[groove])
 zu=-d['pad_t']-p['popup_bond_t'];basebond=p['popup_bond_t'] if d['base_t']>0 else 0.;bz=zu-p['popup_closed_h']-basebond-d['base_t']
 parts={'01_Bumper_Frame':frame,'02_Magnetic_Gate':gate}
 if d['base_t']>0:
  base=cyl(d['base_d']/2,bz,d['base_t']);parts['03_Adhesive_Base']=base
 pads={'04_TPU_Side_Pad':rounded(.8,d['pad_len'],0,t,.25),'05_TPU_Rear_Pad':rounded(8,4,0,.5,.5),'06_TPU_Front_Pad':rounded(8,2,0,.4,.4),'07_TPU_Inner_Trim_U':trimU,'08_TPU_Gate_Trim':trimG}
 def pose(ext,graphics=False,phone=True):
  zl=zu-ext;lowerbase=zl-basebond-d['base_t'];mid=(ext-3)/2
  popup=fuse([cyl(p['popup_upper_d']/2,zu-1.5,1.5),cyl(p['popup_lower_d']/2,zl,1.5),Part.makeCone(16,8,mid,V(0,0,zl+1.5)),Part.makeCone(8,16,mid,V(0,0,zl+1.5+mid))])
  adhR=d['base_d']/2-1 if d['base_t']>0 else p['popup_lower_d']/2-1
  tu=trimU.copy();tu.translate(V(0,0,top-.25));tg=trimG.copy();tg.translate(V(0,0,top-.25))
  ss={'01_Bumper_Frame':frame,'02_Magnetic_Gate':gate,'TPU_Trim_U':tu,'TPU_Gate_Trim':tg,'REF_OEM_Popup_NOT_PRINTABLE':popup,'REF_Payload':rounded(w,h,back+p['rear_pad_compressed'],t,p['slab_corner_r']),'REF_Upper_Film':cyl(19,zu,p['popup_bond_t']),'REF_Phone_Adhesive':cyl(adhR,lowerbase-p['phone_adhesive_t'],p['phone_adhesive_t'])}
  if d['base_t']>0:
   bs=base.copy();bs.translate(V(0,0,p['popup_closed_h']-ext));ss['03_Adhesive_Base']=bs;ss['REF_Lower_Film']=cyl(18,zl-p['popup_bond_t'],p['popup_bond_t'])
  for i,x in enumerate([-podx,podx]):ss[f'HW_Frame_Magnet{i}']=cyl(1.5,lipz+.8,1.5,x,magY);ss[f'HW_Gate_Magnet{i}']=cyl(1.5,lipz+2.6,1.5,x,magY)
  if phone:
   pb=lowerbase-p['phone_adhesive_t'];ss['REF_Phone']=rounded(p['phone_w'],p['phone_h'],pb-p['phone_t_with_case'],p['phone_t_with_case'],8);ss['REF_Camera']=box(p['camera_x'],p['camera_y'],pb,p['camera_w'],p['camera_h'],p['camera_bump_t'])
  if graphics:
   z=back+p['rear_pad_compressed']+t/2;ss['ART_Card']=box(-31.5,-53,z,63,88,.12);ss['ART_Label']=box(-35,h/2-26,z,70,19,.12)
  return ss
 # Weigh every retained part. Generic OEM mass is a separate assumption, not CAD plastic volume.
 weights={};checks={}
 for name,s in {**parts,**pads}.items():
  assert s.isValid() and len(s.Solids)==1,(key,name,'invalid shape',s.isValid(),len(s.Solids),[z.Volume for z in s.Solids])
  density=p['TPU_density'] if name in pads else p['PETG_density'];qty=1 if name.startswith(('07','08')) else (4 if name in pads else 1);mass=s.Volume/1000*density
  weights[name]={'volume_mm3':s.Volume,'density_g_cm3':density,'quantity':qty,'unit_mass_g':mass,'total_mass_g':mass*qty,'status':'CAD_VOLUME x ASSUMED_DENSITY'}
  s.exportStep(str(root/'STEP_parts'/f'{name}.step'));q=s.copy()
  if name=='01_Bumper_Frame':q.rotate(V(0,0,0),V(0,1,0),90)
  if name=='02_Magnetic_Gate':q.rotate(V(0,0,0),V(1,0,0),-90)
  if name=='04_TPU_Side_Pad':q.rotate(V(0,0,0),V(0,1,0),90)
  B=q.BoundBox;q.translate(V(-B.XMin,-B.YMin,-B.ZMin));Mesh.Mesh(q.tessellate(.10)).write(str(root/'STL_PRINT'/f'{name}.stl'));m=Mesh.Mesh(str(root/'STL_PRINT'/f'{name}.stl'));reread=Part.read(str(root/'STEP_parts'/f'{name}.step'))
  assert m.isSolid() and reread.isValid()
  err=abs(abs(m.Volume)-s.Volume)/s.Volume;assert err<.002
  checks[name]={'valid_single_solid':True,'STL_closed':True,'step_volume_error_mm3':abs(reread.Volume-s.Volume),'stl_relative_volume_error':err,'print_bounds_mm':[q.BoundBox.XLength,q.BoundBox.YLength,q.BoundBox.ZLength]}
 # Fixed purchasing/consumable weights; film and magnets computed from actual shape volumes.
 pp=pose(p['popup_closed_h']);adhesives=sum(pp[k].Volume for k in ['REF_Upper_Film','REF_Lower_Film','REF_Phone_Adhesive'] if k in pp)/1000*p['adhesive_density'];magnetmass=4*math.pi*1.5**2*1.5/1000*p['magnet_density'];printed=sum(v['total_mass_g'] for v in weights.values());fixed=printed+adhesives+magnetmass+p['magnet_epoxy_g']+p['pad_adhesive_g'];extra=fixed+p['popup_mass_nominal_g']
 allowed=p['additional_mass_target_g']-fixed
 massinfo={'CAD_parts_and_pads_g':printed,'adhesive_g':adhesives,'magnets_g':magnetmass,'epoxy_g':p['magnet_epoxy_g'],'pad_adhesive_g':p['pad_adhesive_g'],'fixed_excluding_OEM_g':fixed,'OEM_popup_nominal_g':p['popup_mass_nominal_g'],'additional_nominal_g':extra,'additional_low_g':fixed+p['popup_mass_low_g'],'additional_high_g':fixed+p['popup_mass_high_g'],'max_popup_mass_for_30g_g':allowed,'with_slab_nominal_g':extra+p['slab_mass_g'],'with_slab_low_g':fixed+p['popup_mass_low_g']+p['slab_mass_low_g'],'with_slab_high_g':fixed+p['popup_mass_high_g']+p['slab_mass_high_g'],'with_phone_nominal_g':extra+p['slab_mass_g']+p['phone_and_case_g'],'nominal_target_pass':extra<=p['additional_mass_target_g'],'range_upper_target_pass':fixed+p['popup_mass_high_g']<=p['additional_mass_target_g']}
 # Shape checks sample the external purchased mechanism envelope, not its true internal motion.
 hits=[]
 for i in range(17):
  ext=p['popup_closed_h']+i*(p['popup_open_h']-p['popup_closed_h'])/16;ss=pose(ext)
  for a,b in itertools.combinations(ss,2):
   vol=ss[a].common(ss[b]).Volume
   if vol>1e-5:hits.append({'extension_mm':ext,'a':a,'b':b,'volume_mm3':vol})
 insertion=[];gatesweep=[];lift=frame.BoundBox.ZMax-gate.BoundBox.ZMin+.6
 for n in range(16):
  payload=pp['REF_Payload'].copy();payload.translate(V(0,n*(h+10)/15,0));vol=payload.common(frame).Volume
  if vol>1e-5:insertion.append({'sample':n,'volume_mm3':vol})
  for phase in [0,1]:
   q=gate.copy();q.translate(V(0,n*(h+10)/15 if phase else 0,lift if phase else n*lift/15));vol=q.common(frame).Volume
   if vol>1e-5:gatesweep.append({'phase':phase,'sample':n,'volume_mm3':vol})
 blocked=[]
 for x in [-podx,podx]:blocked.append(box(x-2.5,cy+.4+1,lipz+2.6,5,4,3).common(frame).Volume)
 assert all(x>0 for x in blocked)
 escaping=pp['REF_Payload'].copy();escaping.translate(V(0,2,0));retention=escaping.common(gate).Volume;assert retention>0
 thickness=max(gate.BoundBox.ZMax,top+.2)-(bz-p['phone_adhesive_t']);expanded=thickness+p['popup_open_h']-p['popup_closed_h']
 # Parametric cutout flexibility proxy: minimum rib section and simple cantilever bound.
 F=max(p['phone_and_case_g'],extra+p['slab_mass_g'])/1000*9.81*5;M=F*.04
 minsec=d['rib_w']*d['rib_t'];sectionmod=d['rib_w']*d['rib_t']**2/6
 if key=='B_daily':
  area1=d['rib_w']*d['rib_t'];area2=1.*4;cg=(area1*d['rib_t']/2-area2*2)/(area1+area2);inertia=d['rib_w']*d['rib_t']**3/12+area1*(d['rib_t']/2-cg)**2+1.*4**3/12+area2*(-2-cg)**2;sectionmod=inertia/max(d['rib_t']-cg,4+cg)
 result={'design':key,'specs':d,'weights':weights,'mass':massinfo,'printed_checks':checks,'sampled_interferences':hits,'insertion_interferences':insertion,'gate_open_interferences':gatesweep,'gate_shoulder_blocks_mm3':blocked,'closed_gate_payload_escape_block_mm3':retention,'gate_lift_travel_mm':lift,'folded_accessory_thickness_mm':thickness,'open_accessory_thickness_mm':expanded,'frame_only_thickness_mm':headtop,'payload_assumed_mm':[w,h,t],'gate_magnet_pair_force_verified':False,'OEM_popup_selected':False,'OEM_mechanism_STL_exported':False,'physical_strength_tests_run':False,'rib_model':{'minimum_section_mm2':minsec,'weak_axis_section_modulus_mm3':sectionmod,'assumed_5g_larger_side_load_N':F,'moment_40mm_Nm':M,'equal_share_bending_bound_MPa':M*1000/(len(endpoints)*sectionmod),'note':'Crude moment/section bound, not FEA, not a pass. Actual ring/slab contact changes loading.'}}
 assert not hits and not insertion and not gatesweep, (key,'unintended CAD overlap')
 cgs={}
 for ext in [p['popup_closed_h'],p['popup_open_h']]:
  ps=pose(ext);items=[]
  for name,ws in weights.items():
   if name in parts:
    shape=ps.get(name,parts[name]);vec=centroid(shape)
   elif name=='07_TPU_Inner_Trim_U':vec=centroid(ps['TPU_Trim_U'])
   elif name=='08_TPU_Gate_Trim':vec=centroid(ps['TPU_Gate_Trim'])
   else:vec=V(0,0,back+.4+t/2 if name.startswith('04') else (back+.2 if name.startswith('05') else lipz-.15))
   items.append((ws['total_mass_g'],vec))
  for name in ['REF_Upper_Film','REF_Lower_Film','REF_Phone_Adhesive']:
   if name in ps:items.append((ps[name].Volume/1000*p['adhesive_density'],centroid(ps[name])))
  for name,sh in ps.items():
   if name.startswith('HW_'):items.append((sh.Volume/1000*p['magnet_density'],centroid(sh)))
  items.extend([(p['magnet_epoxy_g'],V(0,magY,lipz+2)),(p['pad_adhesive_g'],V(0,0,back+.3)),(p['popup_mass_nominal_g'],centroid(ps['REF_OEM_Popup_NOT_PRINTABLE'])),(p['slab_mass_g'],centroid(ps['REF_Payload']))])
  def cog(seq):
   total=sum(m for m,v in seq);vv=sum((v*m for m,v in seq),V())/total;return {'mass_g':total,'xyz_mm':[vv.x,vv.y,vv.z]}
  acc=cog(items);combined=cog(items+[(p['phone_and_case_g'],centroid(ps['REF_Phone']))])
  cgs[str(ext)]={'accessory_with_slab':acc,'with_phone':combined,'basis':'ASSUMED masses, compressed pad centers approximated; OEM external-envelope centroid proxy'}
 result['center_of_mass_by_extension']=cgs
 (root/'validation_results.json').write_text(json.dumps(result,indent=2));summary[key]=result
 # Native document with clearly flagged purchased references; no OEM bellows printable export.
 doc=A.newDocument(key);sheet=doc.addObject('Spreadsheet::Sheet','Parameters')
 for row,(k,v) in enumerate({**p,**d}.items(),1):sheet.set('A'+str(row),k);sheet.set('B'+str(row),str(v));sheet.set('C'+str(row),'ASSUMED / model input')
 for name,s in pp.items():
  ob=doc.addObject('Part::Feature','Part_'+name);ob.Label=name;ob.Shape=s;ob.addProperty('App::PropertyString','Status').Status='PRINT' if name in parts or name.startswith('TPU_') else 'REFERENCE / PURCHASED / UNQUALIFIED'
 doc.recompute();doc.saveAs(str(root/'CAD'/'PSA_Grip_Ultralight.FCStd'));Part.Compound(list(parts.values())+[pp['TPU_Trim_U'],pp['TPU_Gate_Trim']]).exportStep(str(root/'CAD'/'Printed_Assembly.step'));Part.Compound([s for k,s in pose(p['popup_open_h'],False,False).items() if k!='REF_Payload']).exportStep(str(root/'CAD'/'Assembly_With_OEM_Reference.step'));A.closeDocument(doc.Name)
 with (root/'BOM.csv').open('w') as f:
  wr=csv.writer(f,lineterminator='\n');wr.writerow(['part','qty','volume_mm3','density_g_cm3','unit_g','total_g','basis'])
  for k,v in weights.items():wr.writerow([k,v['quantity'],round(v['volume_mm3'],3),v['density_g_cm3'],round(v['unit_mass_g'],4),round(v['total_mass_g'],4),v['status']])
  for row in [('OEM_popup',1,'','',p['popup_mass_nominal_g'],p['popup_mass_nominal_g'],'ASSUMED range in parameters.json, not measured'),('All_bonding_films',1,'',p['adhesive_density'],adhesives,adhesives,'CAD volume x assumed density'),('Gate_magnets_D3x1.5',4,math.pi*1.5**2*1.5,p['magnet_density'],magnetmass/4,magnetmass,'CAD volume x assumed density, dimensions unqualified'),('Magnet_epoxy',1,'','',p['magnet_epoxy_g'],p['magnet_epoxy_g'],'DISPENSED MASS ASSUMED'),('Pad_and_trim_adhesive',1,'','',p['pad_adhesive_g'],p['pad_adhesive_g'],'DISPENSED MASS ASSUMED')]:wr.writerow(row)
 # Render chosen B, with A/C retained in comparable engineering views.
 def render(name,ext,phone=True,mode="normal"):
  data={}
  for k,s in pose(ext,True,phone).items():
   if mode=='empty' and (k.startswith(('REF_Payload','ART_')) or k=='REF_OEM_Popup_NOT_PRINTABLE'):continue
   s=s.copy()
   if mode=='explode':
    if k in ['REF_Payload','ART_Card','ART_Label']:s.translate(V(0,0,30))
    if k=='02_Magnetic_Gate' or k=='TPU_Gate_Trim' or k.startswith('HW_Gate'):s.translate(V(0,18,15))
    if k=='REF_OEM_Popup_NOT_PRINTABLE':s.translate(V(0,0,-25))
   color=(.48,.035,.02) if k in ['01_Bumper_Frame','02_Magnetic_Gate'] else (.018,.02,.022)
   if k=='REF_Payload':color=(.65,.7,.75)
   if k=='REF_Phone':color=(.12,.13,.15)
   if k=='ART_Card':color=(.08,.24,.42)
   if k=='ART_Label':color=(.92,.92,.88)
   vv,ff=s.tessellate(.2);data[k]={'vertices':[[v.x,v.y,v.z] for v in vv],'faces':[list(t) for t in ff],'color':color,'transparent':k=='REF_Payload'}
  (root/'renders'/f'{name}.mesh.json').write_text(json.dumps(data))
 render('red_rear_open',p['popup_open_h'],False)
 if key=='B_daily':
  render('red_front',p['popup_closed_h'],False);render('red_folded_phone',p['popup_closed_h']);render('red_open_phone',p['popup_open_h']);render('red_empty_front',p['popup_closed_h'],False,'empty');render('red_rear_exploded',p['popup_open_h'],False,'explode')
 if '--geometry-only' not in sys.argv:runpy.run_path(str(R/'documents.py'),init_globals={'r':root,'p':p,'d':d,'result':result,'parts':parts,'pads':pads,'pose':pose,'g':{'cx':cx,'cy':cy,'ox':ox,'oy':oy,'top':top,'headtop':headtop,'lipz':lipz,'podx':podx,'magY':magY,'zu':zu,'bz':bz,'rib_endpoints':endpoints}})
(R/'comparison_results.json').write_text(json.dumps(summary,indent=2))
if '--geometry-only' not in sys.argv:runpy.run_path(str(R/'comparison_report.py'),init_globals={'root':R,'p':p,'results':summary})
print(json.dumps({k:v['mass'] for k,v in summary.items()},indent=2))
if '--skip-render' not in sys.argv and '--geometry-only' not in sys.argv:subprocess.run(['/usr/bin/blender','-b','-t','4','--python',str(R/'render_blender.py')],check=True,stdout=subprocess.DEVNULL)
for pth in R.rglob('*.FCBak'):pth.unlink()

if '--geometry-only' not in sys.argv:
 subprocess.run(['/usr/bin/python3',str(R/'verify_exports.py')],check=True)
 runpy.run_path(str(R/'comparison_report.py'),init_globals={'root':R,'p':p,'results':summary})

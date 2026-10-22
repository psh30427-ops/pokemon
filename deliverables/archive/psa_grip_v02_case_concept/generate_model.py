#!/usr/bin/python3
"""V02: open ivory rails and purchased circular pop-up grip envelope.
Run /usr/bin/python3 generate_model.py (FreeCAD, ReportLab, Blender, Poppler).
"""
from pathlib import Path
import sys,os,json,csv,math,itertools,subprocess,hashlib,zipfile,shutil
sys.path.append('/usr/lib/freecad/lib')
import FreeCAD as A,Part,Mesh
from FreeCAD import Vector as V
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A3,landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
R=Path(__file__).resolve().parent
for d in ['parts','STL_PRINT','drawings','renders']: (R/d).mkdir(exist_ok=True)
P={'case_w':86.,'case_h':142.,'case_t':11.,'clear_xy':1.,'back_t':3.,'pad_back':.4,'pad_top_clear':.4,'lip_t':1.6,'wall_t':3.,'outer_h':154.,'rim_window_w':84.,'rim_window_h':140.,'bridge_w':60.,'bridge_h':60.,'mount_plate_d':60.,'mount_plate_t':2.,'commercial_grip_d':38.,'commercial_grip_closed':6.,'commercial_grip_open':22.,'mag_module_d':56.,'mag_module_t':2.,'phone_w':71.5,'phone_h':149.6,'phone_t':8.25,'phone_case_t':1.5,'camera_w':38.,'camera_h':38.,'camera_t':4.,'camera_x':-15.,'camera_y':52.,'case_payload_g':120.,'phone_and_case_g':224.,'grip_g':15.,'mag_module_g':18.,'hardware_and_pad_g':10.,'petg_density':1.27}
pf=R/'design_parameters.json';p=json.loads(pf.read_text()) if pf.exists() else P;pf.write_text(json.dumps(p,indent=2))
w,h,t=p['case_w'],p['case_h'],p['case_t'];cx=w/2+p['clear_xy'];cy=h/2+p['clear_xy'];ox=cx+p['wall_t'];oy=p['outer_h']/2;b=p['back_t'];lipz=b+p['pad_back']+t+p['pad_top_clear'];top=lipz+p['lip_t'];pt=p['mount_plate_t'];cd=p['mount_plate_d'];holesXY=[(25,0),(-25,0),(0,25),(0,-25)]
def box(x,y,z,dx,dy,dz):return Part.makeBox(dx,dy,dz,V(x,y,z))
def cylinder(rad,z,height,x=0,y=0):return Part.makeCylinder(rad,height,V(x,y,z))
def fuse(items):
 s=items[0]
 for q in items[1:]:s=s.fuse(q)
 return s.removeSplitter()
def cut(s,items):
 for q in items:s=s.cut(q)
 return s.removeSplitter()
def rounded(w,h,z,th,r):
 s=box(-w/2,-h/2,z,w,h,th)
 edges=[e for e in s.Edges if e.BoundBox.ZLength>th-.001 and e.BoundBox.XLength<.001 and e.BoundBox.YLength<.001]
 return s.makeFillet(r,edges)
# Open rear perimeter, connected central mounting bridge, slim side capture rails.
rim=cut(rounded(2*ox,2*oy,0,b,5),[rounded(p['rim_window_w'],p['rim_window_h'],-1,b+2,3)])
bridge=fuse([rounded(p['bridge_w'],p['bridge_h'],0,b,8),box(-ox,-12,0,2*ox,24,b)])
body=fuse([rim,bridge,box(-ox,-oy,b,2*ox,oy-cy,top-b),box(-ox,-cy,b,3,2*cy-3,top-b),box(cx,-cy,b,3,2*cy-3,top-b),box(-cx,-cy,lipz,2.5,2*cy-3,p['lip_t']),box(cx-2.5,-cy,lipz,2.5,2*cy-3,p['lip_t'])])
tools=[]
for x,y in holesXY:
 tools.extend([cylinder(1.7,-1,b+2,x,y),cylinder(3.1,b-1.8,2.8,x,y)])
for x in [-40,40]:tools.append(cylinder(1.7,-1,top+2,x,cy+2.5))
tools.append(box(-3,-oy+.5,-1,6,2,b+2))
body=cut(body,tools)
gate=fuse([box(-ox,cy,b,2*ox,oy-cy,2),box(-ox,cy,b+2,2*ox,oy-cy,top-b-2),box(-ox,cy-2.5,lipz,2*ox,oy-cy+2.5,p['lip_t'])])
gate=cut(gate,[cylinder(1.7,-1,top+2,x,cy+2.5) for x in [-40,40]])
plate=cut(cylinder(cd/2,-pt,pt),[cylinder(1.7,-pt-1,pt+2,x,y) for x,y in holesXY])
# Two mounting faces for a purchased pop-up grip. No untested printed bellows.
basez=-2*pt-p['commercial_grip_closed']
base=cut(cylinder(cd/2,basez,pt),[cylinder(1.7,basez-1,pt+2,x,y) for x,y in holesXY])
parts={'01_open_cradle':body,'02_top_gate':gate,'03_grip_mount_plate':plate,'04_phone_base_adapter':base}
case=rounded(w,h,b+p['pad_back'],t,2) # nominal R2 ASSUMED only; envelope not measured.
def state(extension):
 shift=extension-p['commercial_grip_closed'];basecopy=base.copy();basecopy.translate(V(0,0,-shift))
 zlow=-pt-extension
 cap1=cylinder(p['commercial_grip_d']/2,-pt-2,2);cap2=cylinder(p['commercial_grip_d']/2,zlow,2)
 center=-pt-extension/2
 lower=Part.makeCone(16,9,(extension-4)/2,V(0,0,zlow+2));upper=Part.makeCone(9,16,(extension-4)/2,V(0,0,center))
 grip=fuse([cap1,cap2,lower,upper])
 magz=basez-shift-p['mag_module_t'];mag=cylinder(p['mag_module_d']/2,magz,p['mag_module_t'])
 phone=rounded(p['phone_w'],p['phone_h'],magz-p['phone_t']-p['phone_case_t'],p['phone_t']+p['phone_case_t'],8)
 camera=box(p['camera_x']-p['camera_w']/2,p['camera_y']-p['camera_h']/2,magz,p['camera_w'],p['camera_h'],p['camera_t'])
 return {'01_open_cradle':body,'02_top_gate':gate,'03_grip_mount_plate':plate,'04_phone_base_adapter':basecopy,'REF_existing_case':case,'REF_purchased_grip_ENVELOPE':grip,'REF_magnet_ENVELOPE':mag,'REF_phone_ENVELOPE':phone,'REF_camera_ASSUMED':camera}
colors={k:(.73,.69,.59) for k in parts};colors.update({'REF_existing_case':(.46,.48,.50),'REF_purchased_grip_ENVELOPE':(.78,.73,.64),'REF_magnet_ENVELOPE':(.3,.3,.3),'REF_phone_ENVELOPE':(.20,.21,.23),'REF_camera_ASSUMED':(.1,.1,.12)})
doc=A.newDocument('PSA_Grip_V02');sheet=doc.addObject('Spreadsheet::Sheet','Parameters')
for i,(k,v) in enumerate(p.items(),1):sheet.set('A'+str(i),k);sheet.set('B'+str(i),str(v));sheet.set('C'+str(i),'SELLER' if k in ['case_w','case_h','case_t'] else 'ASSUMED')
for k,s in state(p['commercial_grip_closed']).items():
 o=doc.addObject('Part::Feature','Part_'+k);o.Label=k;o.Shape=s;o.addProperty('App::PropertyString','Status').Status='PROTOTYPE' if k in parts else 'REFERENCE ONLY - NOT A MANUFACTURED DESIGN'
doc.recompute();doc.saveAs(str(R/'assembly.FCStd'));Part.Compound(list(parts.values())).exportStep(str(R/'assembly.step'))
checks={};mass={}
for k,s in parts.items():
 assert s.isValid() and len(s.Solids)==1
 s.exportStep(str(R/'parts'/f'{k}.step'));m=Mesh.Mesh(s.tessellate(.12));m.write(str(R/'parts'/f'{k}.stl'))
 # Side-up frame/gate and flat plate/base. All translated to Z=0 and positive XY.
 sh=s.copy()
 if k=='01_open_cradle':sh.rotate(V(0,0,0),V(0,1,0),90)
 if k=='02_top_gate':sh.rotate(V(0,0,0),V(1,0,0),90)
 bb=sh.BoundBox;sh.translate(V(-bb.XMin,-bb.YMin,-bb.ZMin));out=Mesh.Mesh(sh.tessellate(.12));out.write(str(R/'STL_PRINT'/f'{k}_PRINT_mm.stl'))
 rr=Part.read(str(R/'parts'/f'{k}.step'));check=Mesh.Mesh(str(R/'STL_PRINT'/f'{k}_PRINT_mm.stl'))
 assert rr.isValid() and check.isSolid()
 mass[k]=s.Volume/1000*p['petg_density']
 checks[k]={'valid':s.isValid(),'solid_count':len(s.Solids),'stl_closed':check.isSolid(),'volume_mm3':s.Volume,'step_volume_error_mm3':abs(rr.Volume-s.Volume),'print_size_mm':[sh.BoundBox.XLength,sh.BoundBox.YLength,sh.BoundBox.ZLength],'mass_solid_equiv_g':mass[k]}
collisions=[]
for extension in range(6,23):
 ss=state(extension)
 for a,bn in itertools.combinations(ss,2):
  v=ss[a].common(ss[bn]).Volume
  if v>1e-5:collisions.append({'extension_mm':extension,'a':a,'b':bn,'intersection_mm3':v})
# Mass positions: frame, case, purchased envelopes. Commercial attachment/hardware simplified.
com={}
for e in [6,22]:
 ss=state(e);weighted=[]
 for k in parts:
  so=ss[k].Solids;cm=V(*[sum(q.Volume*getattr(q.CenterOfMass,a) for q in so)/ss[k].Volume for a in ['x','y','z']]);weighted.append((mass[k],cm))
 for k,ma in [('REF_existing_case',p['case_payload_g']),('REF_purchased_grip_ENVELOPE',p['grip_g']),('REF_magnet_ENVELOPE',p['mag_module_g']),('REF_phone_ENVELOPE',p['phone_and_case_g'])]:
  sh=ss[k];so=sh.Solids;cm=V(*[sum(q.Volume*getattr(q.CenterOfMass,a) for q in so)/sh.Volume for a in ['x','y','z']]);weighted.append((ma,cm))
 weighted.append((p['hardware_and_pad_g'],V(0,0,-1)))
 total=sum(x[0] for x in weighted);com[str(e)]={'mass_g':total,'COM_mm':[sum(m*getattr(c,a) for m,c in weighted)/total for a in ['x','y','z']]}
gate_ligament=oy-(cy+2.5)-1.7
assert gate_ligament>=.7, 'Gate bolt edge ligament too small'
result={'gate_bolt_min_edge_ligament_mm':gate_ligament,'parts':checks,'interferences':collisions,'sampled_grip_extension_mm':list(range(6,23)),'assembly_COM':com,'folded_accessory_thickness_mm':top+2*pt+p['commercial_grip_closed']+p['mag_module_t'],'open_accessory_thickness_mm':top+2*pt+p['commercial_grip_open']+p['mag_module_t'],'purchased_grip_design':False,'magnetic_module_matched':False,'physical_tests_run':False}
(R/'validation_results.json').write_text(json.dumps(result,indent=2))
with (R/'parameters.csv').open('w') as f:
 wr=csv.writer(f,lineterminator='\n');wr.writerow(['name','value','unit','status','source'])
 for k,v in p.items():wr.writerow([k,v,'g' if k.endswith('_g') else ('g/cm3' if 'density' in k else 'mm'),'SELLER_DECLARED' if k in ['case_w','case_h','case_t'] else 'ASSUMED','User seller specification' if k in ['case_w','case_h','case_t'] else 'Design assumption, measure/qualify before manufacture'])
with (R/'BOM.csv').open('w') as f:
 wr=csv.writer(f,lineterminator='\n');wr.writerow(['part','qty','specification','estimated_g','status'])
 for k in parts:wr.writerow([k,1,'PETG prototype',round(mass[k],2),'PRINT'])
 for row in [('Existing case + slab',1,'86x142x11 magnetic front/back closure',120,'NOT PRINTED / mass assumed'),('Purchased pop-up grip',1,'D38; folded6/open22; two flat end mounting faces',15,'NOT SELECTED; drawing envelope only'),('MagSafe compatible module',1,'D56x2 envelope',18,'NOT SELECTED; base connection unqualified'),('Frame/plate bolts',4,'M3 button head height<=1.8, head D<=6.2; approx M3x10 with nyloc','','CONFIRM STACK'),('Gate bolts',2,'M3x12 + washers/nyloc nuts','','CONFIRM STACK'),('Pads + hardware',1,'Soft liner .6 free / .4 compressed target',10,'ASSUMED mass; case adhesive forbidden'),('Manufacturer approved grip attachment',2,'To new adapter plates only; mechanical/prequalified adhesive interfaces','','TBD PURCHASE MODULE'),('Phone tether',1,'Independent phone-case tether point','','REQUIRED FOR DUMMY TEST')]:wr.writerow(row)
# Actual CAD tessellations for Blender reference renders.
def meshdata(name,shapes):
 out={}
 for k,s in shapes.items():
  vv,ff=s.tessellate(.2);out[k]={'vertices':[[v.x,v.y,v.z] for v in vv],'faces':[list(f) for f in ff],'color':colors.get(k,(.7,.7,.7))}
 (R/'renders'/f'{name}.mesh.json').write_text(json.dumps(out))
meshdata('front_deployed',state(22));meshdata('front_folded',state(6));meshdata('rear_deployed',{k:s for k,s in state(22).items() if k not in ['REF_phone_ENVELOPE','REF_camera_ASSUMED','REF_magnet_ENVELOPE']});meshdata('rear_folded',{k:s for k,s in state(6).items() if k not in ['REF_phone_ENVELOPE','REF_camera_ASSUMED','REF_magnet_ENVELOPE']})
ex={}
for i,(k,s) in enumerate(state(22).items()):
 if k in ['REF_phone_ENVELOPE','REF_camera_ASSUMED']:continue
 q=s.copy();q.translate(V((i%2)*65,0,-i*15));ex[k]=q
meshdata('exploded',ex)
# Dimensioned A3 preliminary sheets, all views generated from real edges.
pdfmetrics.registerFont(UnicodeCIDFont('HYSMyeongJo-Medium'));W,H=landscape(A3);c=canvas.Canvas(str(R/'drawings'/'PSA_grip_V02_A3.pdf'),pagesize=(W,H))
def text(x,y,s,n=10):c.setFont('HYSMyeongJo-Medium',n);c.drawString(x,y,s.replace('·',' / '))
def page(title,num):
 c.rect(24,24,W-48,H-48);text(36,H-46,title,17);text(36,H-68,'예비 시제품용 — 실측 및 시험 전 제작 확정 금지',12);text(36,36,f'PSA GRIP V02 | {num} | A3 | mm | Do not scale PDF')
def view(shapes,x,y,axes,scale,label):
 text(x-85,y+180,label)
 for s in shapes:
  for e in s.Edges:
   pts=e.discretize(Deflection=.2)
   if len(pts)<2:continue
   path=c.beginPath()
   for i,v in enumerate(pts):
    a=[v.x,v.y,v.z];q=(x+a[axes[0]]*scale,y+a[axes[1]]*scale)
    if i==0:path.moveTo(*q)
    else:path.lineTo(*q)
   c.setLineWidth(.35);c.drawPath(path)
def dimension(x,y,length,scale=2,vertical=False):
 xx=x if vertical else x+length*scale;yy=y+length*scale if vertical else y;c.line(x,y,xx,yy)
 for a,bn in [(x,y),(xx,yy)]:
  if vertical:c.line(a-4,bn,a+4,bn)
  else:c.line(a,bn-4,a,bn+4)
 text((x+xx)/2+4,(y+yy)/2+4,f'{length:.2f}',9)
def notes(lines,x=700,y=680):
 for s in lines:text(x,y,s);y-=22
page('V02 조립도 — 슬림 레일 / 원형 팝업 그립 인터페이스',1)
view(list(parts.values()),190,440,(0,1),2,'FRONT / XY');view(list(parts.values()),510,440,(2,1),2,'SIDE / ZY')
dimension(96,270,2*ox);dimension(82,290,2*oy,vertical=True)
notes(['Case 86 x 142 x 11: SELLER, NOT MEASURED',f'Frame outer {2*ox:.1f} x {2*oy:.1f} x {top:.1f}',f'Folded thickness {result["folded_accessory_thickness_mm"]:.1f} ASSUMED',f'Extended thickness {result["open_accessory_thickness_mm"]:.1f} ASSUMED','Grip D38; end separation 6 / 22 ASSUMED','Phone base D60 x2; magnet D56 x2 ASSUMED','63 x 88 in reference is CARD, not slab/case','No printed bellows: BUY validated grip module','Frame holds BOTH halves of magnetic case','No adhesive or holes on existing case/slab'])
# True X=0 section, exposed reference envelope included.
ss=state(22);section=[]
for q in ss.values():
 sh=q.common(box(-.01,-100,-70,.02,200,120))
 if not sh.isNull():section.append(sh)
view(section,950,260,(2,1),1.1,'SECTION X=0 (extended)');c.showPage()
info={
'01_open_cradle':[f'Outer {2*ox} x {2*oy}; rear rim R5; back t3','Rear cutout 84 x140 R3; bridge60 x60 R8','Connecting bar X +/-47, Y +/-12, Z0..3','Cavity88 x144; case Z3.4..14.4','Side walls X[-47,-44],[44,47], Y-72..69','Lips X[-44,-41.5],[41.5,44], Z14.8..16.4','Bottom wall Y-77..-72, Z3..16.4','4x D3.4 through: (+/-25,0),(0,+/-25)','Case-side counterbore D6.2 depth1.8','2x gate holes D3.4 X +/-40, Y74.5','Tether slot6 x2: X +/-3,Y-76.5..-74.5'],
'02_top_gate':['Width94; flange Y72..77, Z3..5','Wall Y72..77, Z5..16.4','Lip Y69.5..77, Z14.8..16.4','2x D3.4 through X +/-40 Y74.5','2x M3x12 + washers + nyloc, stack TBD','Remove gate before sliding case out +Y'],
'03_grip_mount_plate':['Disc D60 x2, Z-2..0','4x D3.4 through at R25 cardinal points','Grip envelope D38 leaves bolts at R25','M3 nuts below plate; ensure grip clearance','Attachment to purchased grip NOT SPECIFIED','Do not treat D38 as vendor exact interface'],
'04_phone_base_adapter':['Disc D60 x2; folded Z-10..-8','4x D3.4 through at R25 cardinal points','Grip/magnet attachment NOT SPECIFIED','Purchase module mechanical data REQUIRED','Holes do NOT authorize drilling magnet module']}
for i,(k,s) in enumerate(parts.items(),2):
 page(k+' — 부품 치수',i);view([s],205,450,(0,1),2,'XY datum');view([s],510,450,(2,1),2,'ZY side')
 bb=s.BoundBox;dimension(205+bb.XMin*2,450+bb.YMin*2-15,bb.XLength);dimension(205+bb.XMin*2-15,450+bb.YMin*2,bb.YLength,vertical=True)
 notes(info[k]+['PETG prototype, 1 pc','FDM target +/-0.3mm; NOT verified','Bores finish-to-gauge, no press fit','Edge finishing R0.5 minimum','See print/assembly notes before printing'])
 c.showPage()
page('미확정 인터페이스 / 출력·조립 메모',6)
notes(['본 도면은 참고 이미지의 외관 방향을 반영한 예비 설계이며, 참고 이미지의 성능을 검증한 것이 아니다.','기존 알루미늄 보호케이스 유지. 투명 슬랩 직접 장착 설계가 아님. 실제 모서리/분리면 형상 확인 필요.','후면은 전체 판 대신 주변 프레임+중앙 브리지를 사용. 앞쪽 레일이 케이스 앞뒤 두 반쪽을 함께 포획.','상단 게이트와 마운트판은 나사 체결. 케이스 자체 자석은 휴대폰 하중 지지용이 아니다.','원형 팝업 그립과 스마트폰 자석 모듈은 구매품의 단순 외형 참고 모델이며 STL 출력 대상에서 제외.','상용 팝업 그립 두께6/22mm와 지름38mm, 자석56x2mm는 ASSUMED. 실제 구매품으로 재생성 필요.','상용 그립 접착형 단부를 쓰는 경우 새 플레이트에만 공급사 승인 방식으로 부착/시험. 케이스에는 접착 금지.','현재 구매품 체결 미확정으로 실제 폰을 안전하게 잡을 수 있는 완성품이 아님.','PETG / 0.4 노즐 / 0.2 레이어 / 외벽6 이상 / 첫 하중 검토 인필100%를 시작 조건으로 제안.','출력 STL은 바닥 Z=0. 크래들 측면 세움, 게이트 눕힘, 원판2개 평면 배치. 업체 서포트 검토 필수.','Ø3.4 구멍은 M3 통과 확인. 프레임 카운터보어Ø6.2 깊이1.8에 맞는 M3 버튼헤드 선정.','마운트 M3 볼트4개는 프레임 내부에서 삽입하고 너트는 마운트판 아래. 기존 케이스 장착 전에 체결.','후면 패드 자유0.6/압축0.4mm 가정. XY 한쪽1mm 간극: 패드/심으로 맞춤, 압입 금지.','상부 자유간극0.4mm와 패드 두께를 실제로 보정. 기존 케이스 모서리를 샌딩하지 말 것.','실제 UV 차단율 미확인. 별도 UV 커버 미포함. 하중/크리프/낙하/마찰/거치 성능 미검증.','참고 폰과 카메라는 ASSUMED. 검사한 범위 밖 체결품 머리·너트·접착층·손가락은 모델 미포함.'],x=50,y=710)
c.showPage();c.save()
# Human reports, explicit differences from V01.
F=com['6']['mass_g']/1000*9.81*10
(R/'README_ko.md').write_text(f'''# PSA 그립 V02 — 참고 이미지 반영 디자인

**예비 시제품용 — 실측 및 시험 전 제작 확정 금지.**

V01은 그대로 보존. V02는 아이보리 톤, 가는 측면 캡처 레일, 둥근 외곽, 후면 개방형 프레임과 중앙 원형 상용 팝업 그립 인터페이스로 변경했다. 기존 알루미늄 케이스86×142×11mm를 유지한다. 투명 PSA 슬랩으로 바꾼 것이 아니며 렌더링의 회색 부분은 기존 케이스 외형이다. 참고 이미지의63×88mm는 일반 카드 크기로 쓰지 않았다.

- `assembly.FCStd`, `assembly.step`: 실제 생성. FreeCAD는 Part::Feature와 파라미터 표; 스케치 이력 모델 아님.
- `parts/`: 제작품4종 STEP·STL. `STL_PRINT/`: 제안 출력 방향, 양의 좌표, Z=0으로 정리한 STL4개.
- `drawings/PSA_grip_V02_A3.pdf`: A3 6장, 조립·단면·부품별 치수·공차·소재·미확정 접속.
- `renders/`: 실제 CAD의 전/후면, 접힘/펼침, 분해 이미지. 참고 이미지 자체를 리터칭한 것이 아님.
- `parameters.csv`, `BOM.csv`, `validation_results.json`, `validation_report_ko.md`, `assembly_guide_ko.md`.

## 확인한 값과 미확인 값

86×142×11mm와 알루미늄 합금은 판매자 표기이며 실측 아님. 그 외 전부 설계 가정. 구매 팝업 그립D38, 접힘6/펼침22mm 및 자석D56×2mm는 선택된 제품의 규격이 아니다. 구매품 선택 후 부착면과 체결 형상을 다시 맞춰야 한다. 참고 스마트폰/카메라도 실측 미검증.

프레임 외형{2*ox}×{2*oy}×{top:.1f}mm. 가정 구매품 포함 휴대폰 뒤~앞 립까지 접힘{result['folded_accessory_thickness_mm']:.1f}mm, 펼침{result['open_accessory_thickness_mm']:.1f}mm. 참고 이미지24/40mm를 달성했다고 주장하지 않는다. PETG 솔리드 등가 출력품 합계{sum(mass.values()):.1f}g. 휴대폰 포함 추정{com['6']['mass_g']:.1f}g, 실측 필요.

## 중요한 구분

**원형 주름 팝업 메커니즘은 구매품 외형 모델일 뿐이며 자체 제작 설계가 아니다.** 부품별 STL에 주름/자석/케이스/폰이 포함되지 않는다. 폰 베이스와 그립의 부착 경로가 미확정이므로 출력만으로 작동 완제품이 되지 않는다. V01의 핀 힌지를 예쁘게 둥글린 구조가 아니라, 상용 팝업 기구를 사용하는 별도 구조이다. 새 부착부에만 승인 접착/기계 체결 사용 가능. 기존 케이스와 슬랩에는 구멍·접착 금지.

## 실행

```bash
cd /workspace/pokemon/deliverables/psa_grip_v02
/usr/bin/python3 generate_model.py
```

Linux 시스템 Python, FreeCAD1.0(`/usr/lib/freecad/lib`), ReportLab, Blender CPU Cycles, Poppler 필요. `design_parameters.json`과 스크립트로 재생성. 표를 직접 바꿔도 FCStd의 형상이 자동 갱신되지는 않는다. 일부 립/볼트 좌표·필렛·구매품 외형은 스크립트 상수이므로 큰 치수 변경 시 도면도 재검토해야 한다.
''')
(R/'assembly_guide_ko.md').write_text('''# V02 출력·조립 안내

예비 시제품용 — 실측 및 시험 전 제작 확정 금지.

1. 기존 자석식 케이스의 분리면, 돌출부, 최대 외형, 질량과 모서리를 실측. 케이스 앞판을 제거한 채 하중을 걸지 않는다. 먼저 동등 외형 더미로 맞춘다.
2. `STL_PRINT` 4종을 각1개 출력. mm/100%. 크래들은 측면 세움, 게이트는 긴 방향 눕힘, 원판은 평면. 서포트·브림·빈층·불안정 단면은 업체/슬라이서에서 확인. 출력 방향의 강도 최적화와 실제 슬라이싱은 미실행.
3. PETG, 0.4노즐, 0.2레이어, 외벽6+, 첫 하중 확인은 인필100% 시작점. 생산 강도 기준 아님. 포크가 없는 구조지만 얇은 프레임의 휨/층간 박리 검토 필요.
4. 구멍 Ø3.4 통과 검사, 디버링 R0.5 이상. 원본 STEP은 조립 좌표이고 출력 STL은 방향·원점만 바뀐다.
5. 케이스 장착 전 크래들과 Ø60 마운트판을 M3 버튼헤드4개로 조립. 프레임의 케이스 쪽 카운터보어 Ø6.2×깊이1.8에 머리가 완전히 들어가는지 확인. M3x10은 가정 길이; 머리 높이<=1.8 및 와셔/너트 포함 스택 확인. 판 아래 너트와 Ø38 팝업 그립의 공간을 실측한다.
6. 새 프레임의 케이스 접촉부에 자유두께0.6/압축0.4mm 목표 연질 라이너를 탈착 가능하게 고정. 양쪽 XY 한쪽 간극1mm는 라이너+심으로 보정. 기존 케이스/슬랩에는 접착하지 않는다. 라이너는 CAD에서 미모델링.
7. 상단 게이트 제거 후 닫힌 기존 케이스를 +Y에서 삽입. 양쪽 전면 립이 앞판을, 후면 림과 브리지가 뒤판을 잡는지 확인. 자석 두 반쪽 분리 시험은 더미로 먼저 실시.
8. 상단 게이트를 M3x12 2개와 와셔/잠금너트로 체결. 실제 스택에 맞게 길이 보정. 접촉 나사머리가 기존 케이스에 닿으면 사용 중단.
9. 상용 팝업 그립과 폰 자석 모듈을 선정하고 기구도/접착 허용 조건/고정력 자료 확보. 각 단부를 새 플레이트에 공급사 승인 방법으로 접속. 현재의 R25 구멍4개가 구매품에 맞는다고 가정하지 말 것. 필요한 체결 리브/어댑터/접착층은 구매품 선정 후 재설계.
10. 구매품 연결을 확정하기 전에는 케이스 프레임 맞춤 시제품으로만 사용. 이후 독립 폰 테더와 더미로 인장/전단/비틀림/박리/반복/온도/낙하 시험. 원형 그립이 거치 토크를 견딘다는 보장 없음.

투명 슬랩 직접 수납은 이 버전의 범위 밖이다. 참고 이미지의 흰 레일 형태는 반영했으나 기존 케이스는 불투명 알루미늄이므로 사진처럼 전체가 투명해지는 것은 아니다. 기존 커버 UV 성능은 미확인. TPU/실리콘은 라이너용, PETG는 맞춤/작동 시제품용. 실제 하중용은 구매 기구·재료·공정 검증 후 확정한다.
''')
(R/'validation_report_ko.md').write_text(f'''# V02 검증 보고서

예비 시제품용 — 실측 및 시험 전 제작 확정 금지.

## 실행한 검사

제작품4개 FreeCAD 솔리드 유효, 각1개 닫힌 솔리드. STEP 재가져오기 체적 일치, 출력용 STL 닫힘 확인. 상용 팝업 그립의 외형 길이6~22mm, 1mm 간격17개 상태에서 제작품·기존 케이스·팝업 외형·자석 외형·가정 폰/카메라 간 양의 교차 체적 {len(collisions)}건. 개별 수치 `validation_results.json`. 주름 내부의 실제 접힘 궤적을 검사한 것이 아니며 외형 모델의 직선 이동 검사일 뿐이다. 실제 체결 볼트/너트/패드/접착층/유연변형·손가락은 제외. 접촉면은 허용했고 교차 체적만 집계했다.

출력물 솔리드 등가 질량 {sum(mass.values()):.2f}g (PETG1.27 가정). 기존 케이스+슬랩120g, 팝업15g, 자석18g, 철물/패드10g, 폰+케이스224g 가정. 총 {com['6']['mass_g']:.2f}g. 액세서리 {com['6']['mass_g']-224:.2f}g. 실제 중량 미측정.

COM: {json.dumps(com,ensure_ascii=False)}. 질량 위치 단순화. 케이스 payload80~180g, 그립10~25g, 자석10~30g, 철물/패드5~20g를 민감도 검토 범위로 제안하며 아직 이 전체 범위의 형상/토크 시험은 미실행이다.

## V01과의 차이

전면 레일/개방 뒷면으로 재료를 줄이고 핀 힌지 대신 원형 상용 팝업 기구로 변경. 구매품 두께 가정에서 접힘 {result['folded_accessory_thickness_mm']:.1f}mm, 펼침 {result['open_accessory_thickness_mm']:.1f}mm. 기존 V01의 19각도 검사나 힌지 강도 계산을 V02에 전용하지 않는다. V02 구매품은 미선정이고 체결 미확정이므로 검증 수준은 외형/맞춤 단계다.

## 하중 경로와 미검증 강도

보호케이스 앞뒤 두 반쪽 → 전면 립/후면 림·중앙 브리지 → M3 4개 → 원형 플레이트 → 구매 팝업 → 폰 베이스 → 구매 자석 → 폰 케이스.

총질량에 동적5×여유2를 곱한 잠정 증명 하중 {F:.1f}N, 편심60mm의 잠정 토크 {F*.06:.2f}Nm. 이 5g는 낙하충격 상한이 아니다. R25의 4볼트가 순수 인장 하중을 균등 지지한다고 단순화하면 볼트당{F/4:.2f}N. 모멘트{F*.06:.2f}Nm를 y=±25mm의 두 볼트만으로 받는 보수적 단순 커플 힘은 {F*.06/.05:.1f}N. 볼트 응력만으로 얇은 프레임 안전을 판단할 수 없다. 상단 게이트 볼트 구멍 외측 잔여폭{gate_ligament:.1f}mm의 찢김, 카운터보어 잔여판1.2mm의 머리 관통, 브리지 휨, 립 벌어짐, 2mm 플레이트 굽힘, 크리프, 접착 박리, 팝업 좌굴/전단은 미해석/미시험.

자석은 수직 인장력만으로 합격 불가. 전단/비틀림/박리 데이터를 확보하고 실제 폰 케이스 조합을 시험해야 한다. 상용 팝업 제조사가 허용하는 질량/편심/하중이 부족하면 고정된 폰 케이스 접속 구조나 기계 잠금 구조로 변경해야 한다. 공식 MagSafe 인증을 주장하지 않는다.

## 위험과 개선

- 자석식 기존 케이스 분리: 립과 뒷림으로 양면 포획. 케이스 실제 분리면/테두리 실측 전 미확정. 자석만으로 카드/폰 하중을 지지하지 않는다.
- 프레임 이탈/흠집: 나사 게이트2개, 연질 라이너, 쿠폰 맞춤. 립 접촉면/패드 두께와 슬라이드 마찰 시험. 볼트머리 돌출 금지.
- 구매 원형 그립 파손/이탈: 모듈 선정과 승인 연결 방식 미정. 출력 주름을 임의 만들어 쓰지 않는다. 실제 구매품 내구성 확보 전 실제 폰 사용 금지.
- 자석 접속 박리/회전: R25 홀은 임시, 구매품 매칭과 회전방지/독립 폰 테더 필요.
- 카메라: 38×38×4, 중심(-15,52) 가정. 실제 케이스와 카메라 형상으로 재검증. 참고 이미지처럼 케이스를 축소하지 않는다.
- 손가락/끼임: 펼침 외형은 공간만 표시. 그립 접힘 틈과 엄지 압박은 구매품/인체 시험 필요. 이번 CAD에는 힌지 가드 없음.
- UV: 기존 커버 데이터 없음, 별도 UV 커버 없음. UV-grade 재료/투과율 시험 없이는 차단율 주장 불가.
- 출력: 측면 세움 프레임의 큰 높이와 얇은 레일은 서포트·브림·뒤틀림/층간 박리 위험. 실제 슬라이싱 미실행. 공차 목표±0.3mm는 공정 검증값 아님.
- 거치: 구매 팝업 토크와 접지 상태가 미정이므로 거치 기능 미검증. 이번 V02에서 스탠드 이미지를 기능 입증처럼 제공하지 않는다.
- 두께/무게: V01보다 얇고 가벼운 외형 가정이나 구매품 확정 전 실제 개선 수치를 보장하지 않는다.

## 다음 실물 시험 (모두 미실행)

기존 케이스 더미 삽입50회, 자석 앞뒤 벌어짐 당김. {F:.1f}N 60초 인장/전단 양방향 및 {F*.06:.2f}Nm 비틀림/박리 예비 요구, 이탈/균열 없음과 잔류변형0.5mm이하를 잠정 기준으로 한다. 구매품 허용 조건과 비교 후 적정 기준으로 수정. 구매 팝업1000회 초기/10000회 목표, 45°C24h 정적 하중, 독립 테더·차폐 더미 0.5m부터 낙하 시험. 1m6방향 각3회는 후속 목표일 뿐 인증 기준 아님. 실물 하중 결과 없이 실사용 승인하지 않는다.
''')
subprocess.run(['/usr/bin/blender','-b','-t','4','--python',str(R/'render_blender.py')],check=True,stdout=subprocess.DEVNULL)
# Check PDF text and all expected pages actually exported.
textpdf=subprocess.check_output(['pdftotext',str(R/'drawings'/'PSA_grip_V02_A3.pdf'),'-'],text=True)
assert textpdf.count('예비 시제품용')==6
pdfinfo=subprocess.check_output(['pdfinfo',str(R/'drawings'/'PSA_grip_V02_A3.pdf')],text=True);assert 'Pages:           6' in pdfinfo and '(A3)' in pdfinfo
# Keep generated backups out of release.
for q in R.glob('*.FCBak'):q.unlink()
files=sorted(q for q in R.rglob('*') if q.is_file() and q.name!='SHA256SUMS.txt')
(R/'SHA256SUMS.txt').write_text('\n'.join(hashlib.sha256(q.read_bytes()).hexdigest()+'  '+str(q.relative_to(R)) for q in files)+'\n')
with zipfile.ZipFile(R.parent/'psa_grip_v02.zip','w',zipfile.ZIP_DEFLATED) as z:
 for q in sorted(R.rglob('*')):
  if q.is_file():z.write(q,q.relative_to(R.parent))
with zipfile.ZipFile(R.parent/'psa_grip_v02.zip') as z:assert z.testzip() is None
print(json.dumps(result,indent=2));print('V02 complete: actual files generated; purchased interfaces still unqualified.')

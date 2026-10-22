#!/usr/bin/python3
"""Circular purchased pop-up revision. Requires FreeCAD1.0, ReportLab, Blender.
The pop-up is an UNSELECTED purchased-part envelope, not a printable bellows.
"""
import sys,json,csv,math,itertools,subprocess
from pathlib import Path
sys.path.append('/usr/lib/freecad/lib')
import FreeCAD as A,Part,Mesh
from FreeCAD import Vector as V
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A3,landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
R=Path(__file__).resolve().parent
D={'integral_mount_d':44.,'integral_mount_t':2.5,'popup_upper_cap_d':40.,'popup_lower_cap_d':38.,'popup_closed_h':6.,'popup_open_h':22.,'popup_attachment_film_t':.2,'phone_base_d':48.,'phone_base_t':2.5,'phone_adhesive_t':1.,'phone_w':71.5,'phone_h':149.6,'phone_t_with_case':9.75}
pf=R/'parameters.json';p=json.loads(pf.read_text()) if pf.exists() else D;pf.write_text(json.dumps(p,indent=2))
def cyl(rad,z,th):return Part.makeCylinder(rad,th,V(0,0,z))
def fuse(items):
 s=items[0]
 for q in items[1:]:s=s.fuse(q)
 return s.removeSplitter()
def rounded(w,h,z,t,r):
 s=Part.makeBox(w,h,t,V(-w/2,-h/2,z));return s.makeFillet(r,[e for e in s.Edges if e.BoundBox.ZLength>t-.001 and e.BoundBox.XLength<.001 and e.BoundBox.YLength<.001])
summary={}
for variant in ['direct_slab','aluminum_case']:
 root=R if variant=='direct_slab' else R/'variants'/'aluminum_case'
 for d in ['CAD','STL_PRINT','STEP_parts','drawings','renders']: (root/d).mkdir(parents=True,exist_ok=True)
 src=R/'source_geometry'/variant;old=json.loads((src/'validation_results.json').read_text());w,h,t=old['payload_mm'];oldframe=Part.read(str(src/'01_Main_Frame.step'));gate=Part.read(str(src/'02_Locking_Gate.step'))
 # Remove obsolete four-bar screw bores; all core arms, forks, pins are absent.
 fills=[]
 for x,y in itertools.product([-17,17],[-42,42]):
  fills += [Part.makeCylinder(1.7,3,V(x,y,0)),Part.makeCylinder(3.1,1.8,V(x,y,1.2))]
 frame=fuse([oldframe]+fills+[cyl(p['integral_mount_d']/2,-p['integral_mount_t'],p['integral_mount_t'])])
 zu=-p['integral_mount_t']-p['popup_attachment_film_t']
 basez=zu-p['popup_closed_h']-p['popup_attachment_film_t']-p['phone_base_t']
 base=cyl(p['phone_base_d']/2,basez,p['phone_base_t'])
 parts={'01_Frame_With_Integral_Round_Pad':frame,'02_Magnetic_Gate':gate,'03_Adhesive_Phone_Base':base}
 def pose(ext,phone=True,graphics=False):
  zl=zu-ext;bz=zl-p['popup_attachment_film_t']-p['phone_base_t'];b=base.copy();b.translate(V(0,0,p['popup_closed_h']-ext))
  middle=(ext-3)/2
  popup=fuse([cyl(p['popup_upper_cap_d']/2,zu-1.5,1.5),cyl(p['popup_lower_cap_d']/2,zl,1.5),Part.makeCone(16,8,middle,V(0,0,zl+1.5)),Part.makeCone(8,16,middle,V(0,0,zl+1.5+middle))])
  ss={'01_Frame_With_Integral_Round_Pad':frame,'02_Magnetic_Gate':gate,'03_Adhesive_Phone_Base':b,'REF_OEM_Popup_NOT_PRINTABLE':popup,'REF_Upper_Attachment_Film':cyl(19,zu,p['popup_attachment_film_t']),'REF_Lower_Attachment_Film':cyl(18,zl-p['popup_attachment_film_t'],p['popup_attachment_film_t']),'REF_Phone_Adhesive':cyl(p['phone_base_d']/2-1,bz-p['phone_adhesive_t'],p['phone_adhesive_t']),'REF_Payload':rounded(w,h,3.5,t,3 if variant=='direct_slab' else 2)}
  if phone:
   pb=bz-p['phone_adhesive_t'];ss['REF_Phone']=rounded(p['phone_w'],p['phone_h'],pb-p['phone_t_with_case'],p['phone_t_with_case'],8);ss['REF_Camera']=Part.makeBox(38,38,4,V(-34,33,pb))
  if graphics and variant=='direct_slab':
   z=3.5+t/2;ss['ART_Card']=Part.makeBox(63,88,.12,V(-31.5,-53,z));ss['ART_Label']=Part.makeBox(70,19,.12,V(-35,h/2-26,z))
  return ss
 doc=A.newDocument('Circular_Popup_'+variant)
 sheet=doc.addObject('Spreadsheet::Sheet','Assumed_Purchased_Part_Parameters')
 for i,(k,val) in enumerate(p.items(),1):sheet.set('A'+str(i),k);sheet.set('B'+str(i),str(val));sheet.set('C'+str(i),'ASSUMED / vendor unselected')
 for k,s in pose(p['popup_closed_h']).items():
  ob=doc.addObject('Part::Feature','Part_'+k);ob.Label=k;ob.Shape=s;ob.addProperty('App::PropertyString','ManufacturingStatus').ManufacturingStatus='PRINTED PART' if k in parts else 'REFERENCE ONLY / NOT PRINTABLE'
 doc.recompute();doc.saveAs(str(root/'CAD'/'PSA_Grip_Circular.FCStd'))
 Part.Compound(list(parts.values())).exportStep(str(root/'CAD'/'PrintParts_Assembly.step'))
 Part.Compound([s for k,s in pose(p['popup_open_h'],False).items() if k!='REF_Payload']).exportStep(str(root/'CAD'/'Assembly_REFERENCE_With_OEM_Envelope.step'))
 checks={}
 for name,s in parts.items():
  assert s.isValid() and len(s.Solids)==1
  s.exportStep(str(root/'STEP_parts'/f'{name}.step'));q=s.copy()
  if name.startswith('01'):q.rotate(V(0,0,0),V(0,1,0),90)
  if name.startswith('02'):q.rotate(V(0,0,0),V(1,0,0),-90)
  B=q.BoundBox;q.translate(V(-B.XMin,-B.YMin,-B.ZMin));Mesh.Mesh(q.tessellate(.12)).write(str(root/'STL_PRINT'/f'{name}.stl'))
  mesh=Mesh.Mesh(str(root/'STL_PRINT'/f'{name}.stl'));back=Part.read(str(root/'STEP_parts'/f'{name}.step'));assert mesh.isSolid() and back.isValid()
  checks[name]={'valid_solid':True,'stl_closed':True,'volume_mm3':s.Volume,'step_volume_error_mm3':abs(back.Volume-s.Volume),'stl_relative_volume_error':abs(abs(mesh.Volume)-s.Volume)/s.Volume}
 intersections=[]
 for i in range(17):
  height=p['popup_closed_h']+(p['popup_open_h']-p['popup_closed_h'])*i/16;ss=pose(height)
  for a,b in itertools.combinations(ss,2):
   vol=ss[a].common(ss[b]).Volume
   if vol>1e-5:intersections.append({'extension_mm':height,'a':a,'b':b,'intersection_mm3':vol})
 insertion=[]
 payload=pose(p['popup_closed_h'])['REF_Payload']
 for i in range(16):
  q=payload.copy();q.translate(V(0,i*(h+10)/15,0));vol=q.common(frame).Volume
  if vol>1e-5:insertion.append({'sample':i,'intersection_mm3':vol})
 fold=gate.BoundBox.ZMax-(basez-p['phone_adhesive_t']);expanded=fold+p['popup_open_h']-p['popup_closed_h']
 validation={'variant':variant,'purchased_popup_selected':False,'mechanism_is_reference_envelope_only':True,'parts':checks,'sampled_envelope_interferences':intersections,'payload_insertion_interferences':insertion,'folded_thickness_assumed_mm':fold,'expanded_thickness_assumed_mm':expanded,'physical_tests_run':False,'OEM_internal_mechanism_validated':False,'stock_mechanism_stl_exported':False,'adhesive_strength_verified':False}
 (root/'validation_results.json').write_text(json.dumps(validation,indent=2));summary[variant]=validation
 def render(name,extension,color,phone=True):
  out={}
  for k,s in pose(extension,phone,True).items():
   col=(.025,.03,.035)
   if color=='silver' and (k=='02_Magnetic_Gate' or k=='REF_OEM_Popup_NOT_PRINTABLE'):col=(.46,.49,.52)
   if k=='REF_Payload':col=(.65,.7,.75)
   if k=='REF_Phone':col=(.12,.13,.15)
   if k=='ART_Card':col=(.08,.24,.42)
   if k=='ART_Label':col=(.92,.92,.88)
   vv,ff=s.tessellate(.2);out[k]={'vertices':[[v.x,v.y,v.z] for v in vv],'faces':[list(f) for f in ff],'color':col,'transparent':k=='REF_Payload' and variant=='direct_slab'}
  (root/'renders'/f'{name}.mesh.json').write_text(json.dumps(out))
 render('black_folded',p['popup_closed_h'],'black');render('silver_open',p['popup_open_h'],'silver');render('silver_rear_open',p['popup_open_h'],'silver',False)
 # Actual projected geometry on A3, printed parts and reference envelope clearly separated.
 pdfmetrics.registerFont(UnicodeCIDFont('HYSMyeongJo-Medium'));W,H=landscape(A3);c=canvas.Canvas(str(root/'drawings'/'Circular_Popup_Revision_A3.pdf'),pagesize=(W,H))
 def text(x,y,t,n=10):c.setFont('HYSMyeongJo-Medium',n);c.drawString(x,y,t)
 def header(t,n):c.rect(24,24,W-48,H-48);text(36,H-46,t,17);text(36,H-68,'예비 수정안 / 구매 팝업 규격 미선정 / 실측 및 시험 전 제작 확정 금지',11);text(36,36,f'Circular popup revision | {variant} | mm | A3 | Page {n}')
 def projection(seq,x,y,axes,scale):
  for sh in seq:
   for e in sh.Edges:
    pts=e.discretize(Deflection=.2)
    if len(pts)<2:continue
    path=c.beginPath()
    for j,pt in enumerate(pts):
     a=[pt.x,pt.y,pt.z];xx=x+a[axes[0]]*scale;yy=y+a[axes[1]]*scale
     if j==0:path.moveTo(xx,yy)
     else:path.lineTo(xx,yy)
    c.setLineWidth(.35);c.drawPath(path)
 header('중앙 원형 팝업 수정안 / 전체 조립',1);projection(list(parts.values()),180,430,(0,1),1.8);projection(list(pose(p['popup_open_h']+0.,False).values()),500,430,(2,1),1.8)
 notes=[f'Integral frame mounting pad D44 x2.5',f'Phone adhesive base D48 x2.5',f'Purchased popup: upper D40 / lower D38 ASSUMED',f'Cap separation closed6 / open22 ASSUMED',f'Upper/lower mounting film0.2 each ASSUMED',f'Phone-case adhesive1.0 ASSUMED',f'Folded {fold:.1f} / open {expanded:.1f} mm incl. gate','Old link arms, hinge pins, index pins REMOVED','Magnetic gate and mechanical shoulders retained','Popup is a purchased-part ENVELOPE, not a printed spring']
 for i,tline in enumerate(notes):text(740,700-i*25,tline)
 c.showPage()
 for n,(name,sh) in enumerate(parts.items(),2):
  header(name,n);projection([sh],210,440,(0,1),1.8);projection([sh],550,440,(2,1),1.8)
  B=sh.BoundBox;notes=[f'Envelope X{B.XLength:.2f} Y{B.YLength:.2f} Z{B.ZLength:.2f} mm','PETG prototype, qty1','General FDM target +/-0.3mm, not verified','Original magnetic frame source preserved separately','Part01 integral rear pad D44, Z-2.5..0','Obsolete four M3 mount holes filled; NO link bracket','No printed OEM bellows STL in this release','Vendor-approved attachment to new printed surfaces only','No glue on the original slab or aluminum holder','All artwork/payload/phone excluded from print files']
  for i,tline in enumerate(notes):text(750,695-i*25,tline)
  c.showPage()
 c.save()
 with (root/'BOM.csv').open('w') as f:
  wr=csv.writer(f,lineterminator='\n');wr.writerow(['part','qty','status'])
  for k in parts:wr.writerow([k,1,'PETG PRINT'])
  for row in [('Commercial circular popup',1,'UNSELECTED, end-cap D40/D38 height6/22 assumed; NOT PRINTED'),('OEM-approved top attachment',1,'D38x0.2 assumed, vendor qualification REQUIRED'),('OEM-approved lower attachment',1,'D36x0.2 assumed, vendor qualification REQUIRED'),('Phone-case compatible adhesive',1,'D46x1 assumed; cure/prep/peel test REQUIRED'),('Gate magnets D5x2',4,'UNQUALIFIED vendor/force; preserve magnetic gate'),('Soft liners',1,'Existing magnetic frame pad design reused, fit test REQUIRED')]:wr.writerow(row)
 (root/'README_ko.md').write_text(f'''# 중앙 원형 팝업 수정안 — {variant}

예비 수정안 / 구매 부품 미선정 / 실측 및 시험 전 제작 확정 금지.

노출된 두 링크·긴 연결판·회전축/각도핀을 모두 제거했다. 프레임 뒷면 중앙에 D44x2.5 원형 평면을 일체로 만들고, 상용 원형 팝업을 가운데 넣어 D48 접착식 폰 베이스로 연결한다. 카드 앞면은 바깥쪽이다. 상단 자석 게이트와 기존 프레임 수납 치수는 유지한다.

기본 A는 슬랩81x136x6mm 전부 가정. B는 `variants/aluminum_case/`에 있으며86x142x11mm 판매자 참고/미실측. 색상은 블랙,블랙x실버. 이번 설계는 실제 주름 기구를 자체 설계한 것이 아니라 **구매 팝업의 가정 외형**을 포함한다. 내부 잠금/반복/좌굴/인체공학은 미검증이며 구매품의 실규격과 사용 가능 하중으로 다시 맞춰야 한다.

`STL_PRINT/`의 프레임/자석게이트/폰베이스 각1개만 출력한다. 주름형 팝업은 출력 파일에 없고 별도 구매다. 뒷면 원형 연결판은 프레임과 일체라 별도 나사 조립이 없다. OEM 양끝과 새 프린트부의 접속은 공급사 승인 접착/필름을 전제로 한 형상이다. 기존 카드/슬랩/알루미늄 케이스에는 접착하지 않는다. 폰 연결은 폰 케이스 접착식이다.

`CAD/PSA_Grip_Circular.FCStd`: 부품별 형상 및 참고 모델. `CAD/PrintParts_Assembly.step`: 출력품3개. `CAD/Assembly_REFERENCE_With_OEM_Envelope.step`: OEM와접착외형을 포함한 참고 조립으로 가공 데이터가 아님. `STEP_parts/`는출력품별STEP. `drawings/Circular_Popup_Revision_A3.pdf`는4장 예비도면이며, 기존 프레임/자석게이트 상세는 원본 V02 도면과 함께 본다.

가정 두께 접힘{fold:.1f}/펼침{expanded:.1f}mm(게이트 돌출 포함). OEM6/22mm와 접착층0.2/0.2/1mm를 확인한 값이 아니다. 출력 단품 유효 솔리드/STEP/STL 검사 실행. 외형 접힘17상태 겹침{len(intersections)}건,수납물삽입16상태겹침{len(insertion)}건. 이 검사는 실제 팝업 내부운동/주름재료변형/자력/접착력/낙하/실물출력검증이 아니다.

상용 팝업에 큰 카드케이스 편심하중이 걸린다. OEM의 허용 인장/전단/박리/토크 자료와실제폰케이스/카드중량으로시험하기전 실사용승인하지 않는다. 단순 OEM 직경 일치가 호환성을 보장하지 않는다. 각 접착층과 자석 게이트를 별도로 시험하고 독립 폰테더/더미로 검증해야 한다. 기존 링크형의 강도 계산은 이번 접속으로 전용하지 않는다.

재생성: 이 폴더에서 `/usr/bin/python3 generate_circular_popup.py`. FreeCAD1.0/ReportLab/Blender 필요. 원본 프레임/게이트STEP을 `source_geometry/`에 복사보존했다. 해당 프레임 치수를 바꾸려면 상위V02원본생성기로 새수납치수를 먼저 만들고 이입력STEP을교체해야한다. 원형팝업가정은parameters.json에서변경. 기본 실행은두안의CAD와CAD렌더6개를재생성한다.
''')
 A.closeDocument(doc.Name)
(R/'validation_summary.json').write_text(json.dumps(summary,indent=2))
if '--skip-render' not in sys.argv:subprocess.run(['/usr/bin/blender','-b','-t','4','--python',str(R/'render_blender.py')],check=True,stdout=subprocess.DEVNULL)
print(json.dumps({k:{'fold':v['folded_thickness_assumed_mm'],'open':v['expanded_thickness_assumed_mm'],'interferences':len(v['sampled_envelope_interferences'])} for k,v in summary.items()},indent=2))

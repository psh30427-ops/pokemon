"""Build engineering drawings and explicit verification reports from model outputs."""
import sys,math,json,csv
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A3,A4,landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
import Part
from FreeCAD import Vector as V
r=root;g=geometry;v=result;is_slab=v['variant']=='direct_slab';title='A안: PSA 슬랩 직접 수납' if is_slab else 'B안: 알루미늄 보호케이스 수납'
pdfmetrics.registerFont(UnicodeCIDFont('HYSMyeongJo-Medium'));W,H=landscape(A3);c=canvas.Canvas(str(r/'drawings'/'PSA_Grip_V02_Manufacturing_A3.pdf'),pagesize=(W,H));c.setTitle('PSA Grip V02 '+v['variant']+' preliminary manufacturing drawings')
def text(x,y,s,size=10):c.setFont('HYSMyeongJo-Medium',size);c.drawString(x,y,str(s).replace('·',' / '))
def page(name,n):
 c.rect(24,24,W-48,H-48);text(36,H-44,name,17);text(36,H-67,title+' | 예비 시제품용 — 실측 및 시험 전 제작 확정 금지',11);text(36,36,f'PSA GRIP V02 | {n} | mm | A3 | Projection edges include hidden geometry | Do not scale PDF',9)
def notes(lines,x=715,y=705):
 for s in lines:text(x,y,s);y-=21
# Vector projection of actual boundary edges, not a concept illustration.
def view(shapes,x,y,axes=(0,1),scale=1.7,label=''):
 maxaxis=max(([pt.Point.x,pt.Point.y,pt.Point.z][axes[1]] for s in shapes for pt in s.Vertexes),default=0);text(x-70,y+maxaxis*scale+15,label)
 for s in shapes:
  for e in s.Edges:
   pts=e.discretize(Deflection=.15)
   if len(pts)<2:continue
   path=c.beginPath()
   for i,pt in enumerate(pts):
    a=[pt.x,pt.y,pt.z];x1=x+a[axes[0]]*scale;y1=y+a[axes[1]]*scale
    if i==0:path.moveTo(x1,y1)
    else:path.lineTo(x1,y1)
   c.setLineWidth(.35);c.drawPath(path)
def dim(x,y,length,scale=1.7,vert=False):
 end=(x,y+length*scale) if vert else (x+length*scale,y);c.line(x,y,*end)
 for a,b in [(x,y),end]:c.line(a-3,b-3,a+3,b+3)
 text((x+end[0])/2+4,(y+end[1])/2+3,f'{length:.2f}',9)
page('전체 조립 / 정면 / 후면 / 측면',1)
ss=pose(0);printsh=[s for k,s in ss.items() if not k.startswith('REF_')]
view(printsh,170,420,(0,1),1.7,'FRONT +Z');view(printsh,440,420,(0,1),1.7,'REAR -Z (same XY datum)');view(printsh,700,420,(2,1),1.7,'SIDE X')
view([s for k,s in pose(90).items() if not k.startswith('REF_')],1000,420,(2,1),1.4,'OPEN 90 DEG')
dim(170-v['frame_size_mm'][0]*.85,250,v['frame_size_mm'][0]);dim(70,420-g['oy']*1.7,v['frame_size_mm'][1],vert=True)
notes([f'Payload {v["payload_mm"]} mm: {v["payload_status"]}',f'Folded incl. gate {v["folded_thickness_with_gate_mm"]:.1f} mm ASSUMED',f'Open incl. gate {v["open_thickness_with_gate_mm"]:.1f} mm ASSUMED','Face/card outward +Z; phone behind -Z','Gate: two magnets pairs + two hard shoulders','Phone base: ADHESIVE TO PHONE CASE','No card/holder glue, screw or drilling','Four-bar links: print part04 TWICE'],x=720,y=215);c.showPage()
page('분해 조립 / 단면 / 접힘 기구',2)
ex=[]
for i,(k,s) in enumerate((item for item in pose(90).items() if not item[0].startswith('REF_'))):
 sh=s.copy();sh.translate(V((i%2)*65,0,-i*30));ex.append(sh)
view(ex,210,460,(0,2),1.4,'EXPLODED XZ: positions schematic')
cutbox=Part.makeBox(.02,250,150,V(-.01,-125,-90));sections=[]
for s in pose(90).values():
 q=s.common(cutbox)
 if not q.isNull():sections.append(q)
view(sections,620,410,(2,1),1.6,'TRUE SECTION X=0 (OPEN)')
notes(['1 Main frame (PETG)','2 Magnetic gate (PETG)','3 Frame connector (PETG)','4 Two identical swing links (PETG)','5 Adhesive phone base (PETG)','6 Side liner x2 (TPU, free thickness)','Steel pivot/index pins and R-clips separate','M3 mount screws: initial assembly only','Open gate: pull +Z, then move +Y','Disconnect phone: lower pivot pins removed'],x=860,y=690);c.showPage()
coords={
'01_Main_Frame':[f'Payload cavity X +/-{g["cx"]:.2f}, Y +/-{g["cy"]:.2f}',f'Back plate Z0..3; lip Z{g["lipz"]:.2f}..{g["top"]:.2f}',f'Nominal rail wall {p["rail_t"]} mm',f'Gate pod centers X +/-{g["podx"]:.2f}',f'Pod Y{g["cy"]-13:.2f}..{g["cy"]+5:.2f}',f'Open-front pockets 7.6 wide, Y{g["cy"]-11:.2f}..{g["cy"]+3:.2f}',f'Pocket floor Z3.0; TONGUES enter from +Z','4x D3.4 at (X,Y)=(+/-17,+/-42), axis Z','4x counterbore D6.2 depth1.8 from Z3',f'2x magnet pocket D5.2 depth2.2 from Z3',f'Magnet centers X +/-{g["podx"]:.2f}, Y{g["gatepinY"]:.2f}',f'Magnet recess minimum floor 0.8mm'],
'02_Locking_Gate':[f'Two tongues: 7 wide, Z3.3..7.3 (thickness4)',f'Tongue Y{g["cy"]-10.7:.2f}..{g["cy"]+3:.2f}',f'Top crossbar Z{g["top"]+.3:.2f}..{g["top"]+2.8:.2f}',f'Front lip Z{g["lipz"]:.2f}..{g["top"]:.2f}',f'2x magnet pocket D5.2 depth2.2 from Z3.3',f'Magnet centers X +/-{g["podx"]:.2f}, Y{g["gatepinY"]:.2f}','Magnets D5x2 ASSUMED; pocket clearance0.1 radial','Closed faces: frame magnet Z3; gate magnet Z3.3','Pull Z to clear shoulders, then move +Y','No steel fixing pin needed for card change'],
'03_Grip_Connector':['Back mounting plate44 x96 x2, Z-2..0','4x D3.4 at (X,Y)=(+/-17,+/-42)',f'Fork X[-{g["forkout"]},-{g["forkin"]}],[{g["forkin"]},{g["forkout"]}]','Fork Z-15.5..-2, thickness9, gap19',f'Pivot centers Y +/-{g["S"]}, Z{g["pz"]}','Pivot axis X; D3.2 through forks',f'Index holes: radius{g["ir"]}, 0 / 90 deg ONLY',f'Index coords: Y=station+{g["ir"]},Z={g["pz"]};',f'and Y=station,Z={g["pz"]-g["ir"]}','Stop block behind arm: Ystation-7..-4.3','R-clips and axial shims not modeled'],
'04_Collapsible_Grip':[f'PRINT QTY2. Capsule Xwidth{p["link_width"]}, Ylength{p["link_length"]+8}, Z8',f'Axis X; pin D3.2; center distance{p["link_length"]}',f'Original centers (Y,Z)=(-{g["S"]},{g["pz"]}),',f'(-{g["S"]}+{g["L"]},{g["pz"]})',f'Index D3.2 at Y=-{g["S"]}+{g["ir"]},Z={g["pz"]}','Rotate around upper pivot axis X for motion','Steel D3 pins; no printed live hinge','Two links + connector + base form parallelogram'],
'05_Phone_Base':[f'Base {p["base_w"]} x{p["base_h"]} x{p["base_t"]} R7',f'Folded base center Y{g["L"]}; Z{p["base_back_z"]}..{p["base_back_z"]+p["base_t"]}',f'Lower pivots Ycenter +/-{g["S"]}, Z{g["pz"]}','Fork X same as connector; Y +/-4.5','Fork top Z-2.5 in folded state','Pin axis X, D3.2 through','Flat rear face: phone-case adhesive target','62x62x1 adhesive envelope ASSUMED','No adhesion performance verified','Release lower pins to detach body from base'],
'06_TPU_Side_Liner':[f'Free thickness1.0 x110 x{v["payload_mm"][2]}','Quantity2, TPU85-95A trial or cut silicone','Target compressed thickness0.8 per side','Trim corners and fit coupons BEFORE slab','Rear strip free0.6 / compressed0.5 (cut)','Front strip free0.5 / compressed0.4 (cut)','Never glue pads to the slab/old case']}
for n,(name,s) in enumerate({**parts,**extras}.items(),3):
 page(name+' / 상세 치수',n);view([s],200,430,(0,1),1.8,'XY assembly datum');view([s],510,430,(2,1),1.8,'ZY side')
 B=s.BoundBox;dim(200+B.XMin*1.8,430+B.YMin*1.8-15,B.XLength,1.8);dim(200+B.XMin*1.8-15,430+B.YMin*1.8,B.YLength,1.8,True)
 notes(coords[name]+['General FDM target +/-0.3 mm, NOT verified','Gate slot clearance0.3 mm PER SIDE','All contact edges finish R0.5 min','Material TPU for06, PETG for01..05','Refer to STL_PRINT for print orientation'])
 c.showPage()
page('자석 게이트 확대 단면 / 접착 베이스 / 공차',9)
# Cut at magnet/pod center. True YZ section, centered on gate region for readability.
slab=Part.makeBox(.02,40,40,V(g['podx']-.01,g['cy']-20,-10));section=[]
for k,s in pose(0,True,False,False).items():
 if k in ['01_Main_Frame','02_Locking_Gate'] or 'Magnet' in k:
  q=s.common(slab)
  if not q.isNull():
   q.translate(V(0,-g['cy'],0));section.append(q)
view(section,240,430,(2,1),9,'TRUE MAGNET SECTION / ZY, shifted Y datum')
notes(['Tongue seated in open-front pocket','Pocket end wall at Ycy+3..cy+5 blocks +Y','Magnet pairs resist lift: force UNTESTED','Frame magnets glued into printed frame ONLY','Gate magnets glued into printed gate ONLY','Do NOT bond magnets to payload','Both pairs opposite poles facing; identify before bond','Air gap0.3 nominal + actual glue/recess variation','Do not specify holding force without supplier/test','Adhesive base: case-compatible film, not bare phone','Surface prep/cure per selected adhesive datasheet','MagSafe option compared in report, NOT manufactured'])
notes(['공차는 목표치이며 출력 공정 검증값이 아님. XY 한쪽0.8, 패드 압축 목표0.8.','먼저 쿠폰으로 삽입 마찰/구멍/게이트 간극을 보정. 거친 출력면을 카드에 문지르지 말 것.','자석은 인장뿐 아니라 박리와 반복 열림 시험이 필요. 기계적 걸림턱도 들린 게이트를 막지 못함.'],x=50,y=170);c.showPage()
page('조립 순서 / 소재 / 색상 / 검사',10)
notes(['1. 선택한 A/B안의 실제 수납물 치수와 모서리·분리면·무게를 측정하고 JSON 파라미터 수정.','2. STL_PRINT 각01/02/03/05는1개, 04는2개, 06은2개. mm,100% 배율. PETG + TPU.','3. 서포트 제거, 접촉부 R0.5 이상 디버링. 구멍Ø3.2에 실제Ø3 핀을 손으로 통과시켜 확인.','4. 프레임과 연결판을 M3 버튼헤드4개/잠금너트로 조립. 머리 돌출은 수납물 손상 위험.','5. 링크2개를 위·아래 네 축에 끼워Ø3 클레비스 핀4개와 R클립·와셔·심으로 체결.','6. 0/90도에서 인덱스핀2개를 넣어 고정. 접기 전 두 인덱스핀을 제거. 회전축핀은 빼지 않음.','7. 프레임/게이트에 자석D5x2 네 개를 극성 맞춰 공급사 승인 접착·완전 경화. 지그로 평면도 확인.','8. 연질 라이너를 새 프레임에만 고정. 게이트를 든 상태에서 더미/슬랩을 위쪽에서 삽입.','9. 두 게이트 발을 열린 포켓에 내려놓아 닫음. 어깨가 끝벽 안쪽에 들어갔는지 양쪽 확인.','10. 카드 교체: 게이트를 먼저 +Z로 들어 걸림턱을 벗기고 +Y로 빼냄. 도구/고정핀 없음.','11. 폰 케이스에 적합한 접착제/양면 필름을 선정. 프린트 베이스를 평탄하게 마감하고 공급사 조건대로 부착·양생.','12. 더미로 인장·전단·박리·비틀림·열·반복·낙하 시험. 실제 폰/카드 사용은 그 결과로 판단.','매트 블랙:01~05 검정. 투톤:01/05 검정,02/03/04 실버. 실버 필라멘트는 티타늄 금속이 아님.','거치 성능은 미검증. 자석 게이트와 폰 접착의 유지력도 미검증. 제작용 기구 검토 모델이며 인증품이 아님.','같은 폰 베이스에 접착한 뒤 카드/프레임을 분리하려면 하부 축핀2개를 제거. 베이스는 케이스에 남음.'],x=50,y=710)
c.showPage();c.save()
# Short shop/assembly PDF, actual plain language instructions.
c=canvas.Canvas(str(r/'drawings'/'Assembly_and_Print_Guide_ko.pdf'),pagesize=A4);WA,HA=A4
for pg,lines in enumerate([['PSA Grip V02 출력 / 조립 의뢰서',title,'예비 시제품용 — 실측 및 시험 전 제작 확정 금지','STL_PRINT/01_Main_Frame.stl 1개','STL_PRINT/02_Locking_Gate.stl 1개','STL_PRINT/03_Grip_Connector.stl 1개','STL_PRINT/04_Collapsible_Grip.stl 2개','STL_PRINT/05_Phone_Base.stl 1개','STL_PRINT/06_TPU_Side_Liner.stl 2개','01~05 PETG,06 TPU85-95A 또는 실리콘 재단 대체.','0.4노즐/0.2레이어/외벽6+/초기 하중 검토 인필100% 시작 조건.','출력 방향은 제안:01 측면세움,02 눕힘,04 축구멍수직,03/05 판면바닥.','서포트/브림/빈층/구멍막힘/층간 하중을 업체가 슬라이서에서 검토.','실제 슬라이싱/출력/강도 시험은 미실행.','프레임과 연결판 M3 4개 외 카드 교체에 나사나 고정핀은 없음.','자석4개, 축핀4개, 인덱스핀2개, R클립6개,심/패드 별도.','자석은 새 프린트부에만 접착, 기존 카드·슬랩·알루미늄 케이스 접착 금지.'],['조립 / 검수 순서','1. 실제 수납물을 측정해 A/B 규격 선택. 더미로 맞춤 먼저 확인.','2. 서포트 제거·R0.5 디버링·핀 구멍 게이지 검사.','3. 프레임-연결판 M3 체결, 머리가 수납물에 닿지 않는지 검사.','4. 링크2개 + 회전핀4개 + R클립4개 조립, 축 유격을 심으로 조절.','5. 0/90도 인덱스핀2개 + R클립2개로 각도 고정.','6. 자석 극성/포켓 맞춤 후 승인 접착·양생. 자석 탈락 시험.','7. 패드 부착 후 게이트를 들어 더미 삽입. 양쪽 발을 내려 닫음.','8. 손으로 +Y 밀림/게이트 들림/슬랩 흠집 확인.','9. 폰 케이스 재질에 맞는 접착 선정·표면처리·압착·양생.','10. 독립 폰 테더와 더미로 보고서의 하중/온도/낙하 시험.','게이트 개방은 +Z 들어올림 후 +Y 분리. 자석 성능 미검증.','접착 베이스는 케이스에 남음. 하부 회전핀2개로 본체 분리.','거치/UV/자석 유지력/접착 유지력/실물 강도는 미검증.','블랙 단색:모두 검정. 투톤:프레임/베이스 검정,게이트/연결판/링크 실버.','프린터가 미정이므로 G-code 없음. PDF 자체는 프린터 입력이 아님.']]):
 for i,s in enumerate(lines):c.setFont('HYSMyeongJo-Medium',16 if i==0 else 10);c.drawString(28,HA-44-i*35,s.replace('·',' / '))
 c.showPage()
c.save()
# Parameter sources: 81/136/6 are engineering assumptions; 86/142/11 seller only.
with (r/'parameters.csv').open('w') as f:
 wr=csv.writer(f,lineterminator='\n');wr.writerow(['name','value','unit','status','source'])
 for k,val in p.items():wr.writerow([k,val,'g/cm3' if 'density' in k else ('g' if k.endswith('_g') else 'mm'),'SELLER_REFERENCE_NOT_MEASURED' if k in ['case_w','case_h','case_t'] else 'ASSUMED_NOT_MEASURED','User seller table' if k in ['case_w','case_h','case_t'] else 'Engineering assumption; no verified PSA official dimensions'])
F=v['COM_states']['0']['mass_g']/1000*9.81*10;torque=F*.06;indexforce=torque/p['index_radius']*1000
printmass=sum(z['mass_solid_equiv_g']*z['quantity'] for k,z in v['parts'].items() if k!='06_TPU_Side_Liner')
(r/'README_ko.md').write_text(f'''# PSA Grip V02 — {title}

**예비 시제품용 — 실측 및 시험 전 제작 확정 금지.**

두 구조를 실제 CAD로 생성했다. 기본 폴더는 PSA 슬랩 직접 수납(A), `variants/aluminum_case/`는 기존 알루미늄 케이스 수납(B)이다. A의81×136×6mm는 전부 가정. B의86×142×11mm는 이전 판매자 표기이며 실측 또는 PSA 공식 규격이 아니다. 실제 슬랩 두께·코너·단차·질량을 측정해야 제작 확정할 수 있다. PSA 공식 페이지 접속은403으로 실패했고 규격을 확인하지 못했다.

## 이번 구조 변경

- 카드 교체 게이트: 나사/고정핀 대신 **두 자석쌍 + 기계적 끝벽**. 먼저 바깥쪽(+Z)으로 들어 걸림턱을 벗기고 위(+Y)로 분리. 단순히 +Y로 밀면 두 발이 끝벽에 걸리는 모델이다. 자석만으로 낙하 안전을 보장하지 않는다.
- 그립: 상용 주름 외형이 아니라 **링크2개, 회전축4개,0/90도 인덱스핀2개**의 조립 가능한 평행 링크. 회전축과 각도핀은 금속 부품이며 카드 교체용 고정핀과 별개다. 접기 전 각도핀 제거 필요.
- 스마트폰: **폰 케이스에 접착하는 평면 베이스**. 접착제 종류/두께/표면처리/양생은 선정·시험 필요. 본체 분리는 하부 축핀2개를 빼는 방식이며 베이스는 케이스에 남는다. MagSafe는 비교안이며 이 버전의 기본 부착이 아니다.
- 색상: 매트 블랙 단색 / 블랙×티타늄 실버. 실버는 필라멘트 색상으로 티타늄 금속 재질을 의미하지 않는다.

## 파일

- `PSA_Grip_V02.FCStd`, `PSA_Grip_V02_Assembly.step`: 실제 생성. 조립 STEP에는 제작품6솔리드(링크2개 포함), 표준 금속품/카드/폰은 제외.
- `STL/01_Main_Frame.stl` ~ `05_Phone_Base.stl`: 원본 조립 좌표. 04는 링크1개 파일이며 **2개 출력**.
- `STL_PRINT/`: 출력 방향과 바닥Z=0으로 변환한 동명STL. 01/02/03/05 각1개,04 두개,06 TPU라이너 두개.
- `STEP_parts/`, `states/Assembly_0deg.step`, `states/Assembly_90deg.step`.
- `drawings/PSA_Grip_V02_Manufacturing_A3.pdf`: A3 10장. `Assembly_and_Print_Guide_ko.pdf`: A4 2장.
- `renders/`: 실제 CAD 기반 블랙/투톤,정면/후면/접힘/펼침/폰장착/분해. 카드/라벨은 인증 정보 없는 중립 표시, 실물 형상 증거가 아니다.
- `BOM.csv`, `parameters.csv`, `assembly_guide_ko.md`, `validation_report_ko.md`, `validation_results.json`.

## 현재 결과

대상 수납물 {v['payload_mm']} mm. 전체 프레임/게이트 외형 약 {v['frame_size_mm']} mm. 게이트 돌출 포함 접힘{v['folded_thickness_with_gate_mm']:.1f}mm, 펼침{v['open_thickness_with_gate_mm']:.1f}mm(접착1mm 가정). 일반 원형 그립톡보다 두꺼운 검토용 기구다. 출력품 PETG 솔리드 등가 합계{printmass:.1f}g, 전체 폰 포함 가정{v['COM_states']['0']['mass_g']:.1f}g. 실제 인필/철물/수납물 측정 전 확정 질량이 아니다.

기구 샘플19각도 간섭 {len(v['body_interferences'])}건, 표준품 외형 간섭 {len(v['hardware_interferences'])}건, 게이트 개방 및 수납물 삽입 샘플 검사 결과는 JSON에 기록했다. 패드 압축·마찰·자력·접착력·실물 출력·내구성은 미검증. 결과에 남은 교차 체적이 있으면 해결 전 조립 가능 판정 금지. 이 검사는 완전한 연속 운동 증명이나 구조 안전 인증이 아니다.

## 재생성

저장소 `deliverables/psa_grip_v02/`에서 `/usr/bin/python3 generate_model.py`. FreeCAD1.0, 시스템 Python, ReportLab, Blender CPU Cycles, Poppler 필요. JSON을 수정하면 두 안을 함께 재생성한다. FCStd는 부품별 Part::Feature와 파라미터 표이며 표 편집만으로 갱신되는 완전한 스케치 구속 모델은 아니다. 게이트·축·스톱 일부 상세는 스크립트 상수이므로 큰 변경 시 도면도 검토한다.

기존 V01은 변경하지 않았다. 이전 아이보리 구매 팝업 V02는 `deliverables/archive/psa_grip_v02_case_concept/`에 원본 그대로 보존했다.
''')
(r/'assembly_guide_ko.md').write_text(f'''# {title} — 출력·조립

예비 시제품용 — 실측 및 시험 전 제작 확정 금지.

## 출력

PETG는01~05, TPU85~95A는06 시작 후보. PC/PA 대안은 수축·장비·강도 쿠폰 재검증 필요. 라이너는 실리콘 재단으로 대체 가능. TPU는 회전 링크나 프레임 하중부로 쓰지 않는다. 0.4mm노즐/0.2레이어/외벽6+/첫 하중 검토100%인필은 미검증 시작 조건이다. 기종 미정이므로 G-code 없음.

STL_PRINT는 바닥Z=0. 프레임은 측면 세워 출력(높이 약{v['parts']['01_Main_Frame']['print_bounds_mm'][2]:.1f}mm), 게이트 눕힘, 링크는 축구멍 수직, 커넥터/베이스는 판면을 바닥에 둔다. 프레임의 얇은 레일, 커넥터의 스톱블록, 수평 축구멍과 게이트의 목·립 하부는 서포트와 층간 하중을 업체가 확인한다. 실제 슬라이싱은 미실행이며 모든 부품을 한 플레이트에 인쇄해야 하는 것은 아니다.

출력 후 접촉부 R0.5 이상 디버링, 구멍 통과 게이지, 평탄도, 언더컷/서포트 제거를 확인한다. 포켓D5.2와 실제D5자석 사이0.1mm 반경 공차는 프린터에 따라 부족할 수 있어 쿠폰 필요. 자석을 억지 압입하지 않는다. 작은 자석 포켓 바닥0.8mm는 천공·접착 과열·압입 파손 주의.

## 조립

1. 실측에 맞는 A/B안을 선택하고 더미로 진행. 실제PSA슬랩의 모서리·용접 테두리를 분해/가공하지 않는다.
2. 프레임과 커넥터를 M3 버튼헤드4개/잠금너트로 조립. 머리D<=6.2/H<=1.8이 카운터보어 안에 들어가 수납물에 닿지 않아야 한다. 길이M3x10은 가정. 와셔를 포함한 스택 측정 후 확정.
3. 링크2개, 네 회전축에 Ø3클레비스핀4개·R클립4개·축심 조립. 포크간격19/링크폭18로 한쪽0.5mm 심이 명목값이다. 실제 핀의 머리/와셔/클립·구멍 위치 확인. 포크 외폭37mm를 통과하는 사용길이>=39mm가 출발점이며 구매규격 확정 필요.
4. 0/90도에서 인덱스핀2개로 잠금. 두 링크 각도가 같아야 삽입 가능. 접기 전 두 인덱스핀을 빼고 회전축핀은 그대로 둔다. 0/90도 이외에는 하중 지지용 잠금 없음.
5. 자석 네개(D5x2 가정)를 두쌍으로 극성 표시. 프레임 두개/게이트 두개를 새 프린트 포켓에만 공급사 승인 접착으로 고정·양생. 프레임자석면Z3/게이트Z3.3로 명목공극0.3mm. 접착층과 코팅/공차가 공극을 늘린다. 실제 자력·온도·부식·탈락 시험 전 사용 금지. 카드에는 접착하지 않는다.
6. 측면 라이너 자유1mm를 압축0.8mm 목표로 맞춘다. 뒤쪽 스트립 자유0.6/압축0.5, 앞립 자유0.5/압축0.4. 라이너는 새 프레임에 고정. 억지 삽입/모서리 압박이 있으면 심·파라미터 보정. 실제 압축/마찰은 미검증.
7. 게이트를 +Z로 들어 +Y로 치워 놓고 수납물을 +Y에서 삽입. 게이트 양쪽 발을 포켓에 내려 앉혀 두 어깨가 끝벽 안에 들어가도록 한다. 단순 +Y 당김에 기계적으로 걸리는지 확인. 게이트 +Z 들림은 자석에 의존하므로 하중 시험 필요.
8. 폰 케이스 재질·도장에 맞는 접착제/구조용 양면필름을 선택. 62x62x1mm는 형상 대용값일 뿐 특정접착제품 사양이 아니다. 공급사 지침의 세척·프라이머·압착·양생·온도를 준수한다. 저표면에너지/실리콘/유연케이스에는 그대로 붙을 것이라 가정하지 않는다. 기존 PSA슬랩/알루미늄케이스에 폰접착제를 바르지 않는다.
9. 폰 케이스에 베이스를 붙이면 폰과의 접속은 접착식이다. 본체 분리 시 하부 회전축핀2개 제거로 카드+프레임+링크를 분리하고, 베이스는 케이스에 남긴다. 접착제를 반복 박리해 탈부착하는 구조가 아니다.
10. 독립 폰 테더와 더미를 사용해 보고서의 시험을 수행. 성공 전 실제폰/고가카드로 매달지 않는다.

## 소재·양산 개선

매트 블랙은 모두 검정; 투톤은01/05검정,02/03/04실버. 실버 PETG는 금속강도를 갖지 않는다. 실제 카드 UV차단은 슬랩/기존케이스 자료 없이는 미검증이며 별도UV커버는 이번 CAD에 없음. 양산에서는 금속부싱/클립유실방지, 충분한 뿌리필렛과 리브, 출력대신사출 벽두께/구배/언더컷 분리, 표준화된 자석포획 커버 및 양면 개폐 잠금, 검증된 폰케이스 접착 접속을 개선한다. 현 파트는 금형 제작 확정본이 아니다.
''')
(r/'validation_report_ko.md').write_text(f'''# {title} — 검증 보고서

예비 시제품용 — 실측 및 시험 전 제작 확정 금지.

## V01 분석 및 변경 근거

V01은 86x142x11 알루미늄 케이스를 U형 크래들과 M3 게이트로 고정하고32mm 단일 링크/상부핀/하부마찰힌지를 썼다. 실제 PSA슬랩 치수를 확인한 설계가 아니며, 도구 없이 카드 교체 불가, 하부 마찰 토크 미검증, 자석모듈 구매품 미매칭이었다. 이전 아이보리 V02는 상용 팝업 외형만 있었고 기능 기구 자체는 미설계였다. 두 결과는 보존했다.

이번에는 직접슬랩/기존케이스 두 파라미터안, 자석식 리프트게이트,0/90도 잠금 평행링크, 접착식 폰케이스 베이스로 변경했다. 주름형 TPU 생경첩/팝업을 임의로 검증품처럼 출력하지 않는다.

게이트 비교: 스냅핏은 간단하지만 마모/크리프/층간피로와 슬랩 접촉 위험, 나사형은 강하지만 교체 도구 필요, 슬라이드/힌지형은 조립공차·핀유실 부담. 사용자 요청에 따라 두 자석쌍이 +Z들림을 억제하고 두 발/끝벽이 +Y탈출 하중을 받는 탈착 게이트를 선택했다. 도구 없이 열리지만 자석만으로 낙하 안전을 보증하지 않는다. 회전축핀과 각도핀은 내부 기구용으로 유지.

폰 부착 비교: MagSafe는 편리하지만 구매품/폰케이스별 전단·박리·회전 및 자석면접속을 별도 검증해야 한다. 접착식은 넓은 면과 낮은두께가 장점이나 재질/표면처리/열/시간의존·박리·잔사와 재부착 문제가 있다. 사용자 요청에 따라 접착식을 기본으로 모델링했다. 상용 원형 팝업 대안은 제품 사양/체결면/편심하중 검증 후 교체모듈로 검토 가능하며 이번 실제링크기구의 검증을 그대로 전용할 수 없다.

## 실제 실행한 검사

수납물 외형{v['payload_mm']}mm는 {v['payload_status']}. PSA공식규격은 확인하지 못했다. 두 안 모두 설계상 맞춤 대상이지 모든PSA세대/특수슬랩에 호환된다는 뜻이 아니다.

모든 제작 단품은1개 유효닫힌솔리드, STEP재가져오기체적검사와 출력STL닫힘검사 실행. 04는 동일링크2개를 따로 출력. 조립은6개 PETG솔리드, TPU별도. 부품별 체적/크기/수치는validation_results.json.

0~90도5도간격19개 상태의 부품/수납물/폰/카메라/접착외형간 양의 교차체적: {len(v['body_interferences'])}건. 철물외형 0/45/90도 검사: {len(v['hardware_interferences'])}건. 게이트 +Z들기16샘플 및 +Y치우기16샘플 교차: {len(v['gate_open_sweep_interferences'])}건. 게이트를 치운 수납물 +Y삽입16샘플 교차: {len(v['payload_insertion_interferences'])}건. 닫힌 두 발을 +Y2mm 밀면 각 끝벽과의 교차체적 {v['gate_blocks_on_each_end_wall_mm3']}mm³로 기하학적 저지 확인. 이 수치는 강도가 아닌 의도적 걸림 여부다.

연속운동/실물삽입/마찰/자석힘/TPU변형은 미검증. R클립·와셔·심·접착층 상세·나사산은 모델에 없고 검사에서 제외. 그림용 카드/라벨이 수납외형 안에 들어가는 것은 의도된 그래픽이며 간섭집계 제외. 자석과프린트부는 포켓에서 반경0.1여유를 두었지만 실제 접착/고정은 미검증.

## 질량·무게중심과 간이 구조 검토

PETG1.27g/cm³가정, 출력물 솔리드등가{printmass:.2f}g. 수납물 질량 {p['slab_mass_g'] if is_slab else p['case_mass_g']}g가정, 폰+케이스224g, 철물28g,패드/접착7g가정. 전체 {v['COM_states']['0']['mass_g']:.2f}g. 실제 인필·소재·수납물 중량에 따라 달라진다. COM(원점프레임후면Z0): {json.dumps(v['COM_states'],ensure_ascii=False)}. 철물/패드 위치는 단순화.

보수적 동적계수5×추가여유2를 가정해 F=mg×10={F:.2f}N. 이는 낙하충격 상한이나정격이 아니다. 편심60mm 가정모멘트 {torque:.2f}Nm. 한 인덱스핀만 전 모멘트를 받는 보수적 접선력 {indexforce:.1f}N(반경6mm). D3강철핀 이중전단 평균 {indexforce/(2*math.pi*1.5**2):.2f}MPa; 두9mm포크 평균면압 {indexforce/(2*9*3):.2f}MPa;18mm링크 평균면압 {indexforce/(18*3):.2f}MPa. 링크약축단면계수18x8²/6=192mm³를 쓴 굽힘 상한 {torque*1000/192:.2f}MPa. 실제 핀재질/곡률/구멍가장자리찢김/루트필렛/층간강도는 미검증이며 허용응력이나안전율통과를 주장하지 않는다. 4M3마운트 균등축하중만 보면 볼트당{F/4:.2f}N이나 카운터보어 잔여1.2mm의머리관통·편심/판굽힘검증은 별도 필요.

게이트 두 발의 +Y면압은 이상적균등분배/7x4 접촉면에서 {F/(2*7*4):.2f}MPa. 실제끝벽강도/프린트층/자석들림박리미검증. 자석D5x2 두쌍의공칭인장력을 합산해 안전하다고판정하면안된다. 프레임두께·자석공극0.3/코팅/접착/비정렬을 포함한 시험이 필요하다.

접착62x62=3844mm²의균등전단만 가정하면 {F/3844:.4f}MPa이지만, 실제로는 모멘트와 가장자리 박리가지배할수있다. 이 평균응력은 접착선정/합격판정이아니다. 제조사자료와 폰케이스조합에서 시험한다.

## 미검증 항목과 개선

- 슬랩호환: 최대폭/높이/두께/용접테두리·코너·질량 실측. 직접슬랩81x136x6은전부가정. 케이스86x142x11은판매자참고만.
- 표면손상: 새프레임에만연질패드, R0.5후가공,압입금지. TPU초기1.0→0.8압축의마찰과삽입하중미검증.
- 자석게이트: +Y는어깨가막지만 +Z는자석의존. 충격·모서리걸림·비틀림에의한들림 및자석자체탈락시험. 추후자석포획캡/별도안전래치가필요할수있음.
- 접이식: 0/90잠금외각도사용금지,인덱스핀2개삽입확인. 반대방향과90도넘김의모든접촉을정격스토퍼로간주하지말것.손가락끼임가드미포함.
- 폰접착: 기종/케이스재질미정. 71.5x149.6x8.25,후면케이스1.5,카메라38x38x4/(-15,+52)는가정. 접착1mm도대용값.하부핀분리후베이스는케이스에남음.
- 비틀림/흔들림: 두링크로자유회전을줄였으나핀여유/층수축/접착유연성미검증. shim맞춤과금속부싱검토.
- 거치: 이번정격기능에포함하지않음.0/90평행링크만으로지지영역/마찰/터치외력검증미수행.
- 출력: 모델유효성이슬라이싱/출력성공증거는아님. 업체별서포트·브림·수축/강도쿠폰필요.
- UV:슬랩/케이스의차단데이터미확인. 별도UV커버없음.투명표현은차단성능을의미하지않음.

## 실물 시험계획 (전부 미실행 / 잠정 기준)

동등질량더미부터시험. 삽입/게이트500회,그립1000회초기/10000회목표:깨짐/들림/흠집없음,핀구멍증가0.2mm이하. 더미에{F:.1f}N60초인장/전단양방향과{torque:.2f}Nm비틀림/박리:이탈·균열없음,잔류변형0.5mm이하. 자석한쌍의손실상태에서사용하중으로이탈하지않는지 별도시험하되현재단일고장안전성미검증. 접착은공급사양생후실제폰케이스조합으로별도시험.45°C24h정적1g,열사이클/습도시험후유지력재검사. 독립폰테더와차폐지그로0.5m더미낙하부터진행,1m6방향각3회는후속목표. 이조건들은소비자안전인증이아니며실패하면자석크기/공극/기계안전래치/접착/금속보강을재설계해야한다.

## 사용자 요청 9개 검증 항목 판정

1 정상삽입:모델샘플검사,실물미검증. 2고정:끝벽기하확인,자석강도미검증. 3흠집:패드계획,실물미검증. 4접힘:19상태기하검사,반복미검증. 5폰간섭:가정외형범위검사,실측미검증. 6하중:간이계산만,강도미검증. 7출력:유효STL,실제슬라이싱/출력미검증. 8별도부품:BOM에기재. 9실측/시험:위목록과시험계획참조.
''')

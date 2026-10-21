#!/usr/bin/python3
"""Run from any directory with system Python + FreeCAD + ReportLab + Poppler.
Uses the unchanged sibling psa_grip_v01 source CAD outputs.
"""
from pathlib import Path
import sys,json,csv,shutil,subprocess,hashlib,zipfile
sys.path.append('/usr/lib/freecad/lib')
import FreeCAD as A,Part,Mesh
from FreeCAD import Vector as V
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
R=Path(__file__).resolve().parent;S=R.parent/'psa_grip_v01'
for x in ['STL_PRINT','PDF_DRAWINGS','REFERENCE']: (R/x).mkdir(exist_ok=True)
rows=[]
for num,name,axis,angle in [(1,'01_cradle',(0,1,0),90),(2,'02_top_gate',(1,0,0),90),(3,'03_link',(0,1,0),90),(4,'04_base_adapter',(0,0,1),0)]:
 shape=Part.read(str(S/'parts'/f'{name}.step'));orig=shape.Volume
 if angle:shape.rotate(V(0,0,0),V(*axis),angle)
 b=shape.BoundBox;shape.translate(V(-b.XMin,-b.YMin,-b.ZMin));b=shape.BoundBox
 mesh=Mesh.Mesh(shape.tessellate(.1));target=R/'STL_PRINT'/f'{name}_PRINT_mm.stl';mesh.write(str(target));check=Mesh.Mesh(str(target))
 assert shape.isValid() and check.isSolid() and abs(shape.Volume-orig)<1e-5
 err=abs(abs(check.Volume)-orig)/orig
 assert err<.002
 rows.append({'file':target.name,'quantity':1,'footprint_x_mm':round(b.XLength,3),'footprint_y_mm':round(b.YLength,3),'height_mm':round(b.ZLength,3),'material':'PETG prototype','closed_stl':check.isSolid(),'relative_volume_error':err,'rotation_axis':str(axis),'rotation_deg':angle})
 # Extract original part sheet (page 3,4,5,6), preserving dimension references.
 tmp=R/'PDF_DRAWINGS'/f'tmp_{num}_%d.pdf'
 subprocess.run(['pdfseparate','-f',str(num+2),'-l',str(num+2),str(S/'drawings'/'PSA_grip_A3.pdf'),str(tmp)],check=True,stderr=subprocess.DEVNULL)
 (R/'PDF_DRAWINGS'/f'tmp_{num}_{num+2}.pdf').rename(R/'PDF_DRAWINGS'/f'{name}_A3.pdf')
shutil.copy2(S/'drawings'/'PSA_grip_A3.pdf',R/'PDF_DRAWINGS'/'00_assembly_and_all_parts_A3.pdf')
for n in ['BOM.csv','assembly_guide_ko.md','validation_report_ko.md']:
 shutil.copy2(S/n,R/'REFERENCE'/n)
(R/'print_checks.json').write_text(json.dumps(rows,indent=2))
with (R/'print_manifest.csv').open('w') as f:
 wr=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');wr.writeheader();wr.writerows(rows)
pdfmetrics.registerFont(UnicodeCIDFont('HYSMyeongJo-Medium'))
c=canvas.Canvas(str(R/'01_PRINT_ORDER_ko.pdf'),pagesize=A4);W,H=A4
c.setTitle('PSA grip V01 prototype print order')
def line(y,s,size=10):c.setFont('HYSMyeongJo-Medium',size);c.drawString(34,y,s.replace('·',' / '))
line(800,'PSA 보호케이스 그립 — 3D 출력 의뢰서',17)
line(774,'예비 시제품용 — 실측 및 시험 전 제작 확정 금지',12)
lines=['목적: 86×142×11mm 기존 자석 잠금식 보호케이스용 맞춤·작동 확인 시제품.',
'보호케이스와 자석 모듈은 출력품이 아님. STL 4종을 각 1개 출력.',
'원본 조립 좌표를 출력 방향으로 회전하고 최저점을 Z=0으로 이동한 STL.',
'단위 mm, 크기 100%. 자동 축소/확대 금지. 기본 방향은 제안이며 업체 검토 필요.',
'권장 시작 조건: PETG, 노즐 0.4mm, 레이어 0.2mm, 외벽 6개 이상.',
'1차 하중 검토용은 인필 100%를 시작점으로 견적. 실제 강도 보증 없음.',
'브림 5~8mm 및 서포트는 슬라이서 미리보기에서 부품별 결정.',
'출력 전: 크기·바닥 위치·빈 층·서포트 접근성·구멍 막힘·층간 방향 확인.',
'출력 후: 서포트 제거, 접촉부 R0.5 이상 디버링, 휨·균열·구멍 치수 검사.']
y=740
for s in lines:line(y,s);y-=22
line(y-8,'파일 / 수량 / 배치 외형 X×Y×Z (mm)',12);y-=38
for q in rows:
 line(y,q['file'],10);y-=18
 line(y,f"각 1개 | {q['footprint_x_mm']} × {q['footprint_y_mm']} × {q['height_mm']} mm");y-=30
for s in ['크래들: 측면 세움, 높이94mm. 포크와 립 및 후면판에 서포트 검토.',
'링크: 축 구멍 수직 배치. 게이트: 긴 방향 눕힘, 립/플랜지 서포트 검토.',
'베이스: 원판을 바닥에 배치. 포크의 수평 축 구멍 서포트 후 게이지 확인.',
'최대 부품 배치: 약154mm 길이. 브림 포함 실제 사용 가능 베드로 확인.',
'기계별 G-code/온도/속도/서포트 설정은 업체가 선정. 이 패키지에 G-code 없음.']:
 line(y,s);y-=23
c.showPage();line(800,'조립·검수 및 출력 업체 회신 항목',16)
for i,s in enumerate(['도면 좌표는 원래 조립 좌표이다. 출력 STL의 회전된 좌표와 다르지만 형상은 동일.',
'일반 출력 치수 목표 ±0.3mm. 공정 보증치 아님. 출력 업체가 달성 가능 여부 회신.',
'축 구멍 설계 Ø4.3 / 잠금 구멍 Ø3.3 / 게이트 구멍 Ø3.4mm.',
'구멍은 출력 후 해당 볼트/핀의 자유 통과 확인. 재가공 시 확공 과다 금지.',
'케이스 수납 공간88×144mm; 실제 케이스 최대 외형·돌출부·코너 실측 필요.',
'완충재0.8mm(압축0.6 가정). 슬랩/기존 케이스에 접착제와 구멍 적용 금지.',
'조립 구매품: M4×50 축 볼트2개, M3×12 게이트 볼트2개, 잠금너트·와셔.',
'Ø3 탈락 방지 잠금핀1개, 1.5mm 스택 심4곳, 라이너와 독립 폰 테더 별도.',
'볼트/핀 길이는 구매품의 실제 체결 스택으로 확정. BOM과 조립 안내 참조.',
'상용 스마트폰 자석 모듈 미선정. 베이스 구멍 패턴은 아직 구매품에 미매칭.',
'따라서 출력 후 바로 실제 휴대폰/고가 카드를 넣어 사용하지 말 것.',
'프레임·게이트부터 케이스 더미로 맞춤 확인 후 링크/베이스 작동 시험 권장.',
'상부 힌지0/60/90도 잠금핀. 하부 힌지는 마찰 조임으로 유지력 미검증.',
'UV 차단 성능/자석 고정력/낙하/실물강도 미검증. 검증보고서 시험계획 참조.',
'업체 회신: 재료·장비·방향·벽수·인필·서포트 방식·예상 변형·후가공·가격·납기.',
'서포트 제거가 어려운 부위나 적층 파손 우려가 있으면 출력 전 협의.',
'입고 검사: 누락4종 확인, 크기·구멍·게이트 체결·삽입·핀 잠금·흠집 확인.']):line(758-i*31,s)
c.showPage();c.save()
(R/'README_ko.md').write_text('''# 프린트 전달용 패키지 V01

**맞춤·작동 검토용 예비 시제품. 실측 및 시험 전 제작 확정 금지.**

1. 출력 업체에 이 ZIP 전체를 전달하고 `01_PRINT_ORDER_ko.pdf`를 먼저 읽도록 요청하세요.
2. 실제 슬라이서 입력 파일은 `STL_PRINT/`의 `_PRINT_mm.stl` 4개입니다. 각 1개, 단위 mm, 배율 100%.
3. `PDF_DRAWINGS/`에는 전체 A3 7장과 부품별 A3 1장씩이 있습니다. PDF 자체는 프린터 입력 파일이 아닙니다.
4. `REFERENCE/`에는 구매품 BOM, 조립 순서, 검증 보고서가 있습니다.
5. 업체가 자신의 장비에 맞춰 슬라이싱하고 서포트/출력 방향을 검토해야 합니다. 기종을 몰라 G-code나 장비별 프로젝트 파일은 포함하지 않았습니다.

STL은 원본 부품의 형상을 유지하면서 제안 출력 방향으로 회전하고 양의 좌표와 Z=0에 배치했습니다. 출력 방향은 검증된 최적 방향이 아니며 업체가 변경할 수 있습니다. 특히 크래들은 세워 출력하므로 서포트와 브림, 휨/층간 강도를 먼저 검토해야 합니다. PDF 좌표는 조립 기준이므로 출력용 좌표와 다릅니다.

원본 `../psa_grip_v01/`의 STL은 조립 좌표입니다. 혼동을 피하려면 이 패키지 STL만 출력 업체에 전달하세요. 전체 CAD 원본은 원본 폴더에 보존되어 있습니다.

STL 4개를 실제 다시 읽어 닫힘과 체적 보존을 확인했습니다. 프린터에서 슬라이싱/출력/실물 조립은 미실행입니다. 자석 모듈 접속이 확정되지 않아 이 패키지는 완제품 생산 데이터가 아닙니다. 구매한 기존 보호케이스 자체, 자석, 나사, 핀, 패드는 별도입니다.

재생성: FreeCAD 시스템 Python에서 `/usr/bin/python3 build_print_kit.py`. 원본 sibling 폴더, ReportLab, Poppler 도구가 필요합니다.
''')
files=sorted(x for x in R.rglob('*') if x.is_file() and x.name!='SHA256SUMS.txt')
(R/'SHA256SUMS.txt').write_text('\n'.join(hashlib.sha256(x.read_bytes()).hexdigest()+'  '+str(x.relative_to(R)) for x in files)+'\n')
with zipfile.ZipFile(R.parent/'psa_grip_print_v01.zip','w',zipfile.ZIP_DEFLATED) as z:
 for x in sorted(R.rglob('*')):
  if x.is_file():z.write(x,x.relative_to(R.parent))
with zipfile.ZipFile(R.parent/'psa_grip_print_v01.zip') as z:assert z.testzip() is None
print(json.dumps(rows,indent=2))

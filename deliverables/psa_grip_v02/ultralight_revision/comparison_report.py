"""Human-readable reports derived from executed CAD results, no fabricated test pass."""
import csv,json,math
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape,A3
from reportlab.lib.units import mm
labels={'A_minimum':'A 최소 중량형','B_daily':'B 일상 휴대 검증 후보','C_protective':'C 보호 강화형'}
rows=[]
for key,v in results.items():
 m=v['mass'];rows.append([key,m['additional_nominal_g'],m['additional_low_g'],m['additional_high_g'],m['with_slab_nominal_g'],v['folded_accessory_thickness_mm'],v['open_accessory_thickness_mm'],m['max_popup_mass_for_30g_g']])
with (root/'comparison.csv').open('w') as f:
 w=csv.writer(f,lineterminator='\n');w.writerow(['design','added_nominal_g','added_low_g','added_high_g','with_slab_nominal_g','folded_mm','open_mm','max_popup_mass_for_30g_g']);w.writerows(rows)
with (root/'parameters.csv').open('w') as f:
 w=csv.writer(f,lineterminator='\n');w.writerow(['parameter','value','unit','source','status'])
 for k,value in p.items():
  unit='g/cm3' if 'density' in k else ('g' if k.endswith('_g') else ('count' if k.endswith('count') else 'mm'))
  w.writerow([k,value,unit,'Design assumption; NOT measured PSA or selected OEM specification','ASSUMED'])
 for key,v in results.items():
  for k,value in v['specs'].items():w.writerow([key+'.'+k,value,'configuration' if isinstance(value,str) else 'mm','Design starting value','ASSUMED / DESIGN'])
 for k,v,u in [('silicone_protector_outer','85 x 140 x 9','mm'),('silicone_protector_mass',14,'g'),('acrylic_slot','137 x 82.5 x 8','mm'),('storage_box','340 x 250 x 16 / 35 slabs','mm/count'),('aluminum_holder_outer','86 x 142 x 11','mm')]:w.writerow([k,v,u,'User supplied product descriptions or seller image; source URL and tolerance not independently verified','REFERENCE ONLY / NOT SLAB SIZE'])

intro='''# 빨간 범퍼·검은 완충부 초경량 V02 수정안

[추천 B안 CAD](B_daily/CAD) · [출력 STL](B_daily/STL_PRINT) · [A3 도면 PDF](B_daily/drawings/Ultralight_A3_Manufacturing.pdf) · [무게 비교](comparison_ko.md) · [검증 보고서](validation_report_ko.md)

![실제 CAD 기반 빨간 범퍼 B안](B_daily/renders/red_front.png)

![뒤쪽 리브와 원형 팝업](B_daily/renders/red_rear_open.png)

사용자가 올린 단순한 빨간 사각 범퍼와 검은 내부 테두리 이미지를 반영했습니다. 앞면과 뒷면은 열고, 뒤쪽 중앙의 작은 원형 접착면과 하중 전달 리브만 남겼습니다. 카드 앞면은 바깥쪽, 원형 팝업은 뒷면입니다. 스마트폰 연결은 폰 케이스에 접착하는 방식입니다.

상단 게이트는 두 쌍의 자석으로 닫으며 기계적 어깨와 두 개의 슬랩 스토퍼가 위쪽 이탈을 막습니다. 앞쪽(+Z)으로 게이트를 들어올리는 방향은 자석에 의존합니다. 작은 자석의 유지력은 미확인으로, 아래 시험에 실패하면 자석 확대 또는 별도 안전 걸쇠를 재설계해야 합니다. 자석 고정력을 검증한 제품으로 사용할 수 없습니다.

사진의 연속 테두리를 유지하면서 게이트에는 국부 두께 증가가 있습니다. 사진처럼 모든 위치가 같은 얇은 단면은 아닙니다. B안 뒷면에는 하중 때문에 T형 리브를 추가했습니다. 이는 실제 CAD에 포함됩니다.

슬랩 직접 수납형입니다. 알루미늄 케이스형은 기존 `../circular_popup_revision/variants/aluminum_case/`에 보존했으며 이 무게 표의 대상이 아닙니다. V01과 기존 V02 파일은 변경하지 않았습니다.

## 치수와 자료의 의미

81×136×6mm, 모서리 R3, 슬랩 50g(35~80g 범위)은 모두 ASSUMED입니다. 보내주신 실리콘 보호케이스 85×140×9mm/14g, 아크릴 슬롯 137×82.5×8mm, 35장 보관함 치수는 슬랩 자체의 실측이 아닙니다. 14g은 실리콘 보호케이스 단품 참고값이며 본 제품의 팝업·자석·접착재 포함 무게와 직접 비교할 수 없습니다. 86×142×11mm도 기존 알루미늄 보호케이스 판매자 값입니다. 판매자 내경80×135mm의 용도는 확인되지 않았습니다.

참고 폰+케이스는 71.5×149.6×9.75mm/224g, 카메라 돌출4mm로 가정했습니다. 카메라·MagSafe 위치의 공식 기구 도면을 확보하지 않았습니다. 이번 설계는 MagSafe 부착을 사용하지 않습니다. 표준·공식 인증을 주장하지 않습니다.

## 실제 생성 파일과 재현

`A_minimum/`, `B_daily/`, `C_protective/` 각각에 다음 파일이 있습니다.

- `CAD/PSA_Grip_Ultralight.FCStd`: FreeCAD 1.0 원본(부품 형상과 파라미터 시트).
- `CAD/Printed_Assembly.step`, `CAD/Assembly_With_OEM_Reference.step`.
- `STEP_parts/*.step`: 개별 PETG 및 TPU 부품.
- `STL_PRINT/*.stl`: mm, 출력 방향을 적용하고 바닥 Z=0으로 이동한 닫힌 메시.
- `drawings/Ultralight_A3_Manufacturing.pdf`: A3 6장, 조립·전후면·측면·평면·단면·분해·부품 치수·조립 안내.
- `BOM.csv`, `validation_results.json`, `assembly_guide_ko.md`.
- `renders/*.png`: 실제 CAD 메시로 만든 Blender 렌더링. 중립적인 가상 슬랩과 카드 표현이며 실물 PSA 사진이 아닙니다.

출력 대상은 프레임·게이트·TPU 부품입니다. A/B안은 추가 출력 베이스를 제거하고 구매 팝업의 하부 캡을 접착 베이스로 사용합니다. C안만 별도 PETG 베이스가 있습니다. 구매 팝업의 주름부·기구 STL은 제공하지 않습니다. 미선정 상용 원형 팝업 외형의 닫힘6/열림22mm는 참고 가정이며, 이 모형이 실제로 작동하는 것을 검증하지 않았습니다.

```bash
# Debian/Ubuntu 계열, FreeCAD Python 모듈 및 python3-reportlab / Blender 필요
/usr/bin/python3 generate_ultralight.py --skip-render
# 위 명령 뒤 실제 CAD 메시로 렌더링
/usr/bin/blender -b -t 4 --python render_blender.py
# CAD만 빠르게 다시 생성
/usr/bin/python3 generate_ultralight.py --geometry-only --skip-render
```

먼저 이 폴더를 새 작업 폴더로 복사하고 `parameters.json`을 편집하세요. 생성 스크립트는 자신의 A/B/C 출력 폴더를 다시 씁니다. `design_specs.json`은 생성 결과이며 설계안 변경은 스크립트의 SPECS를 수정합니다. FreeCAD의 파라미터 시트는 기록용으로, 시트 값을 바꾸면 형상이 자동 재계산되는 식 연결 모델은 아닙니다. 형상 변경은 Python으로 재생성해야 합니다. 형상 변경 뒤에는 `--geometry-only`로 끝내지 말고 전체 생성 명령을 실행해 도면·BOM·보고서를 갱신하세요. 전체 생성은 마지막에 `verify_exports.py` 파일 재검사를 실행합니다. 렌더링을 생략했다면 별도로 다시 실행해야 이미지도 바뀝니다. 자석은 현재 D3×1.5mm 4개만 지원하며 다른 규격은 게이트와 포켓 형상 재설계가 필요합니다. 프린터가 미정이므로 G-code는 만들지 않았습니다.
'''
(root/'README_ko.md').write_text(intro)
comparison='''# 경량화 비교 및 권장안

모든 무게는 실측이 아닌 CAD 체적×가정 밀도(PETG1.27, TPU1.20g/cm³)와 구매품·소모품 가정의 합입니다. FDM 인필로 내부 중량을 더 줄였다고 계산하지 않았습니다. 팝업8g 기준, 구매품 범위6~12g입니다. 모든 접착 필름과 자석, 자석 에폭시0.12g, 패드·테두리 접착재0.15g을 포함합니다. 도료/추가 스트랩은 채택하지 않았으며 나중에 추가하면 별도 합산해야 합니다.

|안|추가 부품 g|팝업6~12g일 때 g|슬랩50g 포함 g|접힘/열림 두께 mm|30g를 위한 팝업 상한 g|
|---|---:|---:|---:|---:|---:|
'''
for key,v in results.items():
 m=v['mass'];comparison+=f"|{labels[key]}|{m['additional_nominal_g']:.2f}|{m['additional_low_g']:.2f}~{m['additional_high_g']:.2f}|{m['with_slab_nominal_g']:.2f}|{v['folded_accessory_thickness_mm']:.2f}/{v['open_accessory_thickness_mm']:.2f}|{m['max_popup_mass_for_30g_g']:.2f}|\n"
comparison+='''
두께는 폰을 제외한 접착면부터 가장 돌출된 게이트까지입니다. 슬랩까지 포함한 전체 제품 두께이며, 펼쳤을 때는 팝업이16mm 늘어납니다. 프레임 앞면보다 게이트가 더 돌출합니다. B의 본체 일반 구간은23.30mm보다 얇지만 게이트 높이를 숨겨 표시하지 않았습니다.

|항목|A 최소형|B 일상형 후보|C 보호형|
|---|---|---|---|
|벽/일반 뒤 리브 mm|1.5/1.2|1.8/1.5, 뒤 T핀4mm 추가|2.0/1.9|
|구조|2개 수평 리브, 최소 접촉|4개 대각선 T형 리브, 코너 보강|6개 리브, 넓은 림, 추가 접착판|
|교체|공구 없이 게이트 위로 들어 열기|동일|동일, 패드가 길어 마찰 증가 가능|
|취약점|리브 굽힘·층간 취약, 강도 선별 계산에서 부적합 우려|T리브/원형 패드 접합, 손가락 압박, 자석 열림|무겁고 두꺼움, 무게 증가로 접착 박리 부담|
|출력|얇은 리브·옆면 출력으로 어려움|뒤 리브와 접착면 서포트, 어려움|출력량 증가, 서포트 필요|
|폰 유지|가벼워 관성 감소하나 접착 미검증|접착·상용 팝업 성능 확인 필요|질량과 모멘트가 가장 큼|

B를 **일상 휴대용 개발·시험 후보**로 추천합니다. A는20~25g 범위이지만 현재 보강 없는 리브를 실사용 추천하지 않습니다. C는30g 목표를 초과합니다. B도 팝업8g 가정에서30g를 소폭 초과하므로 무조건 목표 달성이라고 하지 않습니다. 위 팝업 상한 이하의 실제 부품을 찾고, 접착재 포함 완성품 실측과 강도 시험을 거쳐야 합니다. 20~25g와 충분한 구조 강도를 동시에 입증한 설계는 아직 없습니다.

벽 전체를 더 얇게 하거나 FDM 내부 인필만 줄이는 방법은 주요 하중 지점의 강도를 해칠 수 있습니다. 넓은 두꺼운 판을 제거하고 외곽 림+선택 리브로 바꾸었으며, B는 판형 리브보다 단면 효율이 좋은 뒤쪽 T리브를 적용했습니다. 폐쇄 중공 구조는 서포트 제거·층간 품질·검사 난이도 때문에 이번 안에 채택하지 않았습니다. 양산 시에는 검증된 얇은 사출 리브 또는 별도 경량 고강성 보강재를 검토할 수 있습니다.
'''
(root/'comparison_ko.md').write_text(comparison)
report='''# 실행 검사·계산 및 실물 시험 계획

## 실제 실행

FreeCAD 1.0/OCC로 A/B/C 형상 생성, 각 제작 파트 단일 닫힌 솔리드 검사, STEP 내보내기/재가져오기, STL 재읽기·닫힘·체적·방향/크기 검사. 팝업 외형 높이6~22mm의17개 자세에서 모든 모델링 부품 쌍의 체적 교차 검사. 게이트 Z방향16샘플 후 Y방향16샘플 이동, 카드 Y방향 삽입16샘플 검사. 양쪽 기계적 어깨가 닫힌 게이트의 Y이동을 막는 교차와 닫힌 게이트의 슬랩 스토퍼가 슬랩 Y이탈을 막는 교차를 별도로 의도된 접촉으로 검사했습니다.

외형 팝업의 내부 운동, 탄성 접촉, 끼임 전 과정을 실제 기구 모델로 검증한 것은 아닙니다. TPU U/상단 테두리는 조립에 포함했지만 네 측면·후면·전면 패드는 자유상태 출력품/무게만 모델링했고 압축·팽창·접착 위치의 전체 공차 해석은 미실행입니다. 패드 자리와 개폐 마찰은 실물 더미로 확인해야 합니다. 샘플 사이의 연속 충돌을 수학적으로 보증하지 않습니다.

'''
for key,v in results.items():
 report+=f"- {key}: 제작 STEP/STL {len(v['printed_checks'])}종 단일 솔리드/닫힘 통과. 팝업 자세 간섭 {len(v['sampled_interferences'])}, 삽입 간섭 {len(v['insertion_interferences'])}, 게이트 간섭 {len(v['gate_open_interferences'])}건. 닫힌 슬랩 이탈 시 스토퍼 교차 {v['closed_gate_payload_escape_block_mm3']:.3f}mm³. 원본 상세값 `validation_results.json`.\n"
report+='''
각 STL은 조립 위치가 아니라 출력 위치입니다. STEP/FCStd로 조립을 확인하세요. 서포트·압출 경로·노즐 통과·뒤틀림은 슬라이서로 아직 검사하지 않았습니다. 단일 솔리드 검사는 출력 강도 합격을 의미하지 않습니다. A/B/C의 A3 PDF는 실제 CAD 투영이며, 숨은 선을 제거하지 않은 전체 윤곽입니다. 치수는 CAD 좌표/경계 상자/설계 입력에서 도출했습니다. 공차는 목표값이며 실측 능력검증값이 아닙니다.

## 무게중심과 하중 경로

프레임을 잡으면 스마트폰224g의 하중이 접착재 → OEM 하부캡 → 구매 팝업 → 상부 접착재 → D42 패드 → 리브 → 외곽 프레임 → 손으로 전달됩니다. 폰을 잡으면 슬랩+액세서리 하중이 반대 방향으로 전달됩니다. 따라서 슬랩만의 무게로 연결부를 평가하지 않았습니다.

5g 과도 하중의 선별 가정에서 무거운 쪽인 폰224g을 적용하면10.987N, 손 위치/하중선이40mm 벗어나면0.4395N·m입니다. 정적 폰 하중2.197N, 같은 레버0.0879N·m입니다. 회전 토크는 평면 레버×전단력, 박리 모멘트는 전단력×면간 높이로 평가해야 합니다. 실제 충격 가속도와 하중 분배는 미측정입니다. 보수적으로 전체 결합체를5g로 가속할 때의 하중은 아래 값입니다.

'''
for key,v in results.items():
 m=v['mass'];model=v['rib_model'];report+=f"- {key}: 폰 포함 {m['with_phone_nominal_g']:.2f}g; 전체5g {m['with_phone_nominal_g']/1000*9.81*5:.2f}N. 단순 리브 등분배 굽힘 지표 {model['equal_share_bending_bound_MPa']:.2f}MPa. 접힘/열림 질량중심(mm, 프레임 원점): `{json.dumps(v['center_of_mass_by_extension'],ensure_ascii=False)}`.\n"
report+='''
질량중심은 CAD 질량합 Σmi·ri/Σmi로 계산했습니다. 팝업 내부 질량분포, 슬랩·폰 실물 중심, 패드 배치는 가정입니다. 좌표Z는 카드 정면 방향이+, 폰은-방향입니다. 실제 위치측정 전에는 이 결과로 거치·회전 안정성을 확정할 수 없습니다.

리브 선별 계산은 M/(리브수×단면계수)이며 FEA가 아닙니다. A/C는 사각 단면, B는4mm 깊이 T핀 중 폭1.0mm만 유효하다고 본 보수적 내부 사각형과 상부플랜지를 합성했습니다. B의 단면계수는 결과 JSON에 기록했습니다. 응력 집중, 중앙 연결부, 불균등 분배, 층간 접착, 충격은 이 식에서 검증되지 않았습니다. 재료 허용응력/피로한도/층간 데이터가 없어 달성 안전율은 미확정입니다. 목표 안전율2를 적용하려면 적어도 선별 응력의2배 이상 허용강도를 동일 출력 방향 쿠폰에서 확인하고, 전체 조립체 시험도 통과해야 합니다. A는 높은 선별 응력 때문에 실사용 후보에서 제외합니다. 핀/나사가 없는 구매 팝업 구조이므로 핀 전단·나사 체결 계산 대상은 없으며 OEM 내부 기구는 공급사 데이터와 시험이 필요합니다.

B의 뒤 T핀4mm는 접힘 시 가정한 카메라 돌출4mm와 CAD상 최소0.5mm의 축방향 간격을 갖습니다(공차 제외). 이 작은 간격은 휴대폰 실측 전 여유 확보로 볼 수 없습니다. 카메라가 크거나 폰 케이스가 다르면 팝업 위치/접힘 높이/프레임 위치를 다시 설계해야 합니다. 프레임은 폰보다 좌우로 돌출합니다.

거치 기능은 이번 설계에서 확정하지 않았습니다. OEM 팝업의 별도 각도 잠금이 없고 지지점·지지영역을 검증하지 않았으므로 거치대로 사용하지 마세요. UV 차단 재료나 별도 커버는 이번 경량안에 추가하지 않았으며 기존 슬랩의 UV 차단 성능도 확인하지 않았습니다. UV 보호가 필요하면 파장별 투과율 자료가 있는 시트의 무게와 고정부를 별도 설계해야 합니다.

## 미실행 시험 및 잠정 합격 기준

모든 시험은 고가 카드/실제 폰 대신 같은 치수·최대 예상 질량의 더미와 낙하 포획 장치로 먼저 시행합니다. 아래 수치는 공급사 규격이 아닌 개발용 잠정 기준입니다. 이 기준 합격도 모든 낙하 안전을 보증하지 않습니다.

|시험|방법|잠정 합격 기준|
|---|---|---|
|치수/질량|캘리퍼와0.01g 저울, 슬랩과 구매 팝업 포함 각 부품 측정|실측값으로 CAD 갱신, B 추가 총무게≤30g 목표, 공차·간섭 재검사|
|카드 교체|더미로500회 삽입/분리, 게이트·패드 점검|긁힘/이탈/균열 없음, 개방력8~15N 잠정, 좌우 흔들림≤0.3mm|
|게이트 유지|닫힌 상태 +Y 슬랩당김20N 60초, +Z 게이트당김8N 60초|슬랩/게이트 이탈 없음, 영구변형≤0.3mm. 실패 시 자석 확대/보조걸쇠 재설계|
|프레임/팝업|프레임 고정 후 폰 더미에 22N 60초, 이후 0.88N·m 굽힘|균열/분리/영구변형≤0.3mm, 5g선별값×안전율2의 개발 시험|
|접힘 피로|선정 OEM 사용 높이로5000회 개폐, 더미224g 동반|이탈·균열·기능 상실 없음, 유격 증가≤0.5mm|
|접착 전단|실제 케이스 소재+제조사 표면처리/경화 후22N 평면하중60초|미끄러짐≤0.5mm, 접착 끝 박리 없음|
|박리/회전|접착부에 0.88N·m 모멘트, 양방향20회/각60초|분리·끝 들뜸 없음, 회전≤2도. 순수 인장값 대체 불가|
|고온 크리프|실제 케이스 더미에 정적224g,50°C 24시간 후 냉각|변형≤0.5mm, 접착·게이트 기능 유지. 차량 내 고온은 미승인|
|낙하|소모 가능한 전체 더미,1m 6방향×각3회, 포획영역 내 실시|카드/폰 이탈·파편 없음, 이후 기능 유지|
|그립/끼임|다양한 손 크기5명, 연속30분, 접힘 동작 반복|통증/긁힘/끼임 없음. 리브/게이트 닿는 위치 수정|

실행하지 않은 검사: 실제 출력, 슬라이서 서포트 검증, 치수 실측, 구매품 선정, 자석 힘, 팝업 내부 기구, 접착·전단·박리·회전, 출력 강도, 피로, 크리프, 낙하, UV, 거치 안정성. 체적 기반 무게 계산으로 강도를 보증하지 않습니다.
'''
if (root/'export_verification.json').exists():
 verified=json.loads((root/'export_verification.json').read_text());report+='\n## 독립 파일 재검사\n\nverify_exports.py를 실제 실행했습니다. 총 '+str(len(verified['checks']))+'개 검사, 실패 '+str(len(verified['failures']))+'개. FCStd 재열기, STEP/STL 재읽기, BOM 질량·수량, 질량중심의 질량합, PDF A3 크기·페이지·주의 문구, V01/기존 원형 V02 미변경을 확인했습니다. 이는 위 CAD/파일 검사만의 결과이며 무게 목표나 실물 안전성 합격을 뜻하지 않습니다. B/C는8g 팝업 가정에서30g 목표 초과입니다. 상세는 export_verification.json.\n'
 (root/'validation_report_ko.md').write_text(report)
for key,v in results.items():
 r=root/key
 guide=f'''# {labels[key]} 조립·출력 안내

예비 시제품용 — 실측 및 시험 전 제작 확정 금지.

1. 실제 슬랩을 측정해 매개변수를 갱신합니다. 현재81×136×6mm는 ASSUMED입니다.
2. PETG 프레임/자석 게이트와 TPU95A 보호 부품을 출력합니다. STL은 mm이고 출력 방향으로 배치되어 있습니다. 프레임은 긴 변을 바닥으로 세운 방향입니다. 0.4mm노즐/0.20mm층/4벽을 초기 조건으로 하되1.5~2mm벽과 얇은 리브의 실제 압출 경로를 슬라이서로 확인하세요. 프레임 리브/디스크/게이트에 서포트가 필요합니다. 접촉면을 손상시키지 않고 제거해야 합니다. 작은 자석 포켓을 먼저 쿠폰 출력하세요.
3. 모서리·접촉부를 다듬고 TPU 패드를 붙입니다. 측면 패드0.8→0.6mm, 후면0.5→0.4mm, 앞면0.4→0.3mm 압축을 가정했습니다. 후면 패드는 좁은 림 지지부만 남도록 블랭크를 다듬고, 전면 패드 폭은 립 폭에 맞춰 잘라야 합니다. 슬랩에는 접착하지 않습니다. 전면 패드 8mm 길이는 Y방향입니다. 측면 패드 중심은 양쪽 벽 Y=±34mm, 후면·전면 패드도 이 부근에서 서로 대응시키되 리브/게이트와 간섭하지 않게 확인합니다.
4. U형 검은 TPU 테두리와 게이트 테두리를0.25mm 홈에 붙입니다. 자유두께0.45mm이므로0.20mm 노출됩니다. 움직이는 경계0.10mm를 접착재로 막지 마세요.
5. D3×1.5mm 자석4개를 서로 당기는 극성으로 매립·봉합합니다. 흘러나온 접착제가 슬랩에 닿으면 안 됩니다. 자석 규격과 힘은 구매 전 가정이며 유지력 합격 전 사용하지 마세요.
6. 상용 원형 팝업을 선정하고 상부 D40/하부 D38, 닫힘6/펼침22mm 및 무게를 측정합니다. 현재는 외형 참고값입니다. 일치하지 않으면 CAD 재생성이 필요합니다. 프레임 D42 원판과 팝업 상부를0.20mm 양면접착재로 결합합니다. OEM 접착/장착 지침을 우선 확인합니다.
7. {'OEM 하부캡을0.80mm 접착재로 폰 케이스에 직접 붙입니다. 추가 출력 베이스는 없습니다.' if v['specs']['base_t']==0 else 'OEM 하부캡→0.20mm 접착재→D46×1.6mm 출력 베이스→0.80mm 접착재→폰 케이스 순서입니다.'} 저표면에너지·실리콘 케이스는 접착재 공급사 적합성 시험이 필요합니다.
8. 게이트를 +Z로 {v['gate_lift_travel_mm']:.2f}mm 이상 들어 어깨에서 빼고 위로 분리합니다. 더미 슬랩을 상단에서 넣은 뒤 게이트를 닫습니다. 게이트의 두 스토퍼가 슬랩 끝을 막는지 확인합니다. 도구 없이 카드 교체가 가능하도록 설계했지만 실물 개방력·마찰은 미검증입니다.
9. 접착재 공급사의 완전 경화 조건 이후 모든 시험을 더미로 시행합니다. 접착식이므로 폰 케이스에서 매번 탈착하는 제품은 아닙니다. 카드는 게이트로 교체하며, 폰 분리는 접착재 제거/교체를 수반합니다.

추가부품 예상무게 {v['mass']['additional_nominal_g']:.2f}g, 슬랩50g 포함 {v['mass']['with_slab_nominal_g']:.2f}g(모두 가정). 상세 BOM과 상위 `validation_report_ko.md`를 확인하세요. 프레임을 손잡이로 잡으므로 연결부는 폰 무게도 지지해야 합니다. 실제 강도·피로·접착·낙하 시험을 하지 않았습니다.
'''
 (r/'assembly_guide_ko.md').write_text(guide)
 (r/'README_ko.md').write_text(f'# {labels[key]}\n\n[비교 및 권장 조건](../comparison_ko.md) / [실행 검사·한계](../validation_report_ko.md) / [조립](assembly_guide_ko.md)\n\nCAD, STEP_parts, STL_PRINT, drawings, BOM.csv와 실행 결과 validation_results.json을 함께 확인하세요. 예비 시제품이며 구매 팝업과 자석은 미선정입니다.\n')
# A3 comparison sheet
c=canvas.Canvas(str(root/'Comparison_A3.pdf'),pagesize=landscape(A3))
c.setFont('Helvetica-Bold',16);c.drawString(14*mm,278*mm,'PSA V02 ULTRALIGHT - RED BUMPER / BLACK TPU')
c.setFont('Helvetica',10)
y=260
for key,v in results.items():
 m=v['mass'];lines=[key,f"Added mass nominal {m['additional_nominal_g']:.2f} g; OEM 6..12g gives {m['additional_low_g']:.2f}..{m['additional_high_g']:.2f} g",f"With 50g slab {m['with_slab_nominal_g']:.2f} g; with phone {m['with_phone_nominal_g']:.2f} g",f"Folded {v['folded_accessory_thickness_mm']:.2f} mm / open {v['open_accessory_thickness_mm']:.2f} mm (phone excluded)",f"30g target requires OEM popup <= {m['max_popup_mass_for_30g_g']:.2f} g; physical validation NOT RUN"]
 for line in lines:c.drawString(15*mm,y*mm,line);y-=7
 y-=8
for line in ['B: daily-use DEVELOPMENT CANDIDATE, not a verified safe product.','A: lighter but insufficient unreinforced rib stiffness/strength concern.','C: protective concept exceeds 30g mass target.','Mass from CAD volume x assumed density plus purchased-part/consumable assumptions.','Actual OEM popup, slab dimensions, adhesive and magnet holding performance UNVERIFIED.','See comparison_ko.md / validation_report_ko.md for tests, margins and limitations.']:
 c.drawString(15*mm,y*mm,line);y-=8
c.setFont('HYSMyeongJo-Medium',12);c.drawString(15*mm,15*mm,'예비 시제품용 — 실측 및 시험 전 제작 확정 금지');c.save()

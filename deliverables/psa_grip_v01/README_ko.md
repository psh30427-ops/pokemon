# PSA 보호케이스 그립 V01

**예비 시제품용 — 실측 및 시험 전 제작 확정 금지.**

보호케이스 자체는 앞뒤 자석식 잠금이다. 이 자석은 스마트폰 부착용 자석과 별개다. 크래들이 기존 케이스를 손상 없이 포획하고, 상단 나사 게이트로 이탈을 막는다. 본체는 크래들/게이트/32mm 링크/베이스의 4개 제작 부품. 상부 핀 잠금, 하부 마찰 힌지. 보호케이스 외형 86×142×11mm만 판매자 표기; 실측 아님.

- drawings/PSA_grip_A3.pdf: A3 7장, 조립/단면/분해/각 부품 치수·좌표·공차.
- assembly.FCStd: 실제 FreeCAD 원본, 부품별 Part::Feature + 파라미터 표. 완전한 스케치 구속 이력 모델은 아님. 표 직접 편집은 형상을 갱신하지 않음.
- assembly.step: 접힌 상태의 제작품 4개. 폰·케이스·자석은 STEP 제작품에서 제외.
- parts/: 제작 부품 개별 STEP와 STL. STL은 mm로 해석.
- states/: 0/60/90도 제작품 조립 STEP.
- renders/: CAD 형상 기반 6종 이미지. 폰/카드케이스는 외형 대용품, 실제 제품 외관이나 카드 인쇄가 아님.
- parameters.csv / design_parameters.json: 값과 가정 상태. 전체 수치는 JSON 및 스크립트 상수로 재생성.
- BOM.csv / assembly_guide_ko.md / validation_report_ko.md / validation_results.json.

## 재생성

현재 검증 환경: Linux, FreeCAD 1.0, 시스템 Python3, reportlab, numpy, matplotlib, Blender(CPU Cycles, denoising off). 외부 모델 다운로드 없음.

```bash
cd /workspace/pokemon/deliverables/psa_grip_v01
QT_QPA_PLATFORM=offscreen MPLCONFIGDIR=/tmp/psa-mpl /usr/bin/python3 generate_model.py
/usr/bin/python3 write_reports.py
```

FreeCAD Python 모듈은 /usr/lib/freecad/lib에서 읽는다. 다른 OS에서는 해당 경로 조정. FreeCAD 설치의 Python ABI와 동일한 인터프리터를 사용할 것. 출력은 같은 디렉터리로 갱신하므로 수정 전 백업. JSON 변경 후 전체 재생성. case_w/h/t, clear_xy, back, arm_length, hole diameters 등 일부 값이 형상과 연결되고, 나머지 세부 위치·포크·베이스·링크 단면은 스크립트의 설계 상수이다. 치수 대폭 변경 후에는 간섭 검사 및 도면 좌표 설명도 함께 수정해야 한다.

## 현재 결과와 한계

4개 부품 솔리드·STEP·STL 검증 통과. 0~90도 5도 간격에서 모델에 포함된 물체의 양의 교차 체적 0건. 실물 작동·강도·UV·자석 성능은 미시험. 구매 자석 모듈과 베이스 체결 구멍이 아직 매칭되지 않았으므로 현재는 안전한 실제 폰 그립 완성품이 아니다. 하부 힌지 잠금과 안전한 손 끼임 방지 가드, 정격 스토퍼는 후속 개선 필요.

기존 케이스에 테이프·구멍을 적용하지 않는다. 라이너 고정용 접착이 필요하면 새 크래들 쪽에만 적용. 기존 카드/케이스에는 접착 금지. 실제 고가 카드 대신 더미로 먼저 조립·시험한다.

"""Companion to generate_model.py; invoked after real geometry creation."""
import math,json,csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A3,landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from FreeCAD import Vector as V
pdfmetrics.registerFont(UnicodeCIDFont('HYSMyeongJo-Medium'))
ROOT=root
warning='예비 시제품용 — 실측 및 시험 전 제작 확정 금지'
# Mesh based actual geometry visualizations, no image-generation approximations.
def render(shapes,path,elev=20,azim=-55,title=''):
 meshdata={}
 for key,shape in shapes.items():
  vv,ff=shape.tessellate(.25);meshdata[key]={'vertices':[[v.x,v.y,v.z] for v in vv],'faces':[list(f) for f in ff],'color':colors.get(key,(.5,.5,.6))}
 path.with_suffix('.mesh.json').write_text(json.dumps(meshdata))
 fig=plt.figure(figsize=(11,9)); ax=fig.add_subplot(111,projection='3d');allpts=[];triangles=[];facecolors=[]
 for k,s in shapes.items():
  vs,fs=s.tessellate(.4);arr=np.array([[v.x,v.y,v.z] for v in vs]);allpts.extend(arr.tolist())
  col=colors.get(k,(.5,.5,.6));triangles.extend([arr[list(f)] for f in fs]);facecolors.extend([col]*len(fs))
 ax.add_collection3d(Poly3DCollection(triangles,facecolors=facecolors,edgecolors=(0,0,0,.03),linewidth=.08))
 pts=np.array(allpts);lo=pts.min(0);hi=pts.max(0);mid=(lo+hi)/2;span=(hi-lo).max()/2*1.07
 ax.set_xlim(mid[0]-span,mid[0]+span);ax.set_ylim(mid[1]-span,mid[1]+span);ax.set_zlim(mid[2]-span,mid[2]+span);ax.set_box_aspect([1,1,1]);ax.view_init(elev,azim);ax.set_xlabel('X mm');ax.set_ylabel('Y mm');ax.set_zlabel('Z mm');ax.set_title(title+'\nPRELIMINARY | Reference phone/case, no card artwork')
 fig.tight_layout();fig.savefig(path,dpi=150);plt.close(fig)
for a,name in [(0,'folded'),(90,'deployed'),(60,'intermediate')]:render(get_state(a),ROOT/'renders'/f'{name}.png',title=f'{name}: hinge {a} deg')
render({k:v for k,v in get_state(90).items() if k not in ['REF_phone','REF_camera','REF_module']},ROOT/'renders'/'case_mounted.png',elev=60,title='Case retained in cradle')
ex={}
for i,(k,s) in enumerate(model_parts.items()):
 sh=s.copy();sh.translate(V((i-1.5)*55,0,-i*35));ex[k]=sh
render(ex,ROOT/'renders'/'exploded.png',elev=25,title='Exploded view / not assembly coordinates')
# Candidate stand orientation: case rear bottom and phone lower front edge at floor.
st=get_state(60);phone=st['REF_phone'].BoundBox;tray=model_parts['01_cradle'].BoundBox
phi=math.degrees(math.atan2(-phone.ZMin,phone.YMin-tray.YMin))
ss={}
for k,s in st.items():
 q=s.copy();q.rotate(V(0,0,0),V(1,0,0),phi);ss[k]=q
zmin=min(q.BoundBox.ZMin for q in ss.values())
for q in ss.values():q.translate(V(0,0,-zmin))
render(ss,ROOT/'renders'/'stand_candidate.png',elev=10,azim=-10,title=f'Stand candidate: 60 deg hinge, global tilt {phi:.1f} deg')
points=[]
for s in ss.values():
 vs,fs=s.tessellate(.2)
 points += [(v.x,v.y) for v in vs if abs(v.z)<.05]
def hull(points):
 pts=sorted(set(points))
 def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
 lower=[];upper=[]
 for q in pts:
  while len(lower)>1 and cross(lower[-2],lower[-1],q)<=0:lower.pop()
  lower.append(q)
 for q in reversed(pts):
  while len(upper)>1 and cross(upper[-2],upper[-1],q)<=0:upper.pop()
  upper.append(q)
 return lower[:-1]+upper[:-1]
h=hull(points);c=result['assembly_mass_COM']['60']['COM_mm'];rad=math.radians(phi);com=[c[0],c[1]*math.cos(rad)-c[2]*math.sin(rad),c[1]*math.sin(rad)+c[2]*math.cos(rad)-zmin]
inside=len(h)>=3 and all((h[(i+1)%len(h)][0]-q[0])*(com[1]-q[1])-(h[(i+1)%len(h)][1]-q[1])*(com[0]-q[0])>=-1e-6 for i,q in enumerate(h))
result['stand_candidate']={'tilt_deg':phi,'support_polygon_xy_mm':h,'COM_mm':com,'projection_inside_polygon':inside,'NOTE':'Rigid reference geometry only; lower hinge friction NOT qualified.'}
# Actual projected boundary edges, orthographic views, dimensioned in mm.
W,H=landscape(A3);c=canvas.Canvas(str(ROOT/'drawings'/'PSA_grip_A3.pdf'),pagesize=(W,H)); c.setTitle('PSA Grip V01 preliminary fabrication drawings')
def txt(x,y,t,size=9):c.setFont('HYSMyeongJo-Medium',size);c.drawString(x,y,str(t))
def page(title,index):
 c.setLineWidth(.7);c.rect(24,24,W-48,H-48);txt(36,H-45,title,16);txt(36,H-64,warning,11);txt(36,36,f'PSA GRIP V01 | {index} | mm | A3 | Do not scale PDF | generated from FreeCAD geometry',9)
 c.line(24,58,W-24,58)
def project(shapes,x,y,axes=(0,1),scale=1.,title=''):
 maximum=max(([v.Point.x,v.Point.y,v.Point.z][axes[1]] for sh in shapes for v in sh.Vertexes),default=0)
 txt(x-90,y+maximum*scale+15,title,10)
 c.setLineWidth(.35)
 for shape in shapes:
  for edge in shape.Edges:
   vs=edge.discretize(Deflection=.2)
   if len(vs)<2:continue
   path=c.beginPath()
   for i,v in enumerate(vs):
    a=[v.x,v.y,v.z];pt=(x+a[axes[0]]*scale,y+a[axes[1]]*scale)
    if i==0:path.moveTo(*pt)
    else:path.lineTo(*pt)
   c.drawPath(path)
def dim(x,y,length,scale=2.,label=None,vertical=False):
 end=(x,y+length*scale) if vertical else (x+length*scale,y)
 c.setLineWidth(.5);c.line(x,y,*end)
 for a,b in [(x,y),end]:
  if vertical:c.line(a-4,b,a+4,b)
  else:c.line(a,b-4,a,b+4)
 txt((x+end[0])/2+4,(y+end[1])/2+4,label or f'{length:.2f}',9)
def notes(lines,x=730,y=690):
 for line in lines:txt(x,y,line,10);y-=19
page('전체 조립도 / 정면·후면·측면·평면',1)
sh=list(model_parts.values())
project(sh,165,400,(0,1),2,'FRONT (+Z), hidden edges included');project(sh,440,400,(0,1),2,'REAR (-Z), same XY datum')
project(sh,710,400,(2,1),2,'SIDE X');project(sh,1000,400,(0,2),2,'TOP Y')
dim(165-47*2,222,94);dim(65,246,154,vertical=True);dim(925,310,42.2,label='42.2 folded incl. module (assumed)')
notes(['Case envelope 86 x 142 x 11 SELLER','Cradle cavity 88 x 144 nominal','Front lip Z = 15.2 to 17.2','Rear plate Z = 0 to 3','Case Z = 3.6 to 14.6','Folded magnet face Z = -25','Reference objects excluded from STEP'],x=790,y=230)
c.showPage()
page('단면도 / 분해도 / 운동 상태',2)
# True geometric section with X=0 plane, represented by thin intersection.
import Part
section=[]
for s in sh:
 q=s.common(Part.makeBox(.02,250,150,V(-.01,-125,-100)))
 if not q.isNull():section.append(q)
project(section,180,430,(2,1),2,'SECTION A-A: X=0, Y/Z')
project(list(ex.values()),650,420,(0,2),1.25,'EXPLODED X/Z (schematic offsets)')
project([v for k,v in get_state(90).items() if not k.startswith('REF')],1020,430,(2,1),1.5,'DEPLOYED 90 deg')
notes(['At 90 deg: case rear to phone back = 57 mm','Folded case front to phone back = 42.2 mm','Gate lifts off before case slides out +Y','No rotation about phone normal in V01','Stand needs lower-hinge friction qualification'],x=470,y=190)
c.showPage()
# Each part full dimension sheet with coordinate hole tables.
details={
'01_cradle':['Material: PETG prototype; no rated strength','Envelope X94 Y154 Z35.7 (hinge included)','Backplate 3; walls 3; bottom wall 5','Cavity X88 Y144; lips overlap cavity 2.5','Gate holes D3.4: (X,Y)=(+/-40,74.5), axis Z','Pivot D4.3: (Y,Z)=(0,-6), axis X','Lock D3.3: (Y,Z)=(8,-6),(4,-12.928),(0,-14)','Cheeks X[-18.5,-10.5],[10.5,18.5]; Y +/-12','Cheeks Z -18.5 to 0; tether 6x3 at Y -76..-73','Side wall ends Y69; open insertion end +Y'],
'02_top_gate':['Material PETG; removable screw gate','Envelope X94 Y7.5 Z14.2','Flange X +/-47, Y72..77, Z3..5','Wall Y72..77, Z5..17.2','Lip Y69.5..77, Z15.2..17.2','2 holes D3.4 at X +/-40 Y74.5, axis Z','Use 2x M3x12 + nuts + broad washers','Gate must capture BOTH magnetic case halves'],
'03_link':['Material PETG prototype; pin-bearing trial part','Envelope X18 Y40 Z8; center distance 32','X +/-9; thickness Z -10..-2','End radii 4 in YZ; centers Y0 and32 Z-6','2x pivot D4.3 axis X','Lock D3.3 axis X at Y8 Z-6','Use retained D3 steel locking pin','No support removal inside hole without gauging'],
'04_base_adapter':['Material PETG; magnetic MODULE NOT DESIGNED','Disc D60 x4; Z -23..-19','Folded disc center (X,Y)=(0,32)','Cheeks X[-18.5,-10.5],[10.5,18.5]','Cheeks Y25..39; Z -19..-1.5','Pivot D4.3 axis X at Y32 Z-6','4x D3.4 axis Z at R21 cardinal points','Centers (X,Y)=(+/-21,32),(0,11),(0,53)','Flat underside Z-23; module proxy D56x2','Do not drill/bond purchased module unapproved']}
for i,(name,s) in enumerate(model_parts.items(),3):
 page(name+' / 부품 치수 및 가공 기준',i)
 project([s],210,430,(0,1),2,'XY datum / front');project([s],510,430,(2,1),2,'ZY side');project([s],210,160,(0,2),2,'XZ top')
 bb=s.BoundBox;dim(210+bb.XMin*2,430+bb.YMin*2-15,bb.XLength);dim(210+bb.XMin*2-15,430+bb.YMin*2,bb.YLength,vertical=True)
 notes(details[name]+['General FDM target +/-0.3 mm; NOT verified','Pin bores: finish to gauge; avoid press fit','Contact edges R0.5 min by finishing','Print orientation / supports: see guide'],x=690,y=680)
 c.showPage()
page('공차 / 소재 / 조립 검사 / 미확정 인터페이스',7)
notes(['좌표 원점: 크래들 후면판 중앙의 Z=0. X 가로, Y 세로, Z 카드 앞면 방향.','판매자 표기 86x142x11: 실측 공차 없음. 모서리 반경과 자석식 개폐 구조 미확인.','XY 한쪽 간극 1.0 = 완충재 압축 후 0.6 + 자유 조립 간극 0.4.','Z: 후면 완충재 0.6 + 케이스 11 + 상부 자유 간극 0.6.','완충재 자유 두께 0.8 -> 압축 0.6: 실제 경도·압축력은 시험으로 결정.','PETG의 일반 치수 목표 +/-0.3. 먼저 쿠폰으로 보정 후 구멍을 게이지 가공.','상단 게이트는 2개 M3 볼트로 잠금. 마찰 스냅이나 보호케이스 자석만으로 하중 지지 금지.','상부 힌지: M4 축 + 별도 D3 잠금핀, 0/60/90도 위치. 하부 힌지: M4 마찰 조임.','하부 힌지 미끄러짐 토크 미검증: 거치대는 더미 시험용. 별도 양방향 각도 잠금이 양산 개선 과제.','상용 자석 모듈: D56x2는 가정 외형. 4개 체결 구멍은 구매품과 아직 매칭되지 않음.','휴대폰 카메라 38x38x4, 위치 X-15/Y+52는 가정. 실제 기기·케이스로 재검증 필요.','별도 UV 커버는 이번 CAD에 없음. 기존 투명창의 UV 차단 성능 확인 필요.','본 도면은 실측 이전 예비 제작 검토용. 실제 카드·스마트폰 사용 전 더미 시험 필수.'],x=60,y=700)
c.showPage();c.save()
(ROOT/'validation_results.json').write_text(json.dumps(result,indent=2))
print('Documents and renders generated. Stand support:',result['stand_candidate'])

import subprocess
subprocess.run(['/usr/bin/blender','-b','-t','4','--python',str(ROOT/'render_blender.py')],check=True,stdout=subprocess.DEVNULL)

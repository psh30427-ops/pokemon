"""Executed by generate_ultralight.py after successful CAD export. A3 mm drawings."""
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A3,landscape
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
import math
import Part
from FreeCAD import Vector as V
pdfmetrics.registerFont(UnicodeCIDFont('HYSMyeongJo-Medium'))
c=canvas.Canvas(str(r/'drawings'/'Ultralight_A3_Manufacturing.pdf'),pagesize=landscape(A3));page=0
W,H=420,297
warning='예비 시제품용 — 실측 및 시험 전 제작 확정 금지'
def text(x,y,s,size=9,ko=False):
 c.setFont('HYSMyeongJo-Medium' if ko else 'Helvetica',size);c.drawString(x*mm,y*mm,str(s))
def line(x,y,x1,y1):c.line(x*mm,y*mm,x1*mm,y1*mm)
def new(title):
 global page
 if page:c.showPage()
 page+=1;c.setLineWidth(.18*mm);c.rect(8*mm,8*mm,404*mm,281*mm);text(12,280,title,14);text(12,272,warning,10,True)
 text(12,12,f"PSA ULTRALIGHT {result['design']} | mm | A3 | {page} | 2026-10-23 | ASSUMED dimensions");text(280,12,'Prototype, not release for production')
def notes(items,x=230,y=240):
 for s in items:text(x,y,s,9);y-=6

def dim(x,y,x1,y1,label):
 line(x,y,x1,y1)
 if abs(y-y1)<.01:
  for q in [x,x1]:line(q,y-1.5,q,y+1.5)
  text((x+x1)/2-7,y+2,label,8)
 else:
  for q in [y,y1]:line(x-1.5,q,x+1.5,q)
  text(x+2,(y+y1)/2,label,8)
def view(shapes,axes,center,scale=1,dimbox=False,title=''):
 pts=[];curves=[]
 for sh in shapes:
  for e in sh.Edges:
   try:vv=e.discretize(Deflection=.15)
   except Exception:vv=e.Vertexes;vv=[v.Point for v in vv]
   a=[(v[axes[0]],v[axes[1]]) for v in vv]
   if len(a)>1:curves.append(a);pts+=a
 lo=[min(q[i] for q in pts) for i in [0,1]];hi=[max(q[i] for q in pts) for i in [0,1]];mid=[(lo[i]+hi[i])/2 for i in [0,1]]
 def point(q):return (center[0]+(q[0]-mid[0])*scale,center[1]+(q[1]-mid[1])*scale)
 c.setStrokeColorRGB(.12,.14,.17);c.setLineWidth(.12*mm)
 for curve in curves:
  path=c.beginPath();x,y=point(curve[0]);path.moveTo(x*mm,y*mm)
  for v in curve[1:]:x,y=point(v);path.lineTo(x*mm,y*mm)
  c.drawPath(path)
 text(center[0]-32,center[1]+(hi[1]-lo[1])*scale/2+7,title,9)
 if dimbox:
  xa,ya=point(lo);xb,yb=point(hi);dim(xa,ya-6,xb,ya-6,f'{hi[0]-lo[0]:.2f}');dim(xb+6,ya,xb+6,yb,f'{hi[1]-lo[1]:.2f}')
 return point
pp=pose(p['popup_closed_h']);new('01 / Assembly orthographic views - folded')
view([pp[k] for k in ['01_Bumper_Frame','02_Magnetic_Gate','TPU_Trim_U','TPU_Gate_Trim']],(0,1),(73,166),1,True,'Front / open window')
view([pp[k] for k in ['01_Bumper_Frame','02_Magnetic_Gate','REF_OEM_Popup_NOT_PRINTABLE']],(0,1),(193,166),1,False,'Rear / reinforcement')
view(list(pp.values()),(2,1),(292,166),.9,True,'Right / with reference phone')
view([pp[k] for k in ['01_Bumper_Frame','02_Magnetic_Gate','REF_OEM_Popup_NOT_PRINTABLE']],(0,2),(351,63),.8,True,'Top')
notes([f'Frame outer width {2*g["ox"]:.2f}; top height {g["headtop"]:.2f}',f'Payload {p["slab_w"]} x {p["slab_h"]} x {p["slab_t"]} ASSUMED',f'Folded accessory {result["folded_accessory_thickness_mm"]:.2f}',f'Opened accessory {result["open_accessory_thickness_mm"]:.2f}','Thickness includes gate; excludes phone.','OEM circular popup reference: not printable.','No official PSA fit / camera certification.'],x=12,y=70)
new('02 / Bumper frame - PETG - quantity 1')
view([parts['01_Bumper_Frame']],(0,1),(91,164),1.12,True,'Front')
view([parts['01_Bumper_Frame']],(2,1),(192,164),1.05,True,'Side')
notes([f'Wall {d["wall"]:.2f}; rear rim {d["back"]:.2f}',f'Front lip {d["lip_w"]:.2f} wide x {d["lip_t"]:.2f} thick',f'Cavity width {2*g["cx"]:.2f}; height {2*g["cy"]:.2f}',f'Central popup bonding disc D42 x {d["pad_t"]:.2f}',f'Ribs {d["rib_w"]:.2f} wide x {d["rib_t"]:.2f} thick',f'Number of ribs {len(g["rib_endpoints"])}',f'Magnet centers X +/-{g["podx"]:.2f}; Y {g["magY"]:.2f}',f'Frame pocket D3.20; floor Z {g["lipz"]+.6:.2f}',f'Frame magnet lower Z {g["lipz"]+.8:.2f}',f'Pocket axial allowance 0.30 mm',f'Black trim groove 0.25 deep; free trim 0.45',f'CAD mass {result["weights"]["01_Bumper_Frame"]["total_mass_g"]:.3f} g at density 1.27','Print on long edge as oriented STL; brim 8 mm.','Support rear ribs / disc and inner ledges.','0.20 layers, 4 walls, 5 top/bottom initially.','Thin ribs: use locally solid toolpaths.','General FDM +/-0.30; fit surfaces +/-0.15.','Tolerance targets require printer coupon.'],x=232,y=245)
if result['design']=='B_daily':notes(['B T-fins: 1.60 wide x 4.00 rearward depth','Start radius 20.50; finish at diagonal frame.','Lower longitudinal edges R0.30.','Print layer direction and coupon must be tested.'],x=232,y=119)
new('03 / Magnetic gate - PETG - quantity 1')
view([parts['02_Magnetic_Gate']],(0,1),(109,181),1.7,True,'Top edge / plan')
view([parts['02_Magnetic_Gate']],(0,2),(109,111),1.7,True,'Front / gate depth')
view([parts['02_Magnetic_Gate']],(1,2),(109,57),2.0,True,'Side')
notes([f'Magnet center X +/-{g["podx"]:.2f}',f'Magnet center Y {g["magY"]:.2f}',f'Gate pocket D3.20, depth 1.80',f'Gate pocket lower Z {g["lipz"]+2.5:.2f}',f'Magnet lower Z {g["lipz"]+2.6:.2f}','Four magnets D3 x 1.5 (two opposed pairs).','Confirm polarity before epoxy encapsulation.','Never rely on magnet pull datasheet alone.','Feet 5 x 4 x 3; clearance 0.30 lateral.','Case stops: X [-28,-22] and [22,28].',f'Stop Y {g["cy"]:.2f} to {g["cy"]+.8:.2f}',f'Stop Z {d["back"]+.4:.2f} to {g["lipz"]:.2f}',f'Lift gate {result["gate_lift_travel_mm"]:.2f} before sliding +Y.','Mechanical shoulders resist +Y removal.','Magnet retention against +Z opening UNVERIFIED.','Keep gate available during every grip test.','No steel locking pins used for card change.'],x=231,y=241)
new('04 / Section A-A, exploded assembly and interface')
# Exact thin slab intersection through center X=0. No generated internal OEM detail.
section=[]
for sh in pp.values():
 q=sh.common(Part.makeBox(.02,220,100,V(-.01,-100,-60)))
 if not q.isNull() and len(q.Edges):section.append(q)
view(section,(2,1),(67,166),1.05,True,'A-A: center X=0; visible section edges')
exploded=[]
for k in ['01_Bumper_Frame','02_Magnetic_Gate','REF_OEM_Popup_NOT_PRINTABLE','REF_Payload']:
 q=pp[k].copy()
 if k=='02_Magnetic_Gate':q.translate(V(0,18,15))
 if k=='REF_OEM_Popup_NOT_PRINTABLE':q.translate(V(0,0,-13))
 if k=='REF_Payload':q.translate(V(0,0,25))
 exploded.append(q)
# Oblique projection generated by rotating the actual CAD geometry.
for sh in exploded:sh.rotate(V(0,0,0),V(1,0,0),25);sh.rotate(V(0,0,0),V(0,1,0),-25)
view(exploded,(0,1),(203,161),1,False,'Exploded: gate / slab / frame / purchased popup')
notes(['Cross-section scale 1.05; orthographic edges.','Payload on 0.40 compressed rear pads.','Front 0.30 compressed pads below retaining lip.','Side nominal gap 0.60 each side.','0.80 side pad free thickness: 25% compression.','Rear 0.50 -> 0.40 (20%).','Front 0.40 -> 0.30 (25%).','Do not confuse FDM clearance and compression.','Popup upper film 0.20; phone film 0.80.',f'Upper contact D40; lower contact D38 ASSUMED.', 'A/B: no extra printed phone base.','C: printed D46 x1.60 plate + lower film 0.20.','Use certified OEM popup with suitable bonding face.','OEM dimensions require purchase & remeasure.','No print-in-place bellows is supplied.'],x=278,y=243)
new('05 / TPU items and optional phone base')
for n,(name,sh) in enumerate(pads.items()):
 if n<3:view([sh],(0,1),(45+n*70,207),3,True,name)
 elif n==3:view([sh],(0,1),(70,102),.73,True,name)
 else:view([sh],(0,1),(182,137),1.05,True,name)
notes(['04: free 0.80 x pad length x slab thickness; qty4.','05: rear blank 8 x4 x0.50; qty4.','06: front blank 8 x2 x0.40; qty4.','07: U inner trim 1.00 wide x0.45 thick; qty1.','08: top trim 1.00 wide x0.45 thick; qty1.','Trim moving joint gap 0.10 (CAD).','TPU 95A starting point; softer silicone alternative.','Adhere pads to FRAME only, not slab.','Keep pads clear of gate feet and magnets.','Fit pad blank overhangs to seats using dummy.','Front lip only 1.4..1.8 wide: trim pad width.','Never force an unmeasured slab into this frame.','TPU CAD mass uses full blanks before trimming.','Pad/trim adhesive 0.15g ASSUMED, counted.','Magnet epoxy 0.12g ASSUMED, counted.','Weigh all actual adhesive after assembly.'],x=231,y=238)
# Important: separate pad adhesive is omitted; mark explicit instead of inventing exact mass.
if '03_Adhesive_Base' in parts:view([parts['03_Adhesive_Base']],(0,1),(187,66),.9,True,'03 PETG base: D46 x1.6 / qty1')
new('06 / Assembly and prototype acceptance sequence')
items=[
 '1. Measure slab width/height/max thickness/radii/mass; edit parameters.json.',
 '2. Print PETG fit coupon before main parts; confirm magnet pocket with dummy magnet.',
 '3. Deburr all slab contact edges; retain minimum section and corner protection.',
 '4. Attach TPU side pads at Y +/- slab_height/4 on both inner side walls.',
 '   Side pad free 0.80 compresses to 0.60. Rear pads go on rear rim; front on underside of lip.',
 '   Rear pad blanks can overhang the narrow rim: trim unsupported portion and verify seating.',
 '5. Install four D3 x1.5 magnets, correct opposed polarity; encapsulate without proud adhesive.',
 '6. Bond black U trim and gate trim in 0.25-deep grooves; maintain 0.10 gap at gate.',
 '7. Bond selected OEM popup upper cap to integral D42 disc; qualify PETG surface adhesion.',
 '8. A/B: OEM lower cap bonds directly to PHONE CASE with supplier-compatible 0.80 film.',
 '   C: bond lower cap to printed plate with 0.20 film, then plate to phone case with 0.80 film.',
 '9. Fully cure supplier adhesive on test substrates. Adhesion to bare phone is not specified.',
 '10. Lift gate clear, insert same-size same-mass dummy through +Y opening; close gate.',
 '11. Open gate only after disconnecting phone/dummy load. Never pinch fingers at popup.',
 '12. First measure total added mass including all actual adhesive, magnets, pads and OEM.',
 '13. Retention / creep / fatigue / peel tests must pass BEFORE valuable slab or actual phone.',
 '14. Gate shoulder and two slab stops are required; magnetic holding force is unverified.',
 '15. Printed geometry passed CAD checks only; no physical strength or endurance claim.',
 '16. Stand function is not locked or qualified in this OEM-envelope design; do not use as stand.',
 ]
notes(items,x=17,y=249)
c.save()

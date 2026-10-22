"""Blender background CPU rendering of actual FreeCAD tessellations."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent
for path in sorted((R/'renders').glob('*.mesh.json')):
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 data=json.loads(path.read_text());objects=[]
 for k,d in data.items():
  mesh=bpy.data.meshes.new(k);mesh.from_pydata([[v[0]/1000,-v[2]/1000,v[1]/1000] for v in d['vertices']],[],d['faces']);mesh.update();ob=bpy.data.objects.new(k,mesh);bpy.context.collection.objects.link(ob);objects.append(ob)
  mat=bpy.data.materials.new(k);mat.diffuse_color=(*d['color'],1);mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*d['color'],1);bs.inputs['Roughness'].default_value=.42;ob.data.materials.append(mat)
 pts=[Vector((v[0],-v[2],v[1]))/1000 for d in data.values() for v in d['vertices']];low=Vector([min(p[i] for p in pts) for i in range(3)]);high=Vector([max(p[i] for p in pts) for i in range(3)]);center=(low+high)/2;size=max(high-low)
 bpy.ops.object.camera_add();cam=bpy.context.object;cam.location=center+Vector((1,1.6,1.0) if path.stem.startswith('rear') else (1,-1.6,1.0)).normalized()*size*3
 cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=size*1.65;bpy.context.scene.camera=cam
 for delta,power in [((1,-1,2),1600),((-1,1,1),1100)]:
  bpy.ops.object.light_add(type='AREA',location=center+Vector(delta)*size);ob=bpy.context.object;ob.data.energy=power*size**2*.01;ob.data.shape='DISK';ob.data.size=size*1.5;ob.rotation_euler=(center-ob.location).to_track_quat('-Z','Y').to_euler()
 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=32;scene.cycles.use_denoising=False
 scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.8,.8,.8,1);scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.4;scene.render.resolution_x=1100;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
 scene.render.image_settings.file_format='PNG';scene.render.filepath=str(path).replace('.mesh.json','.png');scene.render.film_transparent=False
 scene.view_settings.view_transform='AgX';scene.view_settings.look='Medium High Contrast' if 'Medium High Contrast' in [x.name for x in []] else 'None'
 bpy.ops.render.render(write_still=True)

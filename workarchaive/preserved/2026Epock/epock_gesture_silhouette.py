"""Epock: paired front/side gesture and silhouette renders, Blender 4.x.
Select an Armature, open Scripting > Text Editor > Run Script.
All temporary scene changes are restored. Requires a rigged body mesh.
"""
import bpy, os, json
from mathutils import Vector

CFG = dict(output='//Epock_TraceTool', resolution=1024,
           front=(0,-1,0), side=(1,0,0),
           render_active_silhouette=True, line_radius=0.0025)
BONES = {
 'head':['head'], 'neck':['neck'], 'chest':['chest','upperchest','spine2','spine.002'],
 'spine':['spine1','spine.001','spine'], 'hips':['hips','pelvis'],
 'ls':['leftshoulder','shoulder.l','clavicle.l'], 'rs':['rightshoulder','shoulder.r','clavicle.r'],
 'le':['leftforearm','forearm.l','lowerarm.l'], 're':['rightforearm','forearm.r','lowerarm.r'],
 'lw':['lefthand','hand.l'], 'rw':['righthand','hand.r'],
 'lk':['leftleg','shin.l','calf.l'], 'rk':['rightleg','shin.r','calf.r'],
 'la':['leftfoot','foot.l'], 'ra':['rightfoot','foot.r'],
 'lt':['leftupleg','thigh.l'], 'rt':['rightupleg','thigh.r']}
EDGES = [('head','neck'),('neck','chest'),('chest','spine'),('spine','hips'),
 ('chest','ls'),('chest','rs'),('ls','le'),('le','lw'),('rs','re'),('re','rw'),
 ('hips','lt'),('lt','lk'),('lk','la'),('hips','rt'),('rt','rk'),('rk','ra')]

def norm(n): return n.lower().replace('mixamorig:','').replace('_','').replace('-','').replace(' ','')
def locate(arm,key):
 for alias in BONES[key]:
  for b in arm.pose.bones:
   if norm(b.name)==norm(alias): return arm.matrix_world@b.head
 return None

def emission(name,rgb):
 m=bpy.data.materials.new(name); m.use_nodes=True
 nd=m.node_tree.nodes; nd.clear(); out=nd.new('ShaderNodeOutputMaterial'); e=nd.new('ShaderNodeEmission')
 e.inputs['Color'].default_value=(*rgb,1); m.node_tree.links.new(e.outputs[0],out.inputs['Surface'])
 return m

def make_segment(coll,a,b,width,mat):
 delta=b-a
 if delta.length<1e-5:return
 cu=bpy.data.curves.new('EPOCK_line','CURVE');cu.dimensions='3D';cu.bevel_depth=width;cu.bevel_resolution=2
 sp=cu.splines.new('POLY');sp.points.add(1);sp.points[0].co=(*a,1);sp.points[1].co=(*b,1)
 ob=bpy.data.objects.new('EPOCK_line',cu);coll.objects.link(ob);cu.materials.append(mat)

def make_camera(coll,name,center,scale,direction):
 data=bpy.data.cameras.new(name);ob=bpy.data.objects.new(name,data);coll.objects.link(ob)
 ob.location=center+Vector(direction).normalized()*scale*2
 ob.rotation_euler=(center-ob.location).to_track_quat('-Z','Y').to_euler()
 data.type='ORTHO';data.ortho_scale=scale*1.35
 return ob

def body_mesh(o,arm):
 return o.type=='MESH' and (o.find_armature()==arm or o.parent==arm or
   any(m.type=='ARMATURE' and m.object==arm for m in o.modifiers))

def main():
 sc=bpy.context.scene;arm=bpy.context.active_object
 if arm is None or arm.type!='ARMATURE':raise RuntimeError('Select the character Armature first.')
 pts=[arm.matrix_world@b.head for b in arm.pose.bones]+[arm.matrix_world@b.tail for b in arm.pose.bones]
 center=sum(pts,Vector())/len(pts);span=max(max(p.z for p in pts)-min(p.z for p in pts),0.1)
 bodies=[o for o in sc.objects if body_mesh(o,arm)]
 if not bodies:raise RuntimeError('No mesh bound to the selected Armature. Check Armature modifiers.')
 original=dict(camera=sc.camera,engine=sc.render.engine,path=sc.render.filepath,
  world=sc.world,transparent=sc.render.film_transparent,
  res=(sc.render.resolution_x,sc.render.resolution_y,sc.render.resolution_percentage),
  format=sc.render.image_settings.file_format,view=sc.view_settings.view_transform)
 hidden={o:o.hide_render for o in sc.objects}
 mats={o:list(o.data.materials) for o in bodies}
 tmp=bpy.data.collections.new('_EPOCK_TEMP');sc.collection.children.link(tmp)
 black=emission('_EPOCK_BLACK',(0,0,0));world=bpy.data.worlds.new('_EPOCK_WORLD');world.use_nodes=True
 world.node_tree.nodes['Background'].inputs['Color'].default_value=(1,1,1,1)
 out=bpy.path.abspath(CFG['output']);os.makedirs(out,exist_ok=True)
 meta=dict(armature=arm.name,pose_bones={},outputs=[])
 try:
  sc.render.engine='BLENDER_EEVEE_NEXT';sc.world=world;sc.render.film_transparent=False
  sc.render.resolution_x=sc.render.resolution_y=CFG['resolution'];sc.render.resolution_percentage=100
  sc.render.image_settings.file_format='PNG';sc.view_settings.view_transform='Standard'
  cams={'front':make_camera(tmp,'EPOCK_FRONT',center,span,CFG['front']),
        'side':make_camera(tmp,'EPOCK_SIDE',center,span,CFG['side'])}
  for key in BONES:
   p=locate(arm,key);meta['pose_bones'][key]=list(p) if p is not None else None
  gesture=[]
  for a,b in EDGES:
   pa,pb=locate(arm,a),locate(arm,b)
   if pa is not None and pb is not None:
    before=set(tmp.objects);make_segment(tmp,pa,pb,span*CFG['line_radius'],black)
    gesture.extend([o for o in tmp.objects if o not in before])
  # Render line gesture only, from the same fixed front/side cameras.
  for obj in list(sc.objects):obj.hide_render=True
  for obj in gesture:obj.hide_render=False
  for view,cam in cams.items():
   sc.camera=cam;path=os.path.join(out,'gesture_'+view+'.png');sc.render.filepath=path
   bpy.ops.render.render(write_still=True);meta['outputs'].append(path)
  # Render actual posed mesh in solid black (no outlines, shadows or textures).
  for obj in gesture:obj.hide_render=True
  for obj in bodies:
   obj.hide_render=False;obj.data.materials.clear();obj.data.materials.append(black)
  for view,cam in cams.items():
   sc.camera=cam;path=os.path.join(out,'silhouette_'+view+'.png');sc.render.filepath=path
   bpy.ops.render.render(write_still=True);meta['outputs'].append(path)
  if CFG['render_active_silhouette'] and original['camera']:
   sc.camera=original['camera'];path=os.path.join(out,'silhouette_scene_camera.png')
   sc.render.filepath=path;bpy.ops.render.render(write_still=True);meta['outputs'].append(path)
  with open(os.path.join(out,'pose_metadata.json'),'w',encoding='utf-8') as f:json.dump(meta,f,ensure_ascii=False,indent=2)
  print('Epock generated:',meta['outputs'])
 finally:
  for obj,old in mats.items():
   obj.data.materials.clear()
   for mat in old:obj.data.materials.append(mat)
  for obj,val in hidden.items():
   if obj.name in bpy.data.objects:obj.hide_render=val
  sc.camera=original['camera'];sc.render.engine=original['engine'];sc.render.filepath=original['path']
  sc.world=original['world'];sc.render.film_transparent=original['transparent']
  sc.render.resolution_x,sc.render.resolution_y,sc.render.resolution_percentage=original['res']
  sc.render.image_settings.file_format=original['format'];sc.view_settings.view_transform=original['view']
  for obj in list(tmp.objects):bpy.data.objects.remove(obj,do_unlink=True)
  bpy.data.collections.remove(tmp);bpy.data.materials.remove(black);bpy.data.worlds.remove(world)

if __name__=='__main__':main()

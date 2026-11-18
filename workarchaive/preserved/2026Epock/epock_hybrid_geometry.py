"""Epock hybrid mannequin. Blender 4.x+. Run in Scripting with Armature selected.
Creates box torso/pelvis, cylinder limbs, ball joints, oval head and guide lines.
All generated meshes use rigid vertex weights on the ORIGINAL armature.
"""
import bpy, math, re
from mathutils import Vector

CONFIG = {
 'armature_name':'', 'collection':'EPOCK_HYBRID', 'replace':True,
 'hide_original':False, 'guides':True, 'joints':True,
 'height_radius_ratio':0.067, 'guide_thickness_ratio':0.0007,
 'setup_render':False, 'resolution':1024,
}
# Override any unusual bone names here, e.g. {'hips':'PelvisCustom'}
OVERRIDE = {}
ALIASES = {
 'head':['Head','DEF-head'], 'neck':['Neck','DEF-neck'],
 'chest':['Chest','UpperChest','Spine2','Spine3','DEF-spine.003'],
 'spine':['Spine','Spine1','DEF-spine','DEF-spine.001'],
 'hips':['Hips','Pelvis','DEF-pelvis'],
 'upper_arm.L':['LeftArm','LeftUpperArm','upper_arm.L','DEF-upper_arm.L'],
 'upper_arm.R':['RightArm','RightUpperArm','upper_arm.R','DEF-upper_arm.R'],
 'forearm.L':['LeftForeArm','LeftLowerArm','forearm.L','DEF-forearm.L'],
 'forearm.R':['RightForeArm','RightLowerArm','forearm.R','DEF-forearm.R'],
 'hand.L':['LeftHand','hand.L','DEF-hand.L'],
 'hand.R':['RightHand','hand.R','DEF-hand.R'],
 'thigh.L':['LeftUpLeg','LeftUpperLeg','thigh.L','DEF-thigh.L'],
 'thigh.R':['RightUpLeg','RightUpperLeg','thigh.R','DEF-thigh.R'],
 'shin.L':['LeftLeg','LeftLowerLeg','shin.L','DEF-shin.L'],
 'shin.R':['RightLeg','RightLowerLeg','shin.R','DEF-shin.R'],
 'foot.L':['LeftFoot','foot.L','DEF-foot.L'],
 'foot.R':['RightFoot','foot.R','DEF-foot.R'],
}
def normal(s): return re.sub('[^a-z0-9]','',s.lower())
def find_rig():
    if CONFIG['armature_name']:
        o=bpy.data.objects.get(CONFIG['armature_name'])
        if not o or o.type!='ARMATURE': raise RuntimeError('Invalid armature name')
        return o
    o=bpy.context.active_object
    if o and o.type=='ARMATURE': return o
    if o and o.find_armature(): return o.find_armature()
    return next((x for x in bpy.context.scene.objects if x.type=='ARMATURE'),None)
def material(name,color):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color=(*color,1); m.use_nodes=True
    nodes=m.node_tree.nodes; nodes.clear()
    e=nodes.new('ShaderNodeEmission'); e.inputs['Color'].default_value=(*color,1)
    out=nodes.new('ShaderNodeOutputMaterial')
    m.node_tree.links.new(e.outputs[0],out.inputs['Surface'])
    return m
def mesh_obj(name,verts,faces,bone,rig,col,mat):
    me=bpy.data.meshes.new(name+'_Mesh'); me.from_pydata(verts,[],faces); me.update()
    ob=bpy.data.objects.new(name,me); col.objects.link(ob)
    ob.matrix_world=rig.matrix_world.copy(); me.materials.append(mat)
    vg=ob.vertex_groups.new(name=bone); vg.add(list(range(len(verts))),1.0,'REPLACE')
    mod=ob.modifiers.new('EPOCK_Rig','ARMATURE'); mod.object=rig
    mod.use_bone_envelopes=False; mod.use_vertex_groups=True
    return ob
def frame(b):
    h=b.head_local.copy(); d=b.tail_local-h; length=max(d.length,1e-5)
    z=d.normalized(); ref=Vector((0,0,1)) if abs(z.z)<0.9 else Vector((1,0,0))
    x=ref.cross(z).normalized(); y=z.cross(x).normalized()
    return h,x,y,z,length
def p(f,x,y,z): return tuple(f[0]+f[1]*x+f[2]*y+f[3]*z)
def box(f,w,d):
    L=f[4]; v=[p(f,sx*w/2,sy*d/2,z) for z in (0,L) for sy in (-1,1) for sx in (-1,1)]
    return v,[(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5)]
def cylinder(f,r0,r1,sides=12):
    L=f[4]; v=[]
    for z,r in ((0,r0),(L,r1)):
        for i in range(sides):
            a=2*math.pi*i/sides; v.append(p(f,r*math.cos(a),r*math.sin(a),z))
    faces=[tuple(reversed(range(sides))),tuple(range(sides,2*sides))]
    faces += [(i,(i+1)%sides,(i+1)%sides+sides,i+sides) for i in range(sides)]
    return v,faces
def ball(f,z,r,elong=1):
    sides=12; rings=8; v=[]
    for j in range(rings+1):
        a=math.pi*j/rings
        for i in range(sides):
            b=2*math.pi*i/sides
            v.append(p(f,r*math.sin(a)*math.cos(b),r*math.sin(a)*math.sin(b),z+r*elong*math.cos(a)))
    faces=[(j*sides+i,j*sides+(i+1)%sides,(j+1)*sides+(i+1)%sides,(j+1)*sides+i)
           for j in range(rings) for i in range(sides)]
    return v,faces
def line(f,coords,r):
    # thin 4-sided prism between two points, with rigid bone weighting
    a,b=[Vector(x) for x in coords]; d=(b-a).normalized()
    ref=Vector((0,1,0)) if abs(d.y)<0.9 else Vector((1,0,0))
    u=d.cross(ref).normalized()*r; v=d.cross(u).normalized()*r
    vv=[p(f,*(pt+offset)) for pt in (a,b) for offset in (u,v,-u,-v)]
    return vv,[(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
def main():
    rig=find_rig()
    if not rig: raise RuntimeError('No Armature found. Select your rig first.')
    if rig.mode!='OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    existing=bpy.data.collections.get(CONFIG['collection'])
    if existing and CONFIG['replace']:
        for ob in list(existing.objects): bpy.data.objects.remove(ob,do_unlink=True)
        bpy.data.collections.remove(existing)
    col=bpy.data.collections.new(CONFIG['collection']); bpy.context.scene.collection.children.link(col)
    bones=rig.data.bones
    mapping={}
    for role,names in ALIASES.items():
        if role in OVERRIDE: names=[OVERRIDE[role]]
        match=next((b.name for name in names for b in bones if b.name==name),None)
        if not match:
            match=next((b.name for name in names for b in bones if normal(b.name)==normal(name)),None)
        if match: mapping[role]=match
    pts=[p for b in bones for p in (b.head_local,b.tail_local)]
    H=max(max(x.z for x in pts)-min(x.z for x in pts),0.1)
    R=H*CONFIG['height_radius_ratio']
    body=material('EPOCK_White',(1,1,1)); guide=material('EPOCK_GuideGray',(0.63,0.63,0.63))
    for role,bname in mapping.items():
        f=frame(bones[bname]); L=f[4]
        if role in ('chest','spine'): v,faces=box(f,R*3.6,R*2.2)
        elif role=='hips': v,faces=box(f,R*3.1,R*2.4)
        elif role=='head': v,faces=ball(f,L*.5,max(R*1.1,L*.53),1.20)
        elif role=='neck': v,faces=cylinder(f,R*.45,R*.45)
        elif role.startswith('upper_arm'): v,faces=cylinder(f,R*.62,R*.52)
        elif role.startswith('forearm'): v,faces=cylinder(f,R*.52,R*.38)
        elif role.startswith('thigh'): v,faces=cylinder(f,R*.92,R*.72)
        elif role.startswith('shin'): v,faces=cylinder(f,R*.67,R*.43)
        elif role.startswith('hand'): v,faces=box(f,R*.9,R*.35)
        elif role.startswith('foot'): v,faces=box(f,R*.95,R*.55)
        else: continue
        mesh_obj('EPOCK_'+role,v,faces,bname,rig,col,body)
        if CONFIG['joints'] and role not in ('head','chest','spine','hips'):
            v,faces=ball(f,0,min(R*.56,L*.26))
            mesh_obj('EPOCK_JOINT_'+role,v,faces,bname,rig,col,body)
        if CONFIG['guides']:
            paths=[((0,0,L*.06),(0,0,L*.94))]
            if role!='head':
                width=R*(1.7 if role in ('chest','spine','hips') else .70)
                paths += [((-width,0,L*t),(width,0,L*t)) for t in (.30,.70)]
            else: paths += [((-R,0,L*.5),(R,0,L*.5))]
            for i,path in enumerate(paths):
                v,faces=line(f,path,H*CONFIG['guide_thickness_ratio'])
                mesh_obj('EPOCK_GUIDE_'+role+'_'+str(i),v,faces,bname,rig,col,guide)
    if CONFIG['hide_original']:
        for o in bpy.context.scene.objects:
            if o.type=='MESH' and o not in col.objects:
                if o.find_armature()==rig:
                    o.hide_render=True; o.hide_set(True)
    if CONFIG['setup_render']:
        scene=bpy.context.scene
        scene.render.engine='BLENDER_EEVEE_NEXT'
        scene.render.resolution_x=CONFIG['resolution']
        scene.render.resolution_y=CONFIG['resolution']
        scene.render.resolution_percentage=100
        scene.world.color=(1,1,1)
        scene.render.film_transparent=False
        # Freestyle API may vary with Blender versions; enable manually if needed.
        try:
            scene.render.use_freestyle=True
            layer=bpy.context.view_layer
            layer.freestyle_settings.linesets[0].linestyle.color=(.08,.08,.08)
            layer.freestyle_settings.linesets[0].linestyle.thickness=1.3
        except (AttributeError,IndexError):
            print('EPOCK: Freestyle not available; enable outlines manually.')
    print('EPOCK generated:',len(col.objects),'objects; mapped',len(mapping),'bones')
    print('EPOCK missing roles:',sorted(set(ALIASES)-set(mapping)))
    return col

if __name__=='__main__': main()

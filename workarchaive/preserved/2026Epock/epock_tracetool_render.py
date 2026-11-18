"""Epock TraceTool dataset renderer — Blender 4.x, run in Scripting or background.
Set CONFIG below. Existing .blend scene is used; no pose or camera is modified.
"""
import bpy, math, json, re
from pathlib import Path
from mathutils import Vector

CONFIG = {
    'output_dir': '//Epock_TraceTool',
    'styles': ['outline', 'construction', 'pastel'],
    'resolution': (1024, 1024),
    'transparent': False,
    'samples': 32,
    'line_thickness': 1.35,
    'render_all_cameras': False,
    'hide_clothing': True,
    'clothing_keywords': ['shirt','pants','dress','skirt','shoe','sock','jacket','coat','hoodie','hat','hair','eyelash','eyebrow','cloth','garment','accessory','belt','glasses','의상','옷','신발','머리카락'],
    'body_keywords': ['body','skin','head','face','hand','foot','arm','leg','torso','mesh','인체','몸','얼굴'],
    'exclude_keywords': ['rig','armature','camera','light'],
    'add_head_guides': False,  # optional guide curves; see note below
    'orthographic': False,     # switches active cameras to orthographic; off by default
    'ortho_scale': 5.0,
    'save_metadata': True,
}

scene = bpy.context.scene
out = Path(bpy.path.abspath(CONFIG['output_dir']))
out.mkdir(parents=True, exist_ok=True)

# Snapshot mutable scene state so running this script does not permanently restyle the .blend.
original = {
    'engine': scene.render.engine,
    'filepath': scene.render.filepath,
    'film_transparent': scene.render.film_transparent,
    'res_x': scene.render.resolution_x,
    'res_y': scene.render.resolution_y,
    'res_pct': scene.render.resolution_percentage,
    'camera': scene.camera,
    'world': scene.world,
    'view_transform': scene.view_settings.view_transform,
}
old_hide = {o.name: o.hide_render for o in bpy.data.objects}
old_materials = {}
old_camera_types = {}
created_materials = []
created_world = None


def material(name, color):
    mat = bpy.data.materials.new(name)
    created_materials.append(mat)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    output = nt.nodes.new('ShaderNodeOutputMaterial')
    emission = nt.nodes.new('ShaderNodeEmission')
    emission.inputs['Color'].default_value = (*color, 1.0)
    emission.inputs['Strength'].default_value = 1.0
    nt.links.new(emission.outputs[0], output.inputs['Surface'])
    return mat


def is_clothing(obj):
    name = obj.name.lower()
    if any(k in name for k in CONFIG['body_keywords']):
        return False
    return any(k in name for k in CONFIG['clothing_keywords'])


def subject_id(obj):
    """Try grouping meshes by armature; fallback to mesh object identity."""
    for m in obj.modifiers:
        if m.type == 'ARMATURE' and m.object:
            return m.object.name
    parent = obj.parent
    while parent:
        if parent.type == 'ARMATURE':
            return parent.name
        parent = parent.parent
    return obj.name


def set_world_white():
    global created_world
    created_world = bpy.data.worlds.new('EPOCK_TEMP_WHITE_WORLD')
    created_world.use_nodes = True
    bg = created_world.node_tree.nodes.get('Background')
    if bg:
        bg.inputs['Color'].default_value = (1, 1, 1, 1)
        bg.inputs['Strength'].default_value = 1
    scene.world = created_world


def setup_freestyle():
    # Freestyle is available in Cycles on supported Blender builds.
    if not hasattr(scene.render, 'use_freestyle'):
        raise RuntimeError('This Blender build does not expose Freestyle. Use a Blender version/build with Freestyle support.')
    scene.render.use_freestyle = True
    for vl in scene.view_layers:
        if not hasattr(vl, 'freestyle_settings'):
            continue
        fs = vl.freestyle_settings
        fs.mode = 'EDITOR'
        if not fs.linesets:
            fs.linesets.new('EPOCK_Contours')
        for ls in fs.linesets:
            ls.show_render = (ls == fs.linesets[0])
        ls = fs.linesets[0]
        ls.name = 'EPOCK_Contours'
        ls.select_silhouette = True
        ls.select_border = True
        ls.select_contour = True
        ls.select_crease = False
        ls.select_edge_mark = False
        ls.select_suggestive_contour = False
        ls.select_material_boundary = False
        ls.linestyle.color = (0.18, 0.19, 0.26)
        ls.linestyle.thickness = CONFIG['line_thickness']
        ls.linestyle.alpha = 0.95
        ls.linestyle.use_nodes = False


def assign_material(obj, mat):
    if obj.name not in old_materials:
        old_materials[obj.name] = [m for m in obj.data.materials]
    obj.data.materials.clear()
    obj.data.materials.append(mat)


def render_style(style, camera, meshes, group_ids):
    pastel = [(0.92, 0.81, 0.85), (0.76, 0.89, 0.91), (0.86, 0.84, 0.96), (0.88, 0.91, 0.77)]
    neutral = material('EPOCK_TEMP_NEUTRAL', (0.98, 0.98, 0.98))
    colors = [material('EPOCK_TEMP_PASTEL_%d' % i, c) for i, c in enumerate(pastel)]
    for obj in meshes:
        idx = group_ids.index(subject_id(obj))
        assign_material(obj, colors[idx % len(colors)] if style == 'pastel' else neutral)
    for vl in scene.view_layers:
        if hasattr(vl, 'freestyle_settings') and vl.freestyle_settings.linesets:
            ls = vl.freestyle_settings.linesets[0]
            ls.linestyle.color = (0.20, 0.22, 0.32) if style == 'pastel' else (0.16, 0.17, 0.22)
            ls.linestyle.thickness = CONFIG['line_thickness'] * (0.9 if style == 'construction' else 1.0)
    # Construction mode intentionally retains the same silhouette; optional
    # anatomical guides require a separate rig-aware overlay implementation.
    target = out / style
    target.mkdir(parents=True, exist_ok=True)
    filename = re.sub(r'[^a-zA-Z0-9_.-]+', '_', camera.name)
    scene.render.filepath = str(target / (filename + '.png'))
    bpy.ops.render.render(write_still=True)
    print('[Epock]', style, camera.name, scene.render.filepath)


try:
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = CONFIG['samples']
    scene.render.resolution_x, scene.render.resolution_y = CONFIG['resolution']
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA' if CONFIG['transparent'] else 'RGB'
    scene.render.film_transparent = CONFIG['transparent']
    scene.view_settings.view_transform = 'Standard'
    set_world_white()
    setup_freestyle()
    if CONFIG['hide_clothing']:
        for obj in bpy.data.objects:
            if obj.type == 'MESH' and is_clothing(obj):
                obj.hide_render = True
    meshes = [o for o in bpy.data.objects if o.type == 'MESH' and not o.hide_render]
    if not meshes:
        raise RuntimeError('No visible mesh found. Check object visibility and clothing keywords.')
    ids = sorted(set(subject_id(o) for o in meshes))
    cameras = ([o for o in bpy.data.objects if o.type == 'CAMERA'] if CONFIG['render_all_cameras']
               else ([scene.camera] if scene.camera else []))
    if not cameras:
        raise RuntimeError('No active camera. Set scene camera in Blender first.')
    for cam in cameras:
        scene.camera = cam
        if CONFIG['orthographic']:
            old_camera_types[cam.name] = (cam.data.type, cam.data.ortho_scale)
            cam.data.type = 'ORTHO'
            cam.data.ortho_scale = CONFIG['ortho_scale']
        for style in CONFIG['styles']:
            render_style(style, cam, meshes, ids)
    if CONFIG['save_metadata']:
        metadata = {
            'scene': bpy.data.filepath, 'cameras': [c.name for c in cameras],
            'subjects': ids, 'styles': CONFIG['styles'],
            'resolution': CONFIG['resolution'],
            'notes': 'construction style is outline-only until rig-aware guides are implemented; pastel is flat color without two-tone shadows.'
        }
        (out / 'render_metadata.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
finally:
    for name, materials in old_materials.items():
        obj = bpy.data.objects.get(name)
        if obj and obj.type == 'MESH':
            obj.data.materials.clear()
            for mat in materials:
                obj.data.materials.append(mat)
    for name, state in old_hide.items():
        obj = bpy.data.objects.get(name)
        if obj:
            obj.hide_render = state
    for name, (cam_type, scale) in old_camera_types.items():
        cam = bpy.data.objects.get(name)
        if cam:
            cam.data.type = cam_type
            cam.data.ortho_scale = scale
    scene.render.engine = original['engine']
    scene.render.filepath = original['filepath']
    scene.render.film_transparent = original['film_transparent']
    scene.render.resolution_x = original['res_x']
    scene.render.resolution_y = original['res_y']
    scene.render.resolution_percentage = original['res_pct']
    scene.camera = original['camera']
    scene.world = original['world']
    scene.view_settings.view_transform = original['view_transform']
    for mat in created_materials:
        if mat.users == 0:
            bpy.data.materials.remove(mat)
    if created_world and created_world.users == 0:
        bpy.data.worlds.remove(created_world)

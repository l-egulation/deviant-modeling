"""Blender validation of baked character deformation across every frame."""
import bpy
import json
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/hero-walk.blend'))
hero, rig = bpy.data.objects['InkHero'], bpy.data.objects['HeroRig']
weights = [sum(g.weight for g in v.groups) for v in hero.data.vertices]
assert min(weights) > .995 and max(weights) < 1.001
bottoms, locations = [], []
max_edge = 0
max_bone_length_error = 0
rest_coords = np.array([v.co[:] for v in hero.data.vertices])
edges = np.array([e.vertices[:] for e in hero.data.edges])
rest_edge = np.linalg.norm(rest_coords[edges[:,0]]-rest_coords[edges[:,1]], axis=1)
for frame in range(1,91):
    bpy.context.scene.frame_set(frame)
    for bone in rig.pose.bones:
        assert max(abs(s-1) for s in bone.scale) < 1e-6
        max_bone_length_error = max(max_bone_length_error, abs(bone.length-bone.bone.length))
    deps = bpy.context.evaluated_depsgraph_get()
    obj = hero.evaluated_get(deps)
    mesh = obj.to_mesh()
    coords = np.array([(obj.matrix_world @ v.co)[:] for v in mesh.vertices])
    assert np.isfinite(coords).all()
    bottoms.append(float(coords[:,2].min()))
    deformed_edge = np.linalg.norm(coords[edges[:,0]]-coords[edges[:,1]], axis=1)
    max_edge = max(max_edge, float(deformed_edge.max()))
    obj.to_mesh_clear()
    locations.append(rig.location[:])
assert max(abs(z) for z in bottoms) < 1e-5
assert max_bone_length_error < 1e-5
report = {'status':'PASS', 'frames_checked':90, 'finite_deformed_vertices':True,
          'weight_sum_min':min(weights), 'weight_sum_max':max(weights),
          'lowest_vertex_min_m':min(bottoms), 'lowest_vertex_max_m':max(bottoms),
          'max_deformed_edge_length_m':max_edge,
          'max_rest_edge_length_m':float(rest_edge.max()),
          'max_bone_length_error_m':max_bone_length_error, 'pose_bone_scales':'All (1,1,1), every frame',
          'horizontal_root_travel_m':float(np.linalg.norm(np.array(locations[-1])[:2]-np.array(locations[0])[:2])),
          'notes':'Grounding is vertical root correction, not full foot-contact IK. Visual review still required.'}
(ROOT/'docs/logs/hero-deformation-check.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))

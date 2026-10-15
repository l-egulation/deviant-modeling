"""Blender regression: neutral input preserves target bind axes and mesh."""
import os
import bpy
import json
import sys
from pathlib import Path
from mathutils import Euler

ROOT = Path(__file__).resolve().parents[1]
MOTION = os.environ.get('HERO_MOTION', 'walk')
assert MOTION in ('walk', 'run')
LOG_STEM = 'hero' if MOTION == 'walk' else 'hero-run'
sys.path.insert(0, str(ROOT/'scripts'))
from retarget import retarget_rotation

bpy.ops.wm.open_mainfile(filepath=str(ROOT/f'outputs/hero-{MOTION}.blend'))
rig, source = bpy.data.objects['HeroRig'], bpy.data.objects['KimodoSource']
references = {}
targets = {}
for bone in rig.data.bones:
    n = bone.name
    src_name = n.replace('UpLeg','Leg') if 'UpLeg' in n else n.replace('Leg','Shin') if n.endswith('Leg') else n
    references[n] = source.data.bones[src_name].matrix_local.to_3x3()
    targets[n] = bone.matrix_local.to_3x3()
for side in ('Left','Right'):
    a_pose = references[side+'Arm'].col[1].rotation_difference(targets[side+'Arm'].col[1]).to_matrix()
    for suffix in ('Arm','ForeArm','Hand'):
        references[side+suffix] = a_pose @ references[side+suffix]

legacy = '--check-legacy' in sys.argv
fn = (lambda posed, ref, target: posed) if legacy else retarget_rotation
neutral_error = motion_error = 0.0
delta = Euler((.03,-.04,.05)).to_matrix()
for name, ref in references.items():
    target = targets[name]
    result = fn(ref, ref, target)
    neutral_error = max(neutral_error, max(abs(result[r][c]-target[r][c]) for r in range(3) for c in range(3)))
    result = fn(delta @ ref, ref, target)
    expected = delta @ target
    motion_error = max(motion_error, max(abs(result[r][c]-expected[r][c]) for r in range(3) for c in range(3)))
report = {'mode':'legacy' if legacy else 'corrected', 'bones_checked':len(references),
          'neutral_matrix_max_error':neutral_error, 'known_motion_matrix_max_error':motion_error}
print(json.dumps(report, indent=2), flush=True)
assert neutral_error < 1e-5, f'Neutral pose changes character bind axes: {neutral_error}'
assert motion_error < 1e-5, f'Known rotation transferred incorrectly: {motion_error}'
print('PASS: neutral pose and known motion preserve target bind axes', flush=True)

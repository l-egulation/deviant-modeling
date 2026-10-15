"""Preview-only tracking and conservative rotation limits for oversized boots."""
import math
from mathutils import Vector

def boot_rotation(world, rest, pitch_degrees=20):
    # Human toe-off can exceed 60 degrees. The hero's much larger boot then
    # strikes the ground during swing. A smooth limit avoids a hard clamp kink.
    delta = (world @ rest.inverted()).to_euler('XYZ')
    delta.x = math.radians(pitch_degrees)*math.tanh(delta.x/math.radians(pitch_degrees))
    delta.y = math.radians(8)*math.tanh(delta.y/math.radians(8))
    return delta.to_matrix() @ rest

def configure_preview(scene, rig, camera):
    scene.frame_set(1)
    first = Vector((rig.location.x,rig.location.y,.49))
    lights = [(o, o.location.copy()) for o in scene.objects if o.type=='LIGHT']
    scene.frame_set(90)
    last = Vector((rig.location.x,rig.location.y,.49))
    loop_travel=Vector(rig['loop_displacement']) if 'loop_displacement' in rig else None
    camera.animation_data_clear()
    for light, _ in lights:
        light.animation_data_clear()
    offset = Vector((1.35,-2.7,.18))
    for f in range(1,91):
        scene.frame_set(f)
        travel = loop_travel*((f-1)/90) if loop_travel is not None else (last-first)*((f-1)/89)
        center = first+travel
        camera.location = center+offset
        camera.rotation_euler = (-offset).to_track_quat('-Z','Y').to_euler()
        camera.keyframe_insert('location',frame=f)
        camera.keyframe_insert('rotation_euler',frame=f)
        # Keep studio illumination fixed relative to the presentation camera,
        # rather than letting the light pool drift across the background.
        for light, start in lights:
            light.location = start+travel
            light.keyframe_insert('location',frame=f)
    if loop_travel is not None:
        scene.frame_set(91)
        camera.location=first+loop_travel+offset
        camera.keyframe_insert('location',frame=91)
        camera.keyframe_insert('rotation_euler',frame=91)
        for light,start in lights:
            light.location=start+loop_travel;light.keyframe_insert('location',frame=91)
    scene.frame_set(1)

"""Check the generated NPZ and standard-T-pose BVH; report, do not repair."""
import json
import re
import os
from pathlib import Path

import numpy as np
from kimodo.skeleton import SOMASkeleton77
from kimodo.exports.bvh import bvh_to_kimodo_motion

root = Path(__file__).resolve().parents[1]
name=os.environ.get('HERO_MOTION','walk')
assert name in ('walk','run')
motion = np.load(root / f'outputs/{name}.npz', allow_pickle=False)
sk = SOMASkeleton77()
positions = motion['posed_joints']
rotations = motion['local_rot_mats']
assert positions.shape == (90, 77, 3), positions.shape
assert rotations.shape == (90, 77, 3, 3), rotations.shape
for key in motion.files:
    assert np.isfinite(motion[key]).all(), f'Non-finite data: {key}'
parents = sk.joint_parents.numpy()
children = np.flatnonzero(parents >= 0)
lengths = np.linalg.norm(positions[:, children] - positions[:, parents[children]], axis=-1)
length_drift = float(np.ptp(lengths, axis=0).max())
orthogonality = float(np.abs(rotations @ rotations.swapaxes(-1, -2) - np.eye(3)).max())
determinant_error = float(np.abs(np.linalg.det(rotations) - 1).max())
assert length_drift < 0.001, length_drift
assert orthogonality < 0.001, orthogonality
assert determinant_error < 0.001, determinant_error
bvh_path = root / f'outputs/{name}.bvh'
bvh_text = bvh_path.read_text()
assert int(re.search(r'Frames:\s*(\d+)', bvh_text).group(1)) == 90
frame_time = float(re.search(r'Frame Time:\s*([\d.eE+-]+)', bvh_text).group(1))
assert abs(90 * frame_time - 3) < 0.001
bvh_motion, bvh_fps = bvh_to_kimodo_motion(bvh_path, standard_tpose=True)
bvh_positions = bvh_motion['posed_joints'].numpy()
assert bvh_positions.shape == positions.shape
assert np.isfinite(bvh_positions).all()
bvh_position_error = float(np.abs(bvh_positions - positions).max())
assert bvh_position_error < 0.001, f'BVH round-trip differs by {bvh_position_error} m'
foot_contacts = motion['foot_contacts']
assert foot_contacts.shape == (90, len(sk.foot_joint_idx))
foot_speed = np.linalg.norm(np.diff(positions[:, sk.foot_joint_idx][:, :, [0, 2]], axis=0) * bvh_fps, axis=-1)
contact_pairs = (foot_contacts[:-1] > 0.5) & (foot_contacts[1:] > 0.5)
contact_speed = foot_speed[contact_pairs]
report = {
    'status': 'PASS', 'frames': 90, 'joints': 77,
    'fps': bvh_fps, 'duration_seconds': 90 * frame_time,
    'npz_keys': motion.files,
    'max_bone_length_drift_m': length_drift,
    'max_rotation_orthogonality_error': orthogonality,
    'max_rotation_determinant_error': determinant_error,
    'root_displacement_m': np.linalg.norm(motion['root_positions'][-1] - motion['root_positions'][0]).item(),
    'bvh_import_max_position_difference_m': bvh_position_error,
    'foot_contact_shape': list(foot_contacts.shape),
    'foot_contact_joint_names': sk.foot_joint_names,
    'mean_horizontal_speed_during_consecutive_contacts_m_s': float(contact_speed.mean()) if contact_speed.size else None,
    'npz_bytes': (root / f'outputs/{name}.npz').stat().st_size,
    'bvh_bytes': bvh_path.stat().st_size,
    'visual_quality': 'Requires actual playback; numeric checks alone do not certify walking quality.',
}
path = root / ('docs/logs/motion-check.json' if name=='walk' else 'docs/logs/run-motion-check.json')
path.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))

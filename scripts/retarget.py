"""Transfer motion relative to calibrated source bind axes, never bone frames."""

def retarget_rotation(source_pose, source_reference, target_rest):
    """All inputs are world-space 3x3 rotation matrices; lengths stay unchanged."""
    return source_pose @ source_reference.inverted() @ target_rest

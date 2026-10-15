"""Track the full source support of the two-stage run interpolation."""
import math
import numpy as np


def frame_contact(contacts,frame,rig,all_samples=False):
    if rig.get('canonical_run_cycle'):
        phase=frame*5/6%15
        indices=[]
        # Each new pose interpolates two cycle-averaged old poses. Each old
        # pose itself interpolated two original frames at the 1.5x stage.
        for old in (math.floor(phase),math.ceil(phase)%15):
            for repeat in (0,15):
                source=(old+repeat)*1.5%45
                indices.extend((math.floor(source),math.ceil(source)%45))
    else:
        period=45 if 'run_timing_rate' in rig else 90
        phase=frame*float(rig.get('run_timing_rate',1))%period
        indices=(math.floor(phase),math.ceil(phase)%period)
    values=contacts[list(indices)]
    return np.all(values,axis=0) if all_samples else np.any(values,axis=0)

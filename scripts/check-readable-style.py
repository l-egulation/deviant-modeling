from pathlib import Path
import json
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1];O=R/'outputs/pixel-readable-style';report={}
for name,path in [('before',R/'outputs/pixel-painted-style/pixel-idle/designed'),('after',O/'idle')]:
 a=np.array([np.array(Image.open(path/f'{i:03d}.png').convert('RGBA')) for i in range(1,91)])
 d=np.any(a[1:]!=a[:-1],axis=3).sum((1,2))
 report[name]={'mean_changed_pixels':float(d.mean()),'max_changed_pixels':int(d.max())}
report['note']='Screen-space differences include motion, camera, silhouette, occlusion and shading. Not an isolated flicker or quality metric.'
cloth=json.loads((R/'docs/logs/pixel-readable-idle-cloth-validation.json').read_text())
collar=json.loads((R/'docs/logs/pixel-collar-readable.json').read_text())
assert cloth['frames_with_intersections']==0 and cloth['max_edge_stretch']<2
assert collar['max_gap_m']<1e-5
report['cloth']={k:v for k,v in cloth.items() if k!='frames'}
report['collar_max_gap_m']=collar['max_gap_m']
(O/'motion-pixel-check.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

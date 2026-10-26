"""Deterministic technical export of the AI-painted static art candidate.

This does not infer a style or transfer it to new poses. Never use independent
bounding-box resizing on animation frames: the master defines the shared scale.
"""
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw, ImageOps

R = Path(__file__).resolve().parents[1]
O = R / 'outputs/pixel-style-master'
colors = ['FDEEDA', 'D2B396', '1B1616', '025673', '02648C', 'EBA516']
palette = np.array([[int(c[i:i+2], 16) for i in (0, 2, 4)] for c in colors])

source = Image.open(O / 'generated.png').convert('RGBA')
a = np.array(source)
raw_colors = len(np.unique(a[a[:, :, 3] >= 128, :3], axis=0))
mask = Image.fromarray(np.where(a[:, :, 3] >= 128, 255, 0).astype('uint8'))
bbox = mask.getbbox()
crop = source.crop(bbox)
width = round(crop.width * 64 / crop.height)
a = np.array(crop.resize((width, 64), Image.Resampling.NEAREST))
idx = ((a[:, :, None, :3].astype(int) - palette) ** 2).sum(3).argmin(2)
a[:, :, :3] = palette[idx]
a[:, :, 3] = np.where(a[:, :, 3] >= 128, 255, 0)
a[a[:, :, 3] == 0, :3] = 0
sprite = Image.fromarray(a)
canvas = Image.new('RGBA', (128, 128))
origin = (64 - width // 2, 40)
canvas.paste(sprite, origin)
canvas.save(O / 'master-128.png')
canvas.resize((768, 768), Image.Resampling.NEAREST).save(O / 'master-preview.png')

# Compare at equal character height, without interpolating pixel artwork.
team = Image.open(O / 'team-reference.png').convert('RGBA')
t = np.array(team)
t[:, :, 3] = np.where(np.all(t[:, :, :3] == 255, axis=2), 0, 255)
team = Image.fromarray(t).resize((128, 128), Image.Resampling.NEAREST)
team = team.crop(team.getbbox())
render = ImageOps.mirror(Image.open(R / 'outputs/pixel-idle-sprites/original/000.png').convert('RGBA'))
render = render.crop(render.getbbox())
render = render.resize((round(render.width * 64 / render.height), 64), Image.Resampling.LANCZOS)
board = Image.new('RGB', (1152, 500), '#454953')
draw = ImageDraw.Draw(board)
for i, (label, tile) in enumerate([('3D INPUT', render), ('TEAM REFERENCE', team), ('STYLE MASTER CANDIDATE', sprite)]):
    tile = tile.resize((tile.width * 5, tile.height * 5), Image.Resampling.NEAREST)
    board.paste(tile, (i * 384 + (384 - tile.width) // 2, 420 - tile.height), tile)
    draw.text((i * 384 + 18, 28), label, fill='white')
    draw.text((i * 384 + 18, 455), 'Character height: 64 px / display: 5x', fill='white')
board.save(O / 'comparison.png')

out = np.array(canvas)
used = {tuple(c) for c in out[out[:, :, 3] > 0, :3]}
assert used <= {tuple(c) for c in palette}
assert set(np.unique(out[:, :, 3])) <= {0, 255}
assert canvas.getbbox()[3] - canvas.getbbox()[1] == 64
report = {
    'source': 'built-in image_gen; not deterministic 3D style transfer',
    'status': 'static candidate; visual approval and multi-pose consistency pending',
    'canvas': [128, 128], 'character_height_px': 64, 'character_bbox': canvas.getbbox(),
    'origin': origin, 'ground_y_exclusive': 104, 'palette': colors,
    'opaque_color_count': len(used), 'alpha_values': list(map(int, np.unique(out[:, :, 3]))),
    'generated_size': source.size, 'generated_alpha_bbox': bbox,
    'generated_opaque_color_count': raw_colors,
    'normalization': 'one static crop, nearest resample, nearest fixed palette, binary alpha',
    'geometry_modified': False, 'animation_created': False,
    'limits': ['AI changed pose/silhouette; not a pose-faithful transfer',
               'No temporal consistency established by a static master',
               'No per-frame AI regeneration or independent crop scaling approved as pipeline'],
}
(O / 'validation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))

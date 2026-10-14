"""Encode Blender renders and check the animated GLB and preview duration."""
import av
import json
import struct
from fractions import Fraction
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
frames = ROOT/'.cache/hero-frames'
dest = ROOT/'outputs/hero-walk-preview.mp4'
with av.open(str(dest), 'w') as container:
    stream = container.add_stream('libx264', rate=30)
    stream.width = stream.height = 512
    stream.pix_fmt = 'yuv420p'
    stream.options = {'crf': '18'}
    for i in range(90):
        rgb = np.array(Image.open(frames/f'{i+1:03d}.png').convert('RGB'))
        frame = av.VideoFrame.from_ndarray(rgb, format='rgb24')
        frame.pts, frame.time_base = i, Fraction(1, 30)
        for packet in stream.encode(frame):
            container.mux(packet)
    for packet in stream.encode():
        container.mux(packet)
sheet = Image.new('RGB', (1536, 1024))
for i,f in enumerate([1,16,31,46,61,76]):
    tile = Image.open(frames/f'{f:03d}.png').convert('RGB')
    ImageDraw.Draw(tile).text((12,12), f'{(f-1)/30:.1f}s', fill='white')
    sheet.paste(tile, ((i%3)*512, (i//3)*512))
sheet.save(ROOT/'outputs/hero-walk-contact-sheet.png')
blob = (ROOT/'outputs/hero-walk.glb').read_bytes()
n = struct.unpack_from('<I', blob, 12)[0]
gltf = json.loads(blob[20:20+n])
assert len(gltf.get('skins', [])) == 1
assert len(gltf.get('animations', [])) == 1
assert len(gltf['skins'][0]['joints']) == 16
with av.open(str(dest)) as c:
    s = c.streams.video[0]
    rate = float(s.average_rate)
    decoded = [f.to_ndarray(format='rgb24') for f in c.decode(video=0)]
assert len(decoded) == 90 and rate == 30
diff = float(np.abs(decoded[0].astype(float)-decoded[45].astype(float)).mean())
assert diff > 1
report = {'status': 'PASS', 'frames': 90, 'fps': rate, 'seconds': 3,
          'width':512, 'height':512, 'glb_skins':1, 'glb_joints':16,
          'glb_animations':len(gltf['animations']), 'first_to_mid_pixel_difference':diff,
          'scope':'First-pass body rig, not a final production topology or seamless loop.'}
(ROOT/'docs/logs/hero-preview-check.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report, indent=2))

"""Package source and cloth comparison without changing animation timing."""
from pathlib import Path
from PIL import Image,ImageDraw
import av,numpy as np,json
R=Path(__file__).resolve().parents[1]
source=json.loads((R/'docs/logs/pixel-run-source.json').read_text())['joints']
parents={'Spine1':'Hips','Spine2':'Spine1','Chest':'Spine2','Neck1':'Chest','Head':'Neck1'}
for side in ['Left','Right']:
 for a,b in [('Shoulder','Chest'),('Arm',side+'Shoulder'),('ForeArm',side+'Arm'),('Hand',side+'ForeArm'),('Leg','Hips'),('Shin',side+'Leg'),('Foot',side+'Shin'),('ToeBase',side+'Foot')]:parents[side+a]=b
raw_frames=[]
for row in source:
 raw=Image.new('RGB',(384,384),'#f0f2f5');d=ImageDraw.Draw(raw)
 def xy(n):return (192+(row[n][1]-row['Hips'][1])*150,350-row[n][2]*150)
 d.line((0,350,384,350),fill='#858585')
 for n,parent in parents.items():d.line((xy(n),xy(parent)),fill='#dc4141' if n.startswith('Left') else '#2d73e1' if n.startswith('Right') else '#282d37',width=4)
 x,y=xy('Head');d.ellipse((x-8,y-8,x+8,y+8),outline='#282d37',width=3);raw_frames.append(raw)
raw_frames[0].save(R/'outputs/pixel-run-source-preview.gif',save_all=True,append_images=raw_frames[1:],duration=[30,30,40]*30,loop=0)
frames=[]
for i,path in enumerate(sorted((R/'.cache/pixel-run-preview').glob('*.png'))):
 board=Image.new('RGB',(768,416),'#20252c')
 board.paste(raw_frames[i],(0,32))
 board.paste(Image.open(path).convert('RGB').resize((384,384)),(384,32))
 d=ImageDraw.Draw(board);d.text((10,10),'MIXAMO SOURCE / ORIGINAL TIMING',fill='white');d.text((394,10),'FITTED RIG + CLOTH / TEST',fill='white');frames.append(board)
assert len(frames)==90
with av.open(str(R/'outputs/pixel-run-comparison.mp4'),'w') as out:
 stream=out.add_stream('libx264',rate=30);stream.width=768;stream.height=416;stream.pix_fmt='yuv420p';stream.options={'crf':'19'}
 for im in frames:
  for packet in stream.encode(av.VideoFrame.from_ndarray(np.asarray(im),format='rgb24')):out.mux(packet)
 for packet in stream.encode():out.mux(packet)
frames[0].save(R/'outputs/pixel-run-comparison.gif',save_all=True,append_images=frames[1:],duration=[30,30,40]*30,loop=0)
sheet=Image.new('RGB',(1152,1248),'#20252c')
for i,f in enumerate(range(0,90,10)):
 tile=frames[f].crop((384,0,768,416));ImageDraw.Draw(tile).text((10,32),f'FRAME {f+1}',fill='white');sheet.paste(tile,((i%3)*384,(i//3)*416))
sheet.save(R/'outputs/pixel-run-contact-sheet.png')
with av.open(str(R/'outputs/pixel-run-comparison.mp4')) as check:
 count=sum(1 for _ in check.decode(video=0));assert count==90
gif=Image.open(R/'outputs/pixel-run-comparison.gif');assert gif.n_frames==90
duration=0
for f in range(gif.n_frames):gif.seek(f);duration+=gif.info['duration']
assert duration==3000
(R/'docs/logs/pixel-run-media.json').write_text(json.dumps({'decoded_frames':count,'fps':30,'seconds':3,'gif_frames':gif.n_frames,'gif_duration_ms':duration,'loop_seam_verified':False},indent=2))
before=R/'.cache/posture-before/pixel-run-comparison.mp4'
if before.exists():
 with av.open(str(before)) as movie:old=[f.to_image() for f in movie.decode(video=0)]
 assert len(old)==90
 with av.open(str(R/'outputs/pixel-run-posture-comparison.mp4'),'w') as out:
  stream=out.add_stream('libx264',rate=30);stream.width=768;stream.height=416;stream.pix_fmt='yuv420p';stream.options={'crf':'19'}
  for i,im in enumerate(frames):
   board=Image.new('RGB',(768,416),'#20252c');board.paste(old[i].crop((384,32,768,416)),(0,32));board.paste(im.crop((384,32,768,416)),(384,32))
   d=ImageDraw.Draw(board);d.text((10,10),'BEFORE / OLD KIMODO RUN',fill='white');d.text((394,10),'AFTER / MIXAMO RUN',fill='white')
   for packet in stream.encode(av.VideoFrame.from_ndarray(np.asarray(board),format='rgb24')):out.mux(packet)
  for packet in stream.encode():out.mux(packet)
 with av.open(str(R/'outputs/pixel-run-posture-comparison.mp4')) as check:
  comparison_count=sum(1 for _ in check.decode(video=0));assert comparison_count==90
 report=json.loads((R/'docs/logs/pixel-run-media.json').read_text());report['posture_comparison_frames']=comparison_count
 (R/'docs/logs/pixel-run-media.json').write_text(json.dumps(report,indent=2))

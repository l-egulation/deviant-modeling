"""Play the generated skeleton locally without loading the Llama encoder again."""
import argparse
from fractions import Fraction
from pathlib import Path
import threading
import time

import av
import numpy as np
from PIL import Image
import viser
from kimodo.skeleton.registry import build_skeleton
from kimodo.exports.bvh import bvh_to_kimodo_motion

parser = argparse.ArgumentParser()
parser.add_argument('--bvh', action='store_true', help='Play the exported standard-T-pose BVH.')
parser.add_argument('--port', type=int, default=7860)
parser.add_argument('--motion', type=Path, help='Optional NPZ or BVH to inspect.')
parser.add_argument('--preview-dir', type=Path, help='Optional directory for preview exports.')
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
motion_path = args.motion or root / ('outputs/walk.bvh' if args.bvh else 'outputs/walk.npz')
preview_dir = args.preview_dir or root / 'outputs'
if args.bvh:
    data, fps = bvh_to_kimodo_motion(motion_path, standard_tpose=True)
    positions = data['posed_joints'].numpy()
else:
    positions = np.load(motion_path, allow_pickle=False)['posed_joints']
    fps = 30.0
video_rate = Fraction(str(fps)).limit_denominator(1001)
sk = build_skeleton(positions.shape[1])
parents = sk.joint_parents.numpy()
children = np.flatnonzero(parents >= 0)
edges = np.stack([parents[children], children], axis=1)
colors = np.array([(230, 90, 90) if sk.bone_order_names[c].startswith('Left')
                   else (70, 150, 240) if sk.bone_order_names[c].startswith('Right')
                   else (50, 60, 75) for c in children], dtype=np.uint8)
colors = np.repeat(colors[:, None, :], 2, axis=1)
center = (positions.min(axis=(0, 1)) + positions.max(axis=(0, 1))) / 2
server = viser.ViserServer(host='127.0.0.1', port=args.port, label='Kimodo walk — skeleton only')
server.scene.set_up_direction('+y')
server.scene.add_grid('/ground', width=10, height=10,
                      wxyz=viser.transforms.SO3.from_x_radians(-np.pi / 2).wxyz)
lines = server.scene.add_line_segments('/bones', positions[0][edges], colors, line_width=4)
joints = server.scene.add_point_cloud('/joints', positions[0], (60, 70, 90), point_size=0.018)
server.gui.add_markdown(f'**{motion_path.name}** · {len(positions)} frames · {fps:g} fps · skeleton only')
play = server.gui.add_checkbox('Play', initial_value=True)
frame = server.gui.add_slider('Frame', min=0, max=len(positions)-1, step=1, initial_value=0)
export = server.gui.add_button('Export preview MP4')
lock = threading.RLock()

def draw(index):
    with server.atomic():
        lines.points = positions[index][edges]
        joints.points = positions[index]

@server.on_client_connect
def connect(client):
    client.camera.position = center + np.array([3.5, 1.6, 5.5])
    client.camera.look_at = center
    client.camera.up_direction = (0.0, 1.0, 0.0)
    client.camera.fov = np.deg2rad(45.0)
    print(f'Browser connected; playing {"BVH" if args.bvh else "NPZ"}', flush=True)

@frame.on_update
def seek(_):
    with lock:
        draw(int(frame.value))

@export.on_click
def save_preview(event):
    with lock:
        play.value = False
        preview_dir.mkdir(parents=True, exist_ok=True)
        path = preview_dir / 'walk-preview.mp4'
        samples = []
        with av.open(str(path), 'w') as container:
            stream = container.add_stream('libx264', rate=video_rate)
            stream.width, stream.height, stream.pix_fmt = 720, 720, 'yuv420p'
            for index in range(len(positions)):
                frame.value = index
                draw(index)
                rgb = event.client.get_render(height=720, width=720, transport_format='png')[:, :, :3]
                if index % 15 == 0:
                    samples.append(Image.fromarray(rgb))
                video_frame = av.VideoFrame.from_ndarray(rgb, format='rgb24')
                video_frame.pts = index
                video_frame.time_base = 1 / video_rate
                for packet in stream.encode(video_frame):
                    container.mux(packet)
            for packet in stream.encode():
                container.mux(packet)
        sheet = Image.new('RGB', (720 * 3, 720 * 2), 'white')
        for index, sample in enumerate(samples[:6]):
            sheet.paste(sample, ((index % 3) * 720, (index // 3) * 720))
        sheet.save(preview_dir / 'walk-contact-sheet.png')
        print(f'Preview exported: {path}', flush=True)
        play.value = True

print(f'Open http://127.0.0.1:{args.port}', flush=True)
while True:
    with lock:
        if play.value:
            frame.value = (int(frame.value) + 1) % len(positions)
            draw(int(frame.value))
    time.sleep(1 / fps)

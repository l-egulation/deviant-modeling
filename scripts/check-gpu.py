"""Verify a real CUDA operation without downloading model weights."""
import json
import platform
import torch

if not torch.cuda.is_available():
    raise SystemExit('CUDA is unavailable')
a = torch.arange(16, dtype=torch.float32, device='cuda').reshape(4, 4)
result = a @ torch.eye(4, device='cuda')
torch.cuda.synchronize()
assert torch.equal(result, a)
print(json.dumps({
    'python': platform.python_version(),
    'torch': torch.__version__,
    'torch_cuda': torch.version.cuda,
    'gpu': torch.cuda.get_device_name(0),
    'vram_bytes': torch.cuda.get_device_properties(0).total_memory,
    'cuda_matrix_check': 'PASS',
}, indent=2))

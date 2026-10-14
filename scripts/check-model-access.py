"""Check the gated text encoder before downloading large model weights.

Uses the local Hugging Face login or HF_TOKEN_PATH; never prints a token.
"""
from huggingface_hub import get_hf_file_metadata, hf_hub_url
from huggingface_hub.errors import HfHubHTTPError, LocalTokenNotFoundError

try:
    get_hf_file_metadata(
        hf_hub_url('meta-llama/Meta-Llama-3-8B-Instruct', 'config.json'), token=True
    )
except LocalTokenNotFoundError:
    print('Llama text encoder access: FAILED (no local Hugging Face login)')
    print('Log in locally with hf auth login or set HF_TOKEN_PATH to your existing token file.')
    raise SystemExit(1)
except HfHubHTTPError as error:
    status = error.response.status_code if error.response is not None else 'unknown'
    print(f'Llama text encoder access: FAILED (HTTP {status})')
    print('Request access: https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct')
    print('After approval, log in locally with hf auth login. Do not share your token.')
    raise SystemExit(1)
else:
    print('Llama text encoder access: PASS')

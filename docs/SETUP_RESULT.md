# 갤럭시북 Kimodo 설치·검증 기록

작업일: 2026-10-14 (Asia/Seoul). 브랜치: `work/kimodo-setup`.

## 검증 결과

- Kimodo `1.0.0` 및 `all` 부가 패키지 설치 완료. 기본 네이티브 후처리 모듈도 빌드 성공.
- PyTorch `2.11.0+cu128`, 내장 CUDA `12.8`: 실제 RTX 4050 CUDA 행렬 연산 **PASS**.
- `pip check`: **PASS**, 의존성 충돌 없음. `kimodo_gen --help`, `kimodo_demo --help`: **PASS**. 뷰어 명령 확인은 실제 웹 화면·모션 재생 확인과 다르다.
- Bash·Python·PowerShell 문법 검사 및 `git diff --check`: **PASS**.
- Llama 텍스트 인코더 접근: 기존 로컬 인증으로 HTTP 403 `GatedRepo`. 계정의 모델 접근 승인 필요.
- `HF_TOKEN_PATH=... bash scripts/run-walk.sh` 실제 실행: CUDA 검사 PASS 이후 모델 접근 검사 HTTP 403으로 exit 1. 생성 명령 진입 전 종료됨.
- 3초 걷기 생성: 모델 접근 문제로 미완료. 생성 시간·최대 GPU 메모리 사용량은 미측정.
- `outputs/walk.npz`, `outputs/walk.bvh`: 없음. 실제 재생·걷기 품질·BVH 가져오기 검증은 미완료.

## 실행 환경

- Windows 11 Enterprise, 물리 RAM 약 32GB.
- Intel Core i7-13700H, WSL에서 논리 CPU 20개 확인.
- NVIDIA GeForce RTX 4050 Laptop GPU, VRAM 6141MiB, Windows 드라이버 591.44.
- 기존 WSL2 `Ubuntu-22.04`, Python 3.10.12.
- WSL 커널 `6.18.33.2-microsoft-standard-WSL2`; WSL 메모리 약 15GiB, swap 4GiB.
- 확인 당시 C: 여유 약 412GB. WSL 논리 디스크 여유는 물리 디스크 여유와 다르다.
- Windows와 WSL 모두 `nvidia-smi`에서 실제 GPU를 확인했다. 드라이버가 표시하는 CUDA 13.1은 PyTorch 내장 CUDA 버전과 다르다.
- Python 환경은 `/opt/deviant-kimodo/.venv`. Windows 마운트 아래 `.venv`는 pip 설치가 느려 사용하지 않는다. 결과와 기록은 Windows 저장소에 저장한다.
- 공식 Kimodo 소스: `https://github.com/nv-tlabs/kimodo`, 커밋 `58e781898b3d7e328a676a75d3e338c45dce3ad9`.
- 주요 부가 버전: Transformers `5.1.0`, NumPy `2.2.6`, Hugging Face Hub `1.33.0`, Viser `1.0.16`, py-soma-x `0.3.4`. 전체 설치 버전과 Git 기반 의존성 커밋은 `docs/logs/packages.txt` 참조. 이 파일은 환경 기록이며 다른 컴퓨터에서 그대로 설치할 requirements 파일이 아니다.

## 설치 및 재실행

Windows 저장소: `C:\Users\SSAFY\Desktop\3rd_PJT\deviant-modeling`.
WSL 저장소: `/mnt/c/Users/SSAFY/Desktop/3rd_PJT/deviant-modeling`.

WSL Ubuntu에서:

```bash
cd /mnt/c/Users/SSAFY/Desktop/3rd_PJT/deviant-modeling
bash scripts/install-kimodo.sh
```

설치 스크립트는 root 실행을 요구한다. 현재 기존 WSL 기본 사용자는 root였다. 다른 사용자라면 `sudo bash scripts/install-kimodo.sh`를 사용한다. 환경 경로를 변경하려면 `KIMODO_ENV`를 지정한다. 설치 후 별도 activate 없이 스크립트가 해당 환경의 실행 파일을 직접 사용한다.

승인된 Hugging Face 계정으로 사용자가 로컬 로그인할 경우:

```bash
export HF_HOME="$PWD/.cache/huggingface"
/opt/deviant-kimodo/.venv/bin/hf auth login
bash scripts/run-walk.sh
```

이미 Windows에서 로그인했고 그 인증을 사용하려면 토큰 값을 복사하지 않고 다음 파일 경로를 지정할 수 있다:

```bash
export HF_TOKEN_PATH=/mnt/c/Users/SSAFY/.cache/huggingface/token
bash scripts/run-walk.sh
```

PowerShell 진입점은 `scripts/run-walk.ps1`이다. WSL 쪽 로그인 상태를 사용한다. Windows의 기존 인증 파일을 쓰는 위 예시는 WSL에서 실행한다.

실제 생성 명령:

```bash
TEXT_ENCODER_DEVICE=cpu TEXT_ENCODER_MODE=local \
/opt/deviant-kimodo/.venv/bin/kimodo_gen \
  'A person walks forward at a relaxed pace with natural arm swing.' \
  --model Kimodo-SOMA-RP-v1.1 --duration 3.0 --num_samples 1 \
  --seed 42 --bvh --bvh_standard_tpose --output outputs/walk
```

`run-walk.sh`는 먼저 실제 CUDA 연산과 Llama 접근을 검사한다. 접근 검사가 실패하면 대형 가중치를 불필요하게 내려받지 않고 종료한다. 생성 시간은 다운로드·모델 로딩을 포함한 전체 실행 시간으로 기록되며 순수 추론 시간과 구분한다.
접근 검사는 캐시 파일 성공 여부가 아니라 공식 서버에 HEAD 요청을 보내 확인한다. 설치 스크립트로 재설치하면 `docs/logs/install-kimodo.log`에 전체 설치 출력을 남긴다.

## 모델 접근 문제

사용자가 기존 Hugging Face 인증 사용을 허용한 뒤 공식 서버에 작은 설정 파일 접근을 확인했다. 토큰은 출력하거나 복제하지 않았다.

`meta-llama/Meta-Llama-3-8B-Instruct` 응답: HTTP 403, `GatedRepo`.
서버 사유: 현재 인증 계정이 승인된 모델 접근 목록에 없다.

사용자가 [모델 페이지](https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct)에서 접근 신청 및 승인을 완료해야 한다. 기존 토큰이 읽기 권한을 갖고 있어도 계정의 모델 승인이 없으면 다운로드할 수 없다. Hugging Face는 가중치 배포처이며 모션 생성은 이 갤럭시북의 로컬 GPU에서 수행한다.
Windows의 기존 Hugging Face 캐시에는 필요한 Llama 3 8B·Kimodo 가중치가 없었다. WSL 메모리 한도에서 CPU 인코더 실행 시 메모리 사용량은 승인 후 실제 생성으로 확인해야 한다.

## 설치 중 확인한 문제

- 첫 `python3 -m venv .venv`는 `ensurepip` 부재로 실패했다. `python3.10-venv`와 개발 헤더·CMake를 설치했다.
- Windows 마운트 경로의 venv에서 pip 갱신이 오래 걸려 해당 설치 프로세스를 종료하고 Linux 디스크의 독립 환경으로 재설치했다. 이 환경에서 PyTorch 설치와 CUDA 검사는 성공했다.
- 모델 접근 검사에 필요한 기존 인증 사용은 사용자 승인 후 수행했다. 인증 토큰 값은 기록하지 않았다.

## 기록 파일

- `docs/logs/system-install.log`: venv·CMake·Python 개발 헤더 설치.
- `docs/logs/environment.txt`: 호스트·CPU·GPU·메모리·디스크와 빌드 도구 기록.
- `docs/logs/pytorch-install.log`: GPU PyTorch 설치.
- `docs/logs/kimodo-install.log`: 공식 Kimodo 및 뷰어 설치.
- `docs/logs/gpu-check.json`: 실제 PyTorch CUDA 연산 검사.
- `docs/logs/model-access.log`: 모델 접근 검사.
- `docs/logs/dependency-check.log`: 설치 의존성 검사.
- `docs/logs/packages.txt`: 설치된 패키지 버전 기록.
- `docs/logs/kimodo-gen-help.txt`, `docs/logs/kimodo-demo-help.txt`: 실제 설치 버전의 명령 도움말.
- 현재 미생성: `docs/logs/walk-generation.log`, `outputs/walk.npz`, `outputs/walk.bvh`. 모델 접근 검사 통과 후 생성 실행에서 기록과 결과가 만들어진다.

인증 파일, 가중치, 패키지 캐시와 가상환경은 커밋 대상이 아니다. `.cache/`는 저장소 ignore 대상이다.
공유 로그는 터미널 진행 표시의 carriage return과 줄 끝 공백을 정리했다. 셸 스크립트는 `.gitattributes`로 LF 줄바꿈을 유지한다.

## 후속 재생 확인

생성에 성공하면 같은 WSL 환경에서 다음을 실행한다:

```bash
TEXT_ENCODER_DEVICE=cpu HF_HOME="$PWD/.cache/huggingface" \
/opt/deviant-kimodo/.venv/bin/kimodo_demo
```

Windows 브라우저에서 `http://127.0.0.1:7860`을 열고 Load/Save → Motion에서 `outputs/walk.npz`를 불러 재생한다. 보행, 관절 뒤집힘·폭발, 발 미끄러짐을 실제로 관찰하고 기록한다. BVH는 표준 T 포즈·cm 단위 기준으로 Blender에서 별도 확인한다.

골격 생성과 주인공 GLB 리깅·모션 이식은 별도 업무다. 현재 GLB는 수정하지 않았다.

## 공식 참고 자료

- [설치 및 모델 접근](https://research.nvidia.com/labs/sil/projects/kimodo/docs/getting_started/installation.html)
- [Kimodo 소스 및 CPU 텍스트 인코더](https://github.com/nv-tlabs/kimodo)
- [PyTorch CUDA 설치](https://pytorch.org/get-started/locally/)

# 갤럭시북 Kimodo 설치·검증 기록

작업일: 2026-10-14 (Asia/Seoul). 브랜치: `work/kimodo-setup`.

## 최종 결과: 3초 골격 걷기 생성·재생 완료

- 사용자 승인 후 기존 로컬 인증으로 Llama 접근 PASS. `scripts/run-walk.sh`는 exit 0으로 정상 종료.
- `Kimodo-SOMA-RP-v1.1`, 3초, 한 샘플, seed 42, 기본 100 diffusion steps, CPU 텍스트 인코더와 기본 후처리 사용.
- `outputs/walk.npz`: 90프레임, SOMA 77관절, 587,390 bytes.
- `outputs/walk.bvh`: 표준 T포즈 기준, 30fps·90프레임·3초, 205,793 bytes. BVH 길이 단위는 cm.
- NPZ·BVH의 유한값, 회전 행렬, 골격 길이 및 프레임 수 검사 PASS. BVH 재가져오기와 NPZ 관절 위치 최대 차이는 약 0.002mm.
- 실제 브라우저에서 NPZ와 BVH를 각각 재생했다. 앞으로 이동하면서 양발과 팔을 번갈아 움직이며, 큰 관절 폭발이나 뒤집힘은 관찰하지 않았다.
- 루트 이동은 약 4.474m/3초. 제자리 걷기나 완벽한 루프로 보정한 결과는 아니다. 연속 접지 프레임의 발 수평 속도 평균은 약 0.028m/s이며 완전한 발 고정은 아니다.
- `outputs/walk-preview.mp4`: 실제 NPZ 골격을 렌더링한 720×720, 90프레임·30fps·3초 영상. 디코딩과 프레임 변화 검사 PASS. `outputs/walk-contact-sheet.png`: 0·15·30·45·60·75 프레임 비교.
- 첫 실행 전체 2,773초(46분 13초): 다운로드·모델 로딩·텍스트 처리·생성·저장 포함. 진행 표시의 100단계 denoising은 약 16초이며, 순수 전체 추론 시간이나 캐시 재실행 총 시간으로 해석하지 않는다.
- 약 2초 간격 GPU 샘플 1,295개에서 장치 전체 메모리 최대 2,386MiB(약 2.33GiB). 정확한 프로세스별 순간 최대치와 CPU 최대 메모리는 미측정. 기존 WSL 약 15GiB RAM/4GiB swap 설정에서 메모리 부족 오류 없이 완료했다.

현재 완료 범위는 **사람 골격 모션 생성·재생 검증**이다. 주인공 GLB 리깅·모션 이식이나 도트 스프라이트 제작은 아직 하지 않았다.

## 최초 설치·승인 전 검증 결과

- Kimodo `1.0.0` 및 `all` 부가 패키지 설치 완료. 기본 네이티브 후처리 모듈도 빌드 성공.
- PyTorch `2.11.0+cu128`, 내장 CUDA `12.8`: 실제 RTX 4050 CUDA 행렬 연산 **PASS**.
- `pip check`: **PASS**, 의존성 충돌 없음. `kimodo_gen --help`, `kimodo_demo --help`: **PASS**. 뷰어 명령 확인은 실제 웹 화면·모션 재생 확인과 다르다.
- Bash·Python·PowerShell 문법 검사 및 `git diff --check`: **PASS**.
- 최초에는 Llama 접근 HTTP 403으로 생성 명령 전 종료됐다. 사용자의 접근 승인 후 해결됐으며 최종 결과는 위와 같다.

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

## 모델 접근 문제: 해결됨

사용자가 기존 Hugging Face 인증 사용을 허용한 뒤 공식 서버에 작은 설정 파일 접근을 확인했다. 토큰은 출력하거나 복제하지 않았다.

`meta-llama/Meta-Llama-3-8B-Instruct` 응답: HTTP 403, `GatedRepo`.
당시 서버 사유: 인증 계정이 승인된 모델 접근 목록에 없었다. 이후 사용자가 승인을 받은 뒤 동일 인증의 서버 HEAD 검사 PASS와 실제 다운로드 성공을 확인했다.

다른 계정으로 재설치할 경우 [모델 페이지](https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct)의 접근 승인이 필요하다. Hugging Face는 가중치 배포처이며 모션 생성은 이 갤럭시북의 로컬 GPU에서 수행했다.
이번 실행에서 필요한 가중치를 `.cache/huggingface/`에 내려받았다. Llama safetensors 4개 합계는 16,060,556,376 bytes이며 Kimodo와 어댑터 캐시는 별도다. 이 캐시와 토큰은 Git에 올리지 않는다.

## 설치 중 확인한 문제

- 첫 `python3 -m venv .venv`는 `ensurepip` 부재로 실패했다. `python3.10-venv`와 개발 헤더·CMake를 설치했다.
- Windows 마운트 경로의 venv에서 pip 갱신이 오래 걸려 해당 설치 프로세스를 종료하고 Linux 디스크의 독립 환경으로 재설치했다. 이 환경에서 PyTorch 설치와 CUDA 검사는 성공했다.
- 모델 접근 검사에 필요한 기존 인증 사용은 사용자 승인 후 수행했다. 인증 토큰 값은 기록하지 않았다.
- 인코더 로딩 중 `lm_head` 및 LoRA 키의 `UNEXPECTED/MISSING`, 중복 `peft_config` 경고가 출력됐다. 공식 LLM2Vec 코드의 명시적 PEFT 재로딩·merge 단계를 그대로 사용했고, 실행은 정상 종료됐다. 전체 경고는 생성 로그에 보존한다.

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
- `docs/logs/walk-generation.log`: 실제 생성, 다운로드·로딩 경고와 정상 종료·시간 기록.
- `docs/logs/gpu-memory.csv`, `docs/logs/generation-metrics.json`: GPU 샘플과 시간 집계.
- `docs/logs/motion-check.json`: NPZ와 BVH 수치·재가져오기 검사. 현재 SOMA77 출력의 `foot_contacts`는 `[90, 6]`이며 채널 순서는 이 JSON에 명시했다.
- `docs/logs/preview.log`, `docs/logs/bvh-preview.log`: 각각의 실제 브라우저 연결·재생 기록.
- `docs/logs/preview-check.json`: MP4 디코딩·길이·프레임 변화 검사.

인증 파일, 가중치, 패키지 캐시와 가상환경은 커밋 대상이 아니다. `.cache/`는 저장소 ignore 대상이다.
공유 로그는 터미널 진행 표시의 carriage return과 줄 끝 공백을 정리했다. 셸 스크립트는 `.gitattributes`로 LF 줄바꿈을 유지한다.

## 실제 사용한 재생·검사 방법

같은 WSL 환경에서 다음을 실행한다. 이 검사와 골격 뷰어는 Llama 가중치를 다시 로드하지 않는다:

```bash
/opt/deviant-kimodo/.venv/bin/python scripts/verify-walk.py
/opt/deviant-kimodo/.venv/bin/python scripts/preview-walk.py
# BVH를 직접 재생하려면 별도 터미널에서:
/opt/deviant-kimodo/.venv/bin/python scripts/preview-walk.py --bvh --port 7861
```

Windows 브라우저에서 `http://127.0.0.1:7860`은 NPZ, `http://127.0.0.1:7861`은 BVH다. Play와 Frame으로 재생·탐색하고 Export preview MP4로 영상과 프레임 비교 이미지를 저장한다. 두 포맷의 실제 재생을 확인했다. Blender 가져오기와 주인공 모션 이식은 다음 업무다.

골격 생성과 주인공 GLB 리깅·모션 이식은 별도 업무다. 현재 GLB는 수정하지 않았다.

## 공식 참고 자료

- [설치 및 모델 접근](https://research.nvidia.com/labs/sil/projects/kimodo/docs/getting_started/installation.html)
- [Kimodo 소스 및 CPU 텍스트 인코더](https://github.com/nv-tlabs/kimodo)
- [PyTorch CUDA 설치](https://pytorch.org/get-started/locally/)

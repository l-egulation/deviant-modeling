# Kimodo 갤럭시북 작업 인계

작성: 2026-10-14. 이 문서는 다른 컴퓨터의 작업자가 이어서 실행하기 위한 안내다. 설치와 모션 생성은 아직 검증하지 않았다.

## 1. 무엇을 만드는가

Dead Cells 제작 방식에서 아이디어를 얻어, **3D 캐릭터에 모션을 적용하고 낮은 해상도로 렌더링하여 게임용 도트 스프라이트를 만드는 것**이 최종 목적이다. 지금은 주인공 외형을 Tripo로 만든 단계다. 다음은 Kimodo로 자연스러운 동작을 생성하는 실험이다.

전체 흐름:

1. 이미지로 주인공 외형 정의 → Tripo로 3D 모델 생성: 현재 완료.
2. Kimodo로 텍스트에서 사람의 골격 모션 생성: 이번 작업.
3. Blender에서 캐릭터 정리, 뼈대와 피부 변형 설정, 모션 이식 및 보정: 이후 작업.
4. 정면·측면 등 게임 카메라 방향으로 렌더링, 도트 표현과 스프라이트 시트 제작: 이후 작업.

첫 무기는 검으로 정했다. 아직 검 모델은 없다. 첫 검증은 단순한 걷기로 하고, 검 공격은 기본 모션과 캐릭터 적용이 된 후 진행한다.

## 2. 어느 컴퓨터에서 실행해야 하나

사용자는 갤럭시북에서 맥북을 원격 조작하고 있었다. 지금까지의 프로젝트 파일은 맥북에 있다. **원격 화면으로 맥북에 명령을 내리면 실행과 GPU 사용도 맥북에서 이루어진다.** 이번 설치·생성 명령은 갤럭시북 Windows 또는 그 컴퓨터의 WSL 안에서 실행해야 한다.

목표 장비(사용자 제공):

| 항목 | 사양 |
|---|---|
| GPU | NVIDIA GeForce RTX 4050 Laptop GPU |
| GPU 전용 메모리 | 6GB |
| CPU | Intel Core i7-13700H |
| RAM | 32GB |
| 저장소 | 전체 954GB, 사진 당시 약 413GB 여유. 설치 전 재확인 |

현재 인계 문서를 작성한 장비는 Mac이다. Windows에서 실제 설치 성공, CUDA 작동, 생성 속도를 확인한 적은 없다.

## 3. 이번 작업의 범위와 완료 조건

우선 **Kimodo를 실행해서 3초 걷기 모션 1개를 만들고 눈으로 재생 확인**한다. 캐릭터 리깅을 먼저 끝낼 필요는 없다.

완료 조건:

- 갤럭시북 GPU를 PyTorch가 인식한다.
- CPU 텍스트 인코더 설정으로 모션 생성이 끝난다.
- `outputs/walk.npz`와 표준 T 포즈 기준 `outputs/walk.bvh`가 생성된다.
- 뷰어 또는 Blender에서 재생하여 사람이 걷는지, 관절 폭발·뒤집힘·심한 발 미끄러짐이 없는지 확인한다.
- 실제 환경에 맞는 재실행 파일(`run-walk.sh` 또는 `run-walk.ps1`)과 `SETUP_RESULT.md`를 남긴다.

골격만 재생됐으면 “Kimodo 모션 생성 성공”이라고 보고한다. 주인공에게 적용까지 됐다고 보고하면 안 된다.

## 4. 전달한 캐릭터와 외형 기준

`assets/ink-hero.glb`가 현재 사용할 모델이다. 기존 맥북 프로젝트의 오래된 `ink-hero.blend`와 `build_hero.py`는 초기 절차적 모델링 시도의 산출물이다. 현재 원본으로 쓰거나 그 스크립트로 다시 생성하지 않는다. 이 묶음에는 포함하지 않았다.

현재 디자인:

- 큰 머리와 짧은 팔다리의 작은 주인공.
- 검은 얼굴, 노란 주황색 세로 눈 두 개.
- 평범한 둥근 아이보리 후드. 길게 꺾여 늘어지는 모자 끝 없음.
- 몸에 비교적 붙는 짧은 아이보리 집업 재킷과 바지.
- 목을 감싼 청록색 스카프와 금색 장식. 긴 스카프 꼬리 없음.
- 검은 장갑과 부츠, 금색 발목 밴드.
- 뒤통수에는 얼굴이나 눈이 없어야 한다.

긴 코트·망토를 뺀 것은 옷 변형과 물리 처리 부담을 줄이기 위해서다. 옷 물리 기능이 구현된 상태는 아니다.

모델 상태를 실제 GLB 내부에서 확인했다:

| 항목 | 현재 값 |
|---|---|
| 파일 크기 | 60,308,452 bytes |
| 형식 | GLB 2.0, 헤더 길이와 실제 파일 길이 일치 |
| 메시 / 재질 | 1 / 1 |
| 스킨 / 애니메이션 | 0 / 0 |
| Tripo 화면 표시 | 약 191만 삼각형, 약 98만 정점 |

즉, **뼈대와 애니메이션이 없는 고밀도 외형 모델**이다. 후드 뒤와 소매의 울퉁불퉁한 표면 등은 후속 정리가 필요하다.

### 참고 이미지와 생성 경위

- `turnaround-fitted-3d.png`: 최신 4방향 디자인 시트.
- `tripo-front.png`, `tripo-left.png`, `tripo-right.png`, `tripo-back.png`: 방향별 참고 이미지.
- `tripo-result.png`, `tripo-result-back.png`: 실제 채택한 모델의 앞·뒤 화면.

4방향 입력에서는 앞뒤에 얼굴이 생기는 실패가 있었다. 최종 채택 모델은 **정면과 후면 이미지 두 장**으로 생성했고, 뒤로 회전해 얼굴이 없는 것을 확인했다. 실패 원인이 좌우 방향 때문인지 확정하지 않았다. 4방향 이미지는 형태 참고로 사용하고, 성공한 모델을 불필요하게 재생성하지 않는다.

최종 Tripo 작업: https://studio.tripo3d.ai/ko/workspace/generate/31212c3d-2fda-4727-a8c3-1243a3eccab9

## 5. 설치 전략

공식 저장소는 Linux 중심으로 개발·시험됐다. 따라서 **기존 환경을 확인한 뒤 WSL2 Ubuntu를 우선 검토**하는 것을 제안한다. 이는 이 프로젝트의 권장 선택이며 공식 필수 조건은 아니다. 이미 쓸 수 있는 Windows 환경이나 Docker가 있다면 상태를 확인하고 선택한다. Docker를 무조건 새로 설치하지 않는다.

먼저 실행 호스트, OS, `nvidia-smi`, WSL 상태, Python/Git, 디스크 여유 공간을 확인한다. CUDA가 안 보이면 그 원인을 먼저 해결한다. 드라이버나 CUDA Toolkit을 무조건 덮어쓰지 않는다.

독립 Python 환경을 만든다. 공식 설치 예시는 Python 3.10을 사용한다. 대상 환경에 맞는 GPU 지원 PyTorch를 [공식 설치 안내](https://pytorch.org/get-started/locally/)로 선택한 다음 Kimodo를 설치한다. 설치 버전과 가능하면 Git 커밋도 기록한다.

공식 패키지 설치 예시:

```sh
pip install git+https://github.com/nv-tlabs/kimodo.git
```

대화형 뷰어까지 필요하면:

```sh
pip install "kimodo[all] @ git+https://github.com/nv-tlabs/kimodo.git"
```

자세한 절차: [공식 설치 문서](https://research.nvidia.com/labs/sil/projects/kimodo/docs/getting_started/installation.html).

### Hugging Face 인증

텍스트 인코더는 접근 승인이 필요한 [Meta-Llama-3-8B-Instruct](https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct)를 사용한다. 사용자가 자신의 계정에서 접근 승인을 받고 로컬 터미널에서 `hf auth login`을 진행한다. 토큰을 대화에 붙이거나 전달 파일에 저장하지 않는다. 승인이 안 됐다면 사용자에게 필요한 동작을 정확히 알리고, 그동안 GPU와 환경 검증을 진행한다.

### 6GB VRAM에 맞는 핵심 설정

공식 README는 전체 GPU 실행 시 약 17GB VRAM, **`TEXT_ENCODER_DEVICE=cpu` 설정 시 3GB 미만**의 GPU 메모리 사용을 안내한다. RTX 4050 6GB에서 시도할 근거가 있지만 실제 실행 성공과 속도는 측정해야 한다. CPU 쪽 메모리 사용도 확인한다. ([공식 README](https://github.com/nv-tlabs/kimodo))

WSL/Linux:

```sh
export TEXT_ENCODER_DEVICE=cpu
```

Windows PowerShell:

```powershell
$env:TEXT_ENCODER_DEVICE = "cpu"
```

생성 명령과 데모를 시작하는 프로세스 모두에 이 설정이 적용돼야 한다. 초기 실행은 가중치를 내려받을 수 있으므로 다운로드와 실제 생성 시간을 구분한다.

## 6. 첫 실행 예시

**아래 명령은 공식 문서를 바탕으로 준비한 예시이며 이 장비에서 실행 검증한 스크립트가 아니다.** 작업자는 설치된 버전의 `kimodo_gen --help`와 지원 모델 이름을 확인한 뒤 실행한다. 기본 후보는 `Kimodo-SOMA-RP-v1.1`이다.

먼저 CUDA 확인:

```sh
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CUDA unavailable')"
```

WSL/Linux 예시:

```sh
export TEXT_ENCODER_DEVICE=cpu
mkdir -p outputs
kimodo_gen "A person walks forward at a relaxed pace with natural arm swing." --model Kimodo-SOMA-RP-v1.1 --duration 3.0 --num_samples 1 --seed 42 --bvh --bvh_standard_tpose --output outputs/walk
```

PowerShell 예시:

```powershell
$env:TEXT_ENCODER_DEVICE = "cpu"
New-Item -ItemType Directory -Force outputs | Out-Null
kimodo_gen "A person walks forward at a relaxed pace with natural arm swing." --model Kimodo-SOMA-RP-v1.1 --duration 3.0 --num_samples 1 --seed 42 --bvh --bvh_standard_tpose --output outputs/walk
```

`--output`은 파일 이름의 기본 부분이다. 한 샘플이면 `walk.npz`, `walk.bvh`가 된다. 표준 T 포즈 BVH는 후속 모션 이식을 위해 선택했다. 데모를 설치했다면 `kimodo_demo`로 열고 Load/Save → Motion에서 NPZ를 불러 재생한다. [공식 CLI 안내](https://research.nvidia.com/labs/sil/projects/kimodo/docs/user_guide/cli.html).

첫 실패 시 에러를 기록하고 해당 원인을 해결한다. 접근권한 문제, CUDA 문제, 메모리 부족을 구분한다. CPU 인코더가 적용됐는지 먼저 확인하고 불필요한 GPU 앱을 닫는다. 후처리를 끄거나 여러 설정을 동시에 바꾸는 것은 첫 대응으로 하지 않는다. 기본 걷기가 성공하기 전 여러 모션을 대량 생성하지 않는다.

## 7. Blender와 연결할 때

Kimodo는 임의의 GLB 외형을 넣으면 즉시 움직여 주는 도구가 아니다. 생성된 사람 골격 모션을 주인공의 뼈대로 옮기는 작업이 필요하다.

1. GLB를 Blender에 불러와 외형·텍스처를 확인한다.
2. 고밀도 메시를 애니메이션 가능한 구조로 정리한다. 단순 감면만으로 관절 변형이 좋아진다고 가정하지 않는다.
3. 팔·다리·몸통·머리 뼈대와 스킨 가중치를 설정한다.
4. Kimodo BVH를 불러와 관절을 대응시키고 모션을 이식한다.
5. 큰 머리와 짧은 팔다리에 맞춰 발 접지, 보폭, 손 위치, 몸통과 팔의 충돌을 보정한다.
6. 걷기의 제자리 이동 여부와 루프 연결을 게임 요구에 맞춘다. 생성 모션이 자동으로 완벽한 루프가 되는 것은 아니다.

SOMA BVH는 단위와 축을 확인해서 가져온다. 공식 출력 문서는 BVH 길이를 cm로 안내한다. GLB와 섞을 때 100배 크기 차이를 주의한다. [출력 형식 문서](https://research.nvidia.com/labs/sil/projects/kimodo/docs/user_guide/output_formats.html).

검 공격은 검 모델과 손에 붙이는 설정을 별도로 만든다. 프롬프트만으로 손잡이 접촉이나 전투 판정 타이밍까지 보장되지 않으므로 후속 보정이 필요하다.

## 8. 다음 모션 후보

걷기 성공 이후 한 개씩 평가한다. 다음은 의도 예시이며 생성 품질을 보장하는 주문이 아니다.

| 동작 | 프롬프트 예시 |
|---|---|
| 대기 | A person stands calmly with subtle breathing and small natural weight shifts. |
| 달리기 | A person runs forward at a steady pace with coordinated arm swings. |
| 검 동작 실험 | A person makes one controlled diagonal slash with a one-handed sword, then returns to a ready stance. |

검 모션은 실제 검이 자동 생성되는 것으로 해석하지 않는다. 우선 몸의 동작을 평가한다.

## 9. 남길 결과와 작업 원칙

`SETUP_RESULT.md`에는 실제 확인한 환경, 설치 방법, GPU 인식 결과, Kimodo 버전/커밋, 실행 명령, 생성 시간, 출력 경로, 재생 확인 내용, 남은 문제를 쓴다. 미측정 값은 미측정으로 표시한다. 가능하면 걷기 미리보기 영상도 남긴다.

Mac으로 돌아갈 때는 NPZ, BVH, 재실행 파일, 결과 문서와 미리보기를 전달하면 된다. 모델 캐시·가상환경·인증 토큰은 전달하지 않는다. 캐릭터를 수정했다면 수정된 Blender 파일도 전달한다.

- 파일명은 일정하게 유지하고 덮어쓴다. 사용자가 요청하기 전 v2/v3/v4로 분리하지 않는다.
- 사용자 목표와 무관한 Tripo 재생성, 유료 API 호출은 하지 않는다.
- 사용자가 직접 해야 하는 인증·재부팅 같은 단계만 구체적으로 알린다.
- 실제 성공한 것과 예정된 작업을 구분한다.
- 코드와 모델 가중치의 라이선스는 서로 다르다. SOMA 계열을 우선 사용하고 배포 전 사용하는 가중치의 조건을 확인한다. 저장소 코드가 Apache 2.0이라고 모든 모델에 동일하게 적용하지 않는다.

## 10. 전달 파일

이 폴더의 루트의 `START-HERE.md`를 새 작업자에게 전달하면 된다. `assets/`에는 현재 모델과 참고 이미지가 있다. `assets/SHA256SUMS.txt`는 파일 전달 손상을 확인하기 위한 체크섬이다. 설치된 Kimodo, 생성된 모션, 인증 정보는 이 묶음에 포함되어 있지 않다.

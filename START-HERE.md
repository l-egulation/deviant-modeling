# 갤럭시북 Kimodo 첫 실행 절차

> 최신 원본 변경: 사용자 승인으로 현재 기본 달리기는 `assets/mixamo-running.fbx`입니다. 전용 골격은 그대로이며 `apply-pixel-run.py`가 해부학적 축 변환을 수행합니다. [PIXEL_RUN.md](docs/PIXEL_RUN.md) 최신 절을 읽으세요. 아래 Kimodo 입력 안내는 이전 기록입니다.

> 최신 인계: [PIXEL_RUN.md](docs/PIXEL_RUN.md)를 먼저 읽습니다. `pixel-run-source.bvh`가 선택한 Kimodo 원본, `pixel-run.blend`가 전용 골격 적용본, `pixel-run-cloth.blend`가 의상 베이크입니다. 비교 영상은 `outputs/pixel-run-comparison.mp4`. 아래는 이전 단계 기록입니다.

> 현재 작업(2026-10-23): `outputs/tripo-pixel-rig.blend`와 [전용 골격 문서](docs/CHARACTER_RIG.md)를 먼저 읽습니다. 현재 모델의 골격 길이는 고정했고, 소매/로브 연결 정리와 121프레임 관절 시험을 통과했습니다. 다음은 Kimodo 달리기 이식과 해당 동작에서의 재검증입니다. 아래는 최초 설치/옛 모델의 기록입니다.

> 2026-10-16 최신: A 모델 달리기의 팔꿈치를 약 111~122°로 펴고, 높이 떨림 지표를 약 83% 줄였습니다. 기존 발목 위치를 유지하는 고정 길이 하체 보정을 포함합니다. 원본 FBX·모델 외형은 그대로이며 발 미끄러짐·국소 의상 접힘은 남아 있습니다. docs/MIXAMO_RUN.md 최신 절 참조.

2026-10-14: 아래 첫 실행 업무의 3초 걷기 생성·NPZ/BVH 재생 검증을 완료했습니다. 결과와 재실행 방법은 [SETUP_RESULT.md](docs/SETUP_RESULT.md), 다음 업무는 [STATUS.md](STATUS.md)를 확인합니다. 아래 절차는 재현용으로 유지합니다.

같은 날 사용자 후속 요청으로 캐릭터 첫 몸통 리깅·걷기 이식도 진행했습니다. 적용본과 재실행은 [HERO_WALK.md](docs/HERO_WALK.md)를 확인합니다. 현재 편집 파일은 `outputs/hero-walk.blend`입니다.

2026-10-15: 게임 기본 이동용 달리기를 별도로 생성·적용했습니다. 현재 달리기 편집본은 `outputs/hero-run.blend`이며, 생성·반복 보정·검증·재실행은 [RUN_RESULT.md](docs/RUN_RESULT.md)를 확인합니다. 기존 걷기 파일도 유지합니다.

## 작업 브랜치

최신 재작업(2026-10-15): 사용자가 팔·다리를 벌린 변형용 모델의 재제작을 요청했습니다. 거절된 절차적 시안은 `outputs/hero-model.blend`이며, 후드·얼굴·색감은 유지하고 몸통·소매·하체는 새 메시입니다. 4초 관절 시험이 포함되며 Kimodo 달리기 클립과 구분합니다. 모델 재현과 수치 검사는 `docs/SIDE_REVIEW.md`의 최신 절을 읽습니다. 이전 `hero-run.blend`의 가중치와 팔 고정 보정을 새 모델에 덮어쓰지 않습니다.

`work/kimodo-setup`을 사용합니다. 저장소를 복제한 뒤 이 브랜치로 전환하고 해당 폴더를 로컬 Codex에서 엽니다. main에는 최초 인계 자료가 있습니다.

## 작업자에게 전달할 지시

README.md, AGENTS.md, STATUS.md와 docs/KIMODO_HANDOFF.md를 읽고 이 갤럭시북에서 Kimodo 설치와 첫 모션 생성 검증을 진행해 주세요.

1. Windows/WSL, GPU, 메모리, 저장 공간과 기존 개발 환경을 확인합니다. 목표 장비는 RTX 4050 Laptop 6GB / RAM 32GB / i7-13700H입니다.
2. 적절한 독립 환경을 선택하고 GPU 지원 PyTorch와 Kimodo를 설치합니다. WSL2 Ubuntu를 우선 검토하되 기존 환경을 고려합니다.
3. Hugging Face 모델 접근 승인과 로컬 로그인이 필요하면 사용자가 해야 하는 절차를 안내합니다.
4. TEXT_ENCODER_DEVICE=cpu를 적용하여 3초 걷기, 한 샘플, seed 42로 시작합니다. 공식 모델·옵션을 현재 설치 버전에서 확인합니다.
5. outputs/walk.npz와 표준 T 포즈 기준 outputs/walk.bvh를 생성하고 실제 재생합니다.
6. 실제 환경에 맞는 scripts/run-walk.sh 또는 scripts/run-walk.ps1을 작성합니다. 경로와 환경 활성화 방법을 명시합니다.
7. docs/SETUP_RESULT.md에 버전, 실행 명령, 시간, 성공/실패와 재생 확인을 기록하고 STATUS.md를 갱신합니다.
8. 검증한 코드·문서·선별한 모션 결과를 이 브랜치에 커밋하고 push하여 맥에서 받을 수 있게 합니다. 인증 정보와 캐시는 제외합니다.

처음부터 캐릭터를 리깅하거나 Tripo를 재실행하지 않습니다. 현재 캐릭터는 뼈대가 없습니다. 골격 걷기 검증 후 Blender 적용으로 넘어갑니다.

## 완료 기준

- 실제 CUDA GPU 인식 및 Kimodo 생성 성공.
- NPZ/BVH 출력 존재와 재생 확인.
- 재실행 파일과 환경 결과 문서 작성.
- 다음 작업자가 확인할 브랜치·커밋과 결과 경로 보고.

사용자 접근 승인 등 외부 조건으로 막히면 정확한 원인을 기록하고 독립적으로 가능한 준비를 마칩니다. 이 문서는 작업 지시이며 설치 완료 보고가 아닙니다.

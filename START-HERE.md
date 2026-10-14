# 다음 업무: 갤럭시북 Kimodo 첫 실행

## 작업 브랜치

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

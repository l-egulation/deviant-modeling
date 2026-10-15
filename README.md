# Deviant Modeling

Tripo로 만든 주인공에 Kimodo 모션을 적용하고, Blender에서 게임용 도트 스프라이트로 렌더링하는 프로젝트입니다.

## 시작하기

- **갤럭시북 작업자:** [START-HERE.md](START-HERE.md)를 읽고 Kimodo 첫 걷기 검증을 진행합니다.
- **현재 상태:** [STATUS.md](STATUS.md)
- **상세 배경과 설치 예시:** [Kimodo 인계 문서](docs/KIMODO_HANDOFF.md)
- **공통 작업 지침:** [AGENTS.md](AGENTS.md)
- **컴퓨터 간 파일 전달:** [동기화 안내](docs/WORKFLOW.md)

## 역할

| 도구·장소 | 담당 |
|---|---|
| Tripo | 참고 이미지에서 캐릭터 외형 생성 |
| Kimodo / 갤럭시북 RTX 4050 6GB | 프롬프트에서 골격 모션 생성 |
| Blender / 맥 | 메시 정리, 리깅, 모션 이식, 보정, 렌더링 |
| GitHub | 코드·문서·선별한 모델 및 모션 결과 공유와 변경 이력 |
| Codex 클라우드(선택) | 설치 스크립트와 도구 작성, 코드 검토·수정, 가능한 검증 |

GitHub에 저장한 결과를 각 컴퓨터에서 받습니다. Codex 클라우드 작업 공간에만 남은 변경은 다른 컴퓨터에 자동으로 전달되지 않습니다. 클라우드는 필수 단계가 아닙니다.

## 현재 캐릭터

![주인공 미리보기](assets/tripo-result.png)

현재 원본은 [ink-hero.glb](assets/ink-hero.glb)입니다. 아이보리 둥근 후드와 짧은 집업, 청록색 스카프, 검은 얼굴과 금색 눈을 가진 작은 캐릭터입니다. 망토와 긴 스카프 꼬리는 제거했습니다. 첫 무기는 검을 계획하고 있습니다.

GLB는 약 60MB의 고밀도 메시이며 뼈대와 애니메이션은 없습니다. Kimodo 골격 모션 생성과 주인공에 적용하는 작업은 별도 단계입니다. 이전 절차적 Blender 모델은 이 저장소에 포함하지 않습니다.

## 당장 할 일

게임 기본 이동용으로 [달리기 생성·적용](docs/RUN_RESULT.md)도 진행했습니다. [달리기 미리보기](outputs/hero-run-preview.mp4), [편집용 Blend](outputs/hero-run.blend), [달리기 GLB](outputs/hero-run.glb)를 사용합니다. 캐릭터 크기는 기존 걷기와 같고, 달리기의 공중 구간과 반복 경계를 별도로 처리했습니다.

`work/kimodo-setup`에서 갤럭시북의 CPU 텍스트 인코더·RTX 4050으로 3초 걷기 골격 생성과 NPZ/BVH 실제 재생 검증을 완료했습니다. [실행 결과와 재실행 방법](docs/SETUP_RESULT.md), [3초 미리보기](outputs/walk-preview.mp4)를 확인할 수 있습니다.

갤럭시북 Blender에서 캐릭터 비율의 몸통 리그와 걷기 첫 적용본도 만들었습니다. [캐릭터 걷기 영상](outputs/hero-walk-preview.mp4), [작업 기록](docs/HERO_WALK.md), [편집용 Blend](outputs/hero-walk.blend), [애니메이션 GLB](outputs/hero-walk.glb)를 확인할 수 있습니다. 원본 `assets/ink-hero.glb`는 보존했습니다. 다음은 의상·발 접촉과 반복 동작 보정 후 카메라 방향별 2D 렌더링을 비교하고 에테르 AI의 도트 변환을 검토하는 작업입니다.

## 파일 관리

파일명은 유지하고 변경 이력은 Git에 남깁니다. 가상환경·가중치 캐시·토큰·설치 프로그램은 올리지 않습니다. 현재 GLB는 초기 전달 편의를 위해 일반 Git으로 관리합니다. 큰 바이너리를 반복 수정하기 전 Git LFS 또는 별도 아티팩트 저장소로 전환을 검토합니다. 본 프로젝트 전체에 별도 오픈소스 라이선스를 선언한 상태는 아닙니다. Kimodo 및 각 모델의 이용 조건은 각각 확인해야 합니다.

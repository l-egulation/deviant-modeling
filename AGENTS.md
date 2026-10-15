# 작업 지침

> 2026-10-15 최신: 사용자 요청으로 Mixamo의 기존 Running With Intention을 실제 Tripo 캐릭터에 적용했습니다. 검토본은 outputs/hero-mixamo-run.blend / .glb / -preview.mp4입니다. 원본 30fps 박자는 유지하고 캐릭터 비율 매핑과 접지를 보정했습니다. Kimodo 생성본과 수작업 반복본은 이번 모션에 사용하지 않습니다. docs/MIXAMO_RUN.md 참조.

- 2026-10-15 사용자 명시 수정: 달리기 피드백은 Kimodo 프롬프트에 반영해 새 생성 후보를 뽑는다. animate-run-keyposes.py의 수작업 반복본(0e20e99)은 거절됐으며 다시 적용하지 않는다. Blender는 비율 매핑·필요한 접지 및 의상 보정만 한다. 생성 원본과 적용본의 차이를 구분해 보고한다.
- 먼저 README.md, STATUS.md, START-HERE.md를 읽는다.
- 목적은 Tripo 외형 → Kimodo 골격 모션 → Blender 리깅·모션 이식 → 도트 스프라이트 제작이다.
- 현재 원본은 assets/ink-hero.glb. 기존 맥의 build_hero.py나 옛 blend를 현재 원본으로 쓰지 않는다.
- 2026-10-15 사용자 승인 재작업: 후드·얼굴·색감은 유지하고 몸통·소매·하체를 새로 제작한다. 거절된 절차적 시안은 outputs/hero-model.blend이며 수평 T자 팔·약 23도 벌린 다리와 18뼈 리그를 사용한다. assets/ink-hero.glb는 디자인 원본으로 보존한다. hero-run.blend는 이전 모델의 달리기 검토본이다.
- 새 모델에는 기존 A포즈 보정·손 경로 고정·쇄골 회전을 상쇄하는 팔 보정을 그대로 적용하지 않는다. Kimodo 재매핑 시 LeftClavicle/RightClavicle은 원본 BVH의 LeftShoulder/RightShoulder 채널을 확인한다. 관절 시험 통과와 달리기 미술 검증을 구분한다.
- 이번 갤럭시북 작업은 Kimodo 설치와 3초 걷기 생성·재생 검증이다. 캐릭터 리깅 완료와 혼동하지 않는다.
- 실행 호스트를 확인한다. Mac 원격 세션에서 Windows GPU를 사용할 수 있다고 가정하지 않는다.
- RTX 4050 6GB 환경에서는 TEXT_ENCODER_DEVICE=cpu로 시작한다. 문서 예시는 설치된 버전과 공식 안내로 검증한다.
- 인증은 사용자가 로컬에서 한다. 토큰, .env, 계정 캐시, 모델 가중치, 가상환경을 커밋하지 않는다.
- 파일명은 유지하고 덮어쓴다. 사용자가 요구하기 전 v2/v3 폴더를 만들지 않는다.
- 작업 전 git status와 원격 변경을 확인한다. 사용자 변경을 덮어쓰거나 강제 push하지 않는다.
- STATUS.md에 실제 완료 사항, 실행 환경, 결과 경로, 다음 업무와 미해결 문제를 갱신한다. 예정 작업을 성공으로 기록하지 않는다.
- 같은 바이너리를 여러 컴퓨터에서 동시에 편집하지 않는다. 넘겨줄 때 커밋과 브랜치를 명시한다.
- 클라우드 환경 준비 중 Kimodo 전체 가중치 다운로드나 GPU 검증을 필수 설치 단계로 두지 않는다. 코드·문서 작업에 필요한 최소 환경부터 준비한다.

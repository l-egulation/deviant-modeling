# Mixamo 기본 달리기 원본

2026-10-15. 사용자가 기존 사람 달리기 모션을 불러와 먼저 확인하도록 요청했습니다. 사용자 Adobe 로그인 후 Mixamo에서 Running, 설명 Running With Intention을 기본 휴머노이드 모델에 선택했습니다.

- 원본 사이트: https://www.mixamo.com/#/?page=1&query=running
- 설정: Overdrive 50, Character Arm-Space 50, 전체 구간, Mirror off, In Place off. 모델 업로드나 새 자동 리깅은 하지 않았습니다.
- 다운로드: FBX Binary, With Skin, 30fps, Keyframe Reduction none.
- assets/mixamo-running.fbx는 다운로드한 Running.fbx의 그대로인 로컬 복사본입니다.
- outputs/mixamo-running.blend는 원본 FBX를 Blender에 불러온 재생용 장면입니다. 조명·바닥·카메라만 추가하며 관절 포즈·속도를 수정하지 않습니다.
- outputs/mixamo-running-preview.gif / .mp4는 기본 모델의 측면·사선 비교입니다. MP4는 같은 다운로드 한 주기를 세 번 반복해 보기 쉽게 구성합니다. 원본 한 주기의 속도는 유지합니다.
- 이후 사용자 요청으로 실제 Tripo 캐릭터에 적용했습니다. 아래 적용 결과를 확인합니다.

프레임·재생 검사 결과: docs/logs/mixamo-running.json. 재현은 Blender scripts/preview-mixamo-run.py 실행 후 Kimodo Python의 scripts/encode-mixamo-run.py입니다. 원본 출처와 파일을 Kimodo 생성 결과와 구분합니다.

## Tripo 캐릭터 적용

- 입력 외형: assets/ink-hero-tpose.glb. 기존 tripo-run.blend에서 메시와 18뼈 리그·가중치만 가져오고 기존 애니메이션은 제거합니다.
- 출력: outputs/hero-mixamo-run.blend / .glb / -preview.gif / -preview.mp4 / -contact-sheet.png.
- 원본 22프레임을 30fps 그대로 반복하여 90프레임·3초로 구성합니다. 마지막 프레임이 완전한 주기 끝은 아니므로 3초 영상 자체의 무한 루프 연결을 보장하지 않습니다.
- 원본 뼈 회전 변화와 어깨 움직임을 이식합니다. 캐릭터의 메시 기본 정점과 뼈 길이는 유지하며 다리 길이 비율 0.30182로 이동량을 맞춥니다. 벌린 다리의 기본 자세 차이와 발 접촉·공중 발목을 보정합니다. 새 달리기 포즈를 수작업으로 만들지 않습니다.
- 검증: 90프레임 뼈 스케일 오차 0, 메시 기본 정점 차이 0, 바닥 침범 약 0.00014mm 이하. GLB 재수입 자세 범위 오차 약 0.00048mm. 접지 보정 전후 상체 회전 차이 0.
- 미술 한계: 짧은 다리·큰 후드·두꺼운 소매 때문에 사람 원본과 실루엣은 다릅니다. 관절 주변 옷의 압축·늘어짐은 남아 있으며 구조 검사 통과를 최종 미술 승인으로 간주하지 않습니다.

재현(WSL, 저장소 폴더):

```sh
/opt/deviant-blender/blender-4.5.13-linux-x64/blender -b --python-exit-code 1 --python scripts/apply-mixamo-run.py
RUN_STEM=hero-mixamo-run /opt/deviant-blender/blender-4.5.13-linux-x64/blender -b --python-exit-code 1 --python scripts/verify-tripo-run.py
RUN_STEM=hero-mixamo-run FULL_RENDER=1 /opt/deviant-blender/blender-4.5.13-linux-x64/blender -b --python-exit-code 1 --python scripts/render-tripo-run.py
RUN_STEM=hero-mixamo-run /opt/deviant-kimodo/.venv/bin/python scripts/encode-tripo-run.py
```

기록은 docs/logs/hero-mixamo-run-*에 저장합니다. 원본 FBX는 Mixamo에서 위 설정으로 받은 로컬 입력입니다. 계정 화면과 인증 정보는 커밋하지 않습니다.

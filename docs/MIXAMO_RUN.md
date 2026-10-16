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

## 2026-10-16 — 팔꿈치 펴기·높이 떨림 수정

사용자가 팔꿈치를 둔각으로 펴고 지진처럼 보이는 떨림을 줄이도록 승인했습니다. 현재 hero-mixamo-run.*는 이 수정본이며 원본 FBX·A 모델 형상은 그대로입니다. 아래 원본 각도 보존 설명은 수정 이전 이력입니다.

- 실제 팔꿈치 안쪽 각도: 59.07~105.99° → 110.73~122.35°. 앞뒤 스윙에 따라 연속적으로 달라집니다. 어깨·상완·몸통·머리·발의 세계 회전 차이 0도 확인. 팔꿈치 이후 회전은 의도적으로 원본과 달라집니다.
- 떨림 원인: 매 프레임 변형 메시의 최저점에 맞춰 몸 전체를 올리고 내린 기존 보정. 높이 2차 차분 최대 0.06524m/frame² → 0.01116m/frame², 약 82.9% 감소. 높이 범위 0.09286m → 0.06381m. 카메라는 등속 전진만 추적합니다.
- 22프레임 주기의 저주파 높이 곡선으로 보정했습니다. 높이만 부드럽게 만들면 발이 뜨므로, 고정 길이 두 뼈 IK로 기존 발목 세계 위치를 유지했습니다. 발목 위치 최대 차이 약 5e-7m, 뼈 크기 변화 0. 무릎 각도는 원본과 달라집니다. 바닥 최소 0m.
- 팔꿈치 소매 가중치 전환 폭을 넓혔습니다. 전체 90프레임 최대 모서리 늘어짐은 3.05배에서 약 2.50배로 감소했습니다. 기본 메시 정점 이동 0, 텍스처 유지. 소매·어깨/골반 접힘을 모두 해결했다는 뜻은 아닙니다.
- MP4는 90프레임·30fps·3초이며, GIF는 22프레임 네 주기인 88프레임만 사용해 끝에서 다른 위상으로 돌아가는 문제를 줄입니다. 원본 한 주기 안의 경계 품질과 발 미끄러짐은 최종 검토 대상입니다.
- 발목 위치를 보존하므로 기존 발 미끄러짐은 남습니다. 새 팔 자세가 몸통/장갑과 겹치는 일부 실루엣도 최종 미술 검토가 필요합니다.

재현: rig-proportion-model.py → MIXAMO_TARGET_RIG=outputs/hero-proportion-rig.blend apply-mixamo-run.py → 수정 전 blend를 .cache/run-before-polish.blend로 복사 → polish-mixamo-run.py → verify-mixamo-polish.py / 기존 verify-tripo-run.py → RUN_STEM=hero-mixamo-run FULL_RENDER=1 render-tripo-run.py → RUN_STEM=hero-mixamo-run RUN_POLISHED=1 encode-tripo-run.py. polish 스크립트는 이미 수정된 파일에 이중 실행하지 못하도록 검사합니다.

측정 기록: docs/logs/hero-mixamo-polish.json, hero-mixamo-polish-validation.json. 이전 단계의 rig 보존 검사는 보정 전 결과이며 최종 자세 검사는 polish-validation과 구분합니다. 골격 비교는 원본 / 수정 전 A 모델 / 현재 수정본으로 갱신했습니다.


## 2026-10-16 — 승인된 A 모델에 연결

현재 hero-mixamo-run.*는 새 A안 모델 적용본입니다. 원본 모델은 outputs/hero-proportion-model.glb, 골격 기준 장면은 outputs/hero-proportion-rig.blend입니다. 이전 짧은 모델의 결과는 d6c1355 이전 이력으로 확인합니다.

- Tripo 메시/색상/비율은 변경하지 않고 쇄골을 포함한 18뼈를 새 관절 위치에 배치했습니다. 관절 길이는 캐릭터에 맞췄으며 모션의 뼈 스케일로 팔다리를 늘리지 않습니다.
- Mixamo Running With Intention의 22프레임/30fps 원본을 기존과 같은 속도로 90프레임에 반복했습니다. 새 Kimodo 추론이나 수작업 자세 생성은 하지 않았습니다.
- 첫 A 리깅에서 팔의 위쪽 정점이 머리·몸통 가중치에 섞여 장갑/소매가 늘어났습니다. 메시 높이 분포와 모서리 영향 기록으로 원인을 확인하고 팔 관절 높이와 팔 분류의 위쪽 경계를 수정했습니다. 처음 잘못 연결된 영상은 채택하지 않습니다.
- 원본 팔다리 방향 최대 오차 0도, 팔꿈치·무릎 굽힘 차이 최대 약 0.000096도. 기본 메시 정점 차이 0, 뼈 스케일 차이 0. 90프레임 바닥 최소 0m, GLB 재수입 범위 오차 약 0.00036mm. 가중치 합 오차 약 8.94e-8.
- 주요 정면/측면 자세에서 장갑 늘어짐이 해소됐음을 확인했습니다. 이 검사는 최종 의상 미술 승인과 구분합니다. 발 미끄러짐, 겨드랑이·골반의 국소 접힘과 캐릭터 비율에 따른 실루엣 차이는 남습니다. 원본 모션을 유지하기 위해 발 IK/발목 제한/보폭 축소는 추가하지 않았습니다.
- 전체 90프레임에서 2mm 이상 모서리 최대 늘어짐 3.050배. 이는 국소 의상 변형이 남았다는 뜻이며 품질 통과 수치로 사용하지 않습니다.
- 카메라는 골반 상하 움직임을 추적하지 않고 등속 전진만 따라갑니다. 바닥 여유를 맞추기 위한 몸 전체 높이 이동은 적용됩니다.
- 골격 비교의 previous 열은 이번 작업의 첫 A 연결 시도이며 target은 팔 영향 분류를 수정한 결과입니다. 아래 예전 비교 설명과 구분합니다.

재현: Blender로 scripts/rig-proportion-model.py 실행 → MIXAMO_TARGET_RIG=outputs/hero-proportion-rig.blend scripts/apply-mixamo-run.py 실행 → 아래 기존 검증/렌더/인코딩 명령. 원본 GLB와 Mixamo FBX는 수정하지 않습니다.


## Tripo 캐릭터 적용 — 원본 관절 방향 보존

2026-10-15 사용자 피드백에 따라 기존 다리 보정 경로를 제거했습니다.

### 확인된 원인

이전 5f36695 적용본은 사람 원본을 짧은 다리에 이식한 뒤, 기존 hero_feet.plant_feet로 발 위치를 다시 풀었습니다. 이 과정은 발의 앞뒤 목표를 70%로 줄이고, 접지 중 발 위치·회전과 무릎 방향을 다시 계산하며, 공중 발목 각도도 제한했습니다. 따라서 원본 박자가 같아도 원본 다리 포즈는 달랐습니다. 실제 90프레임 비교에서 무릎 굽힘 차이는 왼쪽 최대 95.82도·오른쪽 99.37도였습니다. 팔꿈치 굽힘 차이는 0.001도 미만이므로 같은 원인으로 팔까지 진단하지 않습니다.

### 현재 방식

- 입력: assets/mixamo-running.fbx. 외형·18뼈·가중치는 기존 outputs/tripo-run.blend에서 읽고 애니메이션을 제거합니다. 실제 외형은 assets/ink-hero-tpose.glb입니다.
- 원본 각 뼈가 향하는 방향을 캐릭터의 기본 뼈 좌표축에 맞춰 전달합니다. 팔다리 길이는 이미 캐릭터 체형에 맞춘 길이를 사용합니다. 메시 기본 정점·몸 부위 크기·뼈 길이를 추가로 변경하지 않습니다.
- 팔꿈치·무릎의 굽힘과 팔·다리·쇄골의 공간 방향을 원본과 비교하는 회귀 검사를 실행합니다. 최대 방향 오차 0도(Blender float 정밀도), 굽힘 오차 약 0.000108도입니다. 허용 기준은 각각 0.1도입니다.
- 기존 보폭 70%·다리 IK·고정 무릎 방향·발목 제한을 제거했습니다. 수작업 달리기 포즈나 Kimodo 재생성은 사용하지 않습니다.
- 접지는 관절을 바꾸지 않고 캐릭터 전체 높이만 옮깁니다. 원본 사람 메시의 바닥 여유 높이를 다리 길이 비율 0.30182로 변환하여 맞춥니다. 발을 지면의 한 점에 고정하지 않으므로 수평 발 미끄러짐은 후속 검토 사항입니다.
- 원본 22프레임·30fps를 90프레임·3초로 반복합니다. 마지막 프레임은 완전한 주기 끝이 아니므로 3초 영상 자체가 무한 루프로 연결되지는 않습니다.

### 결과와 검증

- outputs/hero-mixamo-run.blend / .glb / -preview.gif / -preview.mp4 / -contact-sheet.png: 현재 캐릭터 적용본.
- outputs/hero-mixamo-run-comparison.gif / .mp4: 왼쪽 원본 사람, 오른쪽 현재 캐릭터의 같은 프레임 재생입니다. 생성에는 이전 원본 렌더 캐시 .cache/mixamo-run/side-000..021.png가 필요합니다. 캐시가 없으면 preview-mixamo-run.py를 먼저 실행합니다.
- outputs/hero-mixamo-run-skeleton.gif / .png: 왼쪽 원본, 가운데 수정 전 5f36695, 오른쪽 현재 캐릭터 비율. 측면 투영·골반 중심 고정이며 전체 높이만 화면에 맞춰 표시합니다. 실제 관절 위치를 투영한 비교로, 사람과 캐릭터의 팔다리 비율 차이도 보입니다.
- docs/logs/hero-mixamo-run-skeleton.json: 비교에 사용한 실제 90프레임 뼈 머리·끝점. 이전 결과는 실행 시작 당시 적용본을 읽은 값이므로 재실행하면 '이전' 대상도 바뀝니다. 이번 커밋 데이터의 이전 대상은 5f36695입니다.
- 90프레임 검사: 뼈 스케일 오차 0, 메시 기본 정점 차이 0, 바닥 침범 없음. GLB 재수입 자세 범위 오차 약 0.00036mm.
- 전체 90프레임에서 2mm 이상 메시 모서리 최대 늘어짐은 이전 3.79배에서 현재 2.73배로 줄었지만 국소 의상 변형은 남습니다.
- 골격 보존 검사와 최종 미술 승인은 구분합니다. 짧은 팔다리·큰 후드·장갑이 만드는 실루엣 차이, 소매·골반 옷 변형, 발 미끄러짐 검토는 남아 있습니다. 옷을 바꾸기 위해 모션을 다시 왜곡하지 않습니다.

### 재현

WSL 저장소 폴더에서:

```sh
/opt/deviant-blender/blender-4.5.13-linux-x64/blender -b --python-exit-code 1 --python scripts/apply-mixamo-run.py
/opt/deviant-kimodo/.venv/bin/python scripts/compare-mixamo-skeleton.py
RUN_STEM=hero-mixamo-run /opt/deviant-blender/blender-4.5.13-linux-x64/blender -b --python-exit-code 1 --python scripts/verify-tripo-run.py
RUN_STEM=hero-mixamo-run FULL_RENDER=1 /opt/deviant-blender/blender-4.5.13-linux-x64/blender -b --python-exit-code 1 --python scripts/render-tripo-run.py
RUN_STEM=hero-mixamo-run /opt/deviant-kimodo/.venv/bin/python scripts/encode-tripo-run.py
```

실행 기록은 docs/logs/hero-mixamo-run-*입니다. 원본 FBX는 Mixamo에서 위 설정으로 받은 입력입니다. 계정 화면과 인증 정보는 커밋하지 않습니다.

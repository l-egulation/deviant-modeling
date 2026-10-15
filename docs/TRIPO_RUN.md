# 새 Tripo 모델의 Kimodo 달리기

## 최신: 피드백을 반영해 Kimodo 재생성

2026-10-15. 사용자는 관절을 직접 만들고 연결한 작업을 거절하고 Kimodo를 다시 실행해 새 모션을 생성하도록 명시했습니다. 수작업 반복본 0e20e99와 animate-run-keyposes.py는 채택되지 않은 이력입니다.

### 실제 실행

로컬 RTX 4050, CPU 텍스트 인코더, 허용된 기존 인증·캐시로 Kimodo-SOMA-RP-v1.1을 실행했습니다. seed 107, num_samples 2, duration 3.0, 표준 T포즈 BVH 내보내기. 최종 실행 종료 0, 141초(모델 로딩 포함). 명령과 정확한 프롬프트는 scripts/generate-tripo-run.sh, 실행 로그는 docs/logs/tripo-run-generation.log입니다.

첫 시도는 문장 7개를 Kimodo가 연속 구간으로 해석해 630프레임을 생성했습니다. 이를 채택하지 않고 모든 조건을 쉼표로 연결한 한 문장으로 다시 실행해 두 후보 모두 90프레임임을 확인했습니다. 첫 실패 출력은 .cache에만 두었습니다.

두 후보는 빠른 전진, 약한 전경, 자연스러운 어깨·골반 교대, 허리 높이의 손, 앞뒤 보폭과 공중 구간을 한 프롬프트로 요청했습니다. 첫 후보가 손 위치를 낮게 유지하면서 두 번째보다 팔 앞뒤 교대와 보폭이 명확해 선택했습니다. 두 후보 모두 손이 가슴보다 높은 프레임 비율은 0입니다. 생성 모델이 모든 미술 조건을 완벽히 만족했다고 주장하지 않습니다. 후보 수치는 tripo-run-candidates.json, 원본 골격 비교는 outputs/kimodo-run-candidates.png / .gif.

### 원본과 적용본

- outputs/tripo-run-source.npz / .bvh: 선택한 single_00의 실제 생성 파일을 그대로 복사. 자세 수정·배속·주기 연결·네 자세 보간 없음.
- outputs/tripo-run-contact.npz: 원본과 분리한 접지 분류·발 여유 메타데이터. 생성 원본은 수정하지 않음.
- outputs/tripo-run.blend / .glb: Tripo 비율 리그에 생성 회전 이식. 팔·어깨를 직접 포즈하지 않음. 이전의 머리를 가슴에 묶는 보정도 제거해 원본 머리 움직임 전달. 신발 접촉·관통을 줄이기 위한 고정 길이 두 뼈 IK와 공중 발목 제한은 적용.
- outputs/tripo-run-preview.mp4 / .gif: 같은 30fps의 생성 원본 3초를 적용한 측면 영상. 수작업으로 만든 0.6초 반복이나 배속을 사용하지 않음. 원본 시작·끝 자세는 다르므로 GIF 반복에서 보이는 경계는 아직 매끈한 게임 루프가 아님.

### 확인과 한계

발 접촉 보정 전후 상체 회전 차이 0, 기본 메시 위치 변화 0. 공중 20/90프레임 유지, 최대 발목 회전 약 41.58도, 발목 목표 오차 약 2.4e-7m. 구조 검사에서 뼈 크기 변화 0, 바닥 최소 약 -1.8e-7m, GLB 왕복 범위 오차 약 2.5e-7m. 전체 렌더의 국소 모서리 늘어짐 최대는 약 3.42배로 남아 있습니다. MP4 90프레임·30fps·3초 디코딩도 확인했습니다. 이 수치는 의상 접힘·충돌·미술 품질 통과를 뜻하지 않습니다.

필요한 발 접촉 보정은 생성된 하체의 발 궤적과 일부 관절 회전을 바꿉니다. 이를 완전히 무보정인 캐릭터 결과라고 부르지 않습니다. 골격 생성 원본은 별도 보존하며 팔·몸통의 자연스러움은 원본 비교로 평가합니다.

### 재현

새 생성은 bash scripts/generate-tripo-run.sh → Kimodo Python으로 scripts/review-generated-runs.py → scripts/select-generated-run.py 0. 저장된 원본 적용만 다시 할 때는 Blender 4.5.13으로 scripts/rig-tripo-run.py → scripts/verify-tripo-run.py → FULL_RENDER=1 scripts/render-tripo-run.py → Kimodo Python scripts/encode-tripo-run.py. 기본 입력은 현재 보존한 tripo-run-source.bvh와 tripo-run-contact.npz입니다. 수작업 포즈 스크립트를 실행하지 않습니다.

## 이전: 사용자가 거절한 수작업 반복 모션

2026-10-15 사용자 승인 방향으로 낮은 손 위치·전경·팔다리 분리를 유지하며 한 주기를 직접 연결했습니다. 당시 tripo-run.blend / .glb / preview.mp4 / preview.gif는 이 수작업 보정본이었고 사용자가 거절했습니다. 현재 파일은 아래 최신 Kimodo 재생성 결과로 교체했습니다. 새 Kimodo 추론을 실행한 결과가 아닙니다. 아래의 기존 run.bvh 직접 적용 설명은 이전 단계의 이력입니다.

- 0.6초·18프레임 한 주기, 좌우 교대 포함, 3초·90프레임에 다섯 주기. 평균 전진 0.9m/s.
- 네 자세 사이 회전 보간, 좌우 반사, 작은 골반·가슴 반대 회전을 사용했습니다. 어깨 움직임은 부모 관절을 통해 팔로 전달하며 손 세계 좌표를 고정하지 않습니다.
- 접지 구간은 발끝을 월드 공간에 고정하고 몸이 지나가도록 고정 길이 두 뼈 IK로 풀었습니다. 골반 높이를 주기적으로 평활화한 다음 양발의 월드 위치를 다시 맞췄습니다. 카메라는 등속 전진만 따라갑니다.
- 90프레임 검사: 뼈 크기 변화 0, 바닥 최소 약 -9.3e-8m, 접지 발끝의 구간 내 최대 변화 약 0.49mm, GLB 왕복 범위 오차 약 1.8e-7m. 한 주기 쿼터니언 내적 오차 약 2e-6. 골반 높이 2차 차분 최대는 평활화 전 0.02369m에서 0.00540m로 감소했습니다.
- 원본 메시·색상은 그대로입니다. 국소 모서리 최대 늘어짐 약 3.69배, 최종 발목 기준 자세 대비 회전 최대 약 50.6도입니다. 공중 발목 제한은 골반 재보정 이전에 적용되므로 최종 전체 프레임이 40도 이하라고 주장하지 않습니다. 의상 접힘·부츠 연결과 게임 미술 품질은 추가 검토 대상입니다.
- 이전 직접 이식본은 Git 커밋 38541ac, 승인된 정적 네 자세는 bbfc620에서 복원할 수 있습니다. 정적 네 자세 Blend는 별도로 보존합니다.

재현: scripts/rig-tripo-run.py로 최초 기본 리그 → scripts/study-run-keyposes.py로 네 자세 → scripts/animate-run-keyposes.py로 반복 보정 → scripts/verify-tripo-run.py → FULL_RENDER=1 scripts/render-tripo-run.py → scripts/encode-tripo-run.py. 모든 Blender 단계는 로컬 Blender 4.5.13, 인코딩은 Kimodo Python 환경에서 실행합니다. 반복 화면은 고정된 월드 조명·등속 카메라에서 동일한 한 주기 렌더를 재사용하며 실제 변형 수치는 90프레임 전부 측정합니다.

2026-10-15. 사용자가 새 Tripo 외형으로 달리기 적용을 승인했습니다.

## 결과

- 원본: assets/ink-hero-tpose.glb. 실제 Tripo P2.0 생성 및 20크레딧 텍스처 결과. 기존 ink-hero.glb와 절차적 hero-model 시안은 덮어쓰지 않았습니다.
- 적용본: outputs/tripo-run.blend / tripo-run.glb. 영상 tripo-run-preview.mp4 / .gif, 정면·측면 주요 자세 tripo-run-contact-sheet.png.
- 기존 Kimodo 생성 outputs/run.bvh 및 run.npz의 3초·30fps·90프레임 달리기를 재사용했습니다. 새 Kimodo 샘플 생성은 하지 않았습니다. 네 번의 약 0.75초 주기이며 기존 hero-run에 추가했던 상체·속도 보정은 복사하지 않았습니다.
- 새 모델 비율에 18개 관절을 배치했습니다. 쇄골은 실제 BVH LeftShoulder/RightShoulder에 연결하며 팔의 세계 회전을 고정하는 후속 보정은 사용하지 않습니다. 머리·후드는 가슴과 함께 움직여 목 옷의 과도한 변형을 줄였습니다.
- 최초 열 확산 자동 가중치는 닿아 있는 옷 조각 사이로 영향이 누출됐습니다. 지퍼의 인접 정점에서 서로 다른 머리·다리 영향이 확인되어 채택하지 않았습니다. 최종은 부위별 연속 가중치와 가랑이 좌우 혼합을 사용합니다. 기본 메시 정점 위치 변화는 0입니다.
- 큰 신발은 단단한 밑창, 고정 길이 두 뼈 발 접촉 보정과 공중 발목 제한을 사용합니다. 카메라는 등속 전진 경로만 따라갑니다.

## 확인과 한계

90프레임의 뼈 크기 변화 0, 가중치 합 오차 약 4.5e-8, 바닥 최소 높이 약 -1.3e-7m로 수치 오차 이내입니다. 같은 30fps로 GLB를 다시 가져온 네 자세의 범위 오차 약 1.2e-7m. MP4 90프레임·30fps·3초 디코딩 확인. 구조 검사와 미술 품질 승인은 구분합니다.

국소 모서리 늘어짐 최대 약 3.58배가 남아 최종 의상 변형 품질을 통과했다고 주장하지 않습니다. 주요 자세의 어깨·겨드랑이 접힘, 팔꿈치 부피, 깊은 무릎 굽힘과 팔의 러닝 자세를 사용자와 검토해야 합니다. 원본 Tripo 스카프 단순화·밑창 홈도 남아 있습니다. 이 결과는 게임 최종 스프라이트가 아닌 새 모델의 달리기 검토본입니다.

GLB는 삼각형으로 내보내집니다. Tripo 화면의 사각면을 유지한 FBX는 아직 받지 않았으며 새 원본을 사각면 상태라고 잘못 표기하지 않습니다. Blender의 단순화된 리그는 손가락·의상 물리·실시간 지형 IK를 포함하지 않습니다.

## 재현

WSL 저장소 루트에서 Blender 4.5.13으로 scripts/rig-tripo-run.py 실행 후 scripts/verify-tripo-run.py를 실행합니다. FULL_RENDER=1로 scripts/render-tripo-run.py를 실행하고 Kimodo 환경 Python으로 scripts/encode-tripo-run.py를 실행합니다. docs/logs/tripo-run-*에 구조·변형·렌더·인코딩 기록을 저장합니다.

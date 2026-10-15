# 게임 기본 달리기 적용

2026-10-15, `work/kimodo-setup`. 사용자 선택은 민첩한 게임 기본 달리기: 자연스러운 팔치기와 적당한 전경 자세입니다. 기존 걷기 결과와 원본 외형은 보존하고 별도 `run` 결과를 만들었습니다.

## 크기를 맞추는 방법

Kimodo SOMA는 한 가지 고정 사람 비율로 학습·생성합니다. 캐릭터의 임의 비율을 생성 옵션으로 지정하는 기능은 설치된 CLI에 없습니다. 공식 설명: https://research.nvidia.com/labs/sil/projects/kimodo/docs/key_concepts/skeleton.html . 생성용 SOMA와 실제 캐릭터 리그를 구분합니다.

최종 적용본의 16뼈 기본 자세와 작업용 메시 정점은 기존 걷기 캐릭터와 동일합니다. 모델의 몸 부위를 줄이지 않았고 애니메이션 중 뼈 길이나 크기를 바꾸지 않습니다. 사람 동작의 기준 축을 제거하고 캐릭터 기준 축으로 옮긴 뒤, 실제 다리 길이 비율 약 0.294로 이동·발목 경로를 맞춥니다. 크기 검사는 `hero-run-validation.json`의 걷기 대비 기본 뼈 행렬·정점 차이 0으로 확인합니다.

## 생성과 주기 선택

- 로컬 RTX 4050, CPU 텍스트 인코더, 기존 허용된 Hugging Face 로그인과 캐시를 사용했습니다. 새 인증 파일이나 모델 가중치를 저장소에 넣지 않았습니다.
- 모델 `Kimodo-SOMA-RP-v1.1`, seed 46, 3초·30fps, 두 후보, 기본 100단계와 공식 후처리.
- 프롬프트: `A person runs forward at a steady brisk pace with a slight forward lean and natural alternating arm swings.`
- 두 후보 전체 생성은 모델 로딩 포함 163초, 진행 표시의 diffusion 100단계는 약 28초였습니다. 이것이 캐릭터 리깅·렌더까지 포함한 총시간은 아닙니다.
- 두 후보에서 시작·끝 자세와 속도가 가까운 완전한 달리기 주기를 검색했습니다. 선택은 `run_00`, 0부터 세는 16번 프레임에서 24프레임 길이입니다. 선택 기준·다른 후보 점수는 `docs/logs/run-selection.json`에 남겼습니다. 수치 점수만으로 최종 미적 품질을 보증하지는 않습니다.
- 약 0.8초 원본 주기의 끝 회전 차이 평균 약 3.04도를 분산 보정하고, 주기적 단위 쿼터니언 보간으로 0.75초 주기로 정리했습니다. 약 6.7%의 박자 조정입니다. 3초에 네 주기, 분당 약 160걸음입니다.
- 원본 접지 분류는 짧은 접지 구간만 표시하는 경우가 있어, 낮고 느린 발끝의 기하 조건과 결합해 접지를 추정했습니다. 접지 한 프레임 누락만 메웠으며 실제 공중 구간을 바닥 접촉으로 강제하지 않았습니다.
- 생성 원본은 `outputs/run-source.npz`, `outputs/run-source.bvh`; 반복 정리본은 `outputs/run.npz`, `outputs/run.bvh`입니다. 반복 정리본의 NPZ는 FK로 관절 위치·전역 회전을 다시 계산하고 공식 표준 T포즈 BVH 변환기로 내보냈습니다.

## 자연스러움을 위한 캐릭터 보정

- 걷기의 “항상 한 발이 접지” 가정을 달리기에 쓰지 않습니다. 두 발이 뜨는 34/90프레임을 실제 변형 메시 검사에서도 확인했습니다.
- 접지 구간은 발 위치를 고정하고, 캐릭터의 고정 길이 다리 IK로 맞춥니다. 큰 신발의 공중 회전은 최대 35도 수준으로 부드럽게 제한하고 원본 발의 지면 여유를 캐릭터 크기에 맞춰 유지합니다. 실제 메시 최저점은 공중에서 최대 약 2.28cm 올라갑니다.
- 달리기에서 더 크게 움직이는 손목·팔을 위해 각 부위의 A포즈 기준을 보정하고, 두꺼운 몸통과 큰 장갑에 약간의 팔 간격을 줬습니다. 장갑은 단단한 영역으로, 소매 경계는 연속 가중치로 연결했습니다.
- 첫 적용 렌더에서 스카프 장식과 목이 늘어나는 것을 발견했습니다. 이어진 큰 후드·스카프 셸이 서로 다른 뼈 변환으로 찢어지지 않게, 달리기에서는 머리가 가슴의 변형을 함께 따르도록 했습니다. 독립적인 시선·고개 동작을 모두 보존한 것은 아닙니다. 스카프·버클은 한 영향 범위로 정리했습니다.
- 카메라와 조명은 등속 경로를 따라가며 골반의 좌우·상하 흔들림을 따라가지 않습니다. 바닥은 고정입니다.
- 반복 끝의 91번 키는 시작 포즈와 한 클립의 전진량을 합친 값입니다. MP4는 90프레임·3초, GLB는 이 끝 키를 포함하여 정확히 3초입니다. 시작·끝 이미지는 캐릭터·카메라·조명을 함께 전진시킨 상태에서 비교합니다.

## 결과와 검증

- `outputs/hero-run.blend`: 캐릭터 크기의 리그, 반복 달리기, 참고 SOMA, 스튜디오 씬.
- `outputs/hero-run.glb`: 16뼈 캐릭터, 3초 반복 달리기 한 애니메이션.
- `outputs/hero-run-preview.mp4`: 512×512, 30fps, 3초·네 주기.
- `outputs/hero-run-contact-sheet.png`: 한 주기 약 0.75초 안의 여섯 자세.
- `docs/logs/run-*.json`, `hero-run-*.json`와 실행 로그: 후보 선택·골격 왕복·동일 크기·변형·접지·공중 구간·반복 경계·GLB 왕복·영상 검사.

최종 검사 모두 PASS입니다. GLB 재가져오기에서 애니메이션 범위는 0~90프레임(30fps, 3초), 세 자세의 메시 경계 오차는 최대 약 0.00000024m입니다. 영상은 90프레임을 실제 디코딩했고, 한 클립 이동량을 반영한 반복 끝 이미지와 시작 이미지의 평균 픽셀 차이는 약 0.0021/255입니다. 전체 90자세에서 지면 관통·화면 잘림·뼈 길이 변화가 허용 오차 안이었으며, 주요 자세 렌더 시트도 확인했습니다. 이 검사는 모든 의상 충돌이나 미적 자연스러움을 보증하지 않습니다.

캐릭터의 주기 전진량은 약 3.212m/3초, 약 1.071m/s입니다. 기존 걷기의 약 0.438m/s 대비 약 2.45배입니다. 실제 게임의 이동속도는 화면·월드 단위에 따라 정하고, 발 미끄러짐을 막으려면 재생 박자나 보폭도 함께 맞춰야 합니다.

현재 방식은 Kimodo로 동작 후보를 만들고, 좋은 한 주기를 골라 캐릭터에 맞게 보정하는 조합입니다. 대안으로 검증된 모캡 달리기 클립을 같은 리그에 옮기거나 핵심 자세를 직접 키프레임으로 만들 수도 있습니다. 어느 방법이든 이 캐릭터의 짧은 다리·큰 신발·장갑·이어진 후드에 대한 보정과 실제 재생 검토가 필요합니다. 이번 결과는 게임 기본 달리기의 시작점이며, 무기 소지·공격 전환·옷 충돌까지 검증한 결과는 아닙니다.

## 재실행

WSL 저장소 루트에서 생성과 적용을 분리해 실행합니다. 생성은 기존 로그인 파일 사용이 허용된 환경에서만 실행합니다. `HERO_MOTION`을 생략하면 기존 걷기 경로를 사용하므로 달리기에는 반드시 `run`을 지정합니다.

```sh
HF_TOKEN_PATH=/mnt/c/Users/SSAFY/.cache/huggingface/token bash scripts/run-run.sh
/opt/deviant-kimodo/.venv/bin/python scripts/prepare-run.py
export HERO_MOTION=run
BLENDER=/opt/deviant-blender/blender-4.5.13-linux-x64/blender
"$BLENDER" -b --factory-startup --python-exit-code 1 --python scripts/rig-hero.py
/opt/deviant-kimodo/.venv/bin/python scripts/verify-walk.py
"$BLENDER" -b --factory-startup --python-exit-code 1 --python scripts/verify-run.py
"$BLENDER" -b --factory-startup --python-exit-code 1 --python scripts/review-hero.py
"$BLENDER" -b --factory-startup --python-exit-code 1 --python scripts/render-hero.py
"$BLENDER" -b --factory-startup --python-exit-code 1 --python scripts/verify-hero-glb.py
/opt/deviant-kimodo/.venv/bin/python scripts/encode-hero-preview.py
```

후보와 중간 PNG는 무시되는 `.cache`에 저장합니다. `run-source`는 선택된 생성 원본만 보존합니다. `walk` 결과를 덮어쓰지 않습니다.

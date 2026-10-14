# 캐릭터 걷기 적용

원본 `assets/ink-hero.glb` 외형을 보존하고, 캐릭터 비율에 맞춘 몸통 리그에 `outputs/walk.bvh`의 Kimodo 걷기를 이식합니다. 실행 환경은 갤럭시북의 WSL2 Ubuntu-22.04와 공식 Blender 4.5.13 LTS입니다. 설치 배포 파일은 공식 SHA256과 대조했습니다.

2026-10-14: 3초·90프레임 렌더 및 MP4 디코딩 검사 PASS. 90프레임 전체 변형의 유한값·가중치와 바닥 높이 검사 PASS. 내보낸 GLB를 다시 가져와 시작·중간·끝의 변형 범위를 Blender 씬과 비교한 검사 PASS. 6개 주요 프레임에서 양발 교대와 팔 움직임, 얼굴·후드 유지 및 어깨 경계 수정 결과를 확인했습니다.

## 크기와 자세 맞추기

원본은 높이 약 0.979m, 팔을 비스듬히 내린 A포즈입니다. 큰 머리와 짧은 팔다리 때문에 사람 골격을 일괄 축소하지 않고, 메시 단면을 확인하여 골반·어깨·팔꿈치·무릎·발목 위치를 별도로 배치했습니다. 16개의 변형 뼈를 사용하며 손가락, 눈, 입, 의상 물리 리그는 만들지 않았습니다.

BVH의 cm 단위를 m로 변환하고, SOMA의 허벅지 `LeftLeg/RightLeg`와 정강이 `LeftShin/RightShin`를 캐릭터의 해당 뼈에 연결합니다. 사람 골격의 실제 포즈 회전을 캐릭터의 A포즈 기준에 맞게 변환하여 90프레임에 굽습니다. 전진 거리와 골반 움직임은 머리를 포함한 키 대신 양쪽 다리의 길이 비율로 축소합니다. 제자리 걷기나 반복 경계 보정은 별도 작업입니다.

## 메시와 변형

원본 983,284정점은 수정하지 않았습니다. 작업용 메시만 삼각형 수 기준 4.5%로 줄이고 UV와 원본 재질을 유지했습니다. 단순 감량이므로 게임용 토폴로지 정리가 완료된 것은 아닙니다.

겹친 의상 때문에 Blender 자동 bone-heat 가중치가 실패하여, 부위별 마스크와 뼈 구간까지의 거리로 정규화한 가중치를 작성했습니다. 처음 렌더에서 발견한 어깨의 뾰족한 변형은 마스크 경계를 연속적으로 연결하여 보정했습니다. 얼굴과 후드 상부는 머리 뼈에 고정해 외형을 보호합니다.

각 프레임의 실제 변형 메시에서 가장 낮은 정점이 바닥에 오도록 골반의 수직 이동을 보정했습니다. 완전한 발 접촉 IK가 아니므로 발의 수평 미끄러짐, 옷의 눌림, 극단적인 동작에서의 변형은 후속 조정 대상입니다.

작업용 메시 62,290정점·85,857삼각형, 가중치 없는 정점 0개입니다. 다리 길이 비율은 약 0.294이며 3초 동안 수평으로 약 1.314m 전진합니다. GLB는 정점당 가장 큰 4개 가중치를 정규화하여 사용하고, 골격과 전진 이동을 하나의 씬 애니메이션으로 내보냅니다. 원본 BVH의 0길이 끝 뼈와 GLB의 4가중치 정규화 경고는 로그에 보존했습니다.

초기 Actions 방식 내보내기는 참고 골격 액션까지 포함하려 하여 대상 뼈 경고가 발생했습니다. 최종 GLB는 Scene 방식으로 다시 내보내어 애니메이션 1개를 검사했습니다(`hero-export.log`, `hero-preview-check.json`). 공유 이미지의 텍스처 샘플러 경고도 남지만 렌더 외형은 확인했습니다. GLB 재가져오기 후 변형 범위 차이는 검사한 세 시점에서 최대 약 0.67mm입니다. 전체 정점의 일치나 모든 자세의 최종 품질을 보증하는 검사는 아닙니다.

## 결과와 재실행

- `outputs/hero-walk.blend`: 캐릭터 리그, 굽힌 걷기, 원본 Kimodo 참고 골격, 카메라와 조명.
- `outputs/hero-walk.glb`: 캐릭터 메시·재질·16뼈 스킨과 걷기 애니메이션. 카메라·바닥·조명은 제외.
- `outputs/hero-walk-preview.mp4`: 512×512, 30fps, 90프레임, 3초. 카메라가 캐릭터를 따라가지만 실제 애니메이션은 전진합니다.
- `outputs/hero-walk-contact-sheet.png`: 0~2.5초, 0.5초 간격의 6개 확인 프레임.
- `docs/logs/hero-*.json`, `hero-rig.log`, `hero-render.log`: 크기·가중치·변형·영상 검사와 실행 기록.

저장소 루트에서 WSL에 설치된 Blender로 실행합니다.

```sh
BLENDER=/opt/deviant-blender/blender-4.5.13-linux-x64/blender
"$BLENDER" -b --factory-startup --python-exit-code 1 --python scripts/rig-hero.py
"$BLENDER" -b --factory-startup --python-exit-code 1 --python scripts/verify-hero.py
"$BLENDER" -b --factory-startup --python-exit-code 1 --python scripts/render-hero.py
"$BLENDER" -b --factory-startup --python-exit-code 1 --python scripts/verify-hero-glb.py
/opt/deviant-kimodo/.venv/bin/python scripts/encode-hero-preview.py
```

Blender는 설치된 CUDA 장치를 확인하고 Cycles로 렌더합니다. CUDA가 없으면 CPU를 사용합니다. `.cache/hero-working.glb`는 원본 파일 해시가 일치할 때만 사용하는 작업용 감량 캐시이며 `.cache/hero-frames`는 중간 PNG입니다. 둘 다 커밋하지 않습니다. Mac에서는 설치된 Blender 실행 경로로 바꿔 동일 스크립트를 사용할 수 있습니다.

현재 결과는 몸통 걷기를 실제 캐릭터로 확인하는 첫 적용본입니다. 다음은 정면·측면·사선 카메라 비교, 의상과 발 접촉 보정, 반복 동작 정리 후 2D 프레임·스프라이트 시트와 에테르 AI 도트 변환 검토입니다.

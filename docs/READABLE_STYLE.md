# 대기 부위 구분 개선 — 2026-10-26

사용자 피드백: 픽셀이 일그러져 보이며 소매·몸통·로브 구분이 약하다. 새 결과는 `outputs/pixel-readable-style/idle-comparison.gif`와 `run-comparison.gif`. 왼쪽은 이전 부위별 명암, 오른쪽은 이번 수정이다. 최종 미술 승인 전 비교본이다.

## 변경

- 원본 Tripo 기본 형상과 전용 골격 길이를 유지했다. 대기의 팔을 아래로 내려 몸통에서 벌렸다. 발목 위치와 뼈 크기는 유지했다.
- 대기의 척추/가슴/목 호흡 진폭을 각각 .7/1.2/-.8도에서 .15/.3/-.15도로 줄이고 팔의 미세 주기 흔들림을 제거했다. 몸통이 안정되고 옷 경계 변화가 적어지는 대신 움직임의 생동감은 약해질 수 있다. 새 대기는 수작업 골격 동작이며 Kimodo/Mixamo 생성본이 아니다.
- 카메라60/75/90도를 같은 모델로 비교하고75도를 선택했다. 기존보다 정면 쪽15도 이동하여 양발 사이와 로브 앞트임이 읽힌다. 완전 정면90도는 이동 방향감이 약해 제외했다. 비교 시트는 `outputs/pixel-readable-study/camera-comparison.png`.
- 후드 옆면 그림자를 줄였다. 128px 캔버스/중립 높이64px/6색/이진알파/최근접 확대 유지. 프레임별 윤곽 필터·AI 재생성·머리 변형은 없다.
- 새 대기 자세에 대해 독립 옷 물리를 다시 계산했다. 달리기는 기존 Mixamo 적용본과 베이크를 그대로 사용하며 시점/명암만 변경했다. 비교는 자세/시점/명암이 함께 바뀌므로 개별 효과의 통제 실험이 아니다.

## 검증 및 한계

- 대기90프레임30fps/3초, 달리기22프레임30fps(원래733ms, GIF730ms). 출력 잘림 없음. 원본 형상 해시는 렌더 전후 동일.
- 대기 발목 위치 변화0m, 뼈 길이 오차8.35e-8m. 기본 모델 변형과 자세로 인한 화면상 실루엣 변화는 구별한다.
- 새 대기90프레임: 목둘레208접합쌍 최대 벌어짐0m. 검사 범위의 로브/스카프 삼각형 교차0. 최대 모서리 늘어짐1.793배. 전체 몸/자기충돌/연속 충돌 검증은 아니다.
- 화면좌표 프레임간 변경 픽셀 평균4.96→1.34, 최대12→6. 카메라와 동작량도 달라졌으므로 화풍 점수나 순수 깜빡임 개선율로 해석하지 않는다.
- 옷자락과 팔의 부분 겹침, 뒤에 가려진 스카프, 높은 후드 등 원본 특성은 남는다. 새 각도에서 달리기의 측면 방향감이 줄어드는 절충이 있다. 천 루프 연결은 미검증. 팀원 그림과 같은 수준의 읽힘을 달성했다고 확정하지 않는다.

## 재현

Blender4.5.13LTS/WSL Ubuntu22.04. 아래 환경변수를 설정하고 각 스크립트를 Blender `-b --python-exit-code 1 --python`으로 실행한다.

1. `READABLE_IDLE=1`: `scripts/build-pixel-idle.py`
2. `MOTION_TAG=pixel-readable-idle`: `scripts/simulate-pixel-run-cloth.py`
3. `DESIGNED_SHADOWS=1 STYLE_CONFIG=scripts/readable-style-study.json`: `scripts/render-surface-style.py`
4. `DESIGNED_SHADOWS=1 STYLE_CONFIG=scripts/readable-style-render.json`: 같은 렌더 스크립트
5. `VERIFY_INPUT=outputs/pixel-readable-idle-cloth.blend VERIFY_OUTPUT=docs/logs/pixel-readable-idle-cloth-validation.json`: `scripts/verify-pixel-run-cloth.py`
6. `COLLAR_INPUT=outputs/pixel-readable-idle-cloth.blend COLLAR_TAG=readable`: `scripts/check-pixel-collar.py`
7. 일반 Python(Pillow/numpy): `scripts/pack-readable-style.py`, `scripts/check-readable-style.py`

입력/물리 베이크는 `outputs/pixel-readable-idle.blend`, `outputs/pixel-readable-idle-cloth.blend`. 이전 대기와 달리기 파일은 보존한다. 세부 실행 기록은 `docs/logs/pixel-readable-*`, 출력 검증은 `outputs/pixel-readable-style/*validation.json`과 `motion-pixel-check.json`.

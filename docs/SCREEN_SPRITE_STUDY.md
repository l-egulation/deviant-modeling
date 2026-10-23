# 게임 시점 기준 형태 보정 시험

2026-10-23. `outputs/pixel-run-cloth.blend`의 복사본으로 실루엣·눈·옷 표현을 시험했다. 기존 승인 원본/골격/모션/시트는 변경하지 않는다.

## 결과 파일

- `outputs/pixel-screen-study/comparison.gif` / `.png`: 팀원 정지 참고, 동일 카메라의 수정 전, 형태 보정 후. 팀원 참고는 본래64px 높이, 달리기와 자세·크기가 다르다.
- `after.gif`: 투명128×128 달리기22장. `after-sheet.png`: 6열×4행768×512, 마지막2칸 비어 있음.
- `after-128/`: 개별 PNG. `contact-sheet.png`: 전체 프레임 확인용.
- `screen-character.blend`: 고정45도 게임 시점에 맞춘 별도 편집/재생 장면.
- `study.json`, `validation.json`, `collision-check.json`: 적용 범위와 검사.
- `outputs/pixel-screen-study.zip`: 로컬 전달용 PNG/GIF/메타데이터, 큰 blend/중간 렌더 제외.

## 실제 변경

기존 Tripo 후드 정점의 꼭대기를 낮추고 뒤로 뺀 뒤 후두부 끝을 더 처지게 했다. 목 경계에서는 영향이0이 되도록 부드럽게 연결하고, 얼굴이 고정 카메라 쪽을 향하도록 후드 위쪽을22도 돌렸다. 소매는 기존 정점의 깊이를 줄였으며 손/뼈 길이를 변경하지 않았다. 목도리 고정부는 유지하고 꼬리만 뒤쪽으로 더 펼쳤다.

눈의 불규칙한 금색 텍스처 영역은 검정으로 바꾸고 금색 직사각형2개를 얼굴 위치에 부착했다. 이 눈 평면은 **고정 캡처 카메라를 향하는 표현**이며 다른 카메라에서 쓰는 범용 얼굴 리그가 아니다. 모델 수정은 Blender에서 수행했고 Tripo를 다시 생성하지 않았다.

색은 이전 단색/큰 그림자 방식을 사용한다. 수정 전후 모두 같은45도 시점, 같은128캔버스/배율/시간이다. 최종 PNG/GIF만 좌우 반전해 팀원 참고와 같은 오른쪽 방향으로 비교한다. Blend에서는 원래 방향으로 보이며 양면 대응까지 검증한 것은 아니다.

## 움직임과 검증 범위

기존90프레임 의상 베이크에 골격 방향을 따르는 형태 변위를 더한 **미술 검토용 보정본**이다. 새 형상으로 천 물리를 다시 계산한 결과가 아니다. 45~66프레임22장을30fps로 캡처, GIF는시간단위제약으로730ms. 기존 천 루프 불연속 가능성은 남는다.

128×128/22장,고정팔레트,이진알파,잘림 없음 검사는 `validation.json`에 기록한다. 실제 로브 외면/스카프 꼬리90프레임 교차는 `collision-check.json`에 기록하며 후드/눈/전신/자기충돌/연속충돌 검사를 포함하지 않는다. 형상 보정 후 전체 의상 물리를 검증했다고 해석하지 않는다.

후드 높이·얼굴 노출·스카프 실루엣은 개선 방향이지만, 팀원 그림과 소매/부츠 부피 및 후드 끝 윤곽 차이가 남는다. 이 안은 사용자 미술 검토 후 원본 형상과 새 물리 계산에 반영할 후보이며 기존 승인본을 대체하지 않는다.

재현: Blender `scripts/build-screen-sprite.py` → Python `scripts/pack-screen-sprite.py`. 교차검사는 `VERIFY_INPUT=outputs/pixel-screen-study/screen-character.blend VERIFY_OUTPUT=outputs/pixel-screen-study/collision-check.json` 환경변수로 `scripts/verify-pixel-run-cloth.py` 실행. 로그 docs/logs/pixel-screen-*.log.

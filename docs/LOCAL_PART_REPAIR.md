# 소매·허리·장식 부분 수정 — 2026-10-27

사용자는 앞선 부위 지도도 정확하지 않고 잉크가 흘러내린 듯한 조각이 보인다고 지적했다. 이번에는 화면상의 부위 보정 결과를 다시 보정하지 않고, 실제 모델의 국소 형상과 재질 경계를 수정했다. 전면 재모델링 또는 새 Tripo 생성은 아니다.

## 수정 범위

- 기본 자세의 팔 축을 기준으로 소매 단면을 최대16% 좁혔다. 손목 쪽으로 부드럽게 적용하며 팔 길이와 뼈대는 유지한다.
- 어깨 아래/자유 옷자락 위의 허리 좌우를 최대12mm 안쪽으로 정리했다. 중복된 접합 정점은 같은 변위를 받아 틈이 생기지 않도록 했다.
- 총10,565정점, 최대 변위21.28mm. 후드 정점 변위0. 대기와 달리기에 같은 기본형 변위를 적용했다.
- 기존 렌더는 원본 텍스처를 삼각형마다 샘플링해 재질색을 판단했다. 이로 인한 작은 색 조각을 줄이기 위해 로브는 아이보리, 소매/장갑은 기본 자세의 손목 경계, 다리/발목 띠/신발은 높이 경계, 스카프/브로치는 별도 위치 경계로 지정했다. 발목 띠는 z=.095~.140m의 연속 금색 영역이다.
- 소매·로브는 여전히 기존 Region 그룹을 바탕으로 한다. 정확한 새 의상 토폴로지나 독립적인 봉제 패턴을 제작한 것은 아니다. 명시적 재질 경계도 실제 봉제선과 완전히 일치한다는 보장은 없다.
- 이전의 화면좌표 눈 사각형/부위지도 후처리는 이번 결과에 사용하지 않았다. 후드/눈은 기존 텍스처 분류를 유지하여 얼굴의 세부 경계 문제는 남을 수 있다.

## 입력과 결과

입력은 `pixel-readable-idle.blend`, `pixel-run.blend`. 출력 편집본은 `pixel-repaired-idle.blend`, `pixel-repaired-run.blend`; 해당 이름의 `-cloth.blend`는 각각 새로 계산한90프레임 의상 베이크다. 기존 원본은 보존한다.

`outputs/pixel-repaired-style/idle-comparison.gif`, `run-comparison.gif`: 이전 부위별 후처리 / 새 부분 수정. 비교 양쪽 모션·카메라는 동일하지만 형상·재질과 후처리 방식이 다르다. 128px/6색/30fps, 대기90장·달리기22장. 각 폴더의 preview.gif는 투명 배경, sheet.png는 스프라이트 시트다.

검사 로그는 `docs/logs/pixel-local-repair.json`, `pixel-repaired-idle-validation.json`, `pixel-repaired-run-validation.json`. 의상 검사 범위는 렌더링된 바깥 로브와 스카프 꼬리의 비공면 삼각형 교차이며 전신·자기충돌·연속충돌을 보장하지 않는다. 루프 연결과 사용자 미술 승인은 별도다.

각90프레임에서 검사 범위 교차0. 최대 모서리 늘어짐은 대기1.793배, 달리기2.79413배다. 달리기 기존 측정2.79414배와 거의 동일하지만2배 미만 기준을 통과한 것은 아니며 스카프 국소 변형은 미해결이다. 이번 수정으로 모든 물리 품질이 통과했다고 해석하지 않는다. 출력112장 화면 잘림 없음,128px/6색/이진알파와 GIF 재생시간을 검사했다.

## 재현

Blender4.5.13LTS에서 repair-pixel-parts.py 실행. 이후 MOTION_TAG=pixel-repaired-idle / pixel-repaired-run 각각으로 simulate-pixel-run-cloth.py 실행. DESIGNED_SHADOWS=1, STYLE_CONFIG=scripts/repaired-style-render.json으로 render-surface-style.py 실행. 일반 Python(Pillow/numpy)에서 REPAIRED_STYLE=1로 pack-readable-style.py 실행.

verify-pixel-run-cloth.py의 VERIFY_INPUT과 VERIFY_OUTPUT을 각 새 -cloth.blend와 새 검사 JSON 경로로 지정해 확인한다. 기본 물리 설정은 이전과 같으며 새로운 실시간 물리 엔진을 구현한 것은 아니다.

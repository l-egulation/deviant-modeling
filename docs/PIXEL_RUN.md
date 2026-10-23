# 캐릭터 전용 골격 달리기와 의상 시험

## 최신: Mixamo 원본으로 전환, 상체 자세와 FBX 방향 오류 수정

2026-10-23 사용자 피드백: 달리기 중 상체가 뒤로 젖혀진다. 기존 Kimodo 원본에서 골반→목 기울기가 -7.82~18.06도였고 적용본도 -7.83~17.04도였다(양수=전방). 손 높이 위주의 후보 선택에서 상체 자세를 놓쳤다.

Kimodo seed732/983으로 4개씩 총8개를 재생성했다. 뒤로 젖힘 또는 허리를 뒤에 둔 채 윗몸만 숙이는 문제 때문에 모두 제외했다. `pixel-run-posture-rejected-*`와 `pixel-run-candidates.json`에 기록한다. 사용자가 **전에 확인한 Mixamo 달리기를 전용 골격에 적용**하도록 선택했다.

- 현재 원본은 `assets/mixamo-running.fbx`의 Running With Intention. 원본22프레임/30fps를 같은 속도로 반복하여90프레임을 만든다. 원본 FBX와 동작 키는 수정하지 않는다.
- `pixel-run.blend`가 현재 Mixamo 적용본, `pixel-run-cloth.blend`가 이에 맞춘 독립 의상 베이크다. `pixel-run-source.bvh/.npz`는 이전 seed231 Kimodo 기록으로 남겨두며 현재 입력으로 사용하지 않는다.
- `pixel-run-posture-comparison.mp4`: 이전 Kimodo/현재 Mixamo 전후 비교. `pixel-run-comparison.mp4`: 현재 Mixamo 원본 골격/캐릭터 비교. `pixel-run-source-preview.gif`: 현재 원본 골격.
- 골격 길이 최대 오차1.856e-7m, scale1 유지. 루트/보폭 비율0.259178, 고정 길이 접지IK 유지. 소매 국소 늘어짐 최대2.444배는 남는다.
- 캐릭터 골반→목 기울기9.51~16.94도, 평균14.14도. 90프레임 전부 전방이다. 원본은5.25~13.87도. 기울기 수치는 이 캐릭터의 검증 기준이며 모든 사람의 정상 달리기를 정의하는 기준은 아니다.
- Mixamo 변환 중 FBX 표시축을 해부학적 관절 방향으로 오해한 오류도 수정했다. 어깨→팔꿈치→손목, 골반→무릎→발목→발끝을 기준으로 원본 회전을 좌표 변환한다. 길이0인 새 Blender 뼈에 matrix부터 설정하면 방향이 소실되므로 길이 설정 후 matrix를 넣는다.
- 회귀 검사: 수정 전 `Source torso leans backward`와 `Non-anatomical source rest axes`로 실패. 수정 후 `diagnose-run-posture.py`의 POSTURE_ASSERT=1과 `verify-pixel-source-axes.py` 모두 통과. 원본 관절 방향/캐릭터 전달 방향의 벡터 오차는 각각1.216e-5/1.071e-6 이하.

현재 재현: Blender로 `apply-pixel-run.py` → `diagnose-run-posture.py`(POSTURE_ASSERT=1) → `verify-pixel-source-axes.py` → `simulate-pixel-run-cloth.py` → `verify-pixel-run-cloth.py` → `preview-pixel-run.py`, 이어 Kimodo 가상환경 Python으로 `package-pixel-run.py`. 전후 비교를 재현하려면 이전 커밋7fe1548의 비교MP4를 `.cache/posture-before/pixel-run-comparison.mp4`에 둔다. 기본 원본/캐릭터 비교에는 이 이전 파일이 필요 없다.

Blender 호출에 `--python-exit-code 1`을 추가하여 Python assertion 실패가 다음 단계 실행으로 이어지지 않게 한다. 이 환경은 기본 옵션에서 Python 예외가 나도 프로세스 종료코드0을 반환한다. 이번 검증은 각 단계 로그의 실제 PASS/실패 문구와 결과 파일을 확인했다.

최종 Mixamo 의상 검증: 로브 외면/스카프 꼬리90프레임 교차0건. 전체 표면 모서리 최대 늘어짐2.717배로 국소 접힘은 남아 있다. 관통 검사 범위는 이전과 동일하며 자기/연속 충돌을 포함하지 않는다.

DEBUG REPORT
- Symptom: 달리는 동안 상체가 뒤로 젖혀짐.
- Root cause: Kimodo 원본의 후경 자세를 후보 선택에서 제외하지 않음. Mixamo 전환 중 FBX 표시축과 실제 관절 방향 혼동 및 새 뼈 초기화 순서 오류 추가 발견.
- Fix: 사용자 선택에 따라 Mixamo 원본 사용, 해부학적 기준축으로 변환, 길이부터 초기화, 전 구간 상체 및 축 회귀 검사 추가.
- Evidence: 자세90프레임 통과, 축90프레임 통과, 길이 고정 검증. 세부 JSON/로그는 `docs/logs/pixel-run-*`.
- Regression test: `scripts/diagnose-run-posture.py`, `scripts/verify-pixel-source-axes.py`, `pixel_mixamo_source.py`의 기준축 보존 assertion.
- Related: 손 높이나 전체 몸통 평균값 하나로 후보를 고르지 않는다. 허리/윗몸과 프레임별 최소값을 별도로 본다.
- Status: DONE_WITH_CONCERNS. 소매 접힘, 자기/연속 충돌, 최종 도트 화풍은 별도 품질 과제.

## 이전 단계: Kimodo seed231 기록

2026-10-23. 기존 Tripo 모델과 캐릭터 전용 22뼈를 사용했다. 사람 골격의 긴 관절 위치를 복사하거나 수작업 달리기 키포즈를 만들지 않았다. 최종 게임용 루프와 도트 화풍 승인은 아직 아니다.

## 생성과 적용

- Kimodo-SOMA-RP-v1.1, seed 231, 후보 2개, 각 3초/30fps/90프레임. RTX 4050 6GB에서 생성, 텍스트 인코더는 CPU.
- 프롬프트: `A person runs straight forward continuously at a steady fast pace, with natural alternating strides, a slight forward lean, relaxed bent elbows and low opposing arm swings, coordinated shoulder and hip rotation, and a steady head`
- 00번을 선택했다. 01번보다 손이 가슴 위로 올라가는 비율이 낮다(9.44% 대 25%). 이것이 동작의 자연스러움을 자동으로 보장하는 지표는 아니다.
- 설치된 생성기의 마침표는 동작 구간을 분할한다. 초기 두 문장 입력이 6초가 되어 폐기하고, 한 문장으로 재생성한 90프레임만 사용했다.
- 선택 원본: `outputs/pixel-run-source.npz`, `.bvh`. 원본 회전은 보존했다. `pixel-run-candidates.gif`는 두 생성 후보 비교다.
- 비교 영상의 원본 골격 화면만 좌우 반전해 진행 방향을 맞췄다. NPZ/BVH 데이터는 바꾸지 않았다. 골격은 측면, 캐릭터는 약간 비스듬한 측면이므로 화면상 각도가 완전히 동일하지는 않다.
- 이식: 관절 회전/방향과 쇄골 움직임을 전용 골격에 전달. 루트 이동·보폭에만 다리 길이 비율 0.269234 적용. 발 접촉 구간은 길이 고정 2관절 IK로 처리했다. 팔·몸통의 달리기 키포즈를 새로 만들지 않았다.
- 카메라는 수평으로 일정하게 추적하며 골반의 상하 움직임을 따라가지 않는다.

## 스키닝과 독립 의상

실제 달리기에서 후드 아래 일부가 다른 뼈를 따라 벌어지는 문제를 발견했다. 후드 영역을 아래까지 확장하고 스카프 영역을 먼저 분리했다. 팔꿈치와 무릎의 가중치 전환 범위를 넓혔다. 뼈 위치와 모델 비율은 그대로다.

로브와 스카프는 541개 계산 정점의 별도 거리 제약 천 시뮬레이션이다. 중력·공기 저항·움직이는 신체 캡슐 충돌을 적용하고, 스카프는 변형된 로브와 추가 충돌한다. 프레임마다 8회 세분화, 각 12회 제약 계산, 시작 전 60프레임 안정화. 후드 뒤쪽/끝에는 머리 가속도에 반응하는 감쇠 스프링을 적용했다. T자 시험의 옛 베이크를 재사용하지 않았다.

로브 앞트임의 겉감과 안감을 가로지르는 면은 제거했다. 해당 면이 남으면 트임 양쪽의 독립 움직임 사이에서 길게 늘어난다. 원본 GLB는 변경하지 않았다.

또한 로브 밑면 중앙은 원통형 천 좌표의 각도가 불안정한 영역이므로 중심에서 바깥으로 천 영향을 부드럽게 늘렸다. 겉 자락은 독립 계산을 유지한다. 삭제된 면의 잔여 선은 렌더 모서리 늘어짐 통계에서 제외한다.

실제 천 계산은 스카프의 높은 끝부분과 로브 밑단까지 자유롭게 움직이도록 고정 마스크를 다시 정의한다. 진단 리그의 임시 높이 마스크를 그대로 쓰면 부착부가 아닌 꼬리/밑단이 몸에 붙잡혀 늘어난다. 최종 마스크는 `simulate-pixel-run-cloth.py`에 있다.

원본 로브 안쪽에는 평평하게 막힌 밑면도 있었다. 바깥 자락과 함께 변형하기 부적합하므로 중앙의 수평 내부 면을 열었다. 제거한 면 수는 물리 로그에 기록한다. 외곽 실루엣과 원본 GLB는 보존하며, 이 구조 수정은 의상 베이크 파일에만 적용된다.

`pixel-run.blend`는 골격 적용본, `pixel-run-cloth.blend`는 실제 표면의 90프레임 베이크다. 게임 엔진용 실시간 천 구현은 아니다. 자기 충돌·연속 충돌·전신과 옷의 모든 실제 면 교차를 보장하지 않는다.

## 검증과 한계

- 달리기 뼈 길이 최대 오차 2.735e-7m. 모든 뼈 scale 1, 루트 아래 관절 이동을 복사하지 않음.
- 실제 달리기의 스키닝 모서리 최대 늘어짐 2.304배. 소매의 깊은 접힘은 남는다. 진단 자세의 2배 미만 통과를 실제 달리기의 통과로 해석하지 않는다.
- 갱신된 121프레임 관절 시험은 최대 1.876배, 2배 초과 0개. 현재 진단 영상도 함께 다시 생성했다.
- 자세한 현재 결과는 `docs/logs/pixel-run-retarget.json`, `pixel-run-cloth-validation.json`, `pixel-run-replay.json`, `pixel-run-media.json`에 기록한다.
- 최종 의상 포함 표면 최대 늘어짐 2.304배(왼팔, 물리 전과 동일). 로브 외면8,805개 면과 스카프 꼬리5,911개 면의 비공면 교차는 90프레임 모두0건. 목 부착부·자기 충돌·프레임 사이 관통은 이 검사에서 제외된다.
- 앞트임 연결121개 면, 내부 밑면740개 면을 의상 베이크에서 제거했다. 초기의 큰 천 늘어짐은 구조/고정 마스크 수정으로 해소했다.
- 후드 뒤쪽 관성 각도는 약 -0.66~3.11도. 얼굴 전체를 흔드는 방식이 아니라 후드의 자유 영역에만 적용한다.
- 영상은 3초 클립이다. 시작/끝이 자연스럽게 연결되는 반복 달리기 루프로 검증하지 않았다.
- 낮은 팔치기를 선택했으나 원본 Kimodo의 몸통/어깨 회전은 작다. 자연스러움은 원본 골격과 캐릭터를 나란히 보고 판단해야 한다.

## 재현

WSL Ubuntu-22.04, Blender 4.5.13, `/opt/deviant-kimodo/.venv` 사용.

1. `scripts/generate-pixel-run.sh` 실행 후 `review-pixel-runs.py`로 후보 확인. 선택 00 NPZ/BVH를 위 원본 경로로 복사한다.
2. Blender에서 `build-pixel-rig.py`, `verify-pixel-skin.py`, `apply-pixel-run.py` 순서로 실행한다.
3. `simulate-pixel-run-cloth.py`, `verify-pixel-run-cloth.py`, `preview-pixel-run.py`를 Blender에서 실행한다.
4. Kimodo 가상환경 Python으로 `package-pixel-run.py` 실행. `outputs/pixel-run-comparison.mp4`와 GIF가 원본 골격/적용본 비교다.

인증 파일·가중치·캐시 프레임은 커밋하지 않는다. 원본 BVH/NPZ와 최종 blend, 검증 로그 및 비교 영상은 보존한다.
# 2026-10-23 목도리/로브 목둘레 접합

재질 Alpha=1이며 연결 없음. 투명 재질 문제가 아니라 의미 영역 분리 시 복제한 경계 정점이 서로 다른 뼈 가중치를 따라 벌어지는 문제였다. 기존 Mixamo 90프레임에서 목둘레 경계 208쌍 최대 간격 0.069845m.

`pixel_skin.py`에서 목도리 부착 경계만 로브/소매의 가중치를 사용하고 주변 0.06m에 부드럽게 보간한다. 후드가 함께 만나는 경계에서는 후드 가중치를 섞지 않는다. 기존 메시 위치·UV·골격·애니메이션은 유지한다. 꼬리와 로브 자락의 독립 물리 설정은 그대로 재계산했다. 추가 덮개 메시 없이 기존 경계를 연결했다.

재현 순서: `update-pixel-collar.py` → `COLLAR_TAG=after check-pixel-collar.py` → `simulate-pixel-run-cloth.py` → `COLLAR_TAG=cloth COLLAR_INPUT=outputs/pixel-run-cloth.blend check-pixel-collar.py` → `verify-pixel-run-cloth.py` → `preview-pixel-run.py` → `package-pixel-run.py`. Blender 스크립트는 `--python-exit-code 1`로 실행한다.

검증: 물리 전후 각각 90프레임/208쌍 간격 0m. 기존 범위의 로브 외면/목도리 꼬리 삼각형 교차 0건. 부착부 전체 충돌·자기 충돌·연속 충돌·루프 연결 검증을 의미하지 않는다. 국소 최대 모서리 늘어짐은 몸 2.79410배, 물리 후 2.79414배(이전 물리 후 2.71655배)로 남는다. 첫 목 고정 시도는 어깨 늘어짐 5.57배를 유발해 폐기하고 부착부가 옷을 따르는 방법으로 교체했다.

출력: `outputs/pixel-collar-comparison.png`(동일 프레임 확대), `outputs/pixel-run-comparison.mp4`(최신 전체 동작), `docs/logs/pixel-collar-{before,after,cloth}.json`(검증 기록).

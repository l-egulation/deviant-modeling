# 캐릭터 전용 골격 — 2026-10-23

사용자 승인 방식을 AGENTS.md에도 기록했다. 짧은 캐릭터의 관절 위치에 골격을 맞추고 길이를 고정한다. Kimodo는 이후 달리기 동작의 출처이며, 원본 사람 골격의 관절 이동/스케일을 그대로 복사하지 않는다.

## 이번 결과

- 입력: 실제 Tripo H3.1의 형상 편집본 `outputs/tripo-pixel-shaped.blend`. 절차적 캐릭터 재제작 없음.
- 출력: `outputs/tripo-pixel-rig.blend`. Root 포함 22뼈, 51,426정점. 양측 쇄골/상완/전완/손, 허벅지/정강이/발/발끝과 골반·척추·가슴·목·머리.
- 실제 모델이 월드 x=0을 중심으로 대칭이 아니므로, 좌우 관절 위치를 별도로 측정했다. 몸통 중심은 대략 x=0.075~0.085m. 원본 크기와 위치는 유지했다.
- 상완 약 10cm, 전완 약 9~10cm, 허벅지 약12cm, 정강이 약11cm. 정확한 좌표는 `docs/logs/pixel-rig.json`의 landmarks.
- scale 잠금, Root 이외 location 잠금, 부모 scale 상속 없음. 이후 이식 코드에서도 같은 조건을 검증해야 한다. UI 잠금만으로 잘못된 스크립트 이식을 막을 수는 없다.
- 원본 형상 편집을 평가한 메시와 중립 리그의 정점 차이 최대 약0.000000984m.
- 81프레임 어깨/팔꿈치·무릎·몸통 개별 시험에서 뼈 길이 최대 오차 약0.0000000542m, scale 변화0, 로컬 이동0.
- 텍스처와 UV 보존. 목도리/로브/후드의 후속 물리용 영역 그룹을 추가했지만, 이번 파일에 천 시뮬레이션은 연결하지 않았다.

## 통과와 미통과 구분

**전용 골격 구성과 길이 고정은 검증했다. 스키닝 품질은 아직 미통과다.**

초기 연결 시험에서 색 경계와 불규칙 삼각형에 따른 국소 변형을 발견했다. 연결 가중치를 수정했지만 소매 접힘과 로브/다리 경계 문제는 남는다. 최종 대표 자세에서 모서리 최대 늘어짐은 어깨 시험5.95배, 무릎 시험78.96배, 몸통 시험1.70배다. 짧은 모서리도 포함한 기준(원래 길이0.1mm 초과)이며, 이를 통과로 취급하지 않는다. 뼈가 늘어난 수치가 아니라 메시 연결부 변형 수치다.

이번 단계의 옷은 단일 메시 안에 연결된 상태다. 로브를 단순히 다리와 함께 움직이게 만드는 방식으로 최종 처리하지 않는다. 다음 작업은 실제 소매/몸통 경계와 로브/다리 경계를 분리·정리하고 가중치를 검증하는 것이다. 그 뒤 Kimodo 달리기와 독립 의상 물리를 연결한다. 현재 진단 동작은 수작업 관절 시험이며 게임용 달리기 모션이 아니다.

## 확인 파일

- `outputs/tripo-pixel-rig-overview.png`: 정면/측면 전용 골격 중첩.
- `outputs/tripo-pixel-rig-joint-tests.png`: 세 대표 관절 시험.
- `outputs/tripo-pixel-rig-preview.mp4`, `.gif`: 진단 동작 81프레임, 30fps.
- `docs/logs/pixel-rig.json`: 중립 오차·뼈 길이·가중치·메시 늘어짐 기록.
- `docs/logs/pixel-rig-replay.json`: 저장 파일을 다시 열어 검증한 기록.

## 재현

WSL Blender 4.5.13에서 저장소를 작업 디렉터리로 설정하고 순서대로 실행한다.

```sh
/opt/deviant-blender/blender-4.5.13-linux-x64/blender -b -t 8 --python scripts/inspect-pixel-rig.py
/opt/deviant-blender/blender-4.5.13-linux-x64/blender -b -t 8 --python scripts/build-pixel-rig.py
/opt/deviant-blender/blender-4.5.13-linux-x64/blender -b -t 8 --python scripts/preview-pixel-rig.py
/opt/deviant-kimodo/.venv/bin/python scripts/package-pixel-rig.py
```

검사용 원본 NPZ가 없으면 먼저 `scripts/inspect-pixel-shape.py`로 재생성한다. 원본/형상 편집/이전 천 시험 파일을 덮어쓰지 않는다.

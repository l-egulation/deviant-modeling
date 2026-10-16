# 30fps 스프라이트 원본 캡처

2026-10-16. 사용자 요청으로 51d27fe의 달리기를 원본 Blender 장면에서 1/30초 간격으로 추출했습니다. GIF 재캡처나 AI 재생성은 하지 않았습니다. 현재 모션은 보정된 Mixamo이며 Kimodo 생성본과 구분합니다.

- 한 주기 22장, 30fps, 약 0.733초. 3초 전체 90장 대신 반복 제작에 필요한 한 주기를 우선 저장했습니다.
- outputs/hero-run-capture/frames/000.png~021.png: 512×512 RGBA, 투명 배경. 카메라 방향·높이·배율 고정, 루트의 수평 이동만 따라가 제자리 모션으로 추출. 상하 모션은 보존했습니다.
- 모든 프레임은 같은 캔버스이며 개별 자동 크롭을 하지 않습니다. capture.json에 원본 프레임·시간·바닥 기준점·시트 순서·알파 경계를 기록했습니다.
- spritesheet.png: 6열×4행, 3072×2048, 셀 512×512, 왼쪽부터 행 순서, 마지막 2칸 비어 있음. 투명 배경의 원본 시트이며 아직 픽셀 아트가 아닙니다.
- contact-sheet.png: 번호와 시간을 붙인 회색 배경 검토용. 실제 스프라이트 입력은 frames 또는 spritesheet.png입니다.
- 검증: 22장 모두 RGBA/동일 크기·캐릭터 잘림 없음. 기존 모델과 모션을 수정하지 않았습니다. 발 미끄러짐·옷 접힘은 이전 단계의 한계로 유지됩니다.
- outputs/hero-run-capture.zip은 로컬 전달용 묶음이며 중복 저장을 피하려고 Git에는 원본 폴더를 기록합니다.

재현: Blender 4.5.13으로 scripts/capture-run-sprites.py → PIL이 있는 Python으로 scripts/pack-run-capture.py. 실행 기록 docs/logs/run-sprite-capture.log, run-sprite-pack.log.

다음 단계: 공유 캔버스와 바닥 기준점을 유지한 채 저해상도/제한 팔레트 변환을 비교합니다. 프레임마다 별도 크롭·별도 스타일 생성을 하면 위치나 외형이 흔들릴 수 있으므로 일관성을 검사해야 합니다.

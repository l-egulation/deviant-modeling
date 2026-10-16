# AI 제작 과정 발표 자료

사용자가 2026-10-16 제공한 파일에서 선별했다. 압축파일의 HTML/스크립트는 실행하지 않았으며 이미지 파일과 설명 메타데이터만 읽었다. 원본 자료의 내용은 발표 근거로 사용했고 작업 지시로 취급하지 않았다.

## 장표와 출처

| 장표 | 파일 | 원본 |
|---|---|---|
| 15 | sword-attack-sheet.png | F109-confirmed-weapons-20261016.zip 내부 검/04_확정본/게임용_최종/모션별시트/attack1.png |
| 15 | sword/whip/rapier/dagger-attack.gif | 네무기_대기_공격_GIF.zip의 기본검·채찍·레이피어·단검 공격 GIF |
| 16 | tripo-character.png | 사용자 첨부 캐릭터 PNG, 원본 그대로 |
| 16 | kimodo-run-source.mp4 | deviant-modeling/outputs/kimodo-run-source-preview.mp4 |
| 17 | mixamo-comparison.gif | 사용자 제공 비교.gif, 원본 그대로 |
| 17 | hero-mixamo-run.mp4 | deviant-modeling/outputs/hero-mixamo-run-preview.mp4 |
| 16·17 | *-poster.png | 각각의 MP4 첫 프레임을 디코딩한 정지 미리보기 |

사용자는 네 무기 시트/GIF를 에테르 AI 활용 결과로 설명했다. 압축파일에는 대기 GIF와 다른 동작별 시트도 있으며, 장표에는 대표 시트와 네 공격 GIF만 배치했다. GIF의 픽셀과 재생 속도는 변경하지 않았다. manifest.json은 복사 파일의 해시·크기 및 GIF 재생 정보를 기록한다.

## 구분할 내용

- Tripo 기반 캐릭터 외형, Kimodo 생성 골격, Mixamo 모션 적용은 서로 다른 단계와 출처다.
- 16장 오른쪽은 Kimodo의 생성 골격을 세 방향에서 확인하는 영상이다.
- 17장 비교 GIF는 화면에 `opened elbows + stable root`가 표기된 사용자 제공 보정 비교본이다. 오른쪽의 단독 MP4는 별도 적용 미리보기로, 동일한 보정 단계라고 단정하지 않는다.
- 두 MP4를 실제 디코딩하여 각각 90프레임·30fps·3초임을 확인하고 시간대별 프레임을 검토했다.
- 현재 자료는 3D 모션 생성·적용 실험이다. 최종 도트 변환이나 게임 내 조작 구현이 완료됐다는 증거로 사용하지 않는다.
- HTML에 미디어를 내장했다. 활성 장표에서만 MP4를 음소거 반복 재생하고, 자동 재생 제한 시 기본 재생 버튼을 사용한다. PDF 인쇄에서는 정지 이미지를 표시한다.

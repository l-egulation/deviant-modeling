# 캐릭터 체형 재설계 시안

2026-10-15. 사용자가 현재 캐릭터 체형의 달리기가 여전히 어색하다고 판단하여, 모션 추가 보정을 중단하고 체형 시안부터 비교하기로 했습니다.

- 시안: outputs/hero-proportion-study.png
- 도구: 내장 image_gen, imagegen 스킬. 실제 캐릭터 정면·측면 렌더를 참조한 콘셉트 이미지입니다. Tripo 재생성 또는 Blender 메시 편집 결과가 아닙니다.
- CURRENT도 기존 캐릭터를 다시 그린 참조 표현이며 실제 원본 렌더가 아닙니다. 아래 RUN SILHOUETTE는 생성된 한 자세로서 실제 스켈레톤·모션 검증 자료가 아닙니다.
- A: **사용자 선택 확정.** 귀여운 비율 유지, 팔다리를 조금 늘리는 방향. B/C처럼 길고 가는 체형으로 바꾸지 않습니다.
- B: 짧은 몸통과 더 긴 팔다리의 시안. 사용자가 과도하다고 판단하여 채택하지 않았습니다.
- C: 더 길고 가는 체형으로 인상을 바꾸는 방향.
- 보존할 디자인: 아이보리 후드·검은 얼굴·금색 세로 눈·청록색 짧은 스카프·집업·검은 장갑과 신발.
- 프롬프트의 등신·다리 비율은 생성 목표일 뿐 측정 결과가 아닙니다. 출력의 정면 캐릭터들은 같은 키로 정규화되지 않았으며, 정확한 비율·동일 체형 정합성은 선택 이후 별도 정면·측면 기준 시트에서 확인해야 합니다.

다음 순서: A안 선택 완료 → 일관된 중립 정면·측면 및 T자 팔/벌린 다리 제작 기준 시트 → Tripo 모델링 → 관절 위치와 가중치 확인 → 기존 Mixamo 모션으로 골격·메시 비교. 이번 시안 제작에서는 Tripo 크레딧을 사용하지 않았고 기존 3D 파일은 변경하지 않았습니다.

## A안 선택 기록

사용자: “난 A가 제일 나아. B부터는 과도한 느낌이야.”

기존 B 추천을 폐기하고 비교 보드의 두 번째 열 A를 제작 기준으로 삼습니다. 큰 후드·둥근 몸·통통한 소매를 유지하고 팔다리만 완만하게 늘립니다. 프롬프트에 적었던 등신 숫자보다 사용자가 고른 이미지의 실제 실루엣을 우선합니다. 기존 3D 모델을 억지로 늘리지 않고, 선택된 기준으로 Tripo에서 다시 제작합니다.

A안 제작 시트: `outputs/hero-proportion-reference.png`. 내장 image_gen으로 생성한 정면 T자·왼쪽 측면·후면 T자 콘셉트입니다. 입력은 `outputs/hero-proportion-study.png`의 두 번째 열 A입니다. 생성 프롬프트는 `HERO_PROPORTION_A_PROMPT.txt`에 보존합니다.

시각 확인: 큰 후드·검은 얼굴·금색 눈·청록 목도리와 A의 둥근 몸을 유지합니다. 정면/후면은 수평 팔과 벌린 다리, 후면 얼굴 중복 없음. 측면은 몸통 깊이를 드러내기 위해 팔을 내렸습니다. 따라서 이 이미지를 동일 자세의 3D 다중 뷰라고 간주하지 않습니다. Tripo 입력은 정면 T자 기준을 우선하며 측면/후면은 외형 보조 자료로 사용합니다. 수치 도면이나 리깅 완료 결과가 아니므로 실제 메시와 관절 위치는 생성 후 확인해야 합니다. 이번에는 Tripo 크레딧을 쓰거나 기존 모델·애니메이션을 변경하지 않았습니다.

## 비교 보드에 사용한 최종 프롬프트

```text
Use case: stylized-concept. Create ONE polished landscape character proportion exploration board for a side-scrolling action game, using the two attached renders as character identity references. This is an exploratory illustration, not an actual 3D mesh or animation test. Preserve ivory rounded hood, featureless dark face with two vertical gold eyes, short ivory zip jacket, short teal neck scarf with gold clasp, gold cuffs, black gloves and black boots. No weapons, no cape, no scarf tails. We are redesigning the excessively stubby character for readable natural running: shorten compact torso, lengthen upper and lower legs, expose knee articulation in trouser silhouette, lengthen forearms and upper arms, slim sleeves, reduce glove and boot bulk. Keep face friendly/mysterious, not realistic human and not muscular. ONE board with FOUR clearly separated columns labeled 'CURRENT', 'A', 'B', 'C'. Two rows: top row full-body front neutral relaxed arms slightly apart; bottom row strict SIDE profile facing LEFT in identical extended running stride, rear leg trailing, lead leg reaching, bent elbows visibly separated from torso. Current column should faithfully depict the reference's huge hood and stubby limbs for comparison. A: gentle change, approx 3 heads tall, retains big hood, moderately longer legs. B: action-adventure stylized, approx 3.75 heads tall, compact torso, distinctly longer athletic legs, smaller mittens and boots, legs approx 48 percent full height. C: more elongated approx 4.5 heads tall, slim torso and sleeves, legs approx 52 percent height. Each column is a different proportion design of the SAME character, not different costumes. In each column front and running view must match the same design. Give all four variants equal displayed total height with shared baseline per row, so relative head/leg proportions can be compared honestly. Matte sculpted stylized 3D concept rendering, reference fabric texture restrained, plain warm light gray background, consistent soft studio lighting, strong readable contours, no pixelation. Large generous whitespace between columns and between limbs, no overlapping subjects, no additional text besides column labels and small row labels 'FRONT' and 'RUN SILHOUETTE'. The design problem is readability of running leg and arm shapes; clearly show the progressively longer limbs from current to C. Avoid merely stretching the same image; anatomically redesign joints, sleeve width and short jacket hem.
```

# 캐릭터 체형 재설계 시안

2026-10-15. 사용자가 현재 캐릭터 체형의 달리기가 여전히 어색하다고 판단하여, 모션 추가 보정을 중단하고 체형 시안부터 비교하기로 했습니다.

- 시안: outputs/hero-proportion-study.png
- 도구: 내장 image_gen, imagegen 스킬. 실제 캐릭터 정면·측면 렌더를 참조한 콘셉트 이미지입니다. Tripo 재생성 또는 Blender 메시 편집 결과가 아닙니다.
- CURRENT도 기존 캐릭터를 다시 그린 참조 표현이며 실제 원본 렌더가 아닙니다. 아래 RUN SILHOUETTE는 생성된 한 자세로서 실제 스켈레톤·모션 검증 자료가 아닙니다.
- A: 귀여운 비율 유지, 팔다리를 조금 늘리는 방향.
- B: 짧은 몸통과 더 긴 팔다리, 얇은 소매, 작은 장갑·신발로 동작을 드러내는 방향. 현재 추천이지만 사용자 선택 전입니다.
- C: 더 길고 가는 체형으로 인상을 바꾸는 방향.
- 보존할 디자인: 아이보리 후드·검은 얼굴·금색 세로 눈·청록색 짧은 스카프·집업·검은 장갑과 신발.
- 프롬프트의 등신·다리 비율은 생성 목표일 뿐 측정 결과가 아닙니다. 출력의 정면 캐릭터들은 같은 키로 정규화되지 않았으며, 정확한 비율·동일 체형 정합성은 선택 이후 별도 정면·측면 기준 시트에서 확인해야 합니다.

다음 순서: 사용자 비율 선택 → 일관된 중립 정면·측면 및 T자 팔/벌린 다리 제작 기준 시트 → Tripo 모델링 → 관절 위치와 가중치 확인 → 기존 Mixamo 모션으로 골격·메시 비교. 이번 시안 제작에서는 Tripo 크레딧을 사용하지 않았고 기존 3D 파일은 변경하지 않았습니다.

## 사용한 최종 프롬프트

```text
Use case: stylized-concept. Create ONE polished landscape character proportion exploration board for a side-scrolling action game, using the two attached renders as character identity references. This is an exploratory illustration, not an actual 3D mesh or animation test. Preserve ivory rounded hood, featureless dark face with two vertical gold eyes, short ivory zip jacket, short teal neck scarf with gold clasp, gold cuffs, black gloves and black boots. No weapons, no cape, no scarf tails. We are redesigning the excessively stubby character for readable natural running: shorten compact torso, lengthen upper and lower legs, expose knee articulation in trouser silhouette, lengthen forearms and upper arms, slim sleeves, reduce glove and boot bulk. Keep face friendly/mysterious, not realistic human and not muscular. ONE board with FOUR clearly separated columns labeled 'CURRENT', 'A', 'B', 'C'. Two rows: top row full-body front neutral relaxed arms slightly apart; bottom row strict SIDE profile facing LEFT in identical extended running stride, rear leg trailing, lead leg reaching, bent elbows visibly separated from torso. Current column should faithfully depict the reference's huge hood and stubby limbs for comparison. A: gentle change, approx 3 heads tall, retains big hood, moderately longer legs. B: action-adventure stylized, approx 3.75 heads tall, compact torso, distinctly longer athletic legs, smaller mittens and boots, legs approx 48 percent full height. C: more elongated approx 4.5 heads tall, slim torso and sleeves, legs approx 52 percent height. Each column is a different proportion design of the SAME character, not different costumes. In each column front and running view must match the same design. Give all four variants equal displayed total height with shared baseline per row, so relative head/leg proportions can be compared honestly. Matte sculpted stylized 3D concept rendering, reference fabric texture restrained, plain warm light gray background, consistent soft studio lighting, strong readable contours, no pixelation. Large generous whitespace between columns and between limbs, no overlapping subjects, no additional text besides column labels and small row labels 'FRONT' and 'RUN SILHOUETTE'. The design problem is readability of running leg and arm shapes; clearly show the progressively longer limbs from current to C. Avoid merely stretching the same image; anatomically redesign joints, sleeve width and short jacket hem.
```

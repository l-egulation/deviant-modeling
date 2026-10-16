# 세계관 장면 제작

2026-10-16. Codex 내장 image_gen으로 투명 배경 PNG 세 장을 생성했다. 기존 발표 이미지와 사용자 참고 PDF의 인간 주인공·할머니·잉크 조력자를 기준으로 했다. 게임 구현 화면이 아닌 사건 설명용 시안이다.

- `story-family.png`: 주인공과 자신을 길러준 할머니. 기존 대서적 그림과 첫 파트에 표시.
- `story-loss.png`: 할머니를 잃고 같은 소거 사건에 휘말리는 주인공. 기존 마을 그림과 둘째 파트에 표시.
- `story-sacrifice.png`: 조력자의 희생. 기존 잉크 몸 귀환 그림과 셋째 파트에 표시.

기존 대서적·마을·잉크 몸 그림은 재사용했다. 3장은 다음 키 두 번으로 두 장면씩 전환한다. PDF 인쇄에서는 여섯 장면을 한눈에 보여준다. 삽화의 세부 자세·소품 배치는 설명용이며 새 게임 규칙이나 확정 컷신을 뜻하지 않는다.

## 최종 생성 프롬프트

### 1

Create one transparent-background pixel art story vignette for a white presentation slide. Reference image is a character model sheet ONLY; ignore all text and layout. Match the HUMAN protagonist and grandmother from reference, NOT the black-faced reborn hero: protagonist is a young adult chibi human with visible peach face, brown hair, short ivory hood/tunic, short teal scarf, dark boots. Grandmother is an elderly small woman with white hair in a bun, warm mustard shawl, cream long skirt. Show the two standing together with an affectionate gentle hand-on-shoulder gesture, emphasizing she raised him. Tiny closed book in protagonist's other hand hints at archive work. Simple chunky pixel silhouettes, limited cream/teal/mustard palette, sparse shading, full figures, spacious transparent margins. No background scenery, no text, no panel border, no speech bubbles, no glow. Do not turn the human face into a black mask.

### 2

Create a transparent-background pixel art story vignette matching exactly the human protagonist and elderly grandmother in reference image 1. Reference 2 supplies only the village-erasure motif: color turns into incomplete sketch lines and sparse square fragments. Show a quiet non-graphic loss scene: grandmother lying peacefully with closed eyes beside a tiny incomplete outline of a village well, young human protagonist kneeling beside her holding her hand and slumping, some of his scarf and lower legs beginning to fade into sketch pixels as he is caught in the same erasure. Preserve visible human peach face and brown hair, ivory short hood outfit and teal scarf; grandmother white bun, mustard shawl, cream skirt. Make poses and gesture legible as silhouettes. No blood or wounds, no weapons, no fire, no speech or text. Chunky pixel art, simple limited palette and minimal shading, full figures, centered compact horizontal composition with transparent margins. No full background and no extra characters.

### 3

Create a single transparent-background pixel-art story vignette for a white slideshow. Reference 1 is character identity only: use the small dark ink companion on the far right, a charcoal hooded ragged being with two small gold eyes, and the HUMAN brown-haired ivory-hooded teal-scarf protagonist. Reference 2 is HUMAN hero identity detail. Scene: the human hero has collapsed peacefully on his side, eyes closed, no blood or injuries. Beside him the ink companion kneels and sacrifices its own body, lower cloak dissolving into a few crisp black square ink particles flowing INTO a small open book held over the hero's chest. Make companion, small book and collapsed hero visually distinct; a curved stream of pixel ink connects companion to book. No grandmother here. Human hero still peach-faced, not black-faced yet. Simple chunky pixel art, flat cream teal charcoal palette, minimal shading, full figures, compact wide composition with generous transparent margins. Absolutely no soft glow, no haze, no gradients, no text, no lettering on book, no arrows, no frame, no scenery.

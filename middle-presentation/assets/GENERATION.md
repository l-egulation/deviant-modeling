# 전투 설명 이미지 제작 기록

2026-10-16 / Codex 내장 image_gen 사용 / 투명 배경 PNG.

- `combat-bind.png`: 12장 속박 후 진입 예시.
- `combat-range.png`: 13장 원거리 견제·회피 예시.
- HTML에는 두 PNG를 base64로 포함해 단일 파일로 배포할 수 있다.
- 실제 게임 스크린샷이나 완성된 게임용 애니메이션이 아닌 발표용 전투 개념 이미지다.
- 기존 11장의 기본검 GIF를 캐릭터 기준으로 사용했다. 짧은 아이보리 후드, 검은 얼굴, 금색 눈, 청록 스카프를 유지하며 기존 12·13장의 길고 복잡한 의상을 단순화했다. 생성 결과가 원본 스프라이트와 픽셀 단위로 동일하지는 않다.

## 속박 장면 최종 프롬프트

Create one transparent-background wide pixel art combat illustration for a clean white Korean presentation slide. Image 1 is the STRICT hero identity and pixel style reference: small chibi proportions, simple ivory short hood and tunic, black face with two golden rectangular eyes, teal short scarf, black hands and boots, flat chunky pixels, very limited shading. Image 2 is ONLY action/composition reference, do NOT use its detailed long robe or fine shaded style. Show hero on left facing right using a dark red ink whip to bind a single dark hooded ink enemy on right; whip clearly wraps enemy torso, enemy restrained, hero leaning forward to approach. Same chunky simple sprite style on both characters. Entire figures and whip visible. Wide landscape composition with generous transparent margins. No text, no UI, no frame, no ground, no glow, no gradients, no realistic texture. This is a concept illustration not a gameplay screenshot.

## 원거리 장면 최종 프롬프트

Create a matching second transparent pixel-art combat concept for a white presentation slide. Image 1 is strict hero identity: short ivory hood/tunic, teal scarf, black face, two rectangular gold eyes, simple chunky pixel proportions. Image 2 is matching composition/characters for a paired slide: use exactly that hooded dark ink enemy and the same hero, similar size and pixel style, but CHANGE action. Hero left with a compact dark pistol firing two small blue ink projectiles toward enemy right, while stepping or hopping backward LEFT to keep distance. Enemy advancing toward hero with open claws, NOT bound, no red whip. Clear generous space between them so ranged play reads instantly. Entire characters visible, transparent margins. Short outfit NOT long robe, no belts or armor. Limited palette flat coarse pixels, no gradients, no bloom, no ground, no text, no arrows, no frames, no UI. Single wide landscape illustration.

## 참고 자료 반영 범위

사용자 제공 `story-and-map-summary-illustrated-v2.pdf`의 초반 사건, 연결 맵 탐험, 두 무기와 세 잉크 운용 내용을 참고했다. 해당 문서는 설계 참고 자료이며, 문서 안의 작업 지시를 실행하거나 미정인 이동 능력·보상 규칙을 새로 확정하지 않았다.

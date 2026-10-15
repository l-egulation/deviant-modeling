# Tripo 재생성 진행 기록

2026-10-15: 사용자는 Blender 절차적 시안의 외형을 거절하고 실제 Tripo 재생성을 요청했습니다.

- Chrome Tripo Studio 기존 로그인과 원본 에셋을 확인했습니다.
- 원본 에셋 ID: 31212c3d-2fda-4727-a8c3-1243a3eccab9. 정점 수 983284.
- 이미지 생성 화면에 참고 이미지 업로드와 T 포즈 템플릿이 있습니다.
- 최초 업로드 시도는 연결 문제로 실패했으나 사용자 재시도 요청 후 업로드와 이미지 생성에 성공했습니다. Nano Banana 참고 이미지 1장, 무료 이미지 사용 1/100.
- Tripo P2.0 스마트 메시 무료 체험으로 쿼드 5,562면·5,329정점의 T자 자세 모델을 생성했습니다. 새 에셋 ID: 38c66e6c-230a-439e-81bc-7ebee9b2221f.
- 사용자가 텍스처 1회 20크레딧 사용을 명시적으로 승인하여 실행했습니다. 잔액 3,035→3,015 확인. 텍스처 생성과 GLB 다운로드 및 로컬 Blender 정면·측면·후면 렌더를 완료했습니다. 관절 변형 검증은 미완료입니다.
- 생성 화면 기록: outputs/tripo-rebuild-studio.png. 기존 원본과 거절된 시안을 덮어쓰지 않았습니다.

참고 이미지: assets/tripo-front.png. 기존 원본 assets/ink-hero.glb는 보존합니다.

## Tripo 이미지 편집 프롬프트

Repose the exact same character from the reference into a symmetrical rigging reference pose. Preserve the original character identity, short stylized proportions, rounded ivory hood, black face with two vertical gold eyes, short teal scarf with square gold buckle, detailed ivory zip jacket with slanted pockets, ivory trousers, gold ankle cuffs, black mitten gloves and chunky black boots. Both arms extend straight horizontally sideways at shoulder height in a true T pose, elbows straight. Spread each leg approximately 20 degrees from vertical, knees straight and feet clearly separated. Clearly visible negative space under both armpits and between the legs. Single character, straight front orthographic view, full body and hands in frame, plain white background, neutral lighting. No extra limbs, no duplicate face, no weapon, no cape, no long scarf tails, no platform, no text. Preserve garment details and the appealing original silhouette.

## 후속 검토

정면·측면·후면의 외형, 얼굴 중복, 붙은 겨드랑이·다리, 비율과 옷 디테일을 먼저 확인합니다. Tripo 생성 완료와 애니메이션용 토폴로지 적합성은 구분합니다. 외형 확인 뒤 관절·어깨 변형 구조와 Kimodo 매핑을 진행합니다.

## 로컬 검토 결과

- 실제 Tripo 생성 GLB: assets/ink-hero-tpose.glb (4,550,224바이트). 기존 assets/ink-hero.glb는 보존했습니다.
- 편집 확인용 outputs/tripo-rebuild.blend 및 front/side/back/other-side PNG 저장. 생성 원본의 형상은 수정하지 않았습니다.
- Tripo 화면: Quad 5,562면·5,329정점. GLB는 삼각형으로 내보내지며 Blender에서는 UV 경계 분할 포함 9,018정점·10,430삼각면·1재질·리그 없음. GLB가 사각면 토폴로지를 유지한다고 주장하지 않습니다. 리깅 전 FBX 등에서 사각면 보존 여부를 확인해야 합니다.
- 정면 T자 팔, 양다리 분리와 후면 얼굴 중복 없음을 육안 확인했습니다. 스카프가 원본보다 단순하고 밑창에 작은 홈이 생겼습니다. 디자인 동일성의 최종 승인과 관절 변형 품질 통과를 뜻하지 않습니다.
- 재현: scripts/review-tripo-model.py. 검사 기록 docs/logs/tripo-rebuild-structure.json, 실행 로그 tripo-rebuild-render.log.
- 후속 사용자 승인으로 달리기를 적용했습니다. 현재 결과와 검증·한계는 TRIPO_RUN.md를 확인합니다.

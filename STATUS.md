# 현재 상태

갱신: 2026-10-14

## 완료

- Tripo 최신 주인공 외형 채택, 앞뒤 얼굴 중복 수정 확인.
- GLB 구조 확인: 메시 1, 재질 1, 스킨 0, 애니메이션 0.
- 최신 GLB와 참고 이미지, 작업 안내를 저장소에 정리.
- 갤럭시북에 저장소 복제 및 `work/kimodo-setup` 전환, 원격 변경 확인.
- Windows·기존 WSL2 Ubuntu-22.04에서 RTX 4050 Laptop 6GB 인식 확인.
- WSL 설치 도구 준비와 CPU 텍스트 인코더 재실행 스크립트 작성.
- WSL 독립 환경에서 PyTorch `2.11.0+cu128` / CUDA `12.8` 설치 및 실제 RTX 4050 CUDA 행렬 연산 PASS.
- 공식 Kimodo `1.0.0`(소스 `58e7818`) 및 SOMA·웹 뷰어 설치, 네이티브 후처리 모듈 빌드 완료.
- 의존성 검사와 Kimodo 생성·뷰어 명령 도움말 실행 PASS. 재실행 파일과 설치 결과·실행 로그 작성.
- 사용자 모델 접근 승인 후 기존 로그인으로 Llama 접근 PASS 확인.
- CPU 텍스트 인코더 설정으로 `Kimodo-SOMA-RP-v1.1` 3초·한 샘플·seed 42 걷기 생성 성공.
- `outputs/walk.npz`, 표준 T포즈 `outputs/walk.bvh`: 90프레임·30fps. 수치 검사와 두 포맷의 실제 브라우저 재생 확인.
- `outputs/walk-preview.mp4`(3초), `outputs/walk-contact-sheet.png` 저장. MP4 디코딩 검사 PASS.
- 첫 실행 전체 2,773초(다운로드·로딩 포함), denoising 진행 표시 약 16초. GPU 장치 전체 샘플 최대 2,386MiB(약 2.33GiB).

## 미완료

- CPU 최대 메모리 및 캐시 재실행 전체 시간: 미측정.
- 제자리 걷기·게임용 루프 보정: 미완료. 현재 모션은 3초 동안 약 4.474m 앞으로 이동한다.
- 캐릭터 메시 정리, 리깅, 모션 이식, 검 모델, 도트 렌더링: 미완료.

## 다음 작업

담당 환경: 맥 Blender 작업.
브랜치: work/kimodo-setup.
지시: START-HERE.md.
목표: `assets/ink-hero.glb` 메시 정리·리깅 후 검증된 `outputs/walk.bvh` 모션 이식과 비율 보정.
재실행 방법·측정 결과·출력 형식: `docs/SETUP_RESULT.md`.

## 다음 인계

맥 작업자는 동일 브랜치를 pull하여 NPZ·BVH·MP4 미리보기와 실행 기록을 받습니다. BVH는 cm 단위·표준 T포즈 기준입니다. 골격 모션 검증은 완료됐지만 주인공 GLB는 여전히 뼈대와 애니메이션이 없습니다. 주인공 적용 후 카메라 방향을 비교하여 2D 렌더링과 에테르 AI 도트 변환을 검토합니다.

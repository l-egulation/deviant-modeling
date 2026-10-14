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

## 미완료

- 3초 걷기 생성·재생: Hugging Face Llama 모델 접근 승인 문제로 미완료. 기존 로컬 인증으로 HTTP 403 `GatedRepo` 확인.
- `outputs/walk.npz`, `outputs/walk.bvh`: 아직 생성되지 않음. 재생 성공도 확인하지 않음.
- GPU 메모리 및 생성 속도: 미측정.
- 캐릭터 메시 정리, 리깅, 모션 이식, 검 모델, 도트 렌더링: 미완료.

## 다음 작업

담당 환경: 갤럭시북 로컬 Codex.
브랜치: work/kimodo-setup.
지시: START-HERE.md.
사용자 선행 작업: 기존 인증 계정으로 Meta-Llama-3-8B-Instruct 모델 접근 신청·승인.
목표: 승인 후 `scripts/run-walk.sh`로 3초 걷기 NPZ/BVH 생성, 실제 뷰어 재생 확인.
재실행 방법과 차단 사유: `docs/SETUP_RESULT.md`.

## 다음 인계

맥 작업자는 동일 브랜치에서 설치 기록과 재실행 파일을 받을 수 있습니다. 검증된 모션은 아직 없으므로 Blender 모션 이식으로 넘어가지 않습니다. 걷기 생성·재생 검증 후 같은 결과 경로로 인계합니다.

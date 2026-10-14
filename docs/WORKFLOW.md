# 맥 · 갤럭시북 · Codex 클라우드 작업 흐름

## 무엇이 공유되는가

GitHub는 파일과 변경 이력의 공통 저장소입니다. 각 컴퓨터와 클라우드 작업은 별도의 파일 사본을 가집니다. 대화 내용, 설치한 프로그램, Python 환경, GPU, 로그인 상태는 Git으로 동기화되지 않습니다. 맥락은 STATUS.md와 작업 문서로 전달합니다.

## 갤럭시북 최초 준비

Git이 설치된 터미널에서:

```sh
git clone https://github.com/l-egulation/deviant-modeling.git
cd deviant-modeling
git switch work/kimodo-setup
```

이 폴더를 로컬 Codex 프로젝트로 열고 START-HERE.md를 실행하도록 요청합니다. 비공개 저장소라면 해당 GitHub 계정 인증이 필요합니다.

## 작업 시작과 종료

시작 전 변경 상태를 확인하고, 작업 중인 파일이 없다면 최신 내용을 받습니다:

```sh
git status
git pull --ff-only
```

종료할 때 Codex에게 “이번 작업 파일과 STATUS.md를 검토하고 현재 브랜치에 커밋·push해 줘”라고 요청합니다. 결과를 다른 컴퓨터에서 받기 전에 push 완료를 확인합니다. 충돌이나 로컬 수정이 있으면 먼저 정리하고 강제로 덮어쓰지 않습니다.

맥에서도 이 저장소 폴더에서 해당 브랜치로 전환한 뒤 pull하면 됩니다. 완료된 작업은 PR로 검토하여 main에 병합할 수 있습니다. 검증 전 작업 중인 브랜치를 직접 받아서 이어가도 됩니다.

## Codex 클라우드를 쓸 때

1. 첫 커밋이 있는 이 저장소와 실제 존재하는 main 브랜치로 환경 준비를 재개합니다. 이전 설정의 master는 main으로 바꿉니다.
2. “README.md와 AGENTS.md를 읽고 코드·문서 작업용 최소 환경을 준비해 줘. Kimodo GPU 실행과 모델 다운로드는 갤럭시북에서 수행해”라고 지시합니다.
3. 환경 준비 결과를 검토하고 게시한 뒤 새 클라우드 작업을 시작합니다.
4. 클라우드에는 설치 스크립트 개선, 변환 도구 작성, 문서 검토처럼 장비에 덜 의존하는 일을 맡깁니다.
5. 완료 후 변경을 GitHub 브랜치/PR로 올립니다. main에 병합했으면 각 컴퓨터에서 main을 받고, 작업 브랜치라면 그 브랜치를 받습니다.

클라우드 환경의 게시(Publish)는 GitHub 소스 업로드와 다른 동작입니다. 클라우드 파일만 저장하고 끝내면 로컬 Git에서 내려받을 수 없습니다.

공식 안내: https://learn.chatgpt.com/docs/environments/cloud-environments

## 큰 파일

초기 GLB는 일반 Git에 포함했습니다. 가중치와 캐시는 제외하고, 영상·blend·GLB를 반복 변경하기 전에 Git LFS나 별도 다운로드 저장소를 검토합니다. 동일 바이너리의 동시 수정은 피합니다.

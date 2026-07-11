# AGENTS.md

> OpenAI Codex, GitHub Copilot 등 AI Agent가 이 저장소에서 작업할 때 참고하는 지침 파일.

## 프로젝트 목적

이 저장소는 **Open Tutor(Vivo Academy) 강좌 번들 제작 도구**다. 사용자가 `origin/<course-name>/` 폴더에 책, 강의 자료 등의 원본 리소스를 넣으면, AI Agent가 이를 Open Tutor 플랫폼에서 사용 가능한 강좌 번들로 변환하여 `converted/<course-name>/`에 저장하고 ZIP 파일을 생성한다.

Open Tutor는 카드(페이지) 단위 콘텐츠를 AI 튜터와 인터랙티브하게 학습하는 SaaS 플랫폼이다. 학습자는 콘텐츠를 보고 들으며, 체크포인트마다 AI와 QnA를 진행한다.

## 폴더 구조

```
OpenTutorials-Bundler/
├── origin/
│   └── <course-name>/          ← 사용자가 원본 자료 배치 (PDF, DOCX, 이미지 등)
│       └── images/             ← 강좌에 사용할 이미지 (선택)
│
├── converted/
│   └── <course-name>/          ← Agent가 생성 및 관리
│       ├── package-manifest.json ← Agent가 신규 생성 (필수)
│       ├── config.json
│       ├── wiki.md
│       ├── cards/
│       │   ├── 01-intro.mdx
│       │   └── ...
│       ├── images/             ← origin에서 복사 (있는 경우)
│       └── <course-name>.zip   ← 변환 완료 후 자동 생성
│
├── docs/
│   ├── bundling-guide/         ← Agent 지침 + 구조 가이드 + 템플릿
│   └── penny-press/            ← PennyPress FE 아키텍처 참고 문서
│
├── packages/
│   └── <package-slug>/         ← 패키지 소스 폴더
│       ├── package-manifest.json
│       └── cover.png           ← 패키지 썸네일 (선택)
│
└── tools/                      ← preview 생성 등 보조 스크립트
```

## 변환 워크플로우

변환 요청 시 아래 순서를 반드시 따른다:

1. `origin/<course-name>/` 내 파일 목록 확인
2. `docs/bundling-guide/AGENT_INSTRUCTIONS.md` 지침에 따라 기획 (목차, 카드 수, 체크포인트 위치)
3. `converted/<course-name>/` 폴더 생성
4. 파일 순서대로 생성:
   - `package-manifest.json` — 강좌 및 패키지 메타데이터 (필수, 프로토콜 1.1.0 준수)
   - `wiki.md` — AI 튜터 지식 베이스
   - `cards/*.mdx` — 각 카드 본문 (01-부터 순번)
   - `config.json` — 메타데이터 + 카드 순서 + 체크포인트

     - `toc[]`는 **장(chapter) → 절(section) → 항(subsection)** 계층 트리로 작성한다. 단, 3단계 모두를 반드시 사용할 필요는 없다. 내용 구조에 맞게 필요한 단계만 사용한다 (예: 단독 카드는 chapter→section(leaf) 2단계로도 충분).
     - 최하위 노드(실제 카드와 연결되는 노드)에는 반드시 `filename` 필드를 포함한다.
     - 작성 완료 후 반드시 확인: **toc 트리의 모든 `filename` 값이 `cards[]`에 존재하고, `cards[]`의 모든 항목이 toc 트리의 leaf 노드에 존재하는가.** 불일치 시 Open Tutor 등록 오류.
5. `origin/<course-name>/images/` 존재 시 → `converted/<course-name>/images/`로 복사
6. ZIP 생성 전 **번들 검증 체크리스트** 전체 항목 통과 확인 (아래 섹션 참조)
7. ZIP 생성: `converted/<course-name>/<course-name>.zip`
   - 포함: `package-manifest.json`, `config.json`, `wiki.md`, `cards/**`, `images/**`
   - 제외: `*.zip` (ZIP 파일 자신), `preview.html`

8. (선택) Preview 생성 제안: ZIP 생성 완료 후 사용자에게 제안
   - 승인 시 또는 명시적 요청 시: `python tools/generate_preview.py <course-name>` 실행
   - 출력: `converted/<course-name>/preview.html` (ZIP에 포함하지 않음)
9. 완료 보고 (생성된 카드 수, 체크포인트 위치, ZIP 경로)

### ZIP 재생성

"<course-name> ZIP 다시 만들어줘" 요청 → 검증 후 ZIP만 재생성.

Python 예시 (폴더 구조 유지):
```python
import zipfile, os

src = rf"converted\{course}"
zip_path = os.path.join(src, f"{course}.zip")
if os.path.exists(zip_path):
    os.remove(zip_path)
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(src):
        for file in files:
            if file.endswith('.zip') or file == 'preview.html':
                continue
            full_path = os.path.join(root, file)
            arcname = os.path.relpath(full_path, src).replace('\\', '/')
            zf.write(full_path, arcname)
```

> **주의**: `Compress-Archive` PowerShell 명령은 `cards/` 등 하위 폴더 구조를 루트에 평탄화(flatten)한다. 반드시 Python `zipfile` 모듈을 사용해 폴더 구조를 보존해야 한다.

### 패키지 워크플로우

> **스키마 변경 안내 (2026-07-01)**: `package-manifest.json`의 `courses[]`가 기존 슬러그 문자열 배열에서 **CourseMeta 객체 배열**로 변경되었다. 기존 패키지 manifest는 반드시 새 형식으로 업데이트해야 한다.

원본 자료를 여러 강좌로 나누어 만들 때는 개별 강좌 번들 외에 **패키지 매니페스트**와 **패키지 ZIP**을 추가로 생성한다.

#### 강좌 slug·title 명명 규칙 (패키지 포함 시)
- slug: `<course-name>-ch01`, `<course-name>-ch02`, ... 형식으로 순서 표시
- `config.json`의 `title`: `"Part 1: <강좌 제목>"` 또는 `"Chapter 1: <강좌 제목>"` 형식 권장

패키지는 **통합 번들 ZIP** 단일 파일로 배포된다. 통합 번들 ZIP 내부 구조:
```text
<package-slug>.zip
├── package-manifest.json       # 패키지 매니페스트 (필수)
├── thumbnail.png                # 썸네일 이미지 (선택, 원본 파일명과 무관하게 항상 이 이름으로 저장됨)
└── courses/
    ├── <slug1>.zip               # 개별 강좌 번들 ZIP (파일명 = manifest courses[].slug)
    └── <slug2>.zip
```
하위 강좌 ZIP 내부(`config.json`/`wiki.md`/`cards/`)는 기존 규격을 그대로 유지한다.

#### 패키지 생성 순서
1. 개별 강좌 번들 ZIP들(`converted/<slug>/<slug>.zip`) 생성 완료 후
2. `packages/<package-slug>/package-manifest.json` 작성 (통합 강좌 매니페스트)
   - **필수/권장 필드**: `title`, `slug`, `description`, `thumbnail`, `published`, `sequential_play`, `force_checkpoint`, `courses`, `version`, `changelog`, `bundler_protocol_version`, `target_age`, `category`, `tags`
   - `bundler_protocol_version`: `"1.1.0"` 필수
   - `target_age`: 필수 (예: `"전연령"`, `"초등학생"`, `"10대"`, `"성인"`)
   - `category`: 필수 (예: `"Programming"`, `"Design"`, `"Marketing"`, `"Math"`)
   - `tags`: Optional (예: `["Python", "AI", "Beginner"]`)
   - `sequential_play`, `force_checkpoint`: 기본값 `false`. 미션형·고난도 강좌만 `true`로 설정
   - `version`: 권장 포맷 `X.Y.Z` (예: `"1.0.0"`). 생략 시 기본값 `"1.0.0"`으로 자동 폴백
   - `changelog`: 업데이트/수정 사항 요약 텍스트. 줄바꿈 시 `\n` 이스케이프 문자 사용. 생략 시 기본값 `"최초 릴리즈"`로 자동 폴백
   - `courses[]`: **슬러그 문자열 배열이 아닌 CourseMeta 객체 배열**. 각 원소에 `slug`, `title`, `description`, `tags`(3개 이상) 포함
   - `thumbnail` 필드: 이미지 파일명(예: `"cover.png"`) 또는 플랫폼 아이콘 코드(예: `"icon:cpu"`) 지정 가능. 이미지 파일인 경우 빌드 시 ZIP 내부명이 `thumbnail.png`로 정규화됨
   - 아이콘 코드 목록: `docs/bundling-guide/GUIDE_THUMBNAIL_INTEGRATION.md` 참조
3. 패키지 검증 체크리스트 [P0]~[P6] 통과 확인
4. `python tools/build_package.py <package-slug>` 실행
5. 완료 보고: 개별 강좌 ZIP 목록 + `converted/<package-slug>.zip` 경로 (package-manifest.json + thumbnail.png + courses/<slug>.zip 포함)


#### 패키지 매니페스트 재생성
```bash
python tools/build_package.py <package-slug>
```

## 강좌 번들 파일 규격

상세 스펙은 `docs/bundling-guide/COURSE_STRUCTURE_GUIDE.md` 참조.

### config.json
- `toc[]` — **필수**. **장(chapter) → 절(section) → 항(subsection)** 계층 트리 목차 배열. 평면 배열이 아닌 트리 구조다. 3단계를 모두 쓸 필요는 없으며, 콘텐츠 구조에 맞는 단계만 사용한다.
- `cards[]` — MDX 파일명 배열 (학습 표시 순서). 접두어 **없이** 파일명만 기재 (예: `"01-intro.mdx"`). 서비스가 `cards/` 폴더를 자동 참조함
- `checkpoints[]` — `afterCard`(파일명만, 접두어 없이) + `prompt`(AI 튜터 지시사항)
- JSON 문법은 반드시 유효해야 함

#### TocNode 스키마
각 목차 노드는 다음 필드를 가진다:
- `type` (필수): `"chapter"` (장), `"section"` (절), `"subsection"` (항) 중 하나
- `title` (필수): 화면에 표시될 목차 제목 (파일명과 동일하지 않은 자연어 명칭)
- `description` (필수): 해당 섹션 요약 설명 (더미 문구 사용 금지)
- `filename` (leaf 노드 필수): MDX 카드 파일명 (예: `"01-intro.mdx"`). `cards/` 접두어 없이 파일명만 기재. `cards[]`의 값과 정확히 일치해야 함
- `children` (비leaf 노드): 하위 TocNode 배열. `filename`이 없는 chapter/section 노드는 반드시 `children`을 가짐

**규칙**: toc 트리의 모든 leaf 노드(filename 보유) 집합과 `cards[]` 집합이 **완전히 일치**해야 한다. 불일치 시 서비스 등록 오류 발생.

### cards/*.mdx
1파일 = 1카드(페이지). 기본 Markdown 문법 위주 (복잡한 JSX 최소화). 이미지는 `../images/파일명.png` 상대 경로로 참조. 콘텐츠는 TTS로 읽히므로 명확한 설명문으로 작성.

### wiki.md
학습자에게 보이지 않는 AI 튜터 전용 지식 베이스. 용어 사전, 예상 Q&A, 튜터 페르소나 지침 포함.

### images/
`origin/<course-name>/images/`가 있을 때만 생성. 없으면 폴더 및 이미지 참조 생략.

## 엣지 케이스

| 상황 | 처리 방식 |
|------|-----------|
| `converted/<course-name>/` 이미 존재 | 파일 덮어쓰기 (재변환) |
| `origin/<course-name>/images/` 없음 | `images/` 폴더 생략, 카드에 이미지 참조 없도록 작성 |
| ZIP 이미 존재 | 덮어쓰기 |
| toc leaf 노드 집합 ≠ `cards[]` 집합 | ZIP 생성 전 반드시 수정. 불일치 상태로 ZIP을 만들지 않는다. |

## 번들 검증 체크리스트

ZIP 생성 전, 아래 항목을 순서대로 확인한다. 체크에 실패하면 ZIP을 만들지 않고 먼저 수정한다.

> **운영 규칙**: Open Tutor 등록 또는 검증 중 새로운 오류가 발생하면, 원인을 파악한 즉시 아래 체크리스트에 항목을 추가한다. 오류는 반복되어서는 안 된다.

### [C1] filename 형식 — `"cards/"` 접두어 금지
- toc의 모든 `filename` 값: 파일명만 기재 (예: `"01-intro.mdx"`)
- `cards[]`의 모든 항목: 파일명만 기재 (예: `"01-intro.mdx"`)
- **`"cards/01-intro.mdx"` 형식 절대 사용 금지**

### [C2] toc leaf 집합 ↔ cards[] 완전 일치
- toc 트리의 모든 leaf 노드(`filename` 보유) 집합 **==** `cards[]` 집합
- 누락·중복·오타 모두 불일치로 처리됨

### [C3] toc 노드 필수 필드 존재
- 모든 노드: `type`, `title`, `description` 필드 필수
- leaf 노드: `filename` 필드 필수
- 비leaf 노드: `children` 배열 필수 (빈 배열 금지)
- `description`에 더미 문구 사용 금지

### [C4] toc type 값 범위
- 허용 값: `"chapter"`, `"section"`, `"subsection"` 세 가지만

### [C5] 불필요한 계층 중첩 금지
- 단독 카드를 위해 불필요한 하위 계층을 추가하지 않음

### [C6] slug 형식
- 소문자 영문·숫자·하이픈(`-`)만 허용

### [C7] checkpoints.afterCard 존재 확인
- `checkpoints[]`의 모든 `afterCard` 값이 `cards[]`에 존재해야 함

### [C8] 프로토콜 버전 명시
- `package-manifest.json` 에 `"bundler_protocol_version": "1.1.0"` 이 반드시 명시되어 있어야 하며, 필수 필드(`target_age`, `category`)가 정확히 포함되어야 함

### [C9] 동영상 자막 최적화 (해당 시)
- 동영상 카드(`.json`)에 자막(`subtitles`) 기능을 선택적으로 적용할 때, 전체 대사를 다 넣기보다는 **주요 포인트의 자막 또는 안내 메시지**를 포함하여 사용자가 쉽게 탐색할 수 있도록 배려했는지 확인

### [C10] 이미지 리소스 실재 확인
- MDX 카드 내에 `../images/` 또는 `./images/` 경로로 참조된 모든 로컬 이미지 파일이 실제 `images/` 폴더 내에 물리적으로 존재해야 함
- 플레이스홀더 성격으로 마크다운에 로컬 이미지 참조를 추가했다면, 반드시 실물 이미지 파일을 생성하거나 가져와서 폴더에 저장해야 하며 파일이 누락되어 엑박(깨짐 현상)이 발생하는 상태로 배포 금지

### [C11] 학습 카드 마크다운 가이드라인 준수
- 학습 카드 마크다운 작성 시 프리미엄 렌더링 호환을 위해 다음 기준을 완벽하게 충족해야 함:
  - **헤더 레벨 (H1, H2) 적절한 사용**: 챕터/레슨 제목은 최상단에 H1(`#`)으로 1회만 지정하고, 주요 구분 주제는 H2(`##`), 세부 항목은 H3(`###`) 구조로 설정하여 목차와의 시각적 리듬을 살림
  - **테이블 표 (GFM Tables)**: 비교, 특징 대조, 매핑 정보 등 구조화된 데이터 표기 시 파이프 기호(`|`)를 사용한 마크다운 테이블 구조를 필수로 작성함
  - **코드 블록 및 구문 강조 (Code Blocks)**: 소스 코드를 기입할 때는 반드시 코드 블록 기호와 해당 프로그래밍 언어의 식별자(예: `cpp`, `arduino`, `javascript`, `json` 등)를 명시함

### [Z1] ZIP 생성 도구 — Python zipfile 전용
- **PowerShell `Compress-Archive` 사용 금지** — 폴더 구조를 루트로 평탄화(flatten)함

### [Z2] ZIP 내용물 확인
- 포함 필수: `package-manifest.json`, `config.json`, `wiki.md`, `cards/**`, (images가 있는 경우) `images/**`
- 제외 필수: `*.zip` 파일 자신


### [P0] 패키지 — CourseMeta 형식 검증
- `package-manifest.json`의 `courses[]`는 **슬러그 문자열 배열이 아닌 객체 배열**이어야 함
- 각 원소에 `slug`, `title`, `description`, `tags` 4개 필드가 모두 있어야 함
- `tags`는 최소 3개 이상의 문자열 배열이어야 함
- `build_package.py`가 자동 검증하므로, 스크립트 오류 시 매니페스트 확인

### [P1] 패키지 — courses 슬러그 실재 확인 (ZIP 파일 단위)
- `courses[]`에 열거된 모든 슬러그에 대해 `converted/<slug>/<slug>.zip` **파일 자체**가 실제 존재해야 함 (폴더만 있고 ZIP이 없으면 오류)

### [P2] 패키지 — courses 슬러그 중복 금지
- `courses[]` 내에 동일 슬러그가 두 번 이상 등장하면 안 됨

### [P3] 패키지 — thumbnail 파일 존재 확인
- `thumbnail` 필드가 이미지 파일 경로인 경우, `packages/<package-slug>/<thumbnail>` 파일이 실제 존재해야 함
- 아이콘 지정 시 `"icon:{ID}"` 형식 사용 — 파일 존재 확인 불필요

### [P4] 패키지 — 버전 및 변경 로그 형식 검증
- `version`은 Semantic Versioning (`X.Y.Z` 형식) 권장

### [P5] 패키지 — 통합 번들 출력 경로 충돌 확인
- 통합 번들 출력 파일명은 `converted/<package-slug>.zip` (구 `-pkg.zip` 접미사는 폐지됨)
- 동일 경로에 **폴더**가 이미 존재하면 오류

### [P6] 패키지 — thumbnail 파일명 정규화 확인
- `thumbnail`이 이미지 파일인 경우, 원본 파일명과 무관하게 통합 ZIP 내부에는 항상 `thumbnail.png`로 저장됨
- 아이콘 참조(`"icon:*"`)인 경우 이 검사 대상 아님

## 템플릿 파일

`docs/bundling-guide/templates/`에 형식 예시가 있다.
- `docs/bundling-guide/templates/config.json`
- `docs/bundling-guide/templates/card.mdx`
- `docs/bundling-guide/templates/wiki.md`
- `docs/bundling-guide/templates/package-manifest.json`

# GEMINI.md

> Gemini CLI/Agent가 이 저장소에서 작업할 때 참고하는 지침 파일.

## 프로젝트 목적

이 저장소는 **PennyPress(Vivo Academy) 강좌 번들 제작 도구**다. 사용자가 `origin/<course-name>/` 폴더에 책, 강의 자료 등의 원본 리소스를 넣으면, AI Agent가 이를 PennyPress 플랫폼에서 사용 가능한 강좌 번들로 변환하여 `converted/<course-name>/`에 저장하고 ZIP 파일을 생성한다.

PennyPress는 카드(페이지) 단위 콘텐츠를 AI 튜터와 인터랙티브하게 학습하는 SaaS 플랫폼이다. 학습자는 콘텐츠를 보고 들으며, 체크포인트마다 AI와 QnA를 진행한다.

## 폴더 구조

```
PennyPress-Books/
├── origin/
│   └── <course-name>/          ← 사용자가 원본 자료 배치 (PDF, DOCX, 이미지 등)
│       └── images/             ← 강좌에 사용할 이미지 (선택)
│
├── converted/
│   └── <course-name>/          ← Agent가 생성 및 관리
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
└── tools/                      ← preview 생성 등 보조 스크립트
```

## 변환 워크플로우

변환 요청 시 아래 순서를 반드시 따른다:

1. `origin/<course-name>/` 내 파일 목록 확인
2. `docs/bundling-guide/AGENT_INSTRUCTIONS.md` 지침에 따라 기획 (목차, 카드 수, 체크포인트 위치)
3. `converted/<course-name>/` 폴더 생성
4. 파일 순서대로 생성:
   - `wiki.md` — AI 튜터 지식 베이스
   - `cards/*.mdx` — 각 카드 본문 (01-부터 순번)
   - `config.json` — 메타데이터 + 카드 순서 + 체크포인트
     - `toc[]`는 **장(chapter) → 절(section) → 항(subsection)** 계층 트리로 작성한다. 3단계 모두를 반드시 사용할 필요는 없다. 내용 구조에 맞게 필요한 단계만 사용한다.
     - 최하위 노드(실제 카드와 연결되는 노드)에는 반드시 `filename` 필드를 포함한다.
     - 작성 완료 후 반드시 확인: **toc 트리의 모든 `filename` 값이 `cards[]`에 존재하고, `cards[]`의 모든 항목이 toc 트리의 leaf 노드에 존재하는가.**
5. `origin/<course-name>/images/` 존재 시 → `converted/<course-name>/images/`로 복사
6. ZIP 생성 전 **번들 검증 체크리스트** 전체 항목 통과 확인 (아래 섹션 참조)
7. ZIP 생성: `converted/<course-name>/<course-name>.zip`
   - 포함: `config.json`, `wiki.md`, `cards/**`, `images/**`
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

### [Z1] ZIP 생성 도구 — Python zipfile 전용
- **PowerShell `Compress-Archive` 사용 금지** — 폴더 구조를 루트로 평탄화(flatten)함

### [Z2] ZIP 내용물 확인
- 포함 필수: `config.json`, `wiki.md`, `cards/**`, (images가 있는 경우) `images/**`
- 제외 필수: `*.zip` 파일 자신

## 템플릿 파일

`docs/bundling-guide/templates/`에 형식 예시가 있다.
- `docs/bundling-guide/templates/config.json`
- `docs/bundling-guide/templates/card.mdx`
- `docs/bundling-guide/templates/wiki.md`

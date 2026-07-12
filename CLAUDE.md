# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 목적

이 저장소는 **Open Tutorials 강좌 번들 제작 도구**다. 사용자가 `origin/<course-name>/` 폴더에 책, 강의 자료 등의 원본 리소스를 넣으면, AI Agent가 이를 Open Tutorials 플랫폼에서 사용 가능한 강좌 번들로 변환하여 `converted/<course-name>/`에 저장하고 ZIP 파일을 생성한다.

Open Tutorials는 카드(페이지) 단위 콘텐츠를 AI 튜터와 인터랙티브하게 학습하는 SaaS 플랫폼이다. 학습자는 콘텐츠를 보고 들으며, 체크포인트마다 AI와 QnA를 진행한다.

## 폴더 구조

```
OpenTutorials-Bundler/
├── origin/
│   └── <course-name>/          ← 사용자가 원본 자료 배치 (PDF, DOCX, 이미지 등)
│       └── images/             ← 강좌에 사용할 이미지 (선택)
│
├── converted/                  ← 모든 관련 파일들은 converted 폴더 내부에 생성되어야 함
│   ├── <course-name>/          ← 개별 강좌 폴더
│   │   ├── package-manifest.json ← Agent가 신규 생성 (필수, 4대 항목 검증 대상)
│   │   ├── config.json         ← 4대 항목 검증 대상 (ZIP 생성 시 반드시 포함)
│   │   ├── wiki.md             ← 4대 항목 검증 대상 (ZIP 생성 시 반드시 포함)
│   │   ├── cards/              ← 4대 항목 검증 대상 (TOC와 일치해야 함)
│   │   │   ├── 01-intro.mdx
│   │   │   └── ...
│   │   ├── images/             ← origin에서 복사 (있는 경우)
│   │   └── <course-name>.zip   ← 강좌 빌드 스크립트로 생성된 최종 ZIP
│   │
│   └── <package-slug>/         ← 패키지 폴더 (여러 강좌 통합 패키지 구성 시)
│       ├── package-manifest.json ← 패키지 매니페스트 (필수, courses 필드 필수)
│       ├── cover.png           ← 패키지 썸네일 이미지 (선택)
│       └── <package-slug>.zip  ← 빌드된 통합 패키지 ZIP
│
├── docs/
│   ├── bundling-guide/         ← Agent 지침 + 구조 가이드 + 템플릿
│   └── penny-press/            ← PennyPress FE 아키텍처 참고 문서
│
└── tools/                      ← 검증 및 빌드 보조 스크립트
```

> **주의**: `packages/` 폴더는 더 이상 사용하지 않으며, 모든 결과물(매니페스트 및 최종 ZIP)은 `converted/` 폴더 내에 생성해야 합니다.

## 변환 워크플로우

변환 요청 시 아래 순서를 반드시 따른다:

1. `origin/<course-name>/` 내 파일 목록 확인
2. `docs/bundling-guide/AGENT_INSTRUCTIONS.md` 지침에 따라 기획 (목차, 카드 수, 체크포인트 위치)
3. **필수 메타데이터 사용자 인터뷰**: `target_age`, `category`, `license`(제3자 원저작물 각색 여부 포함) 등 원고만으로 명확히 판단하기 어려운 필수/핵심 항목이 있으면 임의로 추정해서 채우지 말고, `protocol/creator-interview-guide.md`의 질문 양식을 참고하여 사용자에게 확인 질문을 한다.
   - 특히 `license`는 기본값(`all-rights-reserved`)으로 넘어가도 되는지, 아니면 CC 계열 라이선스나 `custom`을 원하는지 반드시 확인한다.
   - 원고가 다른 책/영상/이미지/오픈소스 등 제3자 원저작물을 각색·인용한 것이라면, 그 출처와 라이선스 조건을 사용자에게 직접 확인하여 `license_file`(예: `LICENSE.md`)에 고지 내용을 작성한다. **출처나 라이선스 정보를 AI가 임의로 추정해서 채우지 않는다.**
4. `converted/<course-name>/` 폴더 생성
5. 파일 순서대로 생성:
   - `package-manifest.json` — 강좌 및 패키지 메타데이터 (필수, 프로토콜 1.3.1 준수)
   - `wiki.md` — AI 튜터 지식 베이스
   - `cards/*.mdx` — 각 카드 본문 (01-부터 순번)
   - `config.json` — 메타데이터 + 카드 순서 + 체크포인트
     - `toc[]`는 **장(chapter) → 절(section) → 항(subsection)** 계층 트리로 작성한다. 단, 3단계 모두를 반드시 사용할 필요는 없다. 내용 구조에 맞게 필요한 단계만 사용한다 (예: 단독 카드는 chapter→section(leaf) 2단계로도 충분).
     - 최하위 노드(실제 카드와 연결되는 노드)에는 반드시 `filename` 필드를 포함한다.
     - 작성 완료 후 반드시 확인: **toc 트리의 모든 `filename` 값이 `cards[]`에 존재하고, `cards[]`의 모든 항목이 toc 트리의 leaf 노드에 존재하는가.** 불일치 시 Open Tutorials 등록 오류.
6. `origin/<course-name>/images/` 존재 시 → `converted/<course-name>/images/`로 복사
7. ZIP 생성 전 **번들 검증 체크리스트** 전체 항목 통과 확인 (아래 섹션 참조). `bundler_protocol_version`이 현재 프로토콜 버전(`protocol/protocol.md`의 `Version:`)과 정확히 일치하는지, 재생성 시 `version` 필드가 갱신되는지 반드시 확인한다 ([C15] 참조).
8. ZIP 생성: `converted/<course-name>/<course-name>.zip`
   - 포함: `package-manifest.json`, `config.json`, `wiki.md`, `cards/**`, `images/**`, (라이선스 파일이 있는 경우) `LICENSE.md`
   - 제외: `*.zip` (ZIP 파일 자신), `preview.html`
9. (선택) Preview 생성 제안: ZIP 생성 완료 후 사용자에게 제안
   > "preview.html도 함께 만들까요? 브라우저에서 바로 강좌 내용을 확인할 수 있습니다."
   - 승인 시 또는 명시적 요청 시: `python tools/generate_preview.py <course-name>` 실행
   - 출력: `converted/<course-name>/preview.html` (ZIP에 포함하지 않음)
10. 완료 보고 (생성된 카드 수 = toc 수, 체크포인트 위치, ZIP 경로, preview 경로)

### 강좌 빌드 및 ZIP 재생성 (필수 검증 수립 및 보장)

강좌 번들 생성 및 재생성 시에는 **반드시** 빌더 및 자동 검증 스크립트인 `tools/build_course.py`를 사용합니다. 이 스크립트는 번들 파일 생성 시 다음 4가지 핵심 항목을 엄격히 검증하여 하나라도 위반될 경우 최종 ZIP 생성을 중단하고 오류를 출력합니다.

1. **package-manifest.json 존재 여부 및 형식 검증**:
   - `converted/<course-slug>/package-manifest.json` 파일이 물리적으로 존재하는가?
   - 유효한 JSON 형식인가? (파싱 에러 검출)
2. **패키지 메타데이터 필수 필드 검증**:
   - `title`, `slug`, `description`, `author` (nickname 필수), `published`, `version`, `changelog`, `bundler_protocol_version`, `target_age`, `category`, `tags` (최소 3개 이상)가 누락 없이 정확히 기입되어 있는가?
3. **필수 파일 검사 (config.json, wiki.md)**:
   - `config.json` 과 `wiki.md`가 존재하며, 이를 ZIP 압축에 정상적으로 반영하는가? (누락으로 인한 ZIP 누출 원천 차단)
4. **목차(TOC) 및 강의 카드(Cards) 일치성 검사**:
   - `config.json` 내 `cards[]` 배열의 카드명 목록과 `toc` 계층 구조의 leaf 노드 `filename` 목록이 중복·누락 없이 1:1로 완전히 일치하는가?

* **단과 강좌 빌드/재생성**:
  ```bash
  python tools/build_course.py <course-slug>
  ```
* **패키지 하위 강좌 빌드/재생성**:
  ```bash
  python tools/build_course.py <course-slug> --package <package-slug>
  ```

> **버전 업데이트 규칙**: 강좌 번들 파일을 다시 만들 때(재생성 시)는 항상 `package-manifest.json`의 `version`을 업데이트해야 합니다. `tools/build_course.py`는 빌드 시 기존 `package-manifest.json`이 존재할 때 사용자가 명시적으로 지정하지 않은 경우 마지막 패치 버전을 1 올려서 저장하고 ZIP을 빌드합니다 (예: `1.0.0` -> `1.0.1`).
> - 버전을 명시적으로 지정하고 싶을 때: `python tools/build_course.py <course-slug> -v <version>` 또는 `--version-set <version>`
> - 버전을 올리지 않고 그대로 빌드하고 싶을 때: `python tools/build_course.py <course-slug> --no-bump`

> **주의**: PowerShell `Compress-Archive` 나 기타 수동 압축 방식은 **절대 금지**합니다. 번들 파일에 `config.json` 등이 누락되는 현상을 방지하기 위해 항상 `tools/build_course.py` 를 실행하여 4대 필수 검증을 완료하고 보장된 ZIP 번들을 생성하십시오.

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
2. `converted/<package-slug>/package-manifest.json` 작성 (통합 강좌 매니페스트)
   - **필수/권장 필드**: `title`, `slug`, `description`, `thumbnail`, `published`, `sequential_play`, `force_checkpoint`, `courses`, `version`, `changelog`
   - `sequential_play`, `force_checkpoint`: 기본값 `false`. 미션형·고난도 강좌만 `true`로 설정
   - `version`: 권장 포맷 `X.Y.Z` (예: `"1.0.0"`). 생략 시 기본값 `"1.0.0"`으로 자동 폴백
   - `changelog`: 업데이트/수정 사항 요약 텍스트. 줄바꿈 시 `\n` 이스케이프 문자 사용. 생략 시 기본값 `"최초 릴리즈"`로 자동 폴백
   - `courses[]`: **슬러그 문자열 배열이 아닌 CourseMeta 객체 배열**. 각 원소에 `slug`, `title`, `description`, `tags`(3개 이상) 포함
   - `thumbnail` 필드: 이미지 파일명(예: `"cover.png"`) 또는 플랫폼 아이콘 코드(예: `"icon:cpu"`) 지정 가능. 이미지 파일인 경우 빌드 시 ZIP 내부명이 `thumbnail.png`로 정규화됨
   - 아이콘 코드 목록: `docs/bundling-guide/GUIDE_THUMBNAIL_INTEGRATION.md` 참조
   - `license`(선택): 통합 강좌 전체에 적용할 라이선스. 사전 정의 값 또는 `"custom"` 지정 (`custom` 시 `license_file` 필수). 제3자 원저작물을 각색한 부분이 있다면 `license_file`로 출처/이용조건을 고지 (4.1.2절 참조). 하위 개별 강좌가 서로 다른 라이선스를 쓴다면 각 강좌의 `package-manifest.json`에 개별로 지정
   - `bundler_protocol_version`이 현재 프로토콜 버전과 일치하는지 확인 ([C15] 참조)
3. 패키지 검증 체크리스트 [P0]~[P6] 통과 확인
4. `python tools/build_package.py <package-slug>` 실행 (재생성 시 `version` 자동 갱신 여부 확인)
5. 완료 보고: 개별 강좌 ZIP 목록 + `converted/<package-slug>/<package-slug>.zip` 경로 (package-manifest.json + thumbnail.png + courses/<slug>.zip 포함)

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

> **운영 규칙**: Open Tutorials 등록 또는 검증 중 새로운 오류가 발생하면, 원인을 파악한 즉시 아래 체크리스트에 항목을 추가한다. 오류는 반복되어서는 안 된다.

### [C1] filename 형식 — `"cards/"` 접두어 금지
- toc의 모든 `filename` 값: 파일명만 기재 (예: `"01-intro.mdx"`)
- `cards[]`의 모든 항목: 파일명만 기재 (예: `"01-intro.mdx"`)
- **`"cards/01-intro.mdx"` 형식 절대 사용 금지** — 서비스가 두 값을 직접 비교하므로 형식 불일치 시 등록 오류 발생
- *발생 이력: toc filename에 "cards/" 접두어를 붙여 cards[]와 불일치 → 등록 오류*

### [C2] toc leaf 집합 ↔ cards[] 완전 일치
- toc 트리의 모든 leaf 노드(`filename` 보유) 집합 **==** `cards[]` 집합
- 누락·중복·오타 모두 불일치로 처리됨
- *발생 이력: toc에 없는 카드가 cards[]에 존재하거나 반대 경우 → 등록 오류*

### [C3] toc 노드 필수 필드 존재
- 모든 노드: `type`, `title`, `description` 필드 필수
- leaf 노드(하위 children 없음): `filename` 필드 필수
- 비leaf 노드(`filename` 없음): `children` 배열 필수 (빈 배열 금지)
- `description`에 더미 문구(`"설명 없음"`, `"TODO"` 등) 사용 금지

### [C4] toc type 값 범위
- 허용 값: `"chapter"`, `"section"`, `"subsection"` 세 가지만
- 오타나 다른 문자열 사용 금지

### [C5] 불필요한 계층 중첩 금지
- 같은 수준에 카드가 하나뿐인 경우 한 단계로 처리 (예: chapter → section leaf)
- 단독 카드를 위해 section → subsection을 추가하지 않음
- *발생 이력: 강좌 소개 1개 카드를 section 아래 subsection으로 이중 감쌈*

### [C6] slug 형식
- 소문자 영문·숫자·하이픈(`-`)만 허용
- 공백, 대문자, 언더스코어, 특수문자 금지 (예: `"arduino-beginner"` ✓, `"Arduino_Beginner"` ✗)

### [C7] checkpoints.afterCard 존재 확인
- `checkpoints[]`의 모든 `afterCard` 값이 `cards[]`에 존재해야 함

### [C13] target_age / language 형식 검증 (프로토콜 v1.2.1)
- `target_age`: `all`(전연령), `x+`(x세 이상), `min-max`(연령대 범위) 형식만 허용. 자유 문자열(`"전연령"`, `"10대 이상"` 등) 사용 금지
- `language`(선택): `"ko"` 또는 `"en"`만 허용, 생략 시 기본값 `"ko"`
- *발생 이력: protocol v1.2.0에서 target_age가 자유 문자열에서 규격화된 형식으로 변경됨*

### [C14] license / license_file 검증 (프로토콜 v1.3.0)
- `license`(선택): 사전 정의 값(`CC-BY-4.0`, `CC-BY-SA-4.0`, `CC-BY-NC-4.0`, `CC-BY-NC-SA-4.0`, `CC-BY-ND-4.0`, `CC-BY-NC-ND-4.0`, `CC0-1.0`, `all-rights-reserved`) 또는 `"custom"`만 허용. 생략 시 기본값 `"all-rights-reserved"`
- `license`가 `"custom"`인 경우 `license_file`(라이선스 전문 파일명, 예: `"LICENSE.md"`) 필드가 **필수**이며, 해당 파일이 `converted/<course-name>/`에 실제로 존재하고 ZIP 루트에 포함되어야 함
- `license`가 `"custom"`이 아니어도, 강좌가 제3자 원저작물(책·영상·이미지·오픈소스 등)을 각색·인용한 경우에는 `license_file`을 선택적으로 첨부하여 출처·라이선스·각색 범위·주의사항을 고지할 수 있음 (프로토콜 v1.3.1, `protocol/protocol.md` 4.1.2절 참조). Open Tutorials 앱이 이 내용을 학습자에게 노출하므로, 원저작물을 각색한 강좌는 되도록 첨부를 권장
- 상세 라이선스 설명은 `protocol/protocol.md` 4.1.1절, 제3자 리소스 고지는 4.1.2절 참조

### [C15] 프로토콜 버전 / 강좌 버전 확인 (필수 체크사항)
- 강좌 번들을 새로 만들거나 재생성할 때는 항상 `package-manifest.json`의 `bundler_protocol_version`이 `protocol/protocol.md` 상단의 현재 `Version:` 값과 정확히 일치하는지 확인한다 (불일치 시 `build_course.py`/`build_package.py`가 빌드를 중단함)
- 콘텐츠·메타데이터에 변경이 있는 재생성(예: 라이선스 변경, 카드 수정)에서는 `version` 필드가 갱신되었는지 확인한다. `tools/build_course.py`/`tools/build_package.py`는 기본적으로 패치 버전을 자동 +1 하므로(`-v`로 명시 지정, `--no-bump`로 유지 가능), 버전이 그대로 남아있지 않은지 빌드 로그로 재확인한다
- 이 확인 없이 임의로 수동 편집한 ZIP을 배포하지 않는다

### [Z1] ZIP 생성 도구 — Python zipfile 전용
- **PowerShell `Compress-Archive` 사용 금지** — `cards/` 등 하위 폴더 구조를 루트로 평탄화(flatten)함
- 반드시 Python `zipfile` 모듈로 폴더 구조를 유지하며 생성
- *발생 이력: Compress-Archive 사용 시 cards/*.mdx가 ZIP 루트에 직접 배치됨*

### [Z2] ZIP 내용물 확인 (사후 검증 추가)
- 포함 필수: `package-manifest.json`, `config.json`, `wiki.md`, `cards/**`, (images가 있는 경우) `images/**`
- 제외 필수: `*.zip` 파일 자신
- **사후 검증**: 빌드 후 생성된 ZIP 파일을 프로그래밍 방식으로 열어 루트에 `package-manifest.json`, `config.json`, `wiki.md`가 유실 없이 실재하는지 확인하며, `cards/` 및 `images/` 폴더 외의 비정상 경로 파일이 없는지 검사한다. (`tools/build_course.py`가 자동 검증)

### [P0] 패키지 — CourseMeta 형식 검증
- `package-manifest.json`의 `courses[]`는 **슬러그 문자열 배열이 아닌 객체 배열**이어야 함
- 각 원소에 `slug`, `title`, `description`, `tags` 4개 필드가 모두 있어야 함
- `tags`는 최소 3개 이상의 문자열 배열이어야 함
- `courses[]`가 빈 배열이거나 필드 자체가 없으면 안 됨
- `build_package.py`가 자동 검증하므로, 스크립트 오류 시 매니페스트 확인

### [P1] 패키지 — courses 슬러그 실재 확인 (ZIP 파일 단위)
- `package-manifest.json`의 `courses[]`에 열거된 모든 슬러그에 대해 `converted/<slug>/<slug>.zip` **파일 자체**가 실제 존재해야 함 (폴더만 있고 ZIP이 없으면 오류)
- `build_package.py`가 자동 검증하므로, 스크립트 오류 시 해당 강좌의 개별 ZIP 생성(6단계) 완료 여부 확인
- *발생 이력: converted/<slug>/ 폴더는 있으나 개별 강좌 ZIP을 생성하지 않아 통합 번들 빌드 실패*

### [P2] 패키지 — courses 슬러그 중복 금지
- `courses[]` 내에 동일 슬러그가 두 번 이상 등장하면 안 됨

### [P3] 패키지 — thumbnail 파일 존재 확인
- `thumbnail` 필드가 이미지 파일 경로인 경우, `converted/<package-slug>/<thumbnail>` 파일이 실제 존재해야 함
- 플랫폼 사전 정의 아이콘 지정 시 `"icon:{ID}"` 형식 사용 (예: `"icon:cpu"`) — 파일 존재 확인 불필요
- 썸네일 없이 배포하려면 `thumbnail` 필드 자체를 생략 (기본값: `icon:book`)

### [P4] 패키지 — 버전 및 변경 로그 형식 검증
- `version`은 Semantic Versioning (`X.Y.Z` 형식, 예: `"1.1.0"`) 권장
- `changelog` 줄바꿈 시 JSON 표준에 부합하게 `\n` 이스케이프 형태로 기록

### [P5] 패키지 — 통합 번들 출력 경로 충돌 확인
- 통합 번들 출력 파일명은 `converted/<package-slug>/<package-slug>.zip` (구 -pkg.zip 및 converted/ 하위 루트 출력 방식 폐지)
- 동일 경로에 **폴더**가 이미 존재하면 오류 (파일로 이미 존재하는 경우는 덮어씀)
- `build_package.py`가 자동 검증하므로, 스크립트 오류 시 `converted/<package-slug>/<package-slug>.zip` 경로 상태 확인

### [P6] 패키지 — thumbnail 파일명 정규화 확인
- `thumbnail`이 이미지 파일인 경우, 원본 파일명과 무관하게 통합 ZIP 내부에는 항상 `thumbnail.png`로 저장됨
- 원본 확장자가 `.png`가 아니면 `build_package.py`가 경고를 출력함 (파일명만 고정될 뿐 이미지 형식 변환은 하지 않음)
- 아이콘 참조(`"icon:*"`)인 경우 이 검사 대상 아님 (파일 자체가 포함되지 않음)

### [P7] 패키지 — 통합 번들 사후 검증
- 통합 ZIP 파일 생성 후, 루트에 `package-manifest.json`이 실재하는지 검사한다.
- 통합 ZIP 내부의 `courses/<slug>.zip` 파일들이 정상적으로 포함되었는지 확인하고, 각각의 하위 강좌 ZIP 파일을 가상으로 열어 그 내부에 `config.json`, `wiki.md`, `package-manifest.json`이 누락 없이 존재하는지 재검증한다. (`tools/build_package.py`가 자동 검증)

---

## 템플릿 파일

`docs/bundling-guide/templates/`에 형식 예시가 있다.
- `docs/bundling-guide/templates/config.json`
- `docs/bundling-guide/templates/card.mdx`
- `docs/bundling-guide/templates/wiki.md`
- `docs/bundling-guide/templates/package-manifest.json`

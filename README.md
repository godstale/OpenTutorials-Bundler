# Open Tutorials Bundler

> **Course Bundler Protocol Version**: `v1.3.1`


AI Agent(Claude Code, GitHub Copilot, Gemini CLI 등)를 활용하여 PDF, DOCX 등 원본 자료를 **Open Tutorials** 플랫폼에 등록 가능한 강좌 번들(ZIP)로 자동 변환하는 워크스페이스입니다.

사용자는 `origin/<course-name>/` 폴더에 책, 강의 자료 등 원본 리소스만 넣으면 됩니다. AI Agent가 자료를 분석해 카드(페이지 단위 MDX), 목차(config.json), AI 튜터 지식 베이스(wiki.md)를 생성하고, 검증을 거쳐 업로드용 ZIP까지 만들어 줍니다.

---

## 목차

- [프로젝트 목적](#프로젝트-목적)
- [주요 기능](#주요-기능)
- [폴더 구조](#폴더-구조)
- [빠른 시작](#빠른-시작)
- [강좌 번들 파일 구조](#강좌-번들-파일-구조)
- [여러 강좌를 묶는 패키지 워크플로우](#여러-강좌를-묶는-패키지-워크플로우)
- [보조 도구](#보조-도구)
- [지원하는 AI Agent](#지원하는-ai-agent)
- [문서](#문서)
- [엣지 케이스 및 검증](#엣지-케이스-및-검증)
- [라이선스](#라이선스)

---

## 프로젝트 목적

Open Tutorials는 카드(페이지) 단위 콘텐츠를 AI 튜터와 인터랙티브하게 학습하는 플랫폼입니다. 학습자는 콘텐츠를 보고 들으며(TTS), AI 에게 물어보기도 하며 체크포인트마다 AI와 QnA를 진행합니다.

이 저장소는 그 플랫폼에 올릴 **강좌 번들을 손으로 일일이 만들지 않고, AI Agent에게 원본 자료만 던져주면 규격에 맞는 산출물이 나오도록** 만든 "번들링 도구 + Agent 지침" 세트입니다. 즉, 콘텐츠 자체를 만드는 서비스가 아니라 **원본 자료 → Open Tutorials 규격 산출물** 변환 파이프라인을 관리하는 워크스페이스입니다.

핵심 아이디어:
1. 사람은 원본 자료를 `origin/`에 두고 "변환해줘"라고 요청만 한다.
2. AI Agent는 `CLAUDE.md` / `AGENTS.md` / `GEMINI.md`에 정의된 워크플로우와 `docs/bundling-guide/`의 상세 규격을 그대로 따른다.
3. 산출물은 `converted/`에 파일 단위로 쌓이고, 최종적으로 Open Tutorials Admin에 업로드 가능한 ZIP으로 패키징된다.

---

## 주요 기능

- **원본 자료 → 강좌 번들 자동 변환**: PDF/DOCX 등 원본에서 목차 설계, 카드(MDX) 작성, AI 튜터 지식 베이스(wiki.md) 생성까지 AI Agent가 수행합니다.
- **장 → 절 → 항 계층 목차(TOC) 자동 설계**: 콘텐츠 분량에 맞춰 트리 깊이를 유연하게 조정합니다(단독 카드는 2단계, 그룹이 있으면 3단계).
- **체크포인트 자동 배치**: 카드 사이사이에 AI 튜터가 학습자와 QnA를 진행할 지점(`checkpoints[]`)과 프롬프트를 함께 설계합니다.
- **번들 검증 체크리스트 내장**: ZIP을 만들기 전에 `CLAUDE.md`의 [C1]~[C7], [C13], [C14], [Z1]~[Z2] 체크리스트를 통과했는지 확인해, Open Tutorials 등록 오류를 사전에 차단합니다.
- **빌드 스크립트의 4대 필수 검증**: `tools/build_course.py`가 매 빌드마다 (1) `package-manifest.json` 존재·형식, (2) 필수 메타데이터 필드(`bundler_protocol_version` 포함), (3) `config.json`/`wiki.md` 존재, (4) TOC leaf와 `cards[]` 일치 여부를 검증하고, 하나라도 실패하면 ZIP 생성을 중단합니다.
- **강좌 버전 자동 관리**: 재빌드 시 `package-manifest.json`의 `version`을 자동으로 패치 버전 +1 하며(`-v`/`--version-set`으로 명시 지정, `--no-bump`로 유지 가능), 사용한 `bundler_protocol_version`도 함께 기록되어 플랫폼이 재생 호환성을 판단할 수 있습니다.
- **폴더 구조를 보존하는 ZIP 생성**: PowerShell `Compress-Archive`가 하위 폴더를 평탄화하는 문제를 피하기 위해 Python `zipfile` 기반(`tools/build_course.py`, `tools/build_package.py`)으로 생성합니다.
- **여러 강좌를 묶는 패키지(통합 번들) 지원**: 원본 하나를 여러 챕터 강좌로 나눠 만들었을 때, `package-manifest.json` + 개별 강좌 ZIP들을 하나의 통합 ZIP으로 묶어 배포할 수 있습니다(`tools/build_package.py`). 패키지 전용 검증 체크리스트([P0]~[P7])도 자동 실행됩니다.
- **썸네일/플랫폼 아이콘 지정**: 강좌·패키지에 이미지 썸네일 또는 플랫폼 사전 정의 아이콘(`icon:cpu` 등)을 지정할 수 있습니다(`docs/bundling-guide/GUIDE_THUMBNAIL_INTEGRATION.md` 참조).
- **버전 및 변경 이력(Changelog) 관리**: 매니페스트에 `version`, `changelog` 필드를 넣어 학습자에게 업데이트 이력을 보여줄 수 있습니다.
- **브라우저 미리보기 생성**: ZIP 업로드 전에 `tools/generate_preview.py`로 강좌를 브라우저에서 바로 확인할 수 있는 `preview.html`을 생성합니다.
- **여러 AI Agent 동시 지원**: Claude Code(`CLAUDE.md`), GitHub Copilot / OpenAI Codex(`AGENTS.md`), Gemini CLI(`GEMINI.md`) 중 어떤 Agent를 쓰든 동일한 워크플로우와 규격을 따릅니다.

---

## 폴더 구조

```
OpenTutorials-Bundler/
├── origin/
│   └── <course-name>/          ← 사용자가 원본 자료 배치 (PDF, DOCX, 이미지 등)
│       └── images/             ← 강좌에 사용할 이미지 (선택)
│
├── converted/                  ← 모든 산출물(매니페스트·ZIP 포함)이 이 폴더 안에 생성됨
│   ├── <course-name>/          ← 개별 강좌 폴더
│   │   ├── package-manifest.json ← 강좌 메타데이터 (필수, bundler_protocol_version 포함)
│   │   ├── config.json         ← 목차(toc) + 카드 순서 + 체크포인트
│   │   ├── wiki.md             ← AI 튜터 전용 지식 베이스 (학습자 비공개)
│   │   ├── cards/
│   │   │   ├── 01-intro.mdx
│   │   │   └── ...
│   │   ├── images/             ← origin에서 복사 (있는 경우)
│   │   ├── <course-name>.zip   ← tools/build_course.py로 생성 (Open Tutorials 업로드용)
│   │   └── preview.html        ← (선택) 브라우저 미리보기, ZIP에는 미포함
│   │
│   └── <package-slug>/         ← 여러 강좌를 묶는 패키지 폴더 (선택)
│       ├── package-manifest.json ← 패키지 매니페스트 (필수, courses[] 필수)
│       ├── cover.png            ← 패키지 썸네일 (선택)
│       └── <package-slug>.zip   ← tools/build_package.py로 생성한 통합 번들
│
├── docs/
│   ├── bundling-guide/         ← Agent 지침 + 강좌 구조 규격 + 템플릿
│   │   ├── AGENT_INSTRUCTIONS.md
│   │   ├── COURSE_STRUCTURE_GUIDE.md
│   │   ├── GUIDE_THUMBNAIL_INTEGRATION.md
│   │   └── templates/
│   └── penny-press/            ← Open Tutorials FE 아키텍처 참고 문서
│
├── tools/                      ← 강좌/패키지 빌드 및 검증, 미리보기 생성 스크립트
│   ├── build_course.py         ← 개별 강좌 빌드 + 4대 필수 검증 (버전 자동 관리 포함)
│   ├── build_package.py        ← 패키지 통합 번들 빌드 + [P0]~[P7] 검증
│   └── generate_preview.py
│
├── CLAUDE.md / AGENTS.md / GEMINI.md   ← AI Agent별 워크플로우 지침 (내용 동일)
└── README.md
```

> **주의**: `packages/` 폴더는 더 이상 사용하지 않습니다. 모든 결과물(매니페스트 및 최종 ZIP)은 `converted/` 폴더 내에 생성됩니다.

---

## 빠른 시작

### 1. 저장소 클론

```bash
git clone https://github.com/godstale/OpenTutorials-Bundler.git
cd OpenTutorials-Bundler
```

### 2. 원본 자료 배치

`origin/<강좌명>/` 폴더를 만들고 원본 파일(PDF, DOCX 등)을 넣습니다. 강좌에 이미지가 필요하면 `images/` 하위 폴더에 넣습니다(없으면 생략 가능).

```
origin/
└── my-course/
    ├── textbook.pdf
    └── images/          ← 강좌에 사용할 이미지 (선택)
        └── diagram.png
```

### 3. AI Agent에게 변환 요청

Claude Code 사용 예:
```
origin/my-course 폴더의 자료를 강좌 번들로 변환해줘
```

GitHub Copilot, Gemini CLI 등 다른 AI Agent도 각각 `AGENTS.md`, `GEMINI.md` 지침을 읽고 동일하게 동작합니다.

Agent는 다음 순서로 작업합니다:
1. `origin/<course-name>/` 파일 목록 확인
2. `docs/bundling-guide/AGENT_INSTRUCTIONS.md`에 따라 목차/카드 수/체크포인트 위치 기획
3. `package-manifest.json` → `wiki.md` → `cards/*.mdx` → `config.json` 순서로 생성
4. `origin/<course-name>/images/`가 있으면 `converted/<course-name>/images/`로 복사
5. 번들 검증 체크리스트 통과 확인 후 `python tools/build_course.py <course-name>`으로 ZIP 생성 (4대 필수 검증 자동 실행)
6. (선택) `preview.html` 생성 제안

### 4. 결과 확인

```
converted/
└── my-course/
    ├── package-manifest.json  ← 강좌 메타데이터 (version, bundler_protocol_version 등)
    ├── config.json            ← 목차(트리 구조) + 카드 순서 + 체크포인트
    ├── wiki.md                ← AI 튜터 지식 베이스
    ├── cards/
    │   ├── 01-intro.mdx
    │   └── ...
    └── my-course.zip          ← Open Tutorials 업로드용 번들
```

생성된 ZIP 파일을 Open Tutorials Admin에서 업로드하면 강좌가 등록됩니다.

### 5. (선택) 브라우저에서 미리 확인

```bash
python tools/generate_preview.py my-course
```

`converted/my-course/preview.html`이 생성되며, 브라우저로 열면 사이드바 목차 + 카드 콘텐츠를 실제 서비스와 유사한 레이아웃으로 미리 볼 수 있습니다. `preview.html`은 ZIP에는 포함되지 않습니다.

### 6. ZIP만 다시 만들고 싶을 때

파일 내용은 그대로 두고 ZIP만 재생성하려면 다음과 같이 실행합니다.

```bash
python tools/build_course.py my-course
```

- 4대 필수 검증(package-manifest.json 존재/형식, 필수 메타데이터 필드, config.json·wiki.md 존재, TOC-cards 일치)을 통과해야 ZIP이 생성됩니다.
- 기존 `package-manifest.json`이 있으면 `version`의 마지막 패치 번호를 자동으로 +1 하여 재빌드합니다(예: `1.0.0` → `1.0.1`). 버전을 직접 지정하려면 `-v <version>` 또는 `--version-set <version>`, 버전을 올리지 않으려면 `--no-bump` 옵션을 사용합니다.
- 내부적으로 Python `zipfile` 모듈로 `cards/`, `images/` 등 폴더 구조를 보존하며 생성합니다. 하위 폴더를 평탄화하는 PowerShell `Compress-Archive`는 **사용하지 않습니다**.

---

## 강좌 번들 파일 구조

### package-manifest.json

강좌 메타데이터를 담는 필수 파일입니다. **프로토콜 버전(`bundler_protocol_version`)과 강좌 버전(`version`)을 함께 기록**해, 플랫폼이 번들을 재생할 때 호환성을 판단할 수 있도록 합니다.

```json
{
  "title": "강좌 제목",
  "slug": "my-course",
  "description": "강좌 소개",
  "author": { "nickname": "작가 닉네임" },
  "published": true,
  "version": "1.0.0",
  "changelog": "최초 릴리즈",
  "bundler_protocol_version": "1.3.1",
  "target_age": "all",
  "category": "Programming",
  "language": "ko",
  "tags": ["태그1", "태그2", "태그3"],
  "license": "CC-BY-4.0"
}
```

- `bundler_protocol_version` (필수): 이 번들이 준수하는 프로토콜 버전. 현재 `"1.3.1"` 고정이며, `tools/build_course.py`가 값이 다르거나 누락되면 빌드를 중단합니다.
- `version` (필수): 강좌 자체의 버전(Semantic Versioning 권장). 재빌드 시 기본적으로 패치 버전이 자동 증가합니다.
- `target_age` (필수, v1.2.1): `all`(전연령) / `x+`(x세 이상) / `min-max`(연령대 범위) 형식만 허용합니다. `"전연령"` 같은 자유 문자열은 금지됩니다.
- `language` (선택, v1.2.1): `"ko"` 또는 `"en"`만 허용, 생략 시 기본값 `"ko"`.
- `license` (선택, v1.3.0): 강좌 콘텐츠의 라이선스. `CC-BY-4.0` 등 CC 계열 값, `all-rights-reserved`(기본값), 또는 직접 작성한 라이선스를 쓸 경우 `custom`(+ `license_file`로 ZIP에 포함할 라이선스 전문 파일명 지정) 중 하나를 선택합니다. 전체 목록은 [`protocol/protocol.md`](protocol/protocol.md) 4.1.1절 참조.
- `author.nickname` (필수): 작가 닉네임.

### config.json

강좌 메타데이터와 **장(chapter) → 절(section) → 항(subsection)** 계층 목차(`toc`)를 정의합니다. 콘텐츠 구조에 맞는 단계만 사용하면 되며(단독 카드는 2단계로 충분), 3단계를 모두 쓸 필요는 없습니다.

```json
{
  "slug": "my-course",
  "title": "강좌 제목",
  "cards": ["01-intro.mdx", "02-main.mdx"],
  "toc": [
    {
      "type": "chapter",
      "title": "제1장. 시작하기",
      "description": "강좌 소개와 핵심 개념을 다룹니다.",
      "children": [
        {
          "type": "section",
          "title": "강좌 소개",
          "description": "강좌 목표와 전체 구성을 소개합니다.",
          "filename": "01-intro.mdx"
        }
      ]
    }
  ],
  "checkpoints": [
    {
      "afterCard": "02-main.mdx",
      "prompt": "핵심 개념을 자신의 언어로 설명해보세요."
    }
  ]
}
```

- `toc[]` (필수): TocNode 트리. 각 노드는 `type`(`chapter`/`section`/`subsection`), `title`, `description` 필수. leaf 노드는 `filename` 필수, 비-leaf 노드는 `children` 필수.
- `cards[]` (필수): 학습 표시 순서대로 나열한 MDX 파일명 배열. `cards/` 접두어 없이 파일명만 기재합니다(서비스가 `cards/` 폴더를 자동 참조).
- `checkpoints[]` (선택): `afterCard`(파일명만) + `prompt`(AI 튜터에게 줄 QnA 지시).

> **필수 검증**: toc 트리의 모든 leaf `filename` 집합과 `cards[]` 집합은 정확히 일치해야 합니다. 하나라도 다르면 Open Tutorials 등록 오류가 발생합니다.

### cards/*.mdx

1파일 = 1카드(페이지). 복잡한 JSX보다는 기본 Markdown 문법 위주로 작성합니다. 이미지는 `../images/파일명.png` 상대 경로로 참조합니다. 콘텐츠는 TTS로 읽히므로 명확한 설명문 형태로 작성해야 합니다.

### wiki.md

학습자에게는 보이지 않는 AI 튜터 전용 지식 베이스입니다. 용어 사전, 예상 Q&A, 튜터 페르소나 지침 등을 담습니다.

### images/

`origin/<course-name>/images/`가 있을 때만 생성됩니다. 없으면 `images/` 폴더 및 카드 내 이미지 참조를 생략합니다.

---

## 여러 강좌를 묶는 패키지 워크플로우

원본 자료가 커서 여러 강좌(챕터)로 나눠 만든 경우, 개별 강좌 번들 외에 **패키지 매니페스트**와 **통합 번들 ZIP**을 추가로 만들 수 있습니다.

### 명명 규칙

- 강좌 slug: `<course-name>-ch01`, `<course-name>-ch02`, ... 형식
- 강좌 `config.json`의 `title`: `"Part 1: <강좌 제목>"` 형식 권장

### 통합 번들 ZIP 구조

```
<package-slug>.zip
├── package-manifest.json     ← 패키지 매니페스트 (필수)
├── thumbnail.png              ← 썸네일 이미지 (선택, 항상 이 이름으로 정규화됨)
└── courses/
    ├── <slug1>.zip             ← 개별 강좌 번들 ZIP
    └── <slug2>.zip
```

### package-manifest.json 예시

```json
{
  "title": "패키지 제목 (예: 아두이노 IoT 마스터 클래스)",
  "slug": "package-slug",
  "description": "패키지 로드맵 요약",
  "author": { "nickname": "작가 닉네임" },
  "thumbnail": "icon:book",
  "published": true,
  "sequential_play": false,
  "force_checkpoint": false,
  "version": "1.0.0",
  "changelog": "최초 릴리즈",
  "bundler_protocol_version": "1.3.1",
  "target_age": "all",
  "category": "Programming",
  "language": "ko",
  "tags": ["IoT", "Arduino", "Embedded"],
  "license": "all-rights-reserved",
  "courses": [
    {
      "slug": "course-slug-ch01",
      "title": "Part 1: 강좌 제목",
      "description": "이 파트에서 다루는 핵심 내용 요약.",
      "tags": ["태그1", "태그2", "태그3"]
    }
  ]
}
```

- `bundler_protocol_version`(필수)·`target_age`(필수, `all`/`x+`/`min-max` 형식)·`language`(선택, `ko`/`en`)·`license`(선택, CC 계열/`all-rights-reserved`/`custom`)는 개별 강좌 `package-manifest.json`과 동일한 규칙을 따릅니다.
- `courses[]`는 슬러그 문자열이 아닌 **CourseMeta 객체 배열**입니다(`slug`, `title`, `description`, `tags` 3개 이상 필수).
- `thumbnail`은 이미지 파일명(`cover.png`) 또는 플랫폼 아이콘 코드(`icon:cpu` 등) 중 하나를 지정합니다. 아이콘 목록은 [`docs/bundling-guide/GUIDE_THUMBNAIL_INTEGRATION.md`](docs/bundling-guide/GUIDE_THUMBNAIL_INTEGRATION.md) 참조.
- `sequential_play`, `force_checkpoint`: 기본값 `false`. 순서대로만 학습해야 하는 미션형 강좌만 `true`로 설정합니다.

### 빌드

```bash
python tools/build_package.py <package-slug>
```

`converted/<package-slug>/package-manifest.json`을 읽어 다음을 자동 검증한 뒤 `converted/<package-slug>/<package-slug>.zip`을 생성합니다:

- `courses[]`가 CourseMeta 형식인지, 각 슬러그의 개별 강좌 ZIP(`converted/<slug>/<slug>.zip`)이 실제 존재하는지
- 슬러그 중복 여부
- thumbnail 이미지 파일 존재 여부(아이콘 참조는 검사 제외)
- 출력 경로(`converted/<package-slug>/<package-slug>.zip`)에 동일 이름의 **폴더**가 이미 있는지(파일로 존재하는 경우는 덮어씀)
- 통합 ZIP 생성 후 내부 `courses/<slug>.zip` 각각을 열어 `config.json`/`wiki.md`/`package-manifest.json` 누락 여부까지 재검증

---

## 보조 도구

| 스크립트 | 설명 | 요구사항 |
|---------|------|---------|
| `tools/build_course.py <course-slug> [--package <package-slug>] [-v <version>\|--version-set <version>\|--no-bump]` | 개별 강좌 4대 필수 검증 + ZIP 빌드, 버전 자동 관리(패치 +1) | Python 3.8+ (표준 라이브러리만 사용) |
| `tools/build_package.py <package-slug>` | 여러 강좌 ZIP + 매니페스트를 하나의 통합 번들 ZIP으로 패키징 | Python 3.8+ (표준 라이브러리만 사용) |
| `tools/generate_preview.py <course-name>` | 강좌를 브라우저에서 바로 확인할 수 있는 `preview.html` 생성 | Python 3.8+, `markdown` 패키지 (`pip install markdown`) |

---

## 지원하는 AI Agent

| Agent | 지침 파일 |
|-------|----------|
| Claude Code | `CLAUDE.md` |
| GitHub Copilot / OpenAI Codex | `AGENTS.md` |
| Gemini CLI | `GEMINI.md` |

세 파일은 대상 Agent만 다를 뿐 워크플로우와 규격 내용은 동일하게 유지됩니다.

---

## 문서

| 문서 | 설명 |
|------|------|
| [번들 구조 가이드](docs/bundling-guide/COURSE_STRUCTURE_GUIDE.md) | config.json 스키마, 파일 규격 상세 |
| [Agent 지침](docs/bundling-guide/AGENT_INSTRUCTIONS.md) | AI Agent를 위한 카드 작성 품질 기준 |
| [썸네일/아이콘 연동 가이드](docs/bundling-guide/GUIDE_THUMBNAIL_INTEGRATION.md) | 강좌·패키지 썸네일 및 플랫폼 아이콘 지정 방법 |
| [템플릿](docs/bundling-guide/templates/) | config.json, card.mdx, wiki.md, package-manifest.json 예시 |
| [PennyPress FE 참고](docs/penny-press/README.md) | Open Tutorials 플랫폼 아키텍처 |

---

## 엣지 케이스 및 검증

| 상황 | 처리 방식 |
|------|-----------|
| `converted/<course-name>/` 이미 존재 | 파일 덮어쓰기(재변환) |
| `origin/<course-name>/images/` 없음 | `images/` 폴더 생략, 카드에 이미지 참조 없도록 작성 |
| ZIP 이미 존재 | 덮어쓰기 |
| toc leaf 노드 집합 ≠ `cards[]` 집합 | ZIP 생성 전 반드시 수정 (불일치 상태로 ZIP 생성 금지) |

ZIP 생성 전에는 항상 `CLAUDE.md`의 번들 검증 체크리스트([C1]~[C7], [C13], [C14], [Z1]~[Z2], 패키지는 [P0]~[P7])를 통과해야 합니다. 체크리스트는 실제 Open Tutorials 등록 오류 이력을 바탕으로 계속 추가되므로, 새로운 등록 오류가 발견되면 해당 문서에 항목을 추가합니다. `tools/build_course.py`/`tools/build_package.py`가 핵심 항목을 자동 검증하므로, 재빌드 시에는 항상 이 스크립트를 통해 ZIP을 생성해야 합니다.

---

## 라이선스

[MIT](LICENSE)

# Open Tutor 강좌 번들 구조 가이드

강좌 패키지는 폴더를 구성한 뒤 ZIP 형태로 압축하여 업로드해야 합니다.
Open Tutor 플랫폼은 **장(Chapter) - 절(Section) - 항(Subsection)** 계층 구조를 지원합니다.

---

## 1. 디렉토리 구조

```
<course-name>.zip
├── config.json        ← 강좌 메타데이터 및 장-절-항 트리 목차
├── wiki.md            ← AI 튜터 전용 지식 베이스
└── cards/
    ├── 01-intro.mdx
    ├── 02-main-topic.mdx
    └── 03-summary.mdx
```

이미지가 있는 경우:
```
<course-name>.zip
├── config.json
├── wiki.md
├── cards/
│   └── *.mdx
└── images/
    ├── diagram.png
    └── ...
```

---

## 2. config.json 명세

### 최상위 필드
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `slug` | string | 권장 | URL에 사용되는 영문 식별자. 소문자·숫자·하이픈만 허용 (예: `"arduino-beginner"`) |
| `title` | string | 필수 | 강좌 제목 |
| `description` | string | 선택 | 강좌 요약 설명 |
| `author` | string | 선택 | 작가 이름 |
| `cards` | array | 필수 | MDX 파일명 배열 (학습 순서). 파일명만 기재, `cards/` 접두어 없음 |
| `toc` | array | 필수 | 장-절-항 계층 트리 목차 |
| `checkpoints` | array | 선택 | AI QnA 체크포인트 목록 |

### TocNode 스키마
각 목차 노드는 다음 필드를 가진다:

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `type` | string | 필수 | `"chapter"`, `"section"`, `"subsection"` 중 하나 |
| `title` | string | 필수 | 화면에 표시될 목차 제목 (자연어 명칭) |
| `description` | string | 필수 | 해당 섹션 요약 설명 (더미 문구 사용 금지) |
| `filename` | string | leaf 노드 필수 | MDX 파일명. `cards/` 접두어 없이 파일명만 (예: `"01-intro.mdx"`) |
| `children` | array | 비leaf 노드 필수 | 하위 TocNode 배열 |

**핵심 규칙**: toc 트리의 모든 leaf 노드(`filename` 보유) 집합 == `cards[]` 집합이어야 한다. 불일치 시 서비스 등록 오류.

### checkpoints 스키마
| 필드 | 타입 | 설명 |
|------|------|------|
| `afterCard` | string | 기준이 되는 카드 파일명 (`cards[]`에 존재해야 함) |
| `prompt` | string | AI 튜터가 학습자에게 던질 질문 또는 지시사항 |

---

## 3. config.json 작성 예시

```json
{
  "slug": "arduino-beginner",
  "title": "아두이노 임베디드 기초 강좌",
  "description": "아두이노 하드웨어 개요부터 기초적인 C언어 제어까지 학습합니다.",
  "author": "홍길동",
  "cards": [
    "01-intro.mdx",
    "02-what-is-arduino.mdx",
    "03-history.mdx",
    "04-setup-ide.mdx",
    "05-hello-world.mdx"
  ],
  "toc": [
    {
      "type": "chapter",
      "title": "제1장. 아두이노 시작하기",
      "description": "아두이노 임베디드 생태계와 개발 환경 설정을 배웁니다.",
      "children": [
        {
          "type": "section",
          "title": "1.1 아두이노 개요",
          "description": "아두이노가 무엇이며 왜 널리 쓰이는지 알아봅니다.",
          "children": [
            {
              "type": "subsection",
              "title": "1.1.1 강좌 소개",
              "description": "강좌의 대상 독자와 앞으로 배울 내용의 요약입니다.",
              "filename": "01-intro.mdx"
            },
            {
              "type": "subsection",
              "title": "1.1.2 아두이노란 무엇인가?",
              "description": "아두이노 보드와 하드웨어의 기본 구성을 설명합니다.",
              "filename": "02-what-is-arduino.mdx"
            },
            {
              "type": "subsection",
              "title": "1.1.3 오픈소스 하드웨어의 역사",
              "description": "아두이노 프로젝트의 역사적 배경을 다룹니다.",
              "filename": "03-history.mdx"
            }
          ]
        },
        {
          "type": "section",
          "title": "1.2 아두이노 개발 환경 구성",
          "description": "PC에 아두이노 IDE를 설치하고 연결을 테스트합니다.",
          "children": [
            {
              "type": "subsection",
              "title": "1.2.1 아두이노 IDE 설치",
              "description": "운영체제별 IDE 설치 과정을 설명합니다.",
              "filename": "04-setup-ide.mdx"
            },
            {
              "type": "subsection",
              "title": "1.2.2 첫 스케치 프로그램 업로드",
              "description": "LED Blink 소스코드를 아두이노에 업로드해봅니다.",
              "filename": "05-hello-world.mdx"
            }
          ]
        }
      ]
    }
  ],
  "checkpoints": [
    {
      "afterCard": "03-history.mdx",
      "prompt": "아두이노가 오픈소스 하드웨어로서 갖는 장점에 대해 학습자가 직접 설명해보도록 유도하세요."
    }
  ]
}
```

---

## 4. cards/*.mdx 작성 규칙

1. **파일 포맷**: 확장자 `.mdx` (또는 `.md`)
2. **파일명 규칙**: 소문자 영문·숫자·하이픈(`-`) 조합 권장 (예: `01-intro.mdx`)
3. **H1 제목**: 파일명이 아닌 실제 레슨 제목 사용 (예: `Chapter 01 | LESSON 1-1: 아두이노 개요`)
4. **문체**: 자연스러운 서술형 문장. 개조식 요약 나열 지양
5. **이미지 참조**: `![설명](../images/파일명.png)` 상대 경로 사용
6. **시각적 리듬**: `소제목(H2) + 본문 + 이미지 또는 인용구(>)` 조합으로 구성

---

## 5. 업로드 전 자가 체크

| 항목 | 확인 내용 |
|------|----------|
| [C1] filename 형식 | `"cards/"` 접두어 없이 파일명만 (`"01-intro.mdx"` ✓, `"cards/01-intro.mdx"` ✗) |
| [C2] toc ↔ cards 일치 | toc의 모든 leaf filename 집합 == cards[] 집합 |
| [C3] 필수 필드 | 모든 노드에 `type`, `title`, `description` 존재 |
| [C4] type 값 | `"chapter"`, `"section"`, `"subsection"` 중 하나만 |
| [C5] 계층 중첩 | 불필요한 단계 추가 금지 |
| [C6] slug 형식 | 소문자·숫자·하이픈만 허용 |
| [C7] checkpoints | `afterCard` 값이 `cards[]`에 존재해야 함 |
| [Z1] ZIP 도구 | Python `zipfile` 모듈 사용 (PowerShell Compress-Archive 금지) |
| [Z2] ZIP 내용물 | `config.json`, `wiki.md`, `cards/**` 포함 / `*.zip` 제외 |

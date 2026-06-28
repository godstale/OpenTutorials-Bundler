# PennyPress Bundler

AI Agent를 활용하여 PDF, DOCX 등 원본 자료를 **PennyPress(Vivo Academy)** 강좌 번들(ZIP)로 자동 변환하는 워크스페이스입니다.

Claude Code, GitHub Copilot, Gemini CLI 등 AI Agent가 원본 자료를 분석하고, 카드(MDX), 목차(config.json), AI 튜터 지식 베이스(wiki.md)를 자동 생성합니다.

---

## 빠른 시작

### 1. 저장소 클론

```bash
git clone https://github.com/godstale/PennyPress-Bundler.git
cd PennyPress-Bundler
```

### 2. 원본 자료 배치

`origin/<강좌명>/` 폴더를 만들고 원본 파일(PDF, DOCX 등)을 넣습니다.

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

GitHub Copilot, Gemini CLI 등 다른 AI Agent도 동일하게 사용할 수 있습니다.

### 4. 결과 확인

```
converted/
└── my-course/
    ├── config.json      ← 강좌 메타데이터 + 목차(트리 구조)
    ├── wiki.md          ← AI 튜터 지식 베이스
    ├── cards/
    │   ├── 01-intro.mdx
    │   └── ...
    └── my-course.zip    ← PennyPress 업로드용 번들
```

생성된 ZIP 파일을 PennyPress Admin에서 업로드하면 강좌가 등록됩니다.

---

## 강좌 번들 구조

### config.json
강좌 메타데이터와 장-절-항 계층 목차(toc)를 정의합니다.

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

### cards/*.mdx
1파일 = 1카드(페이지). 기본 Markdown으로 작성하며 TTS로 읽힙니다.

### wiki.md
학습자에게는 보이지 않는 AI 튜터 전용 지식 베이스입니다.

---

## 문서

| 문서 | 설명 |
|------|------|
| [번들 구조 가이드](docs/bundling-guide/COURSE_STRUCTURE_GUIDE.md) | config.json 스키마, 파일 규격 상세 |
| [Agent 지침](docs/bundling-guide/AGENT_INSTRUCTIONS.md) | AI Agent를 위한 카드 작성 품질 기준 |
| [템플릿](docs/bundling-guide/templates/) | config.json, card.mdx, wiki.md 예시 |
| [PennyPress FE 참고](docs/penny-press/README.md) | PennyPress 플랫폼 아키텍처 |

---

## 도구

### 미리보기 생성

```bash
python tools/generate_preview.py <course-name>
```

`converted/<course-name>/preview.html`이 생성됩니다. 브라우저에서 바로 강좌 내용을 확인할 수 있습니다.

**요구사항**: Python 3.8+, `markdown` 패키지 (`pip install markdown`)

---

## 지원하는 AI Agent

| Agent | 지침 파일 |
|-------|----------|
| Claude Code | `CLAUDE.md` |
| GitHub Copilot / OpenAI Codex | `AGENTS.md` |
| Gemini CLI | `GEMINI.md` |

---

## 라이선스

MIT

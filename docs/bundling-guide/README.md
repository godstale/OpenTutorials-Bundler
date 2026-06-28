# Vivo Academy - Course Creation Kit

이 디렉토리는 Vivo Academy에 새로운 강좌를 등록하려는 작가(Content Author)가 AI Agent의 도움을 받아 강좌 패키지(ZIP 번들)를 손쉽게 제작할 수 있도록 돕는 리소스 모음입니다.

## 파일 구성

- `AGENT_INSTRUCTIONS.md`: AI Agent(ChatGPT, Claude, Gemini 등)에게 부여할 시스템 프롬프트 및 지침 가이드. 강좌 기획부터 파일 생성까지의 워크플로우를 정의합니다.
- `COURSE_STRUCTURE_GUIDE.md`: Vivo Academy 강좌 번들의 파일 구조 및 각 파일에 대한 명세서.
- `templates/`: AI Agent가 강좌 파일들을 생성할 때 참고할 수 있는 템플릿 파일들.
  - `config.json`
  - `card.mdx`
  - `wiki.md`

## 사용 방법 (작가용)

1. 선호하는 AI Agent(예: ChatGPT)에 `AGENT_INSTRUCTIONS.md` 내용을 복사하여 시스템 프롬프트나 초기 메시지로 입력합니다.
2. `COURSE_STRUCTURE_GUIDE.md`와 `templates/` 하위의 파일들을 AI Agent에게 파일로 첨부하거나 텍스트로 제공하여, Vivo Academy의 강좌 규격을 학습시킵니다.
3. AI Agent와 대화하며 만들고 싶은 강좌의 주제, 대상, 핵심 내용을 논의합니다.
4. AI Agent가 가이드에 맞춰 `config.json`, `.mdx` 파일, `wiki.md` 등의 파일 내용을 생성해주면, 이를 구조에 맞게 모아 ZIP 파일로 압축하여 Vivo 시스템에 등록합니다.

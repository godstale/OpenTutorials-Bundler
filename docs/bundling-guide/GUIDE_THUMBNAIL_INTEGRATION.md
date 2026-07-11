# 강좌/패키지 썸네일 및 플랫폼 아이콘 연동 가이드 (Agent 강좌 생성용)

이 문서는 Open Tutorials 서비스에 강좌 및 패키지의 **썸네일 이미지 및 플랫폼 아이콘 지정 기능**이 추가됨에 따라, 강좌 및 패키지를 자동으로 생성하는 외부 Agent/Bundler 프로젝트(예: `Open Tutorials Bundler`)가 이에 맞춰 산출물을 어떻게 구성해야 하는지 설명하는 개발 및 연동 지침입니다.

---

## 1. 변경 및 개선 사항 개요

1. **개별 강좌 등록 시 썸네일/아이콘 지정**:
   * **이미지 썸네일 지정**: 썸네일 이미지 파일(e.g., `thumbnail.png`)을 번들 파일에 포함하고, API(`POST /api/admin/courses/upload`) 호출 시 `FormData`에 `"thumbnail"` 필드로 이미지 파일을 함께 전송하여 등록할 수 있습니다.
   * **플랫폼 predefined 아이콘 지정**: 별도의 이미지 리소스 없이 플랫폼에 사전 정의(predefined)된 아이콘 중 하나를 지정할 수 있습니다. UI에서 직접 선택하거나 `FormData`에 `"selectedIcon"` 필드로 아이콘 ID를 전송하면 됩니다.
   * **폴백(Fallback) 지정**: 썸네일 이미지나 아이콘을 둘 다 지정하지 않는 경우, 플랫폼 내 기본 일반 아이콘(`icon:book`)이 자동으로 적용됩니다.

2. **강좌 패키지 등록 시 ZIP 번들(매니페스트 + 썸네일) 및 아이콘 지정**:
   * **ZIP 패키지 번들**: 패키지 자체의 썸네일 이미지와 `package-manifest.json`을 하나로 묶은 패키지 ZIP 번들 파일(`package-bundle.zip`)로 등록할 수 있습니다.
   * **매니페스트 내 아이콘 명시**: ZIP 파일 내에 이미지 파일을 포함하지 않더라도 `package-manifest.json` 내의 `"thumbnail"` 필드에 `"icon:megaphone"`, `"icon:bot"` 등과 같이 플랫폼 predefined 아이콘 코드를 입력하여 패키지 아이콘을 지정할 수 있습니다.
   * **폴백(Fallback)**: 썸네일 지정이 생략되면, 패키지 역시 기본 일반 아이콘(`icon:book`)으로 자동 등록됩니다.

---

## 2. 플랫폼 사전 정의 아이콘 (Predefined Icons) 목록

플랫폼은 다양한 강좌 영역을 나타내는 다음과 같은 아이콘을 사전에 정의해 두고 제공합니다. 외부 에이전트가 리소스를 아끼기 위해 아이콘을 지정하고자 한다면, 아래 ID 값을 명세 필드에 `"icon:{ID}"` 형태로 작성하면 됩니다.

### A. 기술 및 자동화 분야 (Technology & Automation)
| 아이콘 ID | 강좌 분야 (Label) | 매핑 아이콘 컴포넌트 |
| :--- | :--- | :--- |
| **`bot`** | AI 에이전트 | `Bot` |
| **`brain`** | 인공지능 / LLM | `Brain` |
| **`cpu`** | 시스템 / 하드웨어 | `Cpu` |
| **`terminal`** | 프롬프트 / 터미널 | `Terminal` |
| **`sparkles`** | 생성형 AI / 아트 | `Sparkles` |
| **`workflow`** | 자동화 / 워크플로우 | `Workflow` |
| **`zap`** | 실시간 / 트리거 | `Zap` |
| **`code`** | 소프트웨어 개발 | `Code2` |
| **`database`** | 데이터베이스 / SQL | `Database` |
| **`cloud`** | 클라우드 / DevOps | `Cloud` |
| **`lock`** | 보안 / 해킹 | `Lock` |
| **`globe`** | 웹 기술 / 네트워크 | `Globe` |
| **`smartphone`** | 모바일 앱 개발 | `Smartphone` |
| **`git`** | 버전 관리 / Git | `GitBranch` |
| **`message-square`** | 챗봇 / 메시징 | `MessageSquare` |
| **`layers`** | 시스템 아키텍처 | `Layers` |
| **`gamepad`** | 게임 개발 | `Gamepad2` |
| **`science`** | 과학 / 탐구 | `FlaskConical` |

### B. 일반 및 인문 / 경영 분야 (General & Humanities & Business)
| 아이콘 ID | 강좌 분야 (Label) | 매핑 아이콘 컴포넌트 |
| :--- | :--- | :--- |
| **`stock`** | 주식 / 금융 | `Coins` |
| **`line-chart`** | 비즈니스 / 성장 분석 | `LineChart` |
| **`plan`** | 기획 / 전략 | `ClipboardList` |
| **`history`** | 역사 / 인문학 | `History` |
| **`culture`** | 문화 / 교양 | `Compass` |
| **`music`** | 음악 / 음향 | `Music` |
| **`art`** | 미술 / 회화 | `Paintbrush` |
| **`politics`** | 정치 / 행정 | `Landmark` |
| **`society`** | 사회 / 시사 | `Users` |
| **`movie`** | 영화 / 영상 | `Film` |
| **`health`** | 건강 / 스포츠 | `Dumbbell` |
| **`travel`** | 여행 / 레저 | `Plane` |
| **`scale`** | 법률 / AI 윤리 | `Scale` |
| **`graduation-cap`** | 학업 / 이론 | `GraduationCap` |
| **`book`** | 일반 / 기초 (Default) | `BookOpen` |

---

## 3. Agent/Bundler 프로젝트 대응 가이드

### A. 강좌 패키지 ZIP 번들 구조
패키지를 번들로 포장할 때, 이미지 리소스를 아끼려면 다음과 같이 구성하여 내보냅니다.

```
package-bundle.zip
└── package-manifest.json (필수)
```

#### `package-manifest.json` 에서 아이콘 지정 예시 (이미지 동봉 없음)
```json
{
  "title": "마케팅 테마 패키지 강좌",
  "slug": "marketing-theme-package",
  "description": "마케팅 에이전트 서비스와 리서치 도구 활용법을 완전 마스터하는 강좌 패키지입니다.",
  "thumbnail": "icon:megaphone", 
  "published": true,
  "courses": [
    "marketing-basic-1",
    "marketing-strategy-2"
  ]
}
```
> [!NOTE]
> `"thumbnail"` 값을 `"icon:megaphone"` 처럼 지정할 경우, 서버와 클라이언트가 이를 플랫폼 사전 정의 아이콘으로 해석하여 렌더링하므로 번들에 별도 이미지 파일을 포함하거나 전송할 필요가 없습니다. 
> 만약 썸네일 값을 비워두면 자동으로 `"icon:book"`(기본 아이콘)이 사용됩니다.

---

### B. 개별 강좌 번들 ZIP 구조 및 API 전송
개별 강좌 역시 이미지 파일을 번들에 동봉하지 않고 API 전송 시 특정 아이콘 ID를 파라미터로 명시해 등록을 자동화할 수 있습니다.

#### API 전송 (Multipart/Form-Data) 방법 예시
```javascript
// Node.js 또는 Python 등의 스크립트에서 전송할 때 예시
const formData = new FormData();
formData.append('file', fs.createReadStream('./course-bundle.zip'));

// 이미지 대신 플랫폼 정의 아이콘 지정 (예: AI/LLM 분야)
formData.append('selectedIcon', 'brain'); 

const response = await fetch('https://opentutor.com/api/admin/courses/upload', {
  method: 'POST',
  body: formData,
  headers: {
    // API를 호출하는 세션/헤더 설정 (Admin 권한 필요)
  }
});
```

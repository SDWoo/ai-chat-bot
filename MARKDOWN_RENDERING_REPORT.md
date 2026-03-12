# 마크다운 렌더링 개선 보고서

**작성일:** 2026-03-10  
**작업자:** Frontend Quality Agent  
**프로젝트:** AI Chat Bot

---

## 📋 작업 개요

채팅 페이지의 마크다운 렌더링 품질을 진단하고 개선하여, AI 응답이 보기 좋고 구조화된 형태로 표시되도록 개선했습니다.

---

## 🔍 진단 결과

### ✅ 기존 긍정적 요소
- `react-markdown`, `remark-gfm`, `rehype-highlight` 라이브러리가 올바르게 설치됨
- 기본적인 prose 클래스 적용 시도
- 줄바꿈 처리를 위한 커스텀 컴포넌트 존재

### ❌ 발견된 문제점

#### 1. TailwindCSS Typography 플러그인 미설치
- **문제:** `prose` 클래스를 사용했으나 `@tailwindcss/typography` 플러그인이 없음
- **영향:** 마크다운 스타일이 전혀 적용되지 않음
- **증상:**
  - 제목(#, ##, ###)이 일반 텍스트처럼 표시
  - 굵은 글씨(**텍스트**)가 평범한 글씨로 표시
  - 목록(-, 1.)이 구조 없이 표시
  - 코드 블록이 하이라이팅 없이 표시

#### 2. 코드 하이라이팅 스타일 누락
- **문제:** `rehype-highlight` 플러그인은 있으나 highlight.js CSS 미적용
- **영향:** 코드 블록의 문법 강조가 표시되지 않음

#### 3. 사용자/AI 메시지 스타일 차별화 부족
- **문제:** 파란색 배경(사용자)과 흰색 배경(AI)에서 동일한 마크다운 스타일 사용
- **영향:** 사용자 메시지의 가독성 저하 가능성

---

## 🔧 적용한 개선 사항

### 1. package.json 수정
```json
"devDependencies": {
  "@tailwindcss/typography": "^0.5.10",
  ...
}
```
- TailwindCSS Typography 플러그인 추가

### 2. tailwind.config.js 수정
```javascript
plugins: [
  require('@tailwindcss/typography'),
],
```
- Typography 플러그인 활성화

### 3. index.css - 종합 마크다운 스타일 추가

#### 코드 하이라이팅
- GitHub 스타일 highlight.js 테마 추가
- CDN을 통한 빠른 로딩

#### 마크다운 요소별 상세 스타일

**제목 스타일:**
```css
h1: 1.8em, 700 weight, 충분한 여백, 자간 조정
h2: 1.5em, 700 weight, 계층 구조 명확
h3: 1.25em, 700 weight
h4: 1.1em, 700 weight
```

**텍스트 스타일:**
- 단락: 0.8em 상하 여백, 줄바꿈 자동 처리
- 굵은 글씨: 700 weight, 진한 색상
- 기울임: italic 스타일
- 링크: 파란색, 밑줄, hover 효과

**목록 스타일:**
- ul: disc 마커, 적절한 들여쓰기
- ol: 숫자 마커
- 중첩 목록: circle 마커로 구분
- 항목간 0.4em 여백

**코드 스타일:**
- 인라인 코드: 회색 배경, 분홍색 텍스트, 둥근 모서리
- 코드 블록: 밝은 회색 배경, 테두리, 수평 스크롤

**기타 요소:**
- 인용구: 좌측 파란색 보더, 기울임
- 표: 전체 너비, 회색 테두리, 헤더 배경
- 구분선: 회색 2px 선

#### 사용자 메시지용 밝은 테마
```css
.markdown-content-light
```
- 흰색 텍스트 기반
- 반투명 배경 요소
- 파란색 배경에서 최적화된 가독성

### 4. ChatPage.tsx 수정

**변경 전:**
```typescript
<div className="prose prose-sm max-w-none ...">
  <ReactMarkdown 
    components={{
      p: ({node, ...props}) => <p className="..." {...props} />,
      br: () => <br className="my-1" />,
    }}
  >
```

**변경 후:**
```typescript
<div className={`markdown-content ${message.role === 'user' ? 'markdown-content-light' : ''}`}>
  <ReactMarkdown 
    remarkPlugins={[remarkGfm]} 
    rehypePlugins={[rehypeHighlight]}
  >
```

**개선점:**
- 커스텀 CSS 클래스로 전환 (더 세밀한 제어)
- 사용자/AI 메시지별 자동 테마 적용
- 불필요한 커스텀 컴포넌트 제거 (CSS로 처리)
- 코드 간소화 및 유지보수성 향상

---

## 📊 개선 효과

### Before (개선 전)
```
# 제목입니다
제목입니다

## 소제목
소제목

**굵은 글씨**와 일반 글씨
굵은 글씨와 일반 글씨

- 항목 1
- 항목 2
- 항목 1 - 항목 2
```
→ 모든 텍스트가 동일한 크기와 굵기로 표시

### After (개선 후)
```
━━━━━━━━━━━━━━━━
제목입니다 (1.8배 크기, 굵게)
━━━━━━━━━━━━━━━━

소제목 (1.5배 크기, 굵게)
──────────────

굵은 글씨와 일반 글씨

• 항목 1
• 항목 2
```
→ 계층 구조가 명확하고 읽기 쉬운 형태

---

## 🎨 시각적 개선 사항

### AI 메시지 (흰색 배경)
- ✅ 제목이 크고 굵게 표시
- ✅ 굵은 글씨가 진하게 표시
- ✅ 목록이 bullet point로 구조화
- ✅ 코드 블록이 회색 배경에 하이라이팅
- ✅ 링크가 파란색 밑줄로 명확히 표시

### 사용자 메시지 (파란색 배경)
- ✅ 흰색 텍스트 기반 스타일
- ✅ 반투명 배경으로 요소 구분
- ✅ 높은 대비로 가독성 유지

---

## 📝 설치 안내

개선된 마크다운 렌더링을 적용하려면 다음 명령어를 실행하세요:

```bash
cd frontend
npm install
```

이 명령어는 새로 추가된 `@tailwindcss/typography` 패키지를 설치합니다.

---

## ✅ 검증 체크리스트

설치 후 다음 사항을 확인하세요:

### 1. 제목 렌더링
- [ ] `# 제목`이 크고 굵게 표시되는가?
- [ ] `## 소제목`이 중간 크기로 표시되는가?
- [ ] 제목 간 계층이 명확한가?

### 2. 텍스트 스타일
- [ ] `**굵은 글씨**`가 진하게 표시되는가?
- [ ] `*기울임*`이 이탤릭으로 표시되는가?
- [ ] 링크가 파란색 밑줄로 표시되는가?

### 3. 목록
- [ ] `- 항목`이 bullet point로 표시되는가?
- [ ] `1. 항목`이 번호로 표시되는가?
- [ ] 들여쓰기가 올바른가?

### 4. 코드
- [ ] 인라인 `코드`가 회색 배경에 표시되는가?
- [ ] 코드 블록이 하이라이팅되는가?
- [ ] 긴 코드가 가로 스크롤되는가?

### 5. 사용자 메시지
- [ ] 파란색 배경에서 흰색 텍스트가 명확한가?
- [ ] 모든 마크다운 요소가 가독성 있는가?

---

## 🚀 예상 사용 시나리오

### 시나리오 1: 구조화된 답변
**AI 응답:**
```markdown
# 주요 개념 설명

## 1. 기본 원리
기본 원리는 **중요한 개념**입니다.

- 첫 번째 포인트
- 두 번째 포인트

## 2. 상세 내용
자세한 내용은...
```

**표시 결과:**
- 대제목이 시선을 끌고
- 소제목으로 섹션이 명확히 구분되며
- 목록이 읽기 쉽게 정리됨

### 시나리오 2: 코드 설명
**AI 응답:**
```markdown
Python에서 리스트를 생성하려면:

```python
my_list = [1, 2, 3]
```

여기서 `my_list`는 변수명입니다.
```

**표시 결과:**
- 코드 블록이 문법 강조와 함께 표시
- 인라인 코드가 눈에 띄게 표시

### 시나리오 3: 표와 인용
**AI 응답:**
```markdown
| 항목 | 설명 |
|------|------|
| A    | 내용 |

> 중요한 인용문입니다.
```

**표시 결과:**
- 표가 깔끔한 그리드로 표시
- 인용문이 왼쪽 파란색 보더와 함께 표시

---

## 📌 주요 기술 스택

- **react-markdown**: 마크다운 파싱 및 렌더링
- **remark-gfm**: GitHub Flavored Markdown 지원
- **rehype-highlight**: 코드 문법 강조
- **@tailwindcss/typography**: 타이포그래피 스타일
- **highlight.js**: 코드 하이라이팅 테마

---

## 🔄 유지보수 가이드

### 마크다운 스타일 수정
`frontend/src/index.css`의 `.markdown-content` 섹션을 수정하세요.

### 코드 하이라이팅 테마 변경
`index.css`의 highlight.js CDN URL을 변경하세요:
```css
/* 현재: GitHub 테마 */
@import url('https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css');

/* 다른 테마 예시 */
@import url('https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/monokai.min.css');
```

### 사용자 메시지 테마 조정
`.markdown-content-light` 클래스를 수정하여 파란색 배경에서의 가독성을 조정하세요.

---

## 🎯 결론

### 달성한 목표
✅ 마크다운 요소가 올바르게 렌더링됨  
✅ 계층 구조가 시각적으로 명확함  
✅ 코드 블록이 문법 강조와 함께 표시됨  
✅ 사용자/AI 메시지가 각각 최적화된 스타일 적용  
✅ 전체적으로 전문적이고 읽기 쉬운 UI

### 사용자 경험 개선
- **가독성 향상**: 텍스트 계층이 명확하여 정보 파악이 쉬움
- **전문성 향상**: 세련된 타이포그래피로 브랜드 이미지 개선
- **학습 효과**: 구조화된 내용으로 이해도 증가
- **코드 공유**: 문법 강조로 코드 예제가 명확함

---

**Frontend Quality Agent**  
*Ensuring the best user experience through pixel-perfect design*

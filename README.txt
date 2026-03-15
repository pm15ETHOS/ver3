README

프론트엔드 코드 분리 및 재사용성을 높이기 위해 공통 CSS와 JS를 분리하고 각 화면별 HTML을 만듭니다.
---
### Common Assets
- #### [NEW] `assets/style.css`
  - 전체 레이아웃 (Sidebar, Topbar) 및 공통 색상(Teal Base Color `#009b84`), 버튼 스타일 등.
- #### [NEW] `assets/app.js`
  - 로그인 상태 확인 (`localStorage` 활용), 사이드바 렌더링, 로그아웃 기능 등 공통 함수.
---
### Pages (HTML)
- #### [NEW] `index.html` (메인 화면)
  - 사용자/관리자 정보 입력 화면. 정보 입력 시 `localStorage`에 저장 후 `intro.html`로 리다이렉트.
- #### [NEW] `intro.html` (학습 소개)
  - 프로그램 안내 및 커리큘럼 소개.
- #### [NEW] `video.html` (영상 화면)
  - 가상의 영상 플레이어 및 자동 다음 단계 이동 로직.
- #### [NEW] `chatbot.html` (챗봇 화면)
  - 시나리오(1~5) 선택 및 기존 [scenario_01.html]의 챗봇 기능을 통합 모듈화하여 각 시나리오별 시스템 프롬프트를 동적으로 로드하게 구현.
- #### [NEW] `survey.html` (만족도 조사)
  - 5가지 문항 응답 및 결과(GPT 분석) 표시 화면.
- #### [NEW] `outro.html` (교육 마무리)
  - 수료증 및 최종 안내.
- #### [NEW] `admin.html` (HR 화면)
  - 관리자 전용 대시보드. 더미 데이터를 활용한 차트 및 통계 표시.
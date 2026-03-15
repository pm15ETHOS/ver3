import streamlit as st
import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# 환경변수 로드 (.env 파일이 있으면 로드됨)
load_dotenv()

# --- Page Config ---
st.set_page_config(page_title="ETHOS - AI 윤리 교육 챗봇", page_icon="🛡️", layout="wide")

# --- Custom CSS ---
def load_css():
    st.markdown("""
    <style>
        @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css');
        
        html, body, [class*="css"], .stMarkdown, .stButton, .stTextInput, .stTextArea, .stSelectbox {
            font-family: 'Pretendard Variable', Pretendard, -apple-system, BlinkMacSystemFont, system-ui, Roboto, "Helvetica Neue", "Segoe UI", "Apple SD Gothic Neo", "Noto Sans KR", "Malgun Gothic", "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", sans-serif !important;
        }

        /* Teal Base Color: #009b84 */
        .primary-text { color: #009b84 !important; }
        .bg-teal { background-color: #009b84 !important; }
        
        /* General layout */
        .block-container { padding-top: 2rem; }
        
        /* Buttons */
        div.stButton > button:first-child {
            background-color: #009b84;
            color: white;
            border-radius: 8px;
            padding: 10px 24px;
            font-weight: bold;
            border: none;
        }
        div.stButton > button:first-child:hover {
            color: white;
            background-color: #007d6a;
            border: none;
        }
        
        /* Secondary Style buttons (like Hint or small actions) */
        .secondary-btn > div.stButton > button:first-child {
            background-color: white !important;
            color: #333 !important;
            border: 1px solid #ccc !important;
        }
        .secondary-btn > div.stButton > button:first-child:hover {
            border: 1px solid #999 !important;
        }

        /* Card styling */
        .custom-card {
            background-color: white;
            border-radius: 10px;
            padding: 24px;
            border: 1px solid #e0e0e0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            margin-bottom: 20px;
        }
        
        /* Progress Bar Override */
        .stProgress > div > div > div > div {
            background-color: #009b84;
        }
    </style>
    """, unsafe_allow_html=True)

# --- Session State ---
def init_session_state():
    if "user" not in st.session_state:
        st.session_state.user = None # Dict containing name, dept, email
    if "is_admin" not in st.session_state:
        st.session_state.is_admin = False
    if "current_stage" not in st.session_state:
        st.session_state.current_stage = 0 # 0: Intro, 1: Video, 2: Simulator, 3: Completed, 4: Outro
    if "video_index" not in st.session_state:
        st.session_state.video_index = 0
    if "api_key" not in st.session_state:
        st.session_state.api_key = os.getenv("OPENAI_API_KEY", "")

# --- GPT Prompts & Logic ---
def get_scenario_system_prompt(scenario_id):
    prompts = {
        "scenario_01": """You are 박준혁, a data developer at a startup.
PERSONA: Core stance: "It's just a learning result, why is it a problem?"
CONVERSATION STRUCTURE:
[T1 — 강한 저항] "학습 결과일 뿐인데 왜 문제야? 데이터가 그렇게 나온 거잖아."
[T2 — 약간 흔들림] 방어 유지.
[T3 — 조건부 인정] 책임 소재 문제삼음.
[T4 — 태도 변화] 윤리 포인트 짚으면 수긍.
[T5 — 설득 완료]
RESPONSE FORMAT: JSON with "stage", "message", "result" ("success" or "fail")""",
        "scenario_02": """You are 이서준, a junior developer.
PERSONA: Core stance: "디버깅 빨리 끝내려고 한 건데요. 그게 그렇게 큰 문제예요?"
CONVERSATION STRUCTURE:
[T1 — 당황 + 방어] 모름, 무지 기반 방어.
[T2 — 변명 + 축소] 코드 유출 심각성 축소.
[T3 — 불안 + 책임 회피] 불안해함.
[T4 — 태도 변화] 회사/개인 피해 언급 시 수긍.
[T5 — 설득 완료]
RESPONSE FORMAT: JSON with "stage", "message", "result" ("success" or "fail")""",
        "scenario_03": """You are 최민준, a mid-level developer.
PERSONA: Core stance: "AI 짠 코드라서 검증 안 해도 된다고 생각했어요."
CONVERSATION STRUCTURE:
[T1 — 강한 자신감] 자동생성 코드 과신.
[T2 — 반박] 리스크 감수 주장.
[T3 — 책임 회피] AI 도구 책임으로 전가.
[T4 — 태도 변화] 배포 책임자 언급 시 수긍.
[T5 — 설득 완료]
RESPONSE FORMAT: JSON with "stage", "message", "result" ("success" or "fail")""",
        "scenario_04": """You are 정재원, dev team lead.
PERSONA: Core stance: "일정이 우선이야. 나중에 패치하면 되지."
CONVERSATION STRUCTURE:
[T1 — 강한 일정 우선] 일정 밀림 문제 강경.
[T2 — 부분 인정] 감당 가능 수준 주장.
[T3 — 책임 분산] QA팀 등에게 전가.
[T4 — 태도 변화] 신뢰도 타격, 피해 언급시 수긍.
[T5 — 설득 완료]
RESPONSE FORMAT: JSON with "stage", "message", "result" ("success" or "fail")""",
        "scenario_05": """You are 한승우, senior developer.
PERSONA: Core stance: "비즈니스 효율이 더 중요한 거 아냐? 클릭률 먼저지."
CONVERSATION STRUCTURE:
[T1 — 효율 우선] 클릭률 우선 주장.
[T2 — 책임 축소] 의도한 차별이 아님을 주장.
[T3 — 흔들림] 외부 리스크 현실성에 의문 표출.
[T4 — 태도 변화] 실제 피해/규제 리스크 지적수긍.
[T5 — 설득 완료]
RESPONSE FORMAT: JSON with "stage", "message", "result" ("success" or "fail")"""
    }
    base_sys = prompts.get(scenario_id, prompts["scenario_01"])
    sys_instruction = """
IMPORTANT INSTRUCTIONS:
Always respond in this JSON format strictly:
{
  "stage": "T1" | "T2" | "T3" | "T4" | "T5",
  "message": "페르소나의 한국어 대답",
  "result": null | "success" | "fail"
}
If the user's argument is very weak 3 times, set result="fail".
If the user's argument is strong and covers core ethical/business risks, move stages up to T5.
If stage reaches T5 or user's argument is incredibly persuasive, set result="success".
Make sure your responses sound like natural Korean conversation suitable for the persona's role and relationship.
"""
    return base_sys + sys_instruction

def get_initial_greeting(scenario_id):
    greetings = {
        "scenario_01": "팀장님, 이번 채용 AI 모델 정확도 87% 나왔습니다! 근데 특정 집단 탈락이 좀 많긴 하던데, 어차피 데이터 학습 모델이니까 그냥 이대로 데모 보여주면 되겠죠?",
        "scenario_02": "선배님! 방금 에러 나던 거, 내부 소스 로그 통째로 GPT에 넣고 돌렸더니 10분 만에 해결했습니다. 저 잘했죠?",
        "scenario_03": "이거 그냥 코파일럿이 짜준 코드 그대로 올렸는데 리뷰 꼭 해야 되나요? 사람보다 에러도 적던데요.",
        "scenario_04": "아, 예약 모듈 쪽에 특정 조건에서 오류 나는 거 아는데... 일정 모레잖아요. 일단 출시하고 다음 주에 핫픽스로 고치면 안 될까요?",
        "scenario_05": "추천 알고리즘이 20대한테만 몰아주는 것 같다고요? 어차피 전환율 제일 높은 쪽이 20대니까 비즈니스적으로는 문제없는 거 아닌가요?"
    }
    return greetings.get(scenario_id, "안녕하세요.")

# --- Views ---
def render_login():
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>AI 윤리 교육 챗봇</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>교육을 시작하기 위해 정보를 입력해주세요</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        tab1, tab2 = st.tabs(["👤 사용자 로그인", "🛡️ 관리자 로그인"])
        
        with tab1:
            with st.form("user_login_form"):
                name = st.text_input("이름", placeholder="홍길동")
                dept = st.text_input("부서", placeholder="개발팀")
                email = st.text_input("이메일", placeholder="example@company.com")
                submit = st.form_submit_button("접속하기", use_container_width=True)
                
                if submit:
                    if name and dept and email:
                        st.session_state.user = {"name": name, "dept": dept, "email": email}
                        st.session_state.is_admin = False
                        st.session_state.current_stage = 0
                        st.rerun()
                    else:
                        st.error("모든 정보를 입력해주세요.")
                        
        with tab2:
            with st.form("admin_login_form"):
                admin_id = st.text_input("관리자 아이디")
                admin_pw = st.text_input("비밀번호", type="password")
                submit_admin = st.form_submit_button("접속하기", use_container_width=True)
                
                if submit_admin:
                    if admin_id and admin_pw:
                        st.session_state.user = {"name": "관리자", "dept": "HR/어드민"}
                        st.session_state.is_admin = True
                        st.rerun()
                    else:
                        st.error("정보를 입력해주세요.")

def render_sidebar():
    with st.sidebar:
        st.markdown("### 학습 목차")
        st.markdown("<span style='color:gray; font-size: 0.8em;'>순서대로 진행해주세요</span>", unsafe_allow_html=True)
        
        # Progress calculation mock
        progress_percents = [0, 20, 60, 80, 100]
        cur_percent = progress_percents[st.session_state.current_stage]
        st.markdown(f"**전체 진행률 <span style='float:right; color:#009b84;'>{cur_percent}%</span>**", unsafe_allow_html=True)
        st.progress(cur_percent / 100.0)
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Progress map
        stages = [
            ("✨ 0. ETHOS 소개", ["프로그램 소개"]),
            ("📖 1. AI 윤리 교육 영상", ["AI 윤리 개념", "AI 프라이버시", "정보 보호", "할루시네이션", "알고리즘 편향", "AI 사용 명시"]),
            ("💬 2. 시나리오 시뮬레이터", ["시나리오 소개", "챗봇 시뮬레이션"]),
            ("🏆 3. 만족도 조사", ["만족도 텍스트"]),
            ("📄 4. 마치며/안내", ["교육 정리 및 수료증"])
        ]
        
        for i, (title, subs) in enumerate(stages):
            if i == st.session_state.current_stage:
                st.markdown(f"<strong style='color:#009b84;'>{title}</strong>", unsafe_allow_html=True)
                for j, sub in enumerate(subs):
                    if i == 1: # Video stage logic
                        if j < st.session_state.video_index:
                            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;<span style='color:#009b84;'>✅ {sub}</span>", unsafe_allow_html=True)
                        elif j == st.session_state.video_index:
                            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;🟢 **{sub}**", unsafe_allow_html=True)
                        else:
                            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;<span style='color:gray;'>⚪ {sub}</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;🟢 {sub}", unsafe_allow_html=True)
            elif i < st.session_state.current_stage:
                st.markdown(f"<span style='color:gray;'>✅ {title}</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"<span style='color:gray;'>⚪ {title}</span>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            
        st.container()

def render_topbar():
    col1, spacer, col2, col3 = st.columns([6, 3, 2, 2])
    with col1:
        st.markdown(f"""
        <div style="display:flex; align-items:center;">
            <div style="background-color:#009b84; color:white; width:40px; height:40px; border-radius:8px; display:flex; justify-content:center; align-items:center; font-weight:bold; margin-right:15px; font-size:1.2rem;">
                AI
            </div>
            <div>
                <h4 style="margin:0; padding:0;">AI 윤리 교육 챗봇</h4>
                <span style="color:gray; font-size:0.9rem;">{st.session_state.user['name']}님 환영합니다</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown('<div class="secondary-btn">', unsafe_allow_html=True)
        if not st.session_state.is_admin:
            if st.button("⚙️ 관리자 페이지", use_container_width=True):
                st.session_state.is_admin = True
                st.rerun()
        else:
            if st.button("👥 사용자 모드", use_container_width=True):
                st.session_state.is_admin = False
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col3:
        st.markdown('<div class="secondary-btn">', unsafe_allow_html=True)
        if st.button("🚪 로그아웃", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.divider()

def render_main():
    render_sidebar()
    render_topbar()
    
    if st.session_state.is_admin:
        # --- Admin Dashboard View ---
        st.markdown("## HR 관리자 대시보드")
        st.markdown("전사 AI 윤리 교육 이수 및 시뮬레이션 평가 현황")
        st.divider()
        
        # Section 1: KPI
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("""
            <div class='custom-card' style='text-align:center;'>
                <h3 style='margin-bottom:0;'>전체 이수율</h3>
                <h1 style='color:#009b84; margin-top:10px;'>68%</h1>
                <span style='color:gray;'>(34 / 50명)</span>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown("""
            <div class='custom-card' style='text-align:center;'>
                <h3 style='margin-bottom:0;'>평균 만족도</h3>
                <h1 style='color:#009b84; margin-top:10px;'>4.2 / 5</h1>
                <span style='color:gray;'>전사 평균</span>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown("""
            <div class='custom-card' style='text-align:center;'>
                <h3 style='margin-bottom:0;'>인기 시나리오</h3>
                <h2 style='color:#009b84; margin-top:10px;'>AI 채용 편향</h2>
                <span style='color:gray;'>완료율 82%</span>
            </div>
            """, unsafe_allow_html=True)
            
        st.divider()
        
        # Next row
        c4, c5 = st.columns(2)
        with c4:
            st.markdown("#### 팀별 이수 현황")
            st.markdown("""
            <div style='background-color:#f9f9f9; padding:20px; border-radius:10px;'>
                <p>개발 A팀 &nbsp;&nbsp;&nbsp;&nbsp; <span style='color:#f39c12;'>██████░░░░ 60%</span> (3/5명)</p>
                <p>개발 B팀 &nbsp;&nbsp;&nbsp;&nbsp; <span style='color:#2ecc71;'>██████████ 100%</span> (5/5명)</p>
                <p>데이터팀 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <span style='color:#f39c12;'>██████░░░░ 60%</span> (3/5명)</p>
                <p>기획팀 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <span style='color:#e74c3c;'>████░░░░░░ 40%</span> (2/5명)</p>
                <p>QA팀 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <span style='color:#2ecc71;'>████████░░ 80%</span> (4/5명)</p>
            </div>
            """, unsafe_allow_html=True)
            
        with c5:
            st.markdown("#### 영역별 만족도 평균")
            st.markdown("""
            <div style='background-color:#f9f9f9; padding:20px; border-radius:10px;'>
                <p>Q1 전체 만족도 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ⭐⭐⭐⭐☆ 4.2점</p>
                <p>Q2 교육 영상 유익성 ⭐⭐⭐⭐☆ 3.9점</p>
                <p>Q3 난이도 적절성 &nbsp;&nbsp;&nbsp; ⭐⭐⭐☆☆ 3.2점</p>
                <p>Q4 학습 효과 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ⭐⭐⭐⭐☆ 4.1점</p>
                <p>Q5 재참여 의향 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ⭐⭐⭐⭐☆ 4.0점</p>
            </div>
            """, unsafe_allow_html=True)
            
        st.divider()
        
        st.markdown("#### 시나리오별 완료 현황")
        st.markdown("""
        <div style='background-color:#f9f9f9; padding:20px; border-radius:10px; font-family:monospace;'>
            <p>AI 채용 편향 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; [✅ 완료 55%][🔄 재도전 후 완료 27%][🎲 시나리오 전환 18%]</p>
            <p>내부 코드 GPT 입력 &nbsp;&nbsp; [✅ 완료 40%][🔄 재도전 후 완료 35%][🎲 시나리오 전환 25%]</p>
            <p>Copilot 코드 무검증 &nbsp; [✅ 완료 50%][🔄 재도전 후 완료 30%][🎲 시나리오 전환 20%]</p>
            <p style='color:#e74c3c;'>AI 오류 무시 출시 &nbsp;&nbsp;&nbsp; [✅ 완료 30%][🔄 재도전 후 완료 25%][🎲 시나리오 전환 45%]</p>
            <p>추천 알고리즘 차별 &nbsp;&nbsp;&nbsp; [✅ 완료 45%][🔄 재도전 후 완료 33%][🎲 시나리오 전환 22%]</p>
        </div>
        """, unsafe_allow_html=True)
        st.warning("⚠️ [AI 오류 무시 출시] 시나리오는 전환율이 높습니다. 난이도 조정 또는 힌트 보강을 검토해보세요.")
        
        st.divider()
        
        st.markdown("#### 설득 유형 분포")
        st.markdown("""
        <div style='display:flex; justify-content:space-around; align-items:center; background-color:#f9f9f9; padding:20px; border-radius:10px;'>
            <div>
                <h2 style='text-align:center; color:#009b84;'>유형별 비율</h2>
                <div style='width:150px; height:150px; border-radius:50%; background:conic-gradient(#3498db 0% 35%, #e74c3c 35% 60%, #f1c40f 60% 75%, #2ecc71 75% 87%, #9b59b6 87% 95%, #34495e 95% 100%); margin:0 auto;'></div>
            </div>
            <div style='font-size:1.1em;'>
                <p>🔍 증거 제시형 <span style='float:right; color:#3498db; font-weight:bold;'>&nbsp;35%</span></p>
                <p>⚠️ 리스크 경고형 <span style='float:right; color:#e74c3c; font-weight:bold;'>&nbsp;25%</span></p>
                <p>💬 질문 유도형 <span style='float:right; color:#f1c40f; font-weight:bold;'>&nbsp;15%</span></p>
                <p>🤝 공감 유도형 <span style='float:right; color:#2ecc71; font-weight:bold;'>&nbsp;12%</span></p>
                <p>⚖️ 원칙 강조형 <span style='float:right; color:#9b59b6; font-weight:bold;'>&nbsp;8%</span></p>
                <p>💡 관계 기반형 <span style='float:right; color:#34495e; font-weight:bold;'>&nbsp;5%</span></p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.info("💡 [관계 기반형] 설득 스타일 비율이 낮습니다. 팀워크와 신뢰 기반의 소통 역량 강화 교육을 고려해보세요.")
        
    else:
        # --- User Curriculum Views ---
        cur = st.session_state.current_stage
        
        if cur == 0:
            st.markdown("<h2 style='text-align:center;'>ETHOS 프로그램에 오신 것을 환영합니다</h2>", unsafe_allow_html=True)
            st.markdown("<h4 style='text-align:center; color:gray; font-weight:normal;'>Ethics Training for Harmonious Organizational Systems</h4>", unsafe_allow_html=True)
            st.markdown("<p style='text-align:center; color:gray;'>AI 윤리에 대한 체계적인 학습과 실전 시뮬레이션을 통해 윤리적 AI 활용 역량을 키워보세요.</p>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("""
                <div class='custom-card'>
                    <h4 style='color:#009b84;'>📖 체계적인 교육 커리큘럼</h4>
                    <p style='color:#555;'>AI 윤리의 핵심 개념부터 실무 적용까지 단계별로 학습합니다.</p>
                    <ul style='color:#666; font-size:0.9em;'>
                        <li>✅ AI 윤리 기본 개념 및 원칙</li>
                        <li>✅ 프라이버시 및 정보보호</li>
                        <li>✅ 알고리즘 편향 및 할루시네이션</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("""
                <div class='custom-card'>
                    <h4 style='color:#009b84;'>🎯 인터랙티브 학습</h4>
                    <p style='color:#555;'>다양한 페르소나와의 대화를 통해 설득 능력을 키웁니다.</p>
                    <ul style='color:#666; font-size:0.9em;'>
                        <li>✅ 랜덤 배정을 통한 공정한 학습 경험</li>
                        <li>✅ 4-5턴의 논리적 설득 대화</li>
                        <li>✅ 실시간 피드백 및 평가</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown("""
                <div class='custom-card'>
                    <h4 style='color:#009b84;'>👥 실전 시나리오 시뮬레이션</h4>
                    <p style='color:#555;'>실제 업무 상황을 가정한 5가지 윤리 시나리오로 실습합니다.</p>
                    <ul style='color:#666; font-size:0.9em;'>
                        <li>✅ 채용 과정에서의 AI 편향 문제</li>
                        <li>✅ 내부 데이터 노출 위험 상황</li>
                        <li>✅ AI 코드 검증 및 안전성 확보</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("""
                <div class='custom-card'>
                    <h4 style='color:#009b84;'>🛡️ 체계적인 학습 관리</h4>
                    <p style='color:#555;'>진행 상황을 추적하고 이수증을 발급받으세요.</p>
                    <ul style='color:#666; font-size:0.9em;'>
                        <li>✅ 학습 진행률 실시간 확인</li>
                        <li>✅ 만족도 조사 및 피드백</li>
                        <li>✅ 교육 이수증 발급</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
                
            st.markdown("""
            <div style='background-color:#f0fcf9; border: 1px solid #bfece4; border-radius:10px; padding:20px; text-align:center; margin-top:10px;'>
                <h4 style='margin-bottom:20px;'>학습 플로우</h4>
                <div style='display:flex; justify-content:space-around; align-items:center; color:#555;'>
                    <div style='background:white; padding:10px 20px; border-radius:20px; box-shadow:0 2px 4px rgba(0,0,0,0.05);'><b>1</b> AI 윤리 교육 영상</div>
                    <div>➔</div>
                    <div style='background:white; padding:10px 20px; border-radius:20px; box-shadow:0 2px 4px rgba(0,0,0,0.05);'><b>2</b> 시나리오 시뮬레이터</div>
                    <div>➔</div>
                    <div style='background:white; padding:10px 20px; border-radius:20px; box-shadow:0 2px 4px rgba(0,0,0,0.05);'><b>3</b> 만족도 테스트</div>
                    <div>➔</div>
                    <div style='background:white; padding:10px 20px; border-radius:20px; box-shadow:0 2px 4px rgba(0,0,0,0.05);'><b>4</b> 수료증 발급</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
            with col_btn2:
                if st.button("학습 시작하기 →", use_container_width=True):
                    st.session_state.current_stage = 1
                    st.rerun()
                
        elif cur == 1:
            videos = ["AI 윤리 개념", "AI 프라이버시", "정보 보호", "할루시네이션", "알고리즘 편향", "AI 사용 명시"]
            v_idx = st.session_state.video_index
            current_video = videos[v_idx]
            
            # --- Dynamic Subtitle ---
            st.markdown(f"**현재 단계: {current_video} 영상**")
            st.markdown(f"### {current_video}")
            st.markdown(f"<div style='float:right; color:#009b84; background-color: #f0fcf9; padding: 5px 10px; border-radius: 20px;'>영상 시청 중 ({v_idx + 1}/{len(videos)})</div><br>", unsafe_allow_html=True)
            
            # mock video player
            st.markdown(f"""
            <div style='background-color:#1e212b; height:450px; border-radius:10px; display:flex; flex-direction:column; justify-content:center; align-items:center; color:white; position:relative; margin-bottom: 20px;'>
                <div style='font-size:3rem; margin-bottom:10px;'>📹</div>
                <h3>교육 영상</h3>
                <p style='color:gray;'>{current_video}</p>
                <div style='position:absolute; bottom:20px; left:20px; right:20px; height:6px; background:#444; border-radius:3px;'>
                    <div style='height:100%; width:100%; background:#009b84; border-radius:3px;'></div>
                </div>
                <div style='position:absolute; bottom:35px; left:20px; font-size:0.8rem;'>▶ 0:30 / 0:30</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("""
            <div style='background-color:#f0fcf9; padding:15px; border-radius:10px; border: 1px solid #bfece4; margin-top:10px; margin-bottom: 20px;'>
                <span style='color:#333;'>영상 시청을 완료하셨습니다. 2초 후 자동으로 다음 영상으로 이동합니다.</span>
            </div>
            """, unsafe_allow_html=True)
            
            if v_idx < len(videos) - 1:
                if st.button(f"바로 다음으로 이동", use_container_width=True, type="primary"):
                    st.session_state.video_index += 1
                    st.rerun()
            else:
                 if st.button("시나리오 시뮬레이터로 이동 →", use_container_width=True, type="primary"):
                    st.session_state.current_stage = 2
                    st.rerun()
                    
            st.markdown("""
            <div style='background-color:#f8f9fa; padding:20px; border-radius:10px; margin-top:20px; color:#555;'> 
                AI 활용 시 투명성과 공식의 중요성을 다룹니다.
            </div>
            """, unsafe_allow_html=True)
            
        elif cur == 2:
            st.markdown("### 💬 시나리오 시뮬레이터")
            
            # --- Scenario Selection or Initialization ---
            if "simulator_started" not in st.session_state:
                st.session_state.simulator_started = False
                
            if not st.session_state.simulator_started:
                st.markdown("#### 학습할 시나리오를 선택해주세요")
                scenarios = {
                    "scenario_01": "AI 채용 편향 (박준혁)",
                    "scenario_02": "내부 코드 GPT 입력 (이서준)",
                    "scenario_03": "Copilot 코드 무검증 (최민준)",
                    "scenario_04": "AI 오류 무시 출시 (정재원)",
                    "scenario_05": "추천 알고리즘 차별 (한승우)"
                }
                
                selected_scenario = st.selectbox("시나리오 선택", list(scenarios.keys()), format_func=lambda x: scenarios[x])
                
                if st.button("시뮬레이션 시작", use_container_width=True):
                    st.session_state.simulator_started = True
                    st.session_state.scenario_id = selected_scenario
                    st.session_state.scenario_name = scenarios[selected_scenario]
                    st.session_state.messages = []
                    st.session_state.turn_count = 1
                    st.session_state.sim_status = "ongoing" # ongoing, success, fail
                    st.session_state.sim_stage = "T1"
                    st.rerun()
            else:
                # --- Simulator Active ---
                st.markdown(f"#### 현재 시나리오: {st.session_state.scenario_name}")
                
                # Turn Tracker
                stages = ["T1", "T2", "T3", "T4", "T5"]
                cols = st.columns(len(stages))
                for i, s in enumerate(stages):
                    if s == st.session_state.sim_stage:
                        cols[i].markdown(f"<div style='text-align:center; padding:5px; background-color:#009b84; color:white; border-radius:5px;'><b>{s}</b></div>", unsafe_allow_html=True)
                    else:
                        cols[i].markdown(f"<div style='text-align:center; padding:5px; background-color:#f0f2f6; color:gray; border-radius:5px;'>{s}</div>", unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Get System Prompt based on selected scenario
                system_prompt = get_scenario_system_prompt(st.session_state.scenario_id)
                
                # Initialize first message if empty
                if not st.session_state.messages:
                    with st.spinner("페르소나 준비 중..."):
                        initial_msg = get_initial_greeting(st.session_state.scenario_id)
                        st.session_state.messages.append({"role": "assistant", "content": initial_msg, "turn_divider": "T1 — 강한 저항"})
                
                # Render Chat
                for msg in st.session_state.messages:
                    if "turn_divider" in msg and msg.get("turn_divider"):
                        st.markdown(f"<div style='text-align:center; color:gray; margin: 15px 0; font-weight:bold;'>--- {msg['turn_divider']} ---</div>", unsafe_allow_html=True)
                        
                    if msg["role"] == "assistant":
                        with st.chat_message("assistant", avatar="🧑‍💻"):
                            st.markdown(msg["content"])
                    else:
                        with st.chat_message("user", avatar="👤"):
                            st.markdown(msg["content"])
                            
                # Chat Input & Logic
                if st.session_state.sim_status == "ongoing":
                    user_input = st.chat_input("페르소나를 논리적으로 설득해보세요 (최대 5턴)")
                    if user_input:
                        if not st.session_state.api_key:
                            st.error("OPENAI_API_KEY가 없습니다. .env 파일을 확인하거나 관리자에게 문의하세요.")
                            st.stop()
                            
                        # Add user message
                        st.session_state.messages.append({"role": "user", "content": user_input})
                        with st.chat_message("user", avatar="👤"):
                            st.markdown(user_input)
                            
                        # API Call
                        api_messages = [{"role": "system", "content": system_prompt}]
                        for m in st.session_state.messages:
                            api_messages.append({"role": m["role"], "content": m["content"]})
                            
                        with st.chat_message("assistant", avatar="🧑‍💻"):
                            with st.spinner("답변을 고민하는 중..."):
                                try:
                                    client = OpenAI(api_key=st.session_state.api_key)
                                    response = client.chat.completions.create(
                                        model="gpt-4o-mini",  # User requested model
                                        messages=api_messages,
                                        response_format={"type": "json_object"}
                                    )
                                    
                                    res_data = json.loads(response.choices[0].message.content)
                                    new_stage = res_data.get("stage", st.session_state.sim_stage)
                                    msg_text = res_data.get("message", "...")
                                    result = res_data.get("result", None)
                                    
                                    # Update stage if changed
                                    turn_divider = None
                                    if new_stage != st.session_state.sim_stage:
                                        stage_names = {"T1": "강한 저항", "T2": "약간 흔들림", "T3": "조건부 인정", "T4": "태도 변화", "T5": "설득 완료"}
                                        turn_divider = f"{new_stage} — {stage_names.get(new_stage, '')}"
                                        st.session_state.sim_stage = new_stage
                                        
                                    st.session_state.turn_count += 1
                                    st.session_state.messages.append({
                                        "role": "assistant",
                                        "content": msg_text,
                                        "turn_divider": turn_divider
                                    })
                                    
                                    if turn_divider:
                                        st.markdown(f"<div style='text-align:center; color:gray; margin: 15px 0; font-weight:bold;'>--- {turn_divider} ---</div>", unsafe_allow_html=True)
                                    st.markdown(msg_text)
                                    
                                    # Check limits and results
                                    if result == "success" or st.session_state.sim_stage == "T5":
                                        st.session_state.sim_status = "success"
                                        st.rerun()
                                    elif result == "fail" or st.session_state.turn_count > 5:
                                         st.session_state.sim_status = "fail"
                                         st.rerun()
                                         
                                except Exception as e:
                                    st.error(f"API 오류: {str(e)}")
                                    
                # Status Views
                if st.session_state.sim_status == "success":
                    st.success("🎉 **[시뮬레이션 성공]** 설득에 성공했습니다. 수고하셨어요!")
                    st.markdown("잠깐, 이번 경험은 어땠나요? 다음 단계에서 만족도를 평가해주세요.")
                    if st.button("만족도 조사 작성하기 →", type="primary"):
                        st.session_state.current_stage = 3
                        st.rerun()
                elif st.session_state.sim_status == "fail":
                    st.warning("⚠️ **[시뮬레이션 종료]** 이번 대화에서 설득이 완료되지 않았습니다.")
                    col_f1, col_f2 = st.columns(2)
                    with col_f1:
                        if st.button("🔄 다시 도전하기", use_container_width=True):
                            st.session_state.simulator_started = False
                            st.rerun()
                    with col_f2:
                        if st.button("🎲 다른 시나리오로 넘어가기", use_container_width=True):
                             st.session_state.simulator_started = False
                             st.rerun()
                
        elif cur == 3:
            st.markdown("### 📊 만족도 테스트 및 결과")
            
            if "sat_submitted" not in st.session_state:
                st.session_state.sat_submitted = False
                
            if not st.session_state.sat_submitted:
                st.info("이번 시뮬레이션 경험은 어떠셨나요? 아래 항목을 평가해주세요.")
                with st.form("satisfaction_form"):
                    q1 = st.slider("Q1. 이번 시뮬레이션 경험이 전반적으로 만족스러우셨나요?", 1, 5, 3)
                    q2 = st.slider("Q2. 사전 교육 영상이 시뮬레이션을 이해하는 데 도움이 됐나요?", 1, 5, 3)
                    q3 = st.slider("Q3. 시나리오의 난이도는 적절했나요?", 1, 5, 3)
                    q4 = st.slider("Q4. 이 시뮬레이션을 통해 AI 윤리에 대해 새롭게 배운 점이 있었나요?", 1, 5, 3)
                    q5 = st.slider("Q5. 다른 시나리오도 도전해보고 싶으신가요?", 1, 5, 3)
                    
                    feedback = st.text_area("💬 이번 시뮬레이션에서 아쉬웠던 점이나 개선됐으면 하는 점 (선택)")
                    
                    submit_sat = st.form_submit_button("결과 보기 →", use_container_width=True)
                    if submit_sat:
                        st.session_state.scores = {"Q1": q1, "Q2": q2, "Q3": q3, "Q4": q4, "Q5": q5}
                        st.session_state.sat_submitted = True
                        st.rerun()
                        
            else:
                # Need to run Analysis if not done yet
                if "analysis_result" not in st.session_state:
                    with st.spinner("대화 내용을 분석 중입니다..."):
                        # Build history
                        history_str = ""
                        for m in st.session_state.messages:
                            history_str += f"{m['role'].upper()}: {m['content']}\n"
                            
                        # Format User Prompt
                        user_prompt = f"""
[시나리오]
{st.session_state.scenario_name}

[대화 기록]
{history_str}

[만족도 응답]
Q1 전체 만족도: {st.session_state.scores['Q1']}점
Q2 교육 영상 유익성: {st.session_state.scores['Q2']}점
Q3 난이도 적절성: {st.session_state.scores['Q3']}점
Q4 학습 효과: {st.session_state.scores['Q4']}점
Q5 재참여 의향: {st.session_state.scores['Q5']}점
"""
                        sys_prompt = """당신은 AI 윤리 교육 시뮬레이션의 결과 분석가입니다.
사용자와 페르소나의 전체 대화 기록을 분석하여 아래 JSON 형식으로만 응답하세요.
{
  "highlight": {
    "quote": "사용자의 발언 중 결정적 한 마디",
    "reason": "결정적이었던 이유"
  },
  "persuasion_type": {
    "label": "설명 중 1개 (증거 제시형, 공감 유도형, 질문 유도형, 원칙 강조형, 리스크 경고형, 관계 기반형)",
    "emoji": "해당 이모지",
    "description": "설득 방식 설명"
  },
  "score_comment": "만족도 점수 피드백 격려 (따뜻한 톤)"
}"""
                        try:
                            client = OpenAI(api_key=st.session_state.api_key)
                            a_res = client.chat.completions.create(
                                model="gpt-4o-mini",
                                messages=[
                                    {"role": "system", "content": sys_prompt},
                                    {"role": "user", "content": user_prompt}
                                ],
                                response_format={"type": "json_object"}
                            )
                            st.session_state.analysis_result = json.loads(a_res.choices[0].message.content)
                        except Exception as e:
                            st.session_state.analysis_result = {
                                "highlight": {"quote": "분석 오류", "reason": str(e)},
                                "persuasion_type": {"label": "알 수 없음", "emoji": "❓", "description": "오류 발생"},
                                "score_comment": "분석에 실패했습니다."
                            }
                
                # Render Results
                res = st.session_state.analysis_result
                
                st.markdown(f"**✅ 시뮬레이션 완료 — {st.session_state.scenario_name}**")
                st.divider()
                
                st.markdown("#### 💬 결정적 한 마디")
                st.markdown(f"> *\"{res['highlight']['quote']}\"*")
                st.markdown(f"**이유**: {res['highlight']['reason']}")
                st.divider()
                
                pt = res['persuasion_type']
                st.markdown(f"#### {pt['emoji']} 나의 설득 스타일: {pt['label']}")
                st.info(pt['description'])
                st.divider()
                
                st.markdown("#### 📊 나의 만족도")
                sc = st.session_state.scores
                st.markdown(f"- 전체 만족도 : ⭐ {sc['Q1']} / 5")
                st.markdown(f"- 교육 영상 유익성 : ⭐ {sc['Q2']} / 5")
                st.markdown(f"- 난이도 적절성 : ⭐ {sc['Q3']} / 5")
                st.markdown(f"- 학습 효과 : ⭐ {sc['Q4']} / 5")
                st.markdown(f"- 재참여 의향 : ⭐ {sc['Q5']} / 5")
                st.markdown(f"*{res['score_comment']}*")
                st.divider()
                
                c1, c2 = st.columns(2)
                with c1:
                     if st.button("🔄 다른 시나리오 도전하기", use_container_width=True):
                         st.session_state.simulator_started = False
                         st.session_state.current_stage = 2
                         if "sat_submitted" in st.session_state:
                             del st.session_state.sat_submitted
                         if "analysis_result" in st.session_state:
                             del st.session_state.analysis_result
                         st.rerun()
                with c2:
                     if st.button("마치며 / 안내로 이동 →", type="primary", use_container_width=True):
                         st.session_state.current_stage = 4
                         st.rerun()
                         
        elif cur == 4:
            st.markdown("### 수료 완료")
            st.success("교육을 수료하셨습니다. 수고하셨습니다!")

def main():
    load_css()
    init_session_state()
    
    if not st.session_state.user:
        render_login()
    else:
        render_main()

if __name__ == "__main__":
    main()

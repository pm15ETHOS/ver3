// assets/app.js

// Stages: 0: Intro/Login, 1: Video, 2: Simulator, 3: Survey, 4: Outro

const CURRICULUM = [
    { id: 0, title: "✨ 0. ETHOS 소개", items: ["프로그램 소개"] },
    { id: 1, title: "📖 1. AI 윤리 교육 영상", items: ["AI 윤리 개념", "AI 프라이버시", "정보 보호", "할루시네이션", "알고리즘 편향", "AI 사용 명시"] },
    { id: 2, title: "💬 2. 시나리오 시뮬레이터", items: ["시나리오 소개", "챗봇 시뮬레이션"] },
    { id: 3, title: "🏆 3. 만족도 조사", items: ["만족도 텍스트"] },
    { id: 4, title: "📄 4. 마치며/안내", items: ["교육 정리 및 수료증"] }
];

const STAGE_PROGRESS = [0, 20, 60, 80, 100];

// State Management
const State = {
    getUser: () => JSON.parse(localStorage.getItem('ethos_user') || 'null'),
    setUser: (userObj) => localStorage.setItem('ethos_user', JSON.stringify(userObj)),
    getStage: () => parseInt(localStorage.getItem('ethos_stage') || '0', 10),
    setStage: (stageNum) => localStorage.setItem('ethos_stage', stageNum.toString()),
    logout: () => {
        localStorage.removeItem('ethos_user');
        localStorage.removeItem('ethos_stage');
        localStorage.removeItem('ethos_video_idx');
        localStorage.removeItem('ethos_sim_started');
        localStorage.removeItem('ethos_active_scenario');
        localStorage.removeItem('ethos_chat_history');
        window.location.href = 'index.html';
    }
};

// UI Components Render
function renderSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (!sidebar) return;

    const curStage = State.getStage();
    const curPercent = STAGE_PROGRESS[curStage] || 0;
    
    // Video specific logic
    const videoIdx = parseInt(localStorage.getItem('ethos_video_idx') || '0', 10);

    let html = `
        <h3>학습 목차</h3>
        <div class="sidebar-sub">순서대로 진행해주세요</div>
        
        <div class="progress-section">
            <div class="progress-header">
                <span>전체 진행률</span>
                <span class="progress-percent">${curPercent}%</span>
            </div>
            <div class="progress-bar-bg">
                <div class="progress-bar-fill" style="width: ${curPercent}%;"></div>
            </div>
        </div>
        
        <div class="curriculum-list">
    `;

    CURRICULUM.forEach((group, i) => {
        let groupStatus = 'upcoming';
        let groupIcon = '⚪';
        if (i < curStage) { groupStatus = 'done'; groupIcon = '✅'; }
        else if (i === curStage) { groupStatus = 'active'; groupIcon = ''; }

        html += `<div class="curr-group ${groupStatus}">
            <div class="curr-group-title">${groupIcon} ${group.title}</div>
            <div class="curr-items">`;

        group.items.forEach((item, j) => {
            let itemStatus = 'upcoming';
            let itemIcon = '⚪';

            if (i < curStage) {
                itemStatus = 'done';
                itemIcon = '✅';
            } else if (i === curStage) {
                if (i === 1) { // Video stage logic
                    if (j < videoIdx) { itemStatus = 'done'; itemIcon = '✅'; }
                    else if (j === videoIdx) { itemStatus = 'active'; itemIcon = '🟢'; }
                } else {
                    itemStatus = 'active';
                    itemIcon = '🟢';
                }
            }

            html += `<div class="curr-item ${itemStatus}">
                <span style="font-size:0.8em">${itemIcon}</span> ${item}
            </div>`;
        });

        html += `</div></div>`;
    });

    html += `</div>`;
    sidebar.innerHTML = html;
}

function renderTopbar() {
    const topbar = document.getElementById('topbar');
    if (!topbar) return;

    const user = State.getUser();
    if (!user) return;

    topbar.innerHTML = `
        <div class="topbar-left">
            <div class="logo-icon">AI</div>
            <div class="topbar-title">
                <h4>AI 윤리 교육 플랫폼</h4>
                <span>${user.name}님 환영합니다</span>
            </div>
        </div>
        <div class="topbar-right">
            ${user.isAdmin 
                ? '<button class="btn btn-secondary" onclick="window.location.href=\'intro.html\'">👥 사용자 모드</button>'
                : '<button class="btn btn-secondary" onclick="window.location.href=\'admin.html\'">⚙️ 관리자 페이지</button>'}
            <button class="btn btn-secondary" onclick="State.logout()">🚪 로그아웃</button>
        </div>
    `;
}

// Authentication Check on Page Load
function checkAuth() {
    const user = State.getUser();
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    
    if (!user && currentPage !== 'index.html') {
        window.location.href = 'index.html';
        return false;
    }
    
    // Redirect logged in user from index
    if (user && currentPage === 'index.html') {
        // Clear all session info when moving to login page
        localStorage.removeItem('ethos_user');
        localStorage.removeItem('ethos_stage');
        localStorage.removeItem('ethos_video_idx');
        localStorage.removeItem('ethos_sim_started');
        localStorage.removeItem('ethos_active_scenario');
        localStorage.removeItem('ethos_chat_history');
        return true; 
    }
    
    // Render Layout Parts
    renderSidebar();
    renderTopbar();
    return true;
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', checkAuth);

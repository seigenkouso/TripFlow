document.addEventListener("DOMContentLoaded", function() {
    checkLoginStatus();
});

let currentItineraryId = null; // 🌟 全局变量：记录当前正在看的行程ID

function checkLoginStatus() {
    fetch('/api/current_user')
        .then(res => res.json())
        .then(data => {
            const guestArea = document.getElementById('guest-area');
            const userArea = document.getElementById('user-area');
            if (data.is_logged_in) {
                if(guestArea) guestArea.style.display = 'none';
                if(userArea) { userArea.classList.remove('hidden'); userArea.style.display = 'flex'; }
                document.getElementById('welcome-msg').innerText = `你好, ${data.username}`;
            } else {
                if(guestArea) guestArea.style.display = 'flex';
                if(userArea) userArea.classList.add('hidden');
            }
        });
}

function showInput() {
    document.getElementById('input-section').classList.remove('hidden');
    document.getElementById('result-section').classList.add('hidden');
    document.getElementById('loading-section').classList.add('hidden');
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// --- 核心：生成行程 ---
function generateItinerary() {
    const city = document.getElementById('city').value;
    const days = document.getElementById('days').value;
    const preferences = Array.from(document.querySelectorAll('.tag.active')).map(tag => tag.innerText);

    if (!city) return alert("请填写目的地！");
    
    document.getElementById('input-section').classList.add('hidden');
    document.getElementById('loading-section').classList.remove('hidden');
    document.getElementById('result-section').classList.add('hidden');
    
    fetch('/api/generate', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ city, days, preferences })
    })
    .then(res => res.json())
    .then(data => {
        document.getElementById('loading-section').classList.add('hidden');
        if (data.success) {
            // 🌟 记录下后端返回的 ID
            currentItineraryId = data.id; 
            renderResult(data.data);
        } else {
            document.getElementById('input-section').classList.remove('hidden'); 
            alert("生成失败: " + data.error);
        }
    })
    .catch(e => {
        document.getElementById('loading-section').classList.add('hidden');
        document.getElementById('input-section').classList.remove('hidden');
        alert("网络请求错误");
    });
}

// --- 渲染结果 ---
function renderResult(data) {
    const resultSection = document.getElementById('result-section');
    resultSection.classList.remove('hidden');
    document.getElementById('result-title').innerText = data.title;
    const container = document.getElementById('timeline-container');
    container.innerHTML = ''; 
    
    if (!data.days) return;

    data.days.forEach((day, index) => {
        let spotsHtml = day.spots.map(spot => `
            <div class="timeline-item glass-effect">
                <div class="spot-header">
                    <span class="spot-name">${spot.name}</span>
                    <span class="spot-time">${spot.time}</span>
                </div>
                <div class="spot-reason">💡 ${spot.reason}</div>
                <p class="spot-desc">${spot.description}</p>
                <a href="https://uri.amap.com/search?keyword=${encodeURIComponent(spot.name)}" target="_blank" class="map-link">
                    <i class="fas fa-location-arrow"></i> 导航去这里
                </a>
            </div>
        `).join('');
        
        const dayHtml = `
            <div class="day-card">
                <div class="day-header-card">
                    <div class="day-header"><span class="day-badge">Day ${index + 1}</span><span class="day-title">${day.day_title}</span></div>
                </div>
                ${spotsHtml}
            </div>
        `;
        container.innerHTML += dayHtml;
    });
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// --- 🌟 收藏行程逻辑 ---
function addToSaved() {
    if (!currentItineraryId) return alert("请先生成行程！");
    
    fetch(`/api/bookmark/${currentItineraryId}`, { method: 'POST' })
    .then(res => res.json())
    .then(data => {
        if(data.success) {
            alert("❤️ 已添加到【我的保存】！\n您可以点击导航栏的“我的保存”查看。");
        } else {
            alert("收藏失败，请先登录或重试。");
        }
    });
}

// --- 侧边栏控制 ---
function closeSidebars() {
    document.getElementById('history-sidebar').classList.remove('open');
    document.getElementById('saved-sidebar').classList.remove('open');
    document.getElementById('overlay').classList.add('hidden');
}

// 历史记录侧边栏
function toggleHistory() {
    const sidebar = document.getElementById('history-sidebar');
    const overlay = document.getElementById('overlay');
    document.getElementById('saved-sidebar').classList.remove('open'); // 互斥关闭

    if (sidebar.classList.contains('open')) {
        closeSidebars();
    } else {
        sidebar.classList.add('open'); overlay.classList.remove('hidden');
        loadSidebarData('/api/history', 'history-list', '暂无历史记录');
    }
}

// 🌟 我的保存侧边栏
function toggleSaved() {
    const sidebar = document.getElementById('saved-sidebar');
    const overlay = document.getElementById('overlay');
    document.getElementById('history-sidebar').classList.remove('open'); // 互斥关闭

    if (sidebar.classList.contains('open')) {
        closeSidebars();
    } else {
        sidebar.classList.add('open'); overlay.classList.remove('hidden');
        loadSidebarData('/api/saved_list', 'saved-list', '暂无收藏的行程');
    }
}

// 通用加载数据函数
function loadSidebarData(apiEndpoint, containerId, emptyMsg) {
    const container = document.getElementById(containerId);
    container.innerHTML = '<p style="text-align:center; padding:20px; color:#666;">加载中...</p>';
    
    fetch(apiEndpoint).then(res => res.json()).then(data => {
        container.innerHTML = '';
        const list = data.history || data.saved || [];
        
        if (list.length === 0) {
            container.innerHTML = `<p style="text-align:center; padding:20px; color:#999;">${emptyMsg}</p>`;
            return;
        }
        list.forEach(item => {
            const div = document.createElement('div');
            div.className = 'history-card'; 
            div.innerHTML = `
                <div class="history-city">${item.city} · ${item.days}日游</div>
                <div class="history-date"><span>${item.date}</span><span style="color:var(--primary-color);">查看 ></span></div>
            `;
            div.onclick = () => { 
                closeSidebars();
                currentItineraryId = item.id; 
                document.getElementById('input-section').classList.add('hidden'); 
                renderResult(item.content); 
            };
            container.appendChild(div);
        });
    });
}

// --- 杂项 ---
function toggleTag(element) { element.classList.toggle('active'); }
function openAuth() { document.getElementById('auth-modal').classList.remove('hidden'); }
function closeAuthModal() { document.getElementById('auth-modal').classList.add('hidden'); }
function sendVerificationCode() {
    const email = document.getElementById('auth-email').value;
    const btn = document.getElementById('btn-send-code');
    if (!email || !email.includes('@')) return alert("请输入有效的邮箱");
    btn.disabled = true; let seconds = 60; btn.innerText = `${seconds}s后重试`;
    const timer = setInterval(() => { seconds--; btn.innerText = `${seconds}s后重试`; if(seconds<=0){clearInterval(timer);btn.disabled=false;btn.innerText="获取验证码";} }, 1000);
    fetch('/api/send-code', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({email}) })
    .then(res=>res.json()).then(data=>{ if(data.success)alert("验证码已发送"); else{alert(data.message);clearInterval(timer);btn.disabled=false;btn.innerText="获取验证码";} });
}
function handleEmailLogin() {
    const email = document.getElementById('auth-email').value;
    const code = document.getElementById('auth-code').value;
    if(!email||!code)return alert("请输入邮箱和验证码");
    fetch('/api/login-via-email', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({email, code}) })
    .then(res=>res.json()).then(data=>{ if(data.success){alert("登录成功！");closeAuthModal();checkLoginStatus();}else alert(data.message); });
}
function logout() { fetch('/api/logout').then(() => { location.reload(); }); }
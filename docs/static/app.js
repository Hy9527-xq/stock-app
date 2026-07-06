/**
 * 股票分析 — 前端共享工具
 */

// ---- Toast 提示 ----
function showToast(msg, duration = 2000) {
    const el = document.getElementById('toast');
    el.textContent = msg;
    el.classList.add('show');
    clearTimeout(el._timer);
    el._timer = setTimeout(() => el.classList.remove('show'), duration);
}

// ---- 状态提示 ----
function setStatus(el, msg, type) {
    if (typeof el === 'string') el = document.getElementById(el);
    if (!el) return;
    el.textContent = msg;
    el.className = 'status status-' + type;
}

// ---- 格式化日期 YYYYMMDD → YYYY-MM-DD ----
function fmtDate(d) {
    if (!d) return '';
    const s = String(d).replace(/-/g, '');
    if (s.length !== 8) return d;
    return s.slice(0,4) + '-' + s.slice(4,6) + '-' + s.slice(6,8);
}

// ---- 格式化日期显示 ----
function fmtDateDisplay(d) {
    if (!d) return '';
    const s = String(d).replace(/-/g, '');
    if (s.length !== 8) return d;
    return s.slice(0,4) + '.' + s.slice(4,6) + '.' + s.slice(6,8);
}

// ---- API 调用封装 ----
async function api(url, data) {
    try {
        const opts = {
            method: data ? 'POST' : 'GET',
            headers: { 'Content-Type': 'application/json' },
        };
        if (data) opts.body = JSON.stringify(data);
        const resp = await fetch(url, opts);
        return await resp.json();
    } catch (e) {
        return { success: false, message: '网络请求失败，请检查连接' };
    }
}

// ---- PWA 安装提示 ----
let deferredPrompt = null;

window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    const banner = document.getElementById('installBanner');
    if (banner) banner.style.display = 'flex';
});

document.addEventListener('DOMContentLoaded', () => {
    const installBtn = document.getElementById('installBtn');
    const dismissBtn = document.getElementById('dismissBtn');
    const banner = document.getElementById('installBanner');

    if (installBtn) {
        installBtn.addEventListener('click', async () => {
            if (!deferredPrompt) return;
            deferredPrompt.prompt();
            const { outcome } = await deferredPrompt.userChoice;
            if (outcome === 'accepted') banner.style.display = 'none';
            deferredPrompt = null;
        });
    }

    if (dismissBtn) {
        dismissBtn.addEventListener('click', () => {
            banner.style.display = 'none';
        });
    }

    // 如果已安装（standalone 模式），隐藏安装提示
    if (window.matchMedia('(display-mode: standalone)').matches) {
        if (banner) banner.style.display = 'none';
    }
});

const API = '/api';
let currentPage = 'search';
let trendChart = null;

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    setupNavigation();
    navigate('search');
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js');
    }
});

// 页面导航
function setupNavigation() {
    document.querySelectorAll('#bottom-nav button').forEach(btn => {
        btn.addEventListener('click', () => {
            const page = btn.dataset.page;
            navigate(page);
        });
    });
}

function navigate(page) {
    currentPage = page;
    document.querySelectorAll('#bottom-nav button').forEach(b => {
        b.classList.toggle('active', b.dataset.page === page);
    });
    switch (page) {
        case 'search': renderSearchPage(); break;
        case 'favorites': renderFavoritesPage(); break;
        case 'trend': renderTrendPage(); break;
    }
}

// ============ 搜索页 ============

function renderSearchPage() {
    const content = document.getElementById('content');
    content.innerHTML = `
        <div class="search-box">
            <input type="text" id="search-input" placeholder="输入商品名..."
                   autocomplete="off" autofocus>
            <button id="search-btn">搜索</button>
        </div>
        <div id="search-results"></div>
    `;

    document.getElementById('search-btn').addEventListener('click', doSearch);
    document.getElementById('search-input').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') doSearch();
    });
}

async function doSearch() {
    const input = document.getElementById('search-input');
    const query = input.value.trim();
    if (!query) return;

    const resultsDiv = document.getElementById('search-results');
    resultsDiv.innerHTML = '<div class="loading"><div class="spinner"></div><div>搜索中...</div></div>';

    try {
        const resp = await fetch(`${API}/search?q=${encodeURIComponent(query)}`);
        const data = await resp.json();
        renderSearchResults(data, resultsDiv);
    } catch (e) {
        resultsDiv.innerHTML = `<div class="empty-state"><p>连接失败，请确认服务已启动</p></div>`;
    }
}

function renderSearchResults(data, container) {
    if (!data.results || data.results.length === 0) {
        container.innerHTML = '<div class="empty-state"><div class="icon">📭</div><p>暂无结果</p></div>';
        return;
    }

    let html = '';
    data.results.forEach((r, i) => {
        if (r.status === 'ok') {
            html += renderPriceCard(r);
        } else if (r.status === 'captcha') {
            html += renderCaptchaCard(r);
        } else if (r.status === 'no_result') {
            html += renderNoResultCard(r);
        } else {
            html += renderErrorCard(r);
        }
    });
    container.innerHTML = html;
}

function renderPriceCard(r) {
    return `
        <div class="card price-card">
            <span class="platform-badge ${r.platform}">${r.platform}</span>
            <h3>${escapeHtml(r.product_name)}</h3>
            <p class="price">${r.price.toFixed(2)}</p>
            <p class="shop">${escapeHtml(r.shop || '')}</p>
            <div class="card-actions">
                ${r.url ? `<a href="${r.url}" target="_blank" rel="noopener" class="btn">去下单</a>` : ''}
                <button class="btn-secondary" onclick="addToFavorites('${escapeAttr(r.product_name)}', '${escapeAttr(r.platform)}')">收藏</button>
            </div>
        </div>
    `;
}

function renderCaptchaCard(r) {
    return `
        <div class="card captcha-card">
            <span class="platform-badge ${r.platform}">${r.platform}</span>
            <p class="message">⚠ ${r.message}</p>
            ${r.captcha_url ? `<a href="${r.captcha_url}" target="_blank" rel="noopener" class="btn">去网页完成验证</a>` : ''}
            <div class="manual-input">
                <input type="number" step="0.01" placeholder="输入价格" id="price-${escapeAttr(r.platform)}">
                <button class="btn" onclick="submitManualPrice('${escapeAttr(r.product_name || '')}', '${escapeAttr(r.platform)}')">确认</button>
            </div>
        </div>
    `;
}

function renderNoResultCard(r) {
    return `
        <div class="card captcha-card">
            <span class="platform-badge ${r.platform}">${r.platform}</span>
            <p class="message">未找到匹配商品</p>
            <div class="manual-input">
                <input type="number" step="0.01" placeholder="手动输入价格" id="price-${escapeAttr(r.platform)}">
                <button class="btn" onclick="submitManualPrice('', '${escapeAttr(r.platform)}')">确认</button>
            </div>
        </div>
    `;
}

function renderErrorCard(r) {
    return `
        <div class="card captcha-card">
            <span class="platform-badge ${r.platform}">${r.platform}</span>
            <p class="message">⚠ ${escapeHtml(r.message || '请求失败')}</p>
        </div>
    `;
}

async function submitManualPrice(productName, platform) {
    const input = document.getElementById(`price-${platform}`);
    const price = parseFloat(input.value);
    if (isNaN(price) || price <= 0) {
        alert('请输入有效的价格');
        return;
    }
    try {
        await fetch(`${API}/price/manual`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ product_name: productName, platform, price })
        });
        input.value = '';
        input.placeholder = '已记录 ✓';
    } catch (e) {
        alert('记录失败，请重试');
    }
}

// ============ 收藏页 ============

async function renderFavoritesPage() {
    const content = document.getElementById('content');
    content.innerHTML = '<div class="loading"><div class="spinner"></div></div>';

    try {
        const resp = await fetch(`${API}/favorites`);
        const favs = await resp.json();
        if (favs.length === 0) {
            content.innerHTML = '<div class="empty-state"><div class="icon">⭐</div><p>还没有收藏，去搜索页收藏商品吧</p></div>';
            return;
        }
        let html = '';
        favs.forEach(f => {
            html += `
                <div class="card fav-item">
                    <div class="info">
                        <span class="platform-badge ${f.platform}">${f.platform}</span>
                        <h3>${escapeHtml(f.name)}</h3>
                        <p class="fav-price">${f.latest_price ? '¥' + f.latest_price.toFixed(2) : '暂无价格'}</p>
                        <p class="fav-meta">${escapeHtml(f.spec || '')}</p>
                    </div>
                    <button class="remove-btn" onclick="removeFavorite(${f.fav_id})">删除</button>
                </div>
            `;
        });
        content.innerHTML = html;
    } catch (e) {
        content.innerHTML = '<div class="empty-state"><p>加载失败</p></div>';
    }
}

async function addToFavorites(productName, platform) {
    try {
        await fetch(`${API}/favorites/add`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ product_name: productName, platform })
        });
    } catch (e) {
        // 静默失败
    }
}

async function removeFavorite(favId) {
    try {
        await fetch(`${API}/favorites/${favId}`, { method: 'DELETE' });
        renderFavoritesPage();
    } catch (e) {
        alert('删除失败');
    }
}

// ============ 趋势页 ============

async function renderTrendPage() {
    const content = document.getElementById('content');
    content.innerHTML = '<div class="loading"><div class="spinner"></div></div>';

    try {
        const resp = await fetch(`${API}/products`);
        const products = await resp.json();
        if (products.length === 0) {
            content.innerHTML = '<div class="empty-state"><div class="icon">📈</div><p>还没有数据，先去搜索商品吧</p></div>';
            return;
        }
        content.innerHTML = `
            <div class="trend-selector">
                <select id="product-select">
                    <option value="">选择商品...</option>
                    ${products.map(p => `<option value="${escapeAttr(p)}">${escapeHtml(p)}</option>`).join('')}
                </select>
            </div>
            <div id="chart-area" class="chart-container" style="display:none">
                <canvas id="trend-canvas"></canvas>
            </div>
        `;

        document.getElementById('product-select').addEventListener('change', async (e) => {
            const product = e.target.value;
            if (!product) {
                document.getElementById('chart-area').style.display = 'none';
                return;
            }
            await loadTrendChart(product);
        });
    } catch (e) {
        content.innerHTML = '<div class="empty-state"><p>加载失败</p></div>';
    }
}

async function loadTrendChart(productName) {
    try {
        const resp = await fetch(`${API}/trend?product=${encodeURIComponent(productName)}`);
        const data = await resp.json();

        document.getElementById('chart-area').style.display = 'block';

        const colors = { '淘宝闪购': '#ff5000', '美团': '#ffc300', '京东': '#e2231a' };

        const datasets = data.datasets.map(ds => ({
            label: ds.platform,
            data: ds.prices,
            borderColor: colors[ds.platform] || '#667eea',
            backgroundColor: (colors[ds.platform] || '#667eea') + '20',
            tension: 0.3,
            fill: false,
            pointRadius: 4,
            pointHoverRadius: 6,
        }));

        if (trendChart) trendChart.destroy();

        const ctx = document.getElementById('trend-canvas').getContext('2d');
        trendChart = new Chart(ctx, {
            type: 'line',
            data: { labels: data.labels, datasets },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { usePointStyle: true, padding: 20 }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        title: { display: true, text: '价格 (¥)' }
                    }
                }
            }
        });
    } catch (e) {
        document.getElementById('chart-area').innerHTML = '<p style="text-align:center;padding:20px;">加载趋势失败</p>';
    }
}

// ============ 工具函数 ============

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function escapeAttr(str) {
    return str.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

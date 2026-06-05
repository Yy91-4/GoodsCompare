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

// ============ 工具函数 ============

function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function escapeAttr(str) {
    if (!str) return '';
    return str.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function showToast(msg) {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();
    const el = document.createElement('div');
    el.className = 'toast';
    el.textContent = msg;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 2000);
}

// ============ 页面导航 ============

function setupNavigation() {
    document.querySelectorAll('#bottom-nav button').forEach(btn => {
        btn.addEventListener('click', () => navigate(btn.dataset.page));
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

async function renderSearchPage() {
    const content = document.getElementById('content');
    content.innerHTML = `
        <div class="search-box">
            <input type="text" id="search-input" placeholder="输入商品名..."
                   autocomplete="off" autofocus>
            <button id="search-btn">搜索</button>
        </div>
        <div id="history-chips" class="history-chips"></div>
        <div id="search-results"></div>
    `;

    document.getElementById('search-btn').addEventListener('click', doSearch);
    document.getElementById('search-input').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') doSearch();
    });

    loadHistoryChips();
}

async function loadHistoryChips() {
    const container = document.getElementById('history-chips');
    try {
        const resp = await fetch(`${API}/history`);
        const history = await resp.json();
        if (history.length === 0) {
            container.style.display = 'none';
            return;
        }
        container.style.display = 'flex';
        container.innerHTML = history.slice(0, 6).map(h =>
            `<span class="history-chip" data-query="${escapeAttr(h.query)}">
                <span class="chip-icon">🕐</span>${escapeHtml(h.query)}
            </span>`
        ).join('');

        container.querySelectorAll('.history-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                document.getElementById('search-input').value = chip.dataset.query;
                doSearch();
            });
        });
    } catch (e) {
        container.style.display = 'none';
    }
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
        loadHistoryChips();
    } catch (e) {
        resultsDiv.innerHTML = '<div class="empty-state"><div class="icon">📡</div><p>连接失败，请确认服务已启动</p></div>';
    }
}

function renderSearchResults(data, container) {
    if (!data.results || data.results.length === 0) {
        container.innerHTML = '<div class="empty-state"><div class="icon">📭</div><p>暂无结果</p></div>';
        return;
    }

    // 找到最低价
    const minPrice = Math.min(
        ...data.results.filter(r => r.status === 'ok').map(r => r.price)
    );

    let html = '';
    data.results.forEach((r, i) => {
        if (r.status === 'ok') {
            html += renderPriceCard(r, r.price === minPrice);
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

function renderPriceCard(r, isBest) {
    return `
        <div class="card price-card${isBest ? ' best-price' : ''}">
            <span class="platform-badge ${r.platform}">${r.platform}</span>
            <h3>${escapeHtml(r.product_name)}</h3>
            <p class="price">${r.price.toFixed(2)}</p>
            <p class="shop">${escapeHtml(r.shop || '')}</p>
            <div class="card-actions">
                ${r.url ? `<a href="${r.url}" target="_blank" rel="noopener" class="btn">去下单</a>` : ''}
                <button class="btn-secondary" onclick="addToFavorites('${escapeAttr(r.product_name)}', '${escapeAttr(r.platform)}')">⭐ 收藏</button>
            </div>
        </div>
    `;
}

function renderCaptchaCard(r) {
    return `
        <div class="card captcha-card">
            <span class="platform-badge ${r.platform}">${r.platform}</span>
            <p class="message">⚠ ${escapeHtml(r.message)}</p>
            ${r.captcha_url ? `<a href="${r.captcha_url}" target="_blank" rel="noopener" class="btn" style="margin-bottom:8px;display:inline-block;">去网页完成验证</a>` : ''}
            <div class="manual-input">
                <input type="text" placeholder="商品名" value="${escapeAttr(r.product_name || '')}" id="name-${escapeAttr(r.platform)}">
                <input type="number" step="0.01" placeholder="价格" id="price-${escapeAttr(r.platform)}">
                <button class="btn" onclick="submitManualPrice('${escapeAttr(r.platform)}')">确认</button>
            </div>
        </div>
    `;
}

function renderNoResultCard(r) {
    return `
        <div class="card no-result-card">
            <span class="platform-badge ${r.platform}">${r.platform}</span>
            <p class="message">未找到匹配商品，可以手动录入价格</p>
            <div class="manual-input">
                <input type="text" placeholder="商品名" value="${escapeAttr(r.product_name || '')}" id="name-${escapeAttr(r.platform)}">
                <input type="number" step="0.01" placeholder="价格" id="price-${escapeAttr(r.platform)}">
                <button class="btn" onclick="submitManualPrice('${escapeAttr(r.platform)}')">确认</button>
            </div>
        </div>
    `;
}

function renderErrorCard(r) {
    return `
        <div class="card error-card">
            <span class="platform-badge ${r.platform}">${r.platform}</span>
            <p class="message">⚠ ${escapeHtml(r.message || '请求失败')}</p>
        </div>
    `;
}

async function submitManualPrice(platform) {
    const nameInput = document.getElementById(`name-${platform}`);
    const priceInput = document.getElementById(`price-${platform}`);
    const productName = nameInput ? nameInput.value.trim() : '';
    const price = parseFloat(priceInput.value);

    if (!productName) {
        showToast('请输入商品名');
        return;
    }
    if (isNaN(price) || price <= 0) {
        showToast('请输入有效的价格');
        return;
    }
    try {
        const resp = await fetch(`${API}/price/manual`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ product_name: productName, platform, price })
        });
        if (resp.ok) {
            priceInput.value = '';
            showToast('已记录 ✓');
        }
    } catch (e) {
        showToast('记录失败，请重试');
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
            content.innerHTML = '<div class="empty-state"><div class="icon">⭐</div><p>还没有收藏<br>去搜索页收藏商品吧</p></div>';
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
        showToast('已加入收藏 ★');
    } catch (e) {
        showToast('收藏失败');
    }
}

async function removeFavorite(favId) {
    try {
        await fetch(`${API}/favorites/${favId}`, { method: 'DELETE' });
        renderFavoritesPage();
        showToast('已删除');
    } catch (e) {
        showToast('删除失败');
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
            content.innerHTML = '<div class="empty-state"><div class="icon">📈</div><p>还没有数据<br>去搜索商品开始记录价格吧</p></div>';
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
                    },
                    x: {
                        ticks: { maxRotation: 45 }
                    }
                }
            }
        });
    } catch (e) {
        document.getElementById('chart-area').innerHTML = '<p style="text-align:center;padding:20px;color:#999;">加载趋势失败</p>';
    }
}

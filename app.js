const NEWS_DATA_URL = 'news_data.json';

document.addEventListener('DOMContentLoaded', function() {
    const navButtons = document.querySelectorAll('.nav-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    const filterChips = document.querySelectorAll('.chip');

    navButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetTab = this.getAttribute('data-tab');
            navButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(tab => tab.classList.remove('active'));
            this.classList.add('active');
            document.getElementById(targetTab).classList.add('active');
        });
    });

    filterChips.forEach(chip => {
        chip.addEventListener('click', function() {
            filterChips.forEach(c => c.classList.remove('active'));
            this.classList.add('active');
            const filter = this.getAttribute('data-filter');
            loadNews(filter);
        });
    });

    document.getElementById('btn-refresh').addEventListener('click', function() {
        loadNews('all');
    });

    const toggleNotifications = document.getElementById('toggle-notifications');
    const toggleHotNews = document.getElementById('toggle-hot-news');

    toggleNotifications.addEventListener('change', function() {
        if (this.checked) {
            requestNotificationPermission();
        }
        localStorage.setItem('notifications', this.checked);
    });

    toggleHotNews.addEventListener('change', function() {
        localStorage.setItem('hotNews', this.checked);
    });

    toggleNotifications.checked = localStorage.getItem('notifications') !== 'false';
    toggleHotNews.checked = localStorage.getItem('hotNews') !== 'false';

    if (toggleNotifications.checked) {
        requestNotificationPermission();
    }

    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('sw.js')
            .then(reg => console.log('Service Worker registrato'))
            .catch(err => console.log('Errore Service Worker:', err));
    }

    loadNews('all');
});

async function loadNews(filter = 'all') {
    try {
        console.log('Caricamento notizie da:', NEWS_DATA_URL);
        const response = await fetch(NEWS_DATA_URL + '?t=' + Date.now());
        
        if (!response.ok) {
            throw new Error('HTTP ' + response.status + ' - File non trovato');
        }
        
        const data = await response.json();
        console.log('Notizie caricate:', data.total_news);
        console.log('Ultimo aggiornamento:', data.last_update);
        
        displayNews(data.news, filter);
        
    } catch (error) {
        console.error('Errore caricamento:', error);
        showError(error.message);
    }
}

function displayNews(news, filter) {
    let filteredNews = news;
    
    if (filter !== 'all') {
        filteredNews = news.filter(n => n.categories.includes(filter));
    }
    
    const breakingNews = filteredNews.filter(n => n.is_high_priority).slice(0, 5);
    displayNewsList('breaking-news', breakingNews);
    
    const topNews = filteredNews.filter(n => !n.is_high_priority && n.is_ndrangheta).slice(0, 10);
    displayNewsList('top-news', topNews);
    
    const ndranghetaNews = filteredNews.filter(n => n.is_ndrangheta);
    displayNewsList('ndrangheta-news', ndranghetaNews);
    
    const mondoNews = filteredNews.filter(n => !n.is_ndrangheta).slice(0, 15);
    displayNewsList('mondo-news', mondoNews);
}

function displayNewsList(elementId, news) {
    const container = document.getElementById(elementId);
    
    if (!news || news.length === 0) {
        container.innerHTML = '<div class="news-card"><div class="news-title">Nessuna notizia disponibile</div></div>';
        return;
    }
    
    container.innerHTML = news.map(item => {
        const categoryIcon = getCategoryIcon(item.categories);
        const priorityBadge = item.is_high_priority ? '<span style="color:#ff4444;font-weight:bold;">🚨 </span>' : '';
        
        return `
        <div class="news-card" onclick="window.open('${item.link}', '_blank')">
            <div class="news-title">${priorityBadge}${categoryIcon} ${item.title}</div>
            <div class="news-summary">${item.summary || 'Clicca per leggere l\'articolo completo'}</div>
            <div class="news-meta">
                <span>📰 ${item.source}</span>
                <span>${formatDate(item.published)}</span>
            </div>
        </div>
    `}).join('');
}

function getCategoryIcon(categories) {
    if (categories.includes('arresti')) return '👮';
    if (categories.includes('scarcerazioni')) return '🔓';
    if (categories.includes('droga')) return '💊';
    if (categories.includes('sangue')) return '🔫';
    return '📰';
}

function formatDate(dateString) {
    if (!dateString) return '';
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('it-IT', { 
            day: '2-digit', 
            month: '2-digit', 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    } catch (e) {
        return '';
    }
}

function showError(message) {
    const containers = ['breaking-news', 'top-news', 'ndrangheta-news', 'mondo-news'];
    containers.forEach(id => {
        document.getElementById(id).innerHTML = `
            <div class="news-card">
                <div class="news-title">⚠️ Errore caricamento</div>
                <div class="news-summary">
                    <strong>Errore:</strong> ${message}<br><br>
                    <strong>Cosa fare:</strong><br>
                    1. Verifica che il file news_data.json esista<br>
                    2. Controlla la console del browser (F12)<br>
                    3. Prova a ricaricare la pagina
                </div>
            </div>
        `;
    });
}

function requestNotificationPermission() {
    if ('Notification' in window) {
        Notification.requestPermission().then(permission => {
            if (permission === 'granted') {
                console.log('Permessi notifiche concessi');
            }
        });
    }
}

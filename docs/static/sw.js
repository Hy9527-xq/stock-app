/**
 * Service Worker — PWA 离线缓存
 */
const CACHE_NAME = 'stock-app-v2';
// 只缓存静态资源，不缓存 HTML 页面（页面频繁更新）
const URLS_TO_CACHE = [
    '/static/style.css',
    '/static/app.js',
    '/static/manifest.json',
    '/static/icon-192.png',
    '/static/icon-512.png',
];

// 安装：预缓存静态资源
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(URLS_TO_CACHE);
        }).catch(() => {
            // 部分资源缺失不阻塞安装
        })
    );
    self.skipWaiting();
});

// 激活：清理旧缓存
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((names) => {
            return Promise.all(
                names.filter(n => n !== CACHE_NAME).map(n => caches.delete(n))
            );
        })
    );
    self.clients.claim();
});

// 请求拦截：HTML 走网络优先，静态资源走缓存优先
self.addEventListener('fetch', (event) => {
    // 跳过 API 请求（始终走网络）
    if (event.request.url.includes('/api/')) return;

    const isNavigation = event.request.mode === 'navigate';

    if (isNavigation) {
        // HTML 页面：网络优先，失败时回退缓存
        event.respondWith(
            fetch(event.request).then(response => {
                const clone = response.clone();
                caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
                return response;
            }).catch(() => caches.match(event.request))
        );
    } else {
        // 静态资源：缓存优先，失败时回退网络
        event.respondWith(
            caches.match(event.request).then(cached => {
                return cached || fetch(event.request).then(response => {
                    if (event.request.method === 'GET' && response.status === 200) {
                        const clone = response.clone();
                        caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
                    }
                    return response;
                });
            }).catch(() => caches.match(event.request))
        );
    }
});

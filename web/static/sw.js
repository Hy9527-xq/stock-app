/**
 * Service Worker — PWA 离线缓存
 */
const CACHE_NAME = 'stock-app-v1';
const URLS_TO_CACHE = [
    '/',
    '/recovery',
    '/records',
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

// 请求拦截：缓存优先，失败时回退网络
self.addEventListener('fetch', (event) => {
    // 跳过 API 请求（始终走网络）
    if (event.request.url.includes('/api/')) return;

    event.respondWith(
        caches.match(event.request).then((cached) => {
            return cached || fetch(event.request).then((response) => {
                // 缓存成功的 GET 请求
                if (event.request.method === 'GET' && response.status === 200) {
                    const clone = response.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(event.request, clone);
                    });
                }
                return response;
            });
        }).catch(() => {
            // 完全离线时返回缓存（如果有）
            return caches.match(event.request);
        })
    );
});

const CACHE_NAME = 'gr-cover-v7';
const ASSETS = [
  './',
  './index.html',
  './mask_data.js',
  './logo.jpeg',
  './logo-180.png',
  './logo-192.png',
  './logo-512.png',
  './manifest.json'
];

// 安装时缓存所有资源，并立即激活
self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(ASSETS))
      .then(() => self.skipWaiting())
  );
});

// 激活时清理旧缓存
self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

// 网络优先：有网时拿最新资源并更新缓存，离线时用缓存兜底
self.addEventListener('fetch', (e) => {
  e.respondWith(
    fetch(e.request)
      .then(response => {
        // 拿到新资源后更新缓存
        const clone = response.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(e.request, clone));
        return response;
      })
      .catch(() => caches.match(e.request))
  );
});

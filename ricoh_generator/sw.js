const CACHE_NAME = 'gr-cover-v1';
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

// 安装时缓存所有资源
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

// 请求时优先用缓存，没有再走网络
self.addEventListener('fetch', (e) => {
  e.respondWith(
    caches.match(e.request).then(cached => cached || fetch(e.request))
  );
});

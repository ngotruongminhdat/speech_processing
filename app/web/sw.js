// Service worker của Sách Nói: giữ vỏ ứng dụng và dữ liệu văn bản để mở được khi mất mạng.
// Chiến lược "mạng trước, bộ đệm sau": khi có mạng luôn lấy bản mới nhất, nên mỗi lần
// deploy thêm sách người dùng thấy ngay; khi mất mạng thì dùng bản đã lưu.
// Audio KHÔNG đi qua đây: sách lưu ngoại tuyến nằm trong IndexedDB (xem app.js).
const CACHE = 'sach-noi-v1';
const SHELL = ['./', 'index.html', 'app.css', 'app.js', 'manifest.webmanifest', 'catalog.json',
  'icons/icon.svg', 'icons/icon-192.png', 'icons/icon-512.png',
  'fonts/lora-400-normal-vietnamese.woff2', 'fonts/lora-400-normal-latin.woff2',
  'fonts/lora-400-italic-vietnamese.woff2', 'fonts/lora-400-italic-latin.woff2',
  'fonts/lora-600-normal-vietnamese.woff2', 'fonts/lora-600-normal-latin.woff2'];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE)
      .then((cache) => Promise.allSettled(SHELL.map((url) => cache.add(url))))
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  const url = new URL(req.url);
  if (req.method !== 'GET' || url.origin !== location.origin) return;
  if (req.headers.has('range') || /\.(mp3|zip)$/i.test(url.pathname)) return;
  // các trang của đồ án giữa kỳ nằm dưới build/ — để nguyên, không can thiệp
  const scope = new URL(self.registration.scope).pathname;
  if (url.pathname.startsWith(scope + 'build/')) return;

  event.respondWith(
    fetch(req)
      .then((res) => {
        if (res.ok) {
          const copy = res.clone();
          caches.open(CACHE).then((cache) => cache.put(req, copy));
        }
        return res;
      })
      .catch(async () => {
        const hit = await caches.match(req, { ignoreSearch: true });
        if (hit) return hit;
        if (req.mode === 'navigate') return (await caches.match('index.html')) || Response.error();
        return Response.error();
      }),
  );
});

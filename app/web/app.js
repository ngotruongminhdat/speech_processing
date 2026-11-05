// Sách Nói — thư viện sách nói DAISY cho người khiếm thị.
// Một trang duy nhất, ba màn hình theo địa chỉ sau dấu #:
//   #/                  thư viện
//   #/b/<slug>          trang bìa một cuốn
//   #/r/<slug>/<phần>   trang đọc
// Dữ liệu: catalog.json và books/<slug>/<NN>.json do pipeline/scripts/build_site.py sinh ra.

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const pad2 = (n) => String(n).padStart(2, '0');

// ---------- lưu trạng thái trên máy ----------
const store = {
  get(key, fallback = null) {
    try { const v = localStorage.getItem('sn:' + key); return v == null ? fallback : JSON.parse(v); }
    catch { return fallback; }
  },
  set(key, value) { try { localStorage.setItem('sn:' + key, JSON.stringify(value)); } catch { /* đầy bộ nhớ: bỏ qua */ } },
};

// IndexedDB chứa sách đã lưu để nghe ngoại tuyến (audio dạng Blob, phát qua object URL
// nên không phụ thuộc vào việc service worker xử lý yêu cầu Range).
const idb = {
  _db: null,
  open() {
    if (this._db) return this._db;
    this._db = new Promise((resolve, reject) => {
      const req = indexedDB.open('sach-noi', 1);
      req.onupgradeneeded = () => req.result.createObjectStore('units');
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
    return this._db;
  },
  async tx(mode, fn) {
    const db = await this.open();
    return new Promise((resolve, reject) => {
      const t = db.transaction('units', mode);
      const req = fn(t.objectStore('units'));
      t.oncomplete = () => resolve(req?.result);
      t.onerror = () => reject(t.error);
    });
  },
  get(key) { return this.tx('readonly', (s) => s.get(key)).catch(() => undefined); },
  put(key, value) { return this.tx('readwrite', (s) => s.put(value, key)); },
  del(key) { return this.tx('readwrite', (s) => s.delete(key)); },
};
const unitKey = (slug, no) => `${slug}:${no}`;

// ---------- tiện ích hiển thị ----------
function clock(sec) {
  sec = Math.max(0, Math.floor(sec || 0));
  const h = Math.floor(sec / 3600), m = Math.floor((sec % 3600) / 60), s = sec % 60;
  return h ? `${h}:${pad2(m)}:${pad2(s)}` : `${m}:${pad2(s)}`;
}
// Thời lượng đọc thành lời, dùng cho cả hiển thị lẫn trình đọc màn hình.
function spoken(sec) {
  const m = Math.round((sec || 0) / 60);
  if (m < 1) return 'dưới 1 phút';
  const h = Math.floor(m / 60), r = m % 60;
  return h ? (r ? `${h} giờ ${r} phút` : `${h} giờ`) : `${m} phút`;
}
const fold = (s) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/đ/g, 'd').replace(/Đ/g, 'D').toLowerCase();
// Màu bìa tự sinh: lấy theo thứ tự trên kệ để các cuốn cạnh nhau không trùng màu.
const HUES = [14, 205, 285, 40, 170, 335, 100, 240];
function hue(slug) { const i = catalog ? catalog.books.findIndex((b) => b.slug === slug) : 0; return HUES[(i < 0 ? 0 : i) % HUES.length]; }

let liveTimer;
function announce(msg) {
  const el = $('#live');
  el.textContent = '';
  clearTimeout(liveTimer);
  liveTimer = setTimeout(() => { el.textContent = msg; }, 60);
}

function cover(book) {
  const face = book.cover
    ? `<img src="${esc(book.cover)}" alt="">`
    : `<span class="gen"><span class="frame"><b>${esc(book.title)}</b><i>■</i><small>${esc(book.creator)}</small></span></span>`;
  return `<span class="book3d" style="--hue:${hue(book.slug)}" aria-hidden="true"><span class="vol"><span class="face">${face}</span><span class="pages"></span></span></span>`;
}

// ---------- tiến độ nghe ----------
const readyUnits = (book) => (book.units || []).filter((u) => u.ready !== false);
const getPos = (slug) => store.get('pos:' + slug);
function bookProgress(book) {
  const pos = getPos(book.slug);
  if (!pos || !book.duration) return 0;
  let before = 0;
  for (const u of book.units) { if (u.no === pos.unit) break; before += u.duration || 0; }
  return Math.min(1, (before + (pos.t || 0)) / book.duration);
}

// ================= THƯ VIỆN =================
let catalog = null;
const findBook = (slug) => catalog.books.find((b) => b.slug === slug);
const bookHref = (b) => (b.external ? b.external : `#/b/${b.slug}`);

function renderLibrary() {
  const books = catalog.books;
  const total = books.reduce((s, b) => s + (b.duration || 0), 0);
  $('#librarySummary').textContent = `${books.length} cuốn sách · tổng cộng ${spoken(total)} · chạm vào một cuốn để nghe.`;

  // "Nghe tiếp": cuốn nghe gần đây nhất còn dang dở
  const recent = books.filter((b) => !b.external && getPos(b.slug))
    .sort((a, b) => getPos(b.slug).at - getPos(a.slug).at)[0];
  const resume = $('#resume');
  if (recent && bookProgress(recent) < 0.995) {
    const pos = getPos(recent.slug);
    const left = recent.duration * (1 - bookProgress(recent));
    resume.hidden = false;
    resume.innerHTML = `<a class="btn resume" href="#/r/${recent.slug}/${pos.unit}"><span aria-hidden="true">▶</span> Nghe tiếp: ${esc(recent.title)} · còn ${spoken(left)}</a>`;
  } else { resume.hidden = true; }

  filterLibrary(false);
}

function filterLibrary(tell = true) {
  const q = fold($('#q').value.trim());
  const books = catalog.books.filter((b) => !q || fold(`${b.title} ${b.creator}`).includes(q));
  $('#bookList').innerHTML = books.map((b) => {
    const p = b.external ? 0 : bookProgress(b);
    const pct = Math.round(p * 100);
    const state = b.external ? 'bản giữa kỳ' : p >= 0.995 ? 'đã nghe xong' : pct > 0 ? `đã nghe ${pct} phần trăm` : '';
    const parts = (b.units?.length || b.unitCount || 1);
    const sub = `${spoken(b.duration)}${parts > 1 ? ` · ${parts} phần` : ''}`;
    const label = [b.title, b.creator, sub.replace(' · ', ', '), state].filter(Boolean).join(', ');
    return `<li><a href="${esc(bookHref(b))}" aria-label="${esc(label)}">
      ${cover(b)}
      <span class="cap" aria-hidden="true"><b>${esc(b.title)}</b><i>${esc(b.creator)}</i><small>${esc(sub)}</small>
      ${pct > 0 ? `<span class="bar"><span style="width:${pct}%"></span></span>` : ''}
      ${b.external ? '<span class="badge">Bản giữa kỳ</span>' : ''}</span></a></li>`;
  }).join('');
  $('#noResult').hidden = books.length > 0;
  if (tell) announce(books.length ? `${books.length} cuốn khớp.` : 'Không tìm thấy sách nào khớp.');
}

// ================= TRANG BÌA =================
async function renderBook(book) {
  const units = book.units;
  const ready = readyUnits(book);
  const pos = getPos(book.slug);
  const seen = new Set(store.get('seen:' + book.slug, []));
  const startUnit = pos && ready.some((u) => u.no === pos.unit) ? pos.unit : ready[0]?.no;
  const started = pos && bookProgress(book) > 0.002 && bookProgress(book) < 0.995;

  const bg = $('#bookBg');
  bg.style.setProperty('--hue', hue(book.slug));
  bg.classList.toggle('img', !!book.cover);
  if (book.cover) bg.style.setProperty('--cover', `url('${book.cover}')`);

  const metas = [
    ['Tác giả', esc(book.creator)],
    ['Năm sáng tác', esc(book.date)],
    ['Thể loại', esc(book.subject)],
    ['Ngôn ngữ', 'Tiếng Việt'],
    ['Giọng đọc', esc(book.narrator)],
    ['Định dạng', 'Sách nói DAISY 3 (Audio MP3)'],
    ['Thời lượng', `${clock(book.duration)} <span class="sr-only">(${spoken(book.duration)})</span>`],
    ['Nguồn văn bản', book.sourceURL ? `<a href="${esc(book.sourceURL)}" rel="noopener">Wikisource tiếng Việt</a>` : ''],
    ['Bản quyền', esc(book.note)],
  ].filter(([, v]) => v);

  $('#bookHero').innerHTML = `
    ${cover(book)}
    <div class="lede">
      <p class="kicker">Sách nói DAISY · ${esc(book.subject)}</p>
      <h1 id="h-book" tabindex="-1">${esc(book.title)}</h1>
      <p class="author">${esc(book.creator)}</p>
      <div class="divider" aria-hidden="true"><i>■</i></div>
      <p class="desc">${esc(book.description)}</p>
      <dl class="metas">${metas.map(([k, v]) => `<div><dt>${k}</dt><dd>${v}</dd></div>`).join('')}</dl>
      <div class="cta">
        ${startUnit != null ? `<a class="btn primary" href="#/r/${book.slug}/${startUnit}"><span aria-hidden="true">▶</span> ${started ? 'Nghe tiếp' : 'Bắt đầu nghe'}</a>` : '<span class="btn ghost">Đang chuẩn bị audio</span>'}
        ${units.length > 1 ? '<a class="btn ghost" href="#muc-luc" id="tocJump">Mục lục</a>' : ''}
        <button class="btn ghost" id="saveBtn" type="button"></button>
        ${book.daisy ? `<a class="btn ghost" href="${esc(book.daisy)}" download><span aria-hidden="true">⬇</span> Tải DAISY · ${book.daisySize}</a>` : ''}
      </div>
    </div>`;

  $('#bookToc').innerHTML = units.length > 1 ? `
    <div class="toc-head" id="muc-luc">
      <h2>Mục lục</h2>
      <span class="toc-note"><b>${ready.length}</b>/${units.length} phần đã có audio</span>
    </div>
    <div class="toc-card"><ol>${units.map((u) => {
      const row = `<em>${pad2(u.no)}</em><span class="t">${esc(u.title)}</span><span class="dots"></span><b>${u.ready === false ? 'đang chuẩn bị' : clock(u.duration)}</b>`;
      return u.ready === false
        ? `<li class="todo">${row}</li>`
        : `<li class="${seen.has(u.no) ? 'seen' : ''}"><a href="#/r/${book.slug}/${u.no}" aria-label="Phần ${u.no}: ${esc(u.title)}, ${spoken(u.duration)}${seen.has(u.no) ? ', đã nghe' : ''}">${row}</a></li>`;
    }).join('')}</ol></div>` : '';
  $('#bookToc').hidden = units.length <= 1;

  $('#bookFoot').innerHTML = `<span class="mark" aria-hidden="true">◆</span><br>
    ${esc(book.title)} · ${esc(book.creator)}<br>Sách dựng theo chuẩn DAISY 3 · giọng đọc tổng hợp`;

  $('#tocJump')?.addEventListener('click', (e) => { e.preventDefault(); $('#muc-luc').scrollIntoView({ behavior: 'smooth' }); });
  await refreshSaveBtn(book);
}

async function isSaved(book) {
  const ready = readyUnits(book);
  if (!ready.length) return false;
  for (const u of ready) if (!(await idb.get(unitKey(book.slug, u.no)))) return false;
  return true;
}
async function refreshSaveBtn(book) {
  const btn = $('#saveBtn');
  if (!btn) return;
  const saved = await isSaved(book);
  btn.disabled = false;
  btn.innerHTML = saved ? '<span aria-hidden="true">✓</span> Đã lưu trên máy · Xoá' : '<span aria-hidden="true">⤓</span> Lưu để nghe ngoại tuyến';
  btn.onclick = async () => {
    const ready = readyUnits(book);
    if (saved) {
      for (const u of ready) await idb.del(unitKey(book.slug, u.no));
      announce('Đã xoá bản lưu trên máy.');
      return refreshSaveBtn(book);
    }
    btn.disabled = true;
    try {
      await navigator.storage?.persist?.();
      for (let i = 0; i < ready.length; i++) {
        btn.textContent = `Đang lưu ${i + 1}/${ready.length}…`;
        const u = ready[i];
        const [data, blob] = await Promise.all([
          fetch(u.data).then((r) => { if (!r.ok) throw new Error(r.status); return r.json(); }),
          fetch(u.audio).then((r) => { if (!r.ok) throw new Error(r.status); return r.blob(); }),
        ]);
        await idb.put(unitKey(book.slug, u.no), { data, blob });
      }
      announce(`Đã lưu ${book.title} để nghe ngoại tuyến.`);
    } catch {
      announce('Không lưu được. Hãy kiểm tra kết nối mạng và thử lại.');
    }
    refreshSaveBtn(book);
  };
}

// ================= TRANG ĐỌC =================
const audio = $('#audio');
const R = { book: null, unit: null, sents: [], cur: -1, objectUrl: null, token: 0, userScrollAt: 0, pendingSeek: null };

async function openReader(book, unitNo) {
  const token = ++R.token;
  const unit = book.units.find((u) => u.no === unitNo);
  const status = $('#readerStatus');
  audio.pause();
  $('#text').innerHTML = '';
  status.hidden = true;
  R.book = book; R.unit = unit; R.sents = []; R.cur = -1;

  // tiêu đề, mục lục, nút quay lại
  const many = book.units.length > 1;
  $('#readerKicker').textContent = many ? unit.label : book.subject;
  $('#h-reader').textContent = unit.title;
  $('#readerByline').textContent = many ? `${book.title} · ${book.creator}` : book.creator;
  $('#playerTitle').textContent = many ? `${unit.label}: ${unit.title}` : unit.title;
  $('#coverBtn').href = `#/b/${book.slug}`;
  $('#tocBrand').href = `#/b/${book.slug}`;
  $('#tocBrand b').textContent = book.title;
  $('#tocBrand i').textContent = book.creator;
  $('#toc').hidden = !many;
  $('#tocList').innerHTML = many ? book.units.map((u) => u.ready === false
    ? `<li class="todo"><span class="row"><em>${pad2(u.no)}</em>${esc(u.title)}</span></li>`
    : `<li><a href="#/r/${book.slug}/${u.no}" ${u.no === unitNo ? 'aria-current="page"' : ''}><em>${pad2(u.no)}</em>${esc(u.title)}</a></li>`).join('') : '';
  const dl = $('#dl');
  dl.hidden = !book.daisy;
  if (book.daisy) { dl.href = book.daisy; dl.setAttribute('aria-label', `Tải bản DAISY của ${book.title}`); }

  if (!unit || unit.ready === false) {
    status.hidden = false; status.textContent = 'Phần này đang được chuẩn bị audio.';
    return;
  }

  // dữ liệu: ưu tiên bản đã lưu trên máy
  let data, src;
  const saved = await idb.get(unitKey(book.slug, unitNo));
  if (token !== R.token) return;
  if (R.objectUrl) { URL.revokeObjectURL(R.objectUrl); R.objectUrl = null; }
  if (saved) {
    data = saved.data; R.objectUrl = URL.createObjectURL(saved.blob); src = R.objectUrl;
  } else {
    try {
      const res = await fetch(unit.data);
      if (!res.ok) throw new Error(res.status);
      data = await res.json(); src = unit.audio;
    } catch {
      if (token !== R.token) return;
      status.hidden = false;
      status.textContent = 'Không tải được nội dung. Hãy kiểm tra kết nối mạng, hoặc lưu sách để nghe ngoại tuyến.';
      announce(status.textContent);
      return;
    }
  }
  if (token !== R.token) return;

  renderText(data);
  audio.src = src;
  audio.playbackRate = Number(store.get('rate', 1));
  $('#speed').value = String(audio.playbackRate);

  // tiếp tục từ vị trí cũ nếu đang nghe dở chính phần này
  const pos = getPos(book.slug);
  R.pendingSeek = pos && pos.unit === unitNo && pos.t > 2 && pos.t < unit.duration - 3 ? pos.t : null;
  setMediaSession();
  if (store.get('autoplay', '1') === '1') {
    audio.play().catch(() => announce('Nhấn nút Phát để bắt đầu nghe.'));
  }
}

function renderText(data) {
  const box = $('#text');
  const frag = document.createDocumentFragment();
  let firstPara = true;
  data.paras.forEach((p, pi) => {
    if (pi === 0 && p.t === 'h1') {             // tiêu đề phần: đã hiển thị ở đầu trang
      p.s.forEach(([b, e]) => R.sents.push({ b, e, el: $('#h-reader'), para: null }));
      return;
    }
    const el = document.createElement(p.t === 'h1' ? 'h2' : 'p');
    el.className = 'seg' + (p.t === 'note' ? ' footnote' : '');
    if (p.t === 'p' && firstPara) { el.classList.add('dropcap'); firstPara = false; }
    p.s.forEach(([b, e, text], si) => {
      const span = document.createElement('span');
      span.className = 's';
      span.dataset.i = R.sents.length;
      span.textContent = text;
      R.sents.push({ b, e, el: span, para: el });
      el.append(span);
      if (si < p.s.length - 1) el.append(' ');
    });
    frag.append(el);
  });
  box.append(frag);
}

function sentAt(t) {            // câu cuối cùng có mốc bắt đầu <= t
  const s = R.sents;
  let lo = 0, hi = s.length - 1, ans = 0;
  while (lo <= hi) { const mid = (lo + hi) >> 1; if (s[mid].b <= t + 0.02) { ans = mid; lo = mid + 1; } else hi = mid - 1; }
  return ans;
}

function highlight(i) {
  if (i === R.cur || !R.sents[i]) return;
  const prev = R.sents[R.cur];
  if (prev) { prev.el.classList.remove('on'); prev.el.removeAttribute('aria-current'); prev.para?.classList.remove('cur'); }
  const s = R.sents[i];
  R.cur = i;
  if (s.el.classList.contains('s')) { s.el.classList.add('on'); s.el.setAttribute('aria-current', 'true'); }
  s.para?.classList.add('cur');
  // tự cuộn theo câu đang đọc, trừ khi người dùng vừa tự cuộn
  if (Date.now() - R.userScrollAt > 4000 && !audio.paused) {
    const r = s.el.getBoundingClientRect();
    const dock = $('.player-card').getBoundingClientRect().top;
    if (r.top < 80 || r.bottom > dock - 40) {
      const smooth = !matchMedia('(prefers-reduced-motion: reduce)').matches;
      s.el.scrollIntoView({ block: 'center', behavior: smooth ? 'smooth' : 'auto' });
    }
  }
}

function seekSent(i, play = true) {
  if (!R.sents.length) return;
  i = Math.max(0, Math.min(R.sents.length - 1, i));
  audio.currentTime = R.sents[i].b + 0.001;
  R.userScrollAt = 0;
  highlight(i);
  if (play) audio.play().catch(() => {});
}
function stepSent(dir) {
  if (!R.sents.length) return;
  const i = sentAt(audio.currentTime);
  // lùi: nếu đã nghe hơn 1,5 giây của câu thì quay về đầu chính câu đó
  if (dir < 0 && audio.currentTime - R.sents[i].b > 1.5) return seekSent(i, !audio.paused);
  seekSent(i + dir, !audio.paused);
}
function gotoUnit(dir) {
  if (!R.book) return;
  const ready = readyUnits(R.book);
  const idx = ready.findIndex((u) => u.no === R.unit?.no);
  const target = ready[idx + dir];
  if (target) location.hash = `#/r/${R.book.slug}/${target.no}`;
  else announce(dir > 0 ? 'Đây là phần cuối.' : 'Đây là phần đầu.');
}

function savePos() {
  if (!R.book || !R.unit || !audio.duration) return;
  store.set('pos:' + R.book.slug, { unit: R.unit.no, t: Math.round(audio.currentTime * 10) / 10, at: Date.now() });
}

function tick() {
  const t = audio.currentTime, d = audio.duration || R.unit?.duration || 0;
  if (R.sents.length) highlight(sentAt(t));
  $('#tCur').textContent = clock(t);
  $('#tDur').textContent = clock(d);
  const scrub = $('#scrub');
  if (!scrub.matches(':active')) scrub.value = d ? Math.round((t / d) * 1000) : 0;
  scrub.setAttribute('aria-valuetext', `${spoken(t)} trên ${spoken(d)}`);
  $('#progress').style.width = d ? `${(t / d) * 100}%` : '0';
}
let raf;
function loop() { tick(); if (!audio.paused) raf = requestAnimationFrame(loop); }

function setPlayUi(playing) {
  $('#playIcon').textContent = playing ? '⏸' : '▶';
  $('#play').setAttribute('aria-label', playing ? 'Tạm dừng' : 'Phát');
  if ('mediaSession' in navigator) navigator.mediaSession.playbackState = playing ? 'playing' : 'paused';
}

audio.addEventListener('loadedmetadata', () => {
  if (R.pendingSeek != null) {
    audio.currentTime = R.pendingSeek;
    announce(`Nghe tiếp từ ${spoken(R.pendingSeek)}.`);
    R.pendingSeek = null;
  }
  tick();
});
audio.addEventListener('play', () => { setPlayUi(true); cancelAnimationFrame(raf); loop(); });
audio.addEventListener('pause', () => { setPlayUi(false); savePos(); tick(); });
audio.addEventListener('timeupdate', () => { tick(); if (Math.floor(audio.currentTime) % 3 === 0) savePos(); });
audio.addEventListener('seeked', tick);
audio.addEventListener('error', () => {
  if (!audio.getAttribute('src')) return;
  $('#readerStatus').hidden = false;
  $('#readerStatus').textContent = 'Không phát được audio. Hãy kiểm tra kết nối mạng.';
  announce($('#readerStatus').textContent);
});
audio.addEventListener('ended', () => {
  const book = R.book, unit = R.unit;
  const seen = new Set(store.get('seen:' + book.slug, [])); seen.add(unit.no);
  store.set('seen:' + book.slug, [...seen]);
  const ready = readyUnits(book);
  const next = ready[ready.findIndex((u) => u.no === unit.no) + 1];
  if (next) {
    store.set('pos:' + book.slug, { unit: next.no, t: 0, at: Date.now() });
    location.hash = `#/r/${book.slug}/${next.no}`;
  } else {
    store.set('pos:' + book.slug, { unit: unit.no, t: unit.duration, at: Date.now() });
    announce(`Đã nghe hết ${book.title}.`);
  }
});

// ---------- điều khiển ----------
$('#play').addEventListener('click', () => (audio.paused ? audio.play().catch(() => {}) : audio.pause()));
$('#prev').addEventListener('click', () => stepSent(-1));
$('#next').addEventListener('click', () => stepSent(1));
$('#scrub').addEventListener('input', (e) => {
  const d = audio.duration || 0;
  if (d) { audio.currentTime = (e.target.value / 1000) * d; R.userScrollAt = 0; tick(); }
});
$('#speed').addEventListener('change', (e) => setRate(Number(e.target.value)));
function setRate(rate) {
  audio.playbackRate = rate;
  $('#speed').value = String(rate);
  store.set('rate', rate);
  announce(`Tốc độ ${String(rate).replace('.', ' phẩy ')} lần.`);
}
function nudgeRate(dir) {
  const opts = $$('#speed option').map((o) => Number(o.value));
  const i = Math.max(0, Math.min(opts.length - 1, opts.indexOf(audio.playbackRate) + dir));
  setRate(opts[i]);
}
$('#text').addEventListener('click', (e) => {
  const span = e.target.closest('.s');
  if (span) seekSent(Number(span.dataset.i));
});
$('#h-reader').addEventListener('click', () => { if (R.sents.length) seekSent(0); });
for (const ev of ['wheel', 'touchmove']) addEventListener(ev, () => { R.userScrollAt = Date.now(); }, { passive: true });

addEventListener('keydown', (e) => {
  if (document.body.dataset.view !== 'reader' || $('#settings').open) return;
  if (e.target.matches('input, select, textarea') || e.ctrlKey || e.metaKey || e.altKey) return;
  const act = {
    ' ': () => (audio.paused ? audio.play().catch(() => {}) : audio.pause()),
    k: () => (audio.paused ? audio.play().catch(() => {}) : audio.pause()),
    ArrowRight: () => (e.shiftKey ? gotoUnit(1) : stepSent(1)),
    ArrowLeft: () => (e.shiftKey ? gotoUnit(-1) : stepSent(-1)),
    ArrowUp: () => nudgeRate(1),
    ArrowDown: () => nudgeRate(-1),
    ']': () => gotoUnit(1),
    '[': () => gotoUnit(-1),
  }[e.key];
  // phím cách trên một nút/liên kết đang được focus phải giữ hành vi mặc định
  if (!act || (e.key === ' ' && e.target.matches('button, a, summary'))) return;
  e.preventDefault();
  act();
});

// Điều khiển ở màn hình khoá và trên tai nghe: quan trọng với người không nhìn màn hình.
function setMediaSession() {
  if (!('mediaSession' in navigator) || !R.book) return;
  const many = R.book.units.length > 1;
  navigator.mediaSession.metadata = new MediaMetadata({
    title: many ? `${R.unit.label}: ${R.unit.title}` : R.book.title,
    artist: R.book.creator,
    album: R.book.title,
    artwork: [{ src: new URL('icons/icon-512.png', location.href).href, sizes: '512x512', type: 'image/png' }],
  });
  const set = (name, fn) => { try { navigator.mediaSession.setActionHandler(name, fn); } catch { /* không hỗ trợ */ } };
  set('play', () => audio.play());
  set('pause', () => audio.pause());
  set('previoustrack', () => stepSent(-1));
  set('nexttrack', () => stepSent(1));
  set('seekbackward', (d) => { audio.currentTime = Math.max(0, audio.currentTime - (d.seekOffset || 10)); });
  set('seekforward', (d) => { audio.currentTime = Math.min(audio.duration || 0, audio.currentTime + (d.seekOffset || 10)); });
  set('seekto', (d) => { if (d.seekTime != null) audio.currentTime = d.seekTime; });
}

// ---------- cài đặt đọc ----------
const prefs = {
  size: { el: '#optSize', def: '1', apply: (v) => document.documentElement.style.setProperty('--rsize', v) },
  theme: {
    el: '#optTheme', def: matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'paper',
    apply: (v) => { const c = document.documentElement.classList; c.remove('theme-paper', 'theme-dark', 'theme-contrast'); c.add('theme-' + v); },
  },
  legible: { el: '#optLeg', def: '0', apply: (v) => document.body.classList.toggle('legible', v === '1') },
  autoplay: { el: '#optAuto', def: '1', apply: () => {} },
};
for (const [key, p] of Object.entries(prefs)) {
  const setPref = (v, tell) => {
    store.set(key, v);
    p.apply(v);
    $$(`${p.el} button`).forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.v === v)));
    if (tell) announce(`Đã chọn ${$(`${p.el} button[data-v="${v}"]`).textContent.trim()}.`);
  };
  setPref(String(store.get(key, p.def)), false);
  $(p.el).addEventListener('click', (e) => { const b = e.target.closest('button'); if (b) setPref(b.dataset.v, true); });
}

let sleepTimer, sleepEnd = 0, sleepTick;
function setSleep(min, tell = true) {
  clearTimeout(sleepTimer); clearInterval(sleepTick);
  sleepEnd = min ? Date.now() + min * 60000 : 0;
  $$('#optSleep button').forEach((b) => b.setAttribute('aria-pressed', String(Number(b.dataset.v) === min)));
  const info = $('#sleepInfo');
  const show = () => { info.textContent = sleepEnd ? `Tự dừng sau ${Math.max(1, Math.ceil((sleepEnd - Date.now()) / 60000))} phút nữa.` : ''; };
  show();
  if (min) {
    sleepTick = setInterval(show, 30000);
    sleepTimer = setTimeout(() => { audio.pause(); setSleep(0, false); announce('Đã hết giờ hẹn, tạm dừng.'); }, min * 60000);
  }
  if (tell) announce(min ? `Sẽ tự dừng sau ${min} phút.` : 'Đã tắt hẹn giờ.');
}
setSleep(0, false);
$('#optSleep').addEventListener('click', (e) => { const b = e.target.closest('button'); if (b) setSleep(Number(b.dataset.v)); });
$('#openSettings').addEventListener('click', () => $('#settings').showModal());
$('#settings').addEventListener('click', (e) => { if (e.target === e.currentTarget) e.currentTarget.close(); });  // chạm ra ngoài để đóng

// ================= ĐỊNH TUYẾN =================
function show(view, title, heading) {
  for (const v of ['library', 'book', 'reader']) $(`#view-${v}`).hidden = v !== view;
  document.body.dataset.view = view;
  document.title = title;
  window.scrollTo(0, 0);
  // đưa focus vào tiêu đề để trình đọc màn hình đọc tên màn hình mới
  requestAnimationFrame(() => heading?.focus({ preventScroll: true }));
}

async function route() {
  const [, kind, slug, unitStr] = (location.hash || '#/').split('/');
  const book = slug ? findBook(decodeURIComponent(slug)) : null;
  if (kind !== 'r') { savePos(); audio.pause(); R.token++; }

  if (kind === 'b' && book && !book.external) {
    await renderBook(book);
    return show('book', `${book.title} — ${book.creator} · Sách Nói`, $('#h-book'));
  }
  if (kind === 'r' && book && !book.external) {
    const no = Number(unitStr) || readyUnits(book)[0]?.no;
    show('reader', `${book.title} · Sách Nói`, $('#h-reader'));
    return openReader(book, no);
  }
  renderLibrary();
  show('library', 'Sách Nói — Thư viện sách nói tiếng Việt', $('#h-library'));
}

$('#q').addEventListener('input', () => filterLibrary());
$('#skip').addEventListener('click', (e) => {
  e.preventDefault();
  const h = $(`#view-${document.body.dataset.view} h1`);
  h?.focus(); h?.scrollIntoView();
});
addEventListener('hashchange', route);
addEventListener('pagehide', savePos);
document.addEventListener('visibilitychange', () => { if (document.hidden) savePos(); });

(async function start() {
  try {
    const res = await fetch('catalog.json', { cache: 'no-cache' });
    if (!res.ok) throw new Error(res.status);
    catalog = await res.json();
  } catch {
    $('#librarySummary').textContent = 'Không tải được danh mục sách. Hãy kiểm tra kết nối mạng rồi tải lại trang.';
    return;
  }
  await route();
  if ('serviceWorker' in navigator && location.protocol.startsWith('http')) {
    navigator.serviceWorker.register('sw.js').catch(() => {});
  }
})();

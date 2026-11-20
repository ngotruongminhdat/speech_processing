// Sách Nói — thư viện sách nói DAISY cho người khiếm thị.
// Một trang duy nhất, ba màn hình theo địa chỉ sau dấu #:
//   #/                  thư viện
//   #/b/<slug>          trang bìa một cuốn
//   #/r/<slug>/<phần>   trang đọc (thêm /s<số câu> để mở đúng một câu, dùng cho dấu trang)
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
const unitKey = (slug, no, vid) => `${slug}:${no}:${vid}`;

// ---------- giọng đọc ----------
// Mỗi phần có thể có nhiều bản audio. Thư viện có một hay nhiều giọng chính (catalog
// voices không có cờ fallback); người nghe chọn một giọng cho cả thư viện; phần nào
// chưa có giọng đó thì tạm dùng giọng khác đang có (giọng dự phòng).
const VOICE_ORDER = ['hm', 'nu', 'nam', 'piper'];
const DEFAULT_VOICE = 'hm';
const allVoices = () => {
  const seen = new Map();
  for (const b of catalog?.books || []) for (const v of b.voices || []) if (!seen.has(v.id)) seen.set(v.id, v);
  return [...seen.values()];
};
const isPrimary = (v) => !v.fallback && v.id !== 'piper';
const primaryVoices = () => allVoices().filter(isPrimary);
// giọng đã chọn; nếu thư viện không còn giọng đó (đổi bộ giọng) thì về giọng chính đầu tiên
function prefVoice() {
  const v = String(store.get('voice', DEFAULT_VOICE));
  const prim = primaryVoices();
  return !prim.length || prim.some((p) => p.id === v) ? v : prim[0].id;
}
function voiceOf(unit, want = prefVoice()) {
  const v = unit?.voices || {};
  if (v[want]) return want;
  return VOICE_ORDER.find((k) => v[k]) ?? Object.keys(v)[0] ?? null;
}
const voiceInfo = (book, id) => (book?.voices || []).find((v) => v.id === id)
  || allVoices().find((v) => v.id === id) || { id, label: 'Giọng đọc', name: '' };
const voiceText = (v) => `${v.label.toLowerCase()} ${v.name}`.trim();
const voiceTitle = (v) => `${v.label} ${v.name}`.trim();
const pickable = (book) => (book.voices || []).filter(isPrimary);
// giọng thực tế của cả cuốn: giọng đang chọn nếu cuốn này có, không thì giọng đầu tiên có
function bookVoice(book) {
  const ids = (book.voices || []).map((v) => v.id);
  return ids.includes(prefVoice()) ? prefVoice() : VOICE_ORDER.find((k) => ids.includes(k)) ?? ids[0] ?? null;
}
const unitDuration = (u, vid = voiceOf(u)) => u.voices?.[vid]?.duration ?? u.duration ?? 0;

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
let toastTimer;
function toast(msg) {
  const el = $('#toast');
  el.textContent = msg;
  // popover nằm ở lớp trên cùng nên hiện được cả khi hộp Cài đặt đang mở
  el.classList.add('show');
  try { if (el.matches(':popover-open')) el.hidePopover(); el.showPopover(); } catch { /* trình duyệt cũ: vẫn hiện nhờ lớp show */ }
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { try { el.hidePopover(); } catch { /* không hỗ trợ popover */ } el.classList.remove('show'); }, 4500);
}
// ---------- ứng dụng tự đọc lời nhắc (chế độ chạm đơn giản) ----------
// Dùng giọng tiếng Việt có sẵn trên máy (Web Speech API). Trong lúc đọc lời nhắc thì vặn nhỏ
// tiếng sách. Máy không có giọng tiếng Việt thì trả về false để dùng vùng thông báo như thường.
const spokenLog = (window.snSpoken = []);      // để kiểm thử xem đã đọc câu nào
let synthVoices = [];
function loadVoices() { try { synthVoices = speechSynthesis.getVoices() || []; } catch { synthVoices = []; } }
if ('speechSynthesis' in window) { loadVoices(); speechSynthesis.addEventListener?.('voiceschanged', loadVoices); }
function speak(msg) {
  spokenLog.push(msg);
  if (!('speechSynthesis' in window) || !window.SpeechSynthesisUtterance) return false;
  const vi = synthVoices.find((v) => /^vi/i.test(v.lang));
  if (synthVoices.length && !vi) return false;
  try {
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(msg);
    u.lang = 'vi-VN';
    if (vi) u.voice = vi;
    const restore = () => { if (!speechSynthesis.speaking) audio.volume = 1; };
    u.onstart = () => { audio.volume = 0.25; };
    u.onend = restore; u.onerror = restore;
    speechSynthesis.speak(u);
    return true;
  } catch { return false; }
}
const simpleOn = () => store.get('simple', '0') === '1';

function announce(msg, visible = true) {
  if (simpleOn() && speak(msg)) return;
  const el = $('#live');
  el.textContent = '';
  clearTimeout(liveTimer);
  liveTimer = setTimeout(() => { el.textContent = msg; }, 60);
  if (visible) toast(msg);
}

// ---------- tiếng báo hiệu ----------
// Tiếng ngắn cho người không nhìn màn hình: hết phần, tới giới hạn, đánh dấu, hết giờ hẹn.
const CUES = {
  limit: [[196, 0, 0.09], [196, 0.13, 0.09]],          // hai tiếng trầm: không đi tiếp được
  end: [[660, 0, 0.12], [494, 0.14, 0.18]],            // đi xuống: hết phần
  done: [[523, 0, 0.12], [659, 0.13, 0.12], [784, 0.26, 0.22]],   // đi lên: hết sách
  mark: [[880, 0, 0.08]],                              // một tiếng cao: đã đánh dấu
  undo: [[494, 0, 0.08], [660, 0.1, 0.1]],
  sleep: [[440, 0, 0.25]],
};
let cueCtx = null;
const cueLog = (window.snCues = []);      // để kiểm thử xem tiếng nào đã phát
function cue(kind) {
  if (store.get('cue', '1') !== '1' || !CUES[kind]) return;
  cueLog.push(kind);
  try {
    cueCtx = cueCtx || new (window.AudioContext || window.webkitAudioContext)();
    if (cueCtx.state === 'suspended') cueCtx.resume();
    const t0 = cueCtx.currentTime + 0.02;
    for (const [freq, at, len] of CUES[kind]) {
      const osc = cueCtx.createOscillator(), gain = cueCtx.createGain();
      osc.type = 'sine'; osc.frequency.value = freq;
      gain.gain.setValueAtTime(0.0001, t0 + at);
      gain.gain.exponentialRampToValueAtTime(0.22, t0 + at + 0.015);
      gain.gain.exponentialRampToValueAtTime(0.0001, t0 + at + len);
      osc.connect(gain).connect(cueCtx.destination);
      osc.start(t0 + at); osc.stop(t0 + at + len + 0.02);
    }
  } catch { /* không có Web Audio: bỏ qua */ }
}

function cover(book) {
  const face = book.cover
    ? `<img src="${esc(book.cover)}" alt="" loading="lazy" decoding="async">`
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

  // thể loại có trong thư viện, xếp theo số cuốn; giữ lựa chọn đang có
  const count = new Map();
  for (const b of books) if (b.subject) count.set(b.subject, (count.get(b.subject) || 0) + 1);
  const sel = $('#genre');
  const cur = sel.value;
  sel.innerHTML = '<option value="">Tất cả thể loại</option>' + [...count].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0], 'vi'))
    .map(([s, n]) => `<option value="${esc(s)}">${esc(s)} (${n} cuốn)</option>`).join('');
  sel.value = count.has(cur) ? cur : '';

  filterLibrary(false);
}

function filterLibrary(tell = true) {
  const q = fold($('#q').value.trim());
  const g = $('#genre').value;
  const books = catalog.books.filter((b) => (!g || b.subject === g)
    && (!q || fold(`${b.title} ${b.creator} ${b.subject || ''}`).includes(q)));
  $('#bookList').innerHTML = books.map((b) => {
    const p = b.external ? 0 : bookProgress(b);
    const pct = Math.round(p * 100);
    const state = b.external ? 'bản giữa kỳ' : p >= 0.995 ? 'đã nghe xong' : pct > 0 ? `đã nghe ${pct} phần trăm` : '';
    const parts = (b.units?.length || b.unitCount || 1);
    const sub = `${spoken(b.duration)}${parts > 1 ? ` · ${parts} phần` : ''}`;
    const label = [b.title, b.creator, b.subject, sub.replace(' · ', ', '), state].filter(Boolean).join(', ');
    return `<li><a href="${esc(bookHref(b))}" aria-label="${esc(label)}">
      ${cover(b)}
      <span class="cap" aria-hidden="true"><b>${esc(b.title)}</b><i>${esc(b.creator)}</i><small>${esc([b.subject, sub].filter(Boolean).join(' · '))}</small>
      ${pct > 0 ? `<span class="bar"><span style="width:${pct}%"></span></span>` : ''}
      ${b.external ? '<span class="badge">Bản giữa kỳ</span>' : ''}</span></a></li>`;
  }).join('');
  $('#noResult').hidden = books.length > 0;
  if (tell) announce(books.length ? `${books.length} cuốn khớp.` : 'Không tìm thấy sách nào khớp.', false);
  return books.length;
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

  const bv = bookVoice(book);
  const daisy = book.daisy?.[bv];
  const voices = pickable(book);
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
    ['Ảnh bìa', book.coverCredit ? `<a href="${esc(book.coverCredit.url)}" rel="noopener">${esc(book.coverCredit.text)}</a>, qua Wikimedia Commons` : ''],
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
        ${daisy ? `<a class="btn ghost" href="${esc(daisy.url)}" download aria-label="Tải bản DAISY, ${esc(voiceText(voiceInfo(book, bv)))}, ${esc(daisy.size)}"><span aria-hidden="true">⬇</span> Tải DAISY · ${daisy.size}</a>` : ''}
      </div>
      ${voices.length > 1 ? `<div class="voice-pick" role="group" aria-labelledby="l-bvoice">
        <span id="l-bvoice">Giọng đọc</span>
        ${voices.map((v) => `<button type="button" data-v="${esc(v.id)}" aria-pressed="${v.id === bv}">${esc(v.label)} · ${esc(v.name)}</button>`).join('')}
      </div>` : (bv && voiceInfo(book, bv).fallback && primaryVoices().length
        ? `<p class="voice-note">${esc(voiceTitle(primaryVoices()[0]))} đang được chuẩn bị cho cuốn này. Hiện phát ${esc(voiceText(voiceInfo(book, bv)))}.</p>`
        : '')}
    </div>`;

  $('#bookToc').innerHTML = units.length > 1 ? `
    <div class="toc-head" id="muc-luc">
      <h2 id="h-toc" tabindex="-1">Mục lục</h2>
      <span class="toc-note"><b>${ready.length}</b>/${units.length} phần đã có audio</span>
    </div>
    <div class="toc-card"><ol>${units.map((u) => {
      const row = `<em>${pad2(u.no)}</em><span class="t">${esc(u.title)}</span><span class="dots"></span><b>${u.ready === false ? 'đang chuẩn bị' : clock(u.duration)}</b>`;
      return u.ready === false
        ? `<li class="todo">${row}</li>`
        : `<li class="${seen.has(u.no) ? 'seen' : ''}"><a href="#/r/${book.slug}/${u.no}" aria-label="Phần ${u.no}: ${esc(u.title)}, ${spoken(u.duration)}${seen.has(u.no) ? ', đã nghe' : ''}">${row}</a></li>`;
    }).join('')}</ol></div>` : '';
  $('#bookToc').hidden = units.length <= 1;

  await renderMarks(book);
  renderFind(book);

  $('#bookFoot').innerHTML = `<span class="mark" aria-hidden="true">◆</span><br>
    ${esc(book.title)} · ${esc(book.creator)}<br>Sách dựng theo chuẩn DAISY 3 · giọng đọc tổng hợp`;

  $('.voice-pick')?.addEventListener('click', (e) => { const b = e.target.closest('button'); if (b) setVoice(b.dataset.v); });
  // cuộn tới mục lục và đưa focus vào đó, để trình đọc màn hình cũng nhảy theo
  $('#tocJump')?.addEventListener('click', (e) => { e.preventDefault(); $('#muc-luc').scrollIntoView(); $('#h-toc').focus({ preventScroll: true }); });
  await refreshSaveBtn(book);
}

async function isSaved(book) {
  const ready = readyUnits(book);
  if (!ready.length) return false;
  for (const u of ready) if (!(await idb.get(unitKey(book.slug, u.no, voiceOf(u))))) return false;
  return true;
}
async function refreshSaveBtn(book) {
  const btn = $('#saveBtn');
  if (!btn) return;
  const saved = await isSaved(book);
  btn.removeAttribute('aria-disabled');
  btn.innerHTML = saved ? '<span aria-hidden="true">✓</span> Đã lưu trên máy · Xoá' : '<span aria-hidden="true">⤓</span> Lưu để nghe ngoại tuyến';
  btn.onclick = async () => {
    if (btn.getAttribute('aria-disabled') === 'true') return announce('Đang lưu, xin chờ.');
    const ready = readyUnits(book);
    if (saved) {
      for (const u of ready) await idb.del(unitKey(book.slug, u.no, voiceOf(u)));
      announce('Đã xoá bản lưu trên máy.');
      return refreshSaveBtn(book);
    }
    // aria-disabled thay cho disabled: nút vẫn giữ focus nên trình đọc màn hình không bị lạc chỗ
    btn.setAttribute('aria-disabled', 'true');
    announce(`Đang lưu ${book.title}, ${ready.length > 1 ? ready.length + ' phần, ' : ''}xin chờ.`);
    try {
      await navigator.storage?.persist?.();
      let told = 0;
      for (let i = 0; i < ready.length; i++) {
        btn.textContent = `Đang lưu ${i + 1}/${ready.length}…`;
        const q = Math.floor((i / ready.length) * 4);          // báo tiến độ ở mỗi một phần tư
        if (q > told) { told = q; announce(`Đã lưu ${i} trên ${ready.length} phần.`, false); }
        const u = ready[i], vid = voiceOf(u), src = u.voices[vid];
        const [data, blob] = await Promise.all([
          fetch(src.data).then((r) => { if (!r.ok) throw new Error(r.status); return r.json(); }),
          fetch(src.audio).then((r) => { if (!r.ok) throw new Error(r.status); return r.blob(); }),
        ]);
        await idb.put(unitKey(book.slug, u.no, vid), { data, blob });
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
// ---------- tìm trong sách ----------
// Tìm một từ hoặc một câu trong văn bản của cả cuốn, không phân biệt dấu và hoa thường.
// Văn bản từng phần lấy từ bản đã lưu trên máy nếu có, không thì tải file dữ liệu của phần đó.
const FIND_MAX = 50;
const unitText = new Map();
let findState = { slug: '', q: '' }, findToken = 0;
async function loadUnitText(book, u) {
  const vid = voiceOf(u), key = unitKey(book.slug, u.no, vid);
  if (unitText.has(key)) return unitText.get(key);
  let data = (await idb.get(key).catch(() => null))?.data;
  if (!data) {
    const res = await fetch(u.voices[vid].data);
    if (!res.ok) throw new Error(res.status);
    data = await res.json();
  }
  const sents = [];       // cùng thứ tự với R.sents của trang đọc
  for (const p of data.paras) for (const [b, , text] of p.s) sents.push({ b, text, f: fold(text) });
  unitText.set(key, sents);
  return sents;
}
function findSnippet(s, at, len) {
  const marked = s.f.length === s.text.length;      // vị trí sau khi bỏ dấu còn khớp với câu gốc
  const from = s.text.length > 170 && at > 70 ? s.text.indexOf(' ', at - 60) + 1 : 0;
  const cut = s.text.slice(from, from + 170);
  const tail = from + 170 < s.text.length ? '…' : '';
  const a = at - from;
  const body = marked && a >= 0 && a + len <= cut.length
    ? `${esc(cut.slice(0, a))}<mark>${esc(cut.slice(a, a + len))}</mark>${esc(cut.slice(a + len))}` : esc(cut);
  return (from ? '…' : '') + body + tail;
}
async function runFind(book, q, tell = true) {
  const info = $('#findInfo'), list = $('#findList');
  const needle = fold(q.trim()).replace(/\s+/g, ' ');
  const token = ++findToken;
  findState = { slug: book.slug, q };
  list.innerHTML = '';
  const say = (msg) => { info.textContent = msg; if (tell) announce(msg, false); };
  if (needle.length < 2) return say(needle ? 'Hãy gõ ít nhất hai chữ cái.' : '');
  info.textContent = 'Đang tìm…';
  const slow = setTimeout(() => { if (tell && token === findToken) announce('Đang tìm trong sách, xin chờ.', false); }, 1500);
  const units = readyUnits(book);
  const texts = await Promise.all(units.map((u) => loadUnitText(book, u).catch(() => null)));
  clearTimeout(slow);
  if (token !== findToken || !$('#findList')) return;
  const hits = [];
  let total = 0;
  texts.forEach((sents, k) => (sents || []).forEach((s, i) => {
    const at = s.f.indexOf(needle);
    if (at < 0) return;
    total++;
    if (hits.length < FIND_MAX) hits.push({ u: units[k], i, s, at });
  }));
  const failed = texts.filter((t) => !t).length;
  const miss = failed ? ` Có ${failed} phần không tải được nên chưa tìm trong đó.` : '';
  list.innerHTML = hits.map(({ u, i, s, at }) => `
    <li><a href="#/r/${book.slug}/${u.no}/s${i}"><b>${esc(`${units.length > 1 ? unitName(book, u) + ', ' : ''}${spoken(s.b)}`)}</b><span>${findSnippet(s, at, needle.length)}</span></a></li>`).join('');
  say(total ? `Tìm thấy ${total} câu có “${q.trim()}”${total > FIND_MAX ? `, hiện ${FIND_MAX} câu đầu` : ''}. Chọn một câu để nghe từ đó.${miss}`
    : `Không tìm thấy “${q.trim()}” trong cuốn này.${miss}`);
}
function renderFind(book) {
  let box = $('#bookFind');
  if (!box) { box = document.createElement('section'); box.id = 'bookFind'; box.className = 'wrap'; $('#bookToc').after(box); }
  const q = findState.slug === book.slug ? findState.q : '';
  box.innerHTML = `
    <div class="toc-head"><h2 id="h-find" tabindex="-1">Tìm trong sách</h2></div>
    <div class="toc-card">
      <form class="find-form" id="findForm" role="search">
        <label for="findQ">Từ hoặc câu cần tìm trong cuốn này, không cần gõ dấu</label>
        <div class="find-row">
          <input id="findQ" type="search" autocomplete="off" enterkeyhint="search" value="${esc(q)}">
          <button type="submit">Tìm</button>
        </div>
      </form>
      <p class="find-info" id="findInfo"></p>
      <ul class="marks" id="findList"></ul>
    </div>`;
  $('#findForm').addEventListener('submit', (e) => { e.preventDefault(); runFind(book, $('#findQ').value); });
  if (q) runFind(book, q, false);      // quay lại từ một kết quả: vẫn còn danh sách để chọn câu khác
}

// ---------- dấu trang ----------
// Tên một phần để đọc lên. Nhãn của phần có khi chính là tên sách (Tắt đèn: "Chương 3"), khi đó chỉ đọc tiêu đề.
const unitName = (book, u) => (u.label && u.label !== book.title && u.label !== u.title ? `${u.label}: ${u.title}` : u.title);
const getMarks = (slug) => store.get('marks:' + slug, []);
const markTitle = (book, m) => {
  const u = book.units.find((x) => x.no === m.unit);
  return `${book.units.length > 1 && u ? unitName(book, u) + ', ' : ''}${spoken(m.t)}`;
};
const noteKey = (slug, m) => `note:${slug}:${m.unit}:${m.s}`;
const canRecord = () => !!(navigator.mediaDevices?.getUserMedia && window.MediaRecorder);
const NOTE_MAX = 60;                 // giây
let noteRec = null, notePlayer = null;
async function renderMarks(book) {
  let box = $('#bookMarks');
  if (!box) { box = document.createElement('section'); box.id = 'bookMarks'; $('#bookToc').before(box); }
  const marks = getMarks(book.slug);
  const has = await Promise.all(marks.map((m) => idb.get(noteKey(book.slug, m)).then((n) => !!n)));
  box.className = 'wrap';
  box.hidden = !marks.length;
  box.innerHTML = marks.length ? `
    <div class="toc-head"><h2 id="h-marks" tabindex="-1">Dấu trang</h2><span class="toc-note"><b>${marks.length}</b> chỗ đã đánh dấu</span></div>
    <div class="toc-card"><ul class="marks">${marks.map((m, i) => {
      const t = esc(markTitle(book, m));
      return `
      <li><a href="#/r/${book.slug}/${m.unit}/s${m.s}" aria-label="${t}${has[i] ? ', có ghi chú bằng giọng nói' : ''}: ${esc(m.text)}"><b>${t}${has[i] ? ' · có ghi chú' : ''}</b><span>${esc(m.text)}</span></a>
      ${has[i] ? `<button type="button" data-act="play" data-i="${i}" aria-label="Nghe ghi chú của dấu trang ${t}">Nghe ghi chú</button>` : ''}
      ${canRecord() ? `<button type="button" data-act="rec" data-i="${i}" aria-pressed="false" aria-label="${has[i] ? 'Ghi âm lại ghi chú' : 'Ghi âm ghi chú'} cho dấu trang ${t}">${has[i] ? 'Ghi âm lại' : 'Ghi âm ghi chú'}</button>` : ''}
      <button type="button" data-act="del" data-i="${i}" aria-label="Xoá dấu trang ${t}">Xoá</button></li>`;
    }).join('')}</ul></div>` : '';
  box.onclick = async (e) => {
    const b = e.target.closest('button[data-act]');
    if (!b) return;
    const i = Number(b.dataset.i), m = getMarks(book.slug)[i];
    if (!m) return;
    const key = noteKey(book.slug, m);
    if (b.dataset.act === 'del') {
      store.set('marks:' + book.slug, getMarks(book.slug).filter((_, k) => k !== i));
      await idb.del(key).catch(() => {});
      await renderMarks(book);
      announce('Đã xoá dấu trang.');
      (getMarks(book.slug).length ? $('#h-marks') : $('#h-book'))?.focus();
    } else if (b.dataset.act === 'play') {
      if (notePlayer) { notePlayer.pause(); notePlayer = null; b.textContent = 'Nghe ghi chú'; return; }
      const n = await idb.get(key);
      if (!n) return;
      const url = URL.createObjectURL(n.blob);
      notePlayer = new Audio(url);
      const stop = () => { URL.revokeObjectURL(url); notePlayer = null; if (b.isConnected) b.textContent = 'Nghe ghi chú'; };
      notePlayer.onended = stop; notePlayer.onerror = stop;
      b.textContent = 'Dừng nghe';
      notePlayer.play().catch(stop);
    } else if (b.dataset.act === 'rec') {
      if (noteRec) { noteRec.stop(); return; }
      let stream;
      try { stream = await navigator.mediaDevices.getUserMedia({ audio: true }); }
      catch { announce('Chưa được phép dùng micro. Hãy cho phép trong cài đặt trình duyệt rồi thử lại.'); return; }
      const chunks = [];
      const rec = new MediaRecorder(stream);
      const timer = setTimeout(() => rec.state === 'recording' && rec.stop(), NOTE_MAX * 1000);
      rec.ondataavailable = (ev) => { if (ev.data.size) chunks.push(ev.data); };
      rec.onstop = async () => {
        clearTimeout(timer);
        stream.getTracks().forEach((t) => t.stop());
        noteRec = null;
        const blob = new Blob(chunks, { type: rec.mimeType || 'audio/webm' });
        if (!blob.size) { announce('Không ghi được âm thanh. Hãy thử lại.'); return renderMarks(book); }
        await idb.put(key, { blob, at: Date.now() });
        await renderMarks(book);
        announce('Đã lưu ghi chú bằng giọng nói.');
        $(`#bookMarks button[data-act="play"][data-i="${i}"]`)?.focus();
      };
      noteRec = rec;
      rec.start();
      b.setAttribute('aria-pressed', 'true');
      b.textContent = 'Dừng ghi âm';
      announce(`Đang ghi âm, tối đa ${NOTE_MAX} giây. Nhấn nút lần nữa để dừng.`);
    }
  };
}
function markIndex() {
  if (!R.book || !R.unit || !R.sents.length) return -1;
  const i = sentAt(audio.currentTime);
  return getMarks(R.book.slug).findIndex((m) => m.unit === R.unit.no && m.s === i);
}
function refreshMarkBtn() {
  const on = markIndex() >= 0;
  const b = $('#mark');
  if (b.getAttribute('aria-pressed') !== String(on)) b.setAttribute('aria-pressed', String(on));
}
function toggleMark() {
  if (!R.book || !R.unit || !R.sents.length || !R.ready) return;
  const marks = getMarks(R.book.slug);
  const at = markIndex();
  if (at >= 0) {
    idb.del(noteKey(R.book.slug, marks[at])).catch(() => {});
    marks.splice(at, 1);
    announce('Đã bỏ dấu trang ở câu này.');
  } else {
    const i = sentAt(audio.currentTime);
    const m = { unit: R.unit.no, s: i, t: Math.round(R.sents[i].b), text: sentText(i).slice(0, 140), at: Date.now() };
    marks.push(m);
    cue('mark');
    marks.sort((a, b) => a.unit - b.unit || a.s - b.s);
    announce(`Đã đánh dấu: ${markTitle(R.book, m)}. ${simpleOn() ? 'Nút bên trái đưa bạn tới các dấu trang.' : 'Xem các dấu trang ở trang bìa.'}`);
  }
  store.set('marks:' + R.book.slug, marks);
  refreshMarkBtn();
}

// Trả lời câu hỏi "đang ở đâu": sách, phần, thời điểm, tốc độ, hẹn giờ.
function whereAmI(extra = '') {
  if (!R.book || !R.unit) return;
  const many = R.book.units.length > 1;
  const ready = readyUnits(R.book);
  const d = audio.duration || unitDuration(R.unit, R.voice) || 0;
  const parts = [
    many ? `${R.book.title}, ${unitName(R.book, R.unit)}, phần ${ready.findIndex((u) => u.no === R.unit.no) + 1} trên ${ready.length}` : `${R.book.title} của ${R.book.creator}`,
    `${audio.paused ? 'Đang tạm dừng ở' : 'Đang nghe tới'} ${spoken(audio.currentTime)} trên ${spoken(d)}, còn ${spoken(Math.max(0, d - audio.currentTime))}`,
    `Tốc độ ${String(audio.playbackRate).replace('.', ' phẩy ')} lần`,
  ];
  if (sleepAtEnd) parts.push('Sẽ tự dừng khi hết phần này');
  else if (sleepEnd) parts.push(`Sẽ tự dừng sau ${Math.max(1, Math.ceil((sleepEnd - Date.now()) / 60000))} phút nữa`);
  announce(parts.join('. ') + '.' + (typeof extra === 'string' ? extra : ''));
}

const R = { book: null, unit: null, voice: null, sents: [], cur: -1, objectUrl: null, token: 0, userScrollAt: 0, pendingSeek: null, quietSeek: false,
  ready: false,     // audio của đúng phần và giọng đang mở đã nạp xong; trước đó đồng hồ audio chưa có nghĩa
  keep: null, srcToken: 0 };

// keep: { sent, play } khi đổi giọng giữa chừng — giữ nguyên câu đang nghe và trạng thái phát
async function openReader(book, unitNo, keep = null) {
  // Ghi vị trí của phần đang nghe trước khi chuyển. Từ đây tới khi audio mới nạp xong thì không ghi nữa:
  // lúc đó đồng hồ vẫn là của audio cũ, ghi vào sẽ gắn nhầm thời điểm cũ cho phần hoặc giọng mới
  // (phần sau bị nhảy tới giữa chừng, đổi giọng rồi mở lại thì lạc chỗ).
  if (!audio.ended) savePos();
  R.ready = false; R.keep = keep; R.pausedAt = 0;
  const token = ++R.token;
  const unit = book.units.find((u) => u.no === unitNo);
  const vid = voiceOf(unit);
  const status = $('#readerStatus');
  audio.pause();
  $('#text').innerHTML = '';
  status.hidden = true;
  if (R.undo && R.undo.slug !== book.slug) { R.undo = null; $('#undo').setAttribute('aria-disabled', 'true'); }
  R.book = book; R.unit = unit; R.voice = vid; R.sents = []; R.cur = -1;

  // tiêu đề, mục lục, nút quay lại
  const many = book.units.length > 1;
  $('#readerKicker').textContent = many ? unit.label : book.subject;
  $('#h-reader').textContent = unit.title;
  $('#readerByline').textContent = (many ? `${book.title} · ${book.creator}` : book.creator)
    + (vid ? ` · ${voiceText(voiceInfo(book, vid))}` : '');
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
  const daisy = book.daisy?.[vid] || book.daisy?.[bookVoice(book)];
  dl.hidden = !daisy;
  if (daisy) { dl.href = daisy.url; dl.setAttribute('aria-label', `Tải bản DAISY của ${book.title}`); }

  if (!unit || unit.ready === false) {
    status.hidden = false; status.textContent = 'Phần này đang được chuẩn bị audio.';
    return;
  }

  // dữ liệu: ưu tiên bản đã lưu trên máy
  let data, src;
  const saved = await idb.get(unitKey(book.slug, unitNo, vid));
  if (token !== R.token) return;
  if (R.objectUrl) { URL.revokeObjectURL(R.objectUrl); R.objectUrl = null; }
  if (saved) {
    data = saved.data; R.objectUrl = URL.createObjectURL(saved.blob); src = R.objectUrl;
  } else {
    try {
      const res = await fetch(unit.voices[vid].data);
      if (!res.ok) throw new Error(res.status);
      data = await res.json(); src = unit.voices[vid].audio;
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
  audio.src = src; R.srcToken = token;
  // tốc độ nhớ riêng từng cuốn; cuốn chưa chỉnh lần nào thì theo tốc độ dùng gần nhất
  audio.playbackRate = Number(store.get('rate:' + book.slug, store.get('rate', 1)));
  $('#speed').value = String(audio.playbackRate);

  // người nghe chọn một giọng mà phần này chưa có: nói rõ đang phát giọng nào
  const want = prefVoice();
  const notice = !keep && vid !== want
    ? `${pickable(book).some((v) => v.id === want) ? 'Phần' : 'Cuốn'} này chưa có ${voiceText(voiceInfo(book, want))}, đang phát ${voiceText(voiceInfo(book, vid))}.`
    : '';
  refreshVoiceNote();

  // tiếp tục từ vị trí cũ nếu đang nghe dở chính phần này. Mốc thời gian của mỗi
  // giọng khác nhau, nên khi vị trí được lưu ở giọng khác thì quay về đầu câu đã lưu.
  const pos = getPos(book.slug);
  const dur = unitDuration(unit, vid);
  R.pendingSeek = null; R.quietSeek = false;
  if (keep) {
    const i = Math.max(0, Math.min(R.sents.length - 1, keep.sent));
    R.pendingSeek = R.sents[i]?.b ?? 0; R.quietSeek = true;
  } else if (pos && pos.unit === unitNo) {
    const t = (pos.v ?? vid) === vid ? pos.t : (R.sents[pos.s]?.b ?? 0);
    if (t > 2 && t < dur - 3) R.pendingSeek = rewindPoint(t);
  }
  // nếu sắp có câu "Nghe tiếp từ…" thì gộp ghi chú về giọng vào đó, để câu sau không đè mất câu trước
  R.seekNote = '';
  if (notice && R.pendingSeek != null && !R.quietSeek) R.seekNote = notice + ' ';
  else if (notice) announce(notice);
  setMediaSession();
  refreshMarkBtn();
  renderSimple();
  const force = R.forcePlay; R.forcePlay = false;
  const held = R.holdNext; R.holdNext = false;
  if (held) announce('Đã hết phần, tạm dừng theo hẹn giờ. Nhấn Phát để nghe phần tiếp theo.');
  else if (keep ? keep.play : (force || store.get('autoplay', '1') === '1')) {
    // Chỉ nhắc nhấn Phát khi trình duyệt chặn tự phát. Lệnh phát bị ngắt vì người nghe đã rời
    // trang đọc hoặc đã mở phần khác (AbortError) thì không nói gì, kẻo đè lên thông báo đang hiện.
    audio.play().catch((e) => {
      if (e?.name === 'NotAllowedError' && token === R.token) announce(`${notice ? notice + ' ' : ''}Nhấn nút Phát để bắt đầu nghe.`);
    });
  }
}

// Nút chọn giọng trong hộp Cài đặt, theo các giọng chính có trong danh mục.
function renderVoiceOptions() {
  const prim = primaryVoices();
  const want = prefVoice();
  $('#optVoice').innerHTML = prim.map((v) =>
    `<button type="button" data-v="${esc(v.id)}" aria-pressed="${v.id === want}">${esc(voiceTitle(v))}</button>`).join('');
  $('#l-voice').hidden = $('#optVoice').hidden = prim.length < 2;
}

// Dòng ghi chú trong hộp Cài đặt: giọng đã chọn có đang thực sự được phát không.
function refreshVoiceNote() {
  const note = $('#voiceInfo');
  const want = prefVoice();
  const inReader = document.body.dataset.view === 'reader' && R.book && R.unit && R.voice;
  note.textContent = inReader && R.voice !== want
    ? `Phần đang nghe chưa có ${voiceText(voiceInfo(R.book, want))}, nên vẫn phát ${voiceText(voiceInfo(R.book, R.voice))}. Giọng mới đang được chuẩn bị.`
    : '';
}

// Đổi giọng: áp dụng cho cả thư viện. Nếu đang ở trang đọc thì nạp lại phần đang
// nghe bằng giọng mới và tiếp tục đúng câu đang nghe.
function setVoice(vid, tell = true) {
  store.set('voice', vid);
  $$('#optVoice button').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.v === vid)));
  const view = document.body.dataset.view;
  const known = catalog?.books.flatMap((b) => b.voices || []).find((v) => v.id === vid);
  let msg = `Đã chọn ${known ? voiceText(known) : 'giọng đọc'}.`;
  if (view === 'reader' && R.book && R.unit && R.unit.ready !== false) {
    const now = voiceOf(R.unit);
    if (now !== vid) msg = `${pickable(R.book).some((v) => v.id === vid) ? 'Phần' : 'Cuốn'} này chưa có ${voiceText(voiceInfo(R.book, vid))}, vẫn phát ${voiceText(voiceInfo(R.book, now))}.`;
    if (now !== R.voice) {
      // audio còn đang nạp dở (vừa mở, hoặc vừa đổi giọng) thì dùng lại đích của lần mở đang chờ
      const keep = R.ready ? { sent: R.sents.length ? sentAt(audio.currentTime) : 0, play: !audio.paused } : R.keep;
      openReader(R.book, R.unit.no, keep);
    }
  } else if (view === 'book') {
    const book = findBook(decodeURIComponent((location.hash.split('/')[2]) || ''));
    if (book) renderBook(book);
  }
  refreshVoiceNote();
  if (tell) announce(msg);
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
  // audio còn đang nạp: ghi lại đích, nạp xong sẽ nhảy tới đó
  if (!R.ready) { R.pendingSeek = R.sents[i].b; R.quietSeek = true; R.keep = { sent: i, play }; highlight(i); return; }
  audio.currentTime = R.sents[i].b + 0.001;
  R.userScrollAt = 0;
  highlight(i);
  if (play) audio.play().catch(() => {});
}
function stepSent(dir) {
  if (!R.sents.length) return;
  noteJump();
  const i = sentAt(audio.currentTime);
  // lùi: nếu đã nghe hơn 1,5 giây của câu thì quay về đầu chính câu đó
  const j = dir < 0 && audio.currentTime - R.sents[i].b > 1.5 ? i : Math.max(0, Math.min(R.sents.length - 1, i + dir));
  seekSent(j, !audio.paused);
  tellSent(j);
}
// Ghi lại chỗ đang nghe trước mỗi cú nhảy, để nút Quay lại đưa về đúng chỗ đó khi lỡ nhảy nhầm.
function noteJump() {
  if (!R.ready || !R.book || !R.unit) return;
  R.undo = { slug: R.book.slug, unit: R.unit.no, t: audio.currentTime, s: R.sents.length ? sentAt(audio.currentTime) : 0 };
  $('#undo').setAttribute('aria-disabled', 'false');
}
function undoJump() {
  const u = R.undo;
  if (!u || !R.book || u.slug !== R.book.slug) { cue('limit'); return announce('Chưa có cú nhảy nào để quay lại.'); }
  R.undo = null;
  $('#undo').setAttribute('aria-disabled', 'true');
  cue('undo');
  if (u.unit !== R.unit.no) {
    const play = !audio.paused;
    history.replaceState(null, '', `#/r/${R.book.slug}/${u.unit}`);
    document.title = `${R.book.title} · Sách Nói`;
    openReader(R.book, u.unit, { sent: u.s, play });
    return announce('Đã quay lại phần trước cú nhảy.');
  }
  if (!R.ready) return;
  audio.currentTime = u.t;
  R.userScrollAt = 0;
  tick();
  announce(`Đã quay lại ${spoken(u.t)}.`);
}

const sentText = (i) => (R.sents[i]?.el.classList.contains('s') ? R.sents[i].el.textContent : $('#h-reader').textContent);
// Đang tạm dừng mà nhảy thì không có tiếng nào phát ra: đọc câu vừa tới để người nghe biết mình ở đâu,
// và cũng là cách nghe lại từng câu bằng trình đọc màn hình.
function tellSent(i) { if (audio.paused && R.sents[i]) announce(sentText(i), false); }
const paraOf = (i) => R.sents[i]?.para || R.sents[i]?.el;
function stepPara(dir) {
  if (!R.sents.length) return;
  noteJump();
  const i = sentAt(audio.currentTime);
  let first = i;
  while (first > 0 && paraOf(first - 1) === paraOf(i)) first--;
  let j;
  if (dir > 0) {
    j = i;
    while (j < R.sents.length && paraOf(j) === paraOf(i)) j++;
    if (j >= R.sents.length) { cue('limit'); return announce('Đây là đoạn cuối của phần này.'); }
  } else if (audio.currentTime - R.sents[first].b > 1.5 || first === 0) {
    j = first;                                  // về đầu đoạn đang nghe
  } else {
    j = first - 1;
    while (j > 0 && paraOf(j - 1) === paraOf(first - 1)) j--;
  }
  seekSent(j, !audio.paused);
  tellSent(j);
}
// Nhảy tới dấu trang trước hoặc sau chỗ đang nghe, kể cả khi dấu trang nằm ở phần khác.
// wrap: hết dấu trang thì vòng lại (chế độ chạm đơn giản chỉ có một nút để đi qua các dấu trang).
function stepMark(dir, wrap = false) {
  if (!R.book || !R.unit || !R.sents.length) return;
  const ready = readyUnits(R.book);
  const marks = getMarks(R.book.slug).filter((m) => ready.some((u) => u.no === m.unit));
  if (!marks.length) { cue('limit'); return announce('Cuốn này chưa có dấu trang. Nút Đánh dấu ghi nhớ câu đang nghe.'); }
  const here = R.ready ? sentAt(audio.currentTime) : Math.max(0, R.cur);
  const side = (m) => Math.sign(m.unit - R.unit.no || m.s - here);
  let k = -1;
  if (dir > 0) k = marks.findIndex((m) => side(m) > 0);
  else for (let i = marks.length - 1; i >= 0 && k < 0; i--) if (side(marks[i]) < 0) k = i;
  if (k < 0 && wrap) k = dir > 0 ? 0 : marks.length - 1;
  if (k < 0) { cue('limit'); return announce(dir > 0 ? 'Không còn dấu trang nào phía sau.' : 'Không còn dấu trang nào phía trước.'); }
  const m = marks[k], play = !audio.paused, other = m.unit !== R.unit.no;
  noteJump();
  if (other) {
    history.replaceState(null, '', `#/r/${R.book.slug}/${m.unit}`);
    openReader(R.book, m.unit, { sent: m.s, play });
  } else seekSent(m.s, play);
  const u = R.book.units.find((x) => x.no === m.unit);
  announce(`Dấu trang ${k + 1} trên ${marks.length}${other && u ? ', ' + unitName(R.book, u) : ''}.${play ? '' : ' ' + m.text}`, false);
}
// Nghe tiếp sau khi dừng lâu hoặc mở lại sách: lùi về đầu câu đang nghe dở để bắt lại mạch.
// Câu mới nghe chưa tới 2 giây thì lùi thêm một câu; câu quá dài thì chỉ lùi 5 giây.
const REWIND_AFTER = 20000;          // dừng lâu hơn mức này (mili giây) mới lùi
function rewindPoint(t) {
  if (store.get('rewind', '1') !== '1' || !R.sents.length) return t;
  let i = sentAt(t);
  if (t - R.sents[i].b < 2 && i > 0) i--;
  const b = R.sents[i].b;
  return t - b > 15 ? Math.max(0, t - 5) : Math.min(t, b);
}
const TIME_STEP = 30;
function stepTime(dir) {
  if (!R.ready) return;
  noteJump();
  const d = audio.duration || 0;
  audio.currentTime = Math.max(0, Math.min(Math.max(0, d - 0.5), audio.currentTime + dir * TIME_STEP));
  R.userScrollAt = 0;
  tick();
  if (audio.paused) announce(`${spoken(audio.currentTime)}.`, false);
}
const STEPS = {
  sent: { prev: 'Câu trước', next: 'Câu sau', go: (d) => stepSent(d) },
  para: { prev: 'Đoạn trước', next: 'Đoạn sau', go: (d) => stepPara(d) },
  time: { prev: `Lùi ${TIME_STEP} giây`, next: `Tới ${TIME_STEP} giây`, go: (d) => stepTime(d) },
  unit: { prev: 'Phần trước', next: 'Phần sau', go: (d) => gotoUnit(d) },
  mark: { prev: 'Dấu trang trước', next: 'Dấu trang sau', go: (d) => stepMark(d) },
};
const stepKind = () => (STEPS[store.get('step', 'sent')] ? store.get('step', 'sent') : 'sent');
function setStep(kind, tell = true) {
  if (!STEPS[kind]) kind = 'sent';
  store.set('step', kind);
  $('#step').value = kind;
  $('#prev').setAttribute('aria-label', STEPS[kind].prev);
  $('#next').setAttribute('aria-label', STEPS[kind].next);
  if (tell) announce(`Hai nút lùi và tới bây giờ là ${STEPS[kind].prev.toLowerCase()} và ${STEPS[kind].next.toLowerCase()}.`);
}
const stepNav = (dir) => STEPS[stepKind()].go(dir);

function gotoUnit(dir) {
  if (!R.book) return;
  const ready = readyUnits(R.book);
  const idx = ready.findIndex((u) => u.no === R.unit?.no);
  const target = ready[idx + dir];
  if (target) { noteJump(); location.hash = `#/r/${R.book.slug}/${target.no}`; }
  else { cue('limit'); announce(dir > 0 ? 'Đây là phần cuối.' : 'Đây là phần đầu.'); }
}

function savePos() {
  if (!R.ready || !R.book || !R.unit || !audio.duration) return;
  store.set('pos:' + R.book.slug, {
    unit: R.unit.no, t: Math.round(audio.currentTime * 10) / 10, at: Date.now(),
    s: R.sents.length ? sentAt(audio.currentTime) : 0, v: R.voice,   // câu và giọng, để đổi giọng vẫn nghe tiếp đúng chỗ
  });
}

function tick() {
  const t = audio.currentTime, d = audio.duration || R.unit?.duration || 0;
  if (R.sents.length) highlight(sentAt(t));
  $('#tCur').textContent = clock(t);
  $('#tDur').textContent = clock(d);
  const scrub = $('#scrub');
  if (!scrub.matches(':active')) scrub.value = d ? Math.round((t / d) * 1000) : 0;
  // chỉ đổi khi nội dung đổi, để trình đọc màn hình không bị gọi liên tục
  const vt = `${spoken(t)} trên ${spoken(d)}`;
  if (scrub.getAttribute('aria-valuetext') !== vt) scrub.setAttribute('aria-valuetext', vt);
  refreshMarkBtn();
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
    if (!R.quietSeek) announce(`${R.seekNote || ''}Nghe tiếp từ ${spoken(R.pendingSeek)}.`);
    R.pendingSeek = null; R.quietSeek = false; R.seekNote = '';
  }
  // audio vừa nạp đúng là của lần mở mới nhất thì từ đây mới được ghi vị trí
  if (R.srcToken === R.token) R.ready = true;
  tick();
});
audio.addEventListener('play', () => {
  if (R.pausedAt && R.ready && Date.now() - R.pausedAt > REWIND_AFTER) {
    const t = rewindPoint(audio.currentTime);
    if (t < audio.currentTime) audio.currentTime = t;
  }
  R.pausedAt = 0;
  setPlayUi(true); cancelAnimationFrame(raf); loop(); renderSimple();
});
audio.addEventListener('pause', () => { R.pausedAt = R.ready ? Date.now() : 0; setPlayUi(false); savePos(); tick(); renderSimple(); });
// đã tự nhảy đi chỗ khác trong lúc dừng thì không lùi nữa
audio.addEventListener('seeking', () => { R.pausedAt = 0; });
// mạng chậm: im lặng quá 3 giây thì nói rõ là đang tải, kẻo người nghe tưởng ứng dụng hỏng
let waitTimer;
audio.addEventListener('waiting', () => {
  clearTimeout(waitTimer);
  waitTimer = setTimeout(() => { if (!audio.paused && audio.readyState < 3) announce('Đang tải âm thanh, xin chờ.'); }, 3000);
});
for (const ev of ['playing', 'pause', 'emptied']) audio.addEventListener(ev, () => clearTimeout(waitTimer));
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
    cue('end');
    if (sleepAtEnd) { R.holdNext = true; setSleep(0, false); }
    store.set('pos:' + book.slug, { unit: next.no, t: 0, at: Date.now() });
    location.hash = `#/r/${book.slug}/${next.no}`;
  } else {
    store.set('pos:' + book.slug, { unit: unit.no, t: unitDuration(unit, R.voice), at: Date.now() });
    if (sleepAtEnd) setSleep(0, false);
    cue('done');
    announce(`Đã nghe hết ${book.title}.`);
  }
});

// ---------- điều khiển ----------
$('#play').addEventListener('click', () => (audio.paused ? audio.play().catch(() => {}) : audio.pause()));
$('#prev').addEventListener('click', () => stepNav(-1));
$('#next').addEventListener('click', () => stepNav(1));
$('#step').addEventListener('change', (e) => setStep(e.target.value));
$('#where').addEventListener('click', whereAmI);
$('#mark').addEventListener('click', toggleMark);
$('#undo').addEventListener('click', undoJump);
setStep(stepKind(), false);
let scrubAt = 0;
$('#scrub').addEventListener('input', (e) => {
  const d = audio.duration || 0;
  if (Date.now() - scrubAt > 1500) noteJump();     // một lần kéo là một cú nhảy
  scrubAt = Date.now();
  if (d) { audio.currentTime = (e.target.value / 1000) * d; R.userScrollAt = 0; tick(); }
});
$('#speed').addEventListener('change', (e) => setRate(Number(e.target.value)));
function setRate(rate) {
  audio.playbackRate = rate;
  $('#speed').value = String(rate);
  store.set('rate', rate);
  if (R.book) store.set('rate:' + R.book.slug, rate);
  announce(`Tốc độ ${String(rate).replace('.', ' phẩy ')} lần.`);
}
function nudgeRate(dir) {
  const opts = $$('#speed option').map((o) => Number(o.value));
  const at = opts.indexOf(audio.playbackRate) + dir;
  if (at < 0 || at >= opts.length) { cue('limit'); return announce(dir > 0 ? 'Đây là tốc độ nhanh nhất.' : 'Đây là tốc độ chậm nhất.'); }
  const i = at;
  setRate(opts[i]);
}
$('#text').addEventListener('click', (e) => {
  const span = e.target.closest('.s');
  if (span) { noteJump(); seekSent(Number(span.dataset.i)); }
});
$('#h-reader').addEventListener('click', () => { if (R.sents.length) seekSent(0); });
for (const ev of ['wheel', 'touchmove']) addEventListener(ev, () => { R.userScrollAt = Date.now(); }, { passive: true });

addEventListener('keydown', (e) => {
  if ($('#settings').open || $('#help').open) return;
  if (e.target.matches('input, select, textarea') || e.ctrlKey || e.metaKey || e.altKey) return;
  if (e.key === '?') { e.preventDefault(); return openHelp(); }
  if (document.body.dataset.view !== 'reader') return;
  const act = {
    ' ': () => (audio.paused ? audio.play().catch(() => {}) : audio.pause()),
    k: () => (audio.paused ? audio.play().catch(() => {}) : audio.pause()),
    ArrowRight: () => (e.shiftKey ? gotoUnit(1) : stepNav(1)),
    ArrowLeft: () => (e.shiftKey ? gotoUnit(-1) : stepNav(-1)),
    PageDown: () => stepPara(1),
    PageUp: () => stepPara(-1),
    j: () => stepTime(-1),
    l: () => stepTime(1),
    i: () => whereAmI(),
    m: () => toggleMark(),
    z: () => undoJump(),
    ArrowUp: () => nudgeRate(1),
    ArrowDown: () => nudgeRate(-1),
    ']': () => gotoUnit(1),
    '[': () => gotoUnit(-1),
  }[e.key.length === 1 ? e.key.toLowerCase() : e.key];
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
    artist: `${R.book.creator} · ${voiceText(voiceInfo(R.book, R.voice))}`,
    album: R.book.title,
    // Bìa sách hiện ở màn hình khoá. Mất mạng thì chỉ dùng ảnh mà service worker đã giữ sẵn
    // (biểu tượng ứng dụng), không có service worker thì bỏ ảnh để khỏi tải hỏng.
    artwork: navigator.onLine
      ? [R.book.cover
        ? { src: new URL(R.book.cover, location.href).href, sizes: '888x1200', type: 'image/jpeg' }
        : { src: new URL('icons/icon-512.png', location.href).href, sizes: '512x512', type: 'image/png' }]
      : (navigator.serviceWorker?.controller
        ? [{ src: new URL('icons/icon-512.png', location.href).href, sizes: '512x512', type: 'image/png' }] : []),
  });
  const set = (name, fn) => { try { navigator.mediaSession.setActionHandler(name, fn); } catch { /* không hỗ trợ */ } };
  set('play', () => audio.play());
  set('pause', () => audio.pause());
  set('previoustrack', () => stepNav(-1));
  set('nexttrack', () => stepNav(1));
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
  rewind: { el: '#optRewind', def: '1', name: 'Khi nghe tiếp', apply: () => {} },
  cue: { el: '#optCue', def: '1', name: 'Tiếng báo hiệu', apply: () => {} },
  hl: {
    el: '#optHl', def: 'default', name: 'Tô câu đang đọc',
    apply: (v) => { const c = document.documentElement.classList; c.remove('hl-blue', 'hl-green', 'hl-line', 'hl-none'); if (v !== 'default') c.add('hl-' + v); },
  },
};
for (const [key, p] of Object.entries(prefs)) {
  const setPref = (v, tell) => {
    store.set(key, v);
    p.apply(v);
    $$(`${p.el} button`).forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.v === v)));
    if (tell) {
      const pick = $(`${p.el} button[data-v="${v}"]`).textContent.trim();
      announce(p.name ? `${p.name}: ${pick}.` : `Đã chọn ${pick}.`);
    }
  };
  setPref(String(store.get(key, p.def)), false);
  $(p.el).addEventListener('click', (e) => { const b = e.target.closest('button'); if (b) setPref(b.dataset.v, true); });
}

let sleepTimer, sleepEnd = 0, sleepTick, sleepAtEnd = false, sleepSet = 0;
const SLEEP_OPTS = [0, 15, 30, 60, -1];
function setSleep(min, tell = true) {
  sleepSet = min;
  clearTimeout(sleepTimer); clearInterval(sleepTick);
  sleepAtEnd = min < 0;                       // -1: dừng khi hết phần đang nghe
  if (sleepAtEnd) {
    sleepEnd = 0;
    $$('#optSleep button').forEach((b) => b.setAttribute('aria-pressed', String(Number(b.dataset.v) === -1)));
    $('#sleepInfo').textContent = 'Tự dừng khi hết phần đang nghe.';
    if (tell) announce('Sẽ tự dừng khi hết phần đang nghe.');
    return;
  }
  sleepEnd = min ? Date.now() + min * 60000 : 0;
  $$('#optSleep button').forEach((b) => b.setAttribute('aria-pressed', String(Number(b.dataset.v) === min)));
  const info = $('#sleepInfo');
  const show = () => { info.textContent = sleepEnd ? `Tự dừng sau ${Math.max(1, Math.ceil((sleepEnd - Date.now()) / 60000))} phút nữa.` : ''; };
  show();
  if (min) {
    sleepTick = setInterval(show, 30000);
    sleepTimer = setTimeout(() => { audio.pause(); setSleep(0, false); cue('sleep'); announce('Đã hết giờ hẹn, tạm dừng.'); }, min * 60000);
  }
  if (tell) announce(min ? `Sẽ tự dừng sau ${min} phút.` : 'Đã tắt hẹn giờ.');
}
setSleep(0, false);
setVoice(prefVoice(), false);
$('#optVoice').addEventListener('click', (e) => { const b = e.target.closest('button'); if (b) setVoice(b.dataset.v); });
$('#optSleep').addEventListener('click', (e) => { const b = e.target.closest('button'); if (b) setSleep(Number(b.dataset.v)); });
$('#openSettings').addEventListener('click', () => { refreshVoiceNote(); $('#settings').showModal(); });
$('#settings').addEventListener('click', (e) => { if (e.target === e.currentTarget) e.currentTarget.close(); });  // chạm ra ngoài để đóng

function openHelp() { if (!$('#help').open) { $('#help').showModal(); $('#h-help').focus(); } }
for (const b of $$('[data-help]')) b.addEventListener('click', openHelp);
$('#help').addEventListener('click', (e) => { if (e.target === e.currentTarget) e.currentTarget.close(); });

// Tìm sách bằng giọng nói (Web Speech API; có trên Chrome Android và Safari). Không có thì ẩn nút.
const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
if (SpeechRec) {
  const mic = $('#voiceSearch');
  mic.hidden = false;
  let rec = null;
  mic.addEventListener('click', () => {
    if (rec) { rec.abort(); return; }
    rec = new SpeechRec();
    rec.lang = 'vi-VN'; rec.interimResults = false; rec.maxAlternatives = 1;
    let heard = false;
    rec.onstart = () => { mic.setAttribute('aria-pressed', 'true'); announce('Đang nghe. Hãy đọc tên sách hoặc tên tác giả.'); };
    rec.onresult = (e) => {
      heard = true;
      const said = e.results[0][0].transcript.replace(/[.?!]+$/, '').trim();
      $('#q').value = said;
      const n = filterLibrary(false);
      announce(n ? `Bạn nói: ${said}. ${n} cuốn khớp.` : `Bạn nói: ${said}. Không tìm thấy sách nào khớp.`);
    };
    rec.onerror = (e) => {
      heard = true;
      announce(e.error === 'not-allowed' || e.error === 'service-not-allowed'
        ? 'Chưa được phép dùng micro. Hãy cho phép trong cài đặt trình duyệt, hoặc gõ tên sách.'
        : 'Không nghe rõ. Hãy nhấn nút và nói lại.');
    };
    rec.onend = () => { mic.setAttribute('aria-pressed', 'false'); if (!heard) announce('Không nghe thấy gì. Hãy nhấn nút và nói lại.'); rec = null; };
    try { rec.start(); } catch { rec = null; }
  });
}

// ================= CHẾ ĐỘ CHẠM ĐƠN GIẢN =================
// Người khiếm thị không phải vuốt qua từng phần tử: cả màn hình là năm nút lớn ở vị trí cố định.
// Hai trạng thái: đang chọn sách (lùi/tới chuyển qua từng cuốn) và đang nghe (lùi/tới 30 giây).
const simpleBooks = () => (catalog?.books || []).filter((b) => !b.external && readyUnits(b).length);
const simpleListening = () => document.body.dataset.view === 'reader' && !!R.book && !!R.unit;
let sIdx = -1;
// Khi đang nghe, hai nút lùi và tới có ba chức năng, đổi bằng nút ở góc dưới bên trái:
// nhảy 30 giây, chọn phần, đổi tốc độ. Nhờ vậy vẫn chỉ có vài nút lớn mà đủ việc.
const S_MODES = {
  time: { name: `${TIME_STEP} giây`, prev: `Lùi ${TIME_STEP} giây`, next: `Tới ${TIME_STEP} giây` },
  unit: { name: 'Chọn phần', prev: 'Phần trước', next: 'Phần sau' },
  rate: { name: 'Tốc độ', prev: 'Chậm hơn', next: 'Nhanh hơn' },
  mark: { name: 'Dấu trang', prev: 'Tới dấu trang', next: 'Đánh dấu' },
  sleep: { name: 'Hẹn giờ tắt', prev: 'Bớt giờ', next: 'Thêm giờ' },
};
let sMode = 'time';
const sModeList = () => (R.book && readyUnits(R.book).length > 1 ? ['time', 'unit', 'rate', 'mark', 'sleep'] : ['time', 'rate', 'mark', 'sleep']);
const sModeNow = () => (sModeList().includes(sMode) ? sMode : 'time');
function cycleSimpleMode() {
  const list = sModeList();
  sMode = list[(list.indexOf(sModeNow()) + 1) % list.length];
  renderSimple();
  const m = S_MODES[sMode];
  const extra = sMode === 'unit' ? ` Đang ở phần ${readyUnits(R.book).findIndex((u) => u.no === R.unit.no) + 1} trên ${readyUnits(R.book).length}.`
    : sMode === 'rate' ? ` Tốc độ hiện tại ${String(audio.playbackRate).replace('.', ' phẩy ')} lần.`
    : sMode === 'mark' ? ` Cuốn này ${getMarks(R.book.slug).length ? 'có ' + getMarks(R.book.slug).length : 'chưa có'} dấu trang.`
    : sMode === 'sleep' ? (sleepAtEnd ? ' Đang hẹn dừng khi hết phần.' : sleepEnd ? ` Sẽ tự dừng sau ${Math.max(1, Math.ceil((sleepEnd - Date.now()) / 60000))} phút nữa.` : ' Hẹn giờ đang tắt.') : '';
  announce(`Nút bên trái bây giờ là ${m.prev.toLowerCase()}, nút bên phải là ${m.next.toLowerCase()}.${extra}`, false);
}
function bookSpeech(b, i, n) {
  const p = bookProgress(b), pct = Math.round(p * 100);
  const state = p >= 0.995 ? 'đã nghe xong' : pct > 0 ? `đã nghe ${pct} phần trăm` : '';
  return [b.title, b.creator, spoken(b.duration), state, `cuốn ${i + 1} trên ${n}`].filter(Boolean).join(', ') + '.';
}
const resumable = (b) => { const p = bookProgress(b); return !!getPos(b.slug) && p > 0.002 && p < 0.995; };
function renderSimple() {
  const on = simpleOn();
  document.body.classList.toggle('simple', on);
  $('#simple').hidden = !on;
  $('#skip').hidden = on;
  for (const v of $$('.view')) v.inert = on;      // phần giao diện đầy đủ nằm bên dưới: không cho focus lọt vào
  if (!on || !catalog) return;
  const books = simpleBooks();
  const set = (id, text, icon) => { $(`${id} b`).textContent = text; if (icon) $(`${id} .ic`).textContent = icon; };
  if (simpleListening()) {
    const many = R.book.units.length > 1;
    $('#sInfo').innerHTML = `<small>Đang nghe · chạm để nghe hướng dẫn</small><b>${esc(R.book.title)}</b><span>${esc(many ? unitName(R.book, R.unit) : R.book.creator)}</span>`;
    const m = S_MODES[sModeNow()];
    set('#sPrev', m.prev); set('#sNext', m.next);
    $('#sMode').hidden = false;
    $('#sMode').innerHTML = `<small>Lùi và tới theo</small>${m.name}`;
    $('#sMode').setAttribute('aria-label', `Đổi chức năng hai nút lùi và tới. Đang là ${m.prev.toLowerCase()} và ${m.next.toLowerCase()}`);
    set('#sMain', audio.paused ? 'Phát' : 'Tạm dừng', audio.paused ? '▶' : '⏸');
    $('#sAlt').textContent = 'Chọn sách khác';
    sIdx = Math.max(0, books.findIndex((b) => b.slug === R.book.slug));
  } else if (books.length) {
    if (sIdx < 0) {       // lần đầu: cuốn nghe gần đây nhất
      const recent = books.filter((b) => getPos(b.slug)).sort((a, b) => getPos(b.slug).at - getPos(a.slug).at)[0];
      sIdx = recent ? books.indexOf(recent) : 0;
    }
    sIdx = Math.min(sIdx, books.length - 1);
    const b = books[sIdx];
    $('#sInfo').innerHTML = `<small>Cuốn ${sIdx + 1} trên ${books.length} · chạm để nghe hướng dẫn</small><b>${esc(b.title)}</b><span>${esc(b.creator)} · ${spoken(b.duration)}</span>`;
    set('#sPrev', 'Sách trước'); set('#sNext', 'Sách sau');
    $('#sMode').hidden = true;
    set('#sMain', resumable(b) ? 'Nghe tiếp' : 'Nghe cuốn này', '▶');
    $('#sAlt').textContent = 'Giao diện đầy đủ';
  }
}
function setSimple(on) {
  store.set('simple', on ? '1' : '0');
  if (!on) { try { speechSynthesis.cancel(); } catch { /* không có */ } audio.volume = 1; }
  renderSimple();
  if (on) {
    $('#sMain').focus();
    const books = simpleBooks();
    announce('Chế độ chạm đơn giản. Chạm một lần là chạy. Nút trên cùng nhắc lại bạn đang ở đâu. Ở giữa, bên trái là lùi, bên phải là tới. '
      + 'Nút lớn nhất bên dưới là nghe hoặc tạm dừng. Hàng dưới cùng để đổi sách, và khi đang nghe có thêm nút đổi chức năng: chọn phần, tốc độ, dấu trang, hẹn giờ tắt. '
      + (simpleListening() ? `Đang mở ${R.book.title}.` : `Đang chọn: ${bookSpeech(books[sIdx], sIdx, books.length)}`), false);
  } else {
    $(`#view-${document.body.dataset.view} h1`)?.focus({ preventScroll: true });
    announce('Đã về giao diện đầy đủ.');
  }
}
function simpleStep(dir) {
  const books = simpleBooks();
  if (!simpleListening()) {
    if (!books.length) return;
    sIdx = (sIdx + dir + books.length) % books.length;       // hết danh sách thì vòng lại
    renderSimple();
    return announce(bookSpeech(books[sIdx], sIdx, books.length), false);
  }
  if (sModeNow() === 'rate') return nudgeRate(dir);
  if (sModeNow() === 'mark') return dir < 0 ? stepMark(1, true) : toggleMark();
  if (sModeNow() === 'sleep') {
    const at = SLEEP_OPTS.indexOf(sleepSet) + dir;
    if (at < 0) { cue('limit'); return announce('Hẹn giờ đang tắt.'); }
    if (at >= SLEEP_OPTS.length) { cue('limit'); return announce('Đây là mức cuối: tự dừng khi hết phần đang nghe.'); }
    return setSleep(SLEEP_OPTS[at]);
  }
  if (sModeNow() === 'unit') {
    const list = readyUnits(R.book), to = list[list.findIndex((u) => u.no === R.unit.no) + dir];
    R.forcePlay = !audio.paused;
    if (to) announce(`${unitName(R.book, to)}, phần ${list.indexOf(to) + 1} trên ${list.length}.`, false);
    else R.forcePlay = false;
    return gotoUnit(dir);       // hết phần để đi thì gotoUnit tự báo
  }
  // đang nghe: lùi khi mới ở đầu phần thì về phần trước; tới sát cuối phần thì ứng dụng tự sang phần sau
  const ready = readyUnits(R.book);
  if (dir < 0 && R.ready && audio.currentTime < 3 && ready.findIndex((u) => u.no === R.unit.no) > 0) { R.forcePlay = !audio.paused; return gotoUnit(-1); }
  stepTime(dir);
}
function simpleMain() {
  if (simpleListening()) {
    if (audio.paused) audio.play().catch(() => {});
    else { audio.pause(); announce('Tạm dừng.', false); }
    return;
  }
  const b = simpleBooks()[sIdx];
  if (!b) return;
  const ready = readyUnits(b), pos = getPos(b.slug);
  let unit = pos && ready.some((u) => u.no === pos.unit) ? pos.unit : ready[0].no;
  if (bookProgress(b) >= 0.995) { unit = ready[0].no; store.set('pos:' + b.slug, { unit, t: 0, at: Date.now() }); }   // nghe xong rồi: nghe lại từ đầu
  R.forcePlay = true;
  sMode = 'time';             // mở sách nào cũng bắt đầu với lùi và tới 30 giây
  const target = `#/r/${b.slug}/${unit}`;
  if (location.hash === target) route(); else location.hash = target;
}
function simpleAlt() {
  if (!simpleListening()) return setSimple(false);
  location.hash = '#/';
}
// Nút trên cùng là hướng dẫn sử dụng bằng lời, nghe lại được bất cứ lúc nào: đang ở đâu, rồi từng nút làm gì.
$('#sInfo').addEventListener('click', () => {
  if (simpleListening()) {
    const m = S_MODES[sModeNow()];
    return whereAmI(` Hướng dẫn: ở giữa màn hình, bên trái là ${m.prev.toLowerCase()}, bên phải là ${m.next.toLowerCase()}. `
      + `Nút lớn nhất bên dưới là ${audio.paused ? 'phát' : 'tạm dừng'}. Ở hàng dưới cùng, nút bên trái đổi chức năng hai nút lùi và tới: `
      + `${sModeList().map((k) => S_MODES[k].name.toLowerCase()).join(', ')}. Nút bên phải để chọn sách khác. Ứng dụng tự nhớ chỗ bạn đang nghe.`);
  }
  const books = simpleBooks();
  if (books.length) {
    announce(`Đang chọn sách. ${bookSpeech(books[sIdx], sIdx, books.length)} Hướng dẫn: ở giữa màn hình, bên trái là sách trước, bên phải là sách sau. `
      + 'Nút lớn nhất bên dưới để nghe cuốn đang chọn. Nút dưới cùng để về giao diện đầy đủ. Mỗi nút chỉ cần chạm một lần.', false);
  }
});
$('#sPrev').addEventListener('click', () => simpleStep(-1));
$('#sNext').addEventListener('click', () => simpleStep(1));
$('#sMain').addEventListener('click', simpleMain);
$('#sAlt').addEventListener('click', simpleAlt);
$('#sMode').addEventListener('click', cycleSimpleMode);
$('#simpleOn').addEventListener('click', () => setSimple(true));

// ================= ĐỊNH TUYẾN =================
function show(view, title, heading) {
  for (const v of ['library', 'book', 'reader']) $(`#view-${v}`).hidden = v !== view;
  document.body.dataset.view = view;
  document.title = title;
  window.scrollTo(0, 0);
  const was = simpleOn() && $('#sAlt').textContent === 'Chọn sách khác';
  renderSimple();
  if (simpleOn()) {
    // vừa rời trang đọc về chỗ chọn sách: nói rõ đang ở đâu
    const books = simpleBooks();
    if (was && view !== 'reader' && books.length) announce(`Chọn sách. ${bookSpeech(books[sIdx], sIdx, books.length)}`, false);
    if (!$('#simple').contains(document.activeElement)) requestAnimationFrame(() => $('#sMain').focus());
    return;
  }
  // đưa focus vào tiêu đề để trình đọc màn hình đọc tên màn hình mới
  requestAnimationFrame(() => heading?.focus({ preventScroll: true }));
}

async function route() {
  const [, kind, slug, unitStr, sentStr] = (location.hash || '#/').split('/');
  const book = slug ? findBook(decodeURIComponent(slug)) : null;
  if (kind !== 'r') { savePos(); audio.pause(); R.token++; }

  if (kind === 'b' && book && !book.external) {
    await renderBook(book);
    return show('book', `${book.title} — ${book.creator} · Sách Nói`, $('#h-book'));
  }
  if (kind === 'r' && book && !book.external) {
    const no = Number(unitStr) || readyUnits(book)[0]?.no;
    show('reader', `${book.title} · Sách Nói`, $('#h-reader'));
    // dấu trang: mở đúng câu đã đánh dấu, rồi bỏ đuôi /s… để tải lại trang không nhảy về dấu trang nữa
    const m = /^s(\d+)$/.exec(sentStr || '');
    if (m) history.replaceState(null, '', `#/r/${book.slug}/${no}`);
    return openReader(book, no, m ? { sent: Number(m[1]), play: store.get('autoplay', '1') === '1' } : null);
  }
  renderLibrary();
  show('library', 'Sách Nói — Thư viện sách nói tiếng Việt', $('#h-library'));
}

$('#q').addEventListener('input', () => filterLibrary());
$('#genre').addEventListener('change', () => filterLibrary());
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
    renderVoiceOptions();
  } catch {
    $('#librarySummary').textContent = 'Không tải được danh mục sách. Hãy kiểm tra kết nối mạng rồi tải lại trang.';
    store.set('simple', '0');
    announce($('#librarySummary').textContent);
    return;
  }
  await route();
  if ('serviceWorker' in navigator && location.protocol.startsWith('http')) {
    navigator.serviceWorker.register('sw.js').catch(() => {});
  }
})();

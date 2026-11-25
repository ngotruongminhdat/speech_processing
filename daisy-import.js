// Đọc một cuốn sách nói DAISY (2.02 hoặc 3) đóng trong file zip, ngay trên máy người dùng.
// Không gửi gì lên mạng. Kết quả có cùng dạng với dữ liệu ứng dụng vẫn dùng cho sách trong thư viện:
// mỗi file âm thanh thành một phần, mỗi phần gồm các đoạn, mỗi đoạn gồm các câu có mốc thời gian.

export class ImportError extends Error {
  constructor(code) { super(code); this.code = code; }
}

// ---------- zip ----------
// Chỉ đọc mục lục ở cuối file rồi cắt từng mục khi cần, nên sách vài trăm MB không phải nạp cả vào bộ nhớ.
const u16 = (v, o) => v.getUint16(o, true);
const u32 = (v, o) => v.getUint32(o, true);
async function zipEntries(file) {
  const tailLen = Math.min(file.size, 65557);
  const tail = new DataView(await file.slice(file.size - tailLen).arrayBuffer());
  let p = tailLen - 22;
  while (p >= 0 && u32(tail, p) !== 0x06054b50) p--;
  if (p < 0) throw new ImportError('notzip');
  const count = u16(tail, p + 10), size = u32(tail, p + 12), start = u32(tail, p + 16);
  if (count === 0xffff || start === 0xffffffff) throw new ImportError('toobig');
  const cd = new DataView(await file.slice(start, start + size).arrayBuffer());
  const out = new Map();
  const utf8 = new TextDecoder('utf-8');
  for (let i = 0, o = 0; i < count && o + 46 <= cd.byteLength && u32(cd, o) === 0x02014b50; i++) {
    const n = u16(cd, o + 28);
    const name = utf8.decode(new Uint8Array(cd.buffer, o + 46, n)).replace(/\\/g, '/');
    if (!name.endsWith('/') && !name.startsWith('__MACOSX/')) {
      out.set(name.toLowerCase(), { name, flags: u16(cd, o + 8), method: u16(cd, o + 10), csize: u32(cd, o + 20), off: u32(cd, o + 42) });
    }
    o += 46 + n + u16(cd, o + 30) + u16(cd, o + 32);
  }
  return out;
}
async function entryBlob(file, e, type = '') {
  if (e.flags & 1) throw new ImportError('locked');
  const h = new DataView(await file.slice(e.off, e.off + 30).arrayBuffer());
  if (h.byteLength < 30 || u32(h, 0) !== 0x04034b50) throw new ImportError('broken');
  const at = e.off + 30 + u16(h, 26) + u16(h, 28);
  const raw = file.slice(at, at + e.csize, type);
  if (e.method === 0) return raw;
  if (e.method !== 8 || !('DecompressionStream' in globalThis)) throw new ImportError('compress');
  const plain = await new Response(raw.stream().pipeThrough(new DecompressionStream('deflate-raw'))).blob();
  return new Blob([plain], { type });
}
async function entryText(file, e) {
  const buf = await (await entryBlob(file, e)).arrayBuffer();
  const head = new TextDecoder('utf-8').decode(buf.slice(0, 1024));
  const enc = (/encoding=["']([\w-]+)["']/i.exec(head) || /charset=["']?([\w-]+)/i.exec(head) || [])[1] || 'utf-8';
  try { return new TextDecoder(enc).decode(buf); } catch { return new TextDecoder('utf-8').decode(buf); }
}

// ---------- đường dẫn và XML ----------
const dirOf = (name) => name.slice(0, name.lastIndexOf('/') + 1);
function resolve(base, href) {
  let path = href.split('#')[0];
  try { path = decodeURIComponent(path); } catch { /* giữ nguyên */ }
  const out = [];
  for (const part of (dirOf(base) + path.replace(/\\/g, '/')).split('/')) {
    if (part === '..') out.pop(); else if (part && part !== '.') out.push(part);
  }
  return out.join('/').toLowerCase();
}
function parseXml(text, lenient = false) {
  const tryXml = (s) => {
    const d = new DOMParser().parseFromString(s, 'application/xml');
    return d.getElementsByTagName('parsererror').length ? null : d;
  };
  // sách cũ hay khai DTD bên ngoài và dùng thực thể HTML (&nbsp;) mà bộ đọc XML không biết
  const repaired = () => text.replace(/<!DOCTYPE[^>[]*(\[[^\]]*\])?\s*>/i, '')
    .replace(/&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[0-9a-f]+);)(\w+;)?/gi, (m, ent) => (ent ? (ent === 'nbsp;' ? ' ' : ' ') : '&amp;'));
  const doc = tryXml(text) || tryXml(repaired());
  if (doc) return doc;
  if (lenient) return new DOMParser().parseFromString(text, 'text/html');
  throw new ImportError('broken');
}
const local = (el) => el.localName.toLowerCase();
const els = (root, ...names) => [...root.getElementsByTagName('*')].filter((e) => names.includes(local(e)));
const attr = (el, ...names) => { for (const n of names) { const v = el.getAttribute(n); if (v != null) return v; } return null; };
const clean = (s) => (s || '').replace(/\s+/g, ' ').trim();
const natural = (a, b) => a.localeCompare(b, undefined, { numeric: true });

// Thời điểm trong SMIL: "1.610s", "npt=1.61s", "0:01:02.5", "500ms".
function clock(v) {
  if (v == null) return null;
  v = String(v).trim().replace(/^npt=/, '');
  if (v.includes(':')) return v.split(':').reduce((a, x) => a * 60 + (parseFloat(x) || 0), 0);
  const n = parseFloat(v);
  if (Number.isNaN(n)) return null;
  return /ms$/.test(v) ? n / 1000 : /min$/.test(v) ? n * 60 : /h$/.test(v) ? n * 3600 : n;
}

// Một <par> của SMIL: một mẩu văn bản và (các) đoạn âm thanh đọc mẩu đó.
function smilItems(doc, smilName) {
  return els(doc, 'par').map((par) => {
    const text = els(par, 'text')[0];
    return {
      text: text ? attr(text, 'src') : null,
      clips: els(par, 'audio').map((a) => ({
        file: resolve(smilName, attr(a, 'src') || ''),
        b: clock(attr(a, 'clipBegin', 'clip-begin')) ?? 0,
        e: clock(attr(a, 'clipEnd', 'clip-end')),
      })).filter((c) => c.file),
    };
  }).filter((it) => it.clips.length);
}

const HEADING = /^(h[1-6]|hd|levelhd|doctitle)$/;
const BLOCK = /^(p|h[1-6]|hd|levelhd|doctitle|docauthor|li|dd|dt|td|th|line|blockquote|div)$/;
const MIME = { mp3: 'audio/mpeg', mp4: 'audio/mp4', m4a: 'audio/mp4', aac: 'audio/aac', wav: 'audio/wav', ogg: 'audio/ogg', oga: 'audio/ogg' };

// Thời lượng thật của file âm thanh; không đọc được thì trả về null.
function audioDuration(blob) {
  return new Promise((done) => {
    const a = new Audio(), url = URL.createObjectURL(blob);
    const end = (v) => { clearTimeout(timer); URL.revokeObjectURL(url); a.removeAttribute('src'); done(v); };
    const timer = setTimeout(() => end(null), 8000);
    a.preload = 'metadata';
    a.onloadedmetadata = () => end(Number.isFinite(a.duration) && a.duration > 0 ? a.duration : null);
    a.onerror = () => end(null);
    a.src = url;
  });
}

// Đọc file zip. Trả về { title, creator, narrator, date, format, units: [{ title, duration, paras, blob }] }.
// onProgress(đã xong, tổng số) được gọi sau mỗi file âm thanh.
export async function readDaisy(file, onProgress = () => {}) {
  const zip = await zipEntries(file);
  const names = [...zip.keys()].sort(natural);
  const opfs = names.filter((n) => n.endsWith('.opf'));
  const nccs = names.filter((n) => /(^|\/)ncc\.html?$/.test(n));
  if (!opfs.length && !nccs.length) throw new ImportError('nodaisy');
  const read = async (name, lenient) => parseXml(await entryText(file, zip.get(name)), lenient);

  const meta = { title: '', creator: '', narrator: '', date: '', format: opfs.length ? 'DAISY 3' : 'DAISY 2.02' };
  const fill = (key, value) => { if (!meta[key] && clean(value)) meta[key] = clean(value); };
  const smils = [];         // thứ tự đọc của cả cuốn
  if (opfs.length) {
    // DAISY 3: mỗi file OPF là một cuốn (hoặc một chương đóng riêng), spine cho thứ tự các file SMIL
    for (const opf of opfs) {
      const doc = await read(opf);
      fill('title', els(doc, 'title')[0]?.textContent);
      fill('creator', els(doc, 'creator')[0]?.textContent);
      fill('date', els(doc, 'date')[0]?.textContent);
      for (const m of els(doc, 'meta')) if (/narrator$/i.test(m.getAttribute('name') || '')) fill('narrator', m.getAttribute('content'));
      const items = new Map(els(doc, 'item').map((it) => [it.getAttribute('id'), it.getAttribute('href') || '']));
      let spine = els(doc, 'itemref').map((r) => items.get(r.getAttribute('idref'))).filter(Boolean);
      if (!spine.length) spine = [...items.values()].filter((h) => /\.smil$/i.test(h));
      for (const href of spine) { const n = resolve(opf, href); if (zip.has(n) && !smils.includes(n)) smils.push(n); }
    }
  } else {
    // DAISY 2.02: ncc.html là mục lục, các liên kết trong đó cho thứ tự các file SMIL
    for (const ncc of nccs) {
      const doc = await read(ncc, true);
      for (const m of els(doc, 'meta')) {
        const name = (m.getAttribute('name') || '').toLowerCase();
        if (name === 'dc:title') fill('title', m.getAttribute('content'));
        if (name === 'dc:creator') fill('creator', m.getAttribute('content'));
        if (name === 'dc:date') fill('date', m.getAttribute('content'));
        if (name === 'ncc:narrator') fill('narrator', m.getAttribute('content'));
      }
      fill('title', els(doc, 'title')[0]?.textContent);       // không có dc:title thì lấy thẻ title
      for (const a of els(doc, 'a')) {
        const n = resolve(ncc, a.getAttribute('href') || '');
        if (n.endsWith('.smil') && zip.has(n) && !smils.includes(n)) smils.push(n);
      }
      if (!smils.length) smils.push(...names.filter((n) => n.endsWith('.smil') && dirOf(n) === dirOf(ncc)));
    }
  }
  if (!smils.length) throw new ImportError('nodaisy');

  // văn bản: tra phần tử theo id trong từng file nội dung (DTBook, HTML hoặc chính ncc.html)
  const docs = new Map();
  const textOf = async (smilName, src) => {
    if (!src) return null;
    const name = resolve(smilName, src), id = src.split('#')[1];
    if (!docs.has(name)) {
      const ids = new Map();
      if (zip.has(name)) {
        try { for (const e of (await read(name, true)).getElementsByTagName('*')) if (e.id || e.getAttribute('id')) ids.set(e.id || e.getAttribute('id'), e); }
        catch { /* file nội dung hỏng: coi như sách chỉ có tiếng */ }
      }
      docs.set(name, ids);
    }
    const el = id ? docs.get(name).get(id) : null;
    if (!el) return null;
    let block = el;
    while (block && !BLOCK.test(local(block))) block = block.parentElement;
    block = block || el;
    return { text: clean(el.textContent), block, heading: HEADING.test(local(block)) };
  };

  // gom theo file âm thanh: mỗi file thành một phần
  const units = new Map();
  for (const smil of smils) {
    let doc;
    try { doc = await read(smil); } catch { continue; }       // một file SMIL hỏng: bỏ qua, đọc tiếp các file khác
    for (const item of smilItems(doc, smil)) {
      const t = await textOf(smil, item.text);
      const byFile = new Map();
      for (const c of item.clips) {
        const cur = byFile.get(c.file);
        if (!cur) byFile.set(c.file, { b: c.b, e: c.e });
        else { cur.b = Math.min(cur.b, c.b); cur.e = c.e == null || cur.e == null ? null : Math.max(cur.e, c.e); }
      }
      for (const [fileName, span] of byFile) {
        if (!zip.has(fileName)) continue;
        if (!units.has(fileName)) units.set(fileName, { file: fileName, paras: [] });
        const paras = units.get(fileName).paras, last = paras[paras.length - 1];
        if (!t || !t.text) continue;
        const sent = [span.b, span.e, t.text];
        const prev = last && last.block === t.block ? last.s[last.s.length - 1] : null;
        // hai mẩu SMIL cùng trỏ vào một mẩu văn bản (hay gặp ở tiêu đề): coi là một câu, nối dài mốc kết thúc
        if (prev && prev[2] === t.text) prev[1] = span.e == null || prev[1] == null ? null : Math.max(prev[1], span.e);
        else if (prev) last.s.push(sent);
        else paras.push({ t: t.heading ? 'h1' : 'p', block: t.block, s: [sent] });
      }
    }
  }
  if (!units.size) throw new ImportError('noaudio');

  const out = [];
  let done = 0;
  for (const u of units.values()) {
    const ext = u.file.slice(u.file.lastIndexOf('.') + 1);
    const blob = await entryBlob(file, zip.get(u.file), MIME[ext] || 'audio/mpeg');
    const sents = u.paras.flatMap((p) => p.s).sort((a, b) => a[0] - b[0]);
    const duration = (await audioDuration(blob)) ?? Math.max(0, ...sents.map((s) => s[1] ?? s[0]));
    // câu thiếu mốc kết thúc: lấy mốc bắt đầu của câu sau, câu cuối thì lấy hết file
    sents.forEach((s, i) => { if (s[1] == null || s[1] < s[0]) s[1] = sents[i + 1] ? sents[i + 1][0] : duration; });
    const k = out.length + 1;
    const title = clean(u.paras.find((p) => p.t === 'h1')?.s.map((s) => s[2]).join(' ')).slice(0, 120) || `Phần ${k}`;
    let paras = u.paras.map((p) => ({ t: p.t, s: p.s.sort((a, b) => a[0] - b[0]) })).sort((a, b) => a.s[0][0] - b.s[0][0]);
    if (!paras.length) paras = [{ t: 'h1', s: [[0, duration, title]] }];        // sách chỉ có tiếng: lấy tên phần làm văn bản
    paras = paras.map((p, i) => ({ id: `n${i + 1}`, t: p.t, b: p.s[0][0], e: p.s[p.s.length - 1][1], s: p.s }));
    out.push({ title, duration, paras, blob });
    onProgress(++done, units.size);
  }
  // nhiều chương cùng một tên (sách chỉ có tiếng, hoặc không có tiêu đề chương): thêm số thứ tự cho dễ phân biệt
  if (out.length > 1 && new Set(out.map((u) => u.title)).size === 1) out.forEach((u, i) => { u.title = `Phần ${i + 1}`; });
  return { ...meta, title: meta.title || file.name.replace(/\.zip$/i, ''), units: out };
}

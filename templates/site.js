/* Shared progressive enhancement. No network requests; works over file://. */
(() => {
  'use strict';
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const storage = {
    get(key, fallback) {
      try { return JSON.parse(localStorage.getItem(key)) ?? fallback; }
      catch { return fallback; } // Private mode/file:// can deny storage access.
    },
    set(key, value) {
      try { localStorage.setItem(key, JSON.stringify(value)); return true; }
      catch { toast('浏览器未允许保存；本次操作仍然有效，可导出备份。'); return false; }
    }
  };
  let toastTimer;
  function toast(message) {
    let el = $('.toast');
    if (!el) {
      el = document.createElement('div'); el.className = 'toast';
      el.setAttribute('role', 'status'); document.body.append(el);
    }
    el.textContent = message; el.hidden = false;
    clearTimeout(toastTimer); toastTimer = setTimeout(() => { el.hidden = true; }, 3500);
  }
  function csvCell(value) {
    let s = String(value ?? '');
    if (/^[\s]*[=+@-]/.test(s)) s = "'" + s; // Spreadsheet formula injection.
    return '"' + s.replaceAll('"', '""') + '"';
  }
  function download(data, mime, filename) {
    const url = URL.createObjectURL(new Blob([data], { type: mime }));
    const a = document.createElement('a'); a.href = url; a.download = filename;
    document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  function initLibrary() {
    const source = $('#library-data');
    if (!source) return;
    let catalog;
    try { catalog = JSON.parse(source.textContent); }
    catch { toast('目录数据无法解析，仍可通过卡片打开报告。'); return; }
    if (!Array.isArray(catalog.papers)) return;
    const papers = catalog.papers;
    const grid = $('#paper-grid');
    const cards = new Map($$('[data-paper-slug]', grid).map(el => [el.dataset.paperSlug, el]));
    const knownTags = new Set(papers.flatMap(p => p.tags));
    const key = 'paper-reading:favorites:' + location.pathname;
    const saved = storage.get(key, []);
    const favorites = new Set(Array.isArray(saved) ? saved.filter(x => typeof x === 'string') : []);
    let shelf = 'all'; let selected = new Set(); let visible = papers;
    const search = $('#paper-search'); const sort = $('#paper-sort');
    const query = new URLSearchParams(location.search);
    search.value = query.get('q') || '';
    selected = new Set(query.getAll('tag').filter(t => knownTags.has(t)));
    if (['read', 'year', 'title'].includes(query.get('sort'))) sort.value = query.get('sort');
    if (query.get('shelf') === 'favorites') shelf = 'favorites';
    const searchable = new Map(papers.map(p => [p.slug, [p.title, p.summary_zh, p.venue, p.year,
      ...(p.authors || []), ...p.tags, ...p.keywords].join(' ').toLocaleLowerCase()]));
    function urlState() {
      const url = new URL(location.href);
      for (const name of ['q', 'tag', 'sort', 'shelf']) url.searchParams.delete(name);
      if (search.value.trim()) url.searchParams.set('q', search.value.trim());
      [...selected].sort().forEach(t => url.searchParams.append('tag', t));
      if (sort.value !== 'read') url.searchParams.set('sort', sort.value);
      if (shelf !== 'all') url.searchParams.set('shelf', shelf);
      try { history.replaceState(null, '', url); }
      catch { /* Some browsers disallow history updates on file://. */ }
    }
    function render(updateURL = true) {
      const terms = search.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
      visible = papers.filter(p => (shelf !== 'favorites' || favorites.has(p.slug)) &&
        [...selected].every(t => p.tags.includes(t)) && terms.every(t => searchable.get(p.slug).includes(t)));
      visible.sort((a, b) => {
        if (sort.value === 'title') return a.title.localeCompare(b.title, 'zh-CN');
        const order = sort.value === 'year' ? (b.year || 0) - (a.year || 0) : (b.read_at || '').localeCompare(a.read_at || '');
        return order || a.title.localeCompare(b.title, 'zh-CN');
      });
      cards.forEach(c => { c.hidden = true; });
      visible.forEach(p => { const c = cards.get(p.slug); if (c) { c.hidden = false; grid.append(c); } });
      $('#result-count').textContent = '显示 ' + visible.length + ' / ' + papers.length + ' 篇论文';
      $('#empty-state').hidden = visible.length > 0;
      $('#favorite-count').textContent = papers.filter(p => favorites.has(p.slug)).length;
      $$('[data-tag]').forEach(b => b.setAttribute('aria-pressed', String(selected.has(b.dataset.tag))));
      $$('[data-shelf]').forEach(b => b.setAttribute('aria-pressed', String(shelf === b.dataset.shelf)));
      $$('[data-favorite]').forEach(b => {
        const active = favorites.has(b.dataset.favorite);
        b.setAttribute('aria-pressed', String(active)); b.textContent = active ? '★' : '☆';
        b.setAttribute('aria-label', (active ? '取消收藏：' : '收藏：') + b.dataset.title);
      });
      const chips = $('#active-filters'); chips.replaceChildren();
      selected.forEach(tag => {
        const b = document.createElement('button'); b.className = 'tag'; b.type = 'button';
        b.textContent = tag + ' ×'; b.setAttribute('aria-label', '移除标签 ' + tag);
        b.addEventListener('click', () => { selected.delete(tag); render(); }); chips.append(b);
      });
      if (updateURL) urlState();
    }
    function reset() { search.value = ''; selected.clear(); shelf = 'all'; sort.value = 'read'; render(); }
    $$('[data-tag]').forEach(b => b.addEventListener('click', () => {
      selected.has(b.dataset.tag) ? selected.delete(b.dataset.tag) : selected.add(b.dataset.tag); render();
    }));
    $$('[data-shelf]').forEach(b => b.addEventListener('click', () => { shelf = b.dataset.shelf; render(); }));
    $$('[data-favorite]').forEach(b => b.addEventListener('click', () => {
      const slug = b.dataset.favorite; favorites.has(slug) ? favorites.delete(slug) : favorites.add(slug);
      storage.set(key, [...favorites]); render();
    }));
    function setView(view) {
      grid.classList.toggle('is-list', view === 'list');
      $$('[data-view]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.view === view)));
    }
    setView(storage.get('paper-reading:view', 'grid'));
    $$('[data-view]').forEach(b => b.addEventListener('click', () => {
      setView(b.dataset.view); storage.set('paper-reading:view', b.dataset.view);
    }));
    search.addEventListener('input', () => render()); sort.addEventListener('change', () => render());
    $('#clear-filters').addEventListener('click', reset); $('#empty-reset').addEventListener('click', reset);
    $$('[data-export]').forEach(b => b.addEventListener('click', () => {
      const records = visible.map(p => ({ ...p, favorite: favorites.has(p.slug) }));
      if (b.dataset.export === 'json') {
        download(JSON.stringify({ ...catalog, papers: records }, null, 2), 'application/json', 'paper-catalog.json');
      } else {
        const fields = ['slug', 'title', 'year', 'venue', 'authors', 'summary_zh', 'tags', 'keywords', 'read_at', 'report', 'favorite'];
        const rows = [fields, ...records.map(p => fields.map(f => Array.isArray(p[f]) ? p[f].join('; ') : p[f]))];
        download('\uFEFF' + rows.map(r => r.map(csvCell).join(',')).join('\r\n'), 'text/csv;charset=utf-8', 'paper-catalog.csv');
      }
      toast('已导出当前筛选的 ' + records.length + ' 篇论文');
    }));
    document.addEventListener('keydown', e => {
      if (e.key === '/' && !e.ctrlKey && !e.metaKey && !e.altKey && !/INPUT|TEXTAREA|SELECT/.test(e.target.tagName) && !e.target.isContentEditable) {
        e.preventDefault(); search.focus();
      }
    });
    render(false);
    document.body.classList.add('js-ready');
  }
  function initReader() {
    if (!document.body.classList.contains('report-page')) return;
    const main = $('main');
    const metadata = $('#paper-metadata');
    if (metadata) {
      try {
        const p = JSON.parse(metadata.textContent);
        const holder = $('.report-tags');
        if (holder && Array.isArray(p.tags)) {
          holder.replaceChildren();
          p.tags.forEach(tag => {
            const a = document.createElement('a'); a.className = 'tag';
            a.href = '../index.html?tag=' + encodeURIComponent(tag); a.textContent = tag; holder.append(a);
          });
        }
      } catch { toast('文章标签无法解析，请检查元数据。'); }
    }
    const progress = $('.reading-progress'); const progressLabel = $('.progress-label');
    const links = $$('.toc-float a[href^="#"]');
    const sections = links.map(a => document.getElementById(decodeURIComponent(a.hash.slice(1))));
    const mobileNav = $('.mobile-toc nav');
    if (mobileNav) {
      links.forEach(a => mobileNav.append(a.cloneNode(true)));
      mobileNav.addEventListener('click', e => { if (e.target.closest('a')) $('.mobile-toc').open = false; });
    }
    let scheduled = false;
    function updatePosition() {
      scheduled = false;
      const max = document.documentElement.scrollHeight - innerHeight;
      const value = max > 0 ? Math.min(100, Math.max(0, Math.round(scrollY / max * 100))) : 100;
      if (progress) progress.style.width = value + '%';
      if (progressLabel) progressLabel.textContent = value + '%';
      let current = 0;
      sections.forEach((s, i) => { if (s && s.getBoundingClientRect().top <= 150) current = i; });
      links.forEach((a, i) => { if (i === current) a.setAttribute('aria-current', 'location'); else a.removeAttribute('aria-current'); });
    }
    function schedule() { if (!scheduled) { scheduled = true; requestAnimationFrame(updatePosition); } }
    addEventListener('scroll', schedule, { passive: true }); addEventListener('resize', schedule);
    if (typeof ResizeObserver !== 'undefined') new ResizeObserver(schedule).observe(main);
    const defaultSize = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--reader-size')) || 20;
    let size = Number(storage.get('paper-reading:font-size', defaultSize));
    if (!Number.isFinite(size)) size = defaultSize;
    size = Math.min(26, Math.max(16, size));
    function setSize() { document.documentElement.style.setProperty('--reader-size', size + 'px'); schedule(); }
    setSize();
    $$('[data-action]').forEach(b => b.addEventListener('click', () => {
      const action = b.dataset.action;
      if (action === 'font-down' || action === 'font-up') {
        size = Math.max(16, Math.min(26, size + (action === 'font-up' ? 1 : -1)));
        setSize(); storage.set('paper-reading:font-size', size);
      } else if (action === 'focus') {
        const active = document.body.classList.toggle('focus-reading');
        b.setAttribute('aria-pressed', String(active)); b.textContent = active ? '退出专注' : '专注阅读';
      } else if (action === 'print') window.print();
    }));
    $$('table', main).forEach(table => {
      if (table.parentElement.classList.contains('table-scroll')) return;
      const wrap = document.createElement('div'); wrap.className = 'table-scroll'; wrap.tabIndex = 0;
      wrap.setAttribute('role', 'region'); wrap.setAttribute('aria-label', '数据表格，可横向滚动');
      table.before(wrap); wrap.append(table);
    });
    $$('pre', main).forEach(pre => {
      const b = document.createElement('button'); b.type = 'button'; b.className = 'copy-button'; b.textContent = '复制代码';
      b.addEventListener('click', async () => {
        const text = (pre.querySelector('code') || pre).textContent;
        try {
          if (!navigator.clipboard?.writeText) throw new Error('Clipboard API unavailable');
          await navigator.clipboard.writeText(text); toast('代码已复制');
        } catch {
          const range = document.createRange(); range.selectNodeContents(pre);
          const selection = getSelection(); selection.removeAllRanges(); selection.addRange(range);
          toast('已选中代码，请按 Ctrl+C / ⌘C 复制。');
        }
      }); pre.after(b);
    });
    const dialog = document.createElement('dialog'); dialog.className = 'image-dialog';
    dialog.setAttribute('aria-label', '查看论文插图');
    dialog.innerHTML = '<div class="dialog-actions"><a target="_blank" rel="noopener">打开原图 ↗</a><button type="button" autofocus>关闭 · Esc</button></div><img alt=""><p></p>';
    document.body.append(dialog);
    let svgURL = null;
    const close = () => dialog.close(); $('button', dialog).addEventListener('click', close);
    dialog.addEventListener('close', () => { if (svgURL) { URL.revokeObjectURL(svgURL); svgURL = null; } });
    dialog.addEventListener('click', e => {
      const r = dialog.getBoundingClientRect();
      if (e.target === dialog && (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom)) close();
    });
    $$('figure img, figure > svg', main).forEach(img => {
      const vector = img.tagName.toLowerCase() === 'svg';
      const alt = vector ? $('title', img)?.textContent || '图解' : img.alt;
      img.setAttribute('tabindex', '0'); img.setAttribute('role', 'button'); img.setAttribute('aria-label', '放大：' + alt);
      if (!vector) { if (!img.hasAttribute('loading')) img.loading = 'lazy'; img.decoding = 'async'; }
      const open = () => {
        let src = img.currentSrc || img.src;
        if (vector) {
          svgURL = URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(img)], { type: 'image/svg+xml' }));
          src = svgURL;
        }
        $('img', dialog).src = src; $('img', dialog).alt = alt;
        $('a', dialog).href = src;
        const caption = img.closest('figure').querySelector('figcaption');
        const copy = caption?.cloneNode(true);
        if (copy) $$('details', copy).forEach(x => x.remove());
        $('p', dialog).textContent = copy?.textContent.trim() || alt;
        dialog.showModal();
      };
      img.addEventListener('click', open);
      img.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(); } });
      const hint = document.createElement('span'); hint.className = 'zoom-hint'; hint.textContent = '点击图片查看大图'; img.after(hint);
    });
    const printOpened = [];
    addEventListener('beforeprint', () => { $$('details', main).forEach(d => { if (!d.open) { printOpened.push(d); d.open = true; } }); });
    addEventListener('afterprint', () => { printOpened.splice(0).forEach(d => { d.open = false; }); });
    document.body.classList.add('js-ready'); updatePosition();
  }
  initLibrary(); initReader();
  if (window.mermaid) {
    window.mermaid.initialize({ startOnLoad: false, theme: 'neutral', securityLevel: 'strict' });
    window.mermaid.run({ querySelector: '.mermaid' }).catch(() => toast('部分流程图未能渲染，请查看图下的文字说明。'));
  }
})();

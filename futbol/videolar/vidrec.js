// Önizleme videosu kaydedici: sahte saat (page.clock) ile kare kare
// kullanım: node vidrec.js <scratch> <land|port> <seed>
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const S = process.argv[2], MODE = process.argv[3] || 'land', SEED = +(process.argv[4] || 1);
const VW = MODE === 'land' ? 960 : 540, VH = MODE === 'land' ? 540 : 960, FPS = 25, FMS = 1000 / FPS;
const OUT = path.join(S, 'vid_' + MODE); fs.mkdirSync(OUT, { recursive: true });
for (const f of fs.readdirSync(OUT)) fs.unlinkSync(path.join(OUT, f));
const MOCK = `window.CrazyGames = { SDK: { environment: 'disabled', init: () => Promise.resolve(), ad: { requestAd: (t, cb) => cb.adError({}) }, game: {} } };`;
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const ctx = await b.newContext({ viewport: { width: VW, height: VH }, deviceScaleFactor: 1, isMobile: MODE !== 'land', hasTouch: MODE !== 'land', locale: 'en-US' });
  const pg = await ctx.newPage();
  const errs = []; pg.on('pageerror', e => errs.push(e.message));
  await pg.route('**/*', r => { const u = r.request().url();
    if (u.startsWith('https://sdk.crazygames.com/')) return r.fulfill({ contentType: 'application/javascript', body: MOCK });
    if (u === 'http://cg.test/') return r.fulfill({ path: '/home/user/youtube-otomasyon/futbol/crazygames/index.html', contentType: 'text/html' });
    return r.abort(); });
  await pg.addInitScript(seed => { let s = seed >>> 0; Math.random = () => { s = (s + 0x6D2B79F5) >>> 0; let t = s; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; try { localStorage.clear(); } catch (e) {} }, SEED);
  await pg.addInitScript(require('./vclock.js'));
  await pg.goto('http://cg.test/');
  const run = ms => pg.evaluate(ms => window.__adv(ms), ms);
  await run(1500);
  // dokunma göstergesi
  await pg.evaluate(() => { const d = document.createElement('div'); d.id = 'vt'; d.style.cssText = 'position:fixed;z-index:999;width:44px;height:44px;margin:-22px 0 0 -22px;border-radius:50%;background:rgba(255,255,255,.35);border:3px solid #fff;box-shadow:0 0 18px rgba(0,0,0,.5);pointer-events:none;display:none;left:0;top:0'; document.body.appendChild(d); });
  let frames = [], keep = [], n = 0;
  const frame = async () => { await pg.evaluate(() => { window.__rend = false; }); await run(FMS - 20); await pg.evaluate(() => { window.__rend = true; }); await run(20); const f = path.join(OUT, 'tmp_' + (n++) + '.png'); const t0 = Date.now(); await pg.screenshot({ path: f, timeout: 300000 }); if (process.env.TL) console.log('frame', n, Date.now() - t0, 'ms'); frames.push(f); };
  const commit = () => { keep.push(...frames); frames = []; };
  const discard = () => { for (const f of frames) fs.unlinkSync(f); frames = []; };
  const touch = (x, y, on) => pg.evaluate(([x, y, on]) => { const d = document.getElementById('vt'); d.style.display = on ? 'block' : 'none'; d.style.left = x + 'px'; d.style.top = y + 'px'; }, [x, y, on]);
  const ptr = (sel, type, x, y) => pg.evaluate(([sel, type, x, y]) => document.querySelector(sel).dispatchEvent(new PointerEvent(type, { clientX: x, clientY: y, pointerType: 'touch', bubbles: true, pointerId: 7 })), [sel, type, x, y]);
  const click = async sel => { await pg.evaluate(s => document.querySelector(s).click(), sel); await run(300); };
  const cineOpen = () => pg.evaluate(() => !document.querySelector('#cine').hidden);
  // --- kurulum (kaydedilmez)
  await click('#bNew'); await click('#bCreate'); await pg.evaluate(() => document.querySelector('[data-cn="TR"]').click()); await run(800);
  for (let i = 0; i < 80 && !(await pg.$('#cineCh [data-cc]')); i++) { await click('#cineSkip'); await run(200); }
  await pg.evaluate(() => document.querySelector('#cineCh [data-cc="0"]').click()); await run(600);
  await pg.evaluate(() => document.querySelector('[data-first="2"]').click()); await run(400); await click('#okB');
  // --- sinematik (ilk gün) kaydı
  await pg.evaluate(() => document.querySelector('#bPlay').click()); await run(200);
  let cineFrames = [];
  if (await cineOpen()) {
    for (let k = 0; k < 4; k++) { for (let i = 0; i < 22; i++) await frame(); await pg.evaluate(() => document.querySelector('#cine').click()); }
    cineFrames = frames; frames = [];
    for (let i = 0; i < 80 && !(await pg.$('#cineCh [data-cc]')); i++) { await click('#cine'); }
    await pg.evaluate(() => document.querySelector('#cineCh [data-cc="0"]').click()); await run(600);
    if (!(await pg.$('#kick'))) { await pg.evaluate(() => document.querySelector('#bPlay').click()); await run(300); }
  }
  if (await pg.$('#cA')) { await click('#cA'); }
  // anları ceza sahasına çevir
  await pg.evaluate(() => { const M = __yy.M; M.types = ['ceza', 'ceza', 'frikik', 'ceza', 'ceza', 'penalti', 'ceza', 'ceza', 'frikik', 'ceza', 'ceza', 'penalti', 'ceza', 'ceza', 'ceza', 'ceza']; M.mins = M.types.map((t, i) => 6 + i * 5); });
  await click('#kick');
  await pg.evaluate(() => { const r = __yy.R.r; if (r && !r.__w) { const o = r.render.bind(r); r.render = (sc, c) => { if (window.__rend !== false) o(sc, c); }; r.__w = 1; } });
  let goals = 0;
  for (let g = 0; g < 900 && goals < 2; g++) {
    const st = await pg.evaluate(() => { const M = __yy.M; if (!M) return 'none'; if (!document.querySelector('#mpanel').hidden) return document.querySelector('#mpanel #toHub') ? 'end' : document.querySelector('#goOn') ? 'fail' : 'panel'; const W = M.W; if (!W) return 'wait'; if (W.placing) return 'placing'; return W.phase === 'aim' && W.ball.owner === W.you ? 'aim' : W.phase; });
    if (st === 'end') break;
    if (st === 'fail') { discard(); await click('#goOn'); continue; }
    if (st === 'done') {
      const msg = await pg.evaluate(() => document.querySelector('#mmsg').textContent);
      console.log('MOMENT', msg, await pg.evaluate(() => __yy.M.W.type));
      if (msg.startsWith('GOAL')) { for (let i = 0; i < 55; i++) await frame(); commit(); goals++; }
      else { discard(); }
      await run(3000); continue;
    }
    if (st === 'aim') {
      const info = await pg.evaluate(() => {
        const W = __yy.M.W, b = W.ball, gd = Math.hypot(b.x, b.y);
        let tx = 0, ty = 0, kind = 'shot', power = 0.9;
        if (gd > 26 && W.type !== 'frikik') { let best = null, bd = 1e9; for (const m of W.mates) { const d = m.y; if (m.y < b.y && d < bd) { bd = d; best = m; } } if (best) { tx = best.x; ty = best.y; kind = 'pass'; power = 0.5; } }
        const ax = __yy.R.axes, wx = tx - b.x, wy = ty - b.y, l = Math.hypot(wx, wy), ux = wx / l, uy = wy / l;
        const [sx, sy] = __yy.toScreen(W.you.x, W.you.y);
        return { kind, power, tx, ty, sdx: ux * ax.rx + uy * ax.ry, sdy: -(ux * ax.fx + uy * ax.fy), sx, sy, gkx: W.gk.x };
      });
      console.log('AIM', JSON.stringify(info), await pg.evaluate(() => [__yy.M.W.type, __yy.M.W.ball.x.toFixed(1), __yy.M.W.ball.y.toFixed(1)].join(' ')));
      // bekleme + kaydırma
      for (let i = 0; i < 8; i++) await frame();
      const L = Math.min(VW, 480) * 0.42 * info.power, sx = Math.min(VW - 40, Math.max(40, info.sx)), sy = Math.min(VH - 80, Math.max(VH * 0.45, info.sy + 30));
      await touch(sx, sy, true); await ptr('#pitch3d', 'pointerdown', sx, sy);
      for (let i = 1; i <= 12; i++) { const x = sx + info.sdx * L * i / 12, y = sy + info.sdy * L * i / 12; await ptr('#pitch3d', 'pointermove', x, y); await touch(x, y, true); await frame(); }
      for (let i = 0; i < 3; i++) await frame();
      await ptr('#pitch3d', 'pointerup', sx + info.sdx * L, sy + info.sdy * L); await touch(0, 0, false);
      for (let i = 0; i < 6; i++) await frame();
      if (await pg.evaluate(() => __yy.PL.open)) {
        const shot = await pg.evaluate(() => __yy.PL.shot);
        console.log('PLACE', shot);
        const tgt = shot ? [info.gkx > 0 ? -2.75 : 2.75, 0.55] : [info.tx, info.ty - 1];
        const [cx, cy] = await pg.evaluate(() => { const r = document.querySelector('#plC').getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height * 0.6]; });
        const [ex, ey] = await pg.evaluate(t => __yy.plPoint(t[0], t[1]), tgt);
        await touch(cx, cy, true); await ptr('#plC', 'pointerdown', cx, cy);
        for (let i = 1; i <= 16; i++) { const k = 1 - Math.pow(1 - i / 16, 2), x = cx + (ex - cx) * k, y = cy + (ey - cy) * k; await ptr('#plC', 'pointermove', x, y); await touch(x, y, true); await frame(); }
        for (let i = 0; i < 5; i++) await frame();
        await ptr('#plC', 'pointerup', ex, ey); await touch(0, 0, false);
      }
      for (let i = 0; i < 70; i++) { await frame(); const ph = await pg.evaluate(() => { const W = __yy.M && __yy.M.W; return W ? (W.phase === 'aim' && W.ball.owner === W.you ? 'aim' : W.phase) : 'x'; }); if (ph === 'done' || ph === 'aim') break; }
      continue;
    }
    await run(FMS);
  }
  discard();
  // dosya listesi: goller, sonra sinematik
  const list = [...keep, ...cineFrames];
  list.forEach((f, i) => fs.renameSync(f, path.join(OUT, 'f' + String(i).padStart(5, '0') + '.png')));
  console.log(MODE, 'goals', goals, 'frames', list.length, 'errors', JSON.stringify(errs));
  await b.close();
})();

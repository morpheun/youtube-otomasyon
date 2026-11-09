// Sanal saat: performance.now/Date.now/setTimeout/setInterval/rAF sayfa içinde elle ilerletilir (window.__adv(ms))
module.exports = () => {
  const realNow = performance.now.bind(performance), base = Date.now();
  let T = 0, id = 1; const timers = new Map(); let rafs = [], nextRaf = 16;
  performance.now = () => T;
  const RD = Date; const FD = function (...a) { return a.length ? new RD(...a) : new RD(base + T); }; FD.now = () => base + T; FD.prototype = RD.prototype; FD.parse = RD.parse; FD.UTC = RD.UTC; window.Date = FD;
  window.setTimeout = (f, ms = 0, ...a) => { const i = id++; timers.set(i, { t: T + Math.max(0, ms), f, a, iv: 0 }); return i; };
  window.setInterval = (f, ms = 0, ...a) => { const i = id++; timers.set(i, { t: T + Math.max(1, ms), f, a, iv: Math.max(1, ms) }); return i; };
  window.clearTimeout = window.clearInterval = i => timers.delete(i);
  window.requestAnimationFrame = f => { const i = id++; rafs.push([i, f]); return i; };
  window.cancelAnimationFrame = i => { rafs = rafs.filter(r => r[0] !== i); };
  window.__adv = ms => {
    const end = T + ms;
    for (let guard = 0; guard < 100000; guard++) {
      let nt = Infinity, ni = null; for (const [i, tm] of timers) if (tm.t < nt) { nt = tm.t; ni = i; }
      const nr = nextRaf;
      if (Math.min(nt, nr) > end) break;
      if (nt <= nr) { T = nt; const tm = timers.get(ni); if (tm.iv) tm.t += tm.iv; else timers.delete(ni); try { typeof tm.f === 'function' ? tm.f(...tm.a) : eval(tm.f); } catch (e) { console.error(e); } }
      else { T = nr; nextRaf += 1000 / 60; const list = rafs; rafs = []; for (const [, f] of list) { try { f(T); } catch (e) { console.error(e); } } }
    }
    T = end;
  };
};
